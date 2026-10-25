# Aegis — Final Simplification of AI Document Review

**Document Version:** 3.0.0 (Final Minimal Architecture)  
**Status:** Approved & Implemented  
**Date:** October 2026  
**Component:** `aegis-foundation / core/validation` & `views`  
**Reference Regulation:** AICTE Approval Process Handbook (APH 2026–27)

---

## 1. Executive Summary: The Decision-Oriented Redesign

The initial version of the Aegis validation engine exposed 24 individual technical checks (byte offsets, trailer counts, regex matches), overwhelming scrutiny officers with low-level diagnostics. While an intermediate layer grouped these checks into four assessment cards, even four assessment cards exposed unnecessary cognitive overhead for the officer's routine scrutiny workflow.

This redesign establishes a **decision-oriented, exception-driven review experience**:

1. **One Application Verdict:** A single prominent verdict banner at the top of the review:
   - **`CLEAR — No issues detected by the completed checks`**
   - **`ACTION REQUIRED — Specific issues detected`**
   - **`MANUAL REVIEW REQUIRED — The evidence cannot be reliably assessed automatically`**
   - **`CHECK INCOMPLETE — Required checks could not be completed`**
2. **Show Only Exceptions:**
   - If clean: The officer sees one clear summary sentence and a compact document list, allowing them to proceed immediately without reading checklists.
   - If a problem is detected: The officer sees only the exact file, the specific problem, the supporting evidence, and the recommended action.
3. **Honest Capability Summary:**
   - Distinguishes document reading/OCR, compliance rules, cross-document comparison, and authenticity verification. Authenticity is honestly reported as **`Not verified`** because algorithmic checks cannot verify physical issuance without external issuer gateways.
4. **Single Collapsed Section ("Technical details"):**
   - All 24 underlying checks, raw JSON evidence, cryptographic hashes, execution times, and officer finding dispositions remain preserved and accessible under one collapsed expander named **`Technical details`**.
5. **Clean College Representative View:**
   - Institutional applicants see submission readiness, missing documents, and correction guidance without exposure to internal forensic risk bands, raw hashes, or diagnostic JSON.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        UPLOADED STATUTORY PDF                          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│              CORE VALIDATION PIPELINE (24 Granular Checks)             │
│  - File Integrity (5)            - Structural Diagnostics (4)          │
│  - Content & Compliance (3)      - Forensic Anomalies (8)              │
│  - Cross-Document (3)            - Typography Consistency (1)          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ Stored in SQLite (validation_runs)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│             AGGREGATION LAYER (core/validation/assessment.py)          │
│  - Application Verdict Generator                                       │
│  - Processing Capability Synthesizer                                   │
│  - Exception & Actionable Finding Formatter                            │
│  - Compact Document Priority Sorter (Issues/Reviews at top)            │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 OFFICER REVIEW INTERFACE (Screen E)                    │
│                                                                        │
│  1. ONE APPLICATION VERDICT BANNER (CLEAR / ACTION / MANUAL / INCOMPL) │
│  2. COMPACT PROCESSING CAPABILITIES SUMMARY (Honest 4-Pill Statuses)   │
│                                                                        │
│  [IF CLEAN]:                                                           │
│    "All required automated checks passed..."                           │
│    Compact Documents List (Status: Clear)                              │
│                                                                        │
│  [IF ISSUES / REVIEWS]:                                                │
│    Actionable Findings Cards:                                          │
│      File: <filename>                                                  │
│      Problem: <1 concise sentence>                                     │
│      Evidence: <specific conflicting value or missing clause>          │
│      Action: <officer next step>                                       │
│    Compact Documents List (Exceptions brought to top)                  │
│                                                                        │
│  3. COLLAPSED SECTION: "Technical details" (Optional Expander)         │
│     - 24 checks with Expected vs. Observed & Raw JSON Evidence         │
│     - Cryptographic SHA-256 Hashes, File Sizes, Engine Metrics         │
│     - Finding Disposition Form (ACCEPTED / DISMISSED / NOTED)          │
│     - Dossier Cross-Document Consistency Matrix                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. One Application Verdict: Specification & Rules

