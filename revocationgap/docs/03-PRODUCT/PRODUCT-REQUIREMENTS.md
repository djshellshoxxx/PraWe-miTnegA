# RevocationGap — Product Requirements (RG-P01-004)

**Status:** v1.0 draft · **Single source of truth for requirement ids** (`FR-*`, `NFR-*`). A requirement is defined **only here**, as a heading `### <ID> — <title>`; every other document cites ids. Traceability (requirement → phase → module → interface → test → status) is generated into [`REQUIREMENTS-TRACEABILITY.md`](../REQUIREMENTS-TRACEABILITY.md) from module-spec front matter.
Inputs: [`../00-PROJECT-CHARTER.md`](../00-PROJECT-CHARTER.md) (GOAL/NG/SC/D/RU ids), [`USER-WORKFLOWS.md`](USER-WORKFLOWS.md) (PER/UC/WF/SCR), [`THREAT-MODEL.md`](THREAT-MODEL.md) (AO/SCN/TV/TM), research under [`../02-RESEARCH/`](../02-RESEARCH/).

## 1. Conventions

* **Keywords.** SHALL = mandatory; SHOULD = default behaviour that may be overridden with an audited reason; MAY = optional.
* **Priority** — `MVP` (required for the first release; master-prompt §15 workflow + MVP gate scenarios SCN-01, 02, 03, 04, 06), `v1.x` (follow-on releases after MVP), `Later` (Phase-14 strategy items, specified as design allowances only).
* **Source** cites charter/workflow/threat ids; **Verify** gives the minimum verification level: `U` unit, `I` integration (lab), `C` contract, `P` property/state-machine, `S` security test, `B` benchmark, `E` end-to-end CLI/GUI, `R` review/inspection.
* **Terminology** (charter §Glossary and `04-ARCHITECTURE/DATA-MODEL.md` §4): *experiment*, *revocation event*, *anchor* (`A_req`, `A_ack`), *probe*, *control*, *baseline*, *last confirmed access* (`L`), *first confirmed denial* (`D`), *exposure bound* (`X_lo`, `X_hi`), *policy profile*, *validation mode*. Outcome class values: `enforced, expected, documented_delay, risky_config, vulnerable, needs_verification, inconclusive` (charter short names `EXPECTED/DOC_DELAY/RISKY_CONFIG/VULN` map 1:1; `enforced` = no continued access beyond tolerance, not a finding).
* Areas: TEMP temporal model · EXP experiment lifecycle · IDP identity adapters · REV revocation orchestration · PRB probe engine · ST Schemathesis integration · SCN scenarios · EVD evidence · ANA analysis · RPT reporting · LAB laboratory · CLI · GUI · API · SEC security/safety · OPS operations · EXT extensibility · HIST regression. NFR areas: PERF · REL · PLAT · MNT · TEST · DOC · LIC · ACC.

## 2. Functional requirements

### 2.1 Temporal model and measurement (TEMP)

### FR-TEMP-001 — Dual-clock instants
The system SHALL represent every locally observed time as a `TimeInstant` (wall ns, monotonic ns, clock id, read cost) obtained only through the injected `Clock`; durations between local events SHALL be computed from monotonic readings of one clock id. **Priority:** MVP · **Source:** D-5, TM-28, TV-08 · **Verify:** U, P, R (lint rule banning direct clock calls).

### FR-TEMP-002 — Remote timestamps and clock offsets
The system SHALL model timestamps reported by other systems (HTTP `Date`, JWT claims, provider event logs, operator entries) as `RemoteInstant` with source, resolution and clock domain, and SHALL convert them to local time only through a `ClockOffset` estimate whose uncertainty widens the resulting interval. **Priority:** MVP · **Source:** TV-08, TV-24 · **Verify:** U, P.

### FR-TEMP-003 — Wall-clock anomaly detection
The system SHALL detect wall-clock steps (change in `wall − mono` offset beyond a configurable tolerance, default 50 ms) during an experiment, record a `clock_anomaly` timeline entry, and lower the confidence of any measurement spanning it. **Priority:** MVP · **Source:** TM-28 · **Verify:** U, I (virtual-clock jump injection).

### FR-TEMP-004 — Identity and permission state model
The system SHALL model, per synthetic identity, account status and a set of grants (roles, groups, scopes, entitlements) as a time-stamped `AuthorizationState`, and SHALL express every tested change as a transition between two states. **Priority:** MVP · **Source:** GOAL-01, D-1 · **Verify:** U, P.

### FR-TEMP-005 — Credential, session and token lifecycle model
The system SHALL model credentials (access/refresh/ID tokens, session cookies, API keys, service credentials) with type, format, sender binding, issuance, expiry, generation, parent/child relation and session membership, and SHALL track their lifecycle states (issued, in-use, rotated, expired, revoked-claimed, revoked-observed). **Priority:** MVP · **Source:** WF-06, SCN-04 · **Verify:** U, P.

### FR-TEMP-006 — Revocation event model
The system SHALL represent every state change under test as a `RevocationEvent` with kind, subject, affected credentials, `requested_at`, `acknowledged_at`, acknowledgment state, actor (`rg`, `operator`, `external`), provider-claimed effective time and restoration reference. **Priority:** MVP · **Source:** GOAL-03, TV-06 · **Verify:** U, C.

### FR-TEMP-007 — Event ordering
The system SHALL order revocation, restoration, observation and external events on one experiment timeline with a total order `(monotonic instant, sequence number)`, and SHALL record duplicated, delayed and out-of-order external events as such rather than discarding them. **Priority:** MVP (ordering) / v1.x (external-event anomalies) · **Source:** SCN-13, AO-07 · **Verify:** U, P.

### FR-TEMP-008 — Expected enforcement model
The system SHALL express expectations as rules keyed by (credential type, format, validation mode, event kind, policy profile) with strength (MUST/SHOULD/MAY/implementation-defined), deadline or validity rule (`must_deny_by`, `may_allow_until`, `until_exp`, `none`) and a cited source (standard section, vendor-document URL with retrieval date, or operator policy). **Priority:** MVP · **Source:** GOAL-02, D-3, SV-046 · **Verify:** U, P.

### FR-TEMP-009 — Observation and confidence model
The system SHALL represent each probe attempt as an `Observation` carrying intended time, send/receive instants, scheduling lateness, outcome (`access_confirmed`, `access_denied`, `indeterminate`, `transport_error`, `not_sent`), assertion results, mechanism hints and an evidence reference, and SHALL derive confidence from enumerated, recorded factors. **Priority:** MVP · **Source:** D-5, TV-05 · **Verify:** U, P.

### FR-TEMP-010 — Exposure bounds
The system SHALL compute, per (credential, target, event), the entailed bounds `X_lo = max(0, s_L − A_ack)` and `X_hi = r_D − A_req`, the localization width `W = r_D − s_L`, censoring (no stable denial by the horizon) and flapping, exactly as defined in `DATA-MODEL.md` §4, and SHALL NOT publish a point estimate of delay. **Priority:** MVP · **Source:** GOAL-01, SC-01, SC-02, NG-12 · **Verify:** U, P, I (SC-01 ground-truth containment).

### FR-TEMP-011 — Confirmation tail and stable denial
The system SHALL declare a first confirmed denial `D` only after the configured confirmation tail (default ≥ 3 consecutive denials and ≥ max(3 × probe interval, 10 s) of monotone time, with no later `access_confirmed`), SHALL mark `D` provisional when the horizon ends first, and SHALL report flapping separately. **Priority:** MVP · **Source:** TV-07, R-004 · **Verify:** U, P.

### FR-TEMP-012 — Experiment state machine
The system SHALL execute every experiment through the states DRAFT, VALIDATED, BASELINING, ARMED, REVOKING, OBSERVING, ANALYZING, CLEANING_UP and a terminal state (COMPLETE, INCONCLUSIVE, FAILED, ABORTED) per a published transition table with guards, and SHALL reject any transition not in the table. **Priority:** MVP · **Source:** WF-01, WF-11 · **Verify:** U, P (state-machine model test), I.

### 2.2 Experiment lifecycle and orchestration (EXP)

### FR-EXP-001 — Declarative experiment specification
An experiment SHALL be fully described by a serialisable, secret-free `ExperimentSpec` (scenario, targets, providers, identities by handle, probes, revocation action, expectations, schedule, horizons, scope reference, policy profiles); the spec digest SHALL be recorded in the run manifest. **Priority:** MVP · **Source:** D-6, ADR-0012 · **Verify:** U, C.

### FR-EXP-002 — Pre-arming validation and dry run
The system SHALL provide a validation/dry-run that resolves the spec, checks scope for every planned action, verifies provider capabilities for every planned operation, renders each planned request/action without sending it, and reports all problems at once with stable error codes. **Priority:** MVP · **Source:** WF-02 · **Verify:** I, E.

### FR-EXP-003 — Baseline and control gate
The system SHALL NOT enter ARMED unless, for every credential under test, a positive baseline has `access_confirmed` and every required negative control (no credential, garbage credential; sibling/foreign controls when configured) is `access_denied`; otherwise the experiment SHALL end `INCONCLUSIVE` with the failed control identified. **Priority:** MVP · **Source:** TV-01, TV-02, SC-04 · **Verify:** I, P.

### FR-EXP-004 — Arming confirmation
Arming an experiment that contains mutating actions SHALL require explicit operator confirmation naming the tenant/realm identifier (interactive or a pre-declared confirmation token in the scope file for CI), and SHALL pin the scope digest. **Priority:** MVP · **Source:** RU-03, TM-05, TM-06 · **Verify:** S, E.

