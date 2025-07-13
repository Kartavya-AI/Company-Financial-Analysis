import pandas as pd
import pdfplumber
from crewai.tools import BaseTool
import re
from typing import Dict, List, Any, Tuple
import logging
from datetime import datetime

class FinancialAnalysisTool(BaseTool):
    name: str = "Enhanced Financial Analysis Tool"
    description: str = "Analyzes Indian financial documents with comprehensive ratio analysis, trend identification, and risk assessment"
    
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        
    @property
    def indian_multipliers(self) -> Dict[str, float]:
        return {
            'crore': 10000000,
            'crores': 10000000,
            'lakh': 100000,
            'lakhs': 100000,
            'thousand': 1000,
            'thousands': 1000,
            'million': 1000000,
            'millions': 1000000,
            'billion': 1000000000,
            'billions': 1000000000
        }
    
    def _run(self, file_path: str, file_type: str = "auto") -> Dict[str, Any]:
        try:
            file_type = self._detect_file_type(file_path) if file_type == "auto" else file_type
            
            if file_type == "pdf":
                data = self._extract_from_pdf(file_path)
            elif file_type == "csv":
                data = self._extract_from_csv(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            analysis = self._analyze_financial_data(data)
            
            return {
                "status": "success",
                "file_type": file_type,
                "analysis": analysis,
                "raw_data": data
            }
            
        except Exception as e:
            self._logger.error(f"Error in financial analysis: {str(e)}")
            return {"status": "error", "error_message": str(e), "file_type": file_type}
    
    def _detect_file_type(self, file_path: str) -> str:
        ext = file_path.lower().split('.')[-1]
        return "pdf" if ext == "pdf" else "csv" if ext in ["csv", "xlsx", "xls"] else "unknown"
    
    def _extract_from_pdf(self, file_path: str) -> Dict[str, Any]:
        extracted_data = {
            "text_content": "",
            "tables": [],
            "financial_figures": {},
            "document_type": "unknown",
            "time_period": None,
            "company_name": None
        }
        
        try:
            with pdfplumber.open(file_path) as pdf:
                full_text = ""
                
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                    
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        extracted_data["tables"].extend(tables)
                
                extracted_data["text_content"] = full_text
                extracted_data["document_type"] = self._identify_document_type(full_text)
                extracted_data["financial_figures"] = self._extract_financial_figures(full_text)
                extracted_data["time_period"] = self._extract_time_period(full_text)
                extracted_data["company_name"] = self._extract_company_name(full_text)
                
        except Exception as e:
            self._logger.error(f"PDF extraction error: {str(e)}")
            raise
        
        return extracted_data
    
    def _extract_from_csv(self, file_path: str) -> Dict[str, Any]:
        try:
            df = pd.read_csv(file_path)
            
            extracted_data = {
                "dataframe": df,
                "columns": df.columns.tolist(),
                "shape": df.shape,
                "financial_figures": {},
                "document_type": "csv_data",
                "time_series": True if any(col.lower() in ['date', 'year', 'quarter', 'month'] for col in df.columns) else False
            }
            
            extracted_data["financial_figures"] = self._extract_csv_financial_figures(df)
            
            return extracted_data
            
        except Exception as e:
            self._logger.error(f"CSV extraction error: {str(e)}")
            raise
    
    def _identify_document_type(self, text: str) -> str:
        text_lower = text.lower()
        
        patterns = {
            "balance_sheet": ["balance sheet", "statement of financial position", "assets and liabilities"],
            "profit_loss": ["profit and loss", "p&l", "income statement", "statement of profit and loss"],
            "cash_flow": ["cash flow", "statement of cash flows", "cash flow statement"],
            "quarterly_results": ["quarterly results", "quarterly report", "q1", "q2", "q3", "q4"],
            "annual_report": ["annual report", "annual accounts", "director's report"]
        }
        
        for doc_type, keywords in patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return doc_type
        
        return "financial_document"
    
    def _extract_financial_figures(self, text: str) -> Dict[str, Any]:
        """Extract financial figures with Indian number format handling"""
        figures = {}
        
        patterns = {
            'revenue': r'(?:revenue|sales|turnover|income from operations)[:\s]+[₹\s]*[\s]*([\d,]+\.?\d*)\s*(?:crore|lakh|thousand|million)?',
            'net_income': r'(?:net (?:income|profit)|profit (?:after|for the) (?:tax|year)|pat)[:\s]+[₹\s]*[\s]*([\d,]+\.?\d*)\s*(?:crore|lakh|thousand|million)?',
            'ebitda': r'(?:ebitda|earnings before)[:\s]+[₹\s]*[\s]*([\d,]+\.?\d*)\s*(?:crore|lakh|thousand|million)?',
            'total_assets': r'(?:total assets)[:\s]+[₹\s]*[\s]*([\d,]+\.?\d*)\s*(?:crore|lakh|thousand|million)?',
            'total_liabilities': r'(?:total liabilities)[:\s]+[₹\s]*[\s]*([\d,]+\.?\d*)\s*(?:crore|lakh|thousand|million)?',
            'equity': r'(?:shareholders[\'\']*\s*equity|total equity)[:\s]+[₹\s]*[\s]*([\d,]+\.?\d*)\s*(?:crore|lakh|thousand|million)?',
            'debt': r'(?:total debt|borrowings|loans)[:\s]+[₹\s]*[\s]*([\d,]+\.?\d*)\s*(?:crore|lakh|thousand|million)?',
            'cash': r'(?:cash and cash equivalents|cash and bank)[:\s]+[₹\s]*[\s]*([\d,]+\.?\d*)\s*(?:crore|lakh|thousand|million)?',
            'working_capital': r'(?:working capital)[:\s]+[₹\s]*[\s]*([\d,]+\.?\d*)\s*(?:crore|lakh|thousand|million)?',
        }
        
        for key, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    value_str = matches[0].replace(',', '')
                    multiplier = self._find_multiplier(text, key)
                    
                    value = float(value_str) * multiplier
                    figures[key] = value
                    
                except (ValueError, IndexError):
                    continue
        
        return figures
    
    def _find_multiplier(self, text: str, metric: str) -> float:
        text_lower = text.lower()
        for multiplier_name, multiplier_value in self.indian_multipliers.items():
            if multiplier_name in text_lower:
                return multiplier_value
        return 100000  # Default to lakh if no multiplier found
    
    def _extract_time_period(self, text: str) -> str:
        fy_pattern = r'(?:fy|financial year|year ended|period ended)\s*[\-:]?\s*(\d{4}[\-/]?\d{2,4})'
        match = re.search(fy_pattern, text, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        quarter_pattern = r'(q[1-4]|quarter [1-4])\s*[\-:]?\s*(\d{4}[\-/]?\d{2,4})'
        match = re.search(quarter_pattern, text, re.IGNORECASE)
        
        if match:
            return f"{match.group(1)} {match.group(2)}"
        
        return None
    
    def _extract_company_name(self, text: str) -> str:
        company_pattern = r'([A-Z][a-zA-Z\s&]+(?:Limited|Ltd\.?|Private|Pvt\.?))'
        matches = re.findall(company_pattern, text)
        
        if matches:
            return matches[0].strip()
        return None
    
    def _extract_csv_financial_figures(self, df: pd.DataFrame) -> Dict[str, Any]:
        figures = {}
        financial_keywords = ['revenue', 'income', 'profit', 'assets', 'liabilities', 'cash', 'debt', 'equity', 'ebitda']
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in financial_keywords):
                if df[col].dtype in ['int64', 'float64']:
                    series_data = df[col].dropna()
                    if len(series_data) > 0:
                        figures[col] = {
                            'latest_value': series_data.iloc[-1],
                            'previous_value': series_data.iloc[-2] if len(series_data) > 1 else series_data.iloc[-1],
                            'growth_rate': self._calculate_growth_rate(series_data),
                            'trend': self._identify_trend(series_data),
                            'volatility': series_data.std() if len(series_data) > 1 else 0
                        }
        
        return figures
    
    def _calculate_growth_rate(self, series: pd.Series) -> float:
        if len(series) < 2:
            return 0.0
        
        latest = series.iloc[-1]
        previous = series.iloc[-2]
        
        if previous != 0:
            return ((latest - previous) / previous) * 100
        return 0.0
    
    def _identify_trend(self, series: pd.Series) -> str:
        if len(series) < 3:
            return 'insufficient_data'
        recent_values = series.tail(3)
        if recent_values.is_monotonic_increasing:
            return 'increasing'
        elif recent_values.is_monotonic_decreasing:
            return 'decreasing'
        else:
            return 'volatile'
    
    def _analyze_financial_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        analysis = {
            "document_type": data.get("document_type", "unknown"),
            "time_period": data.get("time_period"),
            "company_name": data.get("company_name"),
            "key_insights": [],
            "financial_ratios": {},
            "trends": {},
            "performance_summary": {},
            "risk_indicators": [],
            "recommendations": []
        }
        
        financial_figures = data.get("financial_figures", {})
        
        analysis["financial_ratios"] = self._calculate_ratios(financial_figures)
        analysis["key_insights"] = self._generate_insights(financial_figures, analysis["financial_ratios"])
        analysis["performance_summary"] = self._assess_performance(financial_figures, analysis["financial_ratios"])
        analysis["risk_indicators"] = self._identify_risks(financial_figures, analysis["financial_ratios"])
        analysis["recommendations"] = self._generate_recommendations(analysis)
        return analysis
    
    def _calculate_ratios(self, figures: Dict[str, Any]) -> Dict[str, float]:
        ratios = {}
        
        if 'revenue' in figures and 'net_income' in figures and figures['revenue'] > 0:
            ratios['net_margin'] = (figures['net_income'] / figures['revenue']) * 100
        
        if 'ebitda' in figures and 'revenue' in figures and figures['revenue'] > 0:
            ratios['ebitda_margin'] = (figures['ebitda'] / figures['revenue']) * 100
        
        if 'cash' in figures and 'debt' in figures and figures['debt'] > 0:
            ratios['cash_to_debt'] = figures['cash'] / figures['debt']
        
        if 'debt' in figures and 'equity' in figures and figures['equity'] > 0:
            ratios['debt_to_equity'] = figures['debt'] / figures['equity']
        
        if 'total_assets' in figures and 'debt' in figures and figures['total_assets'] > 0:
            ratios['debt_to_assets'] = figures['debt'] / figures['total_assets']
        
        if 'net_income' in figures and 'equity' in figures and figures['equity'] > 0:
            ratios['roe'] = (figures['net_income'] / figures['equity']) * 100
        
        if 'net_income' in figures and 'total_assets' in figures and figures['total_assets'] > 0:
            ratios['roa'] = (figures['net_income'] / figures['total_assets']) * 100
        
        if 'ebitda' in figures and 'total_assets' in figures and figures['total_assets'] > 0:
            ratios['roce'] = (figures['ebitda'] / figures['total_assets']) * 100
        
        return ratios
    
    def _generate_insights(self, figures: Dict[str, Any], ratios: Dict[str, float]) -> List[str]:
        insights = []
        
        if 'revenue' in figures:
            revenue_cr = figures['revenue'] / 10000000
            insights.append(f"Revenue: ₹{revenue_cr:.2f} crores")

        if 'net_margin' in ratios:
            margin = ratios['net_margin']
            if margin > 15:
                insights.append(f"Strong profitability with {margin:.1f}% net margin")
            elif margin > 5:
                insights.append(f"Moderate profitability with {margin:.1f}% net margin")
            else:
                insights.append(f"Low profitability with {margin:.1f}% net margin")

        if 'debt_to_equity' in ratios:
            de_ratio = ratios['debt_to_equity']
            if de_ratio > 1.5:
                insights.append(f"High leverage with D/E ratio of {de_ratio:.2f}")
            elif de_ratio > 0.5:
                insights.append(f"Moderate leverage with D/E ratio of {de_ratio:.2f}")
            else:
                insights.append(f"Conservative leverage with D/E ratio of {de_ratio:.2f}")

        if 'cash_to_debt' in ratios:
            cash_ratio = ratios['cash_to_debt']
            if cash_ratio > 0.5:
                insights.append(f"Strong liquidity position with cash-to-debt ratio of {cash_ratio:.2f}")
            else:
                insights.append(f"Tight liquidity with cash-to-debt ratio of {cash_ratio:.2f}")

        if 'roe' in ratios:
            roe = ratios['roe']
            if roe > 20:
                insights.append(f"Excellent ROE of {roe:.1f}%")
            elif roe > 10:
                insights.append(f"Good ROE of {roe:.1f}%")
            else:
                insights.append(f"Below average ROE of {roe:.1f}%")
        
        return insights
    
    def _assess_performance(self, figures: Dict[str, Any], ratios: Dict[str, float]) -> Dict[str, Any]:
        performance = {
            'overall_score': 0,
            'profitability_score': 0,
            'liquidity_score': 0,
            'leverage_score': 0,
            'efficiency_score': 0,
            'grade': 'N/A'
        }
        
        scores = []

        if 'net_margin' in ratios:
            margin = ratios['net_margin']
            if margin > 15:
                performance['profitability_score'] = 90
            elif margin > 10:
                performance['profitability_score'] = 80
            elif margin > 5:
                performance['profitability_score'] = 65
            else:
                performance['profitability_score'] = 40
            scores.append(performance['profitability_score'])

        if 'cash_to_debt' in ratios:
            cash_ratio = ratios['cash_to_debt']
            if cash_ratio > 0.5:
                performance['liquidity_score'] = 85
            elif cash_ratio > 0.2:
                performance['liquidity_score'] = 70
            else:
                performance['liquidity_score'] = 50
            scores.append(performance['liquidity_score'])

        if 'debt_to_equity' in ratios:
            de_ratio = ratios['debt_to_equity']
            if de_ratio < 0.5:
                performance['leverage_score'] = 90
            elif de_ratio < 1.0:
                performance['leverage_score'] = 75
            elif de_ratio < 1.5:
                performance['leverage_score'] = 60
            else:
                performance['leverage_score'] = 40
            scores.append(performance['leverage_score'])

        if 'roe' in ratios:
            roe = ratios['roe']
            if roe > 20:
                performance['efficiency_score'] = 95
            elif roe > 15:
                performance['efficiency_score'] = 85
            elif roe > 10:
                performance['efficiency_score'] = 70
            else:
                performance['efficiency_score'] = 50
            scores.append(performance['efficiency_score'])
 
        if scores:
            performance['overall_score'] = sum(scores) / len(scores)
            if performance['overall_score'] >= 85:
                performance['grade'] = 'A'
            elif performance['overall_score'] >= 75:
                performance['grade'] = 'B'
            elif performance['overall_score'] >= 60:
                performance['grade'] = 'C'
            elif performance['overall_score'] >= 50:
                performance['grade'] = 'D'
            else:
                performance['grade'] = 'F'
        
        return performance
    
    def _identify_risks(self, figures: Dict[str, Any], ratios: Dict[str, float]) -> List[str]:
        risks = []
        
        if 'cash_to_debt' in ratios and ratios['cash_to_debt'] < 0.2:
            risks.append("HIGH LIQUIDITY RISK: Low cash relative to debt obligations")

        if 'debt_to_equity' in ratios and ratios['debt_to_equity'] > 1.5:
            risks.append("HIGH LEVERAGE RISK: Excessive debt relative to equity")

        if 'net_margin' in ratios and ratios['net_margin'] < 3:
            risks.append("PROFITABILITY RISK: Very low profit margins")

        if 'roe' in ratios and ratios['roe'] < 8:
            risks.append("EFFICIENCY RISK: Low return on equity")

        if 'roa' in ratios and ratios['roa'] < 5:
            risks.append("ASSET UTILIZATION RISK: Poor asset productivity")

        if 'working_capital' in figures and figures['working_capital'] < 0:
            risks.append("WORKING CAPITAL RISK: Negative working capital")
        
        return risks
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        performance = analysis.get('performance_summary', {})
        ratios = analysis.get('financial_ratios', {})
        risks = analysis.get('risk_indicators', [])
        
        if performance.get('overall_score', 0) < 60:
            recommendations.append("PRIORITY: Comprehensive financial restructuring required")
        
        if performance.get('profitability_score', 0) < 70:
            recommendations.append("Focus on cost optimization and revenue enhancement strategies")
    
        if performance.get('liquidity_score', 0) < 70:
            recommendations.append("Improve cash flow management and reduce short-term debt")
        
        if 'debt_to_equity' in ratios and ratios['debt_to_equity'] > 1.0:
            recommendations.append("Consider debt reduction or equity infusion to improve leverage")
        
        if performance.get('efficiency_score', 0) < 70:
            recommendations.append("Enhance operational efficiency and asset utilization")
        
        if "HIGH LIQUIDITY RISK" in str(risks):
            recommendations.append("URGENT: Arrange additional credit facilities or sell non-core assets")
        
        if "HIGH LEVERAGE RISK" in str(risks):
            recommendations.append("URGENT: Implement debt restructuring plan")
        
        if analysis.get('document_type') == 'quarterly_results':
            recommendations.append("Monitor quarterly trends and seasonal variations")
        
        if len(recommendations) == 0:
            recommendations.append("Maintain current performance and explore growth opportunities")
        
        return recommendations
    
    def generate_report(self, analysis: Dict[str, Any]) -> str:
        report = f"""
=== FINANCIAL ANALYSIS REPORT ===

Company: {analysis.get('company_name', 'Unknown')}
Period: {analysis.get('time_period', 'Unknown')}
Document Type: {analysis.get('document_type', 'Unknown')}

=== KEY INSIGHTS ===
"""
        
        for insight in analysis.get('key_insights', []):
            report += f"• {insight}\n"
        
        report += f"""
=== PERFORMANCE SUMMARY ===
Overall Grade: {analysis.get('performance_summary', {}).get('grade', 'N/A')}
Overall Score: {analysis.get('performance_summary', {}).get('overall_score', 0):.1f}/100

Profitability Score: {analysis.get('performance_summary', {}).get('profitability_score', 0):.1f}/100
Liquidity Score: {analysis.get('performance_summary', {}).get('liquidity_score', 0):.1f}/100
Leverage Score: {analysis.get('performance_summary', {}).get('leverage_score', 0):.1f}/100
Efficiency Score: {analysis.get('performance_summary', {}).get('efficiency_score', 0):.1f}/100

=== FINANCIAL RATIOS ===
"""
        
        for ratio, value in analysis.get('financial_ratios', {}).items():
            report += f"{ratio.replace('_', ' ').title()}: {value:.2f}\n"
        
        report += "\n=== RISK INDICATORS ===\n"
        
        risks = analysis.get('risk_indicators', [])
        if risks:
            for risk in risks:
                report += f"⚠️  {risk}\n"
        else:
            report += "No significant risks identified.\n"
        
        report += "\n=== RECOMMENDATIONS ===\n"
        
        for i, rec in enumerate(analysis.get('recommendations', []), 1):
            report += f"{i}. {rec}\n"
        
        report += f"\n=== REPORT GENERATED ===\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report

if __name__ == "__main__":
    tool = FinancialAnalysisTool()