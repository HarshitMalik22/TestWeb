import streamlit as st
import asyncio
import sys
import subprocess
import datetime
import time
import base64
from typing import List, Dict, Any, Optional
from ai_test_agent import AITestAgent, TestAction, TestExecutor
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Playwright
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import threading
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="AI Test Automation Studio",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme configuration in the sidebar
def create_sidebar():
    with st.sidebar:
        st.markdown("# Test Studio")
        
        # Theme selector
        st.radio(
            "Theme",
            ["Light", "Dark"],
            index=0,
            horizontal=True,
            key="theme_selector"
        )
        
        # Quick examples
        st.markdown("### Example Tests")
        examples = [
            "Go to google.com and search for 'AI testing'",
            "Navigate to github.com, click sign up button",
            "Visit amazon.com, search for 'laptop', click first result",
            "Go to wikipedia.org, search for 'machine learning'"
        ]
        
        for example in examples:
            if st.button(example, key=f"example_{example[:10]}"):
                st.session_state.example_selected = example
                st.rerun()
        
        # Help section
        st.markdown("---")
        st.markdown("### Help")
        st.markdown("""
        - Be specific in your test descriptions
        - Include target URLs when possible
        - Use natural language to describe actions
        - Check logs for detailed execution info
        """)

# Call the sidebar function to render it
create_sidebar()

# Get the current theme
theme = st.session_state.get('theme_selector', 'Light')

# Set the theme in the session state
if 'theme' not in st.session_state:
    st.session_state.theme = theme

