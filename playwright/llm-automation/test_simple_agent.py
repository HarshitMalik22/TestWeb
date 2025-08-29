"""
Test script for the SimpleTestAgent
"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright
from simple_test_agent import SimpleTestAgent, TestResult

def print_test_results(test_name: str, results: list[TestResult]):
    """Print test results in a readable format"""
    print(f"\n{'='*50}")
    print(f"Test: {test_name}")
    print(f"{'='*50}")
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result.success else "❌ FAIL"
        print(f"\nStep {i}: {status}")
        print(f"Message: {result.message}")
        
        if result.error:
            print(f"Error: {result.error}")
            
        # Save screenshot if available
        if result.screenshot:
            screenshot_path = f"test_screenshots/{test_name.lower().replace(' ', '_')}_step_{i}.png"
            Path(screenshot_dir).parent.mkdir(exist_ok=True)
            with open(screenshot_path, "wb") as f:
                f.write(result.screenshot)
            print(f"Screenshot saved to: {screenshot_path}")

async def run_test(test_name: str, test_description: str):
    """Run a single test scenario"""
    print(f"\n{'='*50}")
    print(f"Running test: {test_name}")
    print(f"Scenario: {test_description}")
    print(f"{'='*50}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        agent = SimpleTestAgent(
            page=page,
            base_url="https://www.saucedemo.com",
            screenshots_dir=screenshot_dir,
            debug=True
        )
        
        try:
            results = await agent.execute_test_plan(test_description)
            print_test_results(test_name, results)
            
            # Return True if all steps passed
            return all(result.success for result in results)
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            return False
            
        finally:
            await agent.close()
            await browser.close()

async def main():
    """Main test runner"""
    # Configuration
    global screenshot_dir
    screenshot_dir = "test_screenshots"
    
    # Ensure screenshots directory exists
    Path(screenshot_dir).mkdir(exist_ok=True)
    
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
    
    # Run all test scenarios
    results = []
    for scenario in test_scenarios:
        success = await run_test(scenario["name"], scenario["description"])
        results.append((scenario["name"], success))
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {name}")
    
    # Exit with appropriate status code
    sys.exit(0 if all(success for _, success in results) else 1)

if __name__ == "__main__":
    asyncio.run(main())
