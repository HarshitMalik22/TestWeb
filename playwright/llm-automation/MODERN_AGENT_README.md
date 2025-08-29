# Modern AI-Powered Test Agent

A complete rewrite of the test automation framework using LangChain and best practices for AI-powered testing.

## 🚀 Key Improvements

1. **LangChain Integration**
   - Structured output parsing with Pydantic models
   - Better prompt management and templating
   - Memory and context awareness
   - Built-in error handling and retries

2. **Robust Architecture**
   - Type hints and proper error handling
   - Configurable timeouts and retries
   - Proper resource management
   - Extensible design for adding new actions

3. **Enhanced Testing Capabilities**
   - Support for complex test scenarios
   - Better element interaction handling
   - Automatic screenshots on failure
   - Detailed test reporting

## 🛠️ Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

2. Set up your `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## 🧪 Running Tests

Run the example test script:
```bash
python test_modern_agent.py
```

## 🧩 Key Components

### `TestAgent` Class
The main class that handles test execution and AI interactions.

### `TestAction` Model
Defines the structure of test actions with validation.

### Built-in Tools
- `navigate`: Navigate to URLs
- `click`: Click elements
- `fill`: Fill form fields
- `select`: Select dropdown options
- `check`/`uncheck`: Toggle checkboxes
- `hover`: Hover over elements
- `wait`: Wait for conditions
- `assert`: Verify conditions
- `screenshot`: Capture screenshots
- `extract`: Extract page data

## 📝 Example Usage

```python
from playwright.async_api import async_playwright
from modern_test_agent import TestAgent

async def run_test():
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
            results = await agent.execute_test_plan(
                "Navigate to login, enter credentials, and verify dashboard"
            )
            
            for result in results:
                print(f"Success: {result.success}")
                print(f"Message: {result.message}")
                
        finally:
            await agent.close()
            await browser.close()
```

## 🎯 Best Practices

1. **Be Specific**
   - Use clear, specific instructions
   - Include element selectors when possible
   - Specify expected outcomes

2. **Handle Flakiness**
   - Use proper waiting strategies
   - Implement retries for flaky tests
   - Take screenshots on failure

3. **Monitor Usage**
   - Track API usage and costs
   - Monitor test stability
   - Review and update tests regularly

## 📈 Next Steps

1. Add more built-in tools
2. Implement test parallelization
3. Add support for visual regression testing
4. Integrate with CI/CD pipelines
5. Add more documentation and examples
