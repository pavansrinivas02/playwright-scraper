import asyncio
import json
import os
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

SESSION_FILE = "session.json"
LOGIN_URL = "https://hiring.idenhq.com/"
EMAIL = "pavan.sg@campusuvce.in"
PASSWORD = "qzn04Z7u"


# Creating the Session Management Functions and setting up the session.json 
async def save_session(context):
    storage = await context.storage_state()
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(storage, f)
    print("Session saved successfully.")


async def login(page, context):
    print(" No session found. Logging in...")
    await page.goto(LOGIN_URL)
    await page.wait_for_load_state("networkidle")

    email_selectors = ["input[name='email']", "input[type='email']", "#email"]
    password_selectors = ["input[name='password']", "input[type='password']", "#password"]

    # Auto filling of the email if no session exists
    for sel in email_selectors:
        try:
            await page.wait_for_selector(sel, timeout=10000)
            await page.fill(sel, EMAIL)
            break
        except PlaywrightTimeoutError:
            continue

    # Filling of the password
    for sel in password_selectors:
        try:
            await page.wait_for_selector(sel, timeout=10000)
            await page.fill(sel, PASSWORD)
            break
        except PlaywrightTimeoutError:
            continue

    # Clicking on the sign in button and navigating to the dashboard
    try:
        await page.click("button:has-text('Sign in')")
    except PlaywrightTimeoutError:
        print(" Sign in button not found.")
        return False

    try:
        await page.wait_for_selector("text=Launch Challenge", timeout=30000)
        print(" Login successful.")
    except PlaywrightTimeoutError:
        print(" Login failed.")
        return False

    await save_session(context)
    return True


# Helper for finding out the button and clicking it
async def scroll_and_click(page, button_text):
    try:
        locator = page.locator(f"button:has-text('{button_text}')")
        await locator.wait_for(state="visible", timeout=30000)
        await locator.scroll_into_view_if_needed()
        await locator.click()
        print(f"Clicked '{button_text}'")
    except PlaywrightTimeoutError:
        print(f" Failed to click '{button_text}'")
        return False
    return True


async def navigate_to_product_table(page):
    steps = ["Start Journey", "Continue Search", "Inventory Section"]
    for btn_text in steps:
        success = await scroll_and_click(page, btn_text)
        if not success:
            return False
        await asyncio.sleep(1.5)
    return True


async def wait_for_table(page):
    try:
        await page.wait_for_selector("table.w-full tbody tr", timeout=20000)
        print("✅ Product table loaded.")
        return True
    except PlaywrightTimeoutError:
        print(" Product table not found.")
        return False


async def scroll_until_target_rows(page, target_count=2025):
    container = page.locator("div.infinite-table")
    previous_count = -1

    while True:
        rows = await page.locator("table.w-full tbody tr").all()
        current_count = len(rows)
        print(f"Rows loaded: {current_count}")

        if current_count >= target_count:
            print(f"Target of {target_count} rows reached.")
            break

        if current_count == previous_count:
            await asyncio.sleep(1.5)
        else:
            previous_count = current_count
            await container.evaluate("(el) => el.scrollBy(0, el.scrollHeight)")
            await asyncio.sleep(1.5)

    return True


# Extracting the Product Inventory table data #
async def extract_table_data(page, target_count=2025):
    rows = await page.locator("table.w-full tbody tr").all()
    print(f"Extracting first {min(len(rows), target_count)} rows...")

    data = []
    for row in rows[:target_count]:
        cells = await row.locator("td").all_inner_texts()
        if len(cells) < 9:
            continue 
        item = {
            "ID": cells[0],
            "Warranty": cells[1],
            "Material": cells[2],
            "Rating": cells[3],
            "Price": cells[4],
            "SKU": cells[5],
            "Weight (kg)": cells[6],
            "Manufacturer": cells[7],
            "Item": cells[8],
        }
        data.append(item)

    # Exporting the  Products.json data with key value pairs
    with open("products_2025.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f" Saved {len(data)} rows to products_2025.json")





async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()

        
        if os.path.exists(SESSION_FILE):
            try:
                storage = json.load(open(SESSION_FILE))
                await context.set_storage_state(storage)
                print("Loaded existing session.")
            except Exception as e:
                print(f" Failed to load session: {e}")

        page = await context.new_page()
        await page.goto(LOGIN_URL)
        await page.wait_for_load_state("networkidle")

       
        if not os.path.exists(SESSION_FILE):
            login_success = await login(page, context)
            if not login_success:
                await browser.close()
                return

        
        if not await scroll_and_click(page, "Launch Challenge"):
            await browser.close()
            return

        if not await navigate_to_product_table(page):
            await browser.close()
            return

        if not await wait_for_table(page):
            await browser.close()
            return

        
        await scroll_until_target_rows(page, target_count=2025)
        await extract_table_data(page, target_count=2025)

        input("Press Enter to close browser...")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
