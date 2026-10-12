# RevocationGap — Master Development Roadmap

**Status:** canonical roadmap · **Registry (source of truth for IDs, dependencies and status):** [`work-elements.yaml`](work-elements.yaml) · **Progress:** [`PROGRESS.md`](PROGRESS.md) · **Traceability:** [`REQUIREMENTS-TRACEABILITY.md`](REQUIREMENTS-TRACEABILITY.md)

This assignment is **specification and planning only**. No application code is written; repository scripts under `tools/` and `research-scripts/` exist solely to validate the specification package and to verify upstream (Schemathesis) behaviour.

## 1. Governing inputs and precedence

1. The master development prompt defines scope, the 16-phase structure (Phase 0–15), the 27-section module-specification template, the sequential workflow (Steps A–I) and the final deliverables. It is preserved here without removing any phase or requirement.
2. The system prompt adds the **mandatory upstream foundation: Schemathesis** (version-pinned dependency, never a fork) and engineering-execution rules. Where the master prompt left a decision open, the choice reuses Schemathesis and mature libraries (Authlib, Keycloak as the first real IdP).
3. Conflicts are resolved by an Architecture Decision Record in [`04-ARCHITECTURE/DECISIONS/`](04-ARCHITECTURE/DECISIONS/) and recorded in the change log (§9).

## 2. Repository placement (documented decision)

The GitHub repository available to this workspace is `djshellshoxxx/PraWe-miTnegA`, an **existing, unrelated early-stage project** (ChronoFuzz / AuthorityDecay: temporal fuzzing of AI-agent workflows on SimPy; see [`02-RESEARCH/REPO-ASSESSMENT.md`](02-RESEARCH/REPO-ASSESSMENT.md)). No `RevocationGap` repository exists under the same account, and credentials in this workspace are scoped to the loaded repository. To honour "preserve existing work / do not change unrelated work", the whole RevocationGap package lives under the top-level directory **`revocationgap/`** with the master-prompt documentation structure rooted there. Nothing outside `revocationgap/` is modified. If the project is later extracted to its own repository, `git subtree split --prefix=revocationgap` preserves history; all links in the package are relative to `revocationgap/`.

## 3. Phases (mandatory structure, preserved) — goals and exit criteria

| Phase | Goal | Exit criteria (from master prompt) |
|---|---|---|
| 00 Discovery & research | Repo assessment, competitive analysis, standards, provider limits, feasibility, risks, stack evaluation, differentiation | Purpose, feasibility, closest competitors and unresolved research risks documented |
| 01 Product requirements & threat model | Personas, workflows, scope config, threat actors, assets, objectives, test-validity, FR/NFR, exclusions, MVP vs later | Every major capability has a testable requirement and an identifiable user/research purpose |
| 02 Temporal authorization model | Identity/permission/session/token/revocation/expected-enforcement/observation/timeline/clock/outcome models, state transitions | An engineer can determine exactly how an experiment transitions between states and how an outcome is classified |
| 03 Core architecture | Application architecture, boundaries, runtime, orchestration, scheduling, config, logging, plugins, events, async, persistence, DI, deployment | All components have documented responsibilities, I/O, ownership, dependencies and interfaces |
| 04 Identity adapters | Generic OAuth/OIDC, tokens, JWT, introspection, revocation, sessions, admin APIs, SSO, CAEP; Generic, Keycloak, Entra, Okta, Auth0 | Each adapter has a documented contract and capability matrix |
| 05 Probe engine | Scheduler, HTTP engine, templates, credential injection, assertions, baseline, pre/post comparison, retry, rate limit, concurrency, WebSocket, GraphQL, normalization, replay | Every probe type has precise semantics, configuration, outcomes and a reproducible validation method |
| 06 Revocation orchestration | Manual/automated revocation, disablement, role/group removal, session termination, refresh invalidation, password reset, CA, device compliance, service identity, event-driven | A precisely identified revocation event can be correlated with subsequent access outcomes |
| 07 Scenario library | Catalog of reusable temporal authorization scenarios (≥15 mandatory ones) | Every scenario reproducible in a mock environment or an explicitly supported test environment |
| 08 Evidence & analysis | Evidence, clock alignment, correlation, confidence, exposure window, classification, FP reduction, dedup, reproducibility, baselines, history, risk, report contracts | Reports distinguish confirmed findings, expected delays and inconclusive results |
| 09 Test laboratory | Mock IdP, API, session store, cache, delays, lifetimes, skew, reordered events, multi-service enforcement, fixtures, deterministic scheduling, datasets | All foundational scenarios can be evaluated against deterministic fixtures |
| 10 CLI, GUI, UX | Project → scope → auth → scenario → dry-run → revocation → run → live timeline → results → export → compare | Interface implementable without inventing controls, inputs, states, workflows or error behaviours |
| 11 Security & operations | Secrets, credentials, encrypted evidence, safe logging, plugin trust, scope, allowlists, limits, cancellation, recovery, secure defaults, validation, dependency security, offline, updates, diagnostics | Documented security model and operational procedures |
| 12 Testing & QA | Unit, integration, contract, property, state-machine, regression, adapter, negative, concurrency, fault-injection, clock-skew, performance, CLI/GUI, packaging, platform, security, reproducibility | All product requirements map to executable or objectively verifiable tests |
| 13 Build, packaging, docs | Dev env, build, reproducible builds, GitHub Actions, gates, Windows/Linux/macOS packaging, versioning, verification, licenses, install, offline install, reference docs, plugin guide, manuals, release checklist | Software can be built, installed, operated, tested and released from the spec |
| 14 Future expansion | Distributed workers, multi-IdP comparison, continuous regression, CI/CD, enterprise orchestration, attack graphs, generation, inference, connectors, AD hybrid, service-to-service, temporal fuzzing, tool integration, commercial features, baseline libraries | Prioritised roadmap separating essential, valuable and speculative |
| 15 Independent audit | Full cross-package audit; findings register; remediation; re-audit | Package is an implementation contract |

