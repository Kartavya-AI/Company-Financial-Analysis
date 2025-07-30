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

## 🛠️ Installation & Deployment

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

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set environment variables:**
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

5. **Run the Streamlit app:**
```bash
streamlit run app.py
```

6. **Run the FastAPI backend:**
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Docker Deployment

The application includes a `Dockerfile` for containerized deployment:

```dockerfile
FROM python:3.11-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "-w", "1", "--threads", "2", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "api:app"]
```

**Build and run with Docker:**
```bash
# Build the image
docker build -t financial-analysis .

# Run the container
docker run -p 8080:8080 -e OPENAI_API_KEY="your-api-key" financial-analysis
```

### Google Cloud Platform (GCP) Deployment

Deploy to Google Cloud Run using the following commands:

#### Prerequisites
- Google Cloud SDK installed
- GCP project with billing enabled
- Required APIs enabled

#### Step 1: Authentication and Project Setup
```bash
# Authenticate with Google Cloud
gcloud auth login

# List available projects
gcloud projects list

# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Enable required services
gcloud services enable cloudbuild.googleapis.com artifactregistry.googleapis.com run.googleapis.com
```

#### Step 2: Create Artifact Registry Repository
```powershell
# Set variables (PowerShell syntax)
$REPO_NAME = "financial-analysis-repo"
$REGION = "us-central1"  # or your preferred region

# Create repository
gcloud artifacts repositories create $REPO_NAME `
    --repository-format=docker `
    --location=$REGION `
    --description="Financial Analysis Docker Repository"
```

#### Step 3: Build and Push Container
```powershell
# Get project ID
$PROJECT_ID = $(gcloud config get-value project)

# Set image tag
$IMAGE_TAG = "$($REGION)-docker.pkg.dev/$($PROJECT_ID)/$($REPO_NAME)/financial-analysis:latest"

# Build and push to Artifact Registry
gcloud builds submit --tag $IMAGE_TAG
```

#### Step 4: Deploy to Cloud Run
```powershell
$SERVICE_NAME = "financial-analysis-service"

gcloud run deploy $SERVICE_NAME `
    --image=$IMAGE_TAG `
    --platform=managed `
    --region=$REGION `
    --allow-unauthenticated `
    --set-env-vars="OPENAI_API_KEY=your-openai-api-key" `
    --memory=2Gi `
    --cpu=1 `
    --max-instances=10
```

#### Alternative: One-line Deploy with Environment Variables
```bash
gcloud run deploy financial-analysis-service \
    --source . \
    --region=us-central1 \
    --allow-unauthenticated \
    --set-env-vars="OPENAI_API_KEY=your-openai-api-key" \
    --memory=2Gi \
    --cpu=1
```

### Streamlit Cloud Deployment

1. **Fork this repository** to your GitHub account

2. **Deploy to Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your forked repository
   - Set main file path: `app.py`
   - Add secrets in Streamlit Cloud dashboard:
     ```toml
     [secrets]
     OPENAI_API_KEY = "your-openai-api-key"
     ```
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
├── api.py                          # FastAPI backend
├── app.py                          # Streamlit web interface
├── Dockerfile                      # Docker configuration
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Project configuration
├── GCP Deployment Commands.txt     # GCP deployment reference
└── README.md                       # This file
```

## 🎯 Usage

### Web Interface (Streamlit)

1. **Upload Document**: Use the sidebar to upload your financial document
2. **Analyze**: Click "Analyze Document" to start AI analysis
3. **Explore Results**: Navigate through tabs for different insights
4. **AI Chat**: Ask specific questions about the analysis

### API Interface (FastAPI)

**Base URL:** `http://localhost:8000` (local) or your deployed URL

**Endpoints:**

- `GET /` - Welcome message
- `POST /analyze` - Analyze company financials

**Example API Usage:**
```bash
curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{"company": "Reliance Industries"}'
```

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

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI analysis | Yes |
| `PORT` | Port for the application (default: 8080) | No |

### Docker Environment Variables

```bash
docker run -p 8080:8080 \
  -e OPENAI_API_KEY="your-api-key" \
  -e PORT=8080 \
  financial-analysis
```

### GCP Cloud Run Environment Variables

Set during deployment:
```bash
--set-env-vars="OPENAI_API_KEY=your-api-key,PORT=8080"
```

## 🚀 Performance & Scaling

### Cloud Run Configuration
- **Memory**: 2GiB (recommended for document processing)
- **CPU**: 1 vCPU
- **Max Instances**: 10 (adjust based on expected load)
- **Request Timeout**: 300 seconds (for large document processing)

### Gunicorn Configuration
- **Workers**: 1 (optimal for AI workloads)
- **Threads**: 2 (balanced for I/O operations)
- **Worker Class**: uvicorn.workers.UvicornWorker

## 🔧 Troubleshooting

### Common Issues

1. **API Key Issues**
   - Ensure OPENAI_API_KEY is set correctly
   - Verify API key has sufficient credits
   - Check API key permissions

2. **Docker Build Issues**
   - Ensure Docker daemon is running
   - Check Dockerfile syntax
   - Verify requirements.txt is present

3. **GCP Deployment Issues**
   - Verify GCP services are enabled
   - Check IAM permissions
   - Ensure billing is enabled

4. **Memory Issues**
   - Increase Cloud Run memory allocation
   - Optimize document processing for large files

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 🙏 Acknowledgments

- [CrewAI](https://crewai.com/) for the multi-agent framework
- [Streamlit](https://streamlit.io/) for the web interface
- [FastAPI](https://fastapi.tiangolo.com/) for the REST API
- [OpenAI](https://openai.com/) for the language models
- [Google Cloud Platform](https://cloud.google.com/) for hosting infrastructure
- Indian financial regulations and standards (IndAS, Companies Act)
