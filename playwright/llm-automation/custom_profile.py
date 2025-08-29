# create_profile.py
from pathlib import Path
from playwright.sync_api import sync_playwright
 
PROFILE_DIR = Path("/Users/harshit/Downloads/final_web_testing_playwright-main/playwright/llm-automation/custom_chrome_profile").resolve()
 
with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir="/Users/harshit/Downloads/final_web_testing_playwright-main/playwright/llm-automation/custom_chrome_profile/",
        channel="chromium",      # use system Chrome
        headless=False,        # must be visible so you can interact
        viewport={"width": 1440, "height": 900},
    )
 
    page = context.new_page()
    print("\nBrowser started with a fresh profile.")
    print("👉 Go to your site, enter location manually, then close the browser window.\n")
 
    # Block until the browser window is closed
    try:
        if context.pages:
            context.pages[0].wait_for_event("close")
    except Exception:
        pass
 
    print(f"Profile saved at: {PROFILE_DIR}")
 