## 4. Documented deviations from the master prompt's phase structure

| ID | Change | Reason |
|---|---|---|
| RM-D1 | Phase 03 element **RG-P03-001** (system architecture, package boundaries, shared contracts, ADRs) is authored immediately after the PRD and *before* Phase 02 module specs, although numbered later. Phases are numbered by topic; authoring order is the dependency order in the registry (`tools/specgate.py order`). | Phase 02 module specs need package boundaries, the shared type vocabulary and the interface index to avoid contradictory contracts. |
| RM-D2 | Phase 00 gains an explicit **Schemathesis integration** element (RG-P00-002) producing `02-RESEARCH/SCHEMATHESIS-INTEGRATION.md`. | System-prompt mandate. |
| RM-D3 | Scenario **generation** (RG-P07-005) is placed in package `stbridge` because it consumes Schemathesis-derived OpenAPI operation catalogs. | Keeps Schemathesis out of `core`. |
| RM-D4 | Phase 10's GUI is split into architecture (P10-004), screens (P10-005) and findings UX (P10-006); automation API (P10-007) added. | Master prompt requires "automation API" as a shared surface of CLI/GUI/automation. |
| RM-D5 | Master-prompt example elements for Phase 05 are expanded to 14 elements (adds negative-control validation, GraphQL, Schemathesis bridge, replay). | Research (see SCHEMATHESIS-INTEGRATION.md §4) showed baseline/control validity and bridging are independent complex components. |
| RM-D6 | A machine-checked quality gate (`tools/specgate.py`) enforces the 27-section template, ID consistency, requirement citation and test/acceptance linkage. The traceability matrix is generated, not hand-written. | Prevents drift across ~110 elements; saves tokens. |

## 5. Schemathesis dependency and compatibility requirements (integrated into the roadmap)

Authoritative detail: [`02-RESEARCH/SCHEMATHESIS-INTEGRATION.md`](02-RESEARCH/SCHEMATHESIS-INTEGRATION.md). Roadmap-level requirements:

