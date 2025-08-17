import os
import tempfile
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import aiofiles

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
from contextlib import asynccontextmanager

from src.financial_analysis.crew import FinancialAnalysisCrew

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Settings
class Settings(BaseSettings):
    openai_api_key: str = Field("", env='OPENAI_API_KEY')  # Made optional for development
    app_name: str = "Financial Analysis API"
    debug: bool = Field(False, env='DEBUG')
    max_file_size: int = Field(50 * 1024 * 1024, env='MAX_FILE_SIZE')  # 50MB
    allowed_extensions: List[str] = ['.pdf', '.csv', '.xlsx', '.xls', '.txt', '.json']
    cors_origins: List[str] = Field(["*"], env='CORS_ORIGINS')
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # This will ignore extra fields
    }

# Pydantic Models
class AnalysisRequest(BaseModel):
    file_name: str = Field(..., description="Name of the uploaded file")
    analysis_type: str = Field("comprehensive", description="Type of analysis to perform")
    
    @field_validator('analysis_type')
    def validate_analysis_type(cls, v):
        allowed_types = ["comprehensive", "quick", "ratios_only"]
        if v not in allowed_types:
            raise ValueError(f"analysis_type must be one of {allowed_types}")
        return v

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Financial query")
    analysis_id: Optional[str] = Field(None, description="ID of previous analysis to reference")

class AnalysisResponse(BaseModel):
    status: str
    analysis_id: str
    timestamp: datetime
    file_name: str
    document_type: Optional[str] = None
    company_name: Optional[str] = None
    time_period: Optional[str] = None
    overall_grade: Optional[str] = None
    overall_score: Optional[float] = None
    key_insights: List[str] = []
    financial_ratios: Dict[str, float] = {}
    performance_summary: Dict[str, Any] = {}
    risk_indicators: List[str] = []
    recommendations: List[str] = []
    error_message: Optional[str] = None

class QueryResponse(BaseModel):
    status: str
    query: str
    answer: str
    timestamp: datetime
    analysis_referenced: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"
    openai_configured: bool

# Global variables
settings = Settings()
analysis_cache: Dict[str, Dict[str, Any]] = {}

# Lifespan event manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Financial Analysis API")
    logger.info(f"OpenAI API Key configured: {bool(settings.openai_api_key)}")
    logger.info(f"Max file size: {settings.max_file_size / (1024*1024)}MB")
    logger.info(f"Supported formats: {', '.join(settings.allowed_extensions)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Financial Analysis API")
    # Clean up any remaining temporary files
    try:
        temp_dir = tempfile.gettempdir()
        for item in os.listdir(temp_dir):
            if item.startswith('tmp') and os.path.isdir(os.path.join(temp_dir, item)):
                import shutil
                shutil.rmtree(os.path.join(temp_dir, item), ignore_errors=True)
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

# FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Production-ready Financial Analysis API for Indian Markets",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Utility functions
def validate_file_extension(filename: str) -> bool:
    """Validate file extension"""
    return any(filename.lower().endswith(ext) for ext in settings.allowed_extensions)

def generate_analysis_id() -> str:
    """Generate unique analysis ID"""
    return f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"

async def save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded file to temporary location"""
    if file.size > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_file_size / (1024*1024)}MB"
        )
    
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed: {', '.join(settings.allowed_extensions)}"
        )
    
    # Create temporary file
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file.filename)
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    logger.info(f"File saved: {file_path} ({file.size} bytes)")
    return file_path

def cleanup_file(file_path: str):
    """Clean up temporary file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            # Also remove temp directory if empty
            temp_dir = os.path.dirname(file_path)
            if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                os.rmdir(temp_dir)
        logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {str(e)}")

