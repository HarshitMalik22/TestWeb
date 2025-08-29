import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class TestAction:
    """Represents a single test action to be executed by Playwright"""
    action_type: str  # e.g., 'click', 'fill', 'navigate', 'assert', etc.
    selector: Optional[str] = None
    value: Optional[Any] = None
    description: str = ""
    wait_for_selector: Optional[str] = None
    wait_timeout: int = 5000  # ms
    timeout: int = 30000  # Default timeout in ms for actions

class AITestAgent:
    """AI-powered test agent that converts natural language to Playwright actions"""
    
    def __init__(self, model: str = "gpt-4-turbo-preview"):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = model
        self.system_prompt = """
        You are an AI test automation expert that converts natural language instructions into executable Playwright test steps.
        
        INSTRUCTIONS:
        1. Interpret the user's intent and translate it into the most appropriate Playwright action
        2. Be flexible with language - understand that users may describe actions in various ways
        3. For interactive elements, prefer semantic selectors (aria-label, text, placeholder) when possible
        4. Include appropriate waits and assertions to make tests more robust
        
        ACTION MAPPING GUIDE:
        - Navigation: Use 'navigate' for any URL or website access
        - Clicks/Taps: Use 'click' for any interaction requiring element activation
        - Text Input: Use 'fill' for any text entry fields
        - Dropdowns/Selectors: Use 'select' for any selection from a list
        - Checkboxes/Radio: Use 'check' or 'uncheck' as appropriate
        - Hover: Use 'hover' for any mouseover interactions
        - Keyboard: Use 'press' for keyboard inputs
        - Waits: Include 'wait_for_selector' when elements need to load
        - Verification: Use 'assert' for any validation or verification steps
        - Screenshot: Use 'screenshot' for capturing the current state
        
        OUTPUT FORMAT:
        - Always return valid JSON array of action objects
        - Each action must have an 'action_type' and 'description'
        - Include 'selector' for actions that target page elements
        - Add 'value' for inputs, selections, or assertions
        - Use clear, descriptive text in 'description' that matches the user's intent
        - Include 'wait_for_selector' when elements need time to appear
        
        EXAMPLE INPUT: "Go to example.com and log in with test@example.com"
        """

    async def generate_test_actions(self, test_description: str) -> List[TestAction]:
        """Generate a list of test actions from a natural language description"""
        try:
            # Enhanced prompt for better natural language understanding
            prompt = f"""
            Convert the following instruction into a sequence of Playwright test steps:
            
            INSTRUCTION: {test_description}
            
            GUIDELINES:
            - Understand the user's intent even if phrased differently
            - Choose the most appropriate action type based on context
            - Use semantic selectors when possible (prefer text, aria-labels, etc.)
            - Include necessary waits for page transitions or element loading
            - Be explicit about what each step is trying to accomplish
            
            RESPONSE FORMAT (JSON array):
            [
                {{
                    // Required: Type of action (navigate, click, fill, etc.)
                    "action_type": "navigate",
                    
                    // Required: Human-readable description matching user's intent
                    "description": "Navigate to example.com",
                    
                    // Required for element interactions: CSS, text, or other selector
                    "selector": "https://example.com",
                    
                    // For inputs, selections, or assertions
                    "value": "example@test.com",
                    
                    // Optional: Wait for element before action (prevents flakiness)
                    "wait_for_selector": ".login-form",
                    
                    // Optional: Additional parameters as needed
                    "timeout": 10000
                }}
            ]
            
            Return ONLY the JSON array, with no additional text or formatting.
            """
            
            # Print debug info
            print(f"Sending request to OpenAI with model: {self.model}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            if not response or not hasattr(response, 'choices') or not response.choices:
                raise ValueError("Invalid response format from OpenAI API")
                
            # Extract and clean the response
            content = response.choices[0].message.content
            print(f"Raw response content: {content[:200]}...")  # Print first 200 chars for debugging
            
            # Clean up the response
            if not content:
                raise ValueError("Empty response from OpenAI API")
                
            # Try to extract JSON from markdown code blocks if present
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            # Try to parse the JSON
            try:
                actions_data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {e}")
                print(f"Content that failed to parse: {content}")
                raise
                
            # Convert to TestAction objects
            test_actions = []
            if isinstance(actions_data, list):
                for i, action_data in enumerate(actions_data, 1):
                    try:
                        # Create a copy of action_data to avoid modifying the original
                        action_kwargs = action_data.copy()
                        
                        # Handle timeout parameter - map it to the appropriate field
                        if 'timeout' in action_kwargs:
                            if action_kwargs['action_type'] == 'wait_for_selector':
                                action_kwargs['wait_timeout'] = action_kwargs.pop('timeout')
                            else:
                                action_kwargs['timeout'] = action_kwargs['timeout']
                                
                        test_actions.append(TestAction(**action_kwargs))
                    except Exception as e:
                        print(f"Error creating TestAction from action {i}: {e}")
                        print(f"Action data: {action_data}")
                        raise
            elif isinstance(actions_data, dict):
                if 'actions' in actions_data and isinstance(actions_data['actions'], list):
                    for i, action_data in enumerate(actions_data['actions'], 1):
                        try:
                            action_kwargs = action_data.copy()
                            if 'timeout' in action_kwargs:
                                if action_kwargs['action_type'] == 'wait_for_selector':
                                    action_kwargs['wait_timeout'] = action_kwargs.pop('timeout')
                            test_actions.append(TestAction(**action_kwargs))
                        except Exception as e:
                            print(f"Error creating TestAction from action {i}: {e}")
                            print(f"Action data: {action_data}")
                            raise
                else:
                    # If it's a dict but doesn't have 'actions', try to use it as a single action
                    try:
                        test_actions.append(TestAction(**actions_data))
                    except Exception as e:
                        print(f"Error creating TestAction from dict: {e}")
                        print(f"Action data: {actions_data}")
                        raise
            else:
                raise ValueError(f"Unexpected response format: {type(actions_data)}")
                
            if not test_actions:
                print("Warning: No valid actions were generated")
                
            return test_actions
            
        except Exception as e:
            print(f"Error generating test actions: {str(e)}")
            return []

class TestExecutor:
    """Executes test actions using Playwright"""
    
    def __init__(self, page):
        self.page = page
        
    async def execute_action(self, action: TestAction):
        """Execute a single test action with improved error handling and logging"""
        try:
            print(f"\n=== Executing: {action.description} ===")
            print(f"Action type: {action.action_type}")
            
            # Add a small delay between actions to prevent rate limiting
            await self.page.wait_for_timeout(500)
            
            if action.action_type == 'navigate':
                url = action.selector if '://' in action.selector else f'https://{action.selector}'
                print(f"Navigating to: {url}")
                await self.page.goto(url, timeout=60000)
                print(f"Page title: {await self.page.title()}")
                
            elif action.action_type == 'click':
                selector = action.selector
                print(f"Clicking on: {selector}")
                
                # Wait for element to be visible and clickable
                element = await self.page.wait_for_selector(
                    selector,
                    state='visible',
                    timeout=10000  # 10 seconds timeout
                )
                await element.scroll_into_view_if_needed()
                await element.click(delay=100)  # Add small delay to mimic human behavior
                print("Click successful")
                
            elif action.action_type == 'fill':
                print(f"Filling field {action.selector} with: {action.value}")
                await self.page.fill(action.selector, str(action.value))
                
            elif action.action_type == 'select':
                print(f"Selecting option {action.value} from {action.selector}")
                await self.page.select_option(action.selector, value=str(action.value))
                
            elif action.action_type == 'wait':
                seconds = int(action.value) if action.value else 1
                print(f"Waiting for {seconds} seconds...")
                await asyncio.sleep(seconds)
                
            elif action.action_type == 'screenshot':
                filename = action.value or f'screenshot_{int(time.time())}.png'
                print(f"Taking screenshot: {filename}")
                await self.page.screenshot(path=filename, full_page=True)
                
            elif action.action_type == 'scroll':
                print("Scrolling the page")
                await self.page.evaluate('window.scrollBy(0, window.innerHeight)')
                
            # Add more action types as needed
            
            # Take a screenshot after each action for debugging
            try:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                os.makedirs('screenshots', exist_ok=True)
                await self.page.screenshot(path=f'screenshots/step_{timestamp}.png')
            except Exception as e:
                print(f"Warning: Could not take screenshot: {e}")
                
            # Small delay to allow page to update
            await self.page.wait_for_timeout(1000)
            
        except Exception as e:
            error_msg = f"Error executing action '{action.description}': {str(e)}"
            print(f"\n!!! ERROR: {error_msg}")
            
            # Take a screenshot on error
            try:
                os.makedirs('error_screenshots', exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                await self.page.screenshot(
                    path=f'error_screenshots/error_{timestamp}.png',
                    full_page=True
                )
                print(f"Screenshot saved to error_screenshots/error_{timestamp}.png")
            except Exception as screenshot_error:
                print(f"Could not take error screenshot: {screenshot_error}")
                
            raise Exception(error_msg) from e
            
    async def execute_test(self, actions: List[TestAction]):
        """Execute a sequence of test actions"""
        results = []
        for i, action in enumerate(actions, 1):
            try:
                await self.execute_action(action)
                results.append({
                    'step': i,
                    'description': action.description,
                    'status': 'passed',
                    'error': None
                })
            except Exception as e:
                results.append({
                    'step': i,
                    'description': action.description,
                    'status': 'failed',
                    'error': str(e)
                })
                break  # Stop on first failure
                
        return results
