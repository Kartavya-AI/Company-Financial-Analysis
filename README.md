# 🏦 Financial Company Analysis

AI-powered financial document analysis tool specifically designed for Indian markets, leveraging CrewAI for comprehensive financial insights.

## 🚀 Features

- **📊 Comprehensive Analysis**: Automatic extraction and analysis of financial data from Indian documents
- **🎯 Key Ratios**: Calculate important financial ratios with Indian context (IndAS, Companies Act 2013)
- **⚠️ Risk Assessment**: Identify potential financial risks and red flags
- **🤖 AI Chat**: Interactive Q&A about your financial documents
- **📈 Visual Insights**: Interactive charts and performance dashboards
- **🇮🇳 Indian Market Focus**: Handles Indian number formats (lakhs, crores), regulations, and business practices

## 📋 Supported Documents

- Annual Reports (PDF)
- Quarterly Results (PDF)
- Financial Statements (CSV, Excel)
- Balance Sheets
- P&L Statements
- Cash Flow Statements

## 🛠️ Installation

### Local Development

1. **Clone the repository:**
```bash
git clone https://github.com/Kartavya-AI/Company-Financial-Analysis.git
cd Company-Financial-Analysis
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Run the Streamlit app:**
```bash
streamlit run streamlit_app.py
```

### Streamlit Cloud Deployment

1. **Fork this repository** to your GitHub account

2. **Deploy to Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your forked repository
   - Set main file path: `streamlit_app.py`
   - Click "Deploy"

## 📁 Project Structure

```
financial_analysis/
├── src/
│   └── financial_analysis/
│       ├── __init__.py
│       ├── crew.py                 # Main CrewAI implementation
│       ├── main.py                 # CLI interface
│       ├── config/
│       │   ├── agents.yaml         # Agent configurations
│       │   └── tasks.yaml          # Task configurations
│       └── tools/
│           ├── __init__.py
│           └── custom_tool.py      # Financial analysis tool
├── streamlit_app.py                # Streamlit web interface
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Project configuration
└── README.md                       # This file
```

## 🎯 Usage

### Web Interface (Streamlit)

1. **Upload Document**: Use the sidebar to upload your financial document
2. **Analyze**: Click "Analyze Document" to start AI analysis
3. **Explore Results**: Navigate through tabs for different insights
4. **AI Chat**: Ask specific questions about the analysis


## 🤖 AI Agents

The system uses three specialized AI agents:

1. **Financial Analyst (Indian Markets)**
   - Analyzes documents with Indian accounting standards
   - Understands IndAS, Companies Act 2013, SEBI regulations
   - Focuses on Indian market conditions and seasonal patterns

2. **Data Processor (Indian Formats)**
   - Extracts data from Indian financial document formats
   - Handles NSE/BSE filings, annual reports, quarterly results
   - Processes rupee denominations and Indian date formats

3. **Report Generator (Indian Context)**
   - Creates reports for Indian business environment
   - Considers GST impact, monsoon effects, festival seasons
   - Compares with Indian industry benchmarks

## 📊 Analysis Features

### Financial Ratios
- **Profitability**: Net margin, EBITDA margin, ROE, ROCE
- **Liquidity**: Current ratio, Quick ratio, Cash ratio
- **Leverage**: Debt-to-equity, Interest coverage, Debt service coverage
- **Efficiency**: Asset turnover, Working capital turnover, Inventory days

### Risk Assessment
- Liquidity risks
- Leverage risks
- Profitability concerns
- Working capital issues
- Regulatory compliance indicators

### Indian Market Specifics
- Number format handling (lakhs, crores)
- Seasonal pattern analysis
- GST impact assessment
- Regulatory compliance checking
- Industry benchmarking

## 📈 Supported Metrics

### Financial Figures
- Revenue/Sales/Turnover
- Net Income/Profit After Tax
- EBITDA
- Total Assets
- Total Liabilities
- Shareholders' Equity
- Total Debt
- Cash and Cash Equivalents
- Working Capital

### Calculated Ratios
- Profitability ratios (margins, ROE, ROA)
- Liquidity ratios (current, quick, cash)
- Leverage ratios (debt-to-equity, debt-to-assets)
- Efficiency ratios (asset turnover, working capital)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 🙏 Acknowledgments

- [CrewAI](https://crewai.com/) for the multi-agent framework
- [Streamlit](https://streamlit.io/) for the web interface
- [OpenAI](https://openai.com/) for the language models
- Indian financial regulations and standards (IndAS, Companies)