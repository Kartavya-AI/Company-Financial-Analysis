from crewai import Agent, Task, Crew, Process
from crewai_tools import FileReadTool
from src.financial_analysis.tools.custom_tool import FinancialAnalysisTool
import os
from typing import Dict, Any

class FinancialAnalysisCrew:
    def __init__(self, file_path: str = None):
        self.file_path = file_path
        self.financial_tool = FinancialAnalysisTool()
        self.file_read_tool = FileReadTool()

        self._validate_api_key()

        self.financial_analyst = self._create_financial_analyst()
        self.data_processor = self._create_data_processor()
        self.report_generator = self._create_report_generator()
    
    def _validate_api_key(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        if not api_key.startswith('sk-') or len(api_key) < 40:
            raise ValueError("Invalid OpenAI API key format.")
    
    def _create_financial_analyst(self) -> Agent:
        return Agent(
            role="Senior Financial Analyst (Indian Markets)",
            goal="Analyze financial documents with focus on Indian accounting standards, regulations, and market conditions",
            backstory =
            """You are a CA with 15+ years experience in Indian financial markets. 
            You understand IndAS, Companies Act 2013, SEBI regulations, and Indian business practices. 
            You analyze financial statements considering Indian economic conditions, seasonal patterns, 
            and regulatory requirements.""",
            tools=[self.financial_tool],
            verbose=True,
            allow_delegation=False,
            max_execution_time=300,
            llm_config={"model": "gpt-4o-mini", "temperature": 0.1, "max_tokens": 2000}
        )
    
    def _create_data_processor(self) -> Agent:
        return Agent(
            role="Financial Data Processor (Indian Formats)",
            goal="Extract and process data from Indian financial documents (annual reports, quarterly results, etc.)",
            backstory="""You specialize in Indian financial document formats including NSE/BSE 
            filings, annual reports following IndAS, RBI formats, and company announcements. 
            You handle rupee denominations, Indian date formats, and regulatory disclosures.""",
            tools=[self.financial_tool, self.file_read_tool],
            verbose=True,
            allow_delegation=False,
            max_execution_time=300,
            llm_config={"model": "gpt-4o-mini", "temperature": 0.1, "max_tokens": 2000}
        )
    
    def _create_report_generator(self) -> Agent:
        return Agent(
            role="Financial Report Generator (Indian Context)",
            goal="Generate comprehensive reports considering Indian business environment and regulatory requirements",
            backstory="""You create financial reports tailored for Indian businesses, considering 
            factors like GST impact, monsoon effects, festival seasons, regulatory compliance, 
            and comparison with Indian industry benchmarks.""",
            verbose=True,
            allow_delegation=False,
            max_execution_time=300,
            llm_config={"model": "gpt-4o-mini", "temperature": 0.2, "max_tokens": 2000}
        )
    
    def _create_analysis_task(self) -> Task:
        return Task(
            description = f"""
            Analyze the financial document at {self.file_path} with Indian market context.
            
            Focus on:
            1. Document type (Balance Sheet, P&L, Cash Flow, Quarterly Results)
            2. Key financial metrics in INR (lakhs/crores as appropriate)
            3. Important ratios:
               - Profitability: Net margin, EBITDA margin, ROE, ROCE
               - Liquidity: Current ratio, Quick ratio, Cash ratio
               - Leverage: Debt-to-equity, Interest coverage, Debt service coverage
               - Efficiency: Asset turnover, Working capital turnover, Inventory days
            4. Year-over-year growth trends
            5. Seasonal patterns (if applicable)
            6. Red flags: Declining margins, high debt, working capital issues
            7. Regulatory compliance indicators
            8. Industry-specific metrics where relevant
            
            Present figures in Indian format (lakhs/crores) and provide context.
            """,
            agent=self.financial_analyst,
            expected_output="Detailed financial analysis with Indian market context, key ratios, and growth trends."
        )
    
    def _create_processing_task(self) -> Task:
        return Task(
            description=f"""
            Process the financial document at {self.file_path} to extract structured data.
            
            Tasks:
            1. Identify document format and extract tables/figures
            2. Handle Indian number formats (lakhs, crores, thousands)
            3. Extract key financial statements data
            4. Validate data consistency and completeness
            5. Prepare data for ratio calculations
            6. Identify time periods and comparative figures
            7. Extract notes and disclosures
            8. Handle multiple currencies if present (convert to INR)
            
            Ensure all financial data is properly formatted for Indian analysis.
            """,
            agent=self.data_processor,
            expected_output="Structured financial data with Indian formatting, ready for analysis."
        )
    
    def _create_reporting_task(self) -> Task:
        return Task(
            description="""
            Generate a comprehensive financial report for Indian business stakeholders.
            
            Report structure:
            1. Executive Summary (key highlights, concerns)
            2. Financial Performance Overview
               - Revenue growth and trends
               - Profitability analysis
               - Cost structure analysis
            3. Financial Position Analysis
               - Asset quality and utilization
               - Liability management
               - Working capital analysis
            4. Key Ratios and Benchmarks
               - Compare with industry standards
               - Trend analysis over periods
            5. Cash Flow Analysis
               - Operating cash flow quality
               - Capital allocation efficiency
            6. Risk Assessment
               - Financial risks and mitigation
               - Regulatory compliance status
            7. Strategic Recommendations
               - Actionable insights for management
               - Areas for improvement
            8. Outlook and Next Steps
            
            Format for Indian business audience with clear INR figures.
            """,
            agent=self.report_generator,
            expected_output="Professional financial report with executive summary, analysis, and recommendations."
        )
    
    def run(self) -> Dict[str, Any]:
        if not self.file_path:
            raise ValueError("File path is required for analysis")
        
        try:
            self._validate_api_key()
            
            processing_task = self._create_processing_task()
            analysis_task = self._create_analysis_task()
            reporting_task = self._create_reporting_task()
            
            crew = Crew(
                agents=[self.data_processor, self.financial_analyst, self.report_generator],
                tasks=[processing_task, analysis_task, reporting_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = crew.kickoff()
            tool_result = self.financial_tool._run(self.file_path)

            combined_result = {
                "crew_output": result,
                "tool_analysis": tool_result,
                "file_path": self.file_path,
                "status": "completed"
            }

            if tool_result.get("status") == "success":
                analysis_data = tool_result.get("analysis", {})
                combined_result.update({
                    "document_type": analysis_data.get("document_type", "unknown"),
                    "key_insights": analysis_data.get("key_insights", []),
                    "financial_ratios": analysis_data.get("financial_ratios", {}),
                    "trends": analysis_data.get("trends", {}),
                    "recommendations": analysis_data.get("recommendations", []),
                    "financial_figures": tool_result.get("raw_data", {}).get("financial_figures", {}),
                    "performance_summary": analysis_data.get("performance_summary", {}),
                    "risk_indicators": analysis_data.get("risk_indicators", [])
                })
            
            return combined_result
            
        except Exception as e:
            error_message = str(e)
            
            if "api_key" in error_message.lower():
                return {
                    "status": "error",
                    "error_type": "api_key_error",
                    "error_message": "OpenAI API key authentication failed.",
                    "detailed_error": error_message,
                    "file_path": self.file_path
                }
            
            return {
                "status": "error",
                "error_type": "general_error",
                "error_message": error_message,
                "file_path": self.file_path
            }
    
    def answer_query(self, query: str, analysis_results: Dict[str, Any] = None) -> str:
        try:
            self._validate_api_key()
            
            query_agent = Agent(
                role="Financial Query Expert (Indian Markets)",
                goal="Answer specific questions about Indian financial data and provide contextual insights",
                backstory="""Expert in Indian financial analysis who can explain complex financial 
                concepts in simple terms, provide industry comparisons, and give actionable insights 
                considering Indian market conditions.""",
                verbose=True,
                allow_delegation=False,
                llm_config={"model": "gpt-4o-mini", "temperature": 0.1, "max_tokens": 1500}
            )
            
            # Create context
            context = ""
            if analysis_results:
                context = f"""
                Financial Analysis Context:
                Document Type: {analysis_results.get('document_type', 'Unknown')}
                Key Figures: {analysis_results.get('financial_figures', {})}
                Ratios: {analysis_results.get('financial_ratios', {})}
                Insights: {analysis_results.get('key_insights', [])}
                Trends: {analysis_results.get('trends', {})}
                Performance: {analysis_results.get('performance_summary', {})}
                Risk Indicators: {analysis_results.get('risk_indicators', [])}
                """
            
            query_task = Task(
                description=f"""
                Answer this financial question with Indian market context:
                
                Question: {query}
                
                Available Data:
                {context}
                
                Provide a clear, practical answer considering:
                - Indian business environment
                - Regulatory requirements
                - Industry benchmarks
                - Seasonal factors if relevant
                - Currency in INR format
                
                If data is insufficient, explain what additional information is needed.
                """,
                agent=query_agent,
                expected_output="Clear, contextual answer with practical insights for Indian business."
            )
            
            query_crew = Crew(
                agents=[query_agent],
                tasks=[query_task],
                process=Process.sequential,
                verbose=False
            )
            
            return str(query_crew.kickoff())
            
        except Exception as e:
            return f"Error answering query: {str(e)}"
    
    def update_file_path(self, new_file_path: str):
        self.file_path = new_file_path
    
    def get_supported_formats(self) -> list:
        return ['.pdf', '.csv', '.xlsx', '.xls', '.txt', '.json']
    
    def validate_file_path(self, file_path: str = None) -> Dict[str, Any]:
        path_to_check = file_path or self.file_path
        
        if not path_to_check:
            return {"valid": False, "error": "No file path provided"}
        
        if not os.path.exists(path_to_check):
            return {"valid": False, "error": "File does not exist"}
        
        _, ext = os.path.splitext(path_to_check)
        if ext.lower() not in self.get_supported_formats():
            return {"valid": False, "error": f"Unsupported format. Use: {', '.join(self.get_supported_formats())}"}
        
        try:
            file_size = os.path.getsize(path_to_check)
            if file_size > 50 * 1024 * 1024:
                return {"valid": False, "error": "File too large (max 50MB)"}
        except OSError:
            return {"valid": False, "error": "Cannot access file"}
        
        return {"valid": True, "file_path": path_to_check, "file_size": file_size, "format": ext.lower()}
    
    def get_analysis_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        if not analysis_results or analysis_results.get("status") != "completed":
            return {"status": "error", "message": "No valid analysis results"}
        
        return {
            "document_type": analysis_results.get("document_type", "Unknown"),
            "analysis_status": analysis_results.get("status", "unknown"),
            "file_analyzed": analysis_results.get("file_path", "Unknown"),
            "key_metrics_count": len(analysis_results.get("financial_ratios", {})),
            "insights_count": len(analysis_results.get("key_insights", [])),
            "recommendations_count": len(analysis_results.get("recommendations", [])),
            "has_performance_data": bool(analysis_results.get("performance_summary", {})),
            "risk_indicators": analysis_results.get("risk_indicators", []),
            "top_insights": analysis_results.get("key_insights", [])[:3],
            "critical_ratios": {k: v for k, v in analysis_results.get("financial_ratios", {}).items() if k in ["current_ratio", "debt_to_equity", "net_margin", "roe", "roce"]}
        }