### FR-EXP-005 — Settle interval
The system SHALL enforce a configurable settle interval (provider-adapter default; 1 s minimum for providers evaluating `iat < notBefore` at second resolution) between the last credential minting and the revocation action. **Priority:** MVP · **Source:** TV-15, R-008 · **Verify:** I.

### FR-EXP-006 — Observation horizon and stop rules
The system SHALL stop observing when the confirmation tail is satisfied for all credentials, or when the horizon elapses, or on abort/rate-limit stop, and SHALL record which rule ended observation. **Priority:** MVP · **Source:** WF-01 · **Verify:** U, I.

### FR-EXP-007 — Guaranteed cleanup
After any experiment that mutated state, the system SHALL attempt restoration per the restoration ledger regardless of outcome (including FAILED and ABORTED), SHALL verify restoration where the provider allows, and SHALL list residual state explicitly in the report. **Priority:** MVP · **Source:** WF-11, SC-13 · **Verify:** I, P (kill injection).

### FR-EXP-008 — Interrupted-run recovery
After a crash or kill at any state, the system SHALL recover the experiment from durable records, determine the last durable transition, and either resume, finalise as INCONCLUSIVE or run cleanup, according to a published recovery table; no durable observation SHALL be lost or duplicated. **Priority:** MVP · **Source:** WF-11, SC-13 · **Verify:** I, P.

### FR-EXP-009 — Multi-credential and multi-target experiments
An experiment SHALL support several credentials (existing session, new session, refresh token, alternative token) and several targets against one revocation event, producing independent exposure bounds per (credential, target). **Priority:** MVP (≥2 credentials, ≥2 targets in lab) · **Source:** GOAL-08, WF-05 · **Verify:** I.

### FR-EXP-010 — Single active experiment per workspace
The system SHALL enforce one active experiment per workspace via a portable lock and SHALL report a clear error naming the holder when a second start is attempted. **Priority:** MVP · **Source:** ADR-0005 · **Verify:** U, I.

### 2.3 Identity provider adapters (IDP)

### FR-IDP-001 — Adapter contract and capability discovery
Every provider adapter SHALL implement the composite adapter contract and SHALL expose a `ProviderCapabilities` document derived from discovery plus declared, evidence-referenced flags; operations outside declared capabilities SHALL raise a typed UNSUPPORTED error and never be attempted blindly. **Priority:** MVP · **Source:** GOAL-09, GOAL-13, SC-10, TV-10 · **Verify:** C.

### FR-IDP-002 — Generic OAuth 2.0 / OIDC client
The system SHALL acquire credentials from standards-based providers through Authlib using OIDC discovery (and RFC 8414 metadata), supporting at minimum the resource-owner password grant (lab/test identities), client-credentials grant, and a scripted authorization-code + PKCE flow where the provider permits non-interactive form login. **Priority:** MVP (password, client-credentials) / v1.x (scripted code+PKCE, device) · **Source:** WF-01, WF-03, NG-16 · **Verify:** I, C.

### FR-IDP-003 — Token handling and JWT analysis
The system SHALL decode JWTs **without** verification for analysis (header, allow-listed claims, `exp`/`iat`/`nbf`/`jti`/`sid`/`aud`), SHALL classify tokens as JWT/opaque/other, SHALL compute remaining lifetime against the aligned clock, and SHALL perform signature verification only where explicitly requested, using joserfc with an injected clock. **Priority:** MVP · **Source:** TV-09, SV-010–012 · **Verify:** U, P.

### FR-IDP-004 — Introspection, revocation and logout clients
The system SHALL implement RFC 7662 introspection, RFC 7009 revocation, OIDC RP-initiated logout, and back-channel/front-channel logout interactions as independent-oracle and action primitives, treating their success responses as non-proof of state (verification via a separate oracle). **Priority:** MVP (introspection, revocation, RP-initiated logout) / v1.x (back/front-channel) · **Source:** TV-04, SV-005 · **Verify:** C, I.

### FR-IDP-005 — Refresh handling with isolation
The system SHALL perform refresh-token checks using a disposable token family per probe slot so that rotation or reuse detection triggered by one probe cannot contaminate other observations, and SHALL record rotation/reuse outcomes as evidence. **Priority:** MVP · **Source:** TV-12, SCN-04 · **Verify:** I.

### FR-IDP-006 — Session-cookie and application-session adapter
The system SHALL support credentials that are application session cookies (form/JSON login, cookie jar per identity, CSRF-token handling, session identifier fingerprinting) as first-class credentials with per-identity jars isolated from other identities. **Priority:** MVP (lab app) / v1.x (third-party apps) · **Source:** WF-06 · **Verify:** I.

### FR-IDP-007 — Generic standards-based test-service adapter
The system SHALL provide a generic adapter operating purely from discovery metadata and operator-supplied endpoint mappings, used for the lab mock IdP and for any standards-only provider, with every non-discoverable capability explicitly declared by the operator and labelled `assumed`. **Priority:** MVP · **Source:** WF-01 · **Verify:** C, I.

### FR-IDP-008 — Keycloak adapter
The system SHALL provide a Keycloak adapter (verified against 26.8.x) with admin operations: create/disable/enable/delete user, user logout (`POST …/users/{id}/logout`), delete session, realm not-before push, role and group mapping add/remove, password reset, session listing, admin/user event reading; it SHALL document required realm-management roles and enforce the ≥ 1 s not-before settle rule. **Priority:** MVP · **Source:** WF-03, RF-1…3, TV-15 · **Verify:** I (Keycloak lab), C.

### FR-IDP-009 — Microsoft Entra ID adapter
The system SHALL provide an Entra adapter using Microsoft Graph with operator-supplied tenant credentials: disable user, `revokeSignInSessions`, group and app-role assignment removal, sign-in/audit log reading; it SHALL model CAE capability and claims-challenge responses and SHALL NOT assume RFC 7009/7662 endpoints. **Priority:** v1.x · **Source:** RF-4, RF-5, R-017 · **Verify:** C (recorded fixtures), I (operator tenant, opt-in).

### FR-IDP-010 — Okta adapter
The system SHALL provide an Okta adapter (Management API): suspend/deactivate/unsuspend user, clear sessions, revoke tokens/grants, group membership removal, System Log reading, with rate-limit-header pacing and the Okta clearance gate. **Priority:** v1.x · **Source:** RF-6, R-010 · **Verify:** C, I (operator org, opt-in).

### FR-IDP-011 — Auth0 adapter
The system SHALL provide an Auth0 adapter: block/unblock user, `/oauth/revoke`, grants API; Sessions/refresh-token Management API only when the tenant capability probe shows Enterprise availability; it SHALL honour the 2 req/s Management API limit on Free tenants and the paid-tenant/notice clearance gate. **Priority:** v1.x · **Source:** RF-7, R-010 · **Verify:** C, I (operator tenant, opt-in).

### FR-IDP-012 — SSF/CAEP event ingestion and transmission
The system SHALL ingest SETs (push receiver on loopback or configured HTTPS URL, and poll), verify signature and issuer, de-duplicate by `jti`, record receipt instants, and expose events as `external_signal` revocation events; it SHALL support RG-controlled transmission of test events in the lab; it SHALL treat Keycloak SSF as experimental. **Priority:** v1.x · **Source:** WF-08, TM-19…21 · **Verify:** C, I.

### FR-IDP-013 — Provider-claim evidence discipline
Every capability declared by an adapter SHALL reference a research row tagged V/V-doc/V-src/V-lab; anything else SHALL be declared `assumed` and covered by a falsifying contract test. **Priority:** MVP · **Source:** SC-10, GOAL-13 · **Verify:** C, R.

### FR-IDP-014 — Admin credential minimisation
Adapters SHALL document and request the minimum provider privileges per operation, SHALL separate the admin credential from test-identity credentials, and SHALL refuse admin calls whose target identity is not declared synthetic in scope. **Priority:** MVP · **Source:** TM-09, RU-04 · **Verify:** S, C.

### 2.4 Revocation orchestration (REV)

### FR-REV-001 — Revocation action framework
Revocation actions SHALL implement a common contract (descriptor, plan, execute, verify, restore) with declared prerequisites, required provider permissions, expected side effects, action class (`observe`, `authenticate`, `mutate_identity`, `mutate_policy`) and restorability, and SHALL be dry-runnable via `plan`. **Priority:** MVP · **Source:** GOAL-03, ADR-0011 · **Verify:** C.

### FR-REV-002 — Manual revocation acknowledgment
The system SHALL support manual revocation: the operator performs the change out-of-band and signals "starting" (M1) and "acknowledged" (M2); the anchor SHALL be M2 with anchor uncertainty [M1, M2], and operator-asserted vendor timestamps SHALL be recorded as `assumed`. **Priority:** MVP · **Source:** WF-04 · **Verify:** I, E.

### FR-REV-003 — Account disablement and deletion
The system SHALL provide actions to disable, delete and (for restoration/reactivation scenarios) re-enable synthetic accounts through adapters that declare the capability. **Priority:** MVP (Keycloak, mock IdP) · **Source:** SCN-02, SCN-14 · **Verify:** I.

### FR-REV-004 — Role, group and entitlement removal
The system SHALL provide actions to remove (and restore) role mappings, group memberships and entitlements/scopes for synthetic identities. **Priority:** MVP (Keycloak, mock IdP) · **Source:** SCN-01, SCN-05, SCN-06 · **Verify:** I.

### FR-REV-005 — Session termination and token revocation
The system SHALL provide actions for single-session termination, global user logout, refresh-token revocation (RFC 7009), access-token revocation where the provider supports it, grant revocation and realm/tenant not-before advancement. **Priority:** MVP (Keycloak, mock IdP) · **Source:** SCN-03, SCN-04 · **Verify:** I.