| ID | Requirement | Verified by |
|---|---|---|
| RM-ST-1 | Schemathesis is a **version-pinned dependency** (never forked/vendored); upstream selected for specification: **4.30.1** (MIT, Python ≥3.10, released 2026-10-09). | P13-001 lock file; P12-006 pin test |
| RM-ST-2 | Only the distribution `revocationgap-stbridge` may import `schemathesis`. `revocationgap-core`, `-idp`, `-probe`, report generation, store, lab and UIs must not. Enforced by import-linter contracts in CI. | P12-006 isolation suite |
| RM-ST-3 | Only symbols listed in the upstream "Python API" reference (loaders, `Case`, `Response`, `APIOperation`, `BaseSchema`, `hook`, `check`, `auth`, `serializer`, `APIStateMachine`) are used. `schemathesis.engine.*`, `schemathesis.config` internals and CLI internals are **not** used (undocumented/volatile). | P12-006 API-surface test |
| RM-ST-4 | Upstream cadence is high (≈ weekly minor/patch releases, Jun–Oct 2026: v4.21.10 → v4.30.1). Upgrade strategy: exact pin, scheduled weekly compatibility job against latest, manual bump after green run + changelog review. | P13-002 workflow |
| RM-ST-5 | Schemathesis behaviours that would *invalidate* a revocation measurement are explicitly neutralised: reactive re-authentication on 401 (`retry_on`), auth-token caching, random credential generation, hypothesis shrinking/retry re-sends, `X-Schemathesis-TestCaseId`/User-Agent fingerprinting. | P05-005 spec; P12-006 tests |
| RM-ST-6 | Unsupported upstream capability → dedicated adapter: WebSocket and long-lived connections (rg_probe `websocket`), identity administration (rg_idp), SET/CAEP (rg_idp), clock/time (rg_core). | P05-011, P04-*, P04-011 |

## 6. Execution model

* **One canonical roadmap** (this file + registry). **One integration coordinator** (the architect agent) owns the registry, contracts and merging.
* **Authoring order = dependency order** (`python tools/specgate.py order`). Elements are authored in *waves*; elements inside a wave only depend on COMPLETE elements of earlier waves, so they can be authored in parallel by different owners without contradicting each other. Each element has exactly one owner and one output file; owners never edit each other's files.
* **Frozen contracts first:** [`SYSTEM-ARCHITECTURE.md`](04-ARCHITECTURE/SYSTEM-ARCHITECTURE.md), [`DATA-MODEL.md`](04-ARCHITECTURE/DATA-MODEL.md) and [`INTERFACE-CONTRACTS.md`](04-ARCHITECTURE/INTERFACE-CONTRACTS.md) fix package boundaries, shared types and interface signatures before parallel work. Changing a frozen contract requires an entry in `docs/04-ARCHITECTURE/CONTRACT-CHANGELOG.md` and a sweep of dependants.
* **Quality gate per element (Steps E–H):** self-review → cross-module review against frozen contracts → `specgate check` → independent reviewer pass per wave → commit → mark COMPLETE.
* **Wave plan** (each wave closes with a cross-module review and a commit):

| Wave | Elements | Notes |
|---|---|---|
| W0 | P00-001, P00-002 + registry, tooling | Foundation, written by the coordinator (SCHEMATHESIS-INTEGRATION.md carries the preliminary package/adapter boundary) |
| W1 | P00-003, P00-004, P00-005 (parallel research agents) → P00-006 | Research integration |
| W2 | P01-001 → P01-004 | Charter, workflows, threat model, PRD (requirement IDs defined here) |
| W3 | **P03-001** (architecture, ADRs, DATA-MODEL, INTERFACE-CONTRACTS — freezes contracts) → P02-001 → P02-009 (coordinator), P03-002…P03-006 | Core temporal model + platform primitives |
| W4 | P03-007…P03-011, P04, P05, P06 (parallel by area owners) | Adapters, probes, revocation actions |
| W5 | P07, P08, P09 | Scenarios, analysis, lab |
| W6 | P10, P11 | UX, security/ops |
| W7 | P12, P13, P14 | Testing, release, future |
| W8 | P15 (fresh-context independent auditors) | Audit, remediation, re-audit |

## 7. Element registry (generated from `work-elements.yaml`)

Status legend: TODO · IN_PROGRESS · DRAFT (authored, awaiting review) · COMPLETE (passed quality gate) · BLOCKED. "Order" is the position in the global dependency-ordered authoring sequence.

<!-- BEGIN:ELEMENTS -->
#### PHASE-00 — Repository Discovery and Technical Research

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P00-001 | Repository discovery and existing-work assessment | docs | doc | — | `02-RESEARCH/REPO-ASSESSMENT.md` | 1 | COMPLETE |
| RG-P00-002 | Schemathesis integration research and adapter-boundary specification | stbridge | doc | P00-001 | `02-RESEARCH/SCHEMATHESIS-INTEGRATION.md` | 2 | COMPLETE |
| RG-P00-003 | Standards inventory and expected-enforcement reference | docs | research | P00-001 | `02-RESEARCH/STANDARDS-REFERENCE.md` | 3 | COMPLETE |
| RG-P00-004 | Competitive and prior-art analysis | docs | research | P00-001 | `02-RESEARCH/COMPETITIVE-ANALYSIS.md` | 4 | COMPLETE |
| RG-P00-005 | Identity provider and library capability research (Keycloak, Entra, Okta, Auth0, Authlib) | idp | research | P00-001 | `02-RESEARCH/providers/README.md` | 5 | COMPLETE |
| RG-P00-006 | Technical feasibility, stack evaluation, risk register, research register | docs | doc | P00-002, P00-003, P00-004, P00-005 | `02-RESEARCH/TECHNICAL-FEASIBILITY.md` | 6 | COMPLETE |

