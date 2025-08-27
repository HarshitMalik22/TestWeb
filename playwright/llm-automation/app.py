import streamlit as st
import os
import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

# Import the HardeesTest class
from program import HardeesTest, display_test_results

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Debug: Print environment variables
print("Environment Variables:")
print(f"OPENAI_API_KEY exists: {'OPENAI_API_KEY' in os.environ}")
print(f"Current working directory: {os.getcwd()}")
print(f"Environment file exists: {os.path.exists('.env')}")

# Set page config
st.set_page_config(
    page_title="MCP Automation Tester",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main { padding: 2rem; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding: 10px 20px;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e0e2e6;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'test_cases' not in st.session_state:
    st.session_state.test_cases = []
if 'results' not in st.session_state:
    st.session_state.results = {}

# Sidebar for API configuration
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # OpenAI API Key
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        help="Get your API key from https://platform.openai.com/account/api-keys"
    )
    
    # Model selection
    model = st.selectbox(
        "Model",
        ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4"],
        index=0
    )
    
    # Test configuration
    st.subheader("Test Configuration")
    max_turns = st.number_input("Max Turns", min_value=1, max_value=50, value=10)
    
    # Save config
    if st.button("Save Configuration"):
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("Configuration saved!")

# Main content
st.title("🤖 MCP Automation Tester")
st.markdown("Automate your web testing with AI-powered test case generation and execution.")

# Tabs for different sections
tab1, tab2, tab3 = st.tabs(["📝 New Test", "📋 Test Cases", "📊 Results"])

with tab1:
    st.header("Create New Test")
    
    with st.form("test_case_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            url = st.text_input(
                "URL to Test",
                placeholder="https://example.com",
                help="Enter the URL of the web application to test"
            )
        
        with col2:
            test_name = st.text_input(
                "Test Name",
                placeholder="Login Test",
                help="Give a name to your test case"
            )
        
        test_description = st.text_area(
            "Test Description",
            placeholder="Describe what you want to test...",
            height=150,
            help="Provide a detailed description of the test case"
        )
        
        submitted = st.form_submit_button("Run Test")
        
        if submitted:
            if not url or not test_description:
                st.error("Please fill in all required fields")
            elif not api_key:
                st.error("Please enter your OpenAI API key in the sidebar")
            else:
                with st.spinner("Running test... This may take a few minutes."):
                    try:
                        # Create a unique test ID
                        test_id = f"{test_name}_{len(st.session_state.test_cases) + 1}"
                        
                        # Add to test cases
                        test_case = {
                            "id": test_id,
                            "name": test_name,
                            "url": url,
                            "description": test_description,
                            "status": "Running..."
                        }
                        
                        st.session_state.test_cases.append(test_case)
                        st.session_state.results[test_id] = {"status": "running", "output": ""}
                        
                        # Define and run the test
                        headless = not st.checkbox("Show browser", value=True)
                        
                        async def run_test(headless=True):
                            """Run the Hardee's test and return the results with screenshots"""
                            test = HardeesTest(headless=headless)
                            screenshots = []
                            try:
                                await test.setup()
                                success = await test.add_burger_to_cart()
                                
                                # Get all screenshots taken during the test
                                if os.path.exists(test.screenshot_dir):
                                    screenshot_files = sorted([f for f in os.listdir(test.screenshot_dir) 
                                                           if f.endswith('.png')])
                                    screenshots = [os.path.join(test.screenshot_dir, f) 
                                                for f in screenshot_files]
                                
                                message = "Test completed successfully!" if success else "Test failed to add burger to cart."
                                return success, message, screenshots
                                
                            except Exception as e:
                                # Capture error screenshot if possible
                                try:
                                    error_screenshot = os.path.join(test.screenshot_dir, "error.png")
                                    await test.page.screenshot(path=error_screenshot, full_page=True)
                                    if os.path.exists(error_screenshot):
                                        screenshots.append(error_screenshot)
                                except:
                                    pass
                                return False, f"Test failed with error: {str(e)}", screenshots
                                
                            finally:
                                await test.close()
                        
                        success, message, screenshots = asyncio.run(run_test(headless))
                        
                        # Display screenshots in the UI
                        if screenshots:
                            st.subheader("Test Execution Screenshots")
                            cols = st.columns(2)  # 2 columns for better layout
                            
                            for i, screenshot in enumerate(screenshots):
                                with cols[i % 2]:  # Alternate between columns
                                    st.image(screenshot, 
                                            caption=os.path.basename(screenshot).replace('_', ' ').title(),
                                            use_column_width=True)
                                    st.caption(f"Step {i+1}: {os.path.splitext(os.path.basename(screenshot))[0]}")
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                        
                        st.success("Test started! Check the 'Test Cases' tab for progress.")
                        
                    except Exception as e:
                        st.error(f"Error starting test: {str(e)}")

with tab2:
    st.header("Test Cases")
    
    if not st.session_state.test_cases:
        st.info("No test cases have been run yet. Create a new test in the 'New Test' tab.")
    else:
        for test_case in reversed(st.session_state.test_cases):
            with st.expander(f"{test_case['name']} - {test_case['status']}"):
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.write(f"**URL:** {test_case['url']}")
                    st.write(f"**Status:** {test_case['status']}")
                
                with col2:
                    if st.button(f"View Results", key=f"view_{test_case['id']}"):
                        st.session_state.selected_test = test_case['id']
                        st.rerun()

with tab3:
    st.header("Test Results")
    
    if 'selected_test' not in st.session_state or st.session_state.selected_test not in st.session_state.results:
        st.info("Select a test case from the 'Test Cases' tab to view results.")
    else:
        test_id = st.session_state.selected_test
        result = st.session_state.results[test_id]
        test_case = next((tc for tc in st.session_state.test_cases if tc["id"] == test_id), None)
        
        if test_case:
            st.subheader(f"Test: {test_case['name']}")
            st.caption(f"URL: {test_case['url']}")
            
            # Status indicator
            status_col, time_col = st.columns(2)
            with status_col:
                if result["status"] == "running":
                    st.info("⏳ Test in progress...")
                elif result["status"] == "error":
                    st.error("❌ Test Failed")
                else:
                    st.success("✅ Test Completed Successfully")
            
            # Display appropriate content based on status
            if result["status"] == "running":
                with st.spinner("Test in progress. This may take a few minutes..."):
                    st.progress(0, text="Executing test steps...")
                    st.info("Please wait while the test is being executed. This may take a few minutes.")
                    
            elif result["status"] == "error":
                # Error details section
                st.markdown("### ❌ Test Failed")
                
                # Error summary
                with st.expander("Error Details", expanded=True):
                    st.error(result["output"])
                
                # Troubleshooting section
                st.markdown("### 🛠️ Troubleshooting")
                st.markdown("""
                Here are some steps you can try to resolve the issue:
                
                1. **Check the URL**: Make sure the website is accessible and the URL is correct
                2. **Verify Test Case**: Review your test case description for any ambiguities
                3. **Check Console Logs**: Look for any error messages in the console
                4. **Retry the Test**: Sometimes transient issues can cause failures
                """)
                
                # Retry button
                if st.button("🔄 Retry This Test", key=f"retry_{test_id}"):
                    # Reset the test status and remove from results to trigger a rerun
                    test_case["status"] = "Pending"
                    del st.session_state.results[test_id]
                    st.rerun()
                
            else:  # Test completed successfully
                # Test output section
                with st.expander("📝 Test Output", expanded=True):
                    st.markdown("### Test Results")
                    st.markdown(result["output"])
                
                # Detailed results section
                if "details" in result and result["details"]:
                    with st.expander("🔍 Detailed Execution Logs"):
                        st.json(result["details"].model_dump_json())
                
                # Test summary
                st.markdown("### Test Summary")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Status", "✅ Passed")
                with col2:
                    st.metric("Test Case", test_case["name"])

# Add some spacing at the bottom
st.markdown("---")
st.markdown("### About")
st.markdown("""
This tool uses the MCP (Model Context Protocol) framework to automate web testing with AI.
It leverages OpenAI's language models to generate and execute test cases based on your descriptions.

**Note:** Make sure to have Node.js and npm installed for the MCP servers to work properly.
""")
