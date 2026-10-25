# Aegis — Presentation and Demonstration Asset Index

This document provides a verified index of all visual assets, screenshots, UI crops, and demonstration media in the Aegis foundation workspace (`C:\All_Projects\Aegis-Reference-Evaluation\aegis-foundation`).

All file paths are absolute and relative to the project root. Each entry specifies whether the asset is a **genuine browser capture** (from live Playwright Chromium runs on `http://localhost:8503`), a **cropped UI evidence card**, an **extracted official SIH vector/bitmap asset**, or a **synthetic test fixture**.

---

## 1. High-Impact Presentation Crops (Ready for Direct Slide Insertion)

These crops were produced specifically for presentation decks to ensure high contrast, sharp text, and immediate legibility on projector screens or PDF exports without clutter.

| Asset Filename & Path | Classification | Dimensions | Description & Function in Presentation |
| :--- | :--- | :--- | :--- |
| **`browser_evidence/presentation_crops/scenario_a_mismatch_card.png`**<br>`C:\All_Projects\Aegis-Reference-Evaluation\aegis-foundation\browser_evidence\presentation_crops\scenario_a_mismatch_card.png` | **Genuine UI Crop** | 1080 × 516 | **Scenario A Verification Card (Screen E):** Shows status `ISSUE FOUND`, `Application documents: 4/4 uploaded`, `Document matching: 3/4 matched`, `Result: 1 document needs attention`. Features the prominent red-accented box: `Expected: Land Title Certificate`, `Uploaded: Affiliation_Letter.pdf`, `Finding: The uploaded filename/category does not match the expected document`, `Action: Review document`. |
| **`browser_evidence/presentation_crops/scenario_b_clean_card.png`**<br>`C:\All_Projects\Aegis-Reference-Evaluation\aegis-foundation\browser_evidence\presentation_crops\scenario_b_clean_card.png` | **Genuine UI Crop** | 1080 × 266 | **Scenario B Verification Card (Screen E):** Shows status `CLEAR` in green, `Application documents: 4/4 uploaded`, `Document matching: 4/4 matched`, `Result: No document mismatches detected`. Proves that when all statutory documents match, zero noise is shown. |
| **`browser_evidence/presentation_crops/scenario_a_rejection_order.png`**<br>`C:\All_Projects\Aegis-Reference-Evaluation\aegis-foundation\browser_evidence\presentation_crops\scenario_a_rejection_order.png` | **Genuine UI Crop** | 1100 × 145 | **Scenario A Rejection Order:** Shows official red alert `❌ APPLICATION REJECTED · Application Deficient / Disapproved` with the recorded statutory justification: `"Application rejected due to statutory document mismatch: Affiliation Letter uploaded under Land Title requirement."` |
| **`browser_evidence/presentation_crops/scenario_b_approval_order.png`**<br>`C:\All_Projects\Aegis-Reference-Evaluation\aegis-foundation\browser_evidence\presentation_crops\scenario_b_approval_order.png` | **Genuine UI Crop** | 1100 × 145 | **Scenario B Approval Order:** Shows official green alert `✅ APPLICATION APPROVED · Official Scrutiny Order Confirmed` with the recorded remarks: `"All statutory land, building, affidavit, and fire certificates verified and cleared."` |
| **`browser_evidence/presentation_crops/college_checklist_crop.png`**<br>`C:\All_Projects\Aegis-Reference-Evaluation\aegis-foundation\browser_evidence\presentation_crops\college_checklist_crop.png` | **Genuine UI Crop** | 1080 × 170 | **College Portal Completeness (Screen B):** Shows the green progress bar at 100% with label `Completeness: 100% (4 uploaded)` and status `Ready for Submission: All mandatory statutory documents uploaded and verified`. |
| **`browser_evidence/presentation_crops/audit_trail_crop.png`**<br>`C:\All_Projects\Aegis-Reference-Evaluation\aegis-foundation\browser_evidence\presentation_crops\audit_trail_crop.png` | **Genuine UI Crop** | 1100 × 330 | **Immutable Audit Trail (Screen C):** Shows tabular rows of append-only events (`APPLICATION_APPROVED`, `APPLICATION_REJECTED`, `DOCUMENT_VALIDATED`) with actor email, entity ID, and timestamp. |
| **`browser_evidence/presentation_crops/qr_code.png`**<br>`C:\All_Projects\Aegis-Reference-Evaluation\aegis-foundation\browser_evidence\presentation_crops\qr_code.png` | **Generated Asset** | 370 × 370 | **Prototype Access QR Code:** Scannable high-contrast QR code pointing to `https://github.com/aegis-aicte/aegis-foundation`. Ideal for Slide 6 (Research & References) alongside quickstart evaluation commands. |

