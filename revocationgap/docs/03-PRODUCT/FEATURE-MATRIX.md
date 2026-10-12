# Feature Matrix

Condenses PRD scope with competitive evidence (`02-RESEARCH/COMPETITIVE-ANALYSIS.md` §3–§4) and feasibility. Columns: **Rel** = release (MVP / v1.x / Later); **Diff** = charter differentiator; **Overlap** = mature-tool overlap (interoperate rather than rebuild); **Difficulty** (L/M/H); **Value** (practical security value ranking from CA §4.5); requirements are cited by id.

| Feature | Rel | Diff | Overlap with existing tools | Difficulty | Value | Requirements |
|---|---|---|---|---|---|---|
| Event-anchored exposure-window measurement with uncertainty | MVP | D-1, D-5 | None found (OAuch/OIDF are single-sample) | M | 1 | FR-TEMP-010/011, FR-ANA-001/003 |
| Positive/negative controls and identical pre/post probing | MVP | D-4 | `ignored_auth` (unauth only) | M | 1 | FR-PRB-005…008, FR-EXP-003 |
| Policy-profile outcome classification | MVP | D-3 | OAuch (spec-only) | M | 1 | FR-ANA-005/006/007 |
| Keycloak automated revocation (disable, logout, session, role/group, RT) | MVP | D-1 | — | M | 1–2 | FR-IDP-008, FR-REV-003/004/005 |
| Manual-ack experiments for any IdP | MVP | D-1 | — | L | 1 | FR-REV-002 |
| Deterministic virtual-time lab + golden datasets | MVP | D-6 | — | M | enabler | FR-LAB-001…005 |
| Schemathesis-derived protected-operation probes | MVP | D-7 | Schemathesis (reused) | M | enabler | FR-ST-001…007 |
| Refresh-token behaviour after revoke/rotate (basic RFC 7009 cross-reference to OAuch) | MVP | D-4 | OAuch basics | M | 3 | FR-IDP-004/005, SCN-04 |
| Session-cookie apps (lab) | MVP | D-4 | ZAP/Burp session tooling | M | 2 | FR-IDP-006 |
| Evidence timeline + JSON/MD/HTML reports + SVG timeline | MVP | D-8 | — | M | 1 | FR-RPT-001…005, FR-EVD-001…008 |
| Scope, audit, redaction, safe defaults | MVP | — | — | M | essential | FR-SEC-001…014 |
| Entra / Okta / Auth0 adapters (operator tenants) | v1.x | D-3 | — | H (ToS, tenants) | 1 | FR-IDP-009/010/011 |
| Password reset, CA/device-compliance actions | v1.x | D-1 | — | H | 2 | FR-REV-006/007 |
| WebSocket persistence checks | v1.x | D-1 | none for revocation | H | 6 (high impact) | FR-PRB-014 |
| GraphQL probes | v1.x | D-7 | Schemathesis | M | 4 | FR-PRB-015 |
| CAEP/SSF event→enforcement latency | v1.x | D-3 | OIDF (delivery only), SSFgo receivers | H | 4 | FR-IDP-012, FR-REV-009 |
| Cross-service/gateway comparison | v1.x (MVP-partial) | D-2 | none | M | 5 | FR-EXP-009, FR-SCN-002 |
| Historical regression of latency distributions | v1.x | D-6 | Schemathesis baseline (failures only) | M | 7 | FR-HIST-002/003 |
| ASVS/NIST profiles | v1.x | D-3 | — | L | 3 | FR-ANA-006 |
| Automated scenario generation | v1.x | D-7 | — | M | 5 | FR-SCN-005 |
| SARIF/JUnit/CSV; comparison reports | v1.x | D-8 | — | L | 5 | FR-RPT-002/006 |
| GUI control + findings UX; automation API | v1.x | — | — | M | 5 | FR-GUI-003/004, FR-API-001…003 |
| Encrypted raw evidence; third-party plugins | v1.x | D-7 | — | M | 5 | FR-SEC-011/012, FR-EVD-006 |
| Distributed workers; attack graphs; hybrid AD; SaaS connectors; temporal fuzzing | Later | — | varies | H | speculative | RG-P14-001 |
| **Excluded** — authz-matrix/BOLA, OAuth misconfig scanning, JWT forging, SSF conformance, cookie scanning, stealth | — | — | Mature tools | — | — | NG-01…NG-17 |
