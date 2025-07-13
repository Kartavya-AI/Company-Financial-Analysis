import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.financial_analysis.crew import FinancialAnalysisCrew
import tempfile
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Financial Analysis Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: white;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        color: white;
        text-align: center;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    .upload-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed #dee2e6;
        margin-bottom: 2rem;
    }
    
    .api-key-section {
        background: #e3f2fd;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #bbdefb;
        margin-bottom: 2rem;
    }
    
    .analysis-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .sidebar .sidebar-content {
        background: #f8f9fa;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .stButton > button:disabled {
        background: #cccccc;
        transform: none;
        box-shadow: none;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 Financial Analysis Assistant</h1>
        <p>Upload your financial documents (PDF/CSV) for comprehensive analysis including Balance Sheet, P&L, Cash Flow, and Quarterly Results</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'file_uploaded' not in st.session_state:
        st.session_state.file_uploaded = False
    if 'api_key_valid' not in st.session_state:
        st.session_state.api_key_valid = False
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🔑 API Configuration")
        st.markdown("""
        **Required:** Enter your OpenAI API key to enable AI-powered analysis.
        """)
        
        # API Key input
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            help="Get your API key from https://platform.openai.com/api-keys"
        )
        
        if api_key:
            if validate_api_key(api_key):
                st.success("✅ API Key validated")
                st.session_state.api_key_valid = True
                # Set the environment variable
                os.environ['OPENAI_API_KEY'] = api_key
            else:
                st.error("❌ Invalid API Key format")
                st.session_state.api_key_valid = False
        else:
            st.session_state.api_key_valid = False
        
        st.markdown("---")
        
        st.markdown("### 📋 Instructions")
        st.markdown("""
        1. **Enter your OpenAI API key** above
        2. **Upload your financial document** (PDF or CSV)
        3. **Wait for processing** - our AI agent will analyze the data
        4. **Review insights** - get comprehensive financial analysis
        5. **Ask questions** - query specific aspects of your financials
        """)
        
        st.markdown("### 📚 Supported Documents")
        st.markdown("""
        - **Balance Sheet**
        - **Profit & Loss Statement**
        - **Cash Flow Statement**
        - **Quarterly Results**
        - **Financial CSV Data**
        """)
        
        st.markdown("### 🔍 Analysis Features")
        st.markdown("""
        - Financial ratio calculations
        - Trend analysis
        - Key performance indicators
        - Recommendations
        - Interactive visualizations
        """)
        
        st.markdown("### 🔒 Privacy & Security")
        st.markdown("""
        - Your API key is used only for this session
        - No data is stored permanently
        - All analysis happens in real-time
        """)
    
    # API Key warning if not provided
    if not st.session_state.api_key_valid:
        st.markdown("""
        <div class="warning-box">
            <strong>⚠️ API Key Required:</strong> Please enter your OpenAI API key in the sidebar to enable financial analysis.
            <br><br>
            <strong>How to get an API key:</strong>
            <ol>
                <li>Go to <a href="https://platform.openai.com/api-keys" target="_blank">OpenAI Platform</a></li>
                <li>Sign up or log in to your account</li>
                <li>Click "Create new secret key"</li>
                <li>Copy the key and paste it in the sidebar</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # File upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown("### 📁 Upload Financial Document")
    
    uploaded_file = st.file_uploader(
        "Choose a financial document",
        type=['pdf', 'csv', 'xlsx', 'xls'],
        help="Upload PDF financial statements or CSV data files",
        disabled=not st.session_state.api_key_valid
    )
    
    if uploaded_file is not None:
        # Display file information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Type", uploaded_file.type)
        with col3:
            st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
        
        # Process file button
        analyze_button_disabled = not st.session_state.api_key_valid
        if st.button("🚀 Analyze Document", key="analyze_btn", disabled=analyze_button_disabled):
            if st.session_state.api_key_valid:
                analyze_document(uploaded_file)
            else:
                st.error("Please enter a valid OpenAI API key first.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display analysis results
    if st.session_state.analysis_results:
        display_analysis_results(st.session_state.analysis_results)
    
    # Query section
    if st.session_state.analysis_results and st.session_state.api_key_valid:
        st.markdown("### 💬 Ask Questions About Your Financials")
        
        # Predefined questions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📈 What's the financial performance?"):
                handle_query("What is the overall financial performance and key metrics?")
        with col2:
            if st.button("🔍 Any areas of concern?"):
                handle_query("Are there any areas of financial concern or risk?")
        
        # Custom query
        user_query = st.text_input(
            "Or ask your own question:",
            placeholder="e.g., How is the cash flow situation?"
        )
        
        if st.button("Submit Query") and user_query:
            handle_query(user_query)

def validate_api_key(api_key):
    """Validate the format of the OpenAI API key"""
    if not api_key:
        return False
    
    # Basic format validation for OpenAI API keys
    # OpenAI API keys typically start with 'sk-' and are 51 characters long
    if api_key.startswith('sk-') and len(api_key) >= 40:
        return True
    
    return False

def analyze_document(uploaded_file):
    """Process and analyze the uploaded document"""
    with st.spinner("🔄 Analyzing your financial document..."):
        try:
            # Verify API key is still valid
            if not st.session_state.api_key_valid:
                st.error("❌ Please enter a valid OpenAI API key first.")
                return
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # Initialize crew and run analysis
            crew = FinancialAnalysisCrew(tmp_file_path)
            results = crew.run()
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
            # Check if analysis was successful
            if results.get('status') == 'error':
                st.error(f"❌ Analysis failed: {results.get('error_message', 'Unknown error')}")
                st.markdown('<div class="error-box">Please check your file format and API key, then try again.</div>', unsafe_allow_html=True)
                return
            
            # Store results in session state
            st.session_state.analysis_results = results
            st.session_state.file_uploaded = True
            
            st.success("✅ Analysis completed successfully!")
            
        except Exception as e:
            error_message = str(e)
            st.error(f"❌ Error during analysis: {error_message}")
            
            # Provide specific guidance for common errors
            if "api_key" in error_message.lower() or "authentication" in error_message.lower():
                st.markdown("""
                <div class="error-box">
                    <strong>API Key Error:</strong> Please check that your OpenAI API key is correct and has sufficient credits.
                    <br><br>
                    <strong>Troubleshooting:</strong>
                    <ul>
                        <li>Verify your API key starts with 'sk-'</li>
                        <li>Check your OpenAI account has available credits</li>
                        <li>Ensure the API key has the necessary permissions</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-box">Please check your file format and try again.</div>', unsafe_allow_html=True)

def display_analysis_results(results):
    """Display the analysis results in a structured format"""
    st.markdown("## 📊 Analysis Results")
    
    # Check if results contain an error
    if results.get('status') == 'error':
        st.error(f"Analysis failed: {results.get('error_message', 'Unknown error')}")
        return
    
    # Main metrics
    if results.get('financial_figures'):
        st.markdown("### 💰 Key Financial Metrics")
        
        # Create metrics columns
        figures = results['financial_figures']
        if isinstance(figures, dict):
            cols = st.columns(min(len(figures), 4))
            for i, (metric, value) in enumerate(figures.items()):
                with cols[i % 4]:
                    if isinstance(value, (int, float)):
                        st.metric(
                            label=metric.replace('_', ' ').title(),
                            value=format_currency(value)
                        )
    
    # Financial ratios
    if results.get('financial_ratios'):
        st.markdown("### 📈 Financial Ratios")
        
        ratios_df = pd.DataFrame(
            list(results['financial_ratios'].items()),
            columns=['Ratio', 'Value']
        )
        
        # Create a bar chart for ratios
        fig = px.bar(
            ratios_df,
            x='Ratio',
            y='Value',
            title='Financial Ratios Overview',
            color='Value',
            color_continuous_scale='Blues'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Key insights
    if results.get('key_insights'):
        st.markdown("### 🔍 Key Insights")
        for insight in results['key_insights']:
            st.markdown(f"• {insight}")
    
    # Recommendations
    if results.get('recommendations'):
        st.markdown("### 💡 Recommendations")
        for i, recommendation in enumerate(results['recommendations'], 1):
            st.markdown(f"{i}. {recommendation}")
    
    # Document type
    if results.get('document_type'):
        st.markdown("### 📄 Document Information")
        st.info(f"Document Type: {results['document_type'].title()}")
    
    # Raw analysis output
    with st.expander("🔍 Detailed Analysis Report"):
        if results.get('crew_output'):
            st.write("**Crew Analysis Output:**")
            st.write(results['crew_output'])
        
        if results.get('tool_analysis'):
            st.write("**Tool Analysis Output:**")
            st.write(results['tool_analysis'])

def handle_query(query):
    """Handle user queries about the financial data"""
    if not st.session_state.analysis_results:
        st.error("Please analyze a document first before asking questions.")
        return
    
    if not st.session_state.api_key_valid:
        st.error("Please enter a valid OpenAI API key first.")
        return
    
    with st.spinner("🤔 Processing your query..."):
        try:
            # Initialize crew for query processing
            crew = FinancialAnalysisCrew()
            response = crew.answer_query(query, st.session_state.analysis_results)
            
            # Display response
            st.markdown("### 💬 Response")
            st.markdown(f"**Query:** {query}")
            st.markdown(f"**Answer:** {response}")
            
        except Exception as e:
            error_message = str(e)
            st.error(f"Error processing query: {error_message}")
            
            if "api_key" in error_message.lower() or "authentication" in error_message.lower():
                st.markdown("""
                <div class="error-box">
                    <strong>API Key Error:</strong> There was an issue with your OpenAI API key. Please verify it's correct and try again.
                </div>
                """, unsafe_allow_html=True)

# Additional helper functions
def create_trend_chart(data, title):
    """Create a trend chart for financial data"""
    if isinstance(data, dict):
        df = pd.DataFrame(list(data.items()), columns=['Metric', 'Value'])
        fig = px.line(df, x='Metric', y='Value', title=title)
        return fig
    return None

def format_currency(value):
    """Format currency values for display"""
    if isinstance(value, (int, float)):
        if value >= 1e7:  # 1 crore
            return f"₹{value/1e7:.1f}Cr"
        elif value >= 1e5:  # 1 lakh
            return f"₹{value/1e5:.1f}L"
        elif value >= 1e3:  # 1 thousand
            return f"₹{value/1e3:.1f}K"
        else:
            return f"₹{value:.0f}"
    return str(value)

if __name__ == "__main__":
    main()