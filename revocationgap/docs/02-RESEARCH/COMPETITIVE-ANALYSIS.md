# RevocationGap — Competitive & Prior-Art Analysis (DRAFT for `docs/02-RESEARCH/COMPETITIVE-ANALYSIS.md`)

- Author role: security-tooling researcher (spec phase; no implementation).
- Date of research: 2026-10-12. All source IDs (`CA-S###`) are in `SOURCES.md`; academic items are annotated in `PRIOR-ART-ACADEMIC.md`.
- Evidence tags: **(V)** verified from a primary source read this session · **(I)** inference from verified facts · **(U)** unverified / memory / secondary only.
- Search limits: tool discovery used `web_search` + repo reading. "No tool does X" always means "none of the tools I read, and none surfaced by my searches, does X" — absence proofs are limited to the code/docs I actually opened (stated per tool).

---

## 0. Headline findings (decision-relevant)

1. **No tool I examined measures a *temporal* enforcement window.** Every tool is either spatial (who can access what: AuthMatrix, Autorize, ZAP Access Control, Burp Compare site maps), protocol-conformance (OIDF suite, OAuch), or attack-signature scanning (VulnAPI, Nuclei). The closest prior art to the core RevocationGap loop is **OAuch's revocation tests** (revoke via RFC 7009, **sleep a fixed 5 s, probe once**, judge pass/fail) and the OIDF suite's code-reuse check (**wait 30 s, probe once, warn**) — single samples with no uncertainty model (V, CA-S015, CA-S013).
2. **The OpenID conformance suite verifies CAEP/SSF *delivery*, not *enforcement*.** (Its only post-event access probe is a single 30-s-delayed protected-resource call after authorization-code reuse, warning-level.) Its SSF module (alpha, "not currently part of certification") has transmitter and receiver plans including a CAEP-Interop plan; the receiver test passes when events are acknowledged (HTTP 202 / poll `ack`) and fails on rejected events / `setErrs`; I found **no module that calls a protected resource after delivering `session-revoked`** (V, CA-S013). The OIDC logout tests check the OP's own SSO session (`prompt=none` must fail after RP-initiated logout) and, on the RP side, the RP's HTTP handling of logout requests — not whether previously issued access tokens stop working (V, CA-S013).
3. **Schemathesis 4.30.1 has no temporal concept.** `use_after_free` is DELETE→404 within one stateful scenario; `ignored_auth` probes only *absent / garbage* credentials; neither can express "this credential was valid at t0, an admin event occurred at t1, is it still valid at t2?" (V, CA-S001/S002). Two Schemathesis behaviours are actively **hazardous** for revocation testing and must be neutralised: reactive **re-authentication on 401 (`retry_on` default `[401]`)** and token caching (`refresh_interval` default 300 s) — both mint a fresh token and would mask a revoked one (V, CA-S001 `auths.py`).
4. **Version skew trap:** master-branch Schemathesis docs list `object_level_authorization` (multi-user BOLA check, `[auth.wfc] peers`) and an offline HTML report; **neither is in the pinned 4.30.1 wheel** (V: absent from the wheel's `checks.py`/`ReportFormat`; present in CHANGELOG "Unreleased"). Specs must be written against the pinned wheel (CA-S001), not master docs.
5. **Timing is right for CAEP enforcement testing:** SSF 1.0/CAEP 1.0/RISC 1.0 became OpenID *Final* in Sept 2025 (V, CA-S025); Keycloak 26.7.0 (July 2026) shipped an **experimental SSF Transmitter** (CAEP session-revoked/credential-change; RISC account-disabled/enabled added in 26.8.0, Oct 2026) but **no receiver** (V, CA-S036); NIST IR 8587 on token protection was finalised 2026-09-15 (V, CA-S039). Open-source SSF **receiver** libraries that *enforce* (SSFgo `revocation`, easyssf) exist, so a reproducible CAEP lab (Keycloak transmitter → open-source receiver → protected API) is buildable (V/I, CA-S029/S031/S036).
6. **Real-world base rate supports the problem:** a 2025 measurement of the top-1M sites found **85 % of JWT-using sites do not invalidate tokens on logout** and 51 % do not terminate prior sessions after password reset (V abstract, CA-S046). Caveat: that study targets consumer *web* logins; transfer to API/IdP-managed tokens is (I).

---

## 1. Per-tool analysis

Legend per tool: **What it is · Status/licence · Verifiably does (relevant) · Verifiably does NOT · Notes for RevocationGap.**

### 1.1 AuthMatrix (SecurityInnovation) — Burp extension
- **What:** Burp extension that tests authorization with tables of **users × roles × requests**; click-to-run; colour-coded results (green no vuln, red possible vuln, blue possible false positive e.g. expired token or wrong regex) (V, CA-S003 README).
- **Status/licence:** README header "v0.8.2"; last commit **2021-06-15**; CHANGES newest entry v0.8 (2018-11-26) → effectively dormant (I). Licence file text is MIT-style (copyright 2016 Mick Ayzenberg, Security Innovation) (V). Needs Burp + **Jython ≥ 2.7.0** (V). BApp-store listing status not checked (U).
- **Does:** per-request expected-role checkboxes; success or failure regex; **Chains** (regex-extract a value from one response into other requests — CSRF tokens, cross-user resource IDs, "authenticating users / session refreshing"); save/load JSON state "for simple regression testing" (V; `JsonState.md`).
- **Does NOT (V by README + grep of `AuthMatrix.py`):** no timers/scheduling, no logout/revocation/IdP logic (grep for `sleep|logout|revoc|websocket` in source: none); no time series; single run per click.
- **Notes:** its Chains can auto-re-authenticate users (V README) — the same *masking* hazard as Burp session rules (I).

### 1.2 Autorize (Burp; Barak Tawily; repo under PortSwigger)
- **What:** Burp extension that watches proxy traffic of a **high-privileged** user, **replays each request** with a low-privileged user's cookie/Authorization header and with no credentials, and compares responses; statuses *Bypassed!* / *Enforced!* / *Is enforced???* (needs manual detector) (V, CA-S004 README).
- **Status/licence:** `ScreenVersion 1.9.4` (BappManifest); last commit **2026-02-24** → maintained (V). **No LICENSE file** in the repo and no licence statement in README (V listing) → licence unspecified (U). Needs Jython (V).
- **Does:** multi-low-priv-user comparison with per-user viewers; enforcement detectors by body/headers/length/regex; interception filters (V).
- **Does NOT (V):** no scheduled/time-based replay (replay happens when traffic passes); no revocation/logout logic (grep: none); heuristics can give false positives/negatives (README "Limitations").
- **Notes:** PortSwigger's own access-control guide points to Autorize (V, CA-S012).

### 1.3 OWASP ZAP (+ Access Control Testing, Authentication Helper, Auth Statistics, Session Fixation rule)
- **What:** OSS web scanner/proxy, Apache-2.0 headers (V sources). Latest stable **2.17.0 (2025-12-15)** (V, CA-S007; `git ls-remote` shows `v2.17.0` newest tag); weekly builds continuing (zaproxy HEAD 2026-10-08; CA-S005).
- **Access Control Testing add-on** (v13, 2026-06-26): per **context/user/site-node** rules *Allowed / Denied / Unknown* with tree inference; "attack" tries every URL as every user and marks cases where rules were not followed; alerts "Improper Authentication" (10101) / "Improper Authorization" (10102); API `scan` action; not permitted in Safe mode (V, CA-S005 help HTML, CA-S006). → *Spatial* differential testing with an expected-policy matrix.
- **Authentication Helper** (Beta; 0.43.0, 2026-10-08): auto-detect login, session handling and verification; new **OAuth2 authentication method** (`client_credentials`, `password`) (V, CA-S005, CA-S008). → obtains tokens; does not revoke them.
- **Authentication Statistics** add-on: "records logged in/out statistics for all contexts in scope" (V) — measures the *scanner's own* login state, not target enforcement.
- **Session Fixation** active rule (beta): solution text recommends server-side destruction on logout, logout destroying previous sessions, absolute timeouts (V Messages.properties) — the rule detects *fixation*, not post-logout validity.
- **Does NOT (V/I):** no IdP admin-API orchestration, no post-event probing schedule, no window estimation, no CAEP. Add-on directory also lists `websocket`, `sse`, `openapi`, `graphql`, `soap`, `grpc` add-ons (V listing) — protocol reach exists, but no revocation semantics found (I). Licence file of the accessControl add-on itself not checked (U).
- **Notes:** ZAP's authentication/verification machinery re-logs-in automatically when it detects a logged-out state (V, CA-S008) → same masking hazard (I).

### 1.4 Burp Suite built-ins relevant to sessions (Pro/Community; PortSwigger)
- **Session handling rules / macros / cookie jar / tracer:** rule actions include "Check session is valid", run macro, post-request macro, invoke extension, set header; validity can be re-checked "after a set number of requests"; on invalid session Burp can run a login macro "to automatically log back in … part way through an automated scan" (V, CA-S009/S010/S011). The **session handling tracer** lists every request handled by rules (V, CA-S010).
- **Compare site maps** (edition limits not verified, U): re-request a site map in a second user's session context and highlight differences; PortSwigger's guide also recommends Autorize (V, CA-S012).
- **Does NOT:** nothing orchestrates IdP changes or records enforcement-window data; session validity checks exist to *restore* the tester's session, which **hides** revocation unless disabled (V doc text, I for implication). Licence: commercial (U, memory).

### 1.5 Schemathesis 4.30.1 (the mandated foundation) — see also §2
- **What:** property-based API tester for OpenAPI/GraphQL; **MIT**; 4.30.1 released 2026-10-09; runtime deps include `hypothesis`, `requests`, `werkzeug`, `pyrate-limiter`, `jsonschema-rs`, `hypothesis-graphql` (V, CA-S001 METADATA, CHANGELOG).
- **Checks present in 4.30.1 (V, `config/_checks.py`, `specs/openapi/checks.py`):** `not_a_server_error`, `status_code_conformance`, `content_type_conformance`, `response_headers_conformance`, `response_schema_conformance`, `positive_data_acceptance`, `negative_data_rejection`, `use_after_free`, `ensure_resource_availability`, `missing_required_header`, `ignored_auth`, `unsupported_method`, `allow_header_conformance`, `max_response_time`.
- **Does NOT (V):** no time/wall-clock model, no IdP integration, no WebSocket (only SSE with ≤20-event/timeout reads), no multi-peer BOLA check in 4.30.1.

### 1.6 OpenID Foundation Conformance Suite (OIDC, FAPI, **SSF/CAEP**, …)
- **What:** Java/Spring suite for certification; MIT; commit `11999aa` 2026-10-09 (V, CA-S013). README scope lists OIDC, FAPI1-Advanced, FAPI2, FAPI-CIBA, eKYC; the tree also has `openid/ssf`, `authzen`, `vci10*`, `vp1*` (V listing).
- **Logout tests (V source):** OP: RP-initiated logout (plain, bad `id_token_hint`, bad `post_logout_redirect_uri`, …), **back-channel logout** (OP must POST a valid `logout_token` to the RP and then `prompt=none` must return an error "as the user has been logged out"), front-channel, session-management. RP side: `OIDCCClientTestBackChannelLogout*` etc. — suite sends logout requests (some invalid: wrong aud/alg/issuer/event) and checks the **RP's response** and post-logout redirect handling (V, CA-S013/S014).
- **Refresh/code tests (V):** `oidcc-refresh-token` (refresh works and is bound to client); `OIDCCAuthCodeReuse` (second use of a code must give `invalid_grant`, else warning). **Closest thing in the suite to a post-event continued-access probe:** `OIDCCAuthCodeReuseAfter30Seconds` (and the FAPI1-Adv / FAPI2 `AttemptReuseAuthorizationCode…` variants, 1 s) — after the code reuse event the suite **waits a fixed 30 s (`WaitFor30Seconds`), calls the protected resource with the originally issued access token once, and raises a *warning* if it still works** (RFC 6749 §4.1.2 "SHOULD revoke"; FAPI2 text: warning does not block certification) (V). Same pattern as OAuch: fixed delay, one sample, no bounds.
- **RFC 7009 / revocation:** grep of `src/main` finds **no revocation-endpoint (RFC 7009) tests** — hits for "revoke/revocation" are the code-reuse checks above, CAEP event-type strings, and credential/status-list (VCI/mdoc) code (V grep); `revocation_endpoint` appears only in unit-test fixtures.
- **SSF/CAEP (V source, 71 files in `openid/ssf`):** transmitter test plan (metadata, stream create/read/delete + negative cases, verification, push/poll, event validation per CAEP 1.0 with required claims/signature/envelope) and receiver test plan (suite emulates a transmitter; receiver must create streams, handle verification, acknowledge events; **CAEP Interop** variant sends `session-revoked`, `credential-change` (all credential types × change types), `device-compliance-change`, optional `risk-level-change`). Plans are labelled **alpha — not part of certification** (V plan `summary`, SSFgo README).
- **What the CAEP receiver test actually checks (V):** each delivered event "must be acknowledged (HTTP 202 on PUSH delivery, 'ack' on POLL delivery)"; failure if the receiver rejects it or reports it via `setErrs`; stream deleted with unacked events fails. It checks **protocol handling**, not that the receiving service then denies access.
- **Does NOT:** probe protected-resource access after a **CAEP/SSF event** or after logout/admin revocation (the only post-event access probe is the code-reuse warning above); sample repeatedly or measure delays; orchestrate real IdP admin actions. Suite is also a lab asset: self-hostable with docker-compose; SSFgo CI runs it daily (V, CA-S029).

### 1.7 OAuch (KU Leuven DistriNet) — OAuth 2.0 / OIDC AS security-BCP analyser
- **What:** .NET tool testing OAuth/OIDC **authorization-server** implementations against RFC 6749/6750/6819/7009/7523/7636/8628, the Security BCP, FAPI, OIDC Core (docs folder lists these) (V, CA-S015); paper: **113 test cases**, 100 public IdPs measured (V snippet, CA-S016). MIT-style licence; last commit 2026-06-13 (V). Web instance at oauch.io (CA-S017).
- **Revocation-relevant tests (V source, `OAuch.Tests/Tests/Revocation`, `TokenEndpoint`, `Concurrency`, `Tokens`):** `CanAccessTokensBeRevoked` (revoke via RFC 7009, **wait 5 s, call the configured test API once**; still-OK ⇒ "SpecificationNotImplemented"), `CanRefreshTokensBeRevoked`, `RefreshRevokesAccess`, `AccessRevokesRefresh`, `IsBoundToClient` (wrong client id must be rejected), `IsClientAuthRequired`, `UsesTokenRotation`, `RefreshTokenRevokedAfterUse`, `InvalidatedRefreshToken`, `RefreshTokenValidAfterMultiExchange`, `TokenTimeout`/`ShortTokenTimeout` ("access tokens time out after at most one hour"), `ConcurrentTokensRevoked` (race-acquired tokens: **user manually revokes the client's authorization, then resumes** — implemented via an `ITimeDelayedTest` resumable-test mechanism) (V).
- **Outcome model:** `SpecificationFullyImplemented` / `SpecificationNotImplemented` / `Skipped` per spec requirement (V).
- **Does NOT (V):** single sample after a fixed 5 s delay; no probe schedule, no window estimate, no uncertainty; revocation only through the RFC 7009 endpoint (no admin disable-user, role removal, password reset, session kill); probes one user-configured test URL (`ApiRequest` with `TestMethod/TestHeaders`), no multi-service comparison; no CAEP/SSF.
- **Notes:** **closest prior art and the main "do not duplicate the basics" reference**; RevocationGap's RFC 7009 sub-scenario should interoperate with (and exceed) OAuch rather than re-implement a weaker version. Its resumable time-delayed test is a useful design precedent.

### 1.8 VulnAPI (CerberAuth) — OSS API DAST
- **What:** Go CLI; `scan curl` and `scan openapi`; MIT; commit `f9991d1` 2026-09-26; tags up to `v0.10.0` (V, CA-S018).
- **Scans present in source (V `scan/`):** broken-authentication → authentication bypass + JWT (alg none, blank/weak secret, null signature, no verification, HMAC confusion, JWK/JKU/x5c/x5u injection, kid path-traversal/SQLi, psychic signature, claim fuzzing); misconfiguration (cookies/headers/CORS/method override/TRACE); discovery; GraphQL introspection.
- **Revocation claim vs code:** the vendor blog says VulnAPI "can test whether your API properly rejects revoked or expired tokens" (CA-S019), and docs contain a *"JWT Expired"* vulnerability page (V `docs/.../jwt-expired.mdx`: token accepted after `exp`), but **grep of the Go source finds no revocation/logout/expired-token scan implementation** (V, 0 matches for `revok|logout|expired` in `*.go`). So: documented, not found implemented at that commit (I; could live elsewhere, e.g. a different repo/SaaS — U).
- **Docs also include** a "JWT cross-service relay attack" page (audience confusion, not temporal) (V listing).

### 1.9 Nuclei (+ nuclei-templates) — template scanner
- **What:** Go scanner; MIT; commit `a48a58e` 2026-10-09; latest tag seen `v3.11.1` (V, CA-S020). Protocols in `pkg/protocols`: http, dns, file, network, ssl, **websocket**, whois, headless, javascript, code (V). Input formats include **OpenAPI/Swagger/Burp/raw** (`pkg/input/formats`) (V).
- **Templates (V survey of 2b6fcc2):** OAuth/OIDC items are detection/misconfiguration only — e.g. `oidc-detect`, `oauth2-detect`, `oauth-authorization-server-exposure`, `oidc-signing-alg-none-supported`, `ssrf-via-oauth-misconfig`, token-leak patterns. **No template** for logout, revocation, session invalidation or token-lifetime (file-name search + `logout` grep).
- **Does NOT (I):** has no notion of identities, IdP admin events, probe schedules or window estimation; could be scripted for single probes but is not designed for it.

### 1.10 SSF / CAEP test and sample tooling
| Item | What it is (V) | Tests enforcement? |
|---|---|---|
| **caep.dev (SGNL)** | Free hosted CAEP **transmitter** to test receivers; "register and create streams to SSF receivers", scripts to create a receiver (CA-S027, press release; site itself not readable) ; OIDF WG page lists it as a way "to test your SSF transmitters and receivers" (CA-S026); Jamf tells vendors to use it for validation (CA-S034) | No evidence (U) |
| **SGNL-ai/caep.dev-receiver** | Go libraries `secevent`, `ssfreceiver` (MIT) | No — libraries |
| **IDFoundry/SSFgo** | Go SSF/CAEP/RISC transmitter+receiver, MIT, "API frozen for v1.0, not yet released"; `revocation` package turns events into revoked tokens + `http` middleware; `ssftest` in-process transmitter/receiver for *application* tests; self-run OIDF plans (CA-S029) | Implements enforcement; white-box test helper only |
| **easyssf** | Spring Boot receiver; rejects access tokens of revoked sessions; tested against OIDF receiver plans (CA-S031, snippet) | Implementation, not a black-box tester |
| **duo-labs/sharedsignals + sharedsignals.guide** | Educational Python/Docker transmitter+receiver; OpenAPI 3.0.3 `transmitter_spec` (CA-S030, snippet) | No |
| **Keycloak 26.7/26.8** | Experimental SSF Transmitter (feature `ssf`, per-realm opt-in; push+poll; durable outbox; CAEP session-revoked & credential-change, RISC account-disabled/enabled in 26.8; synthetic-event REST emitter in design doc) — **no receiver** (CA-S036; receiver issue still open per CA-S037 secondary) | n/a |
| **Okta** | Transmitter: CAEP *Session Revoked* + *Credential Change* only; Receiver requires Identity Threat Protection (CA-S032) | n/a |
| **Google Workspace** | SSF receiver in **closed beta**, `session-revoked` only (CA-S035) | n/a |
| **Microsoft Entra** | Not SSF in the docs read: CAE = resource provider returns **401 + claims challenge**, tokens up to 28 h in CAE sessions; vendor test advice is manual ("sign in a user and use the Azure portal to revoke the session") (CA-S033) | Manual only |

### 1.11 Dedicated "token revocation tester" tools
Searches for an OSS "token revocation tester", "OAuth logout tester", "oidc tester" surfaced: OAuch (above), blog how-tos (Burp-Repeater replay after logout, CA-S019 context), GitHub PRs adding revocation-after-logout in individual projects, and the VulnAPI claim. **No other dedicated open-source revocation/continued-access tester found** (I; limited to search coverage). Keycloak's own revocation-endpoint tests (PR #6704 discussion) are product unit/integration tests, not a reusable tool (U, snippet only).

---

## 2. Schemathesis: what its checks and stateful features can and cannot say about temporal revocation

All statements about the *pinned* version are from the 4.30.1 wheel (CA-S001); statements flagged "master" come from CA-S002 only.

### 2.1 Checks relevant to authorization
| Check | What it does (V) | Why it cannot express temporal revocation |
|---|---|---|
| `ignored_auth` | For an operation that declares security and returned 2xx, re-sends **without credentials** and **with an invalid credential** (`SCHEMATHESIS-INVALID-VALUE`, or `Basic`/`Bearer`-syntax-valid junk) per scheme until the operation rejects once; "enforced" = 401/403 or redirect/different path; no verdict when an undeclared explicit `Authorization` header is configured (V `checks.py`, `_auth_retry.py`, `docs/reference/checks.md`) | Probes *never-valid* credentials, not *once-valid-now-revoked* ones; no clock; one-shot per operation (`auth_enforced_operations` memo). Its `_enforces_auth` (401/403/redirect/path-change) is a useful but **too coarse** enforcement-signal model (no `WWW-Authenticate` `insufficient_claims`/`invalid_token` parsing, no 5xx/timeout classes) |
| `use_after_free` | After a **successful DELETE** in a scenario, any later non-DELETE, non-creation-method request on the same resource that returns 2xx/3xx is a failure ("expected 404"); adds a **stale-cache hint** from `Age` / `X-Cache: HIT` (V `checks.py` L1394–1460) | Trigger is a resource DELETE, not an identity/authorization event; expectation fixed to 404 (not 401/403); no waiting/repeat; no concept of *eventual* enforcement. (Lineage: RESTler's use-after-free rule, CA-S041.) |
| `ensure_resource_availability` | After successful POST, a link-followed GET returning **404** is a failure — i.e. a *stale-negative* read-after-create check | Mirror image (visibility lag); shows the same cache-attribution idea; still immediate, single-shot |
| `object_level_authorization` | **Not in 4.30.1** (V: absent from wheel; CHANGELOG "Unreleased"). On master: with `[auth.wfc] peers` ≥ 2, replays an owner's read as other peers and fails if equal body returned (CA-S002) | Spatial BOLA; no time |
| `positive_data_acceptance`, `missing_required_header`, status/schema conformance | Input/response conformance; `positive_data_acceptance` default `expected-statuses` already tolerates 401/403/404/429/5xx | Useful only to make probe requests *valid* so they reach the auth layer; can mask or conflate denial with validation failure |

### 2.2 Stateful testing and links
- The stateful phase **chains operations via OpenAPI Links, inferred producer/consumer relations, `Location` headers, and (GraphQL) the type graph**, generating *random* workflows with Hypothesis; default CLI runs it after examples/coverage/fuzzing; pytest users subclass `schema.as_state_machine()` with `setup/teardown/before_call/after_call` hooks (V, CA-S002 `explanations/stateful.md`, `guides/stateful-testing.md`).
- Stateful checks (`use_after_free`, `ensure_resource_availability`) only run in this phase / state machine (V). There is **no wait/sleep step, scheduler, wall-clock budget per step, or event hook** (grep: `time.sleep` only in rate-limit retry, outage confirmation, transport retry, storage lock, schema wait) (V).
- Reproducibility knobs: `--seed`, `--generation-deterministic`, `--max-time`, `--rate-limit`, `--workers` (V `cli.md`); reports in 4.30.1: JUnit, VCR cassette, **HAR**, NDJSON, JSON, WFC, Allure (V `config/_report.py`). `--baseline` records *known failures* so CI fails only on new ones (V `baseline.md`).
- **Verdict:** it can supply *which operations exist, how to call them validly, how resources link* — it cannot supply *when* or *why a denial happens*.

### 2.3 Authentication machinery — hazards for revocation testing (all V from wheel `auths.py`, `wfc/escalation.py`, docs/guides/auth.md)
| Behaviour | Default | Effect on revocation testing |
|---|---|---|
| Dynamic auth provider token cache (`@schemathesis.auth(refresh_interval=…)`; declarative `[auth.dynamic…]` refetch) | **300 s** | Reuses a token across probes; after expiry silently fetches a *new* one (mask) |
| **Reactive re-auth**: `reauth_and_replay` — if response status ∈ `retry_on` (default `[401]`), invalidate cache, call `get()` again, **replay the request once**; breaker after repeated failures | `retry_on=[401]`; only when explicit auth is attached | A revoked token that gets 401 is **replaced by a fresh token and the replay succeeds**, hiding the revocation. Must set `retry_on=[]` and/or avoid Schemathesis auth providers for the identity under test (inject static headers per `Case.call(headers=…)`) |
| WFC multi-identity `EscalatingAuthProvider` (no `user` set): per-operation identity chosen by walking users **and an anonymous rung on 401/403**; once a 2xx/3xx is seen the identity is **pinned for the run** | on when WFC lists >1 user | Identity binding becomes an emergent property of responses — incompatible with "this exact identity, this exact token". Use `--auth-wfc-user` or explicit headers |
| Auto sign-up (creates an account if sign-up+login ops detected and no credentials supplied) | on (opt-out key `auth.auto-signup` is **unreleased**) | Tool may create accounts on the target — unacceptable for an offensive tester that must control the identity set |
| JWT claim seeding (`auth_jwt.py` decodes Bearer JWT payload **without verifying** to seed `sub`, `tid`, … into the resource pool) | when a Bearer JWT is configured (I) | Handy for filling path params with the identity's own IDs; unverified decode is fine for this purpose |

### 2.4 Extension points for custom checks (V `docs/guides/extending.md`, `checks.py`)
`@schemathesis.check` functions receive `(ctx, response, case)`; **class-based checks** may implement `after_response` and `after_run`; `after_run` is unreliable under `pytest-xdist` (per-worker instances, no aggregation) (V). Built-in stateful checks reach into **private** context APIs (`ctx._find_related`, `ctx._find_parent`, `ctx._recorder`) — not a stable surface for third parties (I).

### 2.5 Version-skew inventory (pinned 4.30.1 vs master docs)
In master docs/CHANGELOG "Unreleased" but **not** in the 4.30.1 wheel: `object_level_authorization` check and `[auth.wfc] peers`; `--report html` (4.30.1 `ReportFormat` has no HTML; a `reporting/html` package exists in the wheel, purpose unverified); `auth.auto-signup` opt-out; `ctx.add_report()`. Specs and tests must reference wheel behaviour (V).

---

## 3. Capability matrix

Cell = **Y**es / **P**artial / **N**o / **U**nknown + source ID suffix (`S###` = `CA-S###`). Column key: **AM** AuthMatrix · **AZ** Autorize · **ZAP** ZAP (+ add-ons) · **BURP** Burp built-ins · **ST** Schemathesis 4.30.1 · **OIDF** OpenID conformance suite · **OAUCH** OAuch · **VAPI** VulnAPI · **NUC** Nuclei · **SSF** SSF/CAEP tooling (caep.dev, SSFgo, easyssf, sharedsignals.guide, Keycloak/Okta senders) · **RG** RevocationGap (proposed). Explanations for every non-trivial cell are in the notes below the table.

| # | Capability | AM | AZ | ZAP | BURP | ST | OIDF | OAUCH | VAPI | NUC | SSF | RG |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 | Multi-identity differential access testing | Y S003 | Y S004 | Y S006 | Y S012 | P S001 | N S013 | N S015 | N S018 | N S021 | N S029 | Y (control only) |
| R2 | Repeated post-event probing over time | N S003 | N S004 | N S005 | N S009 | N S001 | P S013 | P S015 | N S018 | N S020 | N S029 | **Y** |
| R3 | Revocation-event orchestration via IdP admin APIs | N S003 | N S004 | N S005 | N S010 | N S002 | P S013 | P S015 | N S018 | N S021 | P S027 | **Y** |
| R4 | Continued-access window measurement with uncertainty bounds | N S003 | N S004 | N S005 | N S009 | N S001 | N S013 | N S015 | N S018 | N S020 | N S029 | **Y** |
| R5 | Refresh-token reuse/rotation after revocation | N S003 | N S004 | N S005 | N S010 | N S002 | P S013 | **Y** S015 | N S018 | N S021 | N S029 | Y |
| R6a | CAEP/SSF *delivery* & protocol conformance | N S003 | N S004 | N S005 | N S010 | N S030 | **Y** S013 | N S015 | N S018 | N S021 | **Y** S027,S029 | N (reuse OIDF) |
| R6b | CAEP/SSF *enforcement* after delivery (denial at RS/RP, with delay) | N S003 | N S004 | N S005 | N S010 | N S001 | N S013 | N S015 | N S018 | N S021 | P S029,S031 | **Y** |
| R7 | Cross-service enforcement comparison | N S003 | N S004 | N S005 | N S010 | N S002 | N S013 | N S015 | N S018 | N S021 | N S029 | **Y** |
| R8 | WebSocket / persistent-connection checks | N S003 | N S004 | P S005 | U | P S002 | N S013 | N S015 | N S018 | P S020 | N S029 | Y (planned, hard) |
| R9 | Outcome classification vs expected-enforcement policy | P S003 | P S004 | P S006 | N S009 | P S002 | P S013 | P S015 | N S018 | N S021 | P S013 | **Y** |
| R10 | Reproducible deterministic lab | N S003 | N S004 | U | U | P S002 | P S013 | N S015 | U | U | P S029,S030 | **Y** |
| R11 | Historical regression comparison | P S003 | U | U | U | P S002 | U | U | U | U | N S029 | **Y** |
| R12 | Evidence-timeline reporting | N S003 | P S004 | P S005 | P S010 | P S001 | U | P S015 | U | U | U | **Y** |
| R13 | OpenAPI-driven operation discovery / generation | N S003 | N S004 | P S005 | U | **Y** S001 | N S013 | N S015 | Y S018 | P S020 | P S030 | Y (via Schemathesis) |

**Notes (source-backed justification; "(V)" = read; "(I)" = inferred; "(U)" = not verified):**
- **R1.** AM: users×roles×requests matrix (V). AZ: replay as low-priv + unauth (V). ZAP: all URLs × all users with Allowed/Denied/Unknown (V). BURP: Compare site maps (V; edition limits U). **ST: Partial** — 4.30.1 has `ignored_auth` (none/invalid creds) and WFC identity *selection*, not peer differential; the peer-differential `object_level_authorization` exists only on unreleased master (V). VAPI: only unauthenticated/auth-bypass probing (V). **RG: yes but deliberately minimal** (pre-event control that the identity *was* authorized; not a product pillar — §4).
- **R2.** OIDF: single probe 30 s after an authorization-code-reuse event (warning only) (V). OAUCH: one probe after fixed 5 s plus resumable `ITimeDelayedTest` for a manual revoke step (V) → Partial. BURP: validity re-check "after a set number of requests" exists to *restore* the tester's session, no result series (V doc). ZAP `authstats` counts the scanner's own login state (V).
- **R3.** OIDF drives `end_session_endpoint` logout and, as emulated transmitter, sends SETs (V) → Partial. OAUCH calls RFC 7009 endpoint (V); `ConcurrentTokensRevoked` needs the human to revoke (V). SSF: caep.dev hosted transmitter emits events to receivers (press, snippet) → Partial.
- **R5.** OAUCH has six refresh/rotation/revocation tests (V). OIDF: refresh works/bound, code-reuse → invalid_grant and access-token-revoked warning; no revoked-refresh test (V).
- **R6b.** OIDF receiver tests judge ack/HTTP status and `setErrs`, not resource access (V). SSF libs (SSFgo `revocation` middleware + `ssftest`; easyssf) enable *developers* to assert enforcement in-process (V/snippet); that is white-box and language-specific → Partial; no black-box tool found.
- **R7.** VulnAPI's "JWT cross-service relay" is audience confusion, not temporal enforcement comparison (V docs listing).
- **R8.** ZAP has `websocket`/`sse` add-ons (V directory listing; revocation semantics absent — I). ST: SSE reads ≤20 events/timeout; no WebSocket code (V grep). NUC: `websocket` protocol exists; no revocation templates (V). BURP WebSocket support not checked (U).
- **R9.** AM expected-role matrix + regex; AZ enforcement detectors; ZAP access rules; ST per-check `expected-statuses`; OIDF/OAUCH spec-requirement outcomes. None encode *provider-specific documented delay* vs *vulnerability* (V/I). RG's taxonomy is given in the project brief.
- **R10.** ST: `--seed`/`--generation-deterministic` give deterministic *generation*, not a deterministic *environment* (V). OIDF: docker-compose stacks (V listing) and SSFgo runs the suite daily in CI (V). SSF: sharedsignals.guide Dockerized examples (snippet).
- **R11.** AM saves/loads *configuration* state (not results history) (V). ST `--baseline` stores known *failures* (V). Others not examined (U).
- **R12.** AZ keeps original/modified/unauth request-response viewers (V); BURP session-handling tracer (V); ST HAR/VCR/NDJSON in 4.30.1, HTML timeline only on master (V); OAUCH per-test log lines (V). None anchors evidence to an *event time t0*.
- **R13.** ST (V). VAPI `scan openapi` (V). NUC accepts OpenAPI input format (V dir) → Partial (I). ZAP `openapi` add-on present, depth not evaluated (V presence). SSF: OpenAPI 3.0.3 transmitter spec exists (snippet) but no tool consumes it for testing (I) — *Schemathesis could be pointed at it as a lab self-test* (I).

---

## 4. Honest differentiation analysis

### 4.1 Genuinely differentiated (not found in any examined tool)
| # | Capability | Closest prior art | Gap evidence |
|---|---|---|---|
| D1 | **Event-anchored window measurement**: orchestrate state change at *t₀*, probe on a schedule, report (last-allowed, first-denied) with bounds that include orchestration latency and clock/probe-interval uncertainty | OAuch: single probe at *t₀*+5 s (V). SAAT: one revoke-then-check-state audit (CA-S044). LoginPlus: cookie re-test after 24 h / 7 d (V, CA-S046). PBS (CA-S042) for *how* to express staleness as a time-indexed probability | No tool outputs an interval or distribution (V per tool) |
| D2 | **Mechanism attribution** — which layer ended access (JWT `exp`, introspection, session lookup, cache TTL, CAEP/claims challenge, refresh failure) from response signals (`WWW-Authenticate error=…`, 401 vs 403, redirect, body codes, `Age`/`X-Cache`) | Schemathesis' stale-cache hint (V); Entra claims-challenge format (V, CA-S033) | No tool classifies *why* |
| D3 | **Outcome classification against provider-specific expectations** (protocol-expected / documented delay / risky config / vulnerability / needs verification / inconclusive) | OAuch classifies vs *spec* only (V) | "Unexpired JWT usable" is flagged by simple scanners as a defect and by others ignored; none contextualise |
| D4 | **CAEP/SSF end-to-end: event → delivery → *enforcement latency*** | OIDF tests delivery only (V); SSFgo/easyssf are receivers (V) | Verified absence of enforcement probing in `openid/ssf` |
| D5 | **Cross-service comparison** of the same event across APIs/gateways/caches | none | — |
| D6 | **Persistent-connection checks** (WebSocket/SSE/gRPC stream stays open after revocation) | none for revocation | Hard (§4.4) |
| D7 | **Regression of enforcement latency over releases** (distribution drift, not just pass/fail) | Schemathesis baseline = known *failures* only (V) | — |

### 4.2 Overlap with mature tools (reuse / interoperate, do not rebuild)
- Multi-identity authorization matrices (AuthMatrix, Autorize, ZAP Access Control, Burp Compare site maps; Schemathesis master `object_level_authorization`).
- OAuth/OIDC AS misconfiguration and BCP-compliance scanning (OAuch's 113 tests; OIDF OP/RP conformance; Nuclei detection templates).
- RFC 7009 *basic* checks (endpoint supports revocation, client-bound, client auth required, refresh↔access cascade after a 5 s wait) — **OAuch already does these** (V).
- JWT attack suite (alg none, weak secrets, JWK injection …) — VulnAPI and others (V).
- Session fixation / cookie-flag checks — ZAP (V).
- SSF/CAEP **wire-format and stream-management conformance** — OIDF suite (V). RevocationGap should *consume* these as preconditions ("transmitter conformant?") not re-implement them.
- Unauthenticated / invalid-credential enforcement probing — Schemathesis `ignored_auth` (V).

### 4.3 Capabilities to EXCLUDE from RevocationGap scope because they duplicate mature tools
1. Generic authz-matrix / BOLA / IDOR testing (keep only a *pre-event control probe* proving the identity was authorized before the event).
2. Generic OAuth/OIDC flow misconfiguration scanning (redirect URI, PKCE, TLS, entropy, `alg none`…).
3. JWT forgery/attack fuzzing.
4. SSF/CAEP protocol-conformance suites (stream CRUD, SET validity).
5. Generic cookie/session-flag and fixation scanning.
6. Re-implementing a 5-second "revoke then call once" check as its own feature — provide it as the *degenerate case* of the window measurement (probe schedule of length 1), and cross-reference OAuch results.

### 4.4 Hard to implement (risk register)
| Risk | Why it is hard (evidence) |
|---|---|
| Event orchestration per IdP | Different admin APIs, permissions and consistency; e.g., Entra CAE semantics (401+claims challenge, up to 28 h token lifetime) differ from Okta (transmits only 2 CAEP event types) and Keycloak (SSF experimental) (V, CA-S033/S032/S036). Another agent specs provider APIs; this doc only flags the coupling |
| **Non-monotonic enforcement** | Multi-replica/cached enforcement makes "first denial" non-final: access may be denied then allowed again (replica/cache skew). Zanzibar documents at-least-as-fresh/zookie semantics and PBS models `t`-visibility as a *probability*, not a threshold (CA-S040/S042). → report **P(allowed | t)**, require *N consecutive denials* (and a confirmation tail) before declaring "first-denied", surface flapping (I) |
| Probe cost vs. rate limits | Probing every second may hit 429 and itself change behaviour; Schemathesis already retries on 429 with `time.sleep` (V) which distorts timestamps → RG must timestamp at send/receive with a monotonic clock and own pacing (I) |
| Natural expiry vs revocation | Distinguish 401-due-to-`exp` from 401-due-to-revocation: needs token `exp`/`iat` knowledge (JWT) or control probes with a *non-revoked sibling token* from the same grant (I) |
| Safe side effects | Disabling users/revoking sessions is destructive; requires dedicated test tenants and cleanup; probe ops must be safe/idempotent (Schemathesis stateful phase *creates* resources) (V/I) |
| Browser/session-cookie targets | Back-channel logout to RPs, cookie sessions need a browser or cookie-jar client (Burp/ZAP/AuthMatrix handle via proxy); Schemathesis is API-only (V/I) |
| Persistent connections | No WebSocket in Schemathesis; need own async client and per-protocol "connection terminated" semantics (V/I) |
| Real IdP determinism | Keycloak in a lab is controllable (clock, cache SPI); SaaS IdPs (Entra, Okta, Auth0) are not → statistical repetition and bounded claims only (I) |
| Third-party free-text claims | NIST IR 8587 numbers (e.g., ≤1 h tokens) only seen through press summaries — do not hard-code as policy until the report is read (U) |

### 4.5 Practical security value ranking (what to build first, by value ÷ novelty)
1. **Disable-user / revoke-session / revoke-refresh-token → continued API access window on real IdPs** (access tokens, refresh tokens, introspection vs local JWT validation). Direct counter to the high measured prevalence of non-invalidation (CA-S046) and to NIST IR 8587's token-lifetime/revocation focus (CA-S039, U on details).
2. **Role/group removal and password-reset propagation** — stale role claims in unexpired JWTs and sessions surviving reset; (51 % of sites fail to end prior sessions after reset, CA-S046) and the Zanzibar *new-enemy* pattern at API level (CA-S040, I).
3. **Refresh-token behaviour after revoke/rotate/reuse** — interoperate with OAuch for the RFC 9700 basics (RFC 9700 §4.14.2: refresh-token replay detection **MUST** for public clients; revoking refresh tokens on password change/logout is only **MAY**; no access-token revocation mandate) (V, CA-S038) → many "findings" will be *expected semantics*, which is exactly why D3 classification matters.
4. **CAEP end-to-end enforcement** (emerging; needs receiver targets; Keycloak transmitter lab available).
5. **Cross-service comparison** (same user disabled → which of 5 APIs still serve).
6. **Persistent connections** (WebSocket/SSE) — high impact, highest implementation cost.

---

## 5. Implications: what RevocationGap should reuse from Schemathesis vs build itself

### 5.1 Reuse (loose coupling behind an adapter; pin `schemathesis==4.30.1`)
| Reuse | Why / how | Caveat (V unless noted) |
|---|---|---|
| OpenAPI/GraphQL **schema loading + operation model** (`APIOperation`, security-scheme resolution `get_security_parameters`) | Operation discovery, `securitySchemes` → where credentials go (header/query/cookie) | Use public API (`schemathesis.openapi.from_*`, `schema.get_all_operations`, `Case`) not underscore internals (I) |
| **Valid request generation** (positive mode / examples / link-resolved path params) for *probe* requests | Ensures probes reach the authorization layer instead of failing validation; use stateful link/inferred-link data to pick real resource IDs | Probe selection must be *safe* (prefer GET/HEAD; honour `x-` or config allow-list); Schemathesis may create resources in stateful runs |
| **Transport + `Case.call(headers=…)`** single-request execution with explicit credentials | Gives us control per request while keeping serialization correct | **Bypass Schemathesis auth providers for the identity under test**; if used, set `retry_on=[]` and `refresh_interval=None` (hazard, §2.3) |
| **HAR/VCR/NDJSON recorders** as *raw evidence* sinks (4.30.1) | Free, standard formats for request/response evidence | Evidence **timeline** (t₀-relative) and tamper-evident store must be RG's own |
| **Custom checks API** (`@schemathesis.check`, class checks) for *static* enforcement assertions inside a normal `st run` (e.g., "operation accepted an expired/junk token") | Cheap integration for the non-temporal part (precondition checks) | `after_run` unreliable under xdist; stateful-check internals are private |
| Rate limiting (`--rate-limit`, pyrate-limiter), seeds, `--max-time` | Probe pacing & reproducible generation | `time.sleep` on 429 retries distorts timing — RG logs own timestamps |
| Failure/severity vocabulary & dedup-key idea (`Failure._unique_key`) | Consistent finding identity | Re-map to RG's outcome taxonomy |
| WFC auth-document format (optional) as an *input* format for identities | Interop with a published schema (Web Fuzzing Commons) | Needs extensions (refresh tokens, IdP user IDs) — RG-specific superset (I) |

### 5.2 Build in RevocationGap (no Schemathesis equivalent)
Event orchestrator + provider adapters; **probe scheduler** (monotonic clock; geometric-then-bisection cadence; N-consecutive-denial confirmation; stop rules); **window estimator** (interval + flapping/probability output); **enforcement-signal parser** (401/403/redirect/`WWW-Authenticate` error + `claims`, introspection `active:false`, refresh `invalid_grant`, body patterns, cache headers); **expectation-policy engine + outcome classifier**; CAEP lab pieces (transmitter control, receiver target, protected API); **persistent-connection prober** (WebSocket/SSE); **evidence timeline store** and regression comparison of *distributions*; browser/GUI layer; control-probe logic to separate natural expiry from revocation.

### 5.3 Engineering rules that follow from the evidence
1. Treat Schemathesis as a **request-factory and recorder**, not the test driver; the *time axis* lives in RG.
2. **Never let Schemathesis (or ZAP/Burp/AuthMatrix-style) auto-re-auth sit between the probe and the target** for the identity under test; add a CI test asserting `retry_on` behaviour of the pinned wheel (a future Schemathesis upgrade could change defaults).
3. Pin and test against the wheel; maintain a skew list (§2.5) so spec authors do not rely on master docs.
4. Keep OAuch/OIDF results as **imported context** (preconditions, supported-feature flags) rather than rebuilding their checks.

---

## 6. Open questions / unverified items
1. **caep.dev behaviour** (page not readable); whether it can *receive/verify* enforcement — (U). Google RISC / Cross-Account Protection and Auth0 behaviour not fetched (U); the Auth0/Authentik/Keycloak-receiver statements come from secondary blogs (CA-S037) and are not used for any "Yes".
2. **Burp licence/edition limits** for Compare site maps and session rules, Burp WebSocket handling (U).
3. **ZAP accessControl add-on licence file**, and whether its alerts/API expose per-request timestamps (U).
4. **NIST IR 8587 body text** (token-validity numbers, revocation requirements) — only summaries read (U).
5. **VulnAPI** — whether a "JWT expired/revoked" scan exists outside the `main` branch or SaaS (U).
6. **OAuch/OIDF history & timestamped logs** — whether they offer result diffing (U).
7. **OAuch RAID 2022 venue** inferred from a citing reference (V reference text), the paper PDF itself only seen as snippets.
8. **Schemathesis `reauth_and_replay` scope**: conditions (`case._has_explicit_auth`, `retry_on`) read from source; behaviour with every auth configuration style not exercised at runtime (I). A runtime spike against a local API is recommended before spec freeze.
9. **Coverage caveat:** absence claims rely on opened code and web searches; commercial tools (Burp DAST/Enterprise, Invicti, Salt, Traceable etc.) were not examined (U).
