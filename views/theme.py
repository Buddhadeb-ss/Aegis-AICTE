"""
Aegis Foundation - UI Theme & Component Design System
Implements a formal, clean, restrained government-service interface matching the wireframes:
- Navy-blue & government-blue palette (#0F172A, #1E3A8A, #2563EB)
- Clean card architecture (#FFFFFF on #F8FAFC)
- Subtle borders (#E2E8F0) and restrained box-shadows
- Consistent top header with emblem and profile/account circle control
- Reusable administrative components: Metrics Ribbon, Multi-step Wizard, Badges, Empty States
"""

import streamlit as st
from typing import Optional, Dict, Any, List


def apply_custom_css():
    """Injects core government-service design system styling."""
    st.markdown("""
    <style>
    /* Google Fonts & Base Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #0F172A;
        background-color: #F8FAFC;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1400px;
    }

    /* Government Top Header */
    .gov-header-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #0F172A;
        color: #FFFFFF;
        padding: 12px 24px;
        border-radius: 8px;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .gov-header-left {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .gov-badge {
        background: #1E3A8A;
        color: #93C5FD;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 4px 10px;
        border-radius: 4px;
        border: 1px solid #3B82F6;
    }
    .gov-header-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #FFFFFF;
        margin: 0;
    }
    .gov-header-subtitle {
        font-size: 0.8rem;
        color: #94A3B8;
        margin: 0;
    }
    .gov-profile-pill {
        display: flex;
        align-items: center;
        gap: 10px;
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 30px;
        padding: 4px 14px 4px 6px;
        color: #F1F5F9;
        font-size: 0.82rem;
    }
    .gov-avatar-circle {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: #2563EB;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.8rem;
    }

    /* Metrics Ribbon */
    .metrics-ribbon {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 14px;
        margin: 16px 0 24px 0;
    }
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
    }
    .metric-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .metric-label {
        font-size: 0.74rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748B;
    }
    .metric-icon {
        font-size: 1.15rem;
    }
    .metric-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.1;
        margin-bottom: 4px;
    }
    .metric-sub {
        font-size: 0.74rem;
        color: #94A3B8;
    }

    /* Multi-step Wizard Step Indicator */
    .wizard-steps-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 20px;
        margin-bottom: 24px;
    }
    .wizard-step-item {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .step-number-circle {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .step-active .step-number-circle {
        background: #1E3A8A;
        color: #FFFFFF;
    }
    .step-done .step-number-circle {
        background: #DCFCE7;
        color: #166534;
        border: 1px solid #86EFAC;
    }
    .step-pending .step-number-circle {
        background: #F1F5F9;
        color: #94A3B8;
        border: 1px solid #CBD5E1;
    }
    .step-label {
        font-size: 0.84rem;
        font-weight: 600;
    }
    .step-active .step-label { color: #1E3A8A; }
    .step-done .step-label { color: #166534; }
    .step-pending .step-label { color: #64748B; }

    /* Empty States */
    .empty-state-box {
        background: #FFFFFF;
        border: 1.5px dashed #CBD5E1;
        border-radius: 8px;
        padding: 36px 20px;
        text-align: center;
        margin: 16px 0;
    }
    .empty-state-icon {
        font-size: 2.2rem;
        margin-bottom: 10px;
    }
    .empty-state-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 4px;
    }
    .empty-state-desc {
        font-size: 0.85rem;
        color: #64748B;
        max-width: 480px;
        margin: 0 auto 16px auto;
        line-height: 1.5;
    }

    /* Wireframe Navigation Card System */
    .wf-card-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
        margin: 20px 0 28px 0;
    }
    .wf-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 220px;
    }
    .wf-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
        border-color: #93C5FD;
    }
    .wf-card-icon {
        font-size: 2rem;
        margin-bottom: 12px;
    }
    .wf-card-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.01em;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .wf-card-desc {
        font-size: 0.88rem;
        color: #475569;
        line-height: 1.5;
        margin-bottom: 16px;
        flex-grow: 1;
    }
    .wf-card-meta {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-top: 12px;
        border-top: 1px solid #F1F5F9;
        font-size: 0.82rem;
        color: #64748B;
        font-weight: 500;
    }

    /* Queue Two-Panel Layout */
    .queue-item {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 10px;
        transition: all 0.15s ease;
        cursor: pointer;
    }
    .queue-item:hover {
        border-color: #3B82F6;
        background: #F8FAFC;
    }
    .queue-item-active {
        background: #EFF6FF !important;
        border: 1.5px solid #2563EB !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.12);
    }

    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .badge-approved { background: #DCFCE7; color: #166534; border: 1px solid #86EFAC; }
    .badge-rejected { background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }
    .badge-submitted { background: #DBEAFE; color: #1E40AF; border: 1px solid #93C5FD; }
    .badge-clarification { background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
    .badge-clarification_requested { background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
    .badge-draft { background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }
    .badge-scrutiny { background: #E0E7FF; color: #3730A3; border: 1px solid #A5B4FC; }
    .badge-under_scrutiny { background: #E0E7FF; color: #3730A3; border: 1px solid #A5B4FC; }
    .badge-pass { background: #DCFCE7; color: #166534; border: 1px solid #86EFAC; }
    .badge-fail { background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }
    .badge-warning { background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
    .badge-review_required { background: #E0E7FF; color: #3730A3; border: 1px solid #A5B4FC; }
    .badge-not_run { background: #F1F5F9; color: #64748B; border: 1px solid #CBD5E1; }
    .badge-error { background: #FEE2E2; color: #991B1B; border: 1px solid #F87171; }
    .badge-issue_found { background: #FEE2E2; color: #991B1B; border: 1.5px solid #F87171; font-weight: 700; }
    .badge-incomplete { background: #F1F5F9; color: #475569; border: 1px solid #94A3B8; }
    .badge-cleared { background: #DCFCE7; color: #166534; border: 1.5px solid #86EFAC; font-weight: 700; }
    .badge-deficient { background: #FEE2E2; color: #991B1B; border: 1.5px solid #EF4444; font-weight: 700; }
    .badge-clear { background: #DCFCE7; color: #166534; border: 1.5px solid #86EFAC; font-weight: 700; }
    .badge-review { background: #FEF3C7; color: #92400E; border: 1.5px solid #FCD34D; font-weight: 700; }
    .badge-issue { background: #FEE2E2; color: #991B1B; border: 1.5px solid #F87171; font-weight: 700; }

    /* Primary Assessment Card */
    .assessment-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 14px;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .assessment-card:hover {
        border-color: #93C5FD;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }
    .assessment-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .assessment-card-title {
        font-weight: 700;
        font-size: 1.05rem;
        color: #0F172A;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .finding-alert-box {
        background: #FFFBEB;
        border-left: 4px solid #F59E0B;
        padding: 12px 16px;
        border-radius: 0 6px 6px 0;
        margin: 10px 0;
    }
    .finding-alert-issue {
        background: #FEF2F2;
        border-left: 4px solid #EF4444;
        padding: 12px 16px;
        border-radius: 0 6px 6px 0;
        margin: 10px 0;
    }

    /* Attached Document Card (Wireframe 5) */
    .doc-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .doc-box-title {
        font-weight: 600;
        font-size: 0.9rem;
        color: #0F172A;
        margin-bottom: 4px;
    }
    .doc-box-meta {
        font-size: 0.78rem;
        color: #64748B;
        margin-bottom: 10px;
    }

    /* AI Check Box (Wireframe 5) */
    .ai-check-card {
        background: #FFFFFF;
        border: 1.5px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }

    /* Streamlit Button Tweaks for Gov Look */
    div.stButton > button {
        border-radius: 6px;
        font-weight: 500;
        border: 1px solid #CBD5E1;
        transition: all 0.15s ease;
    }
    div.stButton > button[kind="primary"] {
        background-color: #1E3A8A;
        border-color: #1E3A8A;
        color: #FFFFFF;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #172554;
        border-color: #172554;
    }

    /* Footer Notice */
    .gov-footer {
        margin-top: 40px;
        padding-top: 16px;
        border-top: 1px solid #E2E8F0;
        text-align: center;
        font-size: 0.8rem;
        color: #64748B;
    }
    </style>
    """, unsafe_allow_html=True)


