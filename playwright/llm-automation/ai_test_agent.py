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

class AITestAgent:
    """AI-powered test agent that converts natural language to Playwright actions"""
    
    def __init__(self, model: str = "gpt-4-turbo-preview"):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = model
        self.system_prompt = """
        You are an AI test automation expert. Your task is to convert natural language test descriptions 
        into a series of executable Playwright actions. Each action should be a step that can be directly 
        executed by a Playwright script.

        Available action types:
        - navigate: Navigate to a URL
        - click: Click an element
        - fill: Fill a form field
        - select: Select an option from a dropdown
        - check: Check a checkbox
        - uncheck: Uncheck a checkbox
        - hover: Hover over an element
        - press: Press a key
        - wait_for_selector: Wait for an element to be visible
        - assert: Verify some condition is true
        - screenshot: Take a screenshot

        For each action, provide a clear selector that can be used to locate the element.
        """

    async def generate_test_actions(self, test_description: str) -> List[TestAction]:
        """Generate a list of test actions from a natural language description"""
        try:
            # More detailed prompt to get better structured output
            prompt = f"""Convert this test description into a sequence of Playwright actions in JSON format:
            
            {test_description}
            
            Return ONLY a JSON array of action objects. Each action must have:
            - action_type (string): The type of action (navigate, click, fill, etc.)
            - selector (string, optional): The CSS selector to find the element
            - value (string, optional): The value to input or select
            - description (string): A brief description of the action
            - wait_for_selector (string, optional): Optional selector to wait for
            
            Example:
            [
                {{
                    "action_type": "navigate",
                    "selector": "https://example.com",
                    "description": "Navigate to example.com"
                }},
                {{
                    "action_type": "click",
                    "selector": "button#login",
                    "description": "Click login button"
                }}
            ]"""
            
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
                        test_actions.append(TestAction(**action_data))
                    except Exception as e:
                        print(f"Error creating TestAction from action {i}: {e}")
                        print(f"Action data: {action_data}")
                        raise
            elif isinstance(actions_data, dict):
                if 'actions' in actions_data and isinstance(actions_data['actions'], list):
                    for i, action_data in enumerate(actions_data['actions'], 1):
                        try:
                            test_actions.append(TestAction(**action_data))
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