### FR-REV-006 — Password and credential reset
The system SHALL provide password-reset/password-change and credential-reset actions for synthetic identities, recording provider-documented side effects (e.g. Keycloak admin reset invalidates nothing). **Priority:** v1.x · **Source:** RF-2, STD ASVS V7.4.3 · **Verify:** I.

### FR-REV-007 — Conditional Access and device-compliance changes
Where a provider exposes a documented, automatable interface, the system SHALL support Conditional Access policy and device-compliance changes as `mutate_policy` actions requiring dedicated scope entries; where no direct interface exists, the scenario SHALL fall back to manual acknowledgment. **Priority:** v1.x · **Source:** MP Phase 6, ENTRA-ID.md · **Verify:** C, R.

### FR-REV-008 — Service identity revocation
The system SHALL provide actions for disabling/rotating workload identities (client credentials, service-account users) and verifying that client-credentials tokens are rejected per expectation. **Priority:** MVP (Keycloak, mock IdP) · **Source:** SCN-10 · **Verify:** I.

### FR-REV-009 — Event-driven and externally observed revocation
The system SHALL support experiments anchored on an externally caused event (CAEP/SSF event received, provider log entry, webhook), recording `ack_state=observed` and the anchor uncertainty from receipt latency and clock offset. **Priority:** v1.x · **Source:** WF-08, AO-07 · **Verify:** I.

### FR-REV-010 — Anchor recording
For automated actions the system SHALL record `requested_at` immediately before the state-changing request is dispatched and `acknowledged_at` immediately after the provider's acceptance is received, from the same monotonic clock as probes; a missing or failed acknowledgment SHALL yield `ack_state` `rejected`/`indeterminate` and an `inconclusive` exposure result. **Priority:** MVP · **Source:** TV-06, SC-02 · **Verify:** U, I.

### FR-REV-011 — Independent verification of the change
After execution, the system SHALL verify the state change through an independent read (`read_state`, oracle, admin API) and record the result; a revoke action whose success cannot be independently verified SHALL be flagged in the report. **Priority:** MVP · **Source:** TV-04 · **Verify:** I.

### FR-REV-012 — Restoration ledger
Every executed action SHALL append to a restoration ledger (what was changed, previous value, restore procedure, verification), persisted before the action executes (write-ahead) so recovery can restore after a crash. **Priority:** MVP · **Source:** WF-11, SC-13 · **Verify:** I, P.

### 2.5 Probe engine (PRB)

### FR-PRB-001 — Probe definition
A probe SHALL be defined by kind, category, target, request template (or WebSocket/oracle specification), credential binding, assertions (positive access, denial signals, guards), control kind, schedule and safety class; probe definitions SHALL be validated before use. **Priority:** MVP · **Source:** GOAL-04 · **Verify:** U, C.

### FR-PRB-002 — Request templates
Request templates SHALL support parameter substitution from experiment variables and identity attributes, SHALL reject CR/LF in header values and unresolved placeholders, and SHALL render to a secret-free `PreparedProbeRequest` snapshot. **Priority:** MVP · **Source:** TM-14, ADR-0012 · **Verify:** U, S.

### FR-PRB-003 — Credential injection
Credentials SHALL be injected per call (header, cookie, query only when the operation declares it, body) from `RequestAuth` built from in-memory material, never written into templates or snapshots, with per-identity cookie jars and connection pools. **Priority:** MVP · **Source:** TM-07, ISO-4 · **Verify:** U, S.

### FR-PRB-004 — Raw HTTP transport
The system SHALL provide an HTTP transport over `requests` with explicit timeouts, `allow_redirects=False`, TLS verification on by default, body-size caps, per-probe fresh-connection or reuse policy, and timestamps taken inside the worker immediately around the wire call. **Priority:** MVP · **Source:** TM-01, TM-10, N8, N9 · **Verify:** U, I, S.

### FR-PRB-005 — Response assertions
The assertion engine SHALL evaluate declarative assertions over normalised exchanges — status sets, header presence/value/regex, JSON-pointer/JSONPath value and schema checks, body markers/regex/hash, redirect-target checks, `WWW-Authenticate` parsing, size bounds — and SHALL classify each as positive-access, denial-signal or guard. An exchange SHALL be `access_confirmed` only if all required positive assertions pass; an HTTP 200 alone SHALL NEVER confirm access. **Priority:** MVP · **Source:** SC-04, TV-05 · **Verify:** U, P (mutation suite).

### FR-PRB-006 — Baseline validation
The system SHALL execute baseline probes with each credential before the event, verify positive assertions on the frozen request, and record the baseline snapshot used by all later probes of that credential. **Priority:** MVP · **Source:** TV-01, TV-03 · **Verify:** I.

### FR-PRB-007 — Negative-control validation
The system SHALL execute no-credential and garbage-credential controls (and sibling-unrevoked and foreign-identity controls when configured) and SHALL fail the experiment gate when a control is accepted or when all tokens yield an identical response. **Priority:** MVP · **Source:** TV-02, SV-001 · **Verify:** I, P.

### FR-PRB-008 — Identical pre/post requests
Post-event probes SHALL be byte-identical to the baseline snapshot except for state that must change by design (fresh DPoP proof, nonce); any such difference SHALL be declared in the probe definition and recorded per attempt. **Priority:** MVP · **Source:** TV-03 · **Verify:** U, I.

### FR-PRB-009 — Post-revocation scheduling
The system SHALL schedule post-event probes by a configurable strategy (dense-then-geometric backoff by default, fixed interval, boundary-focused around known `exp`/cache TTL, adaptive bisection), starting at the anchor, and SHALL record intended times and scheduling lateness. **Priority:** MVP (dense-then-geometric, fixed, boundary-focused) / v1.x (adaptive bisection) · **Source:** TV-07, AuthorityDecay-style boundary mutation · **Verify:** U, P, B.

### FR-PRB-010 — Rate limiting and pacing
The system SHALL enforce per-host, per-identity and global rate limits from scope, SHALL honour `Retry-After` and provider rate-limit headers, and SHALL treat 429/5xx windows as indeterminate (never as denial), pausing and marking the window. **Priority:** MVP · **Source:** TV-13, TM-29 · **Verify:** U, I.

### FR-PRB-011 — Retry and backoff
Transport-level retries SHALL be bounded, jittered and recorded as separate attempts with their own send/receive instants; retries SHALL NOT be used to re-obtain credentials. **Priority:** MVP · **Source:** N2, TV-16 · **Verify:** U.

### FR-PRB-012 — Result normalisation
Every transport result SHALL be normalised into one schema (status, headers lower-cased with repeated values preserved, body reference/hash/truncation flag, server `Date`, `Age`, cache indicators, connection reuse, HTTP version, TLS facts, error info) independent of transport kind; cached responses (positive `Age`) SHALL be marked indeterminate. **Priority:** MVP · **Source:** TV-14, SV-048 · **Verify:** U, C.

### FR-PRB-013 — Mechanism hints
The system SHALL extract enforcement-signal hints (401 vs 403, `WWW-Authenticate error`, redirects, `invalid_grant`, claims-challenge, introspection `active`) and attribute a mechanism only when supported by signals, otherwise `unknown`. **Priority:** MVP (basic) / v1.x (cache-TTL inference) · **Source:** TV-22, CA-D2 · **Verify:** U, I.

### FR-PRB-014 — WebSocket persistence probe
The system SHALL establish an authenticated WebSocket (`websockets`), keep it open across the event, record server-initiated closes (code, reason, instant), perform liveness exchanges, and attempt reconnection with the revoked credential; outcomes default to `needs_verification` unless a policy profile or vendor document defines enforcement. **Priority:** v1.x · **Source:** WF-07, SCN-08, SV-055 · **Verify:** I.

### FR-PRB-015 — GraphQL probes
The system SHALL support GraphQL query/mutation probes derived through Schemathesis (assertion on `data`/`errors` content, not HTTP status) and subscription probes via the WebSocket adapter. **Priority:** v1.x · **Source:** MP Phase 5 · **Verify:** I.

### FR-PRB-016 — Replay and reproducibility
The system SHALL store request snapshots, specs, seeds and tool versions sufficient to replay an experiment's probes against the same or another target, and SHALL generate reproduction steps (curl with credential placeholders, not secrets). **Priority:** MVP · **Source:** D-6, SC-05, ADR-0012 · **Verify:** I.

### FR-PRB-017 — Bounded concurrency and cancellation
Concurrent probes SHALL be bounded (configurable, default 20), executed on a bounded executor, cancelled cooperatively within 1 s of abort, and SHALL NOT leave sockets or threads running after experiment end. **Priority:** MVP · **Source:** NFR-PERF, TM-34 · **Verify:** U, I, B.

### FR-PRB-018 — Cache-defeating variation (opt-in)
The system MAY, as a separate, explicitly configured scenario dimension with its own controls, vary schema-declared non-semantic parameters between probes to detect response/authorization caching; it SHALL NOT apply such variation implicitly. **Priority:** v1.x · **Source:** SCN-06 · **Verify:** I.

### 2.6 Schemathesis integration (ST)

### FR-ST-001 — Confined dependency
Schemathesis SHALL be a version-pinned dependency imported only by `rg_stbridge`; no other package SHALL import `schemathesis`, `hypothesis` or `pytest`. **Priority:** MVP · **Source:** NG-13, SC-08, RM-ST-2 · **Verify:** S (import-linter), R.

### FR-ST-002 — Documented-API-only usage
The bridge SHALL use only symbols of the upstream documented Python API reference (loaders, `Case`, `Response`, `APIOperation`, `BaseSchema`) and `schema.config.update(base_url=…)`; `schemathesis.engine.*`, CLI and config internals SHALL NOT be used. **Priority:** MVP · **Source:** RM-ST-3 · **Verify:** S (API-surface test).

