# Technical Feasibility, Stack Evaluation, Risk Register and Differentiation (RG-P00-006)

_Integrates: [SCHEMATHESIS-INTEGRATION](SCHEMATHESIS-INTEGRATION.md), [STANDARDS-REFERENCE](STANDARDS-REFERENCE.md), [COMPETITIVE-ANALYSIS](COMPETITIVE-ANALYSIS.md), [PRIOR-ART-ACADEMIC](PRIOR-ART-ACADEMIC.md), provider research in [`providers/`](providers/). Evidence tags follow the source documents (V verified/read, I inferred, U unverified). Date: 2026-10-12._

## 1. Feasibility verdict

| Question | Verdict | Basis |
|---|---|---|
| Can the core measurement (state change at t0 → scheduled probes → last-allowed/first-denied with bounds) be made rigorous? | **Yes**, with explicit uncertainty (probe interval, orchestration latency, `Date` 1 s resolution, clock offset). | Time model is pure mathematics over timestamps RG controls; no IdP cooperation needed. Prior art is single-sample only (COMPETITIVE §0.1). |
| Is there a deterministic, free, offline *real-IdP* lab? | **Yes — Keycloak 26.8.0** ran locally (zip, `start-dev`, ≈13 s start, H2) and all revocation experiments in `providers/KEYCLOAK.md` were observed (V-lab). Docker path untested (no daemon in the research sandbox). | `research-scripts/keycloak-lab/`, `lab-assets/keycloak/revocationgap-lab-realm.json`. |
| Can Entra/Okta/Auth0 be tested in CI? | **No** as default jobs: Entra developer tenants are eligibility-gated, 90-day; Okta free org has 10 users, forbids stress/benchmark without consent; Auth0 pen-test policy requires paid tenant + 7-day notice. They are **opt-in, operator-supplied tenant** targets with conservative rate defaults and an explicit clearance gate. | `providers/ENTRA-ID.md` (d), `OKTA.md` (d), `AUTH0.md` (d). |
| Is the Schemathesis foundation viable for the HTTP layer? | **Yes**, as a request-factory/executor behind an adapter; hazardous defaults neutralised (SCHEMATHESIS-INTEGRATION §6). | Executed verification, §2/§9 of that doc. |
| Can persistent connections be tested? | **Yes** via a dedicated WebSocket probe, but semantics are mostly implementation-defined (RFC 6455 has no re-auth), so outcomes need policy profiles and often classify as `NEEDS_VERIFICATION`. | STANDARDS SV-055. |
| Can CAEP enforcement be tested? | **Partially.** Keycloak 26.7+ has an *experimental* SSF transmitter (no receiver); open-source receivers exist; Okta transmits only 2 CAEP event types; Entra's CAE is not SSF. A reproducible lab = Keycloak transmitter → RG-controlled receiver target → protected API. | COMPETITIVE §0.5; KEYCLOAK.md; OKTA.md; ENTRA-ID.md. |
| Can measurements on SaaS IdPs be deterministic? | **No**; results are statistical with bounded claims; repeated trials required. | COMPETITIVE §4.4. |

## 2. Technology stack evaluation (decisions recorded as ADRs in RG-P03-001)