#### PHASE-01 — Product Requirements and Threat Modeling

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P01-001 | Project charter | docs | doc | P00-006 | `00-PROJECT-CHARTER.md` | 7 | TODO |
| RG-P01-002 | Personas and user workflows | docs | doc | P01-001 | `03-PRODUCT/USER-WORKFLOWS.md` | 8 | TODO |
| RG-P01-003 | Threat model (target-side attack objectives and tool-side risks) | docs | doc | P01-001 | `03-PRODUCT/THREAT-MODEL.md` | 9 | TODO |
| RG-P01-004 | Product requirements, feature matrix and MVP scope | docs | doc | P01-002, P01-003 | `03-PRODUCT/PRODUCT-REQUIREMENTS.md` | 10 | TODO |

#### PHASE-02 — Temporal Authorization Model

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P02-001 | Time and clock model | core | module | P01-004, P03-001 | `06-MODULES/RG-P02-001-time-and-clock-model.md` | 12 | TODO |
| RG-P02-002 | Identity and permission state model | core | module | P02-001 | `06-MODULES/RG-P02-002-identity-permission-state.md` | 13 | TODO |
| RG-P02-003 | Credential, session and token lifecycle model | core | module | P02-002 | `06-MODULES/RG-P02-003-credential-lifecycle.md` | 14 | TODO |
| RG-P02-004 | Revocation event model and event ordering | core | module | P02-003 | `06-MODULES/RG-P02-004-revocation-event-model.md` | 15 | TODO |
| RG-P02-005 | Expected enforcement model | core | module | P02-004 | `06-MODULES/RG-P02-005-expected-enforcement-model.md` | 16 | TODO |
| RG-P02-006 | Observation and confidence model | core | module | P02-004 | `06-MODULES/RG-P02-006-observation-confidence-model.md` | 17 | TODO |
| RG-P02-007 | Experiment state machine and transitions | core | module | P02-005, P02-006 | `06-MODULES/RG-P02-007-experiment-state-machine.md` | 18 | TODO |
| RG-P02-008 | Timeline representation | core | module | P02-006 | `06-MODULES/RG-P02-008-timeline-representation.md` | 19 | TODO |
| RG-P02-009 | Outcome classification rules | core | module | P02-005, P02-006, P02-007 | `06-MODULES/RG-P02-009-outcome-classification.md` | 20 | TODO |

#### PHASE-03 — Core System Architecture

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P03-001 | System architecture, package boundaries, shared contracts and ADRs | docs | doc | P01-004 | `04-ARCHITECTURE/SYSTEM-ARCHITECTURE.md` | 11 | TODO |
| RG-P03-002 | Shared schema and serialization framework | core | module | P03-001 | `06-MODULES/RG-P03-002-schema-serialization.md` | 21 | TODO |
| RG-P03-003 | Configuration subsystem | app | module | P03-002 | `06-MODULES/RG-P03-003-configuration.md` | 22 | TODO |
| RG-P03-004 | Logging, tracing and redaction | core | module | P03-002 | `06-MODULES/RG-P03-004-logging-redaction.md` | 23 | TODO |
| RG-P03-005 | Async model, error taxonomy and cancellation | core | module | P03-002 | `06-MODULES/RG-P03-005-async-errors-cancellation.md` | 24 | TODO |
| RG-P03-006 | Scheduler abstraction and clock injection | core | module | P02-001, P03-005 | `06-MODULES/RG-P03-006-scheduler.md` | 25 | TODO |
| RG-P03-007 | Event bus | core | module | P03-005 | `06-MODULES/RG-P03-007-event-bus.md` | 26 | TODO |
| RG-P03-008 | Persistence layer and evidence store | app | module | P03-002, P02-006 | `06-MODULES/RG-P03-008-persistence-store.md` | 27 | TODO |
| RG-P03-009 | Plugin architecture | core | module | P03-002, P03-005 | `06-MODULES/RG-P03-009-plugin-architecture.md` | 28 | TODO |
| RG-P03-010 | Experiment orchestration engine and composition root | app | module | P02-007, P03-003, P03-006, P03-007, P03-008, P03-009 | `06-MODULES/RG-P03-010-experiment-engine.md` | 29 | TODO |
| RG-P03-011 | Cross-platform deployment model | app | module | P03-001 | `06-MODULES/RG-P03-011-cross-platform-deployment.md` | 30 | TODO |

