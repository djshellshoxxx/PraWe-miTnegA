---
id: RG-P01-002
title: "Personas and user workflows"
phase: "01"
package: docs
status: DRAFT
depends_on: [RG-P01-001]
---

# RevocationGap — Personas, Use Cases and User Workflows (RG-P01-002)

**Status:** DRAFT · **Builds on:** [`../00-PROJECT-CHARTER.md`](../00-PROJECT-CHARTER.md) (GOAL/NG/SC/D/RU IDs, glossary) · **Feeds:** RG-P01-004 (PRD), RG-P10 (CLI/GUI), RG-P11 (scope, recovery).

**Citation keys** as in the charter: `[TF]`, `[CA]`, `[STD]` (`SV-xxx`), `[ST]` (`N#`, `ISO-#`), `[KC]`, `[EN]`, `[OK]`, `[A0]`, `[AL]`, `[RR]`; `[MP]` = master prompt (capabilities **A–E**). Capability letters: **A** identity/authorization analysis · **B** temporal attack simulation · **C** offensive verification · **D** evidence and reporting · **E** extensibility. Terms (anchor, probe, control, exposure interval…) are defined in charter §10. Command names are deliberately abstract (e.g. "start the lab"); concrete CLI/GUI surfaces belong to RG-P10-001/-005.

**Conventions.** `⟦STATE⟧` marks a user-visible experiment state (§6). Each workflow lists *Preconditions*, *Actors*, numbered *Steps* (S = system response, O = operator action), *Outputs*, *Failure/alternate paths* (`F#`), capabilities and horizon. Every workflow begins with the scope gate of charter RU-01 and ends with the evidence and audit records of RU-06; these are not repeated per step.

---

## 1. Personas

| ID | Persona | Goals | Environment | Skill | Constraints | Needs from outputs |
|---|---|---|---|---|---|---|
| PER-01 | **Professional pentester / red-team operator** | Prove (or rule out) retained access after offboarding, demotion or session kill within an engagement; deliver reproducible evidence to the client | Client-owned tenants and staging apps, laptop (Windows/Linux), often no inbound connectivity; engagement window and rules of engagement | High (HTTP, OAuth/OIDC, Burp/ZAP); moderate IdP-admin | Written authorisation; client-supplied test identities; limited time; client change-freeze; mutating admin actions only if RoE permit | Finding class with *profile* and defensible wording ("bounded observation", not "delay is X"); exact reproduction steps with credential placeholders; evidence the client can re-run; exportable report |
| PER-02 | **Identity-security researcher** | Characterise provider/protocol enforcement semantics, compare providers and versions, publish baselines | Lab (Keycloak, mock IdP), own tenants; scripts and notebooks | Very high (RFCs, IdP internals) | Reproducibility; vendor ToS (Okta/Auth0/Entra limits [OK §(d); A0 §(d); EN §4]); version drift [TF R-009] | Raw + normalised evidence, interval distributions, run manifests (versions, seeds), machine-readable results, provider-specific interpretation |
| PER-03 | **API security researcher / bug-bounty hunter** | Show a vulnerability in a program's API/IdP integration with minimal impact | Own accounts on a third-party SaaS; no admin rights; program rules; often only manual self-service revocation (logout, password change, "sign out everywhere") | Medium–high | Cannot run IdP admin actions; strict rate limits; no stealth, no DoS; disclosure rules | Evidence that survives triage: controls, timeline, no-200-only proof, minimal reproduction; low-volume schedule; redaction of own credentials |
| PER-04 | **Enterprise security administrator** | Verify that offboarding/role-removal procedures actually end access in the company's apps and gateways | Corporate tenants (Entra/Okta/Keycloak), staging copies; CI available | Medium | Change control; production off-limits without sign-off; must restore state after tests | Plain-language result ("which apps still served the ex-employee, for at least/at most how long"), comparison across apps, remediation hints tied to cause (D-8), restoration confirmation |
| PER-05 | **SSO/OAuth/OIDC/cloud security engineer** | Validate token lifetimes, introspection vs local-JWT decisions, logout propagation, CAE/CAEP wiring | Staging IdP + resource servers, gateways, CI/CD | High | Pipelines must be headless and deterministic; shared tenants | Expected-vs-observed per validation mode, mechanism attribution (`exp`, cache TTL, session lookup, claims challenge), regression diff, CI exit codes |
| PER-06 | **Developer testing session management** | Check own app's logout/disable/role-change handling during development | Local machine, docker-compose, mock IdP or Keycloak | Medium | Fast feedback; no security background assumed; ephemeral environments | Immediate, readable timeline in CLI/GUI; clear "what to fix" pointer; replayable failing experiment; lab fixtures for own app |
| PER-07 | **SaaS / identity-platform security team (vendor-side)** | Regression-test own revocation propagation across services/regions; validate documented SLAs | Multi-service staging, multi-node IdP, CI, distributed workers later | High | Scale (many identities/services), historical comparison, internal tooling integration, plugin development | Interval **distributions** per release, drift detection, cross-service/replica disagreement, plugin/adapter SDK (WF-12) |

---

## 2. Offensive assessment use cases