The verdict banner is rendered prominently at the top of the individual application review screen (and on the queue review panel):

| Verdict Title | When Used | Accompanying Summary Sentence |
| :--- | :--- | :--- |
| **`CLEAR — No issues detected by the completed checks`** | All required documents uploaded; all 24 checks completed with `PASS`; zero issues, zero manual reviews, zero incomplete checks. | *"All required automated checks passed. No issues were detected by these checks. Automated checks do not independently establish document authenticity."* |
| **`ACTION REQUIRED — Specific issues detected`** | One or more documents failed a mandatory requirement (e.g. missing statutory clauses, duplicate payloads, active executable scripts, or format errors). | *"One or more documents require attention before this application can proceed."* |
| **`MANUAL REVIEW REQUIRED — The evidence cannot be reliably assessed automatically`** | No mandatory failure, but automated tools cannot verify contents (e.g. scanned image documents requiring visual seal inspection, date variations, or advisory tool signatures). | *"Document evidence cannot be fully assessed by automated checks and requires manual examination by the scrutiny officer."* |
| **`CHECK INCOMPLETE — Required checks could not be completed`** | Required checks could not execute to completion due to file corruption, parsing errors, or missing documents. | *"Automated checks could not be completed for one or more submitted documents."* |

### Conservative Clearance Rules
- **Never False-Pass:** A warning, skipped check, execution error, or unverified source is **never** counted as a pass.
- **Precedence Hierarchy:**
  $$\text{Verdict} = \begin{cases} 
  \text{ACTION\_REQUIRED} & \text{if any document has } \text{ISSUE\_FOUND} \\
  \text{CHECK\_INCOMPLETE} & \text{else if any document has } \text{INCOMPLETE} \text{ or docs missing} \\
  \text{MANUAL\_REVIEW\_REQUIRED} & \text{else if any document has } \text{REVIEW\_REQUIRED} \\
  \text{CLEAR} & \text{if all documents have } \text{PASS}
  \end{cases}$$
- **Never report "No issues found"** when checks are incomplete or manual reviews remain outstanding.
- **Zero Technical Clutter in Default View:** No raw check counts (`24/24 passed`), execution runtimes (`124.5 ms`), cryptographic hashes, or internal check IDs (`DOC_TYPE_CONTENT_MATCH`) appear in the default view.

---

## 3. Honest Processing Summary

Below the verdict banner, a compact 4-item capability matrix provides honest statuses for the four core technological capabilities:

| Capability | Honest Status | Operational Basis |
| :--- | :--- | :--- |
| **Document reading/OCR** | `Passed`, `Failed`, or `Not available` | • `Passed`: All documents successfully parsed and digital text streams extracted.<br>• `Failed`: A document is corrupt or unparseable.<br>• `Not available`: A document consists of scanned images and server OCR engine is not configured. |
| **Required information checks** | `Passed`, `Issues found`, or `Incomplete` | • `Passed`: All mandatory statutory clauses and date plausibility criteria satisfied.<br>• `Issues found`: Required statutory clauses missing from document text.<br>• `Incomplete`: Unparseable file or rule execution error. |
| **Cross-document comparison** | `Passed`, `Discrepancy found`, or `Not applicable` | • `Passed`: Multiple documents verified; unique payloads and matching institution IDs.<br>• `Discrepancy found`: Duplicate files across checklist or permanent ID mismatch.<br>• `Not applicable`: Standalone single document evaluation. |
| **Authenticity verification** | **`Not verified`** | **Always marked `Not verified`** with statutory footnote: *"Automated checks do not independently establish document authenticity without issuer gateway verification."* Algorithmic checks cannot establish physical authenticity or issuer authority without external integration. |

### Negative Constraints Enforced
- **No Deceptive Claims:** Aegis does not display "AI-generated document detected" or "AI authenticity verified" because synthetic test heuristics do not equal real-world forensic verification.
- **No Presumed Forgery:** Consumer editing tool signatures (e.g., Smallpdf/iLovePDF) and inverted timestamps (scanner clock drift) are never presented as fraud evidence; they are advisory notices only.