### FR-ST-003 — Operation catalog
The system SHALL load OpenAPI 2.0–3.2 and GraphQL descriptions into an operation catalog exposing operation labels, declared security requirements, parameters, media types and declared responses, and SHALL select candidate protected operations automatically. **Priority:** MVP · **Source:** ST U1–U3 · **Verify:** I.

### FR-ST-004 — Safe schema ingestion
RG SHALL fetch API descriptions itself under scope and size limits, pre-validate them, resolve only local/in-scope `$ref`s, and pass them to Schemathesis via `from_dict`/`from_file`; `servers` entries SHALL never widen scope. **Priority:** MVP · **Source:** TM-02, TM-04, OQ-TM-01 · **Verify:** S.

### FR-ST-005 — Pinned deterministic probe derivation
Probe requests derived from the catalog SHALL be pinned (examples-first, explicit values, or a seeded generated value frozen once) so that no randomness remains in post-event probes. **Priority:** MVP · **Source:** ST §5.4 · **Verify:** U, I.

### FR-ST-006 — Neutralisation guards
The bridge SHALL assert at start-up and in tests that no Schemathesis auth provider, check or global hook is registered by RG, that exactly one wire request is issued per attempt, that redirects are not followed, that no `schemathesis.toml` is auto-discovered, and SHALL fail with `UPSTREAM_COMPAT` otherwise. **Priority:** MVP · **Source:** N1–N11, TM-25 · **Verify:** S (ISO-3, ISO-5, ISO-6).

### FR-ST-007 — Version window guard and fallback transport
The bridge SHALL refuse to run outside the supported version window and the system SHALL provide an equivalent raw transport so that probes remain executable without Schemathesis. **Priority:** MVP · **Source:** CR-9, RM-ST-1 · **Verify:** S (ISO-8, ISO-10).

### FR-ST-008 — Optional Schemathesis checks
The system MAY run Schemathesis' `ignored_auth` as a pre-flight enforcement control and schema-conformance checks on baseline responses, recording them as controls/diagnostics distinct from RG assertions. **Priority:** v1.x · **Source:** ST U8–U9 · **Verify:** I.
### 2.7 Scenario library (SCN)

### FR-SCN-001 — Declarative scenario schema
Scenarios SHALL be defined in a versioned declarative schema (YAML/JSON) specifying identities, credentials to mint, targets, probes, revocation action, validation modes, expectations per policy profile, schedule, horizons, preconditions and cleanup; scenarios SHALL be validated against the JSON Schema before use and SHALL contain no executable code. **Priority:** MVP · **Source:** MP Phase 7, TM-14 · **Verify:** U, C.

### FR-SCN-002 — Mandatory scenario catalog
The product SHALL ship a catalog specifying all fifteen mandatory scenarios SCN-01…SCN-15, each with normal vs vulnerable behaviour, preconditions, procedure, expected evidence, false-positive risks and an independent validation method. **Priority:** MVP (SCN-01, 02, 03, 04, 06 executable) / v1.x (SCN-05, 07…15 executable) · **Source:** GOAL-07, SC-11 · **Verify:** I, R.

### FR-SCN-003 — Reproducibility in lab
Every catalog scenario SHALL have a deterministic lab fixture (secure and intentionally vulnerable variants) in which the expected outcome class is defined. **Priority:** MVP (gate scenarios) / v1.x · **Source:** SC-03, MP Phase 7 exit · **Verify:** I.

### FR-SCN-004 — Scenario parameterisation and composition
Scenarios SHALL accept typed parameters (token lifetimes, schedule density, identity count, target set) with defaults and bounds, and MAY include other scenarios' steps by reference (e.g. refresh-after-logout inside a cross-service scenario). **Priority:** v1.x · **Source:** WF-05 · **Verify:** U.

### FR-SCN-005 — Automated scenario generation
The system SHALL derive candidate scenarios from provider capabilities × validation modes × credential types and, when an API description is supplied, from its protected operations; generated scenarios SHALL be shown for operator review and SHALL never auto-arm. **Priority:** v1.x · **Source:** MP Phase 14 / system prompt module 11 · **Verify:** I.

### FR-SCN-006 — Scenario packs
Scenario packs SHALL be distributable as plugins/files with id, version, API version and provenance, and SHALL be loadable only from allow-listed sources. **Priority:** v1.x · **Source:** WF-12, TM-22 · **Verify:** S.

### 2.8 Evidence (EVD)

### FR-EVD-001 — Immutable evidence capture
Every probe exchange, oracle call, admin API call, operator action and external event SHALL be captured as an immutable, content-addressed `EvidenceItem` with provenance (producer, instant, clock id), stored redacted by default. **Priority:** MVP · **Source:** GOAL-05, TM-26 · **Verify:** U, I.

### FR-EVD-002 — Observed/derived separation
Analysis outputs SHALL be stored as derived records referencing input evidence and the producing algorithm id and version; recomputation from stored evidence SHALL reproduce stored derived records byte-for-byte for the same algorithm version. **Priority:** MVP · **Source:** ADR-0013 · **Verify:** P.

### FR-EVD-003 — Derivation labelling
Every statement in stored findings and rendered reports SHALL carry exactly one derivation class (`observed`, `calculated`, `assumed`, `hypothesis`) and every assumption SHALL list the test able to falsify it. **Priority:** MVP · **Source:** TV-19, SC-12 · **Verify:** U, R.

### FR-EVD-004 — Evidence integrity
The system SHALL link evidence items into a hash chain per experiment, record the manifest digest at COMPLETE, and provide a verification command that detects modified, missing or reordered evidence. **Priority:** MVP · **Source:** TM-26 · **Verify:** U, S.

### FR-EVD-005 — Evidence bundle export/import
The system SHALL export an experiment as a portable bundle (manifest, records, blobs, schemas, versions) and import bundles as untrusted input (path validation, size limits, schema validation). **Priority:** MVP (export) / v1.x (import) · **Source:** WF-10, TM-15 · **Verify:** I, S.

### FR-EVD-006 — Redaction and unredacted capture
Evidence SHALL be redacted at the persistence boundary by default; optional unredacted raw capture SHALL be encrypted at rest, require an explicit scope flag, and every reveal SHALL be audited. **Priority:** MVP (redaction) / v1.x (encrypted unredacted) · **Source:** TM-07, TM-08 · **Verify:** S.

### FR-EVD-007 — Run manifest
Each experiment SHALL record tool, dependency (incl. Schemathesis, Authlib), provider and adapter versions, feature settings that change outcomes, seeds, clock kind, lab mode, scope digest and platform. **Priority:** MVP · **Source:** TV-20 · **Verify:** U.

### FR-EVD-008 — Timeline
The system SHALL maintain a gap-free, ordered experiment timeline of state transitions, revocation anchors, observations, operator actions, clock anomalies and notes, queryable by time range and credential, and exportable. **Priority:** MVP · **Source:** GOAL-05 · **Verify:** U, I.

### 2.9 Analysis (ANA)

### FR-ANA-001 — Clock alignment
The system SHALL estimate offsets between the local clock and each remote clock domain from `Date` header brackets and event pairs, SHALL attach uncertainty (including 1 s `Date` resolution and RTT), and SHALL emit no timing verdict from differences below the combined resolution (≈ 2 s by default). **Priority:** MVP · **Source:** TV-08, SV-047 · **Verify:** U, P.

### FR-ANA-002 — Event correlation
The system SHALL correlate each revocation event with provider-side records (admin events, system logs, SETs) and observations, produce a correlation result with matched, unmatched and conflicting records, and use provider logs only as lagging secondary evidence. **Priority:** v1.x (MVP: manual/Keycloak admin events) · **Source:** TV-24 · **Verify:** U, I.

### FR-ANA-003 — Exposure computation
The system SHALL compute exposure bounds per FR-TEMP-010/011, publish them as `BoundedDuration`, and include uncertainty components (probe spacing at the bracket, anchor uncertainty, clock-offset uncertainty, scheduling lateness) such that the reported width equals their algebraic sum. **Priority:** MVP · **Source:** SC-02 · **Verify:** U, P.

### FR-ANA-004 — Confidence scoring
The system SHALL compute a confidence level and factor list from control validity, number and spacing of samples, scheduling lateness, retries/429 windows, clock anomalies, repetition count and oracle agreement, deterministically and with rules documented per factor. **Priority:** MVP · **Source:** TV-21, D-5 · **Verify:** U, P.

### FR-ANA-005 — Outcome classification
The system SHALL classify each exposure result into exactly one outcome class per requested policy profile using published, deterministic rules over (window, expectation set, confidence, controls); `vulnerable` SHALL require a MUST-level expectation in the profile, valid controls, confirmation by a second oracle or repetition, and confidence ≥ medium. **Priority:** MVP · **Source:** GOAL-02, TV-23, ADR-0010 · **Verify:** U, P, I (SC-03).

### FR-ANA-006 — Policy profiles
The system SHALL ship profiles `protocol` (default), `vendor_doc`, `asvs_5_l1/l2/l3`, `nist_aal2/aal3` and `operator`; each classification SHALL record its profile, and re-analysis under another profile SHALL create a new analysis record without altering the stored one. **Priority:** MVP (`protocol`, `vendor_doc`, `operator`) / v1.x (ASVS, NIST) · **Source:** SV-046, RF-10 · **Verify:** U, P.

### FR-ANA-007 — False-positive reduction
The classifier SHALL apply published false-positive rules — natural expiry vs revocation via `exp`/sibling control, cached-response exclusion, rate-limit windows, probe malformation, client-authentication failure, unsupported-capability → not-applicable — before emitting `vulnerable`. **Priority:** MVP · **Source:** TV-09, TV-13, TV-14, TV-17 · **Verify:** U, P.

