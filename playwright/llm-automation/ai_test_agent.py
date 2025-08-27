import os
import json
import datetime
import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from openai import OpenAI
from dotenv import load_dotenv
import re
from playwright.async_api import Page, ElementHandle

# Load environment variables
load_dotenv()

@dataclass
class TestAction:
    """Enhanced test action with better validation and options"""
    action_type: str
    selector: Optional[str] = None
    value: Optional[Any] = None
    description: str = ""
    wait_for_selector: Optional[str] = None
    wait_timeout: int = 10000  # Increased default timeout
    retry_count: int = 3
    expect_condition: Optional[str] = None  # For assertions
    screenshot: bool = True  # Take screenshot by default
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

class SmartSelectorGenerator:
    """Generates intelligent selectors based on common patterns"""
    
    @staticmethod
    def generate_smart_selectors(description: str, action_type: str) -> List[str]:
        """Generate multiple selector options based on element description"""
        selectors = []
        desc_lower = description.lower()
        
        if action_type == 'click':
            if 'button' in desc_lower:
                # Button selectors
                if 'login' in desc_lower:
                    selectors.extend([
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button:has-text("login")',
                        '[data-testid*="login"]',
                        '.login-btn, .btn-login',
                        '#login, #loginBtn'
                    ])
                elif 'sign up' in desc_lower or 'signup' in desc_lower:
                    selectors.extend([
                        'button:has-text("sign up")',
                        'a:has-text("sign up")',
                        '[data-testid*="signup"]',
                        '.signup-btn, .btn-signup'
                    ])
                elif 'submit' in desc_lower:
                    selectors.extend([
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button:has-text("submit")'
                    ])
                else:
                    # Generic button selectors
                    selectors.extend([
                        'button',
                        'input[type="button"]',
                        '[role="button"]'
                    ])
            
            elif 'link' in desc_lower:
                selectors.extend(['a', 'a[href]'])
            
            elif 'menu' in desc_lower:
                selectors.extend([
                    '[role="menu"]',
                    '.menu',
                    'nav',
                    '.navbar',
                    '.navigation'
                ])
        
        elif action_type == 'fill':
            if 'email' in desc_lower:
                selectors.extend([
                    'input[type="email"]',
                    'input[name*="email"]',
                    '#email',
                    '[data-testid*="email"]'
                ])
            elif 'password' in desc_lower:
                selectors.extend([
                    'input[type="password"]',
                    'input[name*="password"]',
                    '#password',
                    '[data-testid*="password"]'
                ])
            elif 'search' in desc_lower:
                selectors.extend([
                    'input[type="search"]',
                    'input[name*="search"]',
                    '#search',
                    '[placeholder*="search"]'
                ])
            else:
                selectors.extend([
                    'input[type="text"]',
                    'input:not([type])',
                    'textarea'
                ])
        
        return selectors