#### PHASE-04 — Authentication and Identity Adapters

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P04-001 | Identity adapter framework and capability model | idp | module | P02-004, P03-005, P03-009 | `06-MODULES/RG-P04-001-idp-adapter-framework.md` | 31 | TODO |
| RG-P04-002 | Generic OAuth/OIDC client (Authlib) | idp | module | P04-001 | `06-MODULES/RG-P04-002-oidc-client.md` | 32 | TODO |
| RG-P04-003 | Token handling and JWT analysis | idp | module | P04-002, P02-003 | `06-MODULES/RG-P04-003-token-jwt-analysis.md` | 33 | TODO |
| RG-P04-004 | Introspection, revocation and logout endpoint clients | idp | module | P04-002 | `06-MODULES/RG-P04-004-introspection-revocation-logout.md` | 34 | TODO |
| RG-P04-005 | Session-cookie and application-session adapter | idp | module | P04-001, P02-003 | `06-MODULES/RG-P04-005-session-cookie-adapter.md` | 35 | TODO |
| RG-P04-006 | Generic standards-based test-service adapter | idp | module | P04-003, P04-004 | `06-MODULES/RG-P04-006-generic-provider-adapter.md` | 36 | TODO |
| RG-P04-007 | Keycloak adapter | idp | module | P04-006, P00-005 | `06-MODULES/RG-P04-007-keycloak-adapter.md` | 37 | TODO |
| RG-P04-008 | Microsoft Entra ID adapter | idp | module | P04-006, P00-005 | `06-MODULES/RG-P04-008-entra-adapter.md` | 38 | TODO |
| RG-P04-009 | Okta adapter | idp | module | P04-006, P00-005 | `06-MODULES/RG-P04-009-okta-adapter.md` | 39 | TODO |
| RG-P04-010 | Auth0 adapter | idp | module | P04-006, P00-005 | `06-MODULES/RG-P04-010-auth0-adapter.md` | 40 | TODO |
| RG-P04-011 | SSF/CAEP event ingestion and transmission | idp | module | P04-001, P03-007 | `06-MODULES/RG-P04-011-ssf-caep.md` | 41 | TODO |

#### PHASE-05 — Probe and Offensive Test Engine

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P05-001 | Probe model and configuration | probe | module | P02-006, P03-002 | `06-MODULES/RG-P05-001-probe-model.md` | 42 | TODO |
| RG-P05-002 | Request templates and variable substitution | probe | module | P05-001 | `06-MODULES/RG-P05-002-request-templates.md` | 43 | TODO |
| RG-P05-003 | Credential and session injection | probe | module | P05-002, P02-003 | `06-MODULES/RG-P05-003-credential-injection.md` | 44 | TODO |
| RG-P05-004 | Raw HTTP transport | probe | module | P05-003, P02-001 | `06-MODULES/RG-P05-004-http-transport.md` | 45 | TODO |
| RG-P05-005 | Schemathesis bridge: operation catalog and probe derivation | stbridge | module | P05-004, P00-002 | `06-MODULES/RG-P05-005-schemathesis-bridge.md` | 46 | TODO |
| RG-P05-006 | Response assertion engine | probe | module | P05-001 | `06-MODULES/RG-P05-006-response-assertions.md` | 47 | TODO |
| RG-P05-007 | Baseline and negative-control validation | probe | module | P05-006, P05-004 | `06-MODULES/RG-P05-007-baseline-controls.md` | 48 | TODO |
| RG-P05-008 | Probe scheduling (post-revocation schedules) | probe | module | P03-006, P05-007, P02-006 | `06-MODULES/RG-P05-008-probe-scheduling.md` | 49 | TODO |
| RG-P05-009 | Rate limiting, retry and backoff | probe | module | P05-004, P03-005 | `06-MODULES/RG-P05-009-rate-limit-retry.md` | 50 | TODO |
| RG-P05-010 | Result normalization | probe | module | P05-006, P05-004, P02-006 | `06-MODULES/RG-P05-010-result-normalization.md` | 51 | TODO |
| RG-P05-011 | WebSocket persistence probe | probe | module | P05-010, P05-003 | `06-MODULES/RG-P05-011-websocket-probe.md` | 52 | TODO |
| RG-P05-012 | GraphQL probes | stbridge | module | P05-005, P05-011 | `06-MODULES/RG-P05-012-graphql-probes.md` | 53 | TODO |
| RG-P05-013 | Replay and reproducibility | probe | module | P05-010, P03-008 | `06-MODULES/RG-P05-013-replay-reproducibility.md` | 54 | TODO |
| RG-P05-014 | Probe concurrency, failure recovery and cancellation | probe | module | P05-008, P05-009, P05-010 | `06-MODULES/RG-P05-014-probe-concurrency.md` | 55 | TODO |

