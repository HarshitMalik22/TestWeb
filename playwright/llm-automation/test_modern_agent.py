"""
Test script for the modern AI test agent
"""
import asyncio
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# Add the current directory to the path so we can import our module
sys.path.append(str(Path(__file__).parent))
from modern_test_agent import TestAgent

async def run_test():
    """Run a test using the modern test agent"""
    # Configuration
    SCREENSHOTS_DIR = "test_screenshots"
    HEADLESS = False  # Set to True for CI/CD pipelines
    
    # Ensure screenshots directory exists
    Path(SCREENSHOTS_DIR).mkdir(exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser with custom profile
        PROFILE_DIR = Path("custom_chrome_profile")
        PROFILE_DIR.mkdir(exist_ok=True)
        
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=HEADLESS,
            channel="chromium"
        )
        context = browser
        
        # Create a new page
        page = await context.new_page()
        
        # Initialize the test agent
        agent = TestAgent(
            page=page,
            model_name="gpt-4-turbo",
            base_url="https://www.saucedemo.com",  # Using a demo e-commerce site for testing
            screenshots_dir=SCREENSHOTS_DIR,
            debug=True
        )
        
        try:
            # Define test scenarios
            test_scenarios = [
                {
                    "name": "Simple Navigation",
                    "description": "Navigate to the login page"
                },
                {
                    "name": "Login Test",
                    "description": "Enter 'standard_user' in the username field, 'secret_sauce' in the password field, and click the login button"
                },
                {
                    "name": "Add to Cart",
                    "description": "Click on the 'Add to cart' button for the first item"
                }
            ]
            
            # Run test scenarios
            for scenario in test_scenarios:
                print(f"\n{'='*50}")
                print(f"Running test: {scenario['name']}")
                print(f"Scenario: {scenario['description']}")
                print(f"{'='*50}")
                
                try:
                    # Execute the test scenario
                    results = await agent.execute_test_plan(scenario['description'])
                    
                    # Print results
                    if isinstance(results, list):
                        for i, result in enumerate(results, 1):
                            status = "✅ PASS" if result.success else "❌ FAIL"
                            print(f"\nStep {i}: {status}")
                            print(f"Message: {result.message}")
                            
                            if hasattr(result, 'error') and result.error:
                                print(f"Error: {result.error}")
                            
                            if hasattr(result, 'screenshot') and result.screenshot:
                                screenshot_path = Path(SCREENSHOTS_DIR) / f"{scenario['name'].lower().replace(' ', '_')}_step_{i}.png"
                                with open(screenshot_path, "wb") as f:
                                    f.write(result.screenshot)
                                print(f"Screenshot saved to: {screenshot_path}")
                    else:
                        print(f"Unexpected result format: {type(results)}")
                    
                    # Add a small delay between tests
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"\n❌ Error during test execution: {str(e)}")
                
        except Exception as e:
            print(f"\n❌ Test execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Clean up
            if 'agent' in locals():
                await agent.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())