class EnhancedAITestAgent:
    """Enhanced AI test agent with better accuracy and performance"""
    
    def __init__(self, model: str = "gpt-4-turbo-preview"):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = model
        self.selector_generator = SmartSelectorGenerator()
        self.system_prompt = self._get_enhanced_system_prompt()
        
    def _get_enhanced_system_prompt(self) -> str:
        """Get enhanced system prompt with better instructions"""
        return """
        You are an expert web test automation engineer. Your task is to convert natural language test descriptions 
        into precise, executable Playwright actions that will reliably interact with web elements.

        CRITICAL REQUIREMENTS:
        1. Generate ONLY valid, executable actions
        2. Use robust, specific selectors that are likely to work
        3. Include proper wait conditions and error handling
        4. Break complex actions into smaller, atomic steps
        5. Always include clear descriptions for each step

        AVAILABLE ACTION TYPES:
        - navigate: Go to a specific URL
        - click: Click on buttons, links, or interactive elements
        - fill: Enter text into input fields
        - select: Choose options from dropdowns
        - check/uncheck: Toggle checkboxes
        - hover: Hover over elements
        - press: Press keyboard keys
        - wait: Wait for a specific time or condition
        - scroll: Scroll the page
        - screenshot: Capture a screenshot
        - assert: Verify page content or element state

        SELECTOR BEST PRACTICES:
        - Use text-based selectors when possible: button:has-text("Login")
        - Prefer data attributes: [data-testid="submit-btn"]
        - Use semantic selectors: input[type="email"], button[type="submit"]
        - Include fallback options for reliability
        - Avoid overly specific selectors that might break

        OUTPUT FORMAT:
        Return a JSON array of action objects. Each action must include:
        - action_type: The type of action to perform
        - selector: CSS selector or URL (for navigate)
        - value: Input value (for fill/select actions)
        - description: Clear description of what this step does
        - wait_timeout: Timeout in milliseconds (optional, defaults to 10000)
        
        EXAMPLE RESPONSE:
        [
            {
                "action_type": "navigate",
                "selector": "https://example.com",
                "description": "Navigate to example.com homepage"
            },
            {
                "action_type": "click",
                "selector": "button:has-text('Get Started')",
                "description": "Click the 'Get Started' button",
                "wait_timeout": 5000
            }
        ]
        """
    
    async def generate_test_actions(self, test_description: str) -> List[TestAction]:
        """Generate enhanced test actions with better error handling and validation"""
        try:
            # Pre-process the description for better understanding
            enhanced_description = self._enhance_description(test_description)
            
            prompt = f"""
            Convert this test scenario into a sequence of Playwright actions:
            
            TEST SCENARIO: {enhanced_description}
            
            REQUIREMENTS:
            1. Break down into atomic, executable steps
            2. Use reliable selectors that work across different websites
            3. Include proper wait conditions
            4. Add verification steps where appropriate
            5. Handle common edge cases (loading states, overlays, etc.)
            
            Return ONLY the JSON array of actions, no additional text.
            """
            
            # Make API call with retry logic
            response = await self._make_api_call_with_retry(prompt)
            
            if not response:
                raise ValueError("No response received from OpenAI API")
            
            content = response.choices[0].message.content.strip()
            
            # Enhanced JSON parsing
            actions_data = self._parse_json_response(content)
            
            # Convert to TestAction objects with validation
            test_actions = self._create_test_actions(actions_data)
            
            # Optimize actions for better performance
            optimized_actions = self._optimize_actions(test_actions)
            
            return optimized_actions
            
        except Exception as e:
            print(f"Error generating test actions: {str(e)}")
            # Fallback: try to create basic actions from keywords
            return self._create_fallback_actions(test_description)
    
    def _enhance_description(self, description: str) -> str:
        """Enhance the test description with context and clarifications"""
        # Add common web testing context
        enhancements = []
        
        if 'go to' in description.lower() or 'navigate' in description.lower():
            enhancements.append("Include proper page load waiting")
        
        if 'click' in description.lower():
            enhancements.append("Ensure element is visible and clickable before clicking")
        
        if 'fill' in description.lower() or 'enter' in description.lower():
            enhancements.append("Clear field before entering new text")
        
        enhanced = description
        if enhancements:
            enhanced += f"\n\nAdditional requirements: {'; '.join(enhancements)}"
        
        return enhanced
    
    async def _make_api_call_with_retry(self, prompt: str, max_retries: int = 3) -> Any:
        """Make API call with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,  # Lower temperature for more consistent results
                    max_tokens=2000
                )
                return response
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"API call attempt {attempt + 1} failed: {e}. Retrying...")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _parse_json_response(self, content: str) -> List[Dict]:
        """Enhanced JSON parsing with better error handling"""
        try:
            # Clean up the response
            content = content.strip()
            
            # Remove markdown code blocks if present
            if '```json' in content:
                content = re.search(r'```json\s*(\[.*?\])\s*```', content, re.DOTALL)
                if content:
                    content = content.group(1)
            elif '```' in content:
                content = re.search(r'```\s*(\[.*?\])\s*```', content, re.DOTALL)
                if content:
                    content = content.group(1)
            
            # Try to extract JSON array
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                content = json_match.group()
            
            # Parse JSON
            actions_data = json.loads(content)
            
            # Ensure it's a list
            if isinstance(actions_data, dict):
                if 'actions' in actions_data:
                    actions_data = actions_data['actions']
                else:
                    actions_data = [actions_data]
            
            return actions_data if isinstance(actions_data, list) else []
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            print(f"Content: {content}")
            return []
        except Exception as e:
            print(f"Error parsing response: {e}")
            return []
    
    def _create_test_actions(self, actions_data: List[Dict]) -> List[TestAction]:
        """Create TestAction objects with validation"""
        test_actions = []
        
        for i, action_data in enumerate(actions_data):
            try:
                # Validate required fields
                if 'action_type' not in action_data:
                    print(f"Warning: Action {i+1} missing action_type, skipping")
                    continue
                
                # Set defaults for optional fields
                action_data.setdefault('description', f"Step {i+1}")
                action_data.setdefault('wait_timeout', 10000)
                action_data.setdefault('retry_count', 3)
                action_data.setdefault('screenshot', True)
                
                # Enhance selectors for better reliability
                if 'selector' in action_data and action_data['selector']:
                    action_data['selector'] = self._enhance_selector(
                        action_data['selector'], 
                        action_data['action_type']
                    )
                
                test_action = TestAction(**action_data)
                test_actions.append(test_action)
                
            except Exception as e:
                print(f"Error creating TestAction {i+1}: {e}")
                continue
        
        return test_actions
    
    def _enhance_selector(self, selector: str, action_type: str) -> str:
        """Enhance selector for better reliability"""
        # Don't modify URLs
        if action_type == 'navigate':
            return selector
        
        # Add common robustness patterns
        if action_type == 'click' and 'button' in selector:
            # Make button selector more robust
            if not ':has-text' in selector and not '[' in selector:
                # If it's just 'button', make it more specific
                return 'button:visible'
        
        return selector
    
    def _optimize_actions(self, actions: List[TestAction]) -> List[TestAction]:
        """Optimize actions for better performance and reliability"""
        optimized = []
        
        for i, action in enumerate(actions):
            # Add wait after navigation
            if action.action_type == 'navigate':
                optimized.append(action)
                # Add a wait for page to be ready
                wait_action = TestAction(
                    action_type='wait',
                    value=2,
                    description='Wait for page to load completely',
                    screenshot=False
                )
                optimized.append(wait_action)
            
            # Add hover before click for better reliability
            elif action.action_type == 'click' and action.selector:
                # First hover to ensure element is interactive
                hover_action = TestAction(
                    action_type='hover',
                    selector=action.selector,
                    description=f'Hover over element before clicking',
                    screenshot=False,
                    wait_timeout=5000
                )
                optimized.append(hover_action)
                optimized.append(action)
            
            else:
                optimized.append(action)
        
        return optimized
    
    def _create_fallback_actions(self, description: str) -> List[TestAction]:
        """Create basic fallback actions when AI generation fails"""
        actions = []
        desc_lower = description.lower()
        
        # Look for URL patterns
        url_pattern = r'(?:go to|visit|navigate to)\s+([a-zA-Z0-9.-]+\.com|https?://[^\s]+)'
        url_match = re.search(url_pattern, desc_lower)
        
        if url_match:
            url = url_match.group(1)
            if not url.startswith('http'):
                url = f'https://{url}'
            
            actions.append(TestAction(
                action_type='navigate',
                selector=url,
                description=f'Navigate to {url}'
            ))
        
        # Look for click actions
        if 'click' in desc_lower:
            actions.append(TestAction(
                action_type='click',
                selector='button, a, [role="button"]',
                description='Click on interactive element'
            ))
        
        return actions

class EnhancedTestExecutor:
    """Enhanced test executor with better performance and error handling"""
    
    def __init__(self, page: Page):
        self.page = page
        self.screenshot_counter = 0
        
    async def execute_action(self, action: TestAction) -> Dict[str, Any]:
        """Execute a single test action with enhanced error handling and performance"""
        start_time = time.time()
        result = {
            'description': action.description,
            'action_type': action.action_type,
            'status': 'passed',
            'start_time': start_time,
            'duration': 0,
            'error': None,
            'screenshot': None,
            'selector': action.selector,
            'value': action.value
        }
        
        try:
            print(f"\n Executing: {action.description}")
            
            # Execute the appropriate action
            if action.action_type == 'navigate':
                await self._execute_navigate(action)
            elif action.action_type == 'external_navigate':
                await self._execute_external_navigate(action)
            elif action.action_type == 'click':
                await self._execute_click(action)
            elif action.action_type == 'fill':
                await self._execute_fill(action)
            elif action.action_type == 'select':
                await self._execute_select(action)
            elif action.action_type in ['check', 'uncheck']:
                await self._execute_check(action)
            elif action.action_type == 'hover':
                await self._execute_hover(action)
            elif action.action_type == 'wait':
                await self._execute_wait(action)
            elif action.action_type == 'scroll':
                await self._execute_scroll(action)
            elif action.action_type == 'screenshot':
                await self._execute_screenshot(action)
            elif action.action_type == 'press':
                await self._execute_press(action)
            else:
                raise ValueError(f"Unsupported action type: {action.action_type}")
            
            # Capture screenshot if requested
            if action.screenshot:
                result['screenshot'] = await self.page.screenshot(type='png')
            
            print(f" Action completed successfully")
            print(f"✅ Action completed successfully")
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Action failed: {error_msg}")
            result.update({
                'status': 'failed',
                'error': error_msg
            })
            
            # Capture error screenshot
            try:
                result['screenshot'] = await self.page.screenshot(type='png')
            except:
                pass
        
        finally:
            result['duration'] = time.time() - start_time
            
        return result
    
    async def _execute_navigate(self, action: TestAction):
        """Execute navigation with enhanced reliability"""
        url = action.selector
        
        # Handle relative URLs by checking if it's a path
        if not (url.startswith('http://') or url.startswith('https://')):
            # If it's a path, get the current base URL and append the path
            base_url = self.page.url
            if not base_url.endswith('/') and not url.startswith('/'):
                base_url += '/'
            url = f"{base_url}{url}"
        
        print(f"📍 Navigating to: {url}")
        
        try:
            # Navigate with multiple wait strategies
            response = await self.page.goto(
                url, 
                timeout=30000,
                wait_until='domcontentloaded'
            )
            
            # Wait for network to be mostly idle
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            
            print(f"✅ Navigation successful (Status: {response.status if response else 'N/A'})")
            
        except Exception as e:
            # Fallback: try with just 'load' event
            print(f"⚠️  Initial navigation failed, trying fallback: {e}")
            await self.page.goto(url, timeout=30000, wait_until='load')
            print("✅ Fallback navigation successful")
    
    async def _execute_external_navigate(self, action: TestAction):
        """Execute navigation to an external URL in a new browser context"""
        url = action.selector
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        
        print(f"🌐 Opening external URL: {url}")
        
        try:
            # Store the current page reference
            original_page = self.page
            
            # Create a new context for the external navigation
            context = await self.page.context.browser.new_context()
            new_page = await context.new_page()
            
            # Set the page reference to the new page
            self.page = new_page
            
            # Navigate to the external URL
            response = await self.page.goto(
                url,
                timeout=30000,
                wait_until='domcontentloaded'
            )
            
            # Wait for network to be mostly idle
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            
            print(f"✅ External navigation successful (Status: {response.status if response else 'N/A'})")
            
            # Keep the context and page for future use
            self.external_context = context
            
        except Exception as e:
            # Fallback: try with just 'load' event
            print(f"⚠️  Initial external navigation failed, trying fallback: {e}")
            await self.page.goto(url, timeout=30000, wait_until='load')
            print("✅ Fallback external navigation successful")
            
            # Clean up on error
            if 'new_page' in locals():
                await new_page.close()
            if 'context' in locals():
                await context.close()
            # Restore the original page reference
            self.page = original_page
    
    async def _execute_click(self, action: TestAction):
        """Execute click with multiple fallback strategies for Hardee's website"""
        selector = action.selector
        if not selector:
            raise Exception("No selector provided for click action")
        
        print(f"🔍 Attempting to click: {selector}")
        
        # Try multiple strategies to find and click the element
        max_attempts = 3
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                # Strategy 1: Wait for element to be visible and enabled
                try:
                    element = await self.page.wait_for_selector(
                        selector,
                        state='visible',
                        timeout=10000,
                        strict=True
                    )
                    print(f"✅ Found element with selector: {selector}")
                except Exception as e:
                    # Strategy 2: Try with a more flexible approach
                    print(f"⚠️  Standard selector failed, trying more flexible approach...")
                    elements = await self.page.query_selector_all(selector)
                    if not elements:
                        raise Exception(f"No elements found matching selector: {selector}")
                    element = elements[0]
                
                # Ensure element is in viewport with smooth scroll
                await self.page.evaluate('''element => {
                    element.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center',
                        inline: 'center'
                    });
                }''', element)
                
                # Add a small delay for any scroll animations
                await self.page.wait_for_timeout(800)
                
                # Highlight the element temporarily (for debugging)
                try:
                    await self.page.evaluate('''element => {
                        const originalStyle = element.style.cssText;
                        element.style.border = '2px solid #ff0000';
                        element.style.boxShadow = '0 0 10px #ff0000';
                        setTimeout(() => {
                            element.style.cssText = originalStyle;
                        }, 1000);
                    }''', element)
                except:
                    pass  # Ignore errors in highlighting
                
                # Try different click strategies
                click_strategies = [
                    # 1. Standard click
                    lambda: element.click(timeout=5000),
                    
                    # 2. JavaScript click
                    lambda: self.page.evaluate('''element => {
                        element.dispatchEvent(new MouseEvent('click', {
                            view: window,
                            bubbles: true,
                            cancelable: true,
                            buttons: 1,
                            clientX: element.getBoundingClientRect().left + element.offsetWidth/2,
                            clientY: element.getBoundingClientRect().top + element.offsetHeight/2
                        }));
                    }''', element),
                    
                    # 3. Click via bounding box (async lambda)
                    lambda: self.page.evaluate('''async (element) => {
                        const box = await element.boundingBox();
                        const x = box.x + box.width / 2;
                        const y = box.y + box.height / 2;
                        await this.page.mouse.click(x, y);
                    }''', element),
                    
                    # 4. Focus and press Enter
                    lambda: self.page.evaluate('''async (element) => {
                        element.focus();
                        await new Promise(resolve => setTimeout(resolve, 100));
                        element.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
                        element.dispatchEvent(new KeyboardEvent('keyup', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
                    }''', element)
                ]
                
                # Try each click strategy
                for i, click_strategy in enumerate(click_strategies, 1):
                    try:
                        print(f"🔄 Trying click strategy {i}...")
                        await click_strategy()
                        print(f"✅ Click successful with strategy {i}")
                        
                        # Verify the click had an effect
                        await self.page.wait_for_timeout(1000)  # Wait for any navigation/update
                        return
                        
                    except Exception as click_error:
                        last_error = click_error
                        if i < len(click_strategies):
                            print(f"⚠️  Click strategy {i} failed, trying next...")
                            await self.page.wait_for_timeout(500)
                        continue
                
                # If we get here, all click strategies failed
                raise Exception("All click strategies failed")
                
            except Exception as e:
                last_error = e
                print(f"⚠️  Click attempt {attempt + 1} failed: {str(e)}")
                
                if attempt == max_attempts - 1:
                    # Take a screenshot before failing
                    try:
                        os.makedirs('error_screenshots', exist_ok=True)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_path = f'error_screenshots/click_error_{timestamp}.png'
                        await self.page.screenshot(path=screenshot_path, full_page=True)
                        print(f"📸 Screenshot saved to: {screenshot_path}")
                    except Exception as screenshot_error:
                        print(f"⚠️  Failed to save screenshot: {screenshot_error}")
                    
                    raise Exception(f"Failed to click element after {max_attempts} attempts: {str(e)}")
                
                # Wait before retry with exponential backoff
                wait_time = 2 ** attempt  # 2, 4, 8 seconds
                print(f"⏳ Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                    
            except Exception as e:
                print(f"⚠️  Click attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_attempts - 1:
                    # Take screenshot before failing
                    try:
                        os.makedirs('error_screenshots', exist_ok=True)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_path = f'error_screenshots/click_error_{timestamp}.png'
                        await self.page.screenshot(path=screenshot_path, full_page=True)
                        print(f"📸 Screenshot saved to: {screenshot_path}")
                    except Exception as screenshot_error:
                        print(f"⚠️  Failed to save screenshot: {screenshot_error}")
                    
                    raise Exception(f"Failed to click element after {max_attempts} attempts: {str(e)}")
                
                # Wait before retry with exponential backoff
                wait_time = 2 ** attempt  # 2, 4, 8 seconds
                print(f"⏳ Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                print(f"⚠️  Click attempt {attempt + 1} failed, retrying: {e}")
                await self.page.wait_for_timeout(1000)
    
    async def _execute_fill(self, action: TestAction):
        """Execute fill with enhanced input handling"""
        selector = action.selector
        value = str(action.value) if action.value else ""
        print(f"✏️  Filling '{selector}' with: {value}")
        
        element = await self._wait_for_element(selector, action.wait_timeout)
        
        # Clear and fill with proper timing
        await element.clear()
        await self.page.wait_for_timeout(200)
        await element.type(value, delay=50)  # Add typing delay for realism
        
        print("✅ Fill successful")
    
    async def _execute_select(self, action: TestAction):
        """Execute select dropdown"""
        selector = action.selector
        value = str(action.value) if action.value else ""
        print(f"📋 Selecting '{value}' from: {selector}")
        
        await self.page.select_option(selector, value=value, timeout=action.wait_timeout)
        print("✅ Select successful")
    
    async def _execute_hover(self, action: TestAction):
        """Execute hover action"""
        selector = action.selector
        print(f"👆 Hovering over: {selector}")
        
        element = await self._wait_for_element(selector, action.wait_timeout)
        await element.hover()
        
        print("✅ Hover successful")
    
    async def _execute_wait(self, action: TestAction):
        """Execute wait action"""
        duration = float(action.value) if action.value else 1.0
        print(f"⏳ Waiting for {duration} seconds")
        
        await asyncio.sleep(duration)
        print("✅ Wait completed")
    
    async def _execute_scroll(self, action: TestAction):
        """Execute scroll action"""
        print("📜 Scrolling page")
        await self.page.evaluate('window.scrollBy(0, window.innerHeight)')
        await self.page.wait_for_timeout(500)
        print("✅ Scroll completed")
    
    async def _execute_screenshot(self, action: TestAction):
        """Execute screenshot action"""
        filename = action.value or f'screenshot_{int(time.time())}.png'
        print(f"📸 Taking screenshot: {filename}")
        
        await self.page.screenshot(path=filename, full_page=True)
        print("✅ Screenshot saved")
    
    async def _execute_press(self, action: TestAction):
        """Execute key press action"""
        key = action.value or 'Enter'
        print(f"⌨️  Pressing key: {key}")
        
        await self.page.keyboard.press(key)
        print("✅ Key press completed")
    
    async def _wait_for_element(self, selector: str, timeout: int = 20000) -> ElementHandle:
        """Wait for element with multiple strategies and better error handling"""
        start_time = time.time()
        last_error = None
        
        # Clean up the selector
        clean_selector = selector.strip()
        
        # Generate alternative selectors based on the input
        def generate_alternative_selectors(s):
            alts = []
            
            # Clean up the text
            clean_text = s.replace('text=', '').strip('"\'').strip()
            
            # Common Hardee's specific selectors
            hardees_selectors = [
                # Menu button patterns
                f'button:has-text("{clean_text}")',
                f'a:has-text("{clean_text}")',
                f'[data-test*="{clean_text.lower()}"]',
                f'[data-testid*="{clean_text.lower()}"]',
                f'[class*="menu" i] [class*="item" i]:has-text("{clean_text}")',
                f'[class*="nav" i] [class*="item" i]:has-text("{clean_text}")',
                f'[class*="btn" i]:has-text("{clean_text}")',
                f'[class*="button" i]:has-text("{clean_text}")',
                f'[class*="link" i]:has-text("{clean_text}")',
                f'[role="button"]:has-text("{clean_text}")',
                f'[role="menuitem"]:has-text("{clean_text}")',
                f'[role="navigation"] :text-is("{clean_text}")',
                f'[class*="header"] :text-is("{clean_text}")',
                f'[class*="menu"] :text-is("{clean_text}")',
                f'[class*="nav"] :text-is("{clean_text}")',
            ]
            
            # Text variations
            text_variations = [
                clean_text,  # Original
                clean_text.upper(),  # UPPERCASE
                clean_text.lower(),  # lowercase
                clean_text.title(),  # Title Case
                clean_text.capitalize(),  # First letter capitalized
            ]
            
            # Generate text-based selectors
            for text in text_variations:
                if not text.strip():
                    continue
                    
                # Standard text selectors
                alts.extend([
                    f'text={text}',
                    f'text="{text}"',
                    f':text-is("{text}")',
                    f':text-matches("{text}", "i")',
                    f':has-text("{text}")',
                ])
                
                # Button-specific selectors
                alts.extend([
                    f'button:text-is("{text}")',
                    f'a:text-is("{text}")',
                    f'[role="button"]:text-is("{text}")',
                    f'[type="button"]:text-is("{text}")',
                ])
            
            # Add Hardee's specific selectors
            alts.extend(hardees_selectors)
            
            # If it's a CSS selector, add variations
            if not s.startswith('text='):
                alts.append(s)  # Original
                
                # Try different variations of the selector
                if '[' in s and ']' in s:
                    # Try without attributes
                    base_selector = s.split('[')[0]
                    alts.append(base_selector)
                    
                    # Try with different attribute quotes
                    if '"' in s:
                        alts.append(s.replace('"', "'"))
                    elif "'" in s:
                        alts.append(s.replace("'", '"'))
                
                # Try adding common data attributes
                data_attrs = ['test', 'testid', 'qa', 'cy', 'data-test', 'data-qa', 'data-cy']
                for attr in data_attrs:
                    if attr not in s.lower():
                        alts.append(f'[{attr}*="{clean_text.lower()}"]')
                
                # Try with different class patterns
                if 'class' not in s:
                    alts.append(f'.{clean_text}')
                    alts.append(f'[class*="{clean_text.lower()}"]')
                    alts.append(f'[class*="{clean_text.lower().replace(" ", "-")}"]')
                    alts.append(f'[class*="{clean_text.lower().replace(" ", "_")}"]')
            
            return alts
        
        # Generate all possible selectors to try
        selectors_to_try = generate_alternative_selectors(clean_selector)
        
        # Add some common fallback strategies
        if 'button' in clean_selector.lower() or 'btn' in clean_selector.lower():
            selectors_to_try.extend([
                f'button:has-text("{clean_selector}")',
                f'[role="button"]:has-text("{clean_selector}")',
                f'[onclick*="{clean_selector.lower()}"]'
            ])
        
        # Try each selector with a timeout
        for selector_to_try in set(selectors_to_try):  # Remove duplicates
            if time.time() - start_time > timeout / 1000:
                break
                
            try:
                print(f"🔍 Trying selector: {selector_to_try}")
                
                # First try visible
                element = await self.page.wait_for_selector(
                    selector_to_try,
                    state='visible',
                    timeout=min(5000, timeout - (time.time() - start_time) * 1000)
                )
                
                if element:
                    # Scroll into view
                    await element.scroll_into_view_if_needed()
                    await self.page.wait_for_timeout(500)  # Wait for any scroll animations
                    
                    # Check if it's really visible and enabled
                    is_visible = await element.is_visible()
                    is_enabled = await element.is_enabled()
                    
                    if is_visible and is_enabled:
                        print(f"✅ Found element with selector: {selector_to_try}")
                        return element
                    
            except Exception as e:
                last_error = e
                continue
        
        # If we get here, all strategies failed
        error_msg = f"Could not find element with any selector. Tried: {', '.join(selectors_to_try[:5])}..."
        if last_error:
            error_msg += f"\nLast error: {str(last_error)}"
            
        # Take a screenshot to help with debugging
        try:
            os.makedirs('error_screenshots', exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f'error_screenshots/element_not_found_{timestamp}.png'
            await self.page.screenshot(path=screenshot_path, full_page=True)
            error_msg += f"\nScreenshot saved to: {screenshot_path}"
            
            # Also save page source for debugging
            page_source = await self.page.content()
            with open(screenshot_path.replace('.png', '.html'), 'w', encoding='utf-8') as f:
                f.write(page_source)
                
        except Exception as e:
            error_msg += f"\nFailed to save debug info: {str(e)}"
            
        raise Exception(error_msg)
    
    async def execute_test(self, test_actions: List[TestAction]) -> List[Dict[str, Any]]:
        """Execute a complete test with enhanced error recovery"""
        results = []
        
        for i, action in enumerate(test_actions, 1):
            print(f"\n{'='*50}")
            print(f"STEP {i}/{len(test_actions)}: {action.description}")
            print(f"\n{'='*80}")
            print(f"STEP {i+1}/{len(test_actions)}: {action.description}")
            print(f"Action: {action.action_type}")
            if action.selector:
                print(f"Selector: {action.selector}")
            if action.value:
                print(f"Value: {action.value}")
            print(f"{'='*80}")
            
            # Execute action with retry logic
            max_retries = action.retry_count if hasattr(action, 'retry_count') else 3
            result = None
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    start_time = time.time()
                    result = await self.execute_action(action)
                    result['duration'] = time.time() - start_time
                    result['attempt'] = attempt + 1
                    
                    if result['status'] == 'passed':
                        print(f"✅ Step {i+1} passed (attempt {attempt + 1}/{max_retries})")
                        if result.get('screenshot'):
                            print("📸 Screenshot captured")
                        break
                    else:
                        last_error = result.get('error', 'Unknown error')
                        print(f"⚠️  Step {i+1} failed (attempt {attempt + 1}/{max_retries}): {last_error}")
                        
                except Exception as e:
                    last_error = str(e)
                    print(f"⚠️  Error in step {i+1} (attempt {attempt + 1}/{max_retries}): {last_error}")
                    
                    if attempt == max_retries - 1:
                        result = {
                            'description': action.description,
                            'action_type': action.action_type,
                            'status': 'failed',
                            'error': last_error,
                            'duration': time.time() - start_time if 'start_time' in locals() else 0,
                            'screenshot': None,
                            'attempt': attempt + 1
                        }
                    else:
                        # Add exponential backoff
                        delay = min(2 ** attempt, 10)  # Cap at 10 seconds
                        print(f"⏳ Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
            
            if result:
                results.append(result)
                # If step failed and we have a screenshot, save it
                if result['status'] == 'failed' and not result.get('screenshot'):
                    try:
                        os.makedirs('error_screenshots', exist_ok=True)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_path = f'error_screenshots/step_{i+1}_error_{timestamp}.png'
                        await self.page.screenshot(path=screenshot_path, full_page=True)
                        result['screenshot_path'] = screenshot_path
                        print(f"📸 Error screenshot saved to: {screenshot_path}")
                    except Exception as e:
                        print(f"⚠️  Failed to save error screenshot: {e}")
            
            # Add small delay between steps to allow UI to update
            await asyncio.sleep(0.5)
        
        return results

# Backwards compatibility
AITestAgent = EnhancedAITestAgent
TestExecutor = EnhancedTestExecutor