#### PHASE-06 — Revocation Orchestration

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P06-001 | Revocation action framework | core | module | P04-001, P02-004, P03-005 | `06-MODULES/RG-P06-001-revocation-action-framework.md` | 56 | TODO |
| RG-P06-002 | Manual revocation acknowledgment | app | module | P06-001 | `06-MODULES/RG-P06-002-manual-revocation.md` | 57 | TODO |
| RG-P06-003 | Account and entitlement removal actions (disable, delete, role, group) | idp | module | P06-001, P04-006 | `06-MODULES/RG-P06-003-account-entitlement-actions.md` | 58 | TODO |
| RG-P06-004 | Session termination and token revocation actions | idp | module | P06-001, P04-004 | `06-MODULES/RG-P06-004-session-token-actions.md` | 59 | TODO |
| RG-P06-005 | Password and credential reset actions | idp | module | P06-001 | `06-MODULES/RG-P06-005-credential-reset-actions.md` | 60 | TODO |
| RG-P06-006 | Conditional Access and device compliance changes | idp | module | P06-001, P04-008 | `06-MODULES/RG-P06-006-conditional-access-device.md` | 61 | TODO |
| RG-P06-007 | Service identity (workload) revocation | idp | module | P06-003 | `06-MODULES/RG-P06-007-service-identity-revocation.md` | 62 | TODO |
| RG-P06-008 | Event-driven and externally observed revocation | idp | module | P06-001, P04-011 | `06-MODULES/RG-P06-008-event-driven-revocation.md` | 63 | TODO |
| RG-P06-009 | Revocation correlation and acknowledgment anchoring | core | module | P06-001, P02-004, P02-001 | `06-MODULES/RG-P06-009-revocation-anchoring.md` | 64 | TODO |
| RG-P06-010 | Restoration, cleanup and reactivation | core | module | P06-003, P06-004 | `06-MODULES/RG-P06-010-restoration-cleanup.md` | 65 | TODO |

#### PHASE-07 — Attack Scenario Library

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P07-001 | Scenario definition schema (declarative DSL) | core | module | P05-001, P06-001, P02-005 | `06-MODULES/RG-P07-001-scenario-dsl.md` | 66 | TODO |
| RG-P07-002 | Scenario catalog A: credential and session lifecycle | core | module | P07-001, P06-004, P06-003 | `06-MODULES/RG-P07-002-scenario-catalog-a.md` | 67 | TODO |
| RG-P07-003 | Scenario catalog B: authorization propagation and cross-service enforcement | core | module | P07-001, P06-003, P05-011 | `06-MODULES/RG-P07-003-scenario-catalog-b.md` | 68 | TODO |
| RG-P07-004 | Scenario catalog C: events, ordering and reactivation | core | module | P07-001, P06-008, P06-010 | `06-MODULES/RG-P07-004-scenario-catalog-c.md` | 69 | TODO |
| RG-P07-005 | Automated temporal scenario generation | stbridge | module | P07-002, P07-003, P07-004, P05-005 | `06-MODULES/RG-P07-005-scenario-generation.md` | 70 | TODO |