### FR-ANA-008 — Duplicate detection
Findings SHALL carry a stable fingerprint over (provider/target identity class, credential type, event kind, validation mode, mechanism, outcome class) and duplicates within and across experiments SHALL be grouped. **Priority:** v1.x · **Source:** MP Phase 8 · **Verify:** U.

### FR-ANA-009 — Reproducibility scoring
The system SHALL score reproducibility from repeated runs of the same scenario (agreement of outcome class and overlap of exposure bounds) and attach the score and run count to the finding. **Priority:** v1.x (MVP records repetition counts) · **Source:** SC-05 · **Verify:** U, I.

### FR-ANA-010 — Provider enforcement baselines
The system SHALL maintain versioned enforcement baselines per provider/version (source URL, retrieval date, rule set) expressing documented delays and defaults (e.g. Entra CAE windows, Keycloak token lifespans), selectable by profile `vendor_doc`; baselines SHALL be data, replaceable by plugins. **Priority:** MVP (Keycloak, generic) / v1.x (Entra, Okta, Auth0) · **Source:** R-009 · **Verify:** U, R.

### FR-ANA-011 — Risk and impact scoring
The system SHALL assign a risk rating to each non-`enforced` finding from documented factors (outcome class, exposure bounds relative to credential lifetime, privilege level of the retained operation, data sensitivity label supplied in the scenario, breadth across services) with the formula and factor values published in the report. **Priority:** v1.x (MVP: severity from class + bounds) · **Source:** MP D · **Verify:** U.

### FR-ANA-012 — Mechanism-aware explanation
Each finding SHALL include a protocol-aware explanation of why access may have continued (e.g. local JWT validation until `exp`, introspection cache, session store lag), flagged `observed`, `calculated` or `hypothesis`, citing the standard or vendor source. **Priority:** MVP · **Source:** D-3, CA-D2 · **Verify:** U, R.

### 2.10 Reporting (RPT)

### FR-RPT-001 — Report data contract
The system SHALL generate a versioned, schema-validated `ReportModel` (experiment summary, scope, environment, timeline, controls, per-credential exposure with uncertainty, classification matrix across profiles, findings, assumptions, reproduction steps, evidence index) from which all formats are rendered. **Priority:** MVP · **Source:** SC-12 · **Verify:** C, U.

### FR-RPT-002 — Formats
The system SHALL render JSON (canonical), Markdown and self-contained HTML reports (MVP), and SARIF, JUnit XML and CSV timelines (v1.x), each safely escaping all untrusted strings and making no network requests. **Priority:** MVP / v1.x · **Source:** TM-12 · **Verify:** U, S.

### FR-RPT-003 — Timeline visualisation
Reports SHALL include a timeline visualisation (inline SVG) showing the anchor interval, each probe interval coloured by outcome, `L`, `D`, the exposure bounds, the expectation deadline and any clock anomalies. **Priority:** MVP · **Source:** GOAL-05 · **Verify:** U (golden SVG), R.

### FR-RPT-004 — Wording discipline
Reports SHALL state exposure only as bounds with their uncertainty components, SHALL never present a point delay, SHALL show classification per profile, and SHALL separate observed, calculated, assumed and hypothesised statements. **Priority:** MVP · **Source:** NG-12, TV-19 · **Verify:** U, R.

### FR-RPT-005 — Reproduction steps
Reports SHALL include reproduction steps: environment, scope entries, spec digest, commands (`rg replay …`) and credential placeholders; reproduction content SHALL never contain secret values. **Priority:** MVP · **Source:** MP D · **Verify:** U, S.

### FR-RPT-006 — Comparison reports
The system SHALL render comparisons between runs, providers and services (interval overlap, class changes, distribution shift), with the same wording discipline. **Priority:** v1.x · **Source:** MP D, GOAL-12 · **Verify:** U.

### FR-RPT-007 — Handling classification
Reports SHALL carry a handling-classification field, the responsible-use banner text and an attestation that raw credentials are absent (from redaction checks). **Priority:** MVP · **Source:** RU-09, RU-10 · **Verify:** U.

### FR-RPT-008 — Deterministic rendering
Rendering the same `ReportModel` with the same options SHALL produce byte-identical output (volatile fields excluded or injected). **Priority:** MVP · **Source:** SC-05 · **Verify:** U.

### FR-RPT-009 — Security impact narrative
Each finding SHALL include an impact assessment and remediation guidance drawn from a controlled vocabulary mapped to mechanism and provider (e.g. enable introspection, reduce token lifetime, add `jti` denylist, enable back-channel logout), flagged as advice. **Priority:** v1.x · **Source:** MP D · **Verify:** R.

### 2.11 Laboratory (LAB)

### FR-LAB-001 — Deterministic virtual-time lab
The system SHALL provide an in-process lab (mock IdP, mock services) executing under a virtual clock and scheduler such that experiments covering hours of token lifetime complete without wall-time waiting and with fully deterministic ordering. **Priority:** MVP · **Source:** GOAL-06, ADR-0014 · **Verify:** I, P.

### FR-LAB-002 — Mock identity provider
The mock IdP SHALL implement OIDC discovery, token issuance (JWT and opaque), refresh with optional rotation, introspection, revocation, userinfo, logout, admin control (disable user, remove role/group, kill session, not-before) and configurable propagation delays and token lifetimes. **Priority:** MVP · **Source:** WF-01 · **Verify:** C, I.

### FR-LAB-003 — Mock protected services with enforcement profiles
The lab SHALL provide protected services with configurable enforcement behaviours: immediate session lookup, per-call introspection, introspection cache TTL, local JWT until `exp`, replica lag, flapping, gateway/backend disagreement, and secure vs intentionally vulnerable variants. **Priority:** MVP (≥ 5 profiles) / v1.x (all) · **Source:** SCN-05…07, SCN-15 · **Verify:** I.

### FR-LAB-004 — Fault and clock injection
The lab SHALL inject clock skew and jumps, delayed/duplicated/reordered events, response delays and errors, rate limiting, and connection drops, all driven by the deterministic scheduler. **Priority:** MVP (clock skew, delays) / v1.x (event reorder, connection faults) · **Source:** SCN-13, FR-TEMP-003 · **Verify:** I, P.

### FR-LAB-005 — Fixtures and expected datasets
Lab fixtures SHALL be versioned, seedable and shipped with expected-output datasets (normalised evidence digests and classifications) used as golden tests; fixture changes SHALL require dataset review. **Priority:** MVP · **Source:** SC-03, SC-05 · **Verify:** I, R.

### FR-LAB-006 — Real-IdP lab (Keycloak)
The system SHALL provide a reproducible Keycloak 26.8.x lab (container compose and zip-distribution script, realm import fixture, loopback-only, generated credentials) for integration experiments. **Priority:** MVP · **Source:** GOAL-06, KC-lab · **Verify:** I.

### FR-LAB-007 — Mode labelling
Every lab-derived result SHALL be labelled with lab mode (virtual/real-time), transport kind and clock kind, and virtual-time results SHALL NOT be mixed with live-target results in one exposure computation or comparison. **Priority:** MVP · **Source:** ADR-0014 · **Verify:** U.

### FR-LAB-008 — Lab safety
Lab listeners SHALL bind to loopback, generate random secrets per start, and refuse non-loopback binds without an explicit flag recorded in the audit log. **Priority:** MVP · **Source:** TM-32 · **Verify:** S.

### 2.12 CLI (CLI)

### FR-CLI-001 — Command contract
The CLI (`rg`) SHALL provide commands for workspace init, scope validation, scenario list/show/validate, experiment dry-run/run/abort/resume, status/timeline, findings, report render/export/verify, compare, lab up/down, adapter capabilities, diagnostics (`doctor`), configuration show, and plugin list/allow, with stable names, options, exit codes and machine-readable (`--json`) output. **Priority:** MVP (subset per workflow) · **Source:** GOAL-11 · **Verify:** E.

### FR-CLI-002 — Exit codes
The CLI SHALL use documented exit codes distinguishing success with no finding, success with findings by class, inconclusive, validation/config error, scope refusal, internal error and operator abort. **Priority:** MVP · **Source:** WF-09 · **Verify:** E.

### FR-CLI-003 — Safe terminal output
All target-controlled strings printed by the CLI SHALL be sanitised for control characters and ANSI/OSC sequences, and secrets SHALL never be printed. **Priority:** MVP · **Source:** TM-11 · **Verify:** S.

### FR-CLI-004 — Responsible-use banner and confirmations
Runs SHALL print the responsible-use banner (scope file, tenants, permitted mutating actions) and require the arming confirmation of FR-EXP-004 for mutating runs, with `--yes` permitted only when the scope file pre-authorises it. **Priority:** MVP · **Source:** RU-09 · **Verify:** E.

### FR-CLI-005 — Live progress
`rg run` SHALL show a live text timeline (state, anchor, probe outcomes, countdown to horizon) and a final summary with outcome class, bounds and report paths. **Priority:** MVP · **Source:** WF-01 · **Verify:** E.

### FR-CLI-006 — Configuration precedence
The CLI SHALL apply configuration precedence defaults < workspace file < environment (`RG_*`) < flags, report the effective configuration with provenance (`rg config show`), and reject unknown keys. **Priority:** MVP · **Source:** NFR-MNT · **Verify:** U, E.

### FR-CLI-007 — Non-interactive operation
All commands SHALL work non-interactively for CI (no prompts when `--non-interactive`; required confirmations satisfied by scope pre-authorisation or failing with a clear code). **Priority:** MVP · **Source:** WF-09 · **Verify:** E.

