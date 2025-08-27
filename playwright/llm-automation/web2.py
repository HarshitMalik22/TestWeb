import streamlit as st
import asyncio
import sys
import subprocess
import datetime
import time
import base64
from typing import List, Dict, Any, Optional
# Mock classes for demonstration since the original files are not available.
# In your actual implementation, you would import these from your modules.
class TestAction:
    def __init__(self, description, action_type, selector=None, value=None):
        self.description = description
        self.action_type = action_type
        self.selector = selector
        self.value = value

class AITestAgent:
    async def generate_test_actions(self, description: str) -> List[TestAction]:
        # This is a mock implementation.
        print(f"Generating test actions for: {description}")
        await asyncio.sleep(1)
        actions = [
            TestAction("Navigate to Google", "navigate", value="https://www.google.com"),
            TestAction("Type in search bar", "type", selector="[name='q']", value="AI Test Automation"),
            TestAction("Click search button", "click", selector="[name='btnK']"),
            TestAction("Verify search results", "verify_text", selector="#search", value="AI Test Automation")
        ]
        return actions

class TestExecutor:
    def __init__(self, page):
        self.page = page

    async def execute_action(self, action: TestAction) -> Dict[str, Any]:
        # This is a mock implementation.
        start_time = time.time()
        print(f"Executing action: {action.description}")
        await asyncio.sleep(1.5) # Simulate action execution
        duration = time.time() - start_time
        
        # Simulate a screenshot
        screenshot_bytes = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")

        # Simulate success/failure
        if "fail" in action.description.lower():
             return {
                'description': action.description,
                'action_type': action.action_type,
                'status': 'failed',
                'error': 'Element not found',
                'duration': duration,
                'screenshot': screenshot_bytes
            }
        else:
            return {
                'description': action.description,
                'action_type': action.action_type,
                'status': 'passed',
                'duration': duration,
                'screenshot': screenshot_bytes
            }


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
    page_title="Enterprise AI Test Automation Studio",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Enhanced CSS with New Color Scheme ---
