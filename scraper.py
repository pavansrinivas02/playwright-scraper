import asyncio
import json
import os
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

SESSION_FILE = "session.json"
LOGIN_URL = "https://hiring.idenhq.com/"  
EMAIL = "pavan.sg@campusuvce.in"
PASSWORD = "qzn04Z7u"

async def save_session(context):
    storage = await context.storage_state()
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(storage, f)
    print("Session saved successfully.")

async def login(page, context):
    print("No session found. Logging in...")
    await page.goto(LOGIN_URL)
    await page.wait_for_load_state("networkidle")

    await page.screenshot(path="debug_before_fill.png", full_page=True)

    email_selectors = ["input[name='email']", "input[type='email']", "#email"]
    email_filled = False
    for sel in email_selectors:
        try:
            await page.wait_for_selector(sel, timeout=10000)
            await page.fill(sel, EMAIL)
            email_filled = True
            print(f"Filled email using selector: {sel}")
            break
        except PlaywrightTimeoutError:
            continue
    if not email_filled:
        print("Email input not found.")
        await page.screenshot(path="debug_email_not_found.png", full_page=True)
        return False

    password_selectors = ["input[name='password']", "input[type='password']", "#password"]
    password_filled = False
    for sel in password_selectors:
        try:
            await page.wait_for_selector(sel, timeout=10000)
            await page.fill(sel, PASSWORD)
            password_filled = True
            print(f"Filled password using selector: {sel}")
            break
        except PlaywrightTimeoutError:
            continue
    if not password_filled:
        print("Password input not found.")
        await page.screenshot(path="debug_password_not_found.png", full_page=True)
        return False

    try:
        await page.click("button:has-text('Sign in')")
        print("Clicked Sign in button")
    except PlaywrightTimeoutError:
        print("Sign in button not found or clickable.")
        await page.screenshot(path="debug_signin_not_found.png", full_page=True)
        return False

    try:
        await page.wait_for_selector("text=Launch Challenge", timeout=30000)
        print("Login successful, 'Launch Challenge' button visible.")
        await page.screenshot(path="debug_after_login.png", full_page=True)
    except PlaywrightTimeoutError:
        print("Login may have failed - 'Launch Challenge' button not found.")
        await page.screenshot(path="debug_login_failed.png", full_page=True)
        return False

    await save_session(context)
    return True

async def scroll_and_click(page, button_text):
    try:
        locator = page.locator(f"button:has-text('{button_text}')")
        await locator.wait_for(state="visible", timeout=30000)
        await locator.scroll_into_view_if_needed()
        await locator.click()
        print(f"Clicked '{button_text}' button")
        await page.screenshot(path=f"debug_{button_text.replace(' ', '_').lower()}_clicked.png", full_page=True)
    except PlaywrightTimeoutError:
        print(f"'{button_text}' button not found or not clickable.")
        await page.screenshot(path=f"debug_{button_text.replace(' ', '_').lower()}_not_found.png", full_page=True)
        return False
    return True

async def navigate_to_product_table(page):
    steps = [
        "Start Journey",
        "Continue Search",
        "Inventory Section",
        "Show Product Table",
    ]
    for btn_text in steps:
        success = await scroll_and_click(page, btn_text)
        if not success:
            print(f"Failed to click '{btn_text}', aborting navigation.")
            return False
        await asyncio.sleep(2) 
    try:
        await page.wait_for_selector("table.infinite-table tbody tr", timeout=60000)
        print("Product table visible now.")
        await page.screenshot(path="product_table.png", full_page=True)
        return True
    except PlaywrightTimeoutError:
        print(" Product table rows not found after timeout.")
        await page.screenshot(path="debug_product_table_not_found.png", full_page=True)
        return False

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()

        page = await context.new_page()

        if os.path.exists(SESSION_FILE):
            try:
                storage = json.load(open(SESSION_FILE))
                await context.set_storage_state(storage)
                print("Loaded existing session")
                await page.goto(LOGIN_URL)
                await page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"Failed to load session: {e}")
                login_success = await login(page, context)
                if not login_success:
                    await browser.close()
                    return
        else:
            login_success = await login(page, context)
            if not login_success:
                await browser.close()
                return

        if not await scroll_and_click(page, "Launch Challenge"):
            await browser.close()
            return

        success = await navigate_to_product_table(page)
        if not success:
            print("Navigation to product table failed.")

        input("Press Enter to close browser...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
