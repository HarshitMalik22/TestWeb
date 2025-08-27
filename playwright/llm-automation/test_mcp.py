import asyncio
from playwright.async_api import async_playwright

async def test_mcp():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto('https://example.com')
        print(f"Page title: {await page.title()}")
        await page.screenshot(path='example.png')
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_mcp())
