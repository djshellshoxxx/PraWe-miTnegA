---
id: RG-P01-001
title: "Project charter"
phase: "01"
package: docs
status: DRAFT
depends_on: [RG-P00-006]
---

# RevocationGap — Project Charter (RG-P01-001)

**Status:** DRAFT for coordinator commit · **Date of evidence:** 2026-10-12 · **Scope:** specification package only (no application code) — see [`01-MASTER-ROADMAP.md`](01-MASTER-ROADMAP.md) preamble.

**Citation keys.** Every behavioural claim below cites a research document. `[RM]` = `01-MASTER-ROADMAP.md`; `[TF]` = `02-RESEARCH/TECHNICAL-FEASIBILITY.md` (risks `R-xxx`); `[CA]` = `COMPETITIVE-ANALYSIS.md`; `[STD]` = `STANDARDS-REFERENCE.md` (`STD-xxx` inventory, `SV-xxx` validity rules, §3 taxonomy); `[ST]` = `SCHEMATHESIS-INTEGRATION.md` (`N#` neutralisations, `ISO-#`, `G#` gaps); `[KC]`/`[EN]`/`[OK]`/`[A0]`/`[AL]` = `providers/KEYCLOAK|ENTRA-ID|OKTA|AUTH0|AUTHLIB-AND-LIBS.md`; `[RR]` = `RESEARCH-REGISTER.md` (`RF-#`, `RQ-#`). `[MP]` = the master development prompt as summarised in `[RM]` §1 (capabilities **A–E**, differentiators, MVP workflow, mandatory scenarios). Items marked **ASM-CH-nn** are assumptions listed in §12.

---

## 1. Vision and problem statement

**Problem.** When an administrator, IdP, resource owner or automated security system changes an authorization state (disables an account, removes a role, ends a session, revokes a token, signals a risk event), operators assume access ends. In practice enforcement is distributed across the IdP, gateways, caches, resource servers, application session stores and long-lived connections, each with its own validation mode and delay. Evidence that the gap is real and unmeasured:

1. The standards deliberately leave most of it undefined: a self-contained JWT access token may be accepted until `exp` after revocation, disablement or role removal; only a few behaviours are REQ-level (refresh-token revocation, `exp` enforcement, introspection `active:false`) [STD §3 "Reading the table"; SV-012].
2. Vendors document delays rather than guarantees: Entra CAE "up to 15 minutes", CA/group changes "up to one day" [EN §3]; Auth0 JWT access tokens "cannot be revoked" and Management-API deletes are "eventually consistent" [A0 §0, §(c)]; Okta publishes no latency number [OK §0 item 7]; Keycloak lab shows disable ≠ logout and re-enable revives old tokens [KC §1.2, RF-3].
3. A 2025 measurement of the top-1M sites found 85 % of JWT-using sites do not invalidate tokens on logout (web-login population; transfer to API/IdP-managed tokens is an inference) [CA §0 item 6].
4. No examined tool measures a temporal enforcement window; the closest prior art (OAuch, OIDF suite) revokes, waits a fixed 5–30 s and probes once [CA §0 items 1–2].

**Vision.** RevocationGap (RG) is an offensive identity-security and authorization-testing tool that turns "was access really revoked?" into a **reproducible, evidence-backed, uncertainty-bounded measurement**: which previously authorized operations remain possible after a state change, for how long (as a bounded interval, never a false-precision number), through which authentication mechanism, and whether that behaviour is expected, documented, risky or a vulnerability — judged against explicit enforcement expectations, not against a blanket "unexpired token = bug" assumption [TF R-001, R-003].

RG examines **actual authorization behaviour of the target** (what the API/app does when called), not IdP configuration or token metadata alone [MP purpose; D-4].

## 2. Research question and outcome classes

**RQ (verbatim scope).** After an administrator, IdP, resource owner or automated security system changes an authorization state, exactly which previously authorized operations remain possible, for how long, through which authentication mechanisms, and under what conditions?

**Outcome classes.** Every experiment that reaches analysis ends in exactly one of six classes. The identifiers are the classifier labels already fixed in [STD §4 preamble] and [TF R-001]; the formal classification rules are RG-P02-009.