---

## 2. End-to-End Demonstration Captures (`run_browser_scenarios.py`)

These 14 full-screen screenshots (1440 × 950) were captured during the automated Playwright execution of `run_browser_scenarios.py` on Chromium at `http://localhost:8503`. They represent real, un-retouched browser views.

| Screenshot Filename | Role / Portal | Step in Demonstration | Key Features Visible |
| :--- | :--- | :--- | :--- |
| `browser_evidence/demo_01_gateway.png` | Public / Gateway | Step 1: Initial Landing | Gateway with role selector pills: Scrutiny Officer vs College Representative. |
| `browser_evidence/demo_02_scenario_a_college_dash.png` | College Rep | Scenario A, Step 1 | Screen B: Apex Institute dashboard with 3 navigation cards (APPLY, APPLICATION STATUS, NOTIFICATIONS). |
| `browser_evidence/demo_03_scenario_a_dossier_init.png` | College Rep | Scenario A, Step 2 | Dossier detail view showing 0% completeness and mandatory document checklist. |
| `browser_evidence/demo_04_scenario_a_college_uploaded.png`| College Rep | Scenario A, Step 3 | Uploaded documents list showing `Affiliation_Letter.pdf` uploaded under Land Title with plain-language mismatch advisory. |
| `browser_evidence/demo_05_scenario_a_college_submitted.png` | College Rep | Scenario A, Step 4 | 100% completeness reached; application status updated to `SUBMITTED`. |
| `browser_evidence/demo_06_scenario_a_officer_dash.png` | Scrutiny Officer | Scenario A, Step 5 | Screen C: Officer dashboard with APPLICATIONS (pending queue), ADD APPLICATION, and LOGS cards. |
| `browser_evidence/demo_07_scenario_a_officer_queue.png` | Scrutiny Officer | Scenario A, Step 6 | Screen D: Two-panel queue showing Apex Institute's submitted dossier selected. |
| `browser_evidence/demo_08_scenario_a_officer_mismatch_detected.png` | Scrutiny Officer | Scenario A, Step 7 | Screen E: Individual review showing `ISSUE FOUND` banner, Expected Land Title vs Uploaded Affiliation Letter. |
| `browser_evidence/demo_09_scenario_a_officer_rejection_recorded.png` | Scrutiny Officer | Scenario A, Step 8 | Screen E: Official rejection order recorded with statutory justification. |
| `browser_evidence/demo_10_scenario_b_college_all_correct.png` | College Rep | Scenario B, Step 1 | College dossier showing all 4 correct documents (`land_title_deed.pdf`, `building_plan_approval.pdf`, etc.). |
| `browser_evidence/demo_11_scenario_b_college_submitted.png` | College Rep | Scenario B, Step 2 | College dossier finalized and submitted to AICTE scrutiny queue. |
| `browser_evidence/demo_12_scenario_b_officer_clean_verdict.png` | Scrutiny Officer | Scenario B, Step 3 | Screen E: Officer review showing `CLEAR` verdict, `4/4 matched`, and clean document table. |
| `browser_evidence/demo_13_scenario_b_officer_approval_confirmed.png` | Scrutiny Officer | Scenario B, Step 4 | Screen E: Official approval order confirmed with officer remarks. |
| `browser_evidence/demo_14_statutory_audit_trail.png` | Scrutiny Officer | Scenario B, Step 5 | Screen C: Audit log viewer showing chronological events for both Scenario A rejection and Scenario B approval. |

---

## 3. Official SIH 2026 Template Assets (Directly Extracted)

Extracted directly from the official SIH 2026 PPT template PDF (`media_1792944949530.pdf`).

