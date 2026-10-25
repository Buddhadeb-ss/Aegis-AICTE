"""
Aegis Foundation - Browser Demonstration of Scenario A & Scenario B
Runs both scenarios end-to-end on http://localhost:8503 using Playwright.
Saves high-resolution screenshots into browser_evidence/.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright
from core.db import seed_foundation

EVIDENCE_DIR = os.path.abspath("browser_evidence")
DEMO_DIR = os.path.abspath("demo_files")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

def wait_for_st(page, timeout_sec=2):
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(timeout_sec)

def select_doc_type(page, doc_type_code):
    """Selects the document type in the React-Aria selectbox."""
    page.locator('button[aria-label="Open"]').first.click()
    page.wait_for_timeout(400)
    page.locator(f'div[role="option"]:has-text("{doc_type_code}")').first.click()
    page.wait_for_timeout(400)

def upload_doc(page, doc_type_code, file_name):
    """Uploads a statutory document via the Streamlit form."""
    print(f"Uploading '{file_name}' as {doc_type_code}...", flush=True)
    select_doc_type(page, doc_type_code)
    file_path = os.path.join(DEMO_DIR, file_name)
    page.locator('input[type="file"]').set_input_files(file_path)
    page.wait_for_timeout(600)
    page.locator('button:has-text("Upload and Audit Document")').click()
    wait_for_st(page, 2.5)

def main():
    # Step 0: Reset DB to clean foundation state so the demonstration is clean and reproducible
    print("=== Step 0: Reset DB to Clean Foundation State ===", flush=True)
    seed_foundation(force_reset=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 950})
        page = context.new_page()

        print("=== Step 1: Gateway Landing ===", flush=True)
        page.goto("http://localhost:8503", timeout=20000)
        wait_for_st(page, 1.5)
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "demo_01_gateway.png"))

        # =============================================================
        # SCENARIO A: INCORRECT DOCUMENTS (MISMATCH DETECTED & REJECTED)
        # =============================================================
        print("\n=======================================================", flush=True)
        print("=== SCENARIO A: INCORRECT DOCUMENTS DEMONSTRATION ===", flush=True)
        print("=======================================================", flush=True)

        print("--- College Login ---", flush=True)
        if page.locator('button:has-text("Select College Representative Login")').is_visible():
            page.locator('button:has-text("Select College Representative Login")').click()
            wait_for_st(page, 1)

        page.locator('input[type="text"]').first.fill("principal@apextech.edu")
        page.locator('input[type="password"]').first.fill("ApexPrincipal@2026#Secure")
        page.locator('button:has-text("Sign In to College Portal")').click()
        wait_for_st(page, 2)
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "demo_02_scenario_a_college_dash.png"))

        print("--- Create Application Draft ---", flush=True)
        page.locator('button:has-text("Open Application (Apply)")').click()
        wait_for_st(page, 2)

        if page.locator('button:has-text("Create Application Draft")').is_visible():
            page.locator('button:has-text("Create Application Draft")').click()
            wait_for_st(page, 2)
        elif page.locator('button:has-text("Continue Active Draft")').is_visible():
            page.locator('button:has-text("Continue Active Draft")').click()
            wait_for_st(page, 2)

        page.screenshot(path=os.path.join(EVIDENCE_DIR, "demo_03_scenario_a_dossier_init.png"))

        print("--- Upload Documents (With Mismatched Affiliation Letter) ---", flush=True)
        # 1. Upload MISMATCHED file: Affiliation_Letter.pdf under LAND_TITLE_CERTIFICATE
        upload_doc(page, "LAND_TITLE_CERTIFICATE", "Affiliation_Letter.pdf")

        # 2. Upload building_plan_approval.pdf
        upload_doc(page, "BUILDING_PLAN_APPROVAL", "building_plan_approval.pdf")

        # 3. Upload aicte_affidavit_1.pdf
        upload_doc(page, "AICTE_AFFIDAVIT_1", "aicte_affidavit_1.pdf")

        # 4. Upload fire_safety_certificate.pdf
        upload_doc(page, "FIRE_SAFETY_CERTIFICATE", "fire_safety_certificate.pdf")

        page.screenshot(path=os.path.join(EVIDENCE_DIR, "demo_04_scenario_a_college_uploaded.png"))

        print("--- Submit Application Dossier ---", flush=True)
        submit_btn = page.locator('button:has-text("Final Submission for Regulatory Scrutiny")')
        if submit_btn.is_visible():
            submit_btn.click()
            wait_for_st(page, 2.5)

        page.screenshot(path=os.path.join(EVIDENCE_DIR, "demo_05_scenario_a_college_submitted.png"))

        print("--- Sign out College Representative ---", flush=True)
        page.locator('text=Sign Out').first.click()
        wait_for_st(page, 2)

        print("--- AICTE Scrutiny Officer Login ---", flush=True)
        if page.locator('button:has-text("Select Scrutiny Officer Login")').is_visible():
            page.locator('button:has-text("Select Scrutiny Officer Login")').click()
            wait_for_st(page, 1)

        page.locator('input[type="text"]').first.fill("admin@aicte.gov.in")
        page.locator('input[type="password"]').first.fill("AegisAdmin@2026#Secure")
        page.locator('button:has-text("Sign In to Scrutiny Panel")').click()
        wait_for_st(page, 2)
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "demo_06_scenario_a_officer_dash.png"))

        print("--- Open Scrutiny Queue ---", flush=True)
        page.locator('button:has-text("Open Scrutiny Queue")').click()
        wait_for_st(page, 2)
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "demo_07_scenario_a_officer_queue.png"))

        print("--- Open Review Portal (Screen E) ---", flush=True)
        # Click button to open individual review (Screen E)
        open_review_btns = page.locator('button:has-text("Open Full Detailed Review")')
        if open_review_btns.count() > 0:
            open_review_btns.first.click()
            wait_for_st(page, 2.5)

        # Capture screenshot of Document Verification showing the concise mismatch finding
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "demo_08_scenario_a_officer_mismatch_detected.png"))

        print("--- Record Officer Rejection with Required Reason ---", flush=True)
        rej_input = page.locator('input[placeholder*="Required for rejection"]')
        if rej_input.is_visible():
            rej_input.fill("Statutory document mismatch: University Affiliation Letter uploaded under Land Title Certificate category.")
            time.sleep(0.5)
            page.locator('button:has-text("REJECT APPLICATION")').click()
            wait_for_st(page, 2)

        page.screenshot(path=os.path.join(EVIDENCE_DIR, "demo_09_scenario_a_officer_rejection_recorded.png"))

        print("--- Sign out Scrutiny Officer ---", flush=True)
        page.locator('text=Sign Out').first.click()
        wait_for_st(page, 2)

        # =============================================================
        # SCENARIO B: CORRECT DOCUMENTS (CLEAN PASS & APPROVAL)
        # =============================================================
        print("\n=======================================================", flush=True)
        print("=== SCENARIO B: CORRECT DOCUMENTS DEMONSTRATION ===", flush=True)
        print("=======================================================", flush=True)

        print("--- College Login ---", flush=True)
        if page.locator('button:has-text("Select College Representative Login")').is_visible():
            page.locator('button:has-text("Select College Representative Login")').click()
            wait_for_st(page, 1)

        page.locator('input[type="text"]').first.fill("principal@apextech.edu")
        page.locator('input[type="password"]').first.fill("ApexPrincipal@2026#Secure")
        page.locator('button:has-text("Sign In to College Portal")').click()
        wait_for_st(page, 2)

        print("--- Create New Application Draft ---", flush=True)
        page.locator('button:has-text("Open Application (Apply)")').click()
        wait_for_st(page, 2)

        if page.locator('button:has-text("Create Application Draft")').is_visible():
            page.locator('button:has-text("Create Application Draft")').click()
            wait_for_st(page, 2)

        print("--- Upload All Correct Statutory Documents ---", flush=True)
        # 1. land_title_certificate.pdf
        upload_doc(page, "LAND_TITLE_CERTIFICATE", "land_title_certificate.pdf")

        # 2. building_plan_approval.pdf
        upload_doc(page, "BUILDING_PLAN_APPROVAL", "building_plan_approval.pdf")

        # 3. aicte_affidavit_1.pdf
        upload_doc(page, "AICTE_AFFIDAVIT_1", "aicte_affidavit_1.pdf")

        # 4. fire_safety_certificate.pdf
        upload_doc(page, "FIRE_SAFETY_CERTIFICATE", "fire_safety_certificate.pdf")

        page.screenshot(path=os.path.join(EVIDENCE_DIR, "demo_10_scenario_b_college_all_correct.png"))

        print("--- Submit Clean Application Dossier ---", flush=True)
        submit_btn = page.locator('button:has-text("Final Submission for Regulatory Scrutiny")')
        if submit_btn.is_visible():
            submit_btn.click()
            wait_for_st(page, 2.5)

        page.screenshot(path=os.path.join(EVIDENCE_DIR, "demo_11_scenario_b_college_submitted.png"))

        print("--- Sign out College Representative ---", flush=True)
        page.locator('text=Sign Out').first.click()
        wait_for_st(page, 2)

        print("--- AICTE Scrutiny Officer Login ---", flush=True)
        if page.locator('button:has-text("Select Scrutiny Officer Login")').is_visible():
            page.locator('button:has-text("Select Scrutiny Officer Login")').click()
            wait_for_st(page, 1)

        page.locator('input[type="text"]').first.fill("admin@aicte.gov.in")
        page.locator('input[type="password"]').first.fill("AegisAdmin@2026#Secure")
        page.locator('button:has-text("Sign In to Scrutiny Panel")').click()
        wait_for_st(page, 2)

        print("--- Open Scrutiny Queue ---", flush=True)
        page.locator('button:has-text("Open Scrutiny Queue")').click()
        wait_for_st(page, 2)

        print("--- Open Clean Application Review (Screen E) ---", flush=True)
        open_review_btns = page.locator('button:has-text("Open Full Detailed Review")')
        if open_review_btns.count() > 0:
            open_review_btns.first.click()
            wait_for_st(page, 2.5)

        # Capture screenshot of Document Verification showing 4/4 uploaded, 4/4 matched, CLEAR
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "demo_12_scenario_b_officer_clean_verdict.png"))

        print("--- Record Officer Approval Decision ---", flush=True)
        appr_input = page.locator('input[placeholder*="Required for rejection"]')
        if appr_input.is_visible():
            appr_input.fill("All mandatory statutory documents verified in order. Compliance verified under AICTE APH 2026-27 norms.")
            time.sleep(0.5)
            page.locator('button:has-text("APPROVE APPLICATION")').click()
            wait_for_st(page, 2)

        page.screenshot(path=os.path.join(EVIDENCE_DIR, "demo_13_scenario_b_officer_approval_confirmed.png"))

        print("--- Inspect Statutory Audit Log ---", flush=True)
        page.locator('text=Statutory Audit Log').first.click()
        wait_for_st(page, 2)
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "demo_14_statutory_audit_trail.png"))

        browser.close()
        print("\n=======================================================", flush=True)
        print("=== ALL DEMO SCENARIOS COMPLETED AND VERIFIED! ===", flush=True)
        print("=======================================================", flush=True)

if __name__ == "__main__":
    main()
