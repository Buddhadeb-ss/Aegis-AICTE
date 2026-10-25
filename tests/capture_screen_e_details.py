"""
Capture detailed full-page screenshot of Screen E to document the validation engine interface.
"""
import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8503"
EVIDENCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "browser_evidence"))
os.makedirs(EVIDENCE_DIR, exist_ok=True)

def capture_screen_e():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 1600})
        page = context.new_page()

        # Login as officer
        page.goto(BASE_URL, wait_until="networkidle")
        time.sleep(2)
        page.locator("button", has_text="Select Scrutiny Officer Login").click()
        time.sleep(1)
        page.get_by_label("Official AICTE Email").fill("admin@aicte.gov.in")
        page.locator("input[aria-label='Password']").first.fill("AegisAdmin@2026#Secure")
        page.get_by_role("button", name="Sign In to Scrutiny Panel").click()
        time.sleep(3)

        # Go to Screen D
        page.locator("button", has_text="Open Application Scrutiny Queue →").click()
        time.sleep(2)

        # Open Screen E
        page.locator("button", has_text="Open Individual Review (Screen E) →").click()
        time.sleep(3)

        # Wait for decision-oriented verdict and summary to render
        page.locator("text=Automated Processing Capabilities Summary").first.wait_for(state="visible", timeout=10000)
        time.sleep(1)

        # Capture full page
        full_path = os.path.join(EVIDENCE_DIR, "15_screen_e_decision_oriented_verdict.png")
        page.screenshot(path=full_path, full_page=True)
        print(f"Captured: {full_path}")

        # Expand the single "Technical details" section
        tech_expander = page.locator("summary", has_text="Technical details")
        if tech_expander.count() > 0:
            tech_expander.first.click()
            time.sleep(1.5)
            tech_expander.first.scroll_into_view_if_needed()

            expanded_path = os.path.join(EVIDENCE_DIR, "16_screen_e_technical_details_expanded.png")
            page.screenshot(path=expanded_path)
            print(f"Captured: {expanded_path}")

            # Expand the first granular check technical evidence
            sub_expanders = page.locator("summary", has_text="Inspect Technical Evidence")
            if sub_expanders.count() > 0:
                sub_expanders.first.click()
                time.sleep(1)
                sub_expanders.first.scroll_into_view_if_needed()
                time.sleep(1)
                detail_path = os.path.join(EVIDENCE_DIR, "17_screen_e_check_detail.png")
                page.screenshot(path=detail_path)
                print(f"Captured: {detail_path}")

        browser.close()

if __name__ == "__main__":
    capture_screen_e()