#### PHASE-08 — Evidence, Correlation, and Finding Analysis

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P08-001 | Evidence collection and bundle format | core | module | P03-008, P05-010, P06-009 | `06-MODULES/RG-P08-001-evidence-collection.md` | 71 | TODO |
| RG-P08-002 | Clock alignment and timestamp provenance | core | module | P02-001, P08-001 | `06-MODULES/RG-P08-002-clock-alignment.md` | 72 | TODO |
| RG-P08-003 | Event correlation engine | core | module | P08-002, P06-009 | `06-MODULES/RG-P08-003-event-correlation.md` | 73 | TODO |
| RG-P08-004 | Exposure window computation | core | module | P08-003, P02-006 | `06-MODULES/RG-P08-004-exposure-window.md` | 74 | TODO |
| RG-P08-005 | Confidence scoring | core | module | P08-004 | `06-MODULES/RG-P08-005-confidence-scoring.md` | 75 | TODO |
| RG-P08-006 | Finding classification and false-positive reduction | core | module | P08-005, P02-009 | `06-MODULES/RG-P08-006-finding-classification.md` | 76 | TODO |
| RG-P08-007 | Duplicate detection and reproducibility scoring | core | module | P08-006, P05-013 | `06-MODULES/RG-P08-007-dedup-reproducibility.md` | 77 | TODO |
| RG-P08-008 | Provider enforcement baselines | core | module | P02-005, P08-006 | `06-MODULES/RG-P08-008-enforcement-baselines.md` | 78 | TODO |
| RG-P08-009 | Historical comparison and regression analysis | app | module | P08-007, P03-008 | `06-MODULES/RG-P08-009-historical-regression.md` | 79 | TODO |
| RG-P08-010 | Risk and impact scoring | core | module | P08-006 | `06-MODULES/RG-P08-010-risk-impact-scoring.md` | 80 | TODO |
| RG-P08-011 | Report data contracts and report generation | app | module | P08-006, P08-009, P08-010, P02-008 | `06-MODULES/RG-P08-011-reporting.md` | 81 | TODO |

#### PHASE-09 — Test Laboratory and Simulation Framework

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P09-001 | Lab architecture and deterministic virtual-time simulation | lab | module | P03-006, P02-007 | `06-MODULES/RG-P09-001-lab-architecture.md` | 82 | TODO |
| RG-P09-002 | Mock identity provider | lab | module | P09-001, P04-006 | `06-MODULES/RG-P09-002-mock-idp.md` | 83 | TODO |
| RG-P09-003 | Mock protected services and enforcement profiles | lab | module | P09-002 | `06-MODULES/RG-P09-003-mock-services.md` | 84 | TODO |
| RG-P09-004 | Fault and clock injection | lab | module | P09-003, P02-001 | `06-MODULES/RG-P09-004-fault-injection.md` | 85 | TODO |
| RG-P09-005 | Fixtures, expected datasets and fixture versioning | lab | module | P09-004, P07-004 | `06-MODULES/RG-P09-005-fixtures-datasets.md` | 86 | TODO |
| RG-P09-006 | Keycloak integration laboratory | lab | module | P04-007, P09-003 | `06-MODULES/RG-P09-006-keycloak-lab.md` | 87 | TODO |

#### PHASE-10 — CLI, GUI, and User Experience

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P10-001 | CLI command contract | app | module | P03-010, P08-011, P07-001 | `06-MODULES/RG-P10-001-cli-contract.md` | 88 | TODO |
| RG-P10-002 | Project workspace and configuration UX | app | module | P10-001, P03-003 | `06-MODULES/RG-P10-002-workspace-ux.md` | 89 | TODO |
| RG-P10-003 | Experiment run UX: dry run and live timeline | app | module | P10-002, P08-011 | `06-MODULES/RG-P10-003-run-ux.md` | 90 | TODO |
| RG-P10-004 | Local GUI architecture and internal web API | app | module | P10-001, P03-007 | `06-MODULES/RG-P10-004-gui-architecture.md` | 91 | TODO |
| RG-P10-005 | GUI screens and interactions | app | module | P10-004, P10-003 | `06-MODULES/RG-P10-005-gui-screens.md` | 92 | TODO |
| RG-P10-006 | Findings review, comparison and export UX | app | module | P10-005, P08-009 | `06-MODULES/RG-P10-006-findings-ux.md` | 93 | TODO |
| RG-P10-007 | Automation API | app | module | P10-004 | `06-MODULES/RG-P10-007-automation-api.md` | 94 | TODO |