| # | Master-prompt class | Label | Assigned when (summary; normative rules in RG-P02-005/-009) | Anchoring rules |
|---|---|---|---|---|
| 1 | Expected consequence of protocol semantics | `EXPECTED` | Continued access (or its absence) is what the declared policy profile allows, e.g. JWT access token accepted before `exp` by a local-validation resource server | SV-011, SV-012, SV-018, SV-021, SV-030 |
| 2 | Documented enforcement delay | `DOC_DELAY` | Continued access lies within a propagation window stated in vendor/provider documentation; **standards alone never produce this class** | SV-012, SV-016; [EN §3], [A0 §(c)], [OK §(c)] |
| 3 | Configurable risk / undesirable posture | `RISKY_CONFIG` | Behaviour is permitted but exceeds a recommended bound, e.g. access-token lifetime > 1 h (RFC 6750 §5.3 SHOULD), RT survives password change | SV-013, SV-016, SV-024, SV-033 |
| 4 | Actual authorization vulnerability | `VULN` | A MUST-level requirement, a profile-scoped requirement (ASVS/NIST), or a provider/contract promise is violated and independently confirmed | SV-010, SV-015, SV-019, SV-022, SV-032, SV-033 |
| 5 | Potential vulnerability needing verification | `NEEDS_VERIFICATION` | Evidence is consistent with a defect but the standard/provider is silent or the oracle is ambiguous (e.g. open WebSocket survives revocation) | SV-009, SV-020, SV-023, SV-037, SV-055; [TF R-014] |
| 6 | Inconclusive (missing evidence/limits) | `INCONCLUSIVE` | A validity precondition failed (no positive/negative control, 5xx at revoke, 429, cache-served response, clock ambiguity) | SV-001, SV-002, SV-006, SV-043, SV-048 |

Rules: (a) every classification records the **policy profile** that produced it (`protocol` default; `asvs-5.0.0-L1|L2|L3`; `nist-aal2|aal3`; `vendor-doc:<provider>`) [STD SV-046]; (b) `NOT_APPLICABLE` (SV-044, SV-054: capability absent) is a *test-applicability status*, not a seventh outcome class; (c) an unexpired JWT remaining usable is never classified `VULN` on that fact alone [MP; TF R-001].

## 3. Goals

| ID | Goal | Primary traceability |
|---|---|---|
| GOAL-01 | Measure, for a defined (identity, credential/session, protected operation, state-change event) tuple, the bounded observed exposure interval, with sampling limits, orchestration latency and clock uncertainty stated | [MP B]; [TF §1 row 1]; D-1, D-5 |
| GOAL-02 | Classify each result into the six outcome classes with explicit, profile-aware rules and a recorded profile | [MP D]; D-3 |
| GOAL-03 | Execute or observe revocation events with a precise anchor timestamp and acknowledgment state, supporting manual, automated (test identities only) and event-driven revocation | [MP C]; RG-P06 |
| GOAL-04 | Guarantee probe validity: positive and negative controls, identical pre/post requests, independent oracle, confirmation tail; never infer access from HTTP 200 alone | [MP C]; [STD SV-001–SV-009]; D-4 |
| GOAL-05 | Produce evidence and reports: timestamped authorization timeline, raw and normalised evidence, human- and machine-readable output, explicit separation of observed fact / calculated value / assumption / hypothesis | [MP D]; D-8 |
| GOAL-06 | Provide a deterministic virtual-time lab to validate the measurement model, plus a real-IdP lab (Keycloak 26.8.x) as the first live target | [TF §1 row 2]; RG-P09 |
| GOAL-07 | Ship a catalog covering at least the 15 mandatory scenarios (SCN-01…SCN-15, `03-PRODUCT/THREAT-MODEL.md` Part A), each reproducible in the lab or an explicitly supported environment | [MP Phase 7]; RG-P07 |
| GOAL-08 | Support multi-identity differential and cross-service enforcement comparison against one anchored event | [MP B, C]; D-2 |
| GOAL-09 | Keep every IdP, target type, probe transport, report format and revocation mechanism behind stable, separately testable interfaces; use Schemathesis as a version-pinned, never-forked HTTP/schema layer confined to `rg_stbridge` | [MP E]; [RM RM-ST-1…6]; D-7 |
| GOAL-10 | Be safe by default and auditable: authorised scope file, read-only probes by default, explicit opt-in for mutating operations and administrative revocation, audit log, no stealth | [MP C]; [TF R-006, R-022] |
| GOAL-11 | Offer a cross-platform CLI (Windows and Linux primary, macOS considered) and an optional local browser GUI plus automation API over the same core modules | [MP platforms]; [TF §2 CLI/GUI rows] |
| GOAL-12 | Detect regression of enforcement behaviour across product/config versions by comparing interval distributions, not only pass/fail | [CA §4.1 D7]; RG-P08-009 |
| GOAL-13 | Claim support for a provider/protocol only after its behaviour and API capabilities have been researched and cited | [MP E]; [RR §1 evidence rule] |
| GOAL-14 | Deliver a specification package that is an implementation contract: every requirement maps to a test and every module spec follows the 27-section template | [RM §3 Phase 15; RM-D6] |