| ID | Use case | Personas | Scenario(s) | Workflow(s) |
|---|---|---|---|---|
| UC-01 | Verify that disabling an account ends API access through every credential the account holds (access token, refresh token, session) | 01, 04, 05 | SCN-02 | WF-01, WF-03 |
| UC-02 | Measure how long an access token remains usable after session termination/token revocation, per validation mode | 02, 05 | SCN-02, 09 | WF-03, WF-05 |
| UC-03 | Verify refresh-token invalidation after logout, RT revocation, password reset and rotation replay | 01, 02, 03 | SCN-04 | WF-06 |
| UC-04 | Detect stale role/group claims: operations requiring a removed role keep succeeding | 01, 04 | SCN-01, 05, 06 | WF-03, WF-05 |
| UC-05 | Compare gateway vs backend and service A vs service B behaviour after one event | 04, 05, 07 | SCN-05, 07, 11 | WF-05 |
| UC-06 | Test whether a long-lived connection (WebSocket) survives revocation and whether reconnection succeeds | 01, 03, 07 | SCN-08 | WF-07 |
| UC-07 | Show that a CAEP event was delivered but not enforced, and measure event→enforcement latency | 05, 07 | SCN-12 | WF-08 |
| UC-08 | Test delayed, duplicated and out-of-order revocation/restore events | 02, 07 | SCN-13 | WF-08 |
| UC-09 | Detect inconsistent authorization after re-enable/permission restoration (old tokens revive) | 01, 02, 04 | SCN-14 | WF-03, WF-11 |
| UC-10 | Verify application session cookies die on logout and on account disablement | 03, 06 | SCN-03 | WF-06 |
| UC-11 | Test that service-account/workload privileges end after removal | 05, 04 | SCN-10 | WF-03 |
| UC-12 | Check a vendor-documented propagation window (e.g. Entra CAE "up to 15 minutes" [EN §3]) holds in a tenant | 02, 04 | SCN-02, 15 | WF-04 |
| UC-13 | Detect distributed disagreement (replica/cache skew, non-monotonic enforcement) | 07, 05 | SCN-06, 15 | WF-05, WF-09 |
| UC-14 | Gate a release/config change in CI against a stored enforcement baseline | 05, 07, 06 | any MVP scenario | WF-09 |
| UC-15 | Produce triage-ready evidence for a bug-bounty/pentest finding and re-run it | 01, 03 | any | WF-04, WF-10 |
| UC-16 | Pre-engagement validation: prove scope, capability discovery and budgets are right without mutating anything | 01, 04 | none | WF-02 |
| UC-17 | Develop/extend an adapter or probe transport without touching the temporal core | 07, 02 | — | WF-12 |

---

## 3. Experiment states visible to the user

Names only; legality of transitions, timeouts and invariants are specified in RG-P02-007. The workflows use these names in the **expected happy-path order** `DRAFT → VALIDATED → BASELINING → ARMED → REVOKING → OBSERVING → ANALYZING → CLEANING_UP → COMPLETE|INCONCLUSIVE`, with `CLEANING_UP` also following `FAILED` and `ABORTED` when state was mutated (ASM-UW-01, **corrected by RG-P02-007 §10.1 / CCR-1**: the arming confirmation is recorded in `VALIDATED` and consumed by `start`; `ARMED` means the baseline/control gate passed, the confirmation and scope digest are pinned, and the run awaits the settle interval).

| State | User-visible meaning | What the operator can do |
|---|---|---|
| `DRAFT` | Scenario + fixture/scope chosen; not yet checked | Edit, validate |
| `VALIDATED` | Dry run passed: scope, plan, budgets, capabilities consistent; nothing sent to targets | Arm, edit (returns to DRAFT) |
| `ARMED` | Baseline/control gate passed; the operator's confirmation (given while `VALIDATED`) and the scope digest are pinned; waiting for the settle interval before revocation | Abort (disarm = abort before REVOKING) |
| `BASELINING` | Starts after the operator's confirmation (`start`): positive/negative/sibling controls and pre-event baseline running | Abort |
| `REVOKING` | Revocation event being executed (automated) or awaited (manual); anchor being fixed | Confirm manual acknowledgment, abort |
| `OBSERVING` | Scheduled probes of original and alternative credentials running | Abort; watch live timeline |
| `ANALYZING` | Interval, uncertainty, correlation and classification being computed | — |
| `COMPLETE` | Evidence valid; outcome class assigned (any of the six except where `INCONCLUSIVE` applies) | Review, export, re-run |
| `INCONCLUSIVE` | Run ended without sufficient valid evidence (failed control, 5xx at revoke, rate-limited window, ambiguous clock); outcome class `INCONCLUSIVE` (ASM-UW-02) | Review reason, fix, re-run |
| `FAILED` | Tool/environment error (adapter error, crash, unreachable lab) not attributable to the target | Review, cleanup, re-run |
| `ABORTED` | Operator or safety limit stopped the run (e.g. scope expiry, rate-limit stop) | Review, cleanup |
| `CLEANING_UP` | Restoration/cleanup of synthetic identities, sessions and changed settings from the restoration ledger | Watch; resolve residuals manually (WF-11) |

---

## 4. Workflows

### WF-01 — MVP end-to-end local lab run
**Purpose:** execute the 10-step MVP workflow [MP] on deterministic fixtures. **Persona:** PER-06, PER-02, PER-05. **Capabilities:** A, B, C, D. **Horizon:** MVP. **Goals/SC:** GOAL-01/02/04/05/06; SC-01…05, SC-12.
**Preconditions:** RG installed; container runtime or local Python for lab services; no external network needed. **Actors:** operator; RG experiment engine; lab (mock IdP, mock protected service(s)).

