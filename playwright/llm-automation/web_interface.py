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

# Enhanced CSS for better UI with theme support
st.markdown("""
<style>
    /* Theme variables */
    :root {
        --primary-color: #6366f1;
        --secondary-color: #10b981;
        --error-color: #ef4444;
        --warning-color: #f59e0b;
        --success-color: #10b981;
        --background-color: #f8fafc;
        --card-background: #ffffff;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
        --border-color: #e5e7eb;
        --shadow-color: rgba(0, 0, 0, 0.1);
        --hover-color: #f1f5f9;
    }
    
    /* Dark theme overrides */
    [data-theme='Dark'] {
        --background-color: #0e1117;
        --card-background: #1e293b;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --border-color: #334155;
        --shadow-color: rgba(0, 0, 0, 0.3);
        --hover-color: #1e293b;
    }
    
    /* Update Streamlit's default colors */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-primary);
    }
    
    /* Enhanced buttons */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary-color) 0%, #8b5cf6 100%);
        color: white;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border-radius: 12px;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.2);
        font-size: 1rem;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px -3px rgba(99, 102, 241, 0.3);
        background: linear-gradient(135deg, #5856f6 0%, #7c3aed 100%);
    }
    
    /* Status cards */
    .status-card {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        border-left: 4px solid;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .status-card.success {
        border-left-color: var(--success-color);
        background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
    }
    
    .status-card.error {
        border-left-color: var(--error-color);
        background: linear-gradient(135deg, #fef2f2 0%, #fef7f7 100%);
    }
    
    .status-card.warning {
        border-left-color: var(--warning-color);
        background: linear-gradient(135deg, #fffbeb 0%, #fefce8 100%);
    }
    
    .status-card.info {
        border-left-color: var(--primary-color);
        background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%);
    }
    
    /* Test step cards */
    .test-step {
        background: var(--card-background);
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 12px;
        box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border-left: 4px solid var(--success-color);
        transition: all 0.3s ease;
    }
    
    .test-step:hover {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }
    
    .test-step.failed {
        border-left-color: var(--error-color);
        background: linear-gradient(135deg, #fef2f2 0%, var(--card-background) 100%);
    }
    
    .test-step.running {
        border-left-color: var(--warning-color);
        background: linear-gradient(135deg, #fffbeb 0%, var(--card-background) 100%);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* Screenshot container */
    .screenshot-container {
        background: var(--card-background);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin: 1rem 0;
        border: 1px solid var(--border-color);
    }
    
    .screenshot-container img {
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
        max-width: 100%;
        height: auto;
    }
    
    .screenshot-container img:hover {
        transform: scale(1.02);
    }
    
    /* Metrics dashboard */
    .metrics-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .metric-card {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border-top: 3px solid;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card.primary { border-top-color: var(--primary-color); }
    .metric-card.success { border-top-color: var(--success-color); }
    .metric-card.error { border-top-color: var(--error-color); }
    .metric-card.warning { border-top-color: var(--warning-color); }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        color: var(--text-secondary);
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Real-time logs */
    .log-container {
        background: #1f2937;
        color: #e5e7eb;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 0.875rem;
        max-height: 300px;
        overflow-y: auto;
        margin: 1rem 0;
    }
    
    .log-entry {
        margin: 0.25rem 0;
        padding: 0.25rem 0;
        border-bottom: 1px solid #374151;
    }
    
    .log-entry:last-child {
        border-bottom: none;
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
        self.context = None
        self.page = None
        self.current_step = 0
        self.total_steps = 0
        
    async def initialize_playwright(self, headless=False):
        """Initialize Playwright with persistent Chrome profile"""
        try:
            if self.playwright is None:
                self.playwright = await async_playwright().start()
            
            if self.context is None or not self.context.pages:
                # Use persistent context with custom Chrome profile
                profile_dir = Path("/Users/harshit/Downloads/final_web_testing_playwright-main/playwright/llm-automation/custom_chrome_profile").resolve()
                
                # Create the context with persistent profile
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    headless=headless,
                    viewport={"width": 1440, "height": 900},
                    slow_mo=500,  # Add slow motion for better visibility
                    args=[
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-web-security',
                        '--disable-blink-features=AutomationControlled',
                    ]
                )
                
                # Get the first page from the persistent context
                self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
                self.test_executor = TestExecutor(self.page)
            
            return self.browser, self.playwright
            
        except Exception as e:
            st.error(f"Failed to initialize browser: {str(e)}")
            await self.cleanup()
            raise
    
    async def cleanup(self):
        """Enhanced cleanup with better error handling"""
        try:
            if self.context:
                await self.context.close()
                self.context = None
        except Exception as e:
            print(f"Error closing context: {e}")
            
        try:
            if self.browser:
                await self.browser.close()
                self.browser = None
        except Exception as e:
            print(f"Error closing browser: {e}")
            
        try:
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as e:
            print(f"Error stopping playwright: {e}")
    
    async def run_test_with_progress(self, test_description: str, progress_callback=None, log_callback=None):
        """Run test with real-time progress updates and logging"""
        results = []
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
                log_callback("🚀 Launching browser...")
            
            headless_mode = st.session_state.get('headless_mode', True)
            await self.initialize_playwright(headless=headless_mode)
            if log_callback:
                log_callback("✅ Browser ready")
            
            # Step 3: Execute test with progress tracking
            if log_callback:
                log_callback("⚡ Starting test execution...")
            
            for i, action in enumerate(test_actions, 1):
                self.current_step = i
                start_time = time.time()
                
                if progress_callback:
                    progress_callback(i, self.total_steps, f"Step {i}: {action.description}")
                
                if log_callback:
                    log_callback(f"🔄 Executing step {i}/{self.total_steps}: {action.description}")
                
                try:
                    # Execute the action with enhanced error handling
                    result = await self.execute_action_with_screenshot(action, i)
                    result['step_number'] = i
                    result['duration'] = time.time() - start_time
                    results.append(result)
                    
                    status = "✅" if result['status'] == 'passed' else "❌"
                    if log_callback:
                        log_callback(f"{status} Step {i} completed in {result['duration']:.2f}s")
                    
                except Exception as e:
                    error_result = {
                        'step_number': i,
                        'description': action.description,
                        'action_type': action.action_type,
                        'selector': action.selector,
                        'value': action.value,
                        'status': 'failed',
                        'error': str(e),
                        'duration': time.time() - start_time,
                        'screenshot': await self.capture_error_screenshot(i, action.description)
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
            return results
        finally:
            await self.cleanup()

    async def execute_action_with_screenshot(self, action: TestAction, step_number: int):
        """Execute action and capture screenshot with proper error handling"""
        try:
            # Execute the action using the backend's TestExecutor
            start_time = time.time()
            
            if action.action_type == 'navigate':
                url = action.selector if '://' in action.selector else f'https://{action.selector}'
                await self.page.goto(url, timeout=60000, wait_until='domcontentloaded')
                
            elif action.action_type == 'click':
                element = await self.page.wait_for_selector(
                    action.selector, 
                    state='visible', 
                    timeout=10000
                )
                await element.scroll_into_view_if_needed()
                await element.click()
                
            elif action.action_type == 'fill':
                await self.page.fill(action.selector, str(action.value))
                
            elif action.action_type == 'select':
                await self.page.select_option(action.selector, value=str(action.value))
                
            elif action.action_type == 'wait':
                seconds = int(action.value) if action.value else 1
                await asyncio.sleep(seconds)
                
            elif action.action_type == 'screenshot':
                pass  # Screenshot will be taken below
                
            else:
                # Use the backend's execute_action method for other actions
                await self.test_executor.execute_action(action)
            
            # Take screenshot after successful execution
            screenshot_data = await self.capture_screenshot(step_number, action.description)
            
            return {
                'description': action.description,
                'action_type': action.action_type,
                'selector': action.selector,
                'value': action.value,
                'status': 'passed',
                'screenshot': screenshot_data,
                'duration': time.time() - start_time
            }
            
        except Exception as e:
            # Capture error screenshot
            error_screenshot = await self.capture_error_screenshot(step_number, action.description)
            raise Exception(f"Action failed: {str(e)}")

    async def capture_screenshot(self, step_number: int, description: str):
        """Capture screenshot and return as base64 data"""
        try:
            if not self.page:
                return None
                
            # Take screenshot as bytes
            screenshot_bytes = await self.page.screenshot(
                full_page=True,
                type='png'
            )
            
            # Also save to file for debugging
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_desc = "".join(c if c.isalnum() or c in [' ', '_'] else '' for c in description)[:50]
            filename = f"step_{step_number:02d}_{timestamp}_{safe_desc}.png"
            
            os.makedirs('screenshots', exist_ok=True)
            filepath = os.path.join('screenshots', filename)
            
            with open(filepath, 'wb') as f:
                f.write(screenshot_bytes)
            
            return screenshot_bytes
            
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return None

    async def capture_error_screenshot(self, step_number: int, description: str):
        """Capture screenshot on error"""
        try:
            if not self.page:
                return None
                
            screenshot_bytes = await self.page.screenshot(
                full_page=True,
                type='png'
            )
            
            # Save error screenshot
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_desc = "".join(c if c.isalnum() or c in [' ', '_'] else '' for c in description)[:50]
            filename = f"error_step_{step_number:02d}_{timestamp}_{safe_desc}.png"
            
            os.makedirs('error_screenshots', exist_ok=True)
            filepath = os.path.join('error_screenshots', filename)
            
            with open(filepath, 'wb') as f:
                f.write(screenshot_bytes)
            
            return screenshot_bytes
            
        except Exception as e:
            print(f"Error capturing error screenshot: {e}")
            return None

def create_sidebar():
    """Create enhanced sidebar with settings and help"""
    with st.sidebar:
        st.markdown("#  Test Studio")
        
        # Theme selector
        theme = st.radio(
            "Theme",
            ["Light", "Dark"],
            index=0,
            horizontal=True,
            key="theme_selector"
        )
        
        # Settings
        st.markdown("### ⚙️ Settings")
        st.session_state.headless_mode = st.checkbox("Headless Mode", value=False)
        st.session_state.capture_video = st.checkbox("Record Video", value=False)
        st.session_state.slow_motion = st.slider("Slow Motion (ms)", 0, 2000, 500)
        
        # Quick examples
        st.markdown("### 💡 Example Tests")
        examples = [
            "go to arbys.com and then go to menu and in the burger select deluxe burger then go to location",
            "go to hardees.com the menu go to the breakfast section and  get me a maple biscuit",
            "go to hardees.com and in the menu check for breakfast items and open maple biscuit",
        ]
        
        selected_example = st.selectbox("Choose an example:", [""] + examples)
        if selected_example:
            st.session_state.example_selected = selected_example
        
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
    st.markdown(f"""
    <div class="metrics-container">
        <div class="metric-card primary">
            <div class="metric-label">Total Steps</div>
            <div class="metric-value">{total_steps}</div>
        </div>
        <div class="metric-card success">
            <div class="metric-label">Success Rate</div>
            <div class="metric-value">{success_rate:.1f}%</div>
        </div>
        <div class="metric-card {'error' if failed_steps > 0 else 'success'}">
            <div class="metric-label">Failed Steps</div>
            <div class="metric-value">{failed_steps}</div>
        </div>
        <div class="metric-card warning">
            <div class="metric-label">Avg Duration</div>
            <div class="metric-value">{avg_duration:.1f}s</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    progress_value = passed_steps / total_steps if total_steps > 0 else 0
    st.progress(progress_value)
    
    # Overall status
    if failed_steps == 0:
        st.markdown("""
        <div class="status-card success">
            <h3> Test Passed!</h3>
            <p>All steps executed successfully. Your application is working as expected.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="status-card error">
            <h3>⚠️ Test Issues Detected</h3>
            <p>{failed_steps} out of {total_steps} steps failed. Review the details below.</p>
        </div>
        """, unsafe_allow_html=True)

def display_enhanced_test_results(results: List[Dict[str, Any]]):
    """Display test results with enhanced visuals and proper screenshot handling"""
    if not results:
        return
    
    st.markdown("##  Test Execution Report")
    
    # Display metrics
    display_enhanced_metrics(results)
    
    # Detailed steps
    st.markdown("###  Detailed Test Steps")
    
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
    
    for result in filtered_results:
        step_number = result.get('step_number', 1)
        status = result.get('status', 'unknown')
        status_emoji = "✅" if status == 'passed' else "❌" if status == 'failed' else "⏳"
        
        # Create expandable step
        with st.expander(f"{status_emoji} Step {step_number}: {result.get('description', 'No description')}", expanded=status == 'failed'):
            col1, col2 = st.columns([2, 1])
            
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
                if result.get('selector'):
                    st.code(f"Selector: {result['selector']}")
                if result.get('value'):
                    st.code(f"Value: {result['value']}")
            
            with col2:
                # Enhanced screenshot display
                if result.get('screenshot'):
                    try:
                        screenshot_data = result['screenshot']
                        if isinstance(screenshot_data, bytes):
                            # Convert bytes to base64 for display
                            img_b64 = base64.b64encode(screenshot_data).decode()
                            st.markdown(f"""
                            <div class="screenshot-container">
                                <img src="data:image/png;base64,{img_b64}" 
                                     style="width: 100%; max-width: 400px; cursor: pointer;"
                                     onclick="window.open('data:image/png;base64,{img_b64}', '_blank')">
                                <p style="text-align: center; font-size: 0.8em; color: #666; margin-top: 0.5rem;">
                                    Step {step_number} Screenshot (Click to enlarge)
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.image(screenshot_data, 
                                   caption=f"Step {step_number}", 
                                   width=400)
                    except Exception as e:
                        st.warning(f"Could not display screenshot: {str(e)}")
                else:
                    st.info("No screenshot available for this step")

def main():
    """Enhanced main Streamlit app"""
    # Sidebar
    create_sidebar()
    
    # Main header
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-size: 3rem; margin: 0;">AI Test Automation Studio</h1>
        <p style="font-size: 1.2rem; color: #6b7280; margin: 0.5rem 0;">
            Transform natural language into automated web tests
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
    url_col, _ = st.columns([2, 3])
    with url_col:
        target_url = st.text_input(
            "Target URL:",
            placeholder="https://example.com",
            help="Enter the URL of the website you want to test"
        )
    
    # Test input section
    col1, col2 = st.columns([4, 1])
    with col1:
        test_description = st.text_area(
            "Describe your test scenario:",
            height=100,
            placeholder="e.g., Search for 'AI testing', click the first result, and verify the page title contains 'AI'",
            value=st.session_state.get('example_selected', ''),
            help="Write your test in natural language. Be specific about what actions to perform."
        )
    
    with col2:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        run_button = st.button(
            " Run Test",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.test_running
        )
        
        if st.button("🗑 Clear Results", use_container_width=True):
            st.session_state.test_results = None
            st.session_state.test_logs = []
            st.rerun()
    
    # Test execution
    if run_button and test_description.strip():
        if not target_url.strip():
            st.error("Please enter a target URL")
            st.stop()
            
        st.session_state.test_running = True
        st.session_state.test_results = None
        st.session_state.test_logs = []
        
        # Prepare full test description
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
            <div style="background: white; padding: 1rem; border-radius: 8px; margin: 1rem 0; border-left: 4px solid #6366f1;">
                <h4>Progress: {current}/{total} ({progress_value*100:.1f}%)</h4>
                <p><strong>Current Step:</strong> {message}</p>
            </div>
            """, unsafe_allow_html=True)
            progress_container.progress(progress_value)
        
        def add_log(message):
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            st.session_state.test_logs.append(f"[{timestamp}] {message}")
            
            # Display logs in real-time
            log_html = f"""
            <div class="log-container">
                {''.join([f'<div class="log-entry">{log}</div>' for log in st.session_state.test_logs[-10:]])}
            </div>
            """
            log_container.markdown(log_html, unsafe_allow_html=True)
        
        # Run the test
        async def run_test_async():
            try:
                st.session_state.test_running = True
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
                        st.success(f"Test completed successfully! All {total} steps passed.")
                    else:
                        st.error(f"Test completed with issues. {passed}/{total} steps passed.")
                
            except Exception as e:
                st.error(f"Test execution failed: {str(e)}")
                st.session_state.test_running = False
                progress_container.empty()
        
        # Execute the async function
        try:
            asyncio.run(run_test_async())
        except Exception as e:
            st.error(f"Failed to run test: {str(e)}")
            st.session_state.test_running = False
        finally:
            st.rerun()
    
    # Display results
    if st.session_state.test_results is not None:
        display_enhanced_test_results(st.session_state.test_results)
        
        # Export options
        if st.session_state.test_results:
            st.markdown("### Export Results")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Export as JSON"):
                    json_data = json.dumps(st.session_state.test_results, indent=2, default=str)
                    st.download_button(
                        "Download JSON",
                        json_data,
                        "test_results.json",
                        "application/json"
                    )
            
            with col2:
                if st.button("Generate Report"):
                    # Create a summary report
                    report = f"""# Test Execution Report
Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary
- Total Steps: {len(st.session_state.test_results)}
- Passed: {sum(1 for r in st.session_state.test_results if r.get('status') == 'passed')}
- Failed: {sum(1 for r in st.session_state.test_results if r.get('status') == 'failed')}

## Test Description
{test_description}

## Step Details
"""
                    for i, result in enumerate(st.session_state.test_results, 1):
                        report += f"\n### Step {i}: {result.get('description', 'N/A')}\n"
                        report += f"- Status: {result.get('status', 'unknown')}\n"
                        report += f"- Duration: {result.get('duration', 0):.2f}s\n"
                        if result.get('error'):
                            report += f"- Error: {result['error']}\n"
                    
                    st.download_button(
                        "Download Report",
                        report,
                        "test_report.md",
                        "text/markdown"
                    )
            
            with col3:
                if st.button("Clear Screenshots"):
                    try:
                        # Clean up screenshot directories
                        import shutil
                        if os.path.exists('screenshots'):
                            shutil.rmtree('screenshots')
                        if os.path.exists('error_screenshots'):
                            shutil.rmtree('error_screenshots')
                        st.success("Screenshot directories cleared!")
                    except Exception as e:
                        st.error(f"Failed to clear screenshots: {e}")

    # Footer with system info
    with st.expander("System Information"):
        st.markdown(f"""
        **Environment Details:**
        - Python Version: {sys.version}
        - Streamlit Version: {st.__version__}
        - Screenshot Directory: `{os.path.abspath('screenshots')}`
        - Error Screenshot Directory: `{os.path.abspath('error_screenshots')}`
        
        **Current Settings:**
        - Headless Mode: {st.session_state.get('headless_mode', False)}
        - Video Recording: {st.session_state.get('capture_video', False)}
        - Slow Motion: {st.session_state.get('slow_motion', 500)}ms
        """)

if __name__ == "__main__":
    main()