def render_header(
    portal_title: str,
    badge_label: str = "Aegis Scrutiny Platform",
    subtitle: Optional[str] = None,
    user: Optional[Dict[str, Any]] = None
):
    """
    Renders the consistent top government header with emblem badge and profile/account circle.
    Matches all wireframe top bars.
    """
    apply_custom_css()

    user_info_html = ""
    if user:
        initials = (user.get("name", "U")[:1] or "U").upper()
        inst_label = user.get("institution_code") or user.get("role", "USER").replace("_", " ").title()
        user_info_html = (
            f'<div class="gov-profile-pill" title="{user.get("name")} ({user.get("email")})">'
            f'<div class="gov-avatar-circle">{initials}</div>'
            f'<div style="line-height: 1.2;">'
            f'<div style="font-weight: 600; font-size: 0.78rem;">{user.get("name")}</div>'
            f'<div style="font-size: 0.70rem; color: #94A3B8;">{inst_label}</div>'
            f'</div></div>'
        )
    else:
        user_info_html = (
            '<div class="gov-profile-pill" title="Public Access Gateway">'
            '<div class="gov-avatar-circle" style="background: #475569;">🏛️</div>'
            '<div style="font-weight: 500; font-size: 0.78rem; color: #CBD5E1;">Public Gateway</div>'
            '</div>'
        )

    sub_html = f'<p class="gov-header-subtitle">{subtitle}</p>' if subtitle else ""

    header_html = (
        f'<div class="gov-header-bar">'
        f'<div class="gov-header-left">'
        f'<span class="gov-badge">{badge_label}</span>'
        f'<div><h1 class="gov-header-title">{portal_title}</h1>{sub_html}</div>'
        f'</div>'
        f'<div>{user_info_html}</div>'
        f'</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)


def render_breadcrumbs(crumbs: List[Dict[str, Any]]):
    """
    Renders clean, styled breadcrumbs for in-app navigation hierarchy.
    crumbs: List of dicts, e.g. [{"label": "Portal", "active": False}, {"label": "Queue", "active": True}]
    """
    if not crumbs:
        return
    parts = []
    for c in crumbs:
        label = c.get("label", "")
        icon = c.get("icon", "")
        icon_str = f"{icon} " if icon else ""
        if c.get("active"):
            parts.append(f'<span style="color: #0F172A; font-weight: 700;">{icon_str}{label}</span>')
        else:
            parts.append(f'<span style="color: #64748B;">{icon_str}{label}</span>')
    
    crumb_html = (
        '<div style="display: flex; align-items: center; gap: 8px; font-size: 0.84rem; margin-bottom: 16px; padding: 6px 14px; background: #F1F5F9; border-radius: 6px; border: 1px solid #E2E8F0;">'
        + ' <span style="color: #94A3B8; font-weight: bold;">›</span> '.join(parts)
        + '</div>'
    )
    st.markdown(crumb_html, unsafe_allow_html=True)


def render_metrics_ribbon(metrics: List[Dict[str, Any]]):
    """
    Renders a responsive metrics ribbon displaying institutional or scrutiny indicators.
    Each item: {"label": str, "value": Any, "icon": str, "sub": Optional[str], "color": Optional[str]}
    """
    if not metrics:
        return
    cards_html = []
    for m in metrics:
        label = m.get("label", "")
        val = str(m.get("value", 0))
        icon = m.get("icon", "📊")
        sub = m.get("sub", "")
        color = m.get("color", "#0F172A")
        cards_html.append(f"""
        <div class="metric-card">
            <div class="metric-header">
                <span class="metric-label">{label}</span>
                <span class="metric-icon">{icon}</span>
            </div>
            <div class="metric-value" style="color: {color};">{val}</div>
            <div class="metric-sub">{sub}</div>
        </div>
        """)
    
    html = f'<div class="metrics-ribbon">{"".join(cards_html)}</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_wizard_step_bar(steps: List[str], active_idx: int):
    """
    Renders a multi-step authoring wizard header.
    steps: e.g. ["1. Institutional Details", "2. Statutory Checklist", "3. Document Uploads", "4. Review & Submit"]
    active_idx: 0-indexed active step
    """
    step_items = []
    for i, s in enumerate(steps):
        if i < active_idx:
            status_class = "step-done"
            circle_content = "✓"
        elif i == active_idx:
            status_class = "step-active"
            circle_content = str(i + 1)
        else:
            status_class = "step-pending"
            circle_content = str(i + 1)

        step_items.append(f"""
        <div class="wizard-step-item {status_class}">
            <div class="step-number-circle">{circle_content}</div>
            <div class="step-label">{s}</div>
        </div>
        """)

    connector = '<span style="color: #CBD5E1; font-weight: bold;">───</span>'
    html = f'<div class="wizard-steps-container">{connector.join(step_items)}</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_empty_state(icon: str, title: str, description: str):
    """Renders a styled empty state placeholder."""
    st.markdown(f"""
    <div class="empty-state-box">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-desc">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def render_status_badge(status: str) -> str:
    """Returns the HTML span string for a status badge."""
    clean_status = (status or "DRAFT").strip().upper()
    badge_class = f"badge badge-{clean_status.lower()}"
    return f'<span class="{badge_class}">{clean_status.replace("_", " ")}</span>'


def render_footer():
    """Statutory footer."""
    st.markdown("""
    <div class="gov-footer">
        <strong>Aegis — National Technical Institution Validation Platform</strong><br>
        Statutory Decision-Support Architecture · AICTE Approval Process Scrutiny · Institutional Compliance System
    </div>
    """, unsafe_allow_html=True)