## 4. Non-goals and exclusions

Horizon: **P** = permanent exclusion; **M** = excluded from MVP only (may appear in a later release).

| ID | Non-goal / exclusion | Hor. | Reason / evidence |
|---|---|---|---|
| NG-01 | Generic authorization-matrix / BOLA / IDOR testing. Only a *pre-event control probe* proving the identity was authorized is kept | P | Mature tools overlap [CA §4.2, §4.3 item 1] |
| NG-02 | Generic OAuth/OIDC misconfiguration scanning (redirect URI, PKCE, TLS, entropy) | P | OAuch/OIDF/Nuclei [CA §4.3 item 2] |
| NG-03 | JWT forgery / attack fuzzing (`alg:none`, weak secrets, JWK injection) | P | [CA §4.3 item 3] |
| NG-04 | SSF/CAEP protocol-conformance testing (stream CRUD, SET validity). RG consumes conformance results as preconditions only | P | OIDF suite [CA §4.3 item 4]; SV-038/039 are interop *preconditions* |
| NG-05 | Generic cookie-flag and session-fixation scanning | P | ZAP [CA §4.3 item 5] |
| NG-06 | A stand-alone "revoke, wait 5 s, probe once" feature. It exists only as the degenerate probe schedule of length 1; OAuch results are cross-referenced | P | [CA §4.3 item 6] |
| NG-07 | Stealth, evasion or anti-detection (UA spoofing presets, source-IP rotation, WAF bypass), denial-of-service, load/benchmark testing of third-party services | P | Vendor ToS [OK §(d)], [A0 §(d)], [EN §4 "Policy / ToS"]; [TF R-022] |
| NG-08 | Credential attacks: password guessing, phishing, token theft, user enumeration beyond declared identities, post-exploitation | P | Dual-use risk R-022 |
| NG-09 | Schemathesis negative-generation, fuzz, coverage or stateful-fuzz phases against a live authorization boundary during temporal probes | P (default-off pre-flight may be reconsidered in RG-P14-001) | [ST U5, U19]; side effects [CA §4.4 "Safe side effects"] |
| NG-10 | Custom cryptography or custom authentication protocols | P | [MP engineering principles] |
| NG-11 | Hosted/multi-tenant service, remote-reachable GUI. The GUI binds to loopback | P (distributed workers are a Phase-14 concept) | [TF §2 Local GUI row] |
| NG-12 | Claiming the *exact* server-side enforcement instant or "the" delay. RG reports bounded observations only | P | [TF R-003]; SV-047 |
| NG-13 | Forking, vendoring or patching Schemathesis; using `schemathesis.engine.*`, `schemathesis.config` internals or CLI internals | P | [RM RM-ST-1, RM-ST-3]; [ST U17] |
| NG-14 | Automatic remediation or modification of the target application/IdP configuration (RG reverts only what it itself changed — see WF-11) | P | Scope of an assessment tool |
| NG-15 | Unattended continuous monitoring of production tenants | M (revisit under RG-P14-001) | [TF §5 "Later"]; R-006 |
| NG-16 | Automating interactive/MFA browser logins; MVP obtains credentials through lab-supported grants or operator-supplied sessions | M | ROPC limits [EN §4]; Keycloak lab uses password grant [KC §1.2] |
| NG-17 | Provider-specific claims for Entra/Okta/Auth0 "verified in a tenant" until an operator tenant run exists; their baselines are documentation-derived and labelled so | M | [EN §0], [OK §(f)], [A0 §(f)] |