async def perform_analysis(file_path: str, analysis_id: str, file_name: str) -> Dict[str, Any]:
    """Perform financial analysis"""
    try:
        # Validate environment
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        # Set environment variable for the crew
        os.environ['OPENAI_API_KEY'] = settings.openai_api_key
        
        # Initialize crew
        crew = FinancialAnalysisCrew(file_path=file_path)
        
        # Run analysis
        logger.info(f"Starting analysis for {analysis_id}")
        result = crew.run()
        
        # Process result
        if result.get("status") == "completed":
            analysis_data = {
                "status": "success",
                "analysis_id": analysis_id,
                "timestamp": datetime.now(),
                "file_name": file_name,
                "document_type": result.get("document_type"),
                "company_name": result.get("tool_analysis", {}).get("analysis", {}).get("company_name"),
                "time_period": result.get("tool_analysis", {}).get("analysis", {}).get("time_period"),
                "overall_grade": result.get("performance_summary", {}).get("grade"),
                "overall_score": result.get("performance_summary", {}).get("overall_score"),
                "key_insights": result.get("key_insights", []),
                "financial_ratios": result.get("financial_ratios", {}),
                "performance_summary": result.get("performance_summary", {}),
                "risk_indicators": result.get("risk_indicators", []),
                "recommendations": result.get("recommendations", []),
                "crew_output": str(result.get("crew_output", "")),
                "tool_analysis": result.get("tool_analysis", {})
            }
        else:
            # Handle error case
            analysis_data = {
                "status": "error",
                "analysis_id": analysis_id,
                "timestamp": datetime.now(),
                "file_name": file_name,
                "error_message": result.get("error_message", "Analysis failed"),
                "error_type": result.get("error_type", "unknown_error")
            }
        
        # Cache the result
        analysis_cache[analysis_id] = analysis_data
        logger.info(f"Analysis completed for {analysis_id}: {analysis_data.get('status')}")
        
        return analysis_data
        
    except Exception as e:
        logger.error(f"Analysis error for {analysis_id}: {str(e)}")
        error_data = {
            "status": "error",
            "analysis_id": analysis_id,
            "timestamp": datetime.now(),
            "file_name": file_name,
            "error_message": str(e),
            "error_type": "analysis_error"
        }
        analysis_cache[analysis_id] = error_data
        return error_data
    
    finally:
        # Always cleanup file
        cleanup_file(file_path)

# API Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        openai_configured=bool(settings.openai_api_key)
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Financial Analysis API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_financial_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Financial document to analyze"),
    analysis_type: str = "comprehensive"
):
    """
    Analyze a financial document
    
    - **file**: Upload financial document (PDF, CSV, Excel)
    - **analysis_type**: Type of analysis (comprehensive, quick, ratios_only)
    """
    try:
        # Validate request
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Generate analysis ID
        analysis_id = generate_analysis_id()
        
        # Save uploaded file
        file_path = await save_uploaded_file(file)
        
        # Start analysis in background
        background_tasks.add_task(
            perform_analysis, 
            file_path, 
            analysis_id, 
            file.filename
        )
        
        # Return immediate response
        response_data = {
            "status": "processing",
            "analysis_id": analysis_id,
            "timestamp": datetime.now(),
            "file_name": file.filename,
            "key_insights": [],
            "financial_ratios": {},
            "performance_summary": {},
            "risk_indicators": [],
            "recommendations": []
        }
        
        # Cache processing status
        analysis_cache[analysis_id] = response_data
        
        logger.info(f"Analysis started for {analysis_id}")
        return AnalysisResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_status(analysis_id: str):
    """
    Get analysis status and results
    
    - **analysis_id**: ID of the analysis to retrieve
    """
    if analysis_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis_data = analysis_cache[analysis_id]
    return AnalysisResponse(**analysis_data)

@app.post("/query", response_model=QueryResponse)
async def query_financial_data(request: QueryRequest):
    """
    Ask questions about analyzed financial data
    
    - **query**: Your financial question
    - **analysis_id**: (Optional) Reference previous analysis
    """
    try:
        # Validate environment
        if not settings.openai_api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Set environment variable
        os.environ['OPENAI_API_KEY'] = settings.openai_api_key
        
        # Get analysis context if provided
        analysis_context = None
        if request.analysis_id and request.analysis_id in analysis_cache:
            analysis_context = analysis_cache[request.analysis_id]
        
        # Initialize crew for query
        crew = FinancialAnalysisCrew()
        
        # Get answer
        answer = crew.answer_query(request.query, analysis_context)
        
        response_data = {
            "status": "success",
            "query": request.query,
            "answer": answer,
            "timestamp": datetime.now(),
            "analysis_referenced": request.analysis_id
        }
        
        logger.info(f"Query processed: {request.query[:50]}...")
        return QueryResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyses")
async def list_analyses(limit: int = 10):
    """
    List recent analyses
    
    - **limit**: Maximum number of analyses to return
    """
    analyses = []
    for analysis_id, data in sorted(
        analysis_cache.items(), 
        key=lambda x: x[1].get('timestamp', datetime.min), 
        reverse=True
    )[:limit]:
        analyses.append({
            "analysis_id": analysis_id,
            "status": data.get("status"),
            "file_name": data.get("file_name"),
            "timestamp": data.get("timestamp"),
            "document_type": data.get("document_type"),
            "overall_grade": data.get("overall_grade")
        })
    
    return {"analyses": analyses, "total": len(analyses)}

@app.delete("/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """
    Delete analysis from cache
    
    - **analysis_id**: ID of analysis to delete
    """
    if analysis_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    del analysis_cache[analysis_id]
    logger.info(f"Analysis deleted: {analysis_id}")
    return {"message": f"Analysis {analysis_id} deleted successfully"}

@app.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats"""
    return {
        "formats": settings.allowed_extensions,
        "max_file_size_mb": settings.max_file_size / (1024 * 1024)
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.now().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "timestamp": datetime.now().isoformat()},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        reload=settings.debug
    )