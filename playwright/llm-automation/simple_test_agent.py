"""
Simple Test Agent using Playwright for web testing
"""
import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class TestResult(BaseModel):
    """Test execution result"""
    success: bool
    message: str
    screenshot: Optional[bytes] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}

class SimpleTestAgent:
    """Simple test agent for web automation"""
    
    def __init__(
        self,
        page,
        base_url: Optional[str] = None,
        screenshots_dir: str = "screenshots",
        debug: bool = False
    ):
        self.page = page
        self.base_url = base_url.rstrip('/') if base_url else None
        self.screenshots_dir = Path(screenshots_dir)
        self.debug = debug
        
        # Create screenshots directory if it doesn't exist
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async def _take_screenshot(self) -> bytes:
        """Take a screenshot and return as bytes"""
        try:
            return await self.page.screenshot(full_page=True)
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}")
            return b''
    
    async def navigate(self, path: str = "") -> TestResult:
        """Navigate to a URL"""
        try:
            url = f"{self.base_url}/{path.lstrip('/')}" if self.base_url else path
            logger.info(f"Navigating to: {url}")
            await self.page.goto(url, timeout=60000)
            await self.page.wait_for_load_state("networkidle")
            
            return TestResult(
                success=True,
                message=f"Successfully navigated to {url}",
                screenshot=await self._take_screenshot()
            )
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            return TestResult(
                success=False,
                message=f"Failed to navigate to {path}",
                error=str(e),
                screenshot=await self._take_screenshot()
            )
    
    async def click(self, selector: str) -> TestResult:
        """Click on an element"""
        try:
            logger.info(f"Clicking on: {selector}")
            element = await self.page.wait_for_selector(
                selector,
                state="visible",
                timeout=10000
            )
            await element.scroll_into_view_if_needed()
            await element.click(delay=100)
            
            return TestResult(
                success=True,
                message=f"Successfully clicked on {selector}",
                screenshot=await self._take_screenshot()
            )
        except Exception as e:
            logger.error(f"Click error: {str(e)}")
            return TestResult(
                success=False,
                message=f"Failed to click on {selector}",
                error=str(e),
                screenshot=await self._take_screenshot()
            )
    
    async def fill(self, selector: str, value: str) -> TestResult:
        """Fill a form field"""
        try:
            logger.info(f"Filling {selector} with: {value}")
            await self.page.fill(selector, value)
            
            return TestResult(
                success=True,
                message=f"Successfully filled {selector} with {value}",
                screenshot=await self._take_screenshot()
            )
        except Exception as e:
            logger.error(f"Fill error: {str(e)}")
            return TestResult(
                success=False,
                message=f"Failed to fill {selector}",
                error=str(e),
                screenshot=await self._take_screenshot()
            )
    
    async def execute_test_plan(self, test_description: str) -> List[TestResult]:
        """Execute a test plan from a natural language description"""
        results = []
        
        try:
            # First, navigate to the base URL if specified
            if self.base_url:
                nav_result = await self.navigate()
                results.append(nav_result)
                if not nav_result.success:
                    return results
            
            # For now, we'll implement a simple test case directly
            # In a real-world scenario, you would parse the test_description
            # and generate appropriate actions
            
            # Example: Simple login test
            if "login" in test_description.lower():
                # Fill username
                username_result = await self.fill(
                    "input[data-test='username']",
                    "standard_user"
                )
                results.append(username_result)
                
                if not username_result.success:
                    return results
                
                # Fill password
                password_result = await self.fill(
                    "input[data-test='password']",
                    "secret_sauce"
                )
                results.append(password_result)
                
                if not password_result.success:
                    return results
                
                # Click login button
                login_result = await self.click("input[data-test='login-button']")
                results.append(login_result)
                
                # Verify login was successful
                if login_result.success:
                    try:
                        # Check if we're on the products page
                        await self.page.wait_for_selector(
                            ".inventory_list",
                            state="visible",
                            timeout=5000
                        )
                        results.append(TestResult(
                            success=True,
                            message="Successfully logged in and navigated to products page",
                            screenshot=await self._take_screenshot()
                        ))
                    except Exception as e:
                        results.append(TestResult(
                            success=False,
                            message="Failed to verify successful login",
                            error=str(e),
                            screenshot=await self._take_screenshot()
                        ))
            
            # Example: Add to cart test
            elif "add to cart" in test_description.lower():
                # First, login
                await self.fill("input[data-test='username']", "standard_user")
                await self.fill("input[data-test='password']", "secret_sauce")
                await self.click("input[data-test='login-button']")
                
                # Wait for products to load
                await self.page.wait_for_selector(".inventory_item", state="visible")
                
                # Click first add to cart button
                add_to_cart_result = await self.click("button[data-test^='add-to-cart']")
                results.append(add_to_cart_result)
                
                # Verify item was added to cart
                if add_to_cart_result.success:
                    try:
                        # Check if cart badge is visible
                        await self.page.wait_for_selector(
                            ".shopping_cart_badge",
                            state="visible",
                            timeout=3000
                        )
                        results.append(TestResult(
                            success=True,
                            message="Successfully added item to cart",
                            screenshot=await self._take_screenshot()
                        ))
                    except Exception as e:
                        results.append(TestResult(
                            success=False,
                            message="Failed to verify item was added to cart",
                            error=str(e),
                            screenshot=await self._take_screenshot()
                        ))
            
            # Default case: Just navigate to the base URL
            else:
                nav_result = await self.navigate()
                results.append(nav_result)
        
        except Exception as e:
            logger.error(f"Test execution error: {str(e)}")
            results.append(TestResult(
                success=False,
                message="Unexpected error during test execution",
                error=str(e),
                screenshot=await self._take_screenshot()
            ))
        
        return results
    
    async def close(self):
        """Clean up resources"""
        await self.page.close()

# Example usage
async def example():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        agent = SimpleTestAgent(
            page=page,
            base_url="https://www.saucedemo.com",
            debug=True
        )
        
        try:
            # Test login
            print("\n=== Testing Login ===")
            login_results = await agent.execute_test_plan("Login test")
            for i, result in enumerate(login_results, 1):
                status = "✅ PASS" if result.success else "❌ FAIL"
                print(f"Step {i}: {status} - {result.message}")
                if result.error:
                    print(f"  Error: {result.error}")
            
            # Test add to cart
            print("\n=== Testing Add to Cart ===")
            cart_results = await agent.execute_test_plan("Add to cart test")
            for i, result in enumerate(cart_results, 1):
                status = "✅ PASS" if result.success else "❌ FAIL"
                print(f"Step {i}: {status} - {result.message}")
                if result.error:
                    print(f"  Error: {result.error}")
        
        finally:
            await agent.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(example())