## 5. Success criteria

All numeric thresholds are **PROPOSED**: each carries the validation test that confirms or revises it (no performance or accuracy figure is asserted as a fact) [MP performance rule].

| ID | Criterion | Measure / threshold | Verified by | Goals |
|---|---|---|---|---|
| SC-01 | Ground-truth containment | In the virtual-time lab, for each fixture enforcement profile (immediate, cache-TTL step, local-JWT-until-`exp`, replica lag, flapping), ≥ 1 000 seeded runs per profile: the true enforcement time lies inside the reported bounds in 100 % of runs that are not `INCONCLUSIVE` | Model tests RG-P12-002 + datasets RG-P09-005 | 01, 06 |
| SC-02 | No hidden slack | Reported interval width = (probe spacing at the bracketing probes) + (anchor uncertainty) + (clock uncertainty), algebraically, in 100 % of lab runs | RG-P08-004 acceptance tests | 01 |
| SC-03 | Classification correctness | For every fixture in the expected-outcome dataset: label **and** profile equal the expected values (100 %). Zero `VULN` for the local-JWT-until-`exp` fixture under profile `protocol` | RG-P09-005, RG-P08-006 | 02 |
| SC-04 | No inference from 200 | Mutation suite (target answers 200 with login page / wrong body / identical body for any token; 3xx to login): 0 runs reach confirmed access; each ends in failed controls → `INCONCLUSIVE` | RG-P05-006/-007 tests | 04 |
| SC-05 | Reproducibility | 100 repetitions of one scenario+fixture+seed on the virtual clock yield identical normalised evidence (excluding declared volatile fields) and identical classification; on Keycloak lab ≥ 20 repetitions per MVP scenario yield the same class with overlapping intervals | RG-P05-013, RG-P12 reproducibility suite | 05, 06 |
| SC-06 | Scope safety | Adversarial scope suite (redirect chains, schema-provided server URLs, DNS rebinding, IP-literal/userinfo URL tricks, alternate ports): 0 requests reach an out-of-scope canary listener | RG-P11-002; threat TM-01…TM-04 | 10 |
| SC-07 | Secret hygiene | Canary secrets (tokens, passwords, admin credentials, cookies, incl. base64/URL-encoded forms) occur 0 times in logs, default-redacted exports, reports, reproduction commands, crash output and GUI HTML | RG-P11-001, RG-P03-004 | 10 |
| SC-08 | Dependency isolation | import-linter: 0 modules outside `rg_stbridge` import `schemathesis`/`hypothesis`/`pytest`; ISO-1…ISO-10 pass on the pinned version | [ST §9]; RG-P12-006 | 09 |
| SC-09 | Mutation safety | 100 % of mutating probes and administrative revocation actions in lab runs have a matching scope entry and an audit-log record; an out-of-scope action is refused before any network call | RG-P11-002, RG-P06-001 | 10 |
| SC-10 | Provider-claim discipline | 0 adapters declare a capability whose research row is tagged other than V / V-doc / V-src / V-lab; remaining capabilities are declared `assumed` and covered by a falsifying test | [RR §1 rule]; RG-P04-001 | 13 |
| SC-11 | Scenario coverage | All 15 mandatory scenarios have a Phase-07 spec containing normal-vs-vulnerable behaviour, preconditions, procedure, expected evidence, false-positive risks, independent validation; the MVP gate subset (§7) passes in the lab | RG-P07-002/-003/-004 | 07 |
| SC-12 | Report completeness | 100 % of reports validate against the report schema and contain: outcome class, profile, bounded interval with uncertainty, control results, assumptions, and per-statement tags {observed, calculated, assumed, hypothesised} | RG-P08-011 | 05 |
| SC-13 | Cleanup integrity | With fault injection (`kill -9` in each experiment state), 0 synthetic identities/sessions remain after recovery per the restoration ledger, or the report lists each residual explicitly | RG-P11-005, RG-P06-010 | 10 |
| SC-14 | Platform parity | MVP CLI suite passes on Windows and Linux CI runners; macOS best-effort, results reported | RG-P12 platform suite | 11 |
| SC-15 | Traceability | Every requirement maps to ≥ 1 test; every differentiator D-1…D-8 has ≥ 1 requirement, one architecture element, one test and one report field | `tools/specgate.py`; RG-P12-001 | 14 |
| SC-16 | Performance proposals validated | Each proposed figure (e.g. p95 send-time error ≤ 25 ms at ≤ 50 concurrent probes, [TF §10]) is either confirmed by its benchmark or revised with a recorded rationale | RG-P12-004 | 01 |