1. **(MVP-1)** O: start the lab with a named *fixture profile* (e.g. "introspection per call", "introspection cache 30 s", "local JWT until `exp`", "replica lag"). S: starts mock IdP + mock service(s) bound to loopback only (TM-32), waits for health, writes a **lab manifest** (versions, fixture id, seed, virtual/real clock) and a generated scope file covering exactly the lab hosts (RU-01).
2. **(MVP-2)** O: create an experiment from a scenario (e.g. SCN-02 account disablement) and the lab fixture. S: provisions through the adapter *actor* role: synthetic user, role/permission assignment, protected resource, an authenticated session/token pair; records each setup action in the restoration ledger. `⟦DRAFT⟧`
3. O: run the dry run (WF-02 steps 5–8). S: `⟦VALIDATED⟧`. O: arm. S: echoes tenant/realm, identity and actions; operator confirms; `⟦ARMED⟧`.
4. **(MVP-3)** S: `⟦BASELINING⟧` — waits the settle interval (≥ 1 s between minting probe tokens and any revocation; Keycloak same-second rule [KC §5.1; TF R-008]); runs positive control (identity reaches the resource; **content-level assertion**, not 200 alone, SV-001/SV-009), negative control (no credential and garbage credential rejected on the same endpoint), sibling control; freezes the request snapshot (SV-002; [ST §5.4]). Records results as evidence.
5. **(MVP-4)** S: `⟦REVOKING⟧` — executes the revocation action (here: disable user). Records `t_request_sent`, `t_ack_received`, acknowledgment state (acknowledged/rejected/unconfirmed) and fixes the anchor t₀ with its uncertainty window (charter §10).
6. **(MVP-5)** S: `⟦OBSERVING⟧` — probes the original session/token **and each configured alternative** (e.g. refresh grant, second token, introspection) on the post-revocation schedule: dense initially, backing off, with per-probe send/receive timestamps from monotonic + wall clocks; continues sibling control probes. Live timeline updates in CLI/GUI.
7. **(MVP-6)** S: stops after N consecutive confirmed denials per credential (confirmation tail, SV-004; R-004) or at the maximum observation duration. Records `t_last_access` and `t_first_denial` per credential.
8. **(MVP-7)** S: `⟦ANALYZING⟧` — computes the bounded exposure interval with anchor, probe-spacing and clock uncertainty per credential.
9. **(MVP-8/9)** S: looks up the enforcement expectation for (event, credential type, validation mode, profile) and classifies into one of the six classes with the rule id and profile recorded.
10. **(MVP-10)** S: generates the report (JSON, Markdown, HTML) and the evidence timeline; runs cleanup (`⟦CLEANING_UP⟧`) per restoration ledger; `⟦COMPLETE⟧`. O: opens the report (WF-10).

**Outputs:** run manifest; evidence bundle; report; audit log; restoration result.
**Failure/alternate paths:** F1 lab unhealthy → `⟦FAILED⟧` before arming, nothing mutated. F2 baseline control fails (e.g. identity cannot reach resource; negative control also accepted) → `⟦INCONCLUSIVE⟧` with the failing control named; no revocation is executed (SV-001). F3 revocation unacknowledged (5xx/503) → no downstream "denial" counts (SV-006); `⟦INCONCLUSIVE⟧`. F4 access never confirmed denied within the maximum duration → analysis uses expectation (e.g. local JWT: denial at `exp` → `EXPECTED` if consistent; otherwise class per rules). F5 flapping (denial then access) → exposure is not finalised; class `NEEDS_VERIFICATION` or per rules; evidence retained (R-004). F6 operator abort → `⟦ABORTED⟧` then cleanup. F7 virtual-clock runs are labelled `clock=virtual` and never mixed with real-time results.

### WF-02 — Authorised scope configuration and dry-run validation
**Purpose:** author the scope file, validate every planned action against it and preview all traffic without mutating anything. **Persona:** PER-01, PER-04, PER-05. **Capabilities:** C, D, E. **Horizon:** MVP. **Goals/SC:** GOAL-10; RU-01/02; SC-06, SC-09.
**Preconditions:** written authorisation (outside RG); identities and credentials provisioned by the operator or lab. **Actors:** operator; scope validator; adapters (read-only capability discovery).

1. O: create a project; create a scope file from the requirement set SCR-01…SCR-12 (§5). S: schema-validates with field-level errors (config *parsing* separate from *validation* [MP principles]).
2. S: resolves hostnames, normalises URLs, rejects wildcards broader than declared, userinfo-in-URL, non-declared ports; flags private/link-local/metadata addresses unless explicitly scoped (TM-03).
3. O: select scenario(s) and fixtures; reference identities/credential handles (never secret values).
4. S: expands the **probe plan** and the **admin-action plan** (every request template and administrative call with redacted credentials) and checks each item against scope *before* any network use ([ST G10]).
5. S: budget arithmetic: probes × schedule × rate limits vs the declared time/rate limits; flags schedules that exceed limits or SaaS defaults (RU-07).
6. S (optional, only with explicit opt-in): read-only **capability discovery** (OIDC discovery, adapter capability probes) through the scope-enforcing transport; records which capabilities are *advertised, absent or unknown* (SV-054) and the revocation-endpoint caveats ([EN §1.7]: absence is not a defect).
7. S: renders a dry-run report: scope digest, plan, preview, budget, unresolved assumptions, ToS clearance status. `⟦VALIDATED⟧` only if zero blocking findings.
8. O: **arm** — S echoes tenant/realm, identities, environment label and each mutating action; operator confirms by typing the tenant identifier. `⟦ARMED⟧`; scope digest pinned (change ⇒ back to `⟦DRAFT⟧`).

**Outputs:** validated scope + plan digest; dry-run report. **Failure/alternate paths:** F1 any action outside scope → blocking error naming the entry; nothing sent. F2 scope validity window expired (RU-08) → cannot arm. F3 capability discovery blocked by scope → plan proceeds with `capability=unknown`, flagged. F4 SaaS target lacks clearance acknowledgement (SCR-10) → cannot arm. F5 identity not marked `synthetic` but a mutating action is planned → blocking (RU-04).