---

## 4. Exception-Oriented Display: Show Exactly What Is Wrong

### When Application is Clean (`CLEAR`)
The officer sees:
1. Verdict banner: **`CLEAR — No issues detected by the completed checks`**
2. Exact summary sentence: *"All required automated checks passed. No issues were detected by these checks. Automated checks do not independently establish document authenticity."*
3. Capabilities Summary: Reading `Passed`, Compliance `Passed`, Cross-Doc `Passed`, Authenticity `Not verified`.
4. Compact document list with status **`Clear`** and clean download buttons.
5. The officer can immediately proceed to record the regulatory determination without wading through 24 check cards.

### When There Is a Problem (`ACTION REQUIRED` / `MANUAL REVIEW REQUIRED`)
The officer sees the **Actionable Findings** section first. Every finding displays strictly four fields:
1. **File:** The exact filename (e.g., `land_title_flawed.pdf`).
2. **Problem:** One concise sentence explaining the detected issue.
3. **Evidence:** The specific conflicting value, missing field, affected page, or observed anomaly.
4. **Action:** The next step for the scrutiny officer.

#### Real Dynamic Findings Examples (Derived from Engine Checks):
- **Missing Statutory Clauses:**
  - `File: land_certificate.pdf`
  - `Problem: A required statutory clause could not be located in Land Title Certificate.`
  - `Evidence: Missing mandatory statutory clauses: ['khasra', 'sale deed']; Matched clauses: ['affidavit'].`
  - `Action: Inspect the document or request a corrected copy.`
- **Duplicate Payload Upload:**
  - `File: fire_safety_copy.pdf`
  - `Problem: This file is identical to another submitted document.`
  - `Evidence: Identical file content matches 'land_certificate.pdf' (submitted as LAND_TITLE_CERTIFICATE).`
  - `Action: Review the discrepancy or request clarification.`
- **Permanent ID Mismatch:**
  - `File: building_plan.pdf`
  - `Problem: The institution identifier differs from another submitted document.`
  - `Evidence: This file contains 'AICTE-1-WR-9999'; the other document contains 'AICTE-1-1097241'.`
  - `Action: Review the discrepancy or request clarification.`
- **Scanned Raster Document:**
  - `File: revenue_deed_scan.pdf`
  - `Problem: The document contains scanned images without digital text streams.`
  - `Evidence: 0 digital text characters extracted across 4 page(s); raster image scan detected.`
  - `Action: Visually inspect physical seals, stamps, and signatures in the document viewer.`
- **Active JavaScript Action:**
  - `File: interactive_form.pdf`
  - `Problem: The document contains active embedded scripts or executable actions.`
  - `Evidence: Embedded script action(s) detected: ['/JavaScript'].`
  - `Action: Request a clean, static PDF replacement without interactive scripts.`

### Compact Document List (Exceptions at Top)
Below the actionable findings, a compact table/grid lists the application's documents:
- Documents with **`Issue`** appear first.
- Documents requiring **`Review`** appear second.
- Documents with **`Incomplete`** checks appear third.
- Documents that are **`Clear`** appear last.

---

## 5. Single Collapsed Control: "Technical details"

All deep diagnostics are housed behind a single collapsed control:
```python
with st.expander("🔬 Technical details", expanded=False):
```
Only when the officer explicitly expands this control do they see:
1. **Execution Metadata:** Run ID, Engine Version (`2.0.0-phase2`), Execution Timestamps.
2. **Document Inspection Tabs:** Switch between individual documents.
3. **Granular Check Table (24 checks):** Filterable by Status (`ALL`, `FAIL`, `WARNING`, `REVIEW_REQUIRED`, `PASS`, `NOT_RUN`, `ERROR`) and Category.
4. **Per-Check Technical Inspector:**
   - Expected Value vs. Observed Value.
   - Technical diagnostic details.
   - Raw formatted JSON evidence (`st.json(c["evidence"])`).
   - Execution duration in milliseconds.