## 6. Differentiators and where each is realised

Package areas follow [ST §5.1]. IDs D-1…D-8 are the master-prompt differentiators; "CA-D#" refers to the evidence rows D1–D7 in [CA §4.1].

| ID | Differentiator | Evidence basis | Realised in (area → responsibility) |
|---|---|---|---|
| D-1 | **Temporal authorization analysis**: transitions between states, not one-instant checks | CA-D1; no tool outputs an interval [CA §0.1] | `rg_core` time/clock, temporal state model, experiment state machine, scheduler port; `rg_probe` post-revocation schedule + confirmation tail; `rg_lab` virtual time; `app` experiment engine |
| D-2 | **Cross-system enforcement analysis**: do independent services respect the same state change | CA-D5; none found | `rg_core` scenario DSL + cross-target correlation; `rg_probe` per-identity × per-target probing; `rg_stbridge` catalogs for several services; `rg_lab` mock services with distinct enforcement profiles; `app` comparison reports |
| D-3 | **Protocol-aware interpretation**: why a credential may remain usable | CA-D2, CA-D3; [STD §3] | `rg_core` expected-enforcement model, policy profiles, classifier; `rg_idp` capability discovery, token analysis, adapter notes (e.g. Keycloak same-second rule [KC §5.1]) |
| D-4 | **Evidence-backed attack verification**: confirmed continued access vs response anomalies vs inconclusive | [STD SV-001…009]; CA-D3 | `rg_probe` assertions, baseline + negative controls, normalisation; `rg_core` classification; `app` store/evidence |
| D-5 | **Measured uncertainty**: what testing proves, including timing limits | [TF R-003, R-007]; SV-047/048 | `rg_core` clock alignment, exposure-interval computation, confidence; `rg_probe` send/receive timestamping; `app` report wording rules |
| D-6 | **Reproducible experiments**: same conditions across versions/configs/providers | CA-D7; [CA §3 R10 note: Schemathesis determinism covers generation, not the environment] | `rg_lab` fixtures/datasets/fault + clock injection; `rg_core` scenario DSL; `rg_probe` replay; `app` run manifests (versions, seeds, settings), store, historical comparison |
| D-7 | **Modular extension**: add providers/transports without changing the temporal core | [MP E]; [ST §5] | `rg_idp` adapter framework + capability model; `rg_probe` transport ports; `rg_core` plugin ports; `app` plugin loader; `rg_stbridge` as the only Schemathesis importer |
| D-8 | **Actionable output**: what remained accessible, under which identity, after which event, caused by what configuration/enforcement behaviour | CA-D2 (mechanism attribution) | `rg_core` mechanism attribution + risk/impact; `rg_idp` provider interpretation; `app` report generation (JSON/Markdown/HTML), reproduction steps |

## 7. Scope: MVP, v1.x, later

Consistent with [TF §5]; the PRD (RG-P01-004) turns each row into FR/NFR requirements and may only change a row through a recorded decision.

