import asyncio
import json
import logging
import time
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlaywrightTest:
    def __init__(self, headless: bool = False, slow_mo: int = 100, timeout: int = 30000):
        self.headless = headless
        self.slow_mo = slow_mo  # Add delay between actions (ms)
        self.timeout = timeout  # Default timeout (ms)
        self.browser = None
        self.page = None

    async def setup(self):
        """Initialize browser and page with custom settings"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-notifications'
            ]
        )
        
        # Create a new browser context with viewport settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Grant permissions if needed
        await self.context.grant_permissions(['geolocation', 'notifications'])
        
        # Create a new page
        self.page = await self.context.new_page()
        
        # Set default timeout
        self.page.set_default_timeout(self.timeout)
        
        # Enable request/response logging
        self.page.on("request", lambda request: logger.debug(f"Request: {request.method} {request.url}"))
        self.page.on("response", lambda response: logger.debug(f"Response: {response.status} {response.url}"))

    async def wait_and_click(self, selector: str, timeout: Optional[int] = None):
        """Enhanced method to wait for and click an element with better error handling"""
        try:
            element = self.page.locator(selector)
            logger.debug(f"Attempting to click element: {selector}")
            
            # Wait for element to be attached to DOM
            await element.wait_for(state='attached', timeout=timeout or self.timeout)
            logger.debug(f"Element attached: {selector}")
            
            # Wait for element to be visible
            await element.wait_for(state='visible', timeout=5000)  # Shorter timeout for visibility
            logger.debug(f"Element visible: {selector}")
            
            # Scroll element into view
            await element.scroll_into_view_if_needed()
            logger.debug(f"Scrolled to element: {selector}")
            
            # Check if element is enabled
            is_disabled = await element.get_attribute('disabled')
            if is_disabled:
                logger.warning(f"Element is disabled: {selector}")
                return False
                
            # Try multiple click strategies
            try:
                # First try regular click
                await element.click(timeout=5000)
                logger.info(f"Successfully clicked element: {selector}")
                return True
            except Exception as click_error:
                logger.warning(f"Regular click failed, trying force click: {str(click_error)}")
                try:
                    await element.click(force=True, timeout=5000)
                    logger.info(f"Successfully force-clicked element: {selector}")
                    return True
                except Exception as force_click_error:
                    logger.warning(f"Force click failed, trying JavaScript click: {str(force_click_error)}")
                    try:
                        await self.page.evaluate('''(selector) => {
                            const el = document.querySelector(selector);
                            el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                        }''', selector)
                        logger.info(f"Successfully clicked element via JavaScript: {selector}")
                        return True
                    except Exception as js_error:
                        logger.error(f"JavaScript click also failed: {str(js_error)}")
                        raise js_error
                        
        except Exception as e:
            error_msg = f"Failed to click element {selector}: {str(e)}"
            logger.error(error_msg)
            timestamp = int(time.time())
            await self.page.screenshot(path=f"error_click_{timestamp}.png")
            
            # Log the element's state for debugging
            try:
                element_state = await self.page.evaluate('''(selector) => {
                    const el = document.querySelector(selector);
                    if (!el) return 'Element not found';
                    return {
                        tagName: el.tagName,
                        id: el.id,
                        className: el.className,
                        hidden: el.hidden,
                        disabled: el.disabled,
                        style: window.getComputedStyle(el).display,
                        isConnected: el.isConnected,
                        isVisible: el.offsetParent !== null
                    };
                }''', selector)
                logger.debug(f"Element state: {json.dumps(element_state, indent=2)}")
            except Exception as debug_error:
                logger.debug(f"Could not get element state: {str(debug_error)}")
                
            return False

    async def navigate_to(self, url: str, wait_until: str = 'networkidle', timeout: int = 60000):
        """Navigate to URL with better error handling"""
        try:
            response = await self.page.goto(url, wait_until=wait_until, timeout=timeout)
            if response and response.status >= 400:
                logger.warning(f"Page returned status {response.status}")
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {str(e)}")
            return False

    async def close(self):
        """Close browser and cleanup"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