### WF-03 — Live IdP (Keycloak) revocation experiment
**Purpose:** measure continued access against a real IdP in the lab. **Persona:** PER-02, PER-05, PER-06. **Capabilities:** A, B, C, D. **Horizon:** MVP. **SC:** SC-05.
**Preconditions:** Keycloak 26.8.x started with the lab realm import (`lab-assets/keycloak/revocationgap-lab-realm.json`; client `rg-tester`, resource server `rg-rs`, service account `rg-admin`) [KC §1.8]; required event types enabled (REFRESH/INTROSPECT/USERINFO are not stored by default [KC §1.5]); WF-02 completed. **Actors:** operator; Keycloak adapter (actor + probe roles); lab resource server(s).

1. S: adapter checks the Keycloak version (pin 26.8.x, version recorded in every result [KC §5 item 14]) and capability matrix [KC §2].
2. S: creates a **fresh user per scenario** (never re-enabled/reused across experiments [KC §5.3]); issues tokens via a lab-supported grant; records issuance time (`iat`) as a free server-clock sample (1 s resolution) [KC §1.9].
3. S: `⟦BASELINING⟧` with controls on each observation channel: local-JWT resource server, introspection (RS client in `aud` [KC §5.2]), `userinfo`, refresh grant on a **disposable token-family copy** (probe refresh consumes the RT under rotation and a replay kills the session [KC §5.4]). ≥ 1 s settle before revocation.
4. S: `⟦REVOKING⟧` — executes the chosen action (disable user / delete session / `POST /users/{id}/logout` / remove role or group / revoke RT) using the exact calls in [KC §2.1]; anchors t₀ on the Keycloak **admin-event `time`** (server clock, ms) with the tester's monotonic send/receive bracket as uncertainty [KC §1.9 recipe].
5. S: `⟦OBSERVING⟧` — probes all channels. Expected structure per [KC §1.2]: local JWT stays valid until `exp`; introspection/userinfo/refresh flip after disable/logout; role removal shows in introspection immediately but in tokens only after refresh. Per-channel intervals are reported separately.
6. S: collects Keycloak event `reason`/error codes as *secondary evidence* for mechanism attribution (e.g. `user_disabled`, `user_session_not_found`) [KC §1.5].
7. S: `⟦ANALYZING⟧` — classifies per channel under `protocol` and `vendor-doc:keycloak` profiles (e.g. local-JWT acceptance before `exp` → `EXPECTED`, SV-012).
8. S: `⟦CLEANING_UP⟧` deletes the synthetic user (do **not** re-enable: re-enabling revives old tokens [KC §1.2]); `⟦COMPLETE⟧`.

**Failure/alternate paths:** F1 same-second boundary (probe token minted in the revocation second) → settle rule violated ⇒ the run is marked `⟦INCONCLUSIVE⟧` for that credential [KC §5.1]. F2 introspection `active:false` for non-revocation reasons (client not in `aud`, wrong client auth) → caught by the pre-event control; `⟦INCONCLUSIVE⟧`. F3 no `Date` header on dev responses [KC §1.8] → clock offset taken from events/`iat`; confidence reduced. F4 offline-session/session-less tokens are unaffected by session logout [KC §1.2] → adapter notes explain; not a defect. F5 admin API 403 for missing realm-management role → `⟦FAILED⟧` naming the missing privilege [KC §2.1].

