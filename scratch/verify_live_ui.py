import asyncio
import os
import sys
import json
from playwright.async_api import async_playwright

ARTIFACTS_DIR = "/Users/ankitkumar/.gemini/antigravity-ide/brain/edd2d07f-b4be-4b87-a869-247024519a1a"

async def run():
    print("="*60)
    print("INTELGRAPH AI — FULL LIVE UI BROWSER VERIFICATION")
    print("="*60)

    async with async_playwright() as p:
        # Launch Chrome with visible window size
        browser = await p.chromium.launch(
            headless=True,
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        )
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # Listen to console and network
        page.on("console", lambda msg: print(f"[BROWSER CONSOLE] {msg.type}: {msg.text[:100]}"))

        print("\n[Step 1] Navigating to http://localhost:5173/ ...")
        await page.goto("http://localhost:5173/", wait_until="networkidle")
        await asyncio.sleep(2)
        await page.screenshot(path=f"{ARTIFACTS_DIR}/live_ui_01_dashboard.png")

        # Navigate to Machines / Asset Directory
        print("\n[Step 2] Navigating to Machines Directory...")
        # Check for sidebar link
        machines_btn = page.locator("button, a").filter(has_text="Machines Directory").or_(page.locator("button, a").filter(has_text="Machines"))
        if await machines_btn.count() > 0:
            await machines_btn.first.click()
            await asyncio.sleep(2)

        await page.screenshot(path=f"{ARTIFACTS_DIR}/live_ui_02_machines_directory.png")

        # Select TEST-FINAL-001
        print("\n[Step 3] Selecting machine TEST-FINAL-001...")
        test_final_item = page.locator("text=TEST-FINAL-001").first
        if await test_final_item.count() > 0:
            await test_final_item.click()
            await asyncio.sleep(2)
            print("Successfully clicked TEST-FINAL-001 machine card!")
        else:
            print("WARNING: TEST-FINAL-001 text not directly found on page; checking search/filter...")
            search_input = page.locator("input[placeholder*='Search'], input[placeholder*='Filter']").first
            if await search_input.count() > 0:
                await search_input.fill("TEST-FINAL-001")
                await asyncio.sleep(1)
                await page.locator("text=TEST-FINAL-001").first.click()
                await asyncio.sleep(2)

        await page.screenshot(path=f"{ARTIFACTS_DIR}/live_ui_03_test_final_001_selected.png")

        # Open Global Chat Modal "Ask IntelGraph AI"
        print("\n[Step 4] Opening Ask IntelGraph AI Chat Modal...")
        chat_trigger = page.locator("button:has-text('Ask IntelGraph AI')").or_(
            page.locator("button:has-text('Ask AI')")
        ).or_(
            page.locator("header button:has-text('Ask')")
        ).or_(
            page.locator("button[aria-label*='Assistant']")
        ).or_(
            page.locator("button:has-text('IntelGraph AI')")
        )

        if await chat_trigger.count() > 0:
            await chat_trigger.first.click()
            await asyncio.sleep(1.5)
            print("Chat trigger clicked!")
        else:
            print("Chat trigger not found by text; searching all buttons...")
            for b in await page.locator("header button, nav button, div button").all():
                txt = await b.inner_text()
                if "Ask" in txt or "AI" in txt:
                    await b.click()
                    await asyncio.sleep(1.5)
                    break

        await page.screenshot(path=f"{ARTIFACTS_DIR}/live_ui_04_chat_modal_opened.png")

        # Verify Scope Selector & Current Machine
        scope_select = page.locator("select[title='Knowledge Scope Arbitration']").or_(page.locator("select")).first
        current_scope = await scope_select.input_value()
        scope_options = await scope_select.locator("option").all_inner_texts()
        print(f"Scope selector options: {scope_options}")
        print(f"Active scope filter: {current_scope}")
        assert current_scope == "Auto", f"Expected scope Auto, got {current_scope}"

        # Helper function to submit query, wait for answer, and inspect
        async def submit_and_verify(test_num, query_text, expected_in=[], forbidden_in=[]):
            print(f"\n" + "="*50)
            print(f"[TEST {test_num}] Query: '{query_text}'")
            print(f"="*50)

            input_field = page.locator("input[placeholder*='Ask question about machinery records']").or_(
                page.locator("input[type='text']")
            ).last
            await input_field.fill(query_text)
            await asyncio.sleep(0.5)

            send_button = page.locator("button:has-text('Send')").last
            await send_button.click()
            print("Query submitted. Waiting for response...")

            # Wait for assistant response to render
            # Loading spinner should disappear
            for _ in range(30):
                await asyncio.sleep(0.5)
                loading = page.locator("text=Querying IntelGraph AI...")
                if await loading.count() == 0:
                    break

            await asyncio.sleep(1)

            # Get latest assistant message
            assistant_boxes = page.locator("div.flex.flex-col.items-start")
            box_count = await assistant_boxes.count()
            latest_box = assistant_boxes.last
            answer_text = await latest_box.inner_text()
            print(f"\n[TEST {test_num} RESPONSE]:\n{answer_text}\n")

            # Capture screenshot
            shot_file = f"{ARTIFACTS_DIR}/live_ui_test_{test_num}_{query_text.replace(' ', '_').replace('?', '')}.png"
            await page.screenshot(path=shot_file)
            print(f"Screenshot saved: {shot_file}")

            # Assertions
            for f in forbidden_in:
                if f.lower() in answer_text.lower():
                    raise AssertionError(f"[TEST {test_num} FAILED]: Forbidden term '{f}' found in answer!")
            for e in expected_in:
                if e.lower() not in answer_text.lower():
                    raise AssertionError(f"[TEST {test_num} FAILED]: Expected term '{e}' not found in answer!")

            print(f"[TEST {test_num} PASSED]: All assertions satisfied!")
            return answer_text

        # Test 1: "What is P-194?"
        # Selected Machine: TEST-FINAL-001
        # Mode: Auto (Intelligent Detection)
        # Expected: P-194 evidence (P&ID / Cooling Water Circulation System)
        # Forbidden: TEST-FINAL-001, 44.44 bar
        ans1 = await submit_and_verify(
            test_num=1,
            query_text="What is P-194?",
            expected_in=["P-194"],
            forbidden_in=["TEST-FINAL-001", "44.44"]
        )

        # Test 2: "What is P-101?"
        # Expected: P-101 evidence
        # Forbidden: TEST-FINAL-001
        ans2 = await submit_and_verify(
            test_num=2,
            query_text="What is P-101?",
            expected_in=["P-101"],
            forbidden_in=["TEST-FINAL-001", "44.44"]
        )

        # Test 3: "What is TEST-FINAL-001?"
        # Expected: TEST-FINAL-001 evidence (44.44 bar is valid here)
        ans3 = await submit_and_verify(
            test_num=3,
            query_text="What is TEST-FINAL-001?",
            expected_in=["TEST-FINAL-001"],
            forbidden_in=[]
        )

        # Test 4: "What is P-194B?"
        # Expected: P-194B evidence
        ans4 = await submit_and_verify(
            test_num=4,
            query_text="What is P-194B?",
            expected_in=["P-194B"],
            forbidden_in=["TEST-FINAL-001"]
        )

        # Test 5: "What is its inspection condition?"
        # Following Test 4, resolves "its" to P-194B
        ans5 = await submit_and_verify(
            test_num=5,
            query_text="What is its inspection condition?",
            expected_in=["P-194B", "Inspection"],
            forbidden_in=["TEST-FINAL-001", "44.44"]
        )

        # Full Chat History Snapshot
        await page.screenshot(path=f"{ARTIFACTS_DIR}/live_ui_full_chat_history.png", full_page=True)
        print(f"\nFinal chat screenshot saved: {ARTIFACTS_DIR}/live_ui_full_chat_history.png")

        await browser.close()
        print("\n" + "="*60)
        print("ALL 5 LIVE UI TESTS PASSED WITH 100% SUCCESS!")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(run())