### FR-CLI-008 — Shell completion and help
The CLI SHALL provide `--help` for every command with examples and shell completion scripts for bash, zsh, fish and PowerShell. **Priority:** v1.x · **Source:** NFR-ACC · **Verify:** E.

### 2.13 GUI (GUI)

### FR-GUI-001 — Local-only web GUI
The GUI SHALL be a server-rendered web application bound to 127.0.0.1 with a per-session token, Host/Origin validation and CSRF protection, started by `rg gui`. **Priority:** MVP (read-only) / v1.x (control) · **Source:** TM-16, TM-17, ADR-0008 · **Verify:** S, E.

### FR-GUI-002 — Live timeline and results viewer
The GUI SHALL show experiments (list, state), a live timeline via Server-Sent Events and completed-experiment views (exposure bounds, controls, classification matrix, evidence browser). **Priority:** MVP · **Source:** WF-01, WF-10 · **Verify:** E.

### FR-GUI-003 — Guided experiment setup and run control
The GUI SHALL provide guided scope, target, identity, scenario and revocation setup with dry-run, arming confirmation, manual-acknowledgment buttons (M1/M2) and abort. **Priority:** v1.x · **Source:** WF-02…04 · **Verify:** E.

### FR-GUI-004 — Findings, comparison and export
The GUI SHALL provide findings review (triage status, notes), run/provider/service comparison views and report/bundle export. **Priority:** v1.x · **Source:** WF-05, WF-10 · **Verify:** E.

### FR-GUI-005 — Safe rendering
All untrusted strings SHALL be escaped; the GUI SHALL send a restrictive Content-Security-Policy and make no third-party requests. **Priority:** MVP · **Source:** TM-12 · **Verify:** S.

### FR-GUI-006 — Accessibility and states
GUI screens SHALL define empty, loading and error states, keyboard operability and semantic markup meeting WCAG 2.2 AA for the specified components; colour SHALL never be the sole outcome indicator. **Priority:** MVP · **Source:** NFR-ACC · **Verify:** E, R.

### 2.14 Automation API (API)

### FR-API-001 — Automation HTTP API
The system SHALL expose the ApplicationService operations (experiments, scenarios, reports, status/events) as a versioned loopback HTTP API with OpenAPI description, scoped bearer tokens and the same safety gates as the CLI. **Priority:** v1.x · **Source:** RM-D4, TM-18 · **Verify:** C, S.

### FR-API-002 — Event streaming
The API SHALL stream experiment events (SSE) with resume from a sequence number. **Priority:** v1.x · **Source:** WF-09 · **Verify:** I.

### FR-API-003 — Permission-scoped tokens
API tokens SHALL carry explicit permissions (`read`, `run_observe`, `run_mutate`), expire, and be revocable; `run_mutate` SHALL additionally require the scope file's pre-authorisation. **Priority:** v1.x · **Source:** TM-18 · **Verify:** S.

### 2.15 Security and safety (SEC)

### FR-SEC-001 — Scope document
No network action SHALL occur without a validated scope document (authorisation statement, hosts/tenants, identities flagged synthetic, permitted action classes, rate/time limits, validity window, clearance acknowledgements); the lab SHALL use a generated loopback scope; there SHALL be no scope-free mode. **Priority:** MVP · **Source:** RU-01, RU-02, SCR-01…12 · **Verify:** U, S.

### FR-SEC-002 — Scope enforcement before I/O
Every outbound request and adapter call SHALL be authorised by the scope enforcer before connection, on the **resolved address and every redirect/endpoint** (no redirects followed by default), rejecting loopback/link-local/metadata addresses unless scoped, and SHALL fail closed. **Priority:** MVP · **Source:** TM-01…04, SC-06 · **Verify:** S, P.

### FR-SEC-003 — Action classes
Actions SHALL be classified `observe`, `authenticate`, `mutate_identity`, `mutate_policy`, each individually permitted in scope; mutating actions SHALL apply only to identities declared synthetic on the declared tenant. **Priority:** MVP · **Source:** ADR-0011, RU-03, RU-04, TM-05 · **Verify:** S, P.

### FR-SEC-004 — Audit log
The system SHALL append every scope load, arm, mutating action, abort, evidence reveal and export to a hash-chained append-only audit log with timestamp, OS user, scope digest and targets, and provide a verification command. **Priority:** MVP · **Source:** RU-06, TM-27 · **Verify:** U, S.

### FR-SEC-005 — Secrets handling
Secrets SHALL be referenced by handle (env, OS keyring, file), resolved at point of use into non-serialisable wrappers, never written to disk, logs, evidence, reports, process arguments or crash dumps (canary-tested); configuration files containing inline secrets SHALL be rejected. **Priority:** MVP · **Source:** SC-07, TM-07 · **Verify:** S.

### FR-SEC-006 — Redaction
A single redaction gate SHALL process everything crossing into logs, store, reports and GUI, redacting tokens, cookies, passwords, authorisation headers, client secrets and their encodings, with allow-listed claim fields retained. **Priority:** MVP · **Source:** SC-07 · **Verify:** S, P (fuzzed canaries).

### FR-SEC-007 — Responsible-use gate
Runs against third-party SaaS providers SHALL require a recorded clearance acknowledgement per provider; the system SHALL refuse expired scopes and SHALL stop on persistent rate-limit responses. **Priority:** MVP (mechanism) · **Source:** RU-07, RU-08, R-010 · **Verify:** S.

### FR-SEC-008 — TLS verification
TLS certificate verification SHALL be on by default for all outbound HTTP/WebSocket calls; disabling it SHALL require a scope entry per host and an audit record and SHALL be marked in the report. **Priority:** MVP · **Source:** TM-33 · **Verify:** S.

### FR-SEC-009 — Resource limits on untrusted input
The system SHALL bound response body sizes, decompression ratio, header counts, API description sizes/depth, event payload sizes and queue depths, failing safely with typed errors. **Priority:** MVP · **Source:** TM-10, TM-34 · **Verify:** S.

### FR-SEC-010 — Output escaping
Every renderer and UI SHALL escape untrusted strings for its context (terminal, HTML, Markdown, XML, CSV formula injection) and SHALL pass an injection corpus test. **Priority:** MVP · **Source:** TM-11, TM-12 · **Verify:** S.

### FR-SEC-011 — Evidence at rest
Store and bundle files SHALL be created owner-only (POSIX 0600/0700; Windows ACLs restricted to the current user); encrypted evidence storage (AES-GCM via `cryptography`, key from keyring/passphrase) SHALL be available for raw captures. **Priority:** MVP (permissions) / v1.x (encryption) · **Source:** TM-08 · **Verify:** S.

### FR-SEC-012 — Plugin trust
Plugins SHALL be loaded only from an explicit operator allow-list with manifest and API-version checks; in-process plugins SHALL be documented as fully trusted; no auto-discovery execution. **Priority:** MVP (mechanism; first-party only) / v1.x (third-party) · **Source:** TM-22, ADR-0009 · **Verify:** S.

### FR-SEC-013 — Dependency and supply-chain controls
Releases SHALL pin and hash-lock dependencies, produce an SBOM and licence report, run vulnerability audit in CI, and run the upstream canary job without secrets. **Priority:** MVP · **Source:** TM-23, TM-24 · **Verify:** S, R.

### FR-SEC-014 — Safe defaults
Defaults SHALL be: read-only probes, loopback binds, redirects off, TLS on, mutating actions off, redaction on, conservative rate limits, minimal logging of bodies; relaxing any default SHALL be explicit and audited. **Priority:** MVP · **Source:** GOAL-10 · **Verify:** U, S.

### 2.16 Operations (OPS)

### FR-OPS-001 — Diagnostics
`rg doctor` SHALL report platform, Python and dependency versions (including the Schemathesis window check), clock health (offset check against a configured reference where available), workspace/filesystem suitability (WAL on local FS), permissions, scope validity and adapter reachability, with pass/warn/fail and remediation text. **Priority:** MVP · **Source:** MP Phase 11 · **Verify:** E.

### FR-OPS-002 — Offline operation
All MVP features SHALL work without internet access beyond configured targets; update checks SHALL be opt-in; an offline wheelhouse install SHALL be supported. **Priority:** MVP · **Source:** MP Phase 11, 13 · **Verify:** I.

### FR-OPS-003 — Migrations
Persisted schemas SHALL be versioned; `rg` SHALL migrate workspaces forward with an automatic backup, refuse to open newer-major data, and verify the migration. **Priority:** MVP · **Source:** MP Phase 11 · **Verify:** I.

### FR-OPS-004 — Updates
The system SHALL document an update procedure and (opt-in) check for new versions, verifying signatures/hashes of release artefacts. **Priority:** v1.x · **Source:** MP Phase 11 · **Verify:** R.

### FR-OPS-005 — Logging
Structured logging with correlation ids, levels, rotating file output and mandatory redaction SHALL be provided; debug logging of bodies SHALL be off by default. **Priority:** MVP · **Source:** SC-07 · **Verify:** U, S.

### FR-OPS-006 — Timeouts and cancellation
Every operation SHALL have a configured timeout and cooperative cancellation; abort SHALL stop probing within 1 s and run cleanup. **Priority:** MVP · **Source:** FR-EXP-007 · **Verify:** I.

### FR-OPS-007 — Configuration validation
Configuration SHALL be parsed (syntax) separately from validated (semantics, cross-field, scope), with all errors reported together, field paths, stable codes and suggestions. **Priority:** MVP · **Source:** MP Phase 11 · **Verify:** U.

### 2.17 Extensibility (EXT)