async def run_test():
    test = PlaywrightTest(headless=False, slow_mo=100, timeout=30000)
    
    try:
        # Initialize browser and page
        await test.setup()
        
        # Navigate to the target page
        if not await test.navigate_to('https://www.pinterest.com/login/'):
            logger.error("Failed to navigate to Pinterest login page")
            return
            
        logger.info("Successfully navigated to Pinterest")
        
        # Wait for the page to load completely
        await test.page.wait_for_load_state('networkidle')
        
        # Handle cookie banner if present
        try:
            cookie_accept = test.page.locator('button:has-text("Accept"), button:has-text("Accept all"), [data-test-id="cookie-banner-close-button"]')
            if await cookie_accept.count() > 0:
                await cookie_accept.first.click()
                logger.info("Closed cookie banner")
                await asyncio.sleep(1)  # Wait for any animations
        except Exception as e:
            logger.warning(f"Could not find/click cookie banner: {str(e)}")
        
        # Try multiple selectors for the login form
        login_selectors = [
            'form[data-test-id="login-form"]',
            'form:has(input[type="email"])',
            'form:has(input[type="password"])',
            'button:has-text("Log in")',
            'button:has-text("Continue")',
            'div[role="dialog"]',
            'div[data-test-id="login-form"]'
        ]
        
        login_form = None
        for selector in login_selectors:
            if await test.page.locator(selector).count() > 0:
                login_form = selector
                logger.info(f"Found login form with selector: {selector}")
                break
                
        if not login_form:
            logger.error("Could not find login form with any known selectors")
            await test.page.screenshot(path="login_form_not_found.png")
            return
            
        # Fill in login credentials - try multiple possible selectors
        email_found = False
        password_found = False
        
        # Try different email input selectors
        email_selectors = [
            'input[type="email"]',
            'input[id*="email"]',
            'input[name*="email"]',
            'input[placeholder*="email"]',
            'input[data-test-id*="email"]'
        ]
        
        for selector in email_selectors:
            if await test.page.locator(selector).count() > 0:
                await test.page.fill(selector, 'your_email@example.com')
                email_found = True
                logger.info(f"Filled email using selector: {selector}")
                await asyncio.sleep(0.5)  # Small delay between actions
                break
                
        # Try different password input selectors
        password_selectors = [
            'input[type="password"]',
            'input[id*="password"]',
            'input[name*="password"]',
            'input[placeholder*="password"]',
            'input[data-test-id*="password"]'
        ]
        
        for selector in password_selectors:
            if await test.page.locator(selector).count() > 0:
                await test.page.fill(selector, 'your_password')
                password_found = True
                logger.info(f"Filled password using selector: {selector}")
                await asyncio.sleep(0.5)  # Small delay between actions
                break
                
        if not email_found or not password_found:
            logger.error("Could not find email or password fields")
            await test.page.screenshot(path="login_fields_not_found.png")
            return
            
        # Try to find and click the login button - multiple possible selectors
        login_button_selectors = [
            'button[type="submit"]',
            'button:has-text("Log in")',
            'button:has-text("Continue")',
            'button[data-test-id*="login"]',
            'div[role="button"]:has-text("Log in")',
            'button:has(div:has-text("Log in"))'
        ]
        
        login_success = False
        for selector in login_button_selectors:
            if await test.page.locator(selector).count() > 0:
                login_success = await test.wait_and_click(selector)
                if login_success:
                    logger.info(f"Clicked login button using selector: {selector}")
                    break
        if not login_success:
            logger.error("Failed to click login button")
            return
            
        # Wait for navigation after login
        await test.page.wait_for_load_state('networkidle')
        
        # Add more test steps here...
        
        logger.info("Test completed successfully")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        await test.page.screenshot(path="test_failure.png")
        raise
    finally:
        await test.close()

if __name__ == "__main__":
    asyncio.run(run_test())
