"""
Modern AI-Powered Test Agent using LangChain and Playwright
"""
from __future__ import annotations

import asyncio
import base64
import logging
import os
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union, Literal

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.tools import Tool, StructuredTool
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field, validator
from langchain_openai import ChatOpenAI
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ActionType(str, Enum):
    """Supported test action types"""
    NAVIGATE = "navigate"
    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    HOVER = "hover"
    PRESS = "press"
    WAIT = "wait"
    SCROLL = "scroll"
    ASSERT = "assert"
    SCREENSHOT = "screenshot"
    EXTRACT = "extract"

class WaitCondition(str, Enum):
    """Supported wait conditions"""
    VISIBLE = "visible"
    HIDDEN = "hidden"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ATTACHED = "attached"
    DETACHED = "detached"

class TestAction(BaseModel):
    """Represents a test action with validation"""
    action_type: ActionType = Field(..., description="Type of action to perform")
    target: Optional[str] = Field(None, description="CSS selector, URL, or other target identifier")
    value: Optional[Any] = Field(None, description="Value to input/select/assert")
    description: str = Field(..., description="Human-readable description of the action")
    wait_condition: Optional[WaitCondition] = Field(
        None, 
        description="Condition to wait for before executing the action"
    )
    timeout: int = Field(10000, description="Timeout in milliseconds")
    retry_count: int = Field(3, description="Number of retry attempts")

    @validator('target')
    def validate_target(cls, v, values):
        if values.get('action_type') != ActionType.WAIT and not v:
            raise ValueError(f"Target is required for action type {values.get('action_type')}")
        return v

class TestResult(BaseModel):
    """Test execution result"""
    success: bool
    message: str
    screenshot: Optional[bytes] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}

class TestAgent:
    """Modern AI-powered test agent with LangChain and Playwright"""
    
    def __init__(
        self,
        page: Page,
        model_name: str = "gpt-4-turbo",
        temperature: float = 0.2,
        max_retries: int = 3,
        base_url: Optional[str] = None,
        screenshots_dir: str = "screenshots",
        debug: bool = False
    ):
        self.page = page
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
        self.base_url = base_url.rstrip('/') if base_url else None
        self.screenshots_dir = Path(screenshots_dir)
        self.debug = debug
        
        # Create screenshots directory if it doesn't exist
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_retries=max_retries
        )
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Initialize agent
        self.agent = self._create_agent()
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize available tools for the agent"""
        return [
            StructuredTool.from_function(
                func=self.navigate,
                name="navigate",
                description="Navigate to a URL"
            ),
            StructuredTool.from_function(
                func=self.click,
                name="click",
                description="Click on an element"
            ),
            StructuredTool.from_function(
                func=self.fill,
                name="fill",
                description="Fill a form field"
            ),
            # Add more tools as needed
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create a simple agent executor with the available tools"""
        # Define a simple prompt template
        template = """You are an AI test automation expert. Your task is to convert natural language test descriptions into executable actions.
        
        Here's what you can do:
        - navigate: Navigate to a URL
        - click: Click on an element
        - fill: Fill a form field
        
        Example:
        User: Go to example.com and click the login button
        AI: 
        Action: navigate
        Action Input: {"url": "https://example.com"}
        
        Action: click
        Action Input: {"selector": "button#login"}
        
        Now, execute this test: {input}"""
        
        prompt = PromptTemplate.from_template(template)
        
        # Create a simple agent
        agent = prompt | self.llm | JsonOutputParser()
        
        # Return a simple executor that just runs the agent
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.debug,
            max_iterations=5,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
    
    async def execute_test_plan(self, test_description: str) -> List[TestResult]:
        """Execute a test plan from a natural language description"""
        results = []
        try:
            logger.info(f"Executing test plan: {test_description}")
            
            # First, navigate to the base URL if specified
            if self.base_url:
                try:
                    await self.navigate("")
                    results.append(TestResult(
                        success=True,
                        message=f"Successfully navigated to {self.base_url}",
                        screenshot=await self._take_screenshot()
                    ))
                except Exception as e:
                    logger.error(f"Navigation error: {str(e)}")
                    results.append(TestResult(
                        success=False,
                        message=f"Failed to navigate to {self.base_url}",
                        error=str(e),
                        screenshot=await self._take_screenshot()
                    ))
                    return results
            
            # Execute the test plan
            try:
                response = await self.agent.ainvoke({"input": test_description})
                
                if isinstance(response, dict) and 'output' in response:
                    results.append(TestResult(
                        success=True,
                        message=response['output'],
                        screenshot=await self._take_screenshot()
                    ))
                else:
                    results.append(TestResult(
                        success=True,
                        message="Test plan executed successfully",
                        metadata={"response": str(response)},
                        screenshot=await self._take_screenshot()
                    ))
                    
            except Exception as e:
                logger.error(f"Test execution error: {str(e)}")
                results.append(TestResult(
                    success=False,
                    message="Error during test execution",
                    error=str(e),
                    screenshot=await self._take_screenshot()
                ))
                
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            results.append(TestResult(
                success=False,
                message="Unexpected error during test execution",
                error=str(e),
                screenshot=await self._take_screenshot()
            ))
            
        return results
    
    # Tool implementations
    async def navigate(self, url: str) -> str:
        """Navigate to a URL"""
        try:
            full_url = f"{self.base_url}/{url.lstrip('/')}" if self.base_url and not url.startswith(('http://', 'https://')) else url
            logger.info(f"Navigating to: {full_url}")
            await self.page.goto(full_url, timeout=60000)
            await self.page.wait_for_load_state("networkidle")
            return f"Successfully navigated to {full_url}"
        except Exception as e:
            logger.error(f"Navigation failed: {str(e)}")
            raise
    
    async def click(self, selector: str) -> str:
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
            return f"Successfully clicked on {selector}"
        except Exception as e:
            logger.error(f"Click failed: {str(e)}")
            raise
    
    async def fill(self, selector: str, value: str) -> str:
        """Fill a form field"""
        try:
            logger.info(f"Filling {selector} with: {value}")
            await self.page.fill(selector, value)
            return f"Successfully filled {selector}"
        except Exception as e:
            logger.error(f"Fill failed: {str(e)}")
            raise
    
    async def _take_screenshot(self) -> bytes:
        """Take a screenshot and return as bytes"""
        try:
            screenshot = await self.page.screenshot(full_page=True)
            return screenshot
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}")
            return b''
    
    async def close(self):
        """Clean up resources"""
        await self.page.close()

# Example usage
async def example_usage():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        agent = TestAgent(
            page=page,
            model_name="gpt-4-turbo",
            base_url="https://example.com",
            debug=True
        )
        
        try:
            # Execute a test plan
            results = await agent.execute_test_plan(
                "Navigate to the login page, enter username 'testuser' and password 'password', "
                "click the login button, and verify that the dashboard is displayed"
            )
            
            for result in results:
                print(f"Test result: {result.success}")
                if not result.success:
                    print(f"Error: {result.error}")
                    
        finally:
            await agent.close()
            await browser.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