| Horizon | Included |
|---|---|
| **MVP** | The 10-step MVP workflow [MP] on the deterministic lab and Keycloak 26.8.x (WF-01…WF-03): mock IdP/services; synthetic identity; baseline + controls; manual-acknowledgment (WF-04 mechanics) and Keycloak-automated revocation (disable user, delete session, user logout, role/group removal, refresh-token revoke); HTTP probes (schema-described via Schemathesis and raw); schedule with confirmation tail; exposure-interval computation; classification against `protocol` + `vendor-doc` profiles; evidence timeline; JSON/Markdown/HTML reports; CLI; GUI = read-only live timeline and results viewer. Refresh-token and session-cookie experiments (WF-06), a two-service/two-identity comparison in the lab (WF-05), interrupted-run cleanup (WF-11). **MVP release-gate scenarios (proposal):** SCN-01, 02, 03, 04, 06 |
| **v1.x** | Entra/Okta/Auth0 adapters on operator-supplied tenants (WF-04 with live admin APIs) with clearance gate; WebSocket probe (WF-07); GraphQL probes; CAEP lab (WF-08, experimental per [TF R-015]); historical regression (WF-09); encrypted evidence; full GUI controls; out-of-process plugin isolation; remaining scenarios SCN-05, 07–15 as release-gated |
| **Later** (RG-P14-001) | Distributed workers, CI/CD integrations, attack graphs, hybrid AD, service-to-service, temporal fuzzing, commercial features, baseline libraries |

## 8. Responsible-use and authorization policy

RevocationGap can disable accounts and kill sessions on live tenants and send repeated requests to real services; it is dual-use [TF R-022]. These rules bind the specification of all later elements (scope: RG-P11-002; GUI/CLI: RG-P10).

