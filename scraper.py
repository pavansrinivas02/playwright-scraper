# -*- coding: utf-8 -*-
import asyncio
import json
import os
from playwright.async_api import async_playwright

SESSION_FILE = "session.json"
LOGIN_URL = "https://hiring.idenhq.com/"
EMAIL = "pavan.sg@campusuvce.in"
PASSWORD = "qzn04Z7u"  

async def launch_browser():
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    return pw, browser, context, page

async def save_session(context):
    storage = await context.storage_state()
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(storage))
    print("💾 Session saved successfully.")

async def login_and_save_session():
    pw, browser, context, page = await launch_browser()
    print("⚠️ No session found. Logging in...")

    await page.goto(LOGIN_URL)
    await page.wait_for_selector("#email", timeout=30000)
    await page.fill("#email", EMAIL)
    await page.fill("#password", PASSWORD)
    await page.click("button:has-text('Sign in')")

    
    await page.wait_for_url("**/dashboard**", timeout=30000) 
    await asyncio.sleep(3) 

   
    await page.screenshot(path="debug_after_login.png", full_page=True)
    print("📸 Screenshot saved as debug_after_login.png")

    await save_session(context)
    return pw, browser, context, page

async def load_session(pw):
    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        storage = json.load(f)
    browser = await pw.chromium.launch(headless=False)
    context = await browser.new_context(storage_state=storage)
    page = await context.new_page()
    await page.goto(LOGIN_URL)
    await page.wait_for_load_state("networkidle")
    print("🔄 Loaded existing session")
    return browser, context, page

async def navigate_to_product_table(page):
    print("Navigating to product table...")

    # Wait for the main container that holds the journey buttons
    try:
        await page.wait_for_selector("div:has-text('Start Journey')", timeout=30000)
        await page.screenshot(path="debug_before_clicks.png", full_page=True)
        print("Screenshot saved as debug_before_clicks.png")

        # Click sequence
        await page.click("div:has-text('Start Journey')")
        await asyncio.sleep(2)
        await page.click("div:has-text('Continue Search')")
        await asyncio.sleep(2)
        await page.click("div:has-text('Inventory Section')")
        await asyncio.sleep(2)
        await page.click("div:has-text('Show Product Table')")
        await asyncio.sleep(3)
        print("✅ Product table should now be visible.")
    except Exception as e:
        print(" Error during navigation:", e)
        await page.screenshot(path="debug_navigation_error.png", full_page=True)
        print("Screenshot saved as debug_navigation_error.png")

async def main():
    pw = await async_playwright().start()
    try:
        if os.path.exists(SESSION_FILE):
            browser, context, page = await load_session(pw)
        else:
            pw, browser, context, page = await login_and_save_session()

        await navigate_to_product_table(page)

        input("Press Enter to close browser...")
        await browser.close()
    except Exception as e:
        print("Error:", e)
    finally:
        await pw.stop()

if __name__ == "__main__":
    asyncio.run(main())