st.markdown("""
<style>
    /* Theme variables - Yellow and Grey */
    :root {
        --primary-color: #FAC400; /* Yellow */
        --secondary-color: #D9D9D9; /* Grey */
        --background-color: #f0f2f6; /* Lighter Grey for background */
        --card-background: #ffffff; /* White for cards */
        --text-primary: #333333; /* Dark Grey for text */
        --text-secondary: #6c757d;
        --border-color: #D9D9D9; /* Grey */
        --error-color: #ef4444;
        --success-color: #10b981;
        --shadow-color: rgba(0, 0, 0, 0.08);
    }
    
    /* Apply base styles */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-primary);
    }
    
    /* Style headers */
    h1, h2, h3 {
        color: var(--text-primary) !important;
    }
    
    /* Input fields styling */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>div {
        background-color: var(--card-background) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: var(--card-background) !important;
        border-right: 1px solid var(--border-color);
    }
    
    /* Button styling */
    .stButton>button {
        background-color: var(--primary-color) !important;
        color: var(--text-primary) !important;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px var(--shadow-color);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px var(--shadow-color);
        filter: brightness(1.05);
    }

    /* Secondary button styling */
    .stButton>button[kind="secondary"] {
        background-color: var(--secondary-color) !important;
    }
    
    /* Status cards */
    .status-card {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 var(--shadow-color);
        border-left: 5px solid;
        margin: 1rem 0;
    }
    
    .status-card.success { border-left-color: var(--success-color); }
    .status-card.error { border-left-color: var(--error-color); }
    
    /* Screenshot container - Set to 60% width and centered */
    .screenshot-container {
        width: 60%;
        margin: 1.5rem auto; /* Center the container */
        background: var(--card-background);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 8px -2px var(--shadow-color);
        border: 1px solid var(--border-color);
        text-align: center;
    }
    
    .screenshot-container img {
        border-radius: 8px;
        width: 100%; /* Image fills the container */
        height: auto;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Metrics dashboard */
    .metrics-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin: 1.5rem 0;
    }
    
    .metric-card {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 4px -1px var(--shadow-color);
        border-top: 4px solid var(--primary-color);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 8px -1px var(--shadow-color);
    }
    
    .metric-card.success { border-top-color: var(--success-color); }
    .metric-card.error { border-top-color: var(--error-color); }
    
    .metric-value {
        font-size: 2.25rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0.5rem 0;
    }
    
    .metric-label {
        color: var(--text-secondary);
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Log container for real-time logs */
    .log-container {
        background: #2b2b2b;
        color: #f1f1f1;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 0.875rem;
        height: 300px;
        overflow-y: auto;
        margin-top: 1rem;
        border: 1px solid var(--border-color);
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
        """Initialize Playwright with optimized settings and robust error handling"""
        try:
            if self.playwright is None:
                self.playwright = await async_playwright().start()
            
            if self.browser is None or not self.browser.is_connected():
                self.browser = await self.playwright.chromium.launch(headless=headless)
            
            context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 800},
                ignore_https_errors=True,
            )
            
            page = await context.new_page()
            self.test_executor = TestExecutor(page)
            
            return self.browser, self.playwright
            
        except Exception as e:
            # Provide a specific, user-friendly error message
            st.error(f"❌ Browser Initialization Failed: Could not start the testing browser. Please ensure all dependencies are installed. Details: {e}")
            await self.cleanup()
            raise  # Re-raise the exception to be caught by the main loop

    async def cleanup(self):
        """Enhanced cleanup with better error handling"""
        try:
            if hasattr(self, 'browser') and self.browser and self.browser.is_connected():
                await self.browser.close()
        except Exception as e:
            # Log cleanup errors without crashing the app
            print(f"Warning: Error closing browser during cleanup: {e}")
        finally:
            self.browser = None

        try:
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Warning: Error stopping playwright during cleanup: {e}")
        finally:
            self.playwright = None
    
    async def run_test_with_progress(self, test_description: str, progress_callback=None, log_callback=None):
        """Run test with real-time progress updates and comprehensive error handling"""
        try:
            if log_callback: log_callback("🤖 Analyzing test description...")
            test_actions = await self.ai_agent.generate_test_actions(test_description)
            
            if not test_actions:
                if log_callback: log_callback("❌ Critical Error: Failed to generate test actions from the description.")
                return []
            
            self.total_steps = len(test_actions)
            if log_callback: log_callback(f"✅ Generated {len(test_actions)} test steps.")
            
            if log_callback: log_callback("🚀 Launching browser...")
            await self.initialize_playwright(headless=False)
            if log_callback: log_callback("✅ Browser ready.")
            
            if log_callback: log_callback("⚡ Starting test execution...")
            
            results = []
            for i, action in enumerate(test_actions, 1):
                self.current_step = i
                
                if progress_callback:
                    progress_callback(i, self.total_steps, f"Step {i}: {action.description}")
                
                if log_callback: log_callback(f"🔄 Executing step {i}/{self.total_steps}: {action.description}")
                
                try:
                    result = await self.test_executor.execute_action(action)
                    result['step_number'] = i
                    results.append(result)
                    
                    status_icon = "✅" if result['status'] == 'passed' else "❌"
                    if log_callback:
                        log_callback(f"{status_icon} Step {i} completed in {result.get('duration', 0):.2f}s")
                    
                except Exception as e:
                    # This block catches errors during a single step's execution
                    error_result = {
                        'step_number': i,
                        'description': action.description,
                        'action_type': action.action_type,
                        'status': 'failed',
                        'error': f"An unexpected error occurred: {e}",
                        'duration': 0
                    }
                    results.append(error_result)
                    if log_callback: log_callback(f"❌ Step {i} failed: {e}")
            
            if log_callback: log_callback("🎉 Test execution completed!")
            return results
            
        except Exception as e:
            # This block catches critical errors during the overall test run (e.g., browser crash)
            if log_callback: log_callback(f"💥 Critical Error during test run: {e}")
            st.error(f"A critical error stopped the test execution: {e}")
            return [] # Return empty list to indicate failure
        finally:
            if log_callback: log_callback("🧹 Cleaning up resources...")
            await self.cleanup()
            if log_callback: log_callback("✅ Cleanup complete.")

def display_enhanced_metrics(results: List[Dict[str, Any]]):
    """Display enhanced metrics with the new color scheme"""
    if not results: return
    
    total = len(results)
    passed = sum(1 for r in results if r.get('status') == 'passed')
    failed = total - passed
    success_rate = (passed / total * 100) if total > 0 else 0
    avg_duration = sum(r.get('duration', 0) for r in results) / total if total > 0 else 0
    
    st.markdown(f"""
    <div class="metrics-container">
        <div class="metric-card">
            <div class="metric-label">Total Steps</div>
            <div class="metric-value">{total}</div>
        </div>
        <div class="metric-card success">
            <div class="metric-label">Success Rate</div>
            <div class="metric-value">{success_rate:.1f}%</div>
        </div>
        <div class="metric-card {'error' if failed > 0 else 'success'}">
            <div class="metric-label">Failed Steps</div>
            <div class="metric-value">{failed}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Avg. Duration</div>
            <div class="metric-value">{avg_duration:.1f}s</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_enhanced_test_results(results: List[Dict[str, Any]]):
    """Display test results with the updated screenshot width and layout"""
    if not results: return
    
    st.markdown("---")
    st.markdown("## 📊 Test Execution Report")
    display_enhanced_metrics(results)
    
    st.markdown("### 📋 Detailed Test Steps")
    
    for i, result in enumerate(results, 1):
        status = result.get('status', 'unknown')
        status_emoji = "✅" if status == 'passed' else "❌"
        
        with st.expander(f"{status_emoji} Step {result.get('step_number', i)}: {result.get('description', 'N/A')}", expanded=(status == 'failed')):
            st.markdown(f"""
            - **Action:** `{result.get('action_type', 'unknown')}`
            - **Status:** {status.upper()}
            - **Duration:** {result.get('duration', 0):.2f} seconds
            """)
            
            if result.get('error'):
                st.error(f"**Error Details:** {result['error']}")
            
            if 'screenshot' in result and result['screenshot']:
                try:
                    img_b64 = base64.b64encode(result['screenshot']).decode()
                    st.markdown(f"""
                    <div class="screenshot-container">
                        <p style="text-align: center; font-weight: bold; color: var(--text-secondary);">Screenshot</p>
                        <img src="data:image/png;base64,{img_b64}" alt="Screenshot for step {result.get('step_number', i)}">
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.warning(f"Could not display screenshot for this step. Reason: {e}")

def create_sidebar():
    """Create the application sidebar"""
    with st.sidebar:
        st.markdown("# 🎯 AI Test Studio")
        st.markdown("---")
        st.markdown("### 💡 Example Tests")
        examples = [
            "Go to google.com and search for 'AI testing'",
            "Navigate to github.com, click sign up button",
            "Visit amazon.com, search for 'laptop', click first result",
        ]
        
        selected_example = st.selectbox("Choose an example:", [""] + examples, label_visibility="collapsed")
        if selected_example:
            st.session_state.example_selected = selected_example
        
        st.markdown("---")
        with st.expander("📚 Help & Tips", expanded=True):
            st.info("Describe web interactions in plain English. The more specific you are, the better the test!")

def main():
    """Main Streamlit application logic"""
    create_sidebar()
    
    st.markdown("<h1 style='text-align: center;'>Enterprise AI Test Automation Studio</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: var(--text-secondary);'>Transform natural language into robust automated web tests.</p>", unsafe_allow_html=True)
    
    # Initialize session state variables
    if 'test_runner' not in st.session_state:
        st.session_state.test_runner = EnhancedTestRunner()
    if 'test_results' not in st.session_state:
        st.session_state.test_results = None
    if 'test_logs' not in st.session_state:
        st.session_state.test_logs = []
    if 'test_running' not in st.session_state:
        st.session_state.test_running = False

    # Main UI layout
    input_col, button_col = st.columns([4, 1])
    
    with input_col:
        test_description = st.text_area(
            "Test Scenario Description:",
            height=100,
            placeholder="e.g., Go to streamlit.io, click on the 'Docs' link, and verify the page title is 'Documentation'.",
            value=st.session_state.get('example_selected', ''),
            key="test_description_input"
        )
    
    with button_col:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True) # Align button
        run_button = st.button("▶️ Run Test", use_container_width=True, disabled=st.session_state.test_running)
        if st.button("🧹 Clear", use_container_width=True, type="secondary"):
            st.session_state.test_results = None
            st.session_state.test_logs = []
            st.session_state.example_selected = ""
            st.rerun()

    # Test execution logic
    if run_button and test_description.strip():
        st.session_state.test_running = True
        st.session_state.test_results = None
        st.session_state.test_logs = []

        progress_container = st.empty()
        log_container = st.empty()
        
        def update_progress(current, total, message):
            progress_val = current / total if total > 0 else 0
            progress_container.progress(progress_val, text=f"Executing Step {current}/{total}: {message}")
        
        def add_log(message):
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            st.session_state.test_logs.append(f"[{timestamp}] {message}")
            log_html = "<div class='log-container'>" + "".join([f"<div>{log}</div>" for log in st.session_state.test_logs]) + "</div>"
            log_container.markdown(log_html, unsafe_allow_html=True)
        
        async def run_test_async():
            try:
                results = await st.session_state.test_runner.run_test_with_progress(
                    st.session_state.test_description_input,
                    progress_callback=update_progress,
                    log_callback=add_log
                )
                st.session_state.test_results = results
            except Exception as e:
                # Final catch-all for any unhandled exceptions during the async run
                st.error(f"An unexpected critical error occurred: {e}")
                st.session_state.test_results = [] # Ensure results are not None
            finally:
                st.session_state.test_running = False
                progress_container.empty() # Clear progress bar on completion
                st.rerun() # Rerun to update UI state correctly

        asyncio.run(run_test_async())

    # Display results area
    if st.session_state.test_results is not None:
        if st.session_state.test_results:
            display_enhanced_test_results(st.session_state.test_results)
        else:
            # Handle cases where the test run produced no results (likely due to an early error)
            st.warning("The test run completed but produced no results. Check the logs for critical errors.")

if __name__ == "__main__":
    # Top-level error handling for the entire application
    try:
        main()
    except Exception as e:
        st.error("💥 An unexpected application error occurred!")
        st.exception(e)

