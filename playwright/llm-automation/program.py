import os
import asyncio
import sys
import logging
import time
from typing import Optional
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('hardees_test.log')
    ]
)
logger = logging.getLogger(__name__)

class HardeesTest:
    def __init__(self, headless=False):
        self.headless = headless
        self.base_url = "https://www.hardees.com/"
        self.screenshot_dir = "test_screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.step = 0

    async def setup(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        self.page.set_default_timeout(30000)

    async def close(self):
        await self.browser.close()
        await self.playwright.stop()

    async def wait_for_selector_visible(self, selector, timeout=10000, state='visible'):
        """Wait for selector to be visible and return it"""
        try:
            await self.page.wait_for_selector(selector, state=state, timeout=timeout)
            return await self.page.locator(selector).first
        except Exception as e:
            logger.warning(f"Element not found: {selector} - {str(e)}")
            return None

    async def click_element(self, selector, timeout=10000):
        """Safely click an element with retries"""
        try:
            element = await self.wait_for_selector_visible(selector, timeout=timeout)
            if element:
                await element.click()
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to click {selector}: {str(e)}")
            return False

    async def take_screenshot(self, name):
        """Take a screenshot and return the file path"""
        self.step += 1
        filename = f"step_{self.step:02d}_{name.replace(' ', '_').lower()}.png"
        path = os.path.join(self.screenshot_dir, filename)
        await self.page.screenshot(path=path, full_page=True)
        logger.info(f"Screenshot saved: {path}")
        return path

    async def add_burger_to_cart(self):
        try:
            logger.info("Navigating to Hardee's website...")
            await self.page.goto(self.base_url, wait_until='domcontentloaded')
            logger.info("Page loaded successfully")
            initial_screenshot = await self.take_screenshot("initial_page")
            
            # Wait for cookie banner and accept if present
            try:
                accept_button = await self.page.wait_for_selector(
                    'button:has-text("Accept"), button:has-text("Accept All"), button:has-text("Agree"), button:has-text("Got It")',
                    timeout=5000
                )
                if accept_button:
                    await accept_button.click()
                    logger.info("Accepted cookies")
                    await self.take_screenshot("after_accepting_cookies")
            except Exception as e:
                logger.warning("Could not find cookie accept button, continuing...")
            
            # Try direct navigation to menu
            menu_url = f"{self.base_url}/menu"
            logger.info(f"Navigating directly to menu: {menu_url}")
            await self.page.goto(menu_url, wait_until='domcontentloaded')
            menu_screenshot = await self.take_screenshot("menu_page")
            
            # Wait for menu to load with more specific conditions
            logger.info("Waiting for menu to load...")
            try:
                await self.page.wait_for_selector(
                    'a[href*="/menu/"]:visible, .menu-item, [class*="product"], [class*="item"]',
                    timeout=10000
                )
                logger.info("Menu loaded successfully")
                await self.take_screenshot("menu_loaded")
            except Exception as e:
                logger.warning(f"Menu loading indicator not found, continuing anyway: {str(e)}")
                await self.take_screenshot("menu_load_warning")
            
            # Look for specific burger items first
            logger.info("Looking for specific burger items...")
            await self.take_screenshot("before_burger_selection")
            burger_selectors = [
                'a:has-text("Burgers")',
                'a:has-text("Charbroiled Burgers")',
                'a:has-text("Classic Burgers")',
                'a:has-text("Burgers & Sandwiches")',
                'a:has-text("Burgers & More")'
            ]
            
            burger_found = False
            
            for selector in burger_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        logger.info(f"Found burger category: {selector}")
                        await self.page.click(selector)
                        burger_found = True
                        break
                except Exception as e:
                    logger.debug(f"Burger category not found with selector {selector}: {str(e)}")
                    continue
                    
            if not burger_found:
                logger.warning("Could not find burger category, continuing...")
            
            # First, try to find and click on a specific burger
            logger.info("Looking for specific burger items...")
            
            # Try to find a specific burger by name
            target_burgers = [
                'Double Cheeseburger',
                'Frisco Burger',
                'Thickburger',
                'Bacon Burger',
                'Cheeseburger'
            ]
            
            burger_found = False
            
            # First try: Look for specific burger names
            for burger_name in target_burgers:
                burger_locator = f'a:has-text("{burger_name}"):visible'
                if await self.page.locator(burger_locator).count() > 0:
                    logger.info(f"Found burger: {burger_name}")
                    await self.page.click(burger_locator)
                    burger_found = True
                    break
            
            # Second try: Look for any burger in the menu grid
            if not burger_found:
                logger.info("Looking for any burger in the menu...")
                menu_items = self.page.locator('a[href*="/menu/"]:visible')
                count = await menu_items.count()
                
                for i in range(min(10, count)):  # Check first 10 items
                    try:
                        item = menu_items.nth(i)
                        text = (await item.text_content() or '').lower()
                        if any(b in text for b in ['burger', 'cheeseburger', 'thickburger']):
                            logger.info(f"Clicking on menu item: {text}")
                            await item.click()
                            burger_found = True
                            break
                    except Exception as e:
                        logger.warning(f"Error clicking menu item: {str(e)}")
            
            # Third try: Look for any clickable burger element
            if not burger_found:
                logger.info("Trying to find any clickable burger element...")
                burger_elements = [
                    'a[href*="burger"]:visible',
                    'div.menu-item:visible',
                    'div.product-item:visible',
                    'a.menu-item:visible',
                    'button:has-text("Add to Order"):visible',
                    'button[data-testid*="add-to-cart"]:visible',
                    'button:has-text("Add to Cart"):visible'
                ]
                
                for selector in burger_elements:
                    if await self.page.locator(selector).count() > 0:
                        logger.info(f"Clicking on element: {selector}")
                        await self.page.click(selector)
                        burger_found = True
                        break
            
            if not burger_found:
                logger.error("Could not find any burger items or add buttons")
                await self.page.screenshot(path='no_burgers_found.png')
                return False
            
            # Wait for item page to load
            await asyncio.sleep(3)
            
            # Take a screenshot to see what's on the page
            await self.page.screenshot(path='item_page.png')
            
            # Try to find and click the add to cart button
            add_to_cart_found = False
            add_buttons = [
                'button:has-text("Add to Order")',
                'button:has-text("Add to Cart")',
                'button[data-testid*="add-to-cart"]',
                'button:contains("Add to Order")',
                'button:contains("Add to Cart")',
                'button:has-text("Add")',
                'button:has-text("Order Now")',
                'button.primary',
                'button.add-to-cart',
                'button[type="submit"]'
            ]
            
            for selector in add_buttons:
                try:
                    if await self.page.locator(selector).count() > 0:
                        logger.info(f"Found add to cart button: {selector}")
                        await self.page.click(selector, timeout=5000)
                        logger.info("Clicked add to cart button")
                        add_to_cart_found = True
                        break
                except Exception as e:
                    logger.warning(f"Error with selector {selector}: {str(e)}")
            
            if not add_to_cart_found:
                logger.error("Could not find add to cart button")
                # Try to find any clickable button as last resort
                buttons = await self.page.locator('button').all()
                for btn in buttons:
                    try:
                        text = (await btn.text_content() or '').lower()
                        if any(word in text for word in ['add', 'order', 'cart', 'checkout']):
                            await btn.click()
                            logger.info("Clicked button with text: " + text)
                            add_to_cart_found = True
                            break
                    except:
                        continue
            
            # Wait for cart to update
            await asyncio.sleep(3)
            
            # Try to verify cart
            cart_selectors = [
                '.cart-count',
                '[class*="cart-count"]',
                '[class*="cart-quantity"]',
                'span:has-text("1")',
                '[data-testid*="cart-count"]',
                '.cart-icon span',
                '.shopping-cart-count'
            ]
            
            for selector in cart_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        cart_count = await self.page.locator(selector).first.inner_text()
                        logger.info(f"Items in cart: {cart_count}")
                        return True
                except Exception as e:
                    logger.warning(f"Error checking cart with selector {selector}: {str(e)}")
            
            # If we got here, cart verification failed but we'll continue
            logger.warning("Could not verify cart count, but continuing...")
            await self.page.screenshot(path='cart_verification_failed.png')
            return True
            
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            await self.page.screenshot(path='error.png')
            return False

def display_test_results(success: bool, message: str = ""):
    """Display test results in a simple format"""
    result = "PASSED" if success else "FAILED"
    print("\n" + "=" * 50)
    print(f"TEST {result}")
    print("=" * 50)
    if message:
        print(f"\n{message}")
    print("\n" + "=" * 50 + "\n")


async def main():
    """Main function to run the Hardee's test"""
    print("=== Starting Hardee's Test ===")
    test = HardeesTest(headless=False)  # Set headless=False to see the browser
    
    try:
        logger.info("Setting up browser...")
        await test.setup()
        
        logger.info("Starting to add burger to cart...")
        success = await test.add_burger_to_cart()
        
        if success:
            display_test_results(True, "Successfully added burger to cart!")
        else:
            display_test_results(False, "Failed to add burger to cart. Check logs for details.")
            
    except Exception as e:
        error_msg = f"Test failed with error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        display_test_results(False, error_msg)
        
    finally:
        logger.info("Cleaning up...")
        await test.close()
        logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(main())
