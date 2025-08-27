# AI-Powered Test Automation with Playwright

This project enables you to write test cases in natural language and have them automatically executed by an AI agent using Playwright.

## Features

- Convert natural language test descriptions into executable Playwright actions
- Web interface for easy test execution and visualization
- Support for common web interactions (click, fill, navigate, etc.)
- Real-time test execution feedback
- Error handling and reporting

## Prerequisites

- Python 3.8+
- Node.js (for Playwright browsers)
- OpenAI API key

## Setup

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Install Playwright browsers:
   ```bash
   playwright install
   ```

3. Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Running the Application

1. Start the Streamlit web interface:
   ```bash
   streamlit run web_interface.py
   ```

2. Open your browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

3. Enter your test description in natural language and click "Run Test"

## Example Test Descriptions

- "Go to hardees.com, click on menu, select a burger and add it to cart"
- "Navigate to hardees.com, click on locations, enter zip code 12345, and show locations"
- "Open hardees.com, click login, enter username 'test@example.com' and password 'password', and submit"

## How It Works

1. The AI agent (using OpenAI) processes your natural language description
2. It generates a sequence of Playwright actions
3. The TestExecutor runs these actions in a real browser
4. Results are displayed in real-time with pass/fail status

## Extending Functionality

To add support for more actions or customize the behavior:

1. Edit `ai_test_agent.py` to add new action types or modify existing ones
2. Update the system prompt to improve AI understanding
3. Add new UI components in `web_interface.py` as needed

## Troubleshooting

- If you get API key errors, ensure your `.env` file is properly set up
- For browser-related issues, try reinstalling Playwright browsers: `playwright install`
- Check the terminal for detailed error messages