| ID | Rule |
|---|---|
| RU-01 | No network action (probe, discovery, admin call, listener bind beyond loopback) occurs unless a **scope file** is loaded, validated and its digest recorded in the experiment manifest. The lab uses a generated scope file; there is no scope-free mode |
| RU-02 | The scope file contains an **authorization statement** (who authorises, for which assets, validity window, engagement reference) and declares targets, tenants, identities, permitted actions (mutating ones listed individually), rate/time limits and SaaS-ToS clearance (field list: `03-PRODUCT/USER-WORKFLOWS.md` §5). RG records the statement; it cannot verify it — see RU-12 |
| RU-03 | Default probes are non-destructive (safe, idempotent methods/queries). Mutating probes and every administrative revocation action require an individual scope entry, an ARMED experiment and an audit-log record [MP C] |
| RU-04 | Administrative actions apply only to identities declared `synthetic` in scope, on the declared tenant. RG never enumerates or modifies other users [TF R-006] |
| RU-05 | **No stealth.** Default `User-Agent` identifies RG (`RevocationGap/<ver> (+authorized-test)`) and a probe-correlation header is sent [ST N6]; an operator may override either only through a scope-declared value, and the override is recorded in evidence. RG ships no evasion capability (NG-07) |
| RU-06 | Every mutating action, scope load, ARM, abort, evidence reveal and export is written to an append-only **audit log** with timestamp, OS user, scope digest and target identifiers |
| RU-07 | SaaS targets require a recorded **clearance acknowledgement** per provider (Okta: un-consented benchmarking forbidden; Auth0: paid subscription and ≥ 7 days' notice for security testing; Entra: MSRC rules of engagement, own tenant, modest volume) [OK §(d); A0 §(d); EN §4; TF R-010]. Defaults are conservative (Okta limiter ≤ 25 % of smallest observed `X-Rate-Limit-Limit`; Auth0 Management API ≤ 2 req/s on Free) [OK §(d); A0 §0 item 9] |
| RU-08 | RG refuses to start when the loaded scope's validity window has expired, and stops an experiment on rate-limit (429/`Retry-After`) rather than continuing to push [STD SV-043; TF R-005] |
| RU-09 | The first screen/command output of any run prints a responsible-use banner naming the scope file, tenant(s) and permitted mutating actions |
| RU-10 | Findings against third parties must follow the target's disclosure/bug-bounty rules; the report template carries a handling-classification field and a "contains raw credentials: no" attestation produced by redaction checks |
| RU-11 | The licence carries no field-of-use restriction (see §9); responsible-use constraints live in this policy, `RESPONSIBLE-USE.md` and the scope gate |
| RU-12 | **Limitation (explicit):** scope and audit controls deter and document misuse; they cannot prevent a determined operator from editing the source or forging an authorization statement. The specification does not claim otherwise |

## 9. Licence recommendation (requires owner decision)

**Recommendation: Apache-2.0** for all RevocationGap distributions. **This is a recommendation, not a decision; the repository owner must confirm, and counsel should review. The analysis below is engineering analysis, not legal advice.**

Dependency licences: Schemathesis MIT [ST header]; Authlib BSD-3-Clause [AL §6]; `joserfc` BSD-3 (3P) [AL §6]; Hypothesis MPL-2.0, transitive via Schemathesis, not vendored [ST CR-6]; `jsonschema-rs` MIT [ST CR-6]; `websockets` BSD-3 [AL §6]; `cryptography` Apache-2.0 OR BSD-3 [AL §6]; `requests` Apache-2.0 (task brief; the research row is tagged U — confirm in RG-P13-003); `pydantic` MIT (task brief; not in research docs, **ASM-CH-02**). Keycloak (Apache-2.0) runs as a separate process and is not distributed [KC §4].

| Option | Fit with dependencies | Patent grant | Copyleft | Adoption friction (red teams, vendors, enterprise) | Assessment |
|---|---|---|---|---|---|
| **Apache-2.0** | Compatible with MIT/BSD-3/Apache deps; MPL-2.0 Hypothesis stays file-level and unmodified (notice obligations only; I) | Explicit grant + termination on litigation | None | Low; widely accepted by corporate legal | **Recommended**: explicit patent grant matters for a security tool adopted by vendors; NOTICE-file duty is manageable (RG-P13-003 licence report) |
| MIT | Compatible | No express grant | None | Lowest | Acceptable alternative; simpler but no patent clause or trademark clause |
| MPL-2.0 | Compatible | Yes | File-level | Low–medium | Would add obligations on RG's own modified files without a corresponding benefit; relevant mainly if the owner wants modifications to core files shared back |
| GPL-3.0 / AGPL-3.0 | One-way compatible with permissive deps (I); MPL-2.0 can be combined under its secondary-license clause (I, **U** until counsel confirms) | Yes | Strong | High: many red-team shops and vendors cannot embed or extend it; plugin ecosystem (D-7) discouraged | Not recommended unless the owner prioritises forcing source reciprocity over adoption |

Conditions: (a) SPDX identifiers in every file, `NOTICE`, third-party licence report generated at release [ST CR-6]; (b) **no field-of-use clause** (e.g. "authorised testing only") — such clauses make a licence non-open-source and are unenforceable against attackers anyway; responsible use is handled by RU-01…RU-12; (c) PyInstaller bundles (Windows/Linux) must carry MPL-2.0 source pointers for Hypothesis; PyInstaller's own licence terms are **U** and verified in RG-P13; (d) publishing vendor-specific baselines links to vendor docs rather than copying text [TF R-019]; (e) the repository currently has no licence decided for the host project [REPO-ASSESSMENT §1]; the file `revocationgap/LICENSE` must be created by the owner when this decision is made.

## 10. Glossary

Definitions are charter-level and consistent with [STD] and [ST]; formal schemas are owned by RG-P02-002…-009. Names marked † are provisional vocabulary pending the cited element.

| Term | Definition |
|---|---|
| **Authorization state change** | Any change that should alter what an identity may do: disable/delete, role or group removal, session termination, token/refresh-token revocation, password change/reset, device-compliance or Conditional Access change, service-identity revocation, reactivation |
| **Revocation event** | A recorded authorization state change with: type, target identity/credential, actor (RG automation, operator, external system), request-sent time, acknowledgment, and anchor time. Includes externally observed events (e.g. CAEP SET) |
| **Acknowledgment** | The system-of-record confirmation that the change was accepted: an admin API 2xx, an operator's explicit confirmation (manual revocation), or a delivered event. It is **not proof of enforcement** (SV-005: 200 from revocation/logout endpoints proves nothing; SV-006: 503 means the token still exists). States: *acknowledged, rejected, unconfirmed, timed-out* † (RG-P06-009) |
| **Anchor (t₀)** | The reference instant for exposure measurement: the acknowledgment time on the best-aligned clock (SV-004), carried with an uncertainty interval spanning request-sent to acknowledgment-received (manual revocation: operator "start" to operator "acknowledged") |
| **Probe** | One timestamped attempt, by a declared identity/credential, to perform a declared protected operation, producing a normalised result and explicit assertions (never HTTP status alone). Kinds: HTTP, refresh grant, introspection, userinfo, WebSocket handshake/message, session-cookie request |
| **Observation categories†** | *confirmed access* (assertions prove the operation succeeded), *confirmed denial* (explicit denial signal per SV-009/SV-049), *indeterminate* (neither: 5xx, 429, malformed, cache-served, control failure) (RG-P02-006) |
| **Control** | A probe whose expected result is known and which validates the measurement. *Positive control*: authorised credential accepted before the event. *Negative control*: garbage/foreign credential of the same shape rejected on the same endpoint. *Sibling control*: a non-revoked credential of the same grant/identity class remains accepted during observation (separates revocation from natural expiry or an outage) (SV-001; [CA §4.4]) |
| **Baseline** | The pre-event verification stage in which controls succeed and the frozen request (same method, URL, headers, body) is established as valid; also, in regression use, a stored historical result set. Context determines which; reports say "pre-event baseline" or "historical baseline" |
| **Last confirmed access** (`t_last_access`) | Send/receive-bracketed time of the latest *confirmed access* observation before the first confirmed denial |
| **First confirmed denial** (`t_first_denial`) | Time of the first *confirmed denial* that is followed by the required confirmation tail of N consecutive confirmed denials (SV-004; R-004); a denial later reversed is flapping, not a first denial |
| **Exposure interval** | The bounded observed interval `[t_last_access − t₀, t_first_denial − t₀]` with anchor and clock uncertainty applied. It brackets the continued-access duration **under the assumption of monotonic enforcement**, which the confirmation tail tests but cannot prove. It is a bound, not "the delay" (NG-12; R-003; SV-047). Never a verdict below ~2 s resolution (SV-047) |
| **Enforcement expectation** | The declared rule for how long access to a given credential type is *permitted* to continue after an event type, under a validation mode and policy profile: e.g. `deny_within(W)`, `permit_until(exp)`, `unspecified`, each with its source (standard §/provider doc/contract) (RG-P02-005; [STD §3]) |
| **Policy profile** | The rule set that supplies enforcement expectations and severity: `protocol`, `asvs-5.0.0-L1|L2|L3`, `nist-aal2|aal3`, `vendor-doc:<provider>`; always recorded with the classification (SV-046) |
| **Validation mode** | How the target decides whether a credential is currently acceptable: local JWT verification; introspection per call; introspection with cache (TTL); server-side session lookup; gateway-plus-backend; userinfo-as-validator; unknown. Determines the applicable row of [STD §3] and [KC §1.7] |
| **Experiment** | One run of one scenario: identities, credentials, targets, probes, revocation event(s), schedule, expectation and profile → evidence → classification. User-visible states are named in `03-PRODUCT/USER-WORKFLOWS.md` §3; the state machine is RG-P02-007 |
| **Scenario** | A reusable, declarative experiment definition (SCN-xx; DSL in RG-P07-001) |
| **Scope file** | The operator-authored authorization declaration that gates every action (RU-01/02) |

## 11. Document set and ID registry

| Prefix | Defined in | Range |
|---|---|---|
| GOAL / NG / SC / D / RU | this charter | GOAL-01…14; NG-01…17; SC-01…16; D-1…D-8; RU-01…12 |
| PER / UC / WF / SCR | `03-PRODUCT/USER-WORKFLOWS.md` | see that file |
| AO / SCN / TV / TM | `03-PRODUCT/THREAT-MODEL.md` | see that file |

## 12. Assumptions and open questions

| ID | Assumption / question | Owner |
|---|---|---|
| ASM-CH-01 | The MVP release-gate subset (SCN-01, 02, 03, 04, 06) is a proposal; the PRD may widen it | RG-P01-004 |
| ASM-CH-02 | `pydantic` is MIT and `requests` Apache-2.0 per the task brief; research tags are U/absent | RG-P13-003 |
| ASM-CH-03 | Licence choice (§9) is unresolved until the owner decides; no `LICENSE` file is created by this element | Owner |
| ASM-CH-04 | The outcome-class labels (`EXPECTED`…`INCONCLUSIVE`) from [STD §4] are adopted verbatim; renaming requires a contract-changelog entry | RG-P02-009 |
| ASM-CH-05 | `NOT_APPLICABLE` is an applicability status, not an outcome class (§2 rule b) | RG-P02-009 |
