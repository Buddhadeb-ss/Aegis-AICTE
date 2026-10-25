"""
Aegis Foundation - Versioned Statutory Validation Rule Registry
Defines explicit, versioned regulatory requirements for each document type.
Rules are labeled as Provisional Product Rules pending official AICTE Gazette specification.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

RULE_REGISTRY_VERSION = "2026.1.0"


@dataclass
class DocumentTypeRule:
    rule_id: str
    rule_version: str
    document_type: str
    purpose: str
    required_keywords: List[str]
    supporting_keywords: List[str]
    min_keyword_matches: int
    mandatory_for_approval: bool
    governing_framework: str
    evaluation_logic: str
    known_limitations: str


RULE_REGISTRY: Dict[str, DocumentTypeRule] = {
    "LAND_TITLE_CERTIFICATE": DocumentTypeRule(
        rule_id="RULE_LAND_TITLE_V1",
        rule_version="1.0.0",
        document_type="LAND_TITLE_CERTIFICATE",
        purpose="Verify institutional title, undisputed ownership, and land demarcations required under AICTE Norms.",
        required_keywords=["land", "survey", "plot", "deed", "ownership", "area", "acres", "revenue", "registrar"],
        supporting_keywords=["khasra", "patta", "demarcation", "sub-registrar", "stamp duty", "possession", "contiguous"],
        min_keyword_matches=2,
        mandatory_for_approval=True,
        governing_framework="AICTE Approval Process Handbook (APH 2026-27), Chapter I, Clause 1.4 (Land & Building Requirements). [Provisional Product Rule]",
        evaluation_logic="Scans extracted text for land ownership, revenue survey numbers, and registrar keywords. Scanned records are deferred to manual officer review.",
        known_limitations="Physical land titles and Patta records are frequently scanned vernacular documents (Marathi, Kannada, Hindi); automated keyword checks apply only when digital English/Hindi text streams exist."
    ),
    "BUILDING_PLAN_APPROVAL": DocumentTypeRule(
        rule_id="RULE_BUILDING_PLAN_V1",
        rule_version="1.0.0",
        document_type="BUILDING_PLAN_APPROVAL",
        purpose="Verify that campus instructional and administrative buildings have formal municipal/panchayat sanction.",
        required_keywords=["building", "plan", "approval", "sanction", "architect", "municipal", "corporation", "built-up", "floor"],
        supporting_keywords=["sq.m", "carpet area", "fsi", "far", "engineer", "town planning", "layout", "competent authority"],
        min_keyword_matches=2,
        mandatory_for_approval=True,
        governing_framework="AICTE Approval Process Handbook (APH 2026-27), Chapter I, Clause 1.5. [Provisional Product Rule]",
        evaluation_logic="Validates presence of municipal planning keywords, licensed architect references, and floor area sanction.",
        known_limitations="Blueprints and architectural drawings contain graphic vector layers that may not render as standard text streams."
    ),
    "AICTE_AFFIDAVIT_1": DocumentTypeRule(
        rule_id="RULE_AFFIDAVIT_1_V1",
        rule_version="1.0.0",
        document_type="AICTE_AFFIDAVIT_1",
        purpose="Verify sworn institutional undertaking on non-judicial stamp paper attested by an authorized Notary Public.",
        required_keywords=["affidavit", "oath", "deponent", "notary", "aicte", "undertaking", "approval process", "solemnly", "affirm"],
        supporting_keywords=["stamp", "advocate", "sworn", "verification", "non-judicial", "handbook", "statutory"],
        min_keyword_matches=2,
        mandatory_for_approval=True,
        governing_framework="AICTE Approval Process Handbook (APH 2026-27), Appendix 16 (Format for Statutory Affidavits). [Provisional Product Rule]",
        evaluation_logic="Checks for sworn legal declaration phrasing, deponent terminology, and notary attestation clauses.",
        known_limitations="Stamp paper headers and embossed notary seals require physical verification; OCR text may miss faint notary stamps."
    ),
    "FIRE_SAFETY_CERTIFICATE": DocumentTypeRule(
        rule_id="RULE_FIRE_SAFETY_V1",
        rule_version="1.0.0",
        document_type="FIRE_SAFETY_CERTIFICATE",
        purpose="Verify fire safety compliance certificate (NOC) issued by the competent Fire and Emergency Services Authority.",
        required_keywords=["fire", "safety", "noc", "certificate", "station", "officer", "prevention", "extinguisher", "inspection"],
        supporting_keywords=["hydrant", "emergency", "evacuation", "hazardous", "validity", "chief fire officer", "provisions"],
        min_keyword_matches=2,
        mandatory_for_approval=True,
        governing_framework="National Building Code of India (Part 4: Fire & Life Safety) & APH 2026-27 Clause 1.6. [Provisional Product Rule]",
        evaluation_logic="Verifies that document references fire prevention, life safety inspection, and issuing fire station authority.",
        known_limitations="Municipal fire certificates have periodic expiration dates (typically 1–3 years); validity dates must be verified against current academic session."
    ),
    "FACULTY_CADRE_CERTIFICATE": DocumentTypeRule(
        rule_id="RULE_FACULTY_CADRE_V1",
        rule_version="1.0.0",
        document_type="FACULTY_CADRE_CERTIFICATE",
        purpose="Verify faculty cadre ratio, sanctioned teaching posts, and principal/director appointment.",
        required_keywords=["faculty", "cadre", "professor", "associate", "assistant", "teaching", "ratio", "pay", "appointment"],
        supporting_keywords=["aicte", "qualification", "scale", "selection", "committee", "roster", "phd"],
        min_keyword_matches=2,
        mandatory_for_approval=True,
        governing_framework="AICTE Norms for Faculty Cadre Ratio (APH 2026-27), Chapter II. [Provisional Product Rule]",
        evaluation_logic="Validates teaching staff cadre designation, AICTE pay scale reference, and appointment details.",
        known_limitations="Faculty lists are often tabular spreadsheets embedded within PDF documents."
    ),
    "OCCUPANCY_CERTIFICATE": DocumentTypeRule(
        rule_id="RULE_OCCUPANCY_V1",
        rule_version="1.0.0",
        document_type="OCCUPANCY_CERTIFICATE",
        purpose="Verify building completion and occupancy certificate issued by the competent municipal authority.",
        required_keywords=["occupancy", "completion", "fit", "municipal", "certificate", "building", "engineer", "sanction"],
        supporting_keywords=["competent authority", "habitation", "structural", "stability", "premises"],
        min_keyword_matches=2,
        mandatory_for_approval=True,
        governing_framework="AICTE Approval Process Handbook (APH 2026-27), Chapter I, Clause 1.5. [Provisional Product Rule]",
        evaluation_logic="Checks for municipal completion/occupancy certification for the institutional campus.",
        known_limitations="Local municipal bodies issue varied formats across Indian states."
    ),
    "CLARIFICATION_EVIDENCE": DocumentTypeRule(
        rule_id="RULE_CLARIFICATION_EVIDENCE_V1",
        rule_version="1.0.0",
        document_type="CLARIFICATION_EVIDENCE",
        purpose="Evaluate supplementary evidence submitted in response to statutory scrutiny inquiries.",
        required_keywords=["certificate", "survey", "clarification", "document", "certified", "order", "report", "compliance"],
        supporting_keywords=["demarcation", "revenue", "affidavit", "resolution", "annexure"],
        min_keyword_matches=1,
        mandatory_for_approval=False,
        governing_framework="AICTE Approval Process Scrutiny Procedure — Regulatory Inquiry Response Framework. [Provisional Product Rule]",
        evaluation_logic="Checks supplementary document for evidentiary keywords relevant to the inquiry inquiry topic.",
        known_limitations="Supporting evidence varies widely based on specific officer questions (from bank guarantees to land boundary surveys)."
    )
}


def get_rule_for_document_type(doc_type: str) -> Optional[DocumentTypeRule]:
    """Retrieves the versioned rule for a declared document type."""
    return RULE_REGISTRY.get(doc_type)
