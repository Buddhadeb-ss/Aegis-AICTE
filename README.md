# Aegis Foundation — Validated Open-Source Reference Architecture

This directory contains the validated, minimal viable foundation for the **Aegis AICTE Application Scrutiny Platform**.

It implements:
1. **Streamlit Dynamic Navigation (`st.navigation` + `st.Page`)**: Eliminates directory-based multi-page URL vulnerabilities. Unauthenticated users cannot see or access private routes.
2. **Persistent Bcrypt Authentication**: Secure, salted password hashing with zero plaintext credentials stored or logged.
3. **Multi-Tenant Institutional Isolation**: Strict barriers between institutions (e.g. Apex Institute vs. Beacon College) enforced in queries and backend services.
4. **Document Forensics & Evidence Citations**: Modular PDF structural inspection (detecting incremental tampering, producer/creator drift, and consumer tool fingerprints) derived from Doc-Sentry (MIT License, Copyright (c) 2026 Spandan Mukherjee).
5. **Regulatory Clarification Workflow**: Formal inquiry-response loop with evidence resubmission and status lifecycle tracking.
6. **Immutable Audit Trail**: Chronological event logging for statutory accountability.

## Quickstart

### 1. Run Automated Acceptance Tests
```powershell
python -m pytest tests/ -v
```

### 2. Launch Application
```powershell
streamlit run streamlit_app.py --server.port 8503
```

Visit: `http://localhost:8503`

### 3. Test Credentials
- **AICTE Scrutiny Officer**: `admin@aicte.gov.in` / `AegisAdmin@2026#Secure`
- **Apex Institute Representative**: `principal@apextech.edu` / `ApexPrincipal@2026#Secure`
- **Beacon College Representative**: `registrar@beacon.ac.in` / `BeaconRegistrar@2026#Secure`