5. **Officer Finding Disposition Form:** Formally record determinations (`ACCEPTED`, `DISMISSED`, `NOTED`) with mandatory justification.
6. **Re-Run Validation Button:** Trigger fresh evaluation on demand.
7. **Dossier Cross-Document Consistency Matrix:** Tabular comparison of document types, filenames, SHA-256 hashes, byte sizes, and validation outcomes across the application.

---

## 6. Simplified College Representative View

In accordance with Section 6 of the specification, institutional applicants on Screen B are protected from internal scrutiny jargon:
- **Submission Readiness Banner:**
  - Clear indicator of whether submission can proceed:
    - `"✅ Ready for Submission: All mandatory statutory documents uploaded and verified."`
    - `"📋 Submission Incomplete: Missing mandatory documents: [...]. Please upload missing items."`
    - `"⚠️ Action Needed: One or more uploaded documents require correction."`
- **Clean Document Cards:**
  - Replaced raw SHA-256 digests (`SHA-256: e3b0c44...`) and internal forensic bands (`Forensic: LOW/MEDIUM/HIGH`) with clean institutional status pills (`In Order`, `Action Needed`, `Under Scrutiny`).
- **Applicant Feedback Panel:**
  - Plain-language guidance on what needs to be uploaded or corrected (e.g. `"Please ensure institutional seals and signatures are clearly legible"`, `"Document is password protected. Please upload an unencrypted PDF"`).
  - Zero raw JSON, zero stack traces, zero technical jargon.

---

## 7. Verification & Acceptance Testing

The decision-oriented architecture is covered by automated unit, integration, and browser test suites:

### Unit & Integration Tests (34 Passed)
- **`tests/test_simplified_review.py` (8 tests):**
  1. `test_1_clean_application_shows_concise_clear_verdict`: Proves clean run produces `CLEAR` verdict and exact summary sentence.
  2. `test_2_application_with_real_issue_shows_exact_file_problem_evidence_action`: Proves real failure outputs exact `File`, `Problem`, `Evidence`, `Action` fields.
  3. `test_3_incomplete_validation_run_cannot_show_clear`: Proves pipeline errors or truncated files produce `CHECK_INCOMPLETE`.
  4. `test_4_cross_document_discrepancy_identifies_both_files_and_values`: Proves cross-document issues reference both filenames and compared values.
  5. `test_5_exceptions_sorted_to_top_of_compact_list`: Proves documents with `Issue` and `Review` sort ahead of `Clear` files.
  6. `test_6_processing_summary_distinguishes_capabilities_and_unverified_authenticity`: Proves OCR, compliance, cross-doc, and authenticity (`Not verified`) are correctly reported.
  7. `test_7_college_view_shows_actionable_guidance_without_forensic_jargon`: Proves applicant feedback panel runs cleanly without jargon or raw hashes.
  8. `test_8_end_to_end_persistence_and_technical_details_retention`: Proves all 24 checks, JSON evidence, and dispositions persist in SQLite.
- **`tests/test_assessments.py` (8 tests):** Assessment aggregation state machine.
- **`tests/test_validation_engine.py` (10 tests):** Core validation check execution.
- **`tests/test_e2e_workflow.py` (8 tests):** Regulatory workflow, tenant isolation, audit logging.

### Full Browser Workflow Verification (12 Scenarios Passed)
All 12 browser workflows in `tests/test_browser_workflow.py` executed against `http://localhost:8503` with 100% success rate:
```
=====================================================================
ALL 12 BROWSER-LEVEL WIREFRAME SCENARIOS VERIFIED SUCCESSFULLY!
=====================================================================
```

### Visual Evidence Captured (`browser_evidence/`):
- `15_screen_e_decision_oriented_verdict.png`: Shows the prominent One Application Verdict, Processing Capabilities Summary, and compact document list without technical clutter.
- `16_screen_e_technical_details_expanded.png`: Demonstrates the expanded "Technical details" section with the 24 granular checks and status filters.
- `17_screen_e_check_detail.png`: Shows the detailed check inspector with Expected vs. Observed values, raw JSON evidence, and officer finding disposition form.