### FR-EXT-001 — Stable interfaces
Identity adapters, revocation actions, transports, assertions, report renderers, scenario packs and baselines SHALL be implementable against documented ports with `api_version` compatibility and conformance test kits. **Priority:** MVP (ports) / v1.x (third-party kit) · **Source:** D-7, GOAL-09 · **Verify:** C.

### FR-EXT-002 — Plugin discovery and manifests
Plugins SHALL declare id, version, API version, capabilities and required permissions in a manifest; the CLI SHALL list installed plugins and their allow-list status. **Priority:** MVP · **Source:** WF-12 · **Verify:** U.

### FR-EXT-003 — Core independence
Adding a provider or transport SHALL require no change to `rg_core`; this SHALL be demonstrated by a reference plugin built only against public ports. **Priority:** v1.x · **Source:** D-7 · **Verify:** C, R.

### FR-EXT-004 — Reusable packages
`rg_core`, `rg_idp`, `rg_probe` SHALL be installable and importable without the application package and without Schemathesis. **Priority:** MVP · **Source:** ADR-0003 · **Verify:** S (clean-venv test).

### FR-EXT-005 — Plugin developer documentation
The project SHALL document plugin development (ports, manifests, testing kit, security posture). **Priority:** v1.x · **Source:** WF-12 · **Verify:** R.

### 2.18 Historical regression (HIST)

### FR-HIST-001 — Run history store
The system SHALL keep an indexed history of experiments, findings and exposure bounds per scenario/provider/target for comparison. **Priority:** MVP (store) · **Source:** GOAL-12 · **Verify:** I.

### FR-HIST-002 — Regression comparison
The system SHALL compare runs of the same scenario, reporting changes in outcome class, exposure-bound overlap and distribution (repeated trials), and SHALL flag regressions beyond configurable thresholds. **Priority:** v1.x · **Source:** WF-09, CA-D7 · **Verify:** U, I.

### FR-HIST-003 — CI regression gate
`rg compare --baseline <run|bundle>` SHALL exit non-zero on regression per thresholds and emit a machine-readable summary. **Priority:** v1.x · **Source:** WF-09 · **Verify:** E.

### FR-HIST-004 — Baseline pinning
Operators SHALL be able to pin a run/bundle as the accepted baseline for a scenario/provider pair with an audited reason. **Priority:** v1.x · **Source:** WF-09 · **Verify:** U.
## 3. Non-functional requirements

All numeric figures below are **proposed targets with rationale**, not benchmark results; each is validated (or revised with recorded rationale) by the named benchmark/test (charter SC-16). Reference environment for benchmarks: 4 vCPU, 8 GiB RAM, SSD, Linux and Windows 11, Python 3.12, loopback or LAN target with ≤ 5 ms RTT.

### NFR-PERF-001 — Probe scheduling accuracy
At ≤ 50 concurrent in-flight probes, p95 scheduling lateness (actual dispatch − intended dispatch) SHALL be ≤ 25 ms and p99 ≤ 100 ms on the reference environment, measured and recorded on every observation. **Rationale:** exposure width includes probe spacing; sub-second probe schedules (default dense phase 1 s) must not be dominated by jitter; lateness is already an uncertainty component. **Priority:** MVP · **Verify:** B (P12-004).

### NFR-PERF-002 — Timing measurement precision
The monotonic time source SHALL be `time.perf_counter_ns` (not `time.monotonic`, whose Windows resolution on Python < 3.13 is reported to be ≈ 15.6 ms — U: confirmed by the calibration test in RG-P02-001) with a startup calibration check that rejects a source whose measured resolution exceeds 1 ms, and send/receive stamps SHALL be taken inside the worker thread adjacent to the wire call. **Rationale:** timestamp resolution bounds `W`. **Priority:** MVP · **Verify:** U, B.

### NFR-PERF-003 — Concurrent probes
The engine SHALL sustain ≥ 200 concurrent in-flight probes per process (bounded executor) with RSS growth ≤ 300 MiB over the idle baseline and no scheduling-lateness target violation at 50 concurrent. **Rationale:** cross-service experiments with many credentials; thread offload (ADR-0004). **Priority:** MVP (50) / v1.x (200) · **Verify:** B.

### NFR-PERF-004 — Concurrent experiments
One active experiment per workspace (v1); multiple workspaces MAY run in separate processes; no cross-process shared mutable state. **Priority:** MVP · **Verify:** I.

### NFR-PERF-005 — CPU consumption
Steady-state CPU during observation SHALL be ≤ 15 % of one core per 50 probes/s with redaction and persistence enabled (proposal). **Priority:** MVP · **Verify:** B.

### NFR-PERF-006 — Memory growth
During a 1-hour soak at 20 probes/s, RSS growth after warm-up SHALL be ≤ 5 % (no unbounded queues, bounded in-memory evidence index). **Priority:** MVP · **Verify:** B (soak).

### NFR-PERF-007 — Evidence storage efficiency
Observation metadata SHALL average ≤ 2 KiB per observation excluding bodies; identical response bodies SHALL be deduplicated by content hash; a 10 000-observation experiment SHALL occupy ≤ 100 MiB with default body capture caps (64 KiB/body). **Priority:** MVP · **Verify:** B.

### NFR-PERF-008 — Report generation latency
Rendering the MVP formats SHALL take ≤ 1 s for an experiment with ≤ 500 observations and ≤ 5 s for 10 000 observations (HTML including SVG timeline). **Priority:** MVP · **Verify:** B.

### NFR-PERF-009 — Startup time
`rg --version` SHALL complete in ≤ 0.5 s and `rg run --help` in ≤ 1.0 s (p95, warm disk cache) without importing Schemathesis, Hypothesis or pytest. **Rationale:** Schemathesis' import cone is heavy (SCHEMATHESIS-INTEGRATION §10); lazy import. **Priority:** MVP · **Verify:** B.

### NFR-PERF-010 — Recovery time
After restart following a crash, `rg resume`/recovery SHALL begin within 5 s and recover the workspace to the last durable record with at most the in-flight probe attempts lost (≤ concurrency-limit attempts, recorded as `not_sent`/interrupted). **Priority:** MVP · **Verify:** I (kill injection).

### NFR-REL-001 — Crash consistency
Every state transition and every observation SHALL be durably committed (SQLite WAL with synchronous=FULL for transitions/anchors, NORMAL permitted for bulk observations with batch commit ≤ 250 ms) before the engine acts on it. **Priority:** MVP · **Verify:** I, P.

### NFR-REL-002 — Determinism
Given the same spec, seed, virtual clock and lab fixture, two runs SHALL produce identical normalised evidence and classification (volatile fields enumerated); non-deterministic real-time runs SHALL record the nondeterminism sources. **Priority:** MVP · **Verify:** P, I.

### NFR-REL-003 — Bounded retries and backpressure
All retry loops and queues SHALL be bounded with explicit policies; evidence-bearing queues SHALL never drop data. **Priority:** MVP · **Verify:** U, P.

### NFR-REL-004 — Resource cleanup
Sockets, threads, subprocesses (lab), temp files and locks SHALL be released on completion, abort and crash recovery; leak tests SHALL assert no growth in open handles across 100 consecutive experiments. **Priority:** MVP · **Verify:** I.

### NFR-PLAT-001 — Platforms
MVP SHALL be supported and CI-tested on Linux (x86-64, Ubuntu LTS) and Windows 11/Server 2022 (x86-64); macOS (arm64) best effort with CI results reported; Python 3.11–3.14. **Priority:** MVP · **Verify:** E.

### NFR-PLAT-002 — Portable filesystem behaviour
Path handling, file locking, permission setting, newline handling and encodings SHALL be portable (UTF-8 everywhere; no path-length assumptions < 260 chars on Windows without long-path guidance); behaviour on network filesystems SHALL be diagnosed by `rg doctor`. **Priority:** MVP · **Verify:** E.

### NFR-PLAT-003 — No elevated privileges
No feature SHALL require administrator/root privileges; lab ports are unprivileged (> 1024). **Priority:** MVP · **Verify:** E.

### NFR-PLAT-004 — Packaging
The product SHALL be installable from wheels (`pipx`/`uv`), as a PyInstaller one-folder bundle for Windows and Linux, and as an offline wheelhouse; clean-venv install and import tests SHALL cover each distribution. **Priority:** MVP (wheels) / v1.x (bundles) · **Verify:** E.

### NFR-MNT-001 — Modularity and dependency rules
Package import boundaries SHALL be enforced by tooling (import-linter), no import cycles, and `rg_core` SHALL perform no I/O. **Priority:** MVP · **Verify:** S, R.

### NFR-MNT-002 — Typing and style
`rg_core` SHALL pass mypy `--strict`; other packages SHALL pass mypy in default-strict mode for public interfaces; ruff formatting/lint SHALL be enforced in CI. **Priority:** MVP · **Verify:** R.

### NFR-MNT-003 — Documentation of public contracts
Every public interface SHALL have docstrings with parameters, returns, errors, side effects and thread-safety; JSON Schemas for persisted/exported documents SHALL be generated and golden-tested. **Priority:** MVP · **Verify:** R, C.

### NFR-MNT-004 — Upstream upgrade process
The Schemathesis (and Authlib) upgrade procedure SHALL be automated as a weekly canary plus a reviewed bump PR, with isolation suites ISO-1…ISO-11 as the gate. **Priority:** MVP · **Verify:** R, S.

### NFR-MNT-005 — Semantic versioning and deprecation
Public APIs/CLI/schemas SHALL follow semantic versioning with at least one minor release of deprecation warnings before removal. **Priority:** v1.x · **Verify:** R.