### WF-04 — Manual-revocation experiment against a third-party SaaS IdP
**Purpose:** measure continued access when the *operator* (or the target's own staff) performs the revocation through the vendor console/own tooling and RG only observes. **Persona:** PER-03, PER-01, PER-04. **Capabilities:** B, C, D. **Horizon:** MVP mechanics (manual acknowledgment); live vendor adapters v1.x. **SC:** SC-12.
**Preconditions:** scope declares the target hosts, own/test identities, clearance acknowledgement for the provider (RU-07), conservative rate limits; operator can sign in to the vendor console. **Actors:** operator; RG; third-party IdP/app.

1. WF-02 steps 1–8. S additionally prints provider-specific caveats from research (e.g. Okta `/revoke` always 200 [OK §(e) item 1]; Auth0 JWT access tokens "cannot be revoked", management deletes eventually consistent [A0 §0]; Entra CAE needs `cp1` and CAE-enabled resource, `revokeSignInSessions` has "a few minutes" lag [EN §3, §5]).
2. S: `⟦BASELINING⟧` — controls as in WF-01 step 4, at the provider-safe rate; records token `exp`/`iat` where decodable (analysis only, no verification).
3. S: `⟦REVOKING⟧` — displays an **action card** (what to do, which identity, which console path) and **starts continued low-rate probing**. O: presses "starting revocation" (marker M1), performs the revocation, then presses "revocation acknowledged" (marker M2) and optionally enters the vendor-shown timestamp and the console/API response. S records M1 and M2 on its own clocks and the operator-asserted time as **assumption-tagged** data, never as observed fact (charter §10 "Anchor").
4. S: anchor t₀ = M2 with uncertainty window [M1, M2] (plus operator-asserted time if given, flagged); probes before M1 count as pre-event samples; probes between M1 and M2 are *ambiguous* and excluded from the interval bounds' tight side.
5. S: `⟦OBSERVING⟧` at a paced schedule matched to the documented windows (minutes to hours for Entra/Okta/Auth0 [EN §3, §4 "Delay-sensitive tests"]); honours `Retry-After`/429 by pausing and marking the window `INCONCLUSIVE` (SV-043); for SaaS targets repeats trials where the scope permits, since SaaS measurements are statistical and claims are bounded [TF §1 last row; CA §4.4].
6. S: optional lagging oracles (sign-in/audit logs) are collected as **secondary** evidence only, never as time-of-event source [EN §5 item 9; OK §(e) item 7].
7. S: analysis + classification under `protocol` and the matching `vendor-doc:<provider>` profile; `⟦COMPLETE⟧`.

**Failure/alternate paths:** F1 operator never confirms M2 within the confirmation timeout → `⟦INCONCLUSIVE⟧`. F2 operator reports the vendor action failed → experiment ends without exposure claim. F3 revocation acknowledged but probes never deny within the documented window → class per profile (e.g. Auth0 JWT: `EXPECTED`/`DOC_DELAY`); never `VULN` on provider semantics alone (SV-012). F4 clearance missing → cannot arm (WF-02 F4). F5 vendor-side cleanup remains manual: S lists residuals (WF-11).

### WF-05 — Multi-identity and cross-service comparison
**Purpose:** compare enforcement for several identities and several services after **one** anchored event. **Persona:** PER-04, PER-05, PER-07. **Capabilities:** A, B, C, D, E. **Horizon:** MVP-partial (two identities × two lab services), v1.x (real multi-service). **Goals:** GOAL-08; D-2.
**Preconditions:** scope lists every service host; operator-declared identity roles: *subject* (revoked), *sibling control* (not revoked), optionally *differently-privileged* identity. **Actors:** operator; engine; ≥ 2 targets (e.g. gateway + backend, or services A and B).

1. O: define the experiment matrix: identities × services × operations × credentials (token, session cookie). S: scope-checks every cell; derives per-service probe templates (schema-described via Schemathesis for services that publish OpenAPI, raw otherwise).
2. S: `⟦BASELINING⟧` for each cell: positive control, negative control; cells whose baseline fails are excluded and listed (not silently dropped).
3. S: `⟦REVOKING⟧` one event; one anchor shared by all cells.
4. S: `⟦OBSERVING⟧` — probes every cell with one scheduler (bounded concurrency, per-host limits); each cell gets its own `t_last_access`/`t_first_denial`.
5. S: analysis computes per-cell intervals and **pairwise disagreement** (e.g. gateway denies at 2 s, backend accepts until 3 600 s; service B never denies); correlates with validation modes where known; flags non-monotonic cells.
6. S: classifies each cell and the differential (SCN-05, 07, 11, 15 patterns); report shows the matrix as a timeline per cell.

**Failure/alternate paths:** F1 a service unreachable → that column `INCONCLUSIVE`, others continue. F2 shared per-host rate limit shared between cells → scheduler reduces rate and records it; 429 windows excluded (SV-043). F3 direct-to-backend access outside declared hosts → refused by scope (RU-01, SCR-03). F4 sibling control denied → whole experiment `INCONCLUSIVE` (the resource itself may be down).

### WF-06 — Refresh-token and session-cookie experiments
**Purpose:** test credentials that mint or hold new access: refresh tokens and application sessions; include *new* sessions after revocation. **Persona:** PER-01, PER-02, PER-03, PER-06. **Capabilities:** A, B, C, D. **Horizon:** MVP (Keycloak + lab app sessions). **Scenarios:** SCN-03, SCN-04, SCN-08 (HTTP reconnect/new login).
**Preconditions:** per-probe disposable credential copies available (see step 2). **Actors:** operator; engine; IdP adapter; cookie-jar client.

1. O: choose credential kinds: refresh token (rotating or not), offline token, app session cookie (per identity cookie jar), and an event (logout, RT revoke, password reset, disable).
2. S: **creates a separate token family/session per probe slot** — a refresh probe consumes the RT under rotation and replaying it can revoke the whole family, contaminating later observations [KC §5.4; A0 §(e) item 4; OK §(e) item 3]. Rotation overlap/grace windows (Okta default 30 s; Auth0 configurable) are read into the expectation so that in-window replays are not findings [OK §(c); A0 §(c)].
3. S: baseline: refresh succeeds returning a new AT (and RT if rotating); cookie request returns authenticated content (content assertion). Negative controls: garbage RT → `invalid_grant`-class rejection; no cookie → login/denial.
4. S: executes the event; anchors t₀.
5. S: observes with the **correct failure signatures**: HTTP 400 `invalid_grant` = rejected; 401/`invalid_client` = tester client error → `INCONCLUSIVE`; 2xx with new AT but no new RT = old RT still valid (SV-049; RFC 6749 §6 via [STD]). Cookie probes use fresh vs reused connections as configured and record `connection_reused` ([ST N9]).
6. S: also attempts **new sessions** after the event (new login/refresh for a disabled identity → expected denial text e.g. "Account disabled" [KC §2.2]) and records them as separate observations.
7. S: classifies by token type: RT revoke→refresh success `VULN` (SV-019, after excluding TTL expiry/client mismatch); AT revoked/RT valid `EXPECTED` (SV-021); app session after logout/disable `VULN` only under an ASVS profile (SV-032/033), otherwise `RISKY_CONFIG`/`EXPECTED` per rules (SV-012 caveat).

**Failure/alternate paths:** F1 RT expired by TTL/inactivity before event → experiment `INCONCLUSIVE` (SV-019 pre-check). F2 rotation reuse kills session unexpectedly → recorded as contamination; affected slot discarded. F3 cookie sessions bound to browser-only flows → operator-supplied session export or lab app session (NG-16). F4 non-`offline_access` vs `offline_access` unknown → `INCONCLUSIVE` for that sub-result (SV-027).

### WF-07 — Persistent connection (WebSocket) experiment
**Purpose:** determine whether an established connection continues to serve after revocation and whether reconnection succeeds. **Persona:** PER-01, PER-03, PER-07. **Capabilities:** B, C, D, E. **Horizon:** v1.x. **Scenario:** SCN-08. **Risk:** R-014.
**Preconditions:** scope allows the WebSocket origin; test application defines an authenticated message/echo operation with a verifiable response. **Actors:** operator; WebSocket probe (`rg_probe`, `websockets`); engine.

1. O: define handshake credential (token/cookie), a heartbeat/"authorised echo" message and expected response assertions.
2. S: `⟦BASELINING⟧` — opens connection (handshake 101), sends the authorised message, asserts the response; negative control: handshake without/with garbage credential must not yield 101 (SV-055 a).
3. S: `⟦REVOKING⟧` — event executed, anchor fixed; the baseline connection **stays open**.
4. S: `⟦OBSERVING⟧` — (a) periodic authorised messages on the **existing** connection, recording acceptance, close code (1008/1000/1001/1006/4xxx) and `connection_age_after_revocation`; (b) periodic **new handshakes** with the revoked credential (must not yield 101); both tracks timestamped; (c) Origin handling is **not** tested here (SV-055 c; separate non-revocation check).
5. S: analysis: existing-connection survival is *not* a standards violation (SV-055 b; RFC 6455 has no re-auth [STD §3]); class defaults to `NEEDS_VERIFICATION` unless the profile (ASVS V7.4.1) or vendor doc decides; 101 on revoked-credential handshake is classified like HTTP acceptance by token type (SV-012/015).

**Failure/alternate paths:** F1 server closes idle connection for unrelated reasons (timeout before event) → baseline invalid; `INCONCLUSIVE`. F2 connection dropped by network → reconnect attempt counted separately and flagged. F3 target multiplexes tokens in-band (message-level auth) → probe template must carry the in-band token; unsupported shape → `⟦FAILED⟧` with reason, not a silent skip.

### WF-08 — CAEP event-to-enforcement experiment
**Purpose:** measure delivery and **enforcement** latency of a signalled event. **Persona:** PER-05, PER-07, PER-02. **Capabilities:** A, B, C, D, E. **Horizon:** v1.x, **experimental** [TF R-015]. **Scenarios:** SCN-12, SCN-13.
**Preconditions:** lab = Keycloak 26.8.x with `--features=ssf`, realm attribute `ssf.transmitterEnabled=true`, `ssf-events` listener enabled, a receiver client with `ssf.enabled=true`; an **enforcing target** (lab API implementing a receiver) and RG's own observing subscription; poll delivery preferred (push needs https non-loopback [KC §1.6]). **Actors:** operator; RG SSF client; transmitter; enforcing target.

1. S: discovers the transmitter (`/.well-known/ssf-configuration`); aborts if `issuer` ≠ URL base (SV-041). Creates/uses a stream; asserts `status=enabled` and fires a **Verification event** (SV-038). Failure ⇒ `INCONCLUSIVE` (no event ≠ no enforcement).
2. S: `⟦BASELINING⟧` — controls on the protected API through the enforcing target; subjects subscribed (`default_subjects` is `NONE` by default [KC §5 item 12]).
3. S: `⟦REVOKING⟧` — triggers an event whose SET Keycloak emits (e.g. `POST /users/{id}/logout` → `session-revoked`; disable → `account-disabled`; password reset → `credential-change`) [KC §1.6]; events for role/group removal are **not** emitted, so SCN-12 uses the three above. Anchor t₀ = admin action acknowledgment.
4. S: `⟦OBSERVING⟧` — records SET receipt time at RG's receiver; computes delivery latency from `event_timestamp` if present else `iat` (with caveat, SV-040); simultaneously probes the protected API for enforcement.
5. S: for SCN-13 uses lab fault injection (delay, duplicate, reorder, drop) on the delivery path.
6. S: classification per SV-037: delivered + enforced within documented behaviour → `EXPECTED`/`DOC_DELAY`; delivered + access continues beyond a *declared* receiver policy → `VULN`/`DOC_DELAY`; no declared policy → `NEEDS_VERIFICATION`. SET wire-conformance findings are out of scope (NG-04).

**Failure/alternate paths:** F1 SSF experimental structure changed (26.7→26.8) → version-gate refuses other versions [KC §1.6]. F2 push outbox delay (≥ 30 s drain) mistaken for non-delivery → adapter reads the delivery method and sets the schedule accordingly. F3 dead-lettered event after retries → recorded as non-delivery with cause.

### WF-09 — Historical regression run in CI
**Purpose:** detect enforcement drift across product/config versions. **Persona:** PER-05, PER-07, PER-06. **Capabilities:** B, D, E. **Horizon:** v1.x (regression analysis); MVP produces the machine-readable results it needs. **Goal:** GOAL-12; SC-05.
**Preconditions:** stored historical baseline (prior run set with manifests); scenario + fixture/target pinned; CI has no production credentials; the lab/Keycloak targets are used by default (SaaS in CI is opt-in and discouraged: [TF §1]). **Actors:** CI runner; RG headless; store.

1. CI: invoke the run non-interactively with a scope file committed to the repository (reviewed like code) and secrets from the CI secret store as handles.
2. S: runs WF-01/WF-03 headlessly, K repetitions (K set per scenario); writes machine-readable results (JSON, JUnit, SARIF) and a manifest of component versions.
3. S: compares the new interval distribution against the baseline: shift in bounds, class change, new flapping, new `INCONCLUSIVE` causes; applies configured thresholds (e.g. "class worsened", "upper bound grew by > X %" — thresholds are explicit per project).
4. S: exit status distinguishes *regression*, *no regression*, *inconclusive/infrastructure* (never reported as pass) and *tool failure*.
5. O: review the diff report (WF-10 compare view); accept a new baseline only through an explicit, audited action.

**Failure/alternate paths:** F1 timing noise → decision requires the configured repetitions and uses distributions, not single runs. F2 baseline produced under a different provider version → comparison flagged `version-skew` (R-009). F3 CI cannot reach the lab → `INCONCLUSIVE`, not green.

### WF-10 — Report review and evidence export
**Purpose:** let a reviewer judge, reproduce and share the result. **Persona:** all. **Capabilities:** D. **Horizon:** MVP.
**Preconditions:** a completed experiment. **Actors:** reviewer; report viewer (CLI/GUI); evidence store.

1. O: open the report. S: shows outcome class + **profile**, rule id, one-paragraph conclusion, exposure interval per credential with uncertainty components (anchor, probe spacing, clock) and confidence.
2. S: the authorization **timeline**: setup, controls, event (request/ack/anchor), every probe with outcome and assertion results, first/last markers, flapping.
3. S: every statement is tagged **observed fact / calculated value / assumption / hypothesis**; assumptions (e.g. operator-asserted time, undocumented cache) listed with how to falsify them.
4. S: provider/protocol interpretation and mechanism attribution with the cited rule (e.g. "JWT local validation: acceptance until `exp` is protocol-expected, SV-012").
5. O: drill into any probe → normalised exchange; raw bodies/headers are **redacted by default**; "reveal raw" requires an explicit action and writes an audit record (RU-06).
6. S: reproduction steps: ordered commands with credential placeholders (`${RG_TOKEN_<identity>}`) [ST N7], preconditions and expected result per step.
7. O: export: report (JSON/Markdown/HTML), evidence bundle (hash-verified), HAR/JUnit/SARIF where applicable; S prints the bundle digest. O: compare with another run/IdP/service (diff of intervals, classes, manifests).
8. O: re-analyse the same evidence under a different profile — a **new analysis record**, never an edit of the original classification (ASM-UW-03).

**Failure/alternate paths:** F1 bundle hash mismatch on load → report marked *integrity failed* and refuses export without override (TM-26). F2 export would include raw credentials → blocked unless explicit override, recorded. F3 comparing runs with different manifests → differences listed before the comparison.

### WF-11 — Interrupted-run recovery, cleanup and restoration
**Purpose:** return the environment to a known state after crash, abort, power loss or failure; never leave synthetic users disabled or sessions dangling silently. **Persona:** PER-04, PER-01, PER-02. **Capabilities:** C, D. **Horizon:** MVP (detect, classify, restore from ledger); resuming `⟦OBSERVING⟧` automatically is v1.x (ASM-UW-04). **Goal/SC:** SC-13.
**Preconditions:** the store contains a restoration ledger (every setup and revocation action with its inverse and `restorable` flag). **Actors:** operator; recovery service; adapters.

1. S (at next start, or on `⟦ABORTED⟧`/`⟦FAILED⟧`): detects non-terminal experiments by their persisted state; lists them with last state and time.
2. S: for each, shows the ledger: actions done, inverse action available, `restorable` yes/no/partial, and what *cannot* be restored.
3. O: choose *restore*, *mark and keep evidence only*, or *abandon*. S: `⟦CLEANING_UP⟧` executes inverse actions through the adapters within scope (e.g. delete tool-created synthetic users; **re-enabling is avoided** because it revives old tokens [KC §5.3] and Entra re-enable has 15–40 min downstream latency [EN §3]; Okta users must be deactivated before deletion [OK §(e) item 12]).
4. S: verifies the end state against the ledger (read-back) and records residuals; unresolved items are listed with manual instructions.
5. S: if observation had started, evidence collected so far is preserved; the run ends `⟦ABORTED⟧` or `⟦FAILED⟧` with `analysis=partial`; no classification is assigned from a truncated schedule (INCONCLUSIVE with reason).

**Failure/alternate paths:** F1 adapter credentials expired → prompts for handle, otherwise residual listed. F2 target tenant changed since (scope digest differs) → refuses automated restore, lists manual steps. F3 ledger corrupted → falls back to evidence timeline; restoration is manual. F4 second recovery during recovery → idempotent: each inverse action checks current state first.

### WF-12 — Plugin / provider-adapter development
**Purpose:** add an IdP, probe transport, report format or revocation mechanism without touching the temporal core. **Persona:** PER-07, PER-02. **Capabilities:** E (A–D by effect). **Horizon:** MVP interfaces (internal adapters use them); loading third-party plugins v1.x (ASM-UW-05). **Goal:** GOAL-09, GOAL-13; D-7.
**Preconditions:** published interface contracts and the adapter contract-test kit (RG-P12-003). **Actors:** developer; plugin loader; contract tests; lab.

1. O: scaffold an adapter against the stable interface; declare its **capability matrix** (actor and probe roles, observation endpoints, event sources) with a **research citation** per capability and an evidence tag (rule: no capability is claimed without researched behaviour [MP E; RR §1]).
2. O: run the contract-test kit against the mock IdP/lab and, if available, a real instance; S reports capability claims that the tests cannot falsify.
3. O: register the plugin in the application allow-list with its version and digest (TM-22); S refuses unlisted plugins.
4. S: at load, validates interface version compatibility, capability manifest schema and that the plugin imports nothing outside its permitted layer (e.g. no `schemathesis` import outside `rg_stbridge`, [ST ISO-7]).
5. O: run WF-01 with the new adapter; S shows it in the capability matrix and in reports as *plugin-provided* with its version.

**Failure/alternate paths:** F1 contract tests fail → plugin cannot be allow-listed. F2 undeclared capability invoked at runtime → error category `capability_not_declared`; experiment `⟦FAILED⟧`. F3 interface version mismatch → refuse load with migration pointer.

---

## 5. Authorised-scope configuration requirements

The scope file is the single authorization gate (RU-01). Each requirement is testable; the schema itself is specified in RG-P03-003/RG-P11-002.

| ID | The operator MUST declare | Validation rule (S = system behaviour) |
|---|---|---|
| SCR-01 | **Authorization statement**: authorising party, asset description, engagement/reference id, validity window (`valid_from`, `valid_until`), operator identity | Missing/expired ⇒ refuse to arm (WF-02 F2); recorded verbatim in manifest |
| SCR-02 | **Environment label** per target: `lab`, `staging`, `production`, `third-party-saas` | `production`/`third-party-saas` require SCR-10 and extra arm confirmation; mutating actions refused on unlabelled targets |
| SCR-03 | **Targets**: scheme, exact host (or explicit suffix list), port, path prefixes; TLS verification mode | Everything not listed is denied, including redirect targets and schema-provided server URLs (TM-01, TM-02); IP-literal/link-local/metadata hosts need explicit listing; TLS verify-off recorded as a warning |
| SCR-04 | **Tenants/realms/organisations** (IdP identifiers: realm name, tenant id, org URL, Auth0 domain) | The adapter reads back the tenant identity at preflight and aborts on mismatch (TM-05) |
| SCR-05 | **Identities**: id/handle, role (`subject`, `sibling_control`, `other`), `synthetic: true|false`, owner, credential **handle** (never the secret) | Administrative actions only on `synthetic: true`; ≥ 1 `sibling_control` recommended, required for SaaS/production-labelled runs |
| SCR-06 | **Permitted probe operations**: method + path/operation id + parameters; default read-only. Mutating probes listed individually with justification | Operations not listed are not probed; GraphQL mutations denied unless listed |
| SCR-07 | **Permitted administrative actions** per tenant and identity: e.g. `disable_user`, `remove_role`, `revoke_session`, `revoke_refresh_token`, `password_reset`, `delete_user`; each flagged `mutating` and with a restoration policy (restore / delete-created / manual) | Unlisted action ⇒ refused before any network call (SC-09); `delete_*` requires `synthetic: true` and a created-by-tool marker |
| SCR-08 | **Credential sources**: secret-store/env handles for IdP admin credentials and test-identity credentials; least-privilege declaration | Secrets never appear in the scope file; file with inline secret patterns ⇒ rejected (TM-07) |
| SCR-09 | **Rate and time limits**: max requests/s per host and per identity, max concurrent probes, max experiment duration, max total probes, retry/jitter policy | Defaults conservative (RU-07); schedule exceeding a limit ⇒ dry-run blocks; 429 ⇒ stop/pause rule |
| SCR-10 | **SaaS clearance acknowledgement** per provider: acknowledged policy (e.g. Auth0 pen-test notice reference and date; Okta consent for benchmarking; Entra MSRC rules), acknowledging person, date | Missing ⇒ cannot arm (RU-07) |
| SCR-11 | **Evidence handling**: retention, encryption on/off, handling classification, redaction level | Defaults: redaction on, no raw credentials in exports |
| SCR-12 | **Listeners and plugins**: bind addresses/ports for CAEP/back-channel receivers (default loopback), plugin allow-list (name, version, digest) | Non-loopback bind requires explicit entry plus TLS and authentication (TM-21) |

---

## 6. Workflow ↔ capability map

| Workflow | A identity/authz analysis | B temporal simulation | C offensive verification | D evidence/reporting | E extensibility | Horizon |
|---|---|---|---|---|---|---|
| WF-01 MVP lab run | ● | ● | ● | ● | ○ | MVP |
| WF-02 Scope + dry run | ○ | ○ | ● | ● | ○ | MVP |
| WF-03 Keycloak live | ● | ● | ● | ● | ○ | MVP |
| WF-04 Manual SaaS revocation | ● | ● | ● | ● | ○ | MVP (mechanics) / v1.x (vendor adapters) |
| WF-05 Multi-identity / cross-service | ● | ● | ● | ● | ● | MVP-partial / v1.x |
| WF-06 Refresh token + session cookie | ● | ● | ● | ● | ○ | MVP |
| WF-07 WebSocket | ○ | ● | ● | ● | ● | v1.x |
| WF-08 CAEP | ● | ● | ● | ● | ● | v1.x (experimental) |
| WF-09 CI regression | ○ | ● | ○ | ● | ● | v1.x |
| WF-10 Report review/export | ○ | ○ | ○ | ● | ○ | MVP |
| WF-11 Recovery/cleanup | ○ | ○ | ● | ● | ○ | MVP / v1.x resume |
| WF-12 Plugin development | ○ | ○ | ○ | ○ | ● | MVP interfaces / v1.x loading |

● primary · ○ supporting or not exercised. Every capability letter A–E is the primary subject of at least one workflow (A: WF-01/03/06; B: WF-01/07; C: WF-02/05; D: WF-10; E: WF-12).

## 7. ID registry and assumptions

| Prefix | Range |
|---|---|
| PER | PER-01…PER-07 |
| UC | UC-01…UC-17 |
| WF | WF-01…WF-12 |
| SCR | SCR-01…SCR-12 |

| ID | Assumption / open question | Owner |
|---|---|---|
| ASM-UW-01 | (Resolved by RG-P02-007 — see §3.) The ordering `… ANALYZING → CLEANING_UP → COMPLETE` and the rule that `CLEANING_UP` also follows `FAILED`/`ABORTED` are workflow-level expectations for RG-P02-007 to confirm or change | RG-P02-007 |
| ASM-UW-02 | State `INCONCLUSIVE` coincides with outcome class `INCONCLUSIVE`; all other classes are carried by `COMPLETE` | RG-P02-007/-009 |
| ASM-UW-03 | Re-analysis under another profile creates a new analysis record and never mutates the stored classification | RG-P08-006/-011 |
| ASM-UW-04 | Automatic resumption of an interrupted `OBSERVING` phase is not MVP; recovery restores and ends the run as partial | RG-P11-005 |
| ASM-UW-05 | MVP ships in-tree adapters only; third-party plugin loading is opt-in v1.x | RG-P03-009, RG-P11-004 |
| ASM-UW-06 | RG's own SSF subscription for delivery timestamps (WF-08 step 4) is a second stream/client in addition to the enforcing target's stream; not verified in the Keycloak lab (stream-per-client model from [KC §1.6], **I**) | RG-P04-011 |
