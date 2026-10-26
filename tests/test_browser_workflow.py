"""
Aegis Foundation - Real Browser Verification of Redesigned Wireframe Interface
Tests all 5 screens and workflows using Playwright Chromium against http://localhost:8503:
- Screen A (Wireframe 1): AICTE Portal Landing Page & Dual Login Entry Points
- Screen B (Wireframe 3): College Representative Portal (APPLY, APPLICATION STATUS, NOTIFICATIONS)
- Screen C (Wireframe 2): Scrutiny Officer Portal (APPLICATIONS, LOGS)
- Screen D (Wireframe 4): Scrutiny Officer Queue (Two-Panel Layout & AI Assessment Summary)
- Screen E (Wireframe 5): Individual Review (Context/Why, AI Check PASS/FAIL/SUS, Document Cards, Decision)
- Institution-level Isolation (Beacon vs Apex)
"""

import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.db import seed_foundation

BASE_URL = "http://localhost:8503"
EVIDENCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "browser_evidence"))
os.makedirs(EVIDENCE_DIR, exist_ok=True)


def make_test_pdf(filepath: str, title: str):
    """Creates a minimal valid PDF with proper header and structure."""
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog /Pages 2 0 R >>\n"
        b"endobj\n"
        b"2 0 obj\n"
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
        b"endobj\n"
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\n"
        b"endobj\n"
        b"4 0 obj\n"
        b"<< /Length 55 >>\n"
        b"stream\n"
        b"BT /F1 12 Tf 72 712 Td (" + title.encode("ascii", "replace") + b") Tj ET\n"
        b"endstream\n"
        b"endobj\n"
        b"xref\n"
        b"0 5\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000206 00000 n \n"
        b"trailer\n"
        b"<< /Size 5 /Root 1 0 R >>\n"
        b"startxref\n"
        b"310\n"
        b"%%EOF\n"
    )
    with open(filepath, "wb") as f:
        f.write(pdf_content)