#### PHASE-11 — Security and Operational Engineering

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P11-001 | Secret storage, credential lifecycle and redaction | app | module | P03-004, P03-008 | `06-MODULES/RG-P11-001-secrets-redaction.md` | 95 | TODO |
| RG-P11-002 | Scope enforcement and authorization controls | app | module | P03-003, P06-001 | `06-MODULES/RG-P11-002-scope-enforcement.md` | 96 | TODO |
| RG-P11-003 | Encrypted evidence storage | app | module | P11-001, P08-001 | `06-MODULES/RG-P11-003-evidence-encryption.md` | 97 | TODO |
| RG-P11-004 | Plugin trust boundaries | core | module | P03-009, P11-002 | `06-MODULES/RG-P11-004-plugin-trust.md` | 98 | TODO |
| RG-P11-005 | Interrupted-run recovery | app | module | P03-010, P06-010 | `06-MODULES/RG-P11-005-run-recovery.md` | 99 | TODO |
| RG-P11-006 | Diagnostics, updates, migrations and offline operation | app | module | P03-008, P03-011 | `06-MODULES/RG-P11-006-diagnostics-migrations.md` | 100 | TODO |
| RG-P11-007 | Dependency and supply-chain security | app | module | P03-011 | `06-MODULES/RG-P11-007-supply-chain.md` | 101 | TODO |

#### PHASE-12 — Testing, QA, and Verification

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P12-001 | Test strategy, coverage thresholds and quality gates | docs | doc | P09-005, P08-011 | `07-TESTING/TEST-STRATEGY.md` | 102 | TODO |
| RG-P12-002 | Property-based and state-machine model tests | docs | doc | P12-001 | `07-TESTING/MODEL-TESTS.md` | 103 | TODO |
| RG-P12-003 | Provider adapter contract tests | docs | doc | P12-001, P09-006, P04-010 | `07-TESTING/ADAPTER-CONTRACT-TESTS.md` | 104 | TODO |
| RG-P12-004 | Performance benchmark plan | docs | doc | P12-001, P05-014 | `07-TESTING/PERFORMANCE-PLAN.md` | 105 | TODO |
| RG-P12-005 | Cross-platform, CLI, GUI and packaging tests | docs | doc | P12-001, P10-006 | `07-TESTING/PLATFORM-UI-TESTS.md` | 106 | TODO |
| RG-P12-006 | Security tests and Schemathesis isolation/compatibility suite | docs | doc | P12-001, P11-007, P05-012 | `07-TESTING/SECURITY-AND-UPSTREAM-TESTS.md` | 107 | TODO |

#### PHASE-13 — Build, Packaging, Distribution, and Documentation

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P13-001 | Development environment and build system | docs | doc | P03-011, P12-001 | `09-RELEASE/BUILD-SYSTEM.md` | 108 | TODO |
| RG-P13-002 | CI/CD workflows, quality gates and release automation | docs | doc | P13-001, P12-006 | `09-RELEASE/CI-CD.md` | 109 | TODO |
| RG-P13-003 | Packaging, distribution and release checklist | docs | doc | P13-002, P12-005 | `09-RELEASE/PACKAGING-RELEASE.md` | 110 | TODO |
| RG-P13-004 | User and developer documentation plan | docs | doc | P13-003, P10-006 | `09-RELEASE/DOCUMENTATION-PLAN.md` | 111 | TODO |

#### PHASE-14 — Future Expansion and Product Strategy

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P14-001 | Future expansion and product strategy | docs | doc | P13-004 | `10-OPERATIONS/FUTURE-ROADMAP.md` | 112 | TODO |

#### PHASE-15 — Independent Specification Audit

| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |
|---|---|---|---|---|---|---|---|
| RG-P15-001 | Independent specification audit (round 1) | docs | audit | P14-001 | `SPECIFICATION-AUDIT.md` | 113 | TODO |
| RG-P15-002 | Audit remediation and re-audit | docs | audit | P15-001 | `SPECIFICATION-AUDIT.md` | 114 | TODO |
<!-- END:ELEMENTS -->

## 8. Completion conditions (global)

The roadmap is complete when `python tools/specgate.py check --final` passes (all elements COMPLETE; every requirement covered by a module spec with tests; interfaces defined and indexed), the final audit (RG-P15-002) records no open critical/high findings, and the repository state is committed and pushed (hashes recorded in `PROGRESS.md`).

## 9. Change log

| Date | Change |
|---|---|
| 2026-10-12 | Roadmap created; registry of 114 elements; deviations RM-D1…RM-D6 and Schemathesis requirements RM-ST-1…6 recorded. |