| Decision | Alternatives considered | Selected | Rationale |
|---|---|---|---|
| Implementation language | Python; Go; TypeScript/Node; Rust | **Python** | System-prompt mandate (Schemathesis is Python); Authlib/joserfc/Hypothesis ecosystem; cross-platform; security-research audience familiar. Cost: GIL/threads for ST, mitigated by I/O-bound workload and process-level scaling later (Phase 14). |
| Minimum Python | 3.10 / 3.11 / 3.12 | **3.11** (test 3.11–3.14) | Python 3.10 reaches end-of-life Oct 2026 (**U**: exact date to confirm in RG-P13-001); `websockets` 17 requires ≥3.11 (providers-b); `tomllib`, `asyncio.TaskGroup`, `ExceptionGroup`. ST supports 3.10–3.14 so the range is compatible. |
| Data contracts | `pydantic` v2; `attrs`+`cattrs`; stdlib `dataclasses` + hand validation; msgspec | **pydantic v2** (frozen models) in `rg_core` | JSON Schema export for the shared-schema deliverable, strict validation at boundaries, discriminated unions, mature. Cost: dependency weight → acceptable. (`pydantic` is also a dependency of the lab web stack.) |
| HTTP stack | `requests` (ST's); `httpx`/`httpx2`; `aiohttp` | **`requests` + `urllib3`** everywhere synchronous; asyncio only for WebSocket/servers | One stack shared with ST ⇒ identical TLS/cookie/pool semantics in evidence; Authlib's httpx integration now requires `httpx2` (providers-b: breaking change) — avoided. Cost: no HTTP/2, thread offload. |
| OAuth/OIDC client | Authlib; oauthlib/requests-oauthlib; hand-written | **Authlib 1.8.0** (BSD-3, Python ≥3.10, requests-based `OAuth2Session`) for flows/introspect/revoke/discovery | System-prompt preference; active. Risks: single PyPI maintainer; `authlib.jose` deprecated since 1.7.0 → use **joserfc** for JOSE; no DPoP/back-channel/SET support (to be confirmed) → thin RG implementations. |
| JWT analysis | Authlib jose; joserfc; PyJWT; hand decoder | **Hand-written unverified decoder** (base64url JSON) for analysis + **joserfc** where signature verification is required (`JWTClaimsRegistry(now=…)` gives clock injection) | Analysis must work on tokens we cannot verify and must not enforce validation. |
| WebSocket client | `websockets`; `aiohttp`; `httpx2[ws]` | **`websockets`** (≥3.11) | asyncio-native, close-code access, maintained. |
| Scheduler / timers | asyncio + own `Scheduler` port; APScheduler 3/4; Celery | **Own small `Scheduler` port** with real (asyncio, monotonic) and virtual implementations | Injectable clock is a hard requirement (determinism, tests); APScheduler 4 still alpha (providers-b). |
| Persistence | SQLite (stdlib `sqlite3`, WAL) + content-addressed blob files; DuckDB; Postgres; JSONL only | **SQLite + blobs** | Zero-install, cross-platform, crash-safe WAL, single-file run bundle. Cost: single-writer — acceptable (one engine process per run). |
| CLI | `click`; `typer`; `argparse` | **`click`** (+`rich` for output) | Already transitive via ST; testable with `CliRunner`. |
| Local GUI | FastAPI+Jinja2+htmx (+SSE); React/Vite SPA; Textual TUI; Electron | **FastAPI + Jinja2 + htmx + SSE**, localhost-only | No Node toolchain, small packaging footprint, live timeline via SSE, shares the Python domain layer; automation API is the same app. |
| Packaging | uv + hatchling wheels; PyInstaller; Briefcase; zipapp | **Wheels (PyPI) + `uv`/`pipx` install; PyInstaller one-folder for Windows/Linux; OCI image for lab** | Python audience; offline-installable wheelhouse. |
| Quality tooling | ruff, mypy/pyright, pytest, hypothesis, import-linter, pip-audit, cyclonedx | as listed | Hypothesis is already in the ST cone; used for model tests. |
| Lab IdP | Keycloak; Dex; Ory Hydra; mock only | **Keycloak 26.8 (real) + RG mock IdP (deterministic)** | Real behaviour for integration; deterministic mock for virtual-time experiments. |
| Virtual-time simulation | SimPy 4 (sibling project); own discrete-event scheduler | **Own scheduler implementing the same `Scheduler`/`Clock` ports** (SimPy re-evaluated for pure-simulation mode in RG-P09-001) | SimPy cannot drive real asyncio I/O; ports already needed in production. |

## 3. Risk register (initial; maintained in `OPEN-QUESTIONS.md`/audit)

Severity: C critical, H high, M medium, L low. "Elem" = element that must resolve it.

| ID | Risk | Sev | Mitigation | Elem |
|---|---|---|---|---|
| R-001 | **False findings from "token still works until exp"** (protocol-expected, not a vulnerability) | C | Policy profiles (`protocol`, `asvs-5.0.0-L1…`, `nist-aal2`, `vendor-doc`); classification always records profile; JWT `exp` known ⇒ `EXPECTED` | P02-005, P02-009, P08-006 |
| R-002 | **False negatives/positives from Schemathesis re-auth/caching** | C | Neutralisations N1–N11; ISO tests | P05-005, P12-006 |
| R-003 | Measurement misrepresented as exact delay | C | Interval + uncertainty model; claims limited to bounds; wording rules in reports | P02-006, P08-004, P08-011 |
| R-004 | Non-monotonic enforcement (cache/replica skew; deny then allow) | H | N-consecutive-denial confirmation tail; flapping detection; P(allowed|t) output | P05-008, P08-004 |
| R-005 | Probe side effects / lockouts / rate limiting corrupting results | H | Safe-by-default read-only probes; rate limiter; 429 handling classified, not treated as denial | P05-009, P11-002 |
| R-006 | Destructive revocation actions against non-test identities or production | C | Scope enforcement, test-identity safeguards, allow-listed tenants, explicit `--i-have-authorization`, dry-run, restoration plans | P11-002, P06-001, P06-010 |
| R-007 | Clock misalignment (server `Date` 1 s resolution; absent in Keycloak `start-dev` responses (V-lab)) | H | Offset estimation with uncertainty; no verdict on differences ≲2 s; use IdP event timestamps as secondary anchors | P02-001, P08-002 |
| R-008 | Same-second / not-before boundary effects (Keycloak strict `iat < notBefore` on whole seconds) | M | Mandatory ≥1 s settle between baseline token minting and revocation in Keycloak adapter; recorded as `adapter_notes` | P04-007 |
| R-009 | Provider behaviour changes between versions (vendor docs drift; Keycloak latest-minor-only support) | M | Enforcement baselines versioned with provider version + doc URL + retrieval date; regression suite | P08-008 |
| R-010 | Free-tier/ToS limits on SaaS tenants (Okta consent, Auth0 7-day notice, Entra eligibility) | H | Opt-in targets; "clearance acknowledged" gate recorded in evidence; conservative default rates | P11-002, P04-008..010 |
| R-011 | Upstream (Schemathesis) churn: ≈40 releases in 16 weeks | M | Exact pin + weekly canary + minimal surface | P12-006, P13-002 |
| R-012 | Authlib single-maintainer/deprecation (`authlib.jose`) | M | Wrap Authlib behind `rg_idp.protocol` ports; joserfc for JOSE; RFC-level tests that survive a swap | P04-002 |
| R-013 | Secrets leakage into evidence/logs/reports | C | Central redaction at serialization boundary; typed `SecretStr`; canary-secret tests; encrypted evidence option | P11-001, P03-004, P11-003 |
| R-014 | Persistent-connection semantics ambiguous (no standard re-auth) | M | WebSocket outcomes default to `NEEDS_VERIFICATION` unless policy profile or vendor doc says otherwise | P05-011 |
| R-015 | CAEP/SSF immature ecosystems (Keycloak transmitter experimental; Okta 2 events) | M | CAEP features marked experimental; lab uses RG receiver; wire-format conformance left to OIDF suite | P04-011 |
| R-016 | Python thread offload limits throughput/jitter of probe scheduling | M | Bounded executor; scheduling-lateness metric recorded in every observation; targets validated by benchmark | P05-014, P12-004 |
| R-017 | Entra CAE only for CAE-capable clients (`cp1`) and resource providers; claims challenge flow requires client cooperation | M | Entra adapter models CAE capability explicitly; non-CAE-capable ⇒ classify per documented token lifetime | P04-008 |
| R-018 | Evidence volume growth in long probe campaigns | L | Delta-encoding of identical responses; body hash + capped capture; retention config | P03-008 |
| R-019 | Licence/Trademark/ToS exposure when publishing vendor-specific behaviour baselines | L | Link to vendor docs, avoid copying; version-date baselines | P08-008 |
| R-020 | Unread standards (RFC 8705/8693/8417/8935/8936, OIDC Session Mgmt, 63C-4, RFC 6265bis primary) used in design | M | Items labelled U in STANDARDS-REFERENCE §6; design must not hard-code from S/U text; second-pass read scheduled in RG-P04-011/P04-006 authoring | P04-* |
| R-021 | Specification written against Schemathesis master docs rather than pinned wheel | M | All ST claims verified against 4.30.1 (tags E/S/D); version-skew list in COMPETITIVE §2.5 | P05-005 |
| R-022 | Dual-use/abuse of the tool (unauthorised testing) | H | Scope-file requirement, banner, audit log, no stealth features; documented responsible-use policy | P01-001, P11-002 |

## 4. Differentiation (evidence-backed; from COMPETITIVE-ANALYSIS §4)

**Genuinely differentiated** (no examined tool does them): D1 event-anchored exposure-window measurement with uncertainty; D2 mechanism attribution; D3 provider-aware outcome classification; D4 CAEP event→enforcement latency; D5 cross-service enforcement comparison; D6 persistent-connection checks; D7 regression of enforcement-latency distributions.
**Overlap — interoperate, don't rebuild:** multi-identity authz matrices (AuthMatrix/Autorize/ZAP/Burp), OAuth/OIDC misconfiguration scanning and RFC 7009 basics (OAuch, OIDF suite), JWT attack suites, SSF/CAEP wire conformance (OIDF), unauth enforcement (`ignored_auth`).
**Excluded from scope:** generic authz-matrix/BOLA testing (only a pre-event control probe), generic OAuth flow scanning, JWT forgery, SSF conformance, cookie-flag scanning, a stand-alone "revoke then check once" feature (the degenerate probe schedule of length 1; cross-reference OAuch).
**Highest practical value (build first):** (1) disable/revoke-session/revoke-RT → continued-access window; (2) role/group removal & password reset propagation; (3) refresh-token behaviour (interoperate with OAuch for basics); (4) CAEP end-to-end; (5) cross-service comparison; (6) persistent connections.

## 5. Preliminary scoping consequences for the PRD (P01-004)

* **MVP** = the master-prompt §15 workflow on the deterministic lab + Keycloak: mock IdP/services, synthetic identity, baseline + controls, manual-ack and Keycloak-automated revocation (disable user, session delete, user logout, role/group removal, RT revoke), HTTP probes (schema-described via ST and raw), schedule with confirmation tail, exposure-interval computation, classification against `protocol` + `vendor-doc` profiles, evidence timeline, JSON/Markdown/HTML report, CLI. GUI = read-only live timeline + results viewer (phase 1).
* **Post-MVP (v1.x):** Entra/Okta/Auth0 adapters (operator tenants), WebSocket probe, GraphQL probes, CAEP lab, historical regression, encrypted evidence, full GUI controls.
* **Later:** distributed workers, CI integrations, attack graphs, hybrid AD, etc. (RG-P14-001).

## 6. Unresolved research items carried forward

See [`RESEARCH-REGISTER.md`](RESEARCH-REGISTER.md) §3 (each with owner element and the specification rule that applies until resolved).