### NFR-TEST-001 — Coverage thresholds
Line coverage ≥ 90 % for `rg_core`, ≥ 85 % for `rg_probe`/`rg_idp`/`rg_stbridge`, ≥ 80 % overall; branch coverage ≥ 80 % for classification, exposure, state-machine modules; mutation score ≥ 70 % for classification and exposure modules (proposals, validated in P12-001). **Priority:** MVP · **Verify:** R (CI gate).

### NFR-TEST-002 — Test taxonomy
The project SHALL maintain unit, integration (lab), contract (per port, with conformance kits), property-based, state-machine model, regression (golden datasets), negative, concurrency, fault-injection, clock-skew, performance, CLI, GUI, packaging, platform, security and reproducibility tests as specified in Phase 12. **Priority:** MVP · **Verify:** R.

### NFR-TEST-003 — Determinism of the test suite
Unit and virtual-time lab tests SHALL run without network access and without wall-clock sleeps, and SHALL complete in ≤ 5 minutes on the reference environment. **Priority:** MVP · **Verify:** R.

### NFR-TEST-004 — Traceability
Every FR/NFR SHALL map to ≥ 1 module spec and ≥ 1 test id; `tools/specgate.py check --final` SHALL pass. **Priority:** MVP · **Verify:** R.

### NFR-DOC-001 — Documentation set
The release SHALL include installation, quick start (MVP workflow), user manual, configuration reference, CLI reference (generated), scenario catalog reference, provider capability matrices with evidence, plugin guide, troubleshooting and responsible-use documentation. **Priority:** MVP (core) / v1.x · **Verify:** R.

### NFR-DOC-002 — Example assessments
At least three worked example assessments (lab-only walkthrough, Keycloak, manual SaaS) SHALL be shipped as runnable fixtures. **Priority:** MVP (two) / v1.x · **Verify:** E.

### NFR-DOC-003 — Evidence-labelled research claims
User documentation of provider behaviour SHALL cite source and verification level, and SHALL state limitations (e.g. documentation-derived, not tenant-verified). **Priority:** MVP · **Verify:** R.

### NFR-LIC-001 — Licence compliance
All dependencies' licences SHALL be inventoried; no copyleft code SHALL be statically combined or vendored; Schemathesis, Authlib and others are used as unmodified dependencies; a third-party notice file ships with releases. **Priority:** MVP · **Verify:** R.

### NFR-LIC-002 — Project licence
The project licence is an owner decision (recommended Apache-2.0, charter §9) and SHALL be applied to `revocationgap/` files before first release; no field-of-use restriction. **Priority:** MVP · **Verify:** R.

### NFR-ACC-001 — CLI accessibility
CLI output SHALL not rely on colour alone, SHALL support `NO_COLOR`, plain output (`--plain`) and screen-reader-friendly progress (line-oriented). **Priority:** MVP · **Verify:** E.

### NFR-ACC-002 — GUI accessibility
GUI SHALL meet FR-GUI-006 and be usable at 200 % zoom without loss of function. **Priority:** v1.x · **Verify:** E, R.

## 4. MVP scope definition

**MVP release gate:** the master-prompt §15 workflow end-to-end (WF-01) on the virtual-time lab and the Keycloak lab for scenarios SCN-01, SCN-02, SCN-03, SCN-04, SCN-06; classification correct on all fixtures (SC-03); SC-01, SC-02, SC-04, SC-05, SC-06, SC-07, SC-08, SC-09, SC-12, SC-13, SC-14, SC-15 satisfied.

| Area | MVP | v1.x | Later (design allowance only) |
|---|---|---|---|
| Temporal model, state machine, exposure bounds, confirmation tail | ✔ | CAEP/external-event anomalies | advanced state inference |
| Providers | generic OIDC, mock IdP, Keycloak | Entra, Okta, Auth0 (operator tenants), SSF/CAEP | Google/Cloud IAM, AD hybrid |
| Revocation actions | manual; disable/delete; role/group; session/logout/RT/AT revoke; service identity; not-before | password reset, CA/device policy, event-driven | SaaS connectors |
| Probes | HTTP (raw + Schemathesis-derived), controls, baseline, schedules, refresh, oracle probes | WebSocket, GraphQL, cache-defeating variation, adaptive bisection | gRPC, SSE streams, temporal fuzzing |
| Scenarios | catalog spec (15) + 5 executable | 15 executable, generation, scenario packs | attack graphs |
| Analysis | alignment, exposure, confidence, classification (`protocol`,`vendor_doc`,`operator`), baselines (Keycloak, generic) | ASVS/NIST profiles, dedup, reproducibility scoring, risk scoring, regression | statistical campaigns |
| Reports | JSON, Markdown, HTML, SVG timeline | SARIF, JUnit, CSV, comparison, impact narrative | commercial templates |
| Lab | virtual-time lab, Keycloak lab | event reorder/faults, all profiles, multi-node Keycloak | — |
| UX | CLI, read-only GUI | GUI control, findings UX, automation API, completions | collaboration |
| Security/ops | scope, audit, redaction, doctor, migrations, recovery | encryption of raw evidence, third-party plugins, updates | — |
| Platforms | Linux + Windows (macOS best effort), wheels | PyInstaller bundles, containers | — |

## 5. Explicit project exclusions
NG-01…NG-17 of the charter apply verbatim (generic authz matrices, OAuth misconfiguration scanning, JWT forgery, SSF conformance, cookie scanning, "revoke-then-check-once" as a feature, stealth/DoS, credential attacks, Schemathesis fuzz phases against live boundaries, custom crypto/protocols, hosted service, exact-delay claims, forking Schemathesis, auto-remediation, continuous production monitoring, MFA browser automation, tenant-verified Entra/Okta/Auth0 claims before operator runs).

## 6. Coverage mappings (informative; the generated traceability matrix is authoritative)

### 6.1 Master-prompt capability areas → requirements
| Master capability | Requirements |
|---|---|
| A Identity & authorization analysis | FR-IDP-001…014, FR-TEMP-004/005, FR-REV-003…009, FR-ANA-006/010 |
| B Temporal attack simulation | FR-TEMP-001…012, FR-PRB-009…011, FR-LAB-001…004, FR-SCN-002 |
| C Offensive verification | FR-EXP-001…009, FR-PRB-001…018, FR-ST-001…008, FR-REV-001/010/011 |
| D Evidence & reporting | FR-EVD-001…008, FR-ANA-001…012, FR-RPT-001…009, FR-HIST-001…004 |
| E Extensibility | FR-EXT-001…005, FR-IDP-001/007, FR-ST-007 |

### 6.2 Differentiators → requirements
| Differentiator | Requirements |
|---|---|
| D-1 Temporal authorization analysis | FR-TEMP-004…012, FR-EXP-006 |
| D-2 Cross-service enforcement analysis | FR-EXP-009, FR-LAB-003, FR-SCN-002, FR-HIST-002 |
| D-3 Protocol-aware interpretation | FR-TEMP-008, FR-ANA-005/006/010/012, FR-IDP-003/004 |
| D-4 Evidence-backed attack verification | FR-PRB-005/006/007/008, FR-EXP-003, FR-ANA-007 |
| D-5 Measured uncertainty | FR-TEMP-001/002/009/010/011, FR-ANA-001/003/004, FR-RPT-004 |
| D-6 Reproducible experiments | FR-EXP-001, FR-PRB-016, NFR-REL-002, FR-LAB-005, FR-EVD-007 |
| D-7 Modular extension | FR-EXT-001…005, FR-ST-001, NFR-MNT-001 |
| D-8 Actionable output | FR-RPT-001…009, FR-ANA-012, FR-EVD-008 |

### 6.3 Threat-model items → requirements
| Threats | Requirements |
|---|---|
| TM-01…06 scope bypass/destructive actions | FR-SEC-001/002/003, FR-EXP-004, FR-ST-004 |
| TM-07…09 credential/evidence disclosure | FR-SEC-005/006/011, FR-EVD-006, FR-IDP-014 |
| TM-10…15 hostile inputs/output injection | FR-SEC-009/010, FR-CLI-003, FR-GUI-005, FR-PRB-002, FR-RPT-002, FR-EVD-005 |
| TM-16…18 GUI/API | FR-GUI-001/005, FR-API-001/003 |
| TM-19…21 CAEP receiver | FR-IDP-012 |
| TM-22…25 plugin/supply chain/upstream drift | FR-SEC-012/013, FR-ST-006/007, NFR-MNT-004 |
| TM-26…28 integrity/time | FR-EVD-004, FR-SEC-004, FR-TEMP-001…003 |
| TM-29…31 ToS/side effects/abuse | FR-PRB-010, FR-SEC-001/007, FR-SEC-003 |
| TM-32…34 lab/TLS/resource | FR-LAB-008, FR-SEC-008/009, FR-PRB-017 |

### 6.4 Charter success criteria → requirements and tests
SC-01/02 → FR-TEMP-010/011, FR-ANA-003; SC-03 → FR-ANA-005…007, FR-LAB-005; SC-04 → FR-PRB-005/007, FR-EXP-003; SC-05 → NFR-REL-002, FR-PRB-016; SC-06 → FR-SEC-002; SC-07 → FR-SEC-005/006; SC-08 → FR-ST-001; SC-09 → FR-SEC-003, FR-REV-001; SC-10 → FR-IDP-013; SC-11 → FR-SCN-002/003; SC-12 → FR-RPT-001/004, FR-EVD-003; SC-13 → FR-EXP-007/008, FR-REV-012; SC-14 → NFR-PLAT-001; SC-15 → NFR-TEST-004; SC-16 → NFR-PERF-001…010.

## 7. Requirement change control
Adding, removing or re-scoping a requirement requires: an edit here, an update of every citing module spec's front matter, regeneration of the traceability matrix, and a roadmap change-log line. Priorities may change only with a recorded rationale in `PROGRESS.md`.