| Asset Filename & Path | Source | Description |
| :--- | :--- | :--- |
| **`browser_evidence/template_assets/template_p1_img1_37.jpeg`**<br>`C:\All_Projects\Aegis-Reference-Evaluation\aegis-foundation\browser_evidence\template_assets\template_p1_img1_37.jpeg` | Page 1 of SIH Template | **Official Smart India Hackathon 2026 Logo:** High-resolution official logo with text "SMART INDIA HACKATHON 2026" and tricolor brain icon. Used in top-right of presentation slides. |
| **`browser_evidence/template_assets/template_p1_img0_4.jpeg`**<br>`C:\All_Projects\Aegis-Reference-Evaluation\aegis-foundation\browser_evidence\template_assets\template_p1_img0_4.jpeg` | Page 1 of SIH Template | **Official SIH Bulb-Brain Artwork:** Central hexagonal bulb illustration with binary code pattern and SIH base. Used on Slide 1 Title Page. |

---

## 4. Rendered High-Resolution Slides

Rendered from `Aegis_SIH2026_Final_Presentation.pptx` via Microsoft PowerPoint COM export at 1920 × 1080 resolution.

| Slide Filename & Path | Slide # | Title & Theme |
| :--- | :---: | :--- |
| **`browser_evidence/final_slides/final_slide_1.png`** | Slide 1 | **TITLE PAGE:** SIH 2026 header, Problem Statement metadata, project tagline, and quick links. |
| **`browser_evidence/final_slides/final_slide_2.png`** | Slide 2 | **IDEA TITLE: AEGIS (Proposed Solution):** Executive summary banner, 4 Core Value Pillars, and Implemented Tech Stack. |
| **`browser_evidence/final_slides/final_slide_3.png`** | Slide 3 | **TECHNICAL APPROACH:** 3-Phase Architecture Pipeline (Ingestion → Validation Engine → Officer Scrutiny) with directional flow arrows. |
| **`browser_evidence/final_slides/final_slide_4.png`** | Slide 4 | **FEASIBILITY AND VIABILITY:** Real Prototype UI Crops (Scenario A vs B), Risk Mitigation, and 4-column Competitor Comparison Table. |
| **`browser_evidence/final_slides/final_slide_5.png`** | Slide 5 | **IMPACT AND BENEFITS:** 4 Top KPI Metric Badges (`<2 min`, `0 False-Pass`, `100% Audit`, `10k+ Colleges`), Stakeholder Impact, and NEP 2020 §18 Matrix. |
| **`browser_evidence/final_slides/final_slide_6.png`** | Slide 6 | **RESEARCH AND REFERENCES:** Statutory Frameworks, Technical Standards, Scannable QR Code, Local Execution Steps, and 36/36 Verification Badge. |

---

## 5. Synthetic Demonstration Fixtures (`demo_files/`)

These files in `demo_files/` are synthetically generated test PDFs used for deterministic, reproducible test execution and live browser walkthroughs:

- **`land_title_deed.pdf` / `land_title_certificate.pdf`:** Synthetic PDF containing statutory land keywords (*Land Title Deed, Survey Number 42, Patta Revenue Plot, 15 Acres, Registered conveyance*).
- **`building_plan_approval.pdf`:** Synthetic PDF containing municipal approval keywords (*Municipal Corporation Sanctioned Building Plan, Blueprint, Architect Approved Layout, built-up area*).
- **`aicte_affidavit_1.pdf`:** Synthetic PDF containing notary keywords (*AICTE Statutory Affidavit, Deponent, Notary Public, Sworn Undertaking, non-judicial stamp*).
- **`fire_safety_certificate.pdf` / `fire_safety_noc.pdf`:** Synthetic PDF containing fire prevention keywords (*Fire Safety Certificate, NOC, Chief Fire Officer, Emergency Station*).
- **`Affiliation_Letter.pdf`:** Synthetic PDF containing university affiliation keywords (*University Affiliation Letter, academic session 2026-2027*). Used specifically to trigger the category mismatch check in Scenario A.

> [!IMPORTANT]
> These demonstration files are synthetic fixtures created to test parser compliance, token concordance, and workflow states without exposing confidential institutional records. They do not represent genuine government-issued legal instruments.