# Enhanced CSS with Yellow (#FAC400) and Grey (#D9D9D9) color scheme
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Theme variables with Yellow and Grey color scheme */
    :root {
        --primary-color: #FAC400;
        --primary-hover: #E6B000;
        --secondary-color: #D9D9D9;
        --accent-color: #B8B8B8;
        --error-color: #FF6B6B;
        --warning-color: #FFA726;
        --success-color: #4CAF50;
        --background-color: #F8F8F8;
        --card-background: #FFFFFF;
        --text-primary: #2C2C2C;
        --text-secondary: #5C5C5C;
        --border-color: #D9D9D9;
        --shadow-color: rgba(0, 0, 0, 0.08);
        --hover-color: #F5F5F5;
    }
    
    /* Dark theme overrides */
    [data-theme='Dark'] {
        --background-color: #1A1A1A;
        --card-background: #2C2C2C;
        --text-primary: #F8F8F8;
        --text-secondary: #B8B8B8;
        --border-color: #404040;
        --shadow-color: rgba(0, 0, 0, 0.3);
        --hover-color: #333333;
    }
    
    /* Base styling */
    * {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Update Streamlit's default colors */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-primary);
    }
    
    /* Update text colors */
    h1, h2, h3, h4, h5, h6, p, label, div, span {
        color: var(--text-primary) !important;
    }
    
    /* Update input fields */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>div,
    .stNumberInput>div>div>input {
        background-color: var(--card-background) !important;
        color: var(--text-primary) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 12px !important;
        font-weight: 400 !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput>div>div>input:focus, 
    .stTextArea>div>div>textarea:focus,
    .stSelectbox>div>div>div:focus,
    .stNumberInput>div>div>input:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(250, 196, 0, 0.2) !important;
    }
    
    /* Update sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, var(--card-background) 0%, #F9F9F9 100%) !important;
        border-right: 2px solid var(--border-color) !important;
    }
    
    /* Update sidebar text */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label {
        color: var(--text-primary) !important;
    }
    
    /* Enhanced buttons with yellow primary color */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        padding: 0.75rem 2rem !important;
        border-radius: 12px !important;
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(250, 196, 0, 0.3) !important;
        font-size: 1rem !important;
        text-transform: none !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(250, 196, 0, 0.4) !important;
        background: linear-gradient(135deg, var(--primary-hover) 0%, #CC9900 100%) !important;
    }
    
    /* Secondary buttons */
    .stButton>button:not([data-testid="baseButton-primary"]) {
        background: linear-gradient(135deg, var(--secondary-color) 0%, var(--accent-color) 100%) !important;
        color: var(--text-primary) !important;
        box-shadow: 0 4px 12px rgba(217, 217, 217, 0.3) !important;
    }
    
    .stButton>button:not([data-testid="baseButton-primary"]):hover {
        background: linear-gradient(135deg, var(--accent-color) 0%, #999999 100%) !important;
        box-shadow: 0 8px 20px rgba(217, 217, 217, 0.4) !important;
    }
    
    /* Status cards with yellow and grey theme */
    .status-card {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px var(--shadow-color);
        border-left: 4px solid;
        margin: 1rem 0;
        transition: all 0.3s ease;
        border: 1px solid var(--border-color);
    }
    
    .status-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px var(--shadow-color);
    }
    
    .status-card.success {
        border-left-color: var(--success-color);
        background: linear-gradient(135deg, #F1F8E9 0%, var(--card-background) 100%);
    }
    
    .status-card.error {
        border-left-color: var(--error-color);
        background: linear-gradient(135deg, #FFEBEE 0%, var(--card-background) 100%);
    }
    
    .status-card.warning {
        border-left-color: var(--warning-color);
        background: linear-gradient(135deg, #FFF8E1 0%, var(--card-background) 100%);
    }
    
    .status-card.info {
        border-left-color: var(--primary-color);
        background: linear-gradient(135deg, #FFFBF0 0%, var(--card-background) 100%);
    }
    
    /* Test step cards */
    .test-step {
        background: var(--card-background);
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 16px;
        box-shadow: 0 4px 20px var(--shadow-color);
        border-left: 4px solid var(--success-color);
        transition: all 0.3s ease;
        border: 1px solid var(--border-color);
    }
    
    .test-step:hover {
        box-shadow: 0 8px 30px var(--shadow-color);
        transform: translateY(-2px);
    }
    
    .test-step.failed {
        border-left-color: var(--error-color);
        background: linear-gradient(135deg, #FFEBEE 0%, var(--card-background) 100%);
    }
    
    .test-step.running {
        border-left-color: var(--primary-color);
        background: linear-gradient(135deg, #FFFBF0 0%, var(--card-background) 100%);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.9; }
    }
    
    /* Screenshot container with 60% width */
    .screenshot-container {
        background: var(--card-background);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px var(--shadow-color);
        margin: 1rem 0;
        border: 2px solid var(--border-color);
        width: 60% !important;
        max-width: 60% !important;
        margin: 1rem auto;
        text-align: center;
    }
    
    .screenshot-container img {
        border-radius: 12px;
        box-shadow: 0 6px 20px var(--shadow-color);
        transition: transform 0.3s ease;
        width: 100%;
        height: auto;
        max-width: 100%;
    }
    
    .screenshot-container img:hover {
        transform: scale(1.02);
    }
    
    .screenshot-caption {
        text-align: center;
        font-size: 0.9em;
        color: var(--text-secondary);
        margin-top: 1rem;
        font-weight: 500;
    }
    
    /* Metrics dashboard */
    .metrics-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .metric-card {
        background: var(--card-background);
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 4px 20px var(--shadow-color);
        border-top: 4px solid;
        transition: all 0.3s ease;
        border: 1px solid var(--border-color);
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px var(--shadow-color);
    }
    
    .metric-card.primary { border-top-color: var(--primary-color); }
    .metric-card.success { border-top-color: var(--success-color); }
    .metric-card.error { border-top-color: var(--error-color); }
    .metric-card.warning { border-top-color: var(--warning-color); }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0.5rem 0;
        color: var(--text-primary);
    }
    
    .metric-label {
        color: var(--text-secondary);
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* Progress indicators */
    .progress-container {
        background: var(--card-background);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 20px var(--shadow-color);
        border: 1px solid var(--border-color);
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--primary-hover) 100%) !important;
        border-radius: 10px !important;
        height: 12px !important;
    }
    
    .stProgress > div > div {
        background-color: var(--secondary-color) !important;
        border-radius: 10px !important;
        height: 12px !important;
    }
    
    /* Real-time logs */
    .log-container {
        background: linear-gradient(135deg, #2C2C2C 0%, #1A1A1A 100%);
        color: #E0E0E0;
        padding: 1.5rem;
        border-radius: 12px;
        font-family: 'JetBrains Mono', 'Courier New', monospace !important;
        font-size: 0.9rem;
        max-height: 400px;
        overflow-y: auto;
        margin: 1.5rem 0;
        border: 2px solid var(--border-color);
        box-shadow: 0 4px 20px var(--shadow-color);
    }
    
    .log-entry {
        margin: 0.5rem 0;
        padding: 0.5rem 0;
        border-bottom: 1px solid #404040;
        line-height: 1.5;
    }
    
    .log-entry:last-child {
        border-bottom: none;
    }
    
    .log-timestamp {
        color: var(--primary-color);
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    /* Main title styling */
    .main-title {
        text-align: center;
        margin-bottom: 3rem;
        padding: 2rem 0;
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .status-indicator.success {
        background: linear-gradient(135deg, #E8F5E8 0%, #C8E6C9 100%);
        color: #2E7D32;
        border: 2px solid #4CAF50;
    }
    
    .status-indicator.error {
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        color: #C62828;
        border: 2px solid #FF6B6B;
    }
    
    .status-indicator.running {
        background: linear-gradient(135deg, #FFFBF0 0%, #FFF3C4 100%);
        color: #E65100;
        border: 2px solid var(--primary-color);
    }
    
    /* Expandable sections */
    .streamlit-expanderHeader {
        background-color: var(--card-background) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
    }
    
    .streamlit-expanderContent {
        background-color: var(--card-background) !important;
        border: 2px solid var(--border-color) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
    }
    
    /* Code blocks */
    .stCode {
        border-radius: 12px !important;
        background-color: var(--secondary-color) !important;
        border: 2px solid var(--border-color) !important;
    }
    
    /* Radio buttons */
    .stRadio > div > label {
        background-color: var(--card-background) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 0.5rem 1rem !important;
        margin: 0.25rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stRadio > div > label:hover {
        background-color: var(--hover-color) !important;
        border-color: var(--primary-color) !important;
    }
    
    /* Checkboxes */
    .stCheckbox > label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        background-color: var(--card-background) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 12px !important;
    }
    
    /* Slider */
    .stSlider > div > div > div {
        background-color: var(--primary-color) !important;
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--secondary-color) 0%, var(--accent-color) 100%) !important;
        color: var(--text-primary) !important;
        border: 2px solid var(--border-color) !important;
    }
    
    /* Animation utilities */
    .fade-in {
        animation: fadeIn 0.6s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .metrics-container {
            grid-template-columns: 1fr;
        }
        
        .screenshot-container {
            width: 90% !important;
            max-width: 90% !important;
        }
        
        .metric-card {
            padding: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

class EnhancedTestRunner:
    """Enhanced test runner with real-time updates and better performance"""
    
    def __init__(self):
        self.ai_agent = AITestAgent()
        self.test_executor = None
        self.playwright = None
        self.browser = None
        self.current_step = 0
        self.total_steps = 0
        
    async def initialize_playwright(self, headless=False):
        """Initialize Playwright with optimized settings"""
        try:
            if self.playwright is None:
                self.playwright = await async_playwright().start()
            
            if self.browser is None or not self.browser.is_connected():
                # Optimized browser launch arguments
                browser_args = [
                    '--disable-dev-shm-usage',
                    '--disable-extensions',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--no-sandbox',
                    '--disable-web-security',
                ]
                
                self.browser = await self.playwright.chromium.launch(
                    headless=headless,
                    args=browser_args
                )
            
            # Optimized context settings
            context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 800},
                ignore_https_errors=True,
                record_video_dir='videos/' if os.getenv('RECORD_VIDEO') else None
            )
            
            # Set up request interception for faster loading
            await context.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2}", lambda route: route.abort())
            
            page = await context.new_page()
            self.test_executor = TestExecutor(page)
            
            return self.browser, self.playwright
            
        except Exception as e:
            st.error(f"❌ Failed to initialize browser: {str(e)}")
            await self.cleanup()
            raise
    
    async def cleanup(self):
        """Enhanced cleanup with better error handling"""
        try:
            if hasattr(self, 'browser') and self.browser:
                await self.browser.close()
                self.browser = None
        except Exception as e:
            print(f"Error closing browser: {e}")
            
        try:
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as e:
            print(f"Error stopping playwright: {e}")
    
    async def run_test_with_progress(self, test_description: str, progress_callback=None, log_callback=None):
        """Run test with real-time progress updates and logging"""
        try:
            # Step 1: Generate test actions
            if log_callback:
                log_callback("🤖 Analyzing test description...")
            
            test_actions = await self.ai_agent.generate_test_actions(test_description)
            
            if not test_actions:
                if log_callback:
                    log_callback("❌ Failed to generate test actions")
                return []
            
            self.total_steps = len(test_actions)
            if log_callback:
                log_callback(f"✅ Generated {len(test_actions)} test steps")
            
            # Step 2: Initialize browser
            if log_callback:
                log_callback("🚀 Launching optimized browser...")
            
            await self.initialize_playwright(headless=False)
            if log_callback:
                log_callback("✅ Browser ready")
            
            # Step 3: Execute test with progress tracking
            if log_callback:
                log_callback("⚡ Starting test execution...")
            
            results = []
            for i, action in enumerate(test_actions, 1):
                self.current_step = i
                
                if progress_callback:
                    progress_callback(i, self.total_steps, f"Step {i}: {action.description}")
                
                if log_callback:
                    log_callback(f"🔥 Executing step {i}/{self.total_steps}: {action.description}")
                
                try:
                    result = await self.test_executor.execute_action(action)
                    result['step_number'] = i
                    results.append(result)
                    
                    status = "✅" if result['status'] == 'passed' else "❌"
                    if log_callback:
                        log_callback(f"{status} Step {i} completed in {result.get('duration', 0):.2f}s")
                    
                except Exception as e:
                    error_result = {
                        'step_number': i,
                        'description': action.description,
                        'action_type': action.action_type,
                        'status': 'failed',
                        'error': str(e),
                        'duration': 0
                    }
                    results.append(error_result)
                    
                    if log_callback:
                        log_callback(f"❌ Step {i} failed: {str(e)}")
            
            if log_callback:
                log_callback("🎉 Test execution completed!")
            
            return results
            
        except Exception as e:
            if log_callback:
                log_callback(f"💥 Critical error: {str(e)}")
            return []
        finally:
            await self.cleanup()

def display_enhanced_metrics(results: List[Dict[str, Any]]):
    """Display enhanced metrics with better visualizations"""
    if not results:
        return
    
    total_steps = len(results)
    passed_steps = sum(1 for r in results if r.get('status') == 'passed')
    failed_steps = total_steps - passed_steps
    success_rate = (passed_steps / total_steps * 100) if total_steps > 0 else 0
    avg_duration = sum(r.get('duration', 0) for r in results) / total_steps if total_steps > 0 else 0
    
    # Metrics cards
    st.markdown("""
    <div class="metrics-container fade-in">
        <div class="metric-card primary">
            <div class="metric-label">Total Steps</div>
            <div class="metric-value">{}</div>
        </div>
        <div class="metric-card success">
            <div class="metric-label">Success Rate</div>
            <div class="metric-value">{:.1f}%</div>
        </div>
        <div class="metric-card {}">
            <div class="metric-label">Failed Steps</div>
            <div class="metric-value">{}</div>
        </div>
        <div class="metric-card warning">
            <div class="metric-label">Avg Duration</div>
            <div class="metric-value">{:.1f}s</div>
        </div>
    </div>
    """.format(
        total_steps,
        success_rate,
        "error" if failed_steps > 0 else "success",
        failed_steps,
        avg_duration
    ), unsafe_allow_html=True)
    
    # Progress bar
    progress_value = passed_steps / total_steps if total_steps > 0 else 0
    st.progress(progress_value)
    
    # Overall status
    if failed_steps == 0:
        st.markdown("""
        <div class="status-card success fade-in">
            <h3>🎉 Test Passed!</h3>
            <p>All steps executed successfully. Your application is working as expected.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="status-card error fade-in">
            <h3>⚠️ Test Issues Detected</h3>
            <p>{failed_steps} out of {total_steps} steps failed. Review the details below.</p>
        </div>
        """, unsafe_allow_html=True)

def display_enhanced_test_results(results: List[Dict[str, Any]]):
    """Display test results with enhanced visuals and interactivity"""
    if not results:
        return
    
    st.markdown("## 📊 Test Execution Report")
    
    # Display metrics
    display_enhanced_metrics(results)
    
    # Detailed steps
    st.markdown("### 📋 Detailed Test Steps")
    
    # Filter options
    col1, col2 = st.columns([3, 1])
    with col2:
        filter_option = st.selectbox(
            "Filter steps:",
            ["All Steps", "Passed Only", "Failed Only"],
            key="step_filter"
        )
    
    filtered_results = results
    if filter_option == "Passed Only":
        filtered_results = [r for r in results if r.get('status') == 'passed']
    elif filter_option == "Failed Only":
        filtered_results = [r for r in results if r.get('status') == 'failed']
    
    for i, result in enumerate(filtered_results, 1):
        step_number = result.get('step_number', i)
        status = result.get('status', 'unknown')
        status_emoji = "✅" if status == 'passed' else "❌" if status == 'failed' else "⏳"
        
        # Create expandable step
        with st.expander(f"{status_emoji} Step {step_number}: {result.get('description', 'No description')}", expanded=status == 'failed'):
            col1, col2 = st.columns([4, 6])  # Adjusted for 60% screenshot width
            
            with col1:
                # Step details
                st.markdown(f"""
                **Action Type:** `{result.get('action_type', 'unknown')}`  
                **Status:** {status_emoji} {status.upper()}  
                **Duration:** {result.get('duration', 0):.2f}s  
                """)
                
                if result.get('error'):
                    st.error(f"**Error:** {result['error']}")
                
                # Action details
                if 'selector' in result:
                    st.code(f"Selector: {result['selector']}")
                if 'value' in result and result['value']:
                    st.code(f"Value: {result['value']}")
            
            with col2:
                # Screenshot with 60% width container
                if 'screenshot' in result and result['screenshot']:
                    try:
                        # Convert bytes to base64 for display
                        if isinstance(result['screenshot'], bytes):
                            img_b64 = base64.b64encode(result['screenshot']).decode()
                            st.markdown(f"""
                            <div class="screenshot-container">
                                <img src="data:image/png;base64,{img_b64}" 
                                     style="width: 100%; max-width: 100%; height: auto;">
                                <div class="screenshot-caption">
                                    Step {step_number} Screenshot
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Use Streamlit's image function as fallback
                            st.markdown('<div class="screenshot-container">', unsafe_allow_html=True)
                            st.image(result['screenshot'], 
                                   caption=f"Step {step_number}", 
                                   use_column_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.warning(f"Could not display screenshot: {str(e)}")

def create_sidebar():
    """Create enhanced sidebar with settings and help"""
    with st.sidebar:
        st.markdown("# 🎯 Test Studio")
        
        # Theme selector
        theme = st.radio(
            "Theme",
            ["Light", "Dark"],
            index=0,
            horizontal=True,
            key="theme_selector"
        )
        
        # Quick examples
        st.markdown("### 💡 Example Tests")
        examples = [
            "Go to google.com and search for 'AI testing'",
            "Navigate to github.com, click sign up button",
            "Visit amazon.com, search for 'laptop', click first result",
            "Go to wikipedia.org, search for 'machine learning'"
        ]
        
        selected_example = st.selectbox("Choose an example:", [""] + examples)
        if selected_example:
            st.session_state.example_selected = selected_example
        
        # Settings
        st.markdown("### ⚙️ Settings")
        st.session_state.headless_mode = st.checkbox("Headless Mode", value=False)
        st.session_state.capture_video = st.checkbox("Record Video", value=False)
        st.session_state.slow_motion = st.slider("Slow Motion (ms)", 0, 2000, 500)
        
        # Help section
        with st.expander("📚 Help & Tips"):
            st.markdown("""
            **Writing Good Test Descriptions:**
            - Be specific about actions
            - Include element descriptions
            - Mention expected outcomes
            
            **Examples of good descriptions:**
            - ✅ "Click the blue 'Sign Up' button"
            - ✅ "Fill the email field with test@example.com"
            - ❌ "Do something on the page"
            """)

def main():
    """Enhanced main Streamlit app"""
    # Main header with gradient text
    st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem; padding: 2rem 0;">
        <h1 class="main-title" style="font-size: 3.5rem; margin: 0; font-weight: 700;">
            AI Test Automation Studio
        </h1>
        <p style="font-size: 1.3rem; color: var(--text-secondary); margin: 1rem 0; font-weight: 400;">
            Transform natural language into automated web tests with AI
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'test_runner' not in st.session_state:
        st.session_state.test_runner = EnhancedTestRunner()
    if 'test_results' not in st.session_state:
        st.session_state.test_results = None
    if 'test_logs' not in st.session_state:
        st.session_state.test_logs = []
    if 'test_running' not in st.session_state:
        st.session_state.test_running = False
    
    # URL input section
    st.markdown("### 🌐 Target Configuration")
    url_col, _ = st.columns([3, 2])
    with url_col:
        target_url = st.text_input(
            "Target URL:",
            placeholder="https://example.com",
            help="Enter the URL of the website you want to test"
        )
    
    # Test input section
    st.markdown("### 📝 Test Description")
    col1, col2 = st.columns([4, 1])
    with col1:
        test_description = st.text_area(
            "Describe your test scenario:",
            height=120,
            placeholder="e.g., Search for 'AI testing', click the first result, and verify the page title contains 'AI'",
            value=st.session_state.get('example_selected', ''),
            help="Write your test in natural language. Be specific about what actions to perform."
        )
    
    with col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        run_button = st.button(
            "🚀 Run Test",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.test_running
        )
        
        if st.button("🗑️ Clear Results", use_container_width=True):
            st.session_state.test_results = None
            st.session_state.test_logs = []
            st.rerun()
    
    # Test execution
    if run_button and test_description.strip():
        if test_description.strip() and target_url.strip():
            # Initialize test runner if not already done
            if st.session_state.test_runner is None:
                st.session_state.test_runner = EnhancedTestRunner()
            
            # Prepend URL navigation to test description if not already included
            if not any(word in test_description.lower() for word in ['go to', 'navigate to', 'visit']):
                full_test_description = f"Go to {target_url} and {test_description}"
            else:
                full_test_description = test_description
            
            # Progress tracking containers
            progress_container = st.empty()
            log_container = st.empty()
            
            def update_progress(current, total, message):
                progress_value = current / total if total > 0 else 0
                progress_container.markdown(f"""
                <div class="progress-container fade-in">
                    <h4 style="color: var(--primary-color); margin-bottom: 1rem;">
                        Progress: {current}/{total} ({progress_value*100:.1f}%)
                    </h4>
                    <p style="margin-bottom: 1rem;"><strong>Current Step:</strong> {message}</p>
                </div>
                """, unsafe_allow_html=True)
                progress_container.progress(progress_value)
            
            def add_log(message):
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                st.session_state.test_logs.append(f"[{timestamp}] {message}")
                
                # Display logs in real-time
                log_html = f"""
                <div class="log-container fade-in">
                    <h4 style="color: var(--primary-color); margin-bottom: 1rem;">📋 Execution Logs</h4>
                    {''.join([f'<div class="log-entry"><span class="log-timestamp">[{log.split("] ")[0].replace("[", "")}]</span> {log.split("] ", 1)[1] if "] " in log else log}</div>' for log in st.session_state.test_logs[-15:]])}
                </div>
                """
                log_container.markdown(log_html, unsafe_allow_html=True)
            
            # Set running state
            st.session_state.test_running = True
            
            # Run the test
            async def run_test_async():
                try:
                    results = await st.session_state.test_runner.run_test_with_progress(
                        full_test_description,
                        progress_callback=update_progress,
                        log_callback=add_log
                    )
                    st.session_state.test_results = results
                    st.session_state.test_running = False
                    progress_container.empty()
                    
                    # Show completion message
                    if results:
                        passed = sum(1 for r in results if r.get('status') == 'passed')
                        total = len(results)
                        if passed == total:
                            st.success(f"🎉 Test completed successfully! All {total} steps passed.")
                        else:
                            st.error(f"⚠️ Test completed with issues. {passed}/{total} steps passed.")
                    
                except Exception as e:
                    st.error(f"❌ Test execution failed: {str(e)}")
                    st.session_state.test_running = False
                    progress_container.empty()
            
            # Execute the async function
            asyncio.run(run_test_async())
            st.rerun()
    
    elif run_button:
        if not test_description.strip():
            st.warning("⚠️ Please enter a test description.")
        if not target_url.strip():
            st.warning("⚠️ Please enter a target URL.")
    
    # Display results
    if st.session_state.test_results is not None:
        st.markdown("---")
        display_enhanced_test_results(st.session_state.test_results)
        
        # Export options
        if st.session_state.test_results:
            st.markdown("### 📤 Export Options")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Export JSON", use_container_width=True):
                    json_data = json.dumps(st.session_state.test_results, indent=2, default=str)
                    st.download_button(
                        "⬇️ Download JSON",
                        json_data,
                        "test_results.json",
                        "application/json",
                        use_container_width=True
                    )
            
            with col2:
                if st.button("📊 Generate Report", use_container_width=True):
                    # Create a summary report
                    total_steps = len(st.session_state.test_results)
                    passed_steps = sum(1 for r in st.session_state.test_results if r.get('status') == 'passed')
                    failed_steps = total_steps - passed_steps
                    
                    report = f"""# 🎯 AI Test Automation Report
Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📋 Summary
- **Total Steps:** {total_steps}
- **Passed:** {passed_steps} ✅
- **Failed:** {failed_steps} ❌
- **Success Rate:** {(passed_steps/total_steps*100) if total_steps > 0 else 0:.1f}%

## 📝 Test Description
```
{test_description}
```

## 🔍 Step Details
"""
                    for i, result in enumerate(st.session_state.test_results, 1):
                        status_emoji = "✅" if result.get('status') == 'passed' else "❌"
                        report += f"\n### Step {i}: {result.get('description', 'N/A')} {status_emoji}\n"
                        report += f"- **Status:** {result.get('status', 'unknown')}\n"
                        report += f"- **Duration:** {result.get('duration', 0):.2f}s\n"
                        report += f"- **Action Type:** {result.get('action_type', 'unknown')}\n"
                        if result.get('error'):
                            report += f"- **Error:** {result['error']}\n"
                    
                    st.download_button(
                        "⬇️ Download Report",
                        report,
                        "test_report.md",
                        "text/markdown",
                        use_container_width=True
                    )
            
            with col3:
                if st.button("🔄 Run Again", use_container_width=True):
                    st.session_state.test_results = None
                    st.session_state.test_logs = []
                    st.rerun()

if __name__ == "__main__":
    main()