def run_wireframe_browser_verification():
    print("=====================================================================")
    print("AEGIS FOUNDATION - FRONTEND WIREFRAME REDESIGN VERIFICATION")
    print("Testing Screens A, B, C, D, E against:", BASE_URL)
    print("Evidence Directory:", EVIDENCE_DIR)
    print("=====================================================================")

    # Pristine database state
    print("Initializing clean database state...")
    seed_foundation(force_reset=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 950})
        page = context.new_page()

        # -------------------------------------------------------------
        # 1. SCREEN A (Wireframe 1) - AICTE Portal Public Landing Page
        # -------------------------------------------------------------
        print("\n[STEP 1] Verifying Screen A (Wireframe 1: Public Landing Page)...")
        page.goto(BASE_URL, wait_until="networkidle")
        time.sleep(2)

        # Header check: AICTE Portal badge & title
        assert "AICTE Portal" in page.content(), "Screen A header title missing"
        assert "COLLEGE LOGIN" in page.content(), "COLLEGE LOGIN card missing"
        assert "SCRUTINY OFFICER LOGIN" in page.content(), "SCRUTINY OFFICER LOGIN card missing"
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "01_screen_a_public_portal.png"))
        print("  -> Captured: 01_screen_a_public_portal.png")

        # Test invalid credentials rejection
        print("  -> Testing invalid login rejection...")
        page.get_by_label("Institutional Email").fill("unauthorized@fakecollege.edu")
        page.locator("input[aria-label='Password']").first.fill("WrongPassword#999")
        page.get_by_role("button", name="Sign In to College Portal").click()
        time.sleep(2)
        assert "Invalid credentials" in page.content(), "Expected error message not displayed"
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "02_invalid_credentials_rejected.png"))
        print("  -> Captured: 02_invalid_credentials_rejected.png")

        # -------------------------------------------------------------
        # 2. SCREEN B (Wireframe 3) - College Representative Portal
        # -------------------------------------------------------------
        print("\n[STEP 2] Authenticating as Apex Institute to reach Screen B...")
        page.get_by_label("Institutional Email").fill("principal@apextech.edu")
        page.locator("input[aria-label='Password']").first.fill("ApexPrincipal@2026#Secure")
        page.get_by_role("button", name="Sign In to College Portal").click()
        time.sleep(3)

        # Verify Screen B elements (Wireframe 3: APPLY, APPLICATION STATUS, NOTIFICATIONS)
        assert "College Representative Portal" in page.content()
        assert "Apex Institute of Technology" in page.content()
        assert "APPLY" in page.content(), "Wireframe Card 1 (APPLY) not found"
        assert "APPLICATION STATUS" in page.content(), "Wireframe Card 2 (APPLICATION STATUS) not found"
        assert "NOTIFICATIONS" in page.content(), "Wireframe Card 3 (NOTIFICATIONS) not found"
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "03_screen_b_college_dashboard.png"))
        print("  -> Captured: 03_screen_b_college_dashboard.png")

        # -------------------------------------------------------------
        # 3. CARD 1: APPLY Workflow (Draft Creation & Document Upload)
        # -------------------------------------------------------------
        print("\n[STEP 3] Testing Card 1: APPLY (Application authoring & upload)...")
        page.locator("button", has_text="Open Application (Apply) →").click()
        time.sleep(2)
        assert "Statutory Approval Application (Apply)" in page.content()

        # Fill remarks & create draft
        page.locator("textarea[aria-label='Institutional Remarks & Purpose (Optional)']").fill(
            "Apex Institute Technical Campus Expansion Dossier 2026-27"
        )
        page.get_by_role("button", name="Create Application Draft").click()
        time.sleep(3)
        assert "Statutory Document Checklist" in page.content()

        # Upload mandatory documents
        mandatory_docs = [
            ("LAND_TITLE_CERTIFICATE", "Land Title Deed & Encumbrance Certificate"),
            ("BUILDING_PLAN_APPROVAL", "Approved Building Plan & Structural Sanction"),
            ("AICTE_AFFIDAVIT_1", "Registered AICTE Affidavit-1 on Stamp Paper"),
            ("FIRE_SAFETY_CERTIFICATE", "State Disaster & Fire Safety Clearance")
        ]

        for idx, (doc_code, doc_label) in enumerate(mandatory_docs):
            doc_file = f"{doc_code.lower()}.pdf"
            doc_path = os.path.join(EVIDENCE_DIR, doc_file)
            make_test_pdf(doc_path, doc_label)
            print(f"  -> Uploading ({idx+1}/4): {doc_code}...")

            # Select doc type
            selectbox = page.locator("div[data-testid='stSelectbox']").first
            selectbox.click()
            time.sleep(0.5)

            opt = page.locator("div[role='option']", has_text=doc_code).first
            opt.click()
            time.sleep(0.5)

            # Upload file
            file_input = page.locator("input[type='file']").first
            file_input.set_input_files(doc_path)
            time.sleep(1)

            page.locator("button", has_text="Upload and Audit Document").click()
            time.sleep(2.5)

        assert "Completeness: 100%" in page.content()
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "04_college_dossier_checklist_100pct.png"))
        print("  -> Captured: 04_college_dossier_checklist_100pct.png")

        # Submit application
        print("  -> Final submission of dossier...")
        page.locator("button", has_text="Final Submission for Regulatory Scrutiny").click()
        time.sleep(3)
        assert "SUBMITTED" in page.content()
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "05_college_dossier_submitted.png"))
        print("  -> Captured: 05_college_dossier_submitted.png")

        # Return to Dashboard
        page.locator("button", has_text="← Back to Applications").click()
        time.sleep(2)
        page.locator("button", has_text="← Back to Dashboard").click()
        time.sleep(2)

        # -------------------------------------------------------------
        # 4. CARD 2: APPLICATION STATUS Workflow
        # -------------------------------------------------------------
        print("\n[STEP 4] Testing Card 2: APPLICATION STATUS...")
        page.locator("button", has_text="Check Application Status →").click()
        time.sleep(2)
        assert "Institutional Application Status" in page.content()
        assert "SUBMITTED" in page.content()
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "06_college_application_status_list.png"))
        print("  -> Captured: 06_college_application_status_list.png")

        # Return to Dashboard
        page.locator("button", has_text="← Back to Dashboard").click()
        time.sleep(2)

        # Sign out from Apex
        print("  -> Signing out of College session...")
        page.locator("[data-testid='stSidebarNav'] a", has_text="Sign Out").first.click()
        time.sleep(2)

        # -------------------------------------------------------------
        # 5. SCREEN C (Wireframe 2) - Scrutiny Officer Dashboard
        # -------------------------------------------------------------
        print("\n[STEP 5] Authenticating as Scrutiny Officer to reach Screen C...")
        page.locator("button", has_text="Select Scrutiny Officer Login").click()
        time.sleep(1)
        page.get_by_label("Official AICTE Email").fill("admin@aicte.gov.in")
        page.locator("input[aria-label='Password']").first.fill("AegisAdmin@2026#Secure")
        page.get_by_role("button", name="Sign In to Scrutiny Panel").click()
        time.sleep(3)

        # Verify Screen C elements (Wireframe 2: APPLICATIONS and LOGS)
        assert "Scrutiny Officer Portal" in page.content()
        assert "APPLICATIONS" in page.content(), "Wireframe Card 1 (APPLICATIONS) missing"
        assert "LOGS" in page.content(), "Wireframe Card 2 (LOGS) missing"
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "07_screen_c_officer_dashboard.png"))
        print("  -> Captured: 07_screen_c_officer_dashboard.png")

        # -------------------------------------------------------------
        # 6. SCREEN D (Wireframe 4) - Scrutiny Officer Two-Panel Queue
        # -------------------------------------------------------------
        print("\n[STEP 6] Opening Screen D (Wireframe 4: Two-Panel Application Queue)...")
        page.locator("button", has_text="Open Scrutiny Queue →").first.click()
        time.sleep(2)

        # Verify Screen D elements: SORT BY, Left list, Right details with AI assessment
        assert "APPLICATIONS (Scrutiny Queue)" in page.content()
        assert "SORT BY" in page.content()
        assert "Selected Application Details" in page.content()
        assert ("Forensic Assessment Summary" in page.content() or "Document Verification Summary" in page.content())
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "08_screen_d_officer_twopanel_queue.png"))
        print("  -> Captured: 08_screen_d_officer_twopanel_queue.png")

        # -------------------------------------------------------------
        # 7. SCREEN E (Wireframe 5) - Individual Application Review
        # -------------------------------------------------------------
        print("\n[STEP 7] Opening Screen E (Wireframe 5: Individual Review)...")
        page.locator("button", has_text="Open Full Detailed Review →").first.click()
        time.sleep(2)

        # Verify Screen E elements: APPLICATION, COLLEGE NAME, CONTEXT, AI CHECK, ATTACHED DOCUMENTS, APPROVE/REJECT
        assert "APPLICATION:" in page.content()
        assert "COLLEGE NAME: Apex Institute of Technology" in page.content()
        assert "DETAILS OF THE APPLICATION AND CONTEXT AND WHY" in page.content()
        assert ("AI CHECK PASS / FAIL / SUS" in page.content() or "Document Verification" in page.content())
        assert "ATTACHED DOCUMENTS" in page.content()
        assert "APPROVE / REJECT" in page.content()
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "09_screen_e_individual_review.png"))
        print("  -> Captured: 09_screen_e_individual_review.png")

        # -------------------------------------------------------------
        # 8. Clarification Request from Screen E
        # -------------------------------------------------------------
        print("\n[STEP 8] Officer issuing statutory clarification request...")
        clarif_tab = page.locator("[role='tab']", has_text="Request Regulatory Clarification")
        clarif_tab.click()
        time.sleep(1)

        page.locator("textarea[aria-label='Specify the deficiency or required clarification']").fill(
            "Boundary alignment survey mismatch on Plot 42/1. Please submit certified demarcation certificate from Revenue/Municipal Surveyor."
        )
        page.locator("input[aria-label='Requested Supporting Evidence / Documents (Optional)']").fill(
            "Municipal Surveyor Demarcation Certificate (PDF)"
        )
        page.get_by_role("button", name="Issue Statutory Clarification Request").click()
        time.sleep(3)
        assert "CLARIFICATION_REQUESTED" in page.content()
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "10_officer_clarification_sent.png"))
        print("  -> Captured: 10_officer_clarification_sent.png")

        # -------------------------------------------------------------
        # 9. Card 2: LOGS (Screen C to Audit Log)
        # -------------------------------------------------------------
        print("\n[STEP 9] Inspecting Screen C Card 2: LOGS (Statutory Audit Log)...")
        page.locator("button", has_text="← Back to Application Queue").first.click()
        time.sleep(2)
        page.locator("button", has_text="← Back to Portal").first.click()
        time.sleep(2)

        page.locator("button", has_text="Inspect Audit Log →").first.click()
        time.sleep(2)
        assert "Statutory Audit Log" in page.content()
        assert "CLARIFICATION_REQUESTED" in page.content()
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "11_screen_c_audit_log.png"))
        print("  -> Captured: 11_screen_c_audit_log.png")

        # Sign out from Officer
        page.locator("[data-testid='stSidebarNav'] a", has_text="Sign Out").first.click()
        time.sleep(2)

        # -------------------------------------------------------------
        # 10. Card 3: NOTIFICATIONS Workflow (College Response with Evidence)
        # -------------------------------------------------------------
        print("\n[STEP 10] Apex logging in to inspect Card 3: NOTIFICATIONS & respond...")
        page.locator("button", has_text="Select College Representative Login").click()
        time.sleep(1)
        page.get_by_label("Institutional Email").fill("principal@apextech.edu")
        page.locator("input[aria-label='Password']").first.fill("ApexPrincipal@2026#Secure")
        page.get_by_role("button", name="Sign In to College Portal").click()
        time.sleep(3)

        # Dashboard shows Action Required on Notifications card
        assert "Action Required" in page.content()
        page.locator("button", has_text="View Notifications →").click()
        time.sleep(2)
        assert "Clarification" in page.content()

        # Submit response with supplementary surveyor PDF
        supp_pdf = os.path.join(EVIDENCE_DIR, "municipal_surveyor_demarcation.pdf")
        make_test_pdf(supp_pdf, "Municipal Surveyor Certified Demarcation Plot 42/1")

        page.locator("textarea[aria-label='Your Written Clarification Response']").fill(
            "Plot #42/1 demarcation verified by Municipal City Surveyor. Certified demarcation map attached confirming total campus area."
        )
        page.locator("input[aria-label='Attached Document Description / Reference (Optional)']").fill(
            "Municipal_Surveyor_Demarcation_Plot42.pdf"
        )
        page.locator("input[type='file']").first.set_input_files(supp_pdf)
        time.sleep(1)

        page.get_by_role("button", name="Submit Clarification Response to AICTE").click()
        time.sleep(3)
        assert ("Clarification History (Resolved)" in page.content() or "RESOLVED" in page.content())
        assert "Plot #42/1 demarcation verified" in page.content()
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "12_college_notifications_responded.png"))
        print("  -> Captured: 12_college_notifications_responded.png")

        # Sign out from Apex
        page.locator("[data-testid='stSidebarNav'] a", has_text="Sign Out").first.click()
        time.sleep(2)

        # -------------------------------------------------------------
        # 11. Final Decision: APPROVE from Screen E
        # -------------------------------------------------------------
        print("\n[STEP 11] Officer reviewing resubmitted evidence and granting APPROVAL...")
        page.locator("button", has_text="Select Scrutiny Officer Login").click()
        time.sleep(1)
        page.get_by_label("Official AICTE Email").fill("admin@aicte.gov.in")
        page.locator("input[aria-label='Password']").first.fill("AegisAdmin@2026#Secure")
        page.get_by_role("button", name="Sign In to Scrutiny Panel").click()
        time.sleep(3)

        # Queue -> Individual Review
        page.locator("button", has_text="Open Scrutiny Queue →").first.click()
        time.sleep(2)
        page.locator("button", has_text="Open Full Detailed Review →").first.click()
        time.sleep(2)

        # Select decision tab
        page.locator("[role='tab']", has_text="Record Statutory Scrutiny Outcome").first.click()
        time.sleep(1)

        # Record decision
        page.locator("input[aria-label='Official Scrutiny Remarks / Rejection Justification']").first.fill(
            "Supplementary Municipal Surveyor Demarcation Certificate verified against State Revenue GIS. All statutory requirements under AICTE Approval Process Handbook 2026-27 are fulfilled. Approval granted."
        )
        time.sleep(1)

        page.locator("button", has_text="APPROVE APPLICATION").first.click()
        time.sleep(3)
        assert "APPROVED" in page.content()
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "13_officer_decision_approved.png"))
        print("  -> Captured: 13_officer_decision_approved.png")

        # Sign out from Officer
        page.locator("[data-testid='stSidebarNav'] a", has_text="Sign Out").first.click()
        time.sleep(2)

        # -------------------------------------------------------------
        # 12. Strict Multi-Tenant Isolation (Beacon College)
        # -------------------------------------------------------------
        print("\n[STEP 12] Verifying strict Institution Isolation with Beacon College...")
        page.locator("button", has_text="Select College Representative Login").click()
        time.sleep(1)
        page.get_by_label("Institutional Email").fill("registrar@beacon.ac.in")
        page.locator("input[aria-label='Password']").first.fill("BeaconRegistrar@2026#Secure")
        page.get_by_role("button", name="Sign In to College Portal").click()
        time.sleep(3)

        assert "Beacon College of Engineering" in page.content()
        # Verify Apex Institute data is completely absent
        assert "Apex Institute" not in page.content(), "SECURITY BREACH: Apex Institute visible to Beacon College!"
        page.screenshot(path=os.path.join(EVIDENCE_DIR, "14_beacon_college_strict_isolation.png"))
        print("  -> Captured: 14_beacon_college_strict_isolation.png")

        browser.close()

    print("\n=====================================================================")
    print("ALL 12 BROWSER-LEVEL WIREFRAME SCENARIOS VERIFIED SUCCESSFULLY!")
    print("=====================================================================\n")


if __name__ == "__main__":
    run_wireframe_browser_verification()
