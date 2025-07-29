import os
from fastapi import FastAPI
from pydantic import BaseModel
from src.financial_analysis.crew import FinancialAnalysisCrew

class CompanyRequest(BaseModel):
    company: str

app = FastAPI(
    title="Financial Analysis Crew API",
    description="An API to trigger financial analysis for a given company."
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Financial Analysis API. Use the /analyze endpoint to start."}


@app.post("/analyze")
async def analyze_company(request: CompanyRequest):
    try:
        if not os.getenv("OPENAI_API_KEY"):
            return {"error": "OPENAI_API_KEY environment variable not set."}, 500

        company_name = request.company
        result = FinancialAnalysisCrew.run(company_name)
        return {"company": company_name, "analysis_report": result}

    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500