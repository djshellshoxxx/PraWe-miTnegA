# Authlib and complementary Python libraries — facts and adoption recommendations for RevocationGap

Draft for `docs/02-RESEARCH/providers/AUTHLIB-AND-LIBS.md` · Access date for every URL: **2026-10-12** · Author: providers-b research agent

**Evidence tags.** (V) read in a fetched primary page / repository file (PyPI project page, vendor docs, GitHub file via the GitHub API tool). (V\*) PyPI/GitHub excerpt seen only in `web_search` results. (3P) third-party aggregator/blog. (I) inferred. (U) unverified / from memory. Source IDs `[Ln]` → table at the end.

---

## 0. TL;DR — recommendations

| Concern | Adopt | Pin (as of 2026-10-12) | Why (evidence) |
|---|---|---|---|
| OAuth/OIDC client flows, RFC 7009/7662/7523/7636 | **Authlib** | `authlib==1.8.0` (released 2026-08-30) | Current, BSD-3-Clause, Py ≥3.10, active (commit 2026-10-10), has `revoke_token`, `introspect_token`, `refresh_token`, PKCE S256, `client_secret_jwt`/`private_key_jwt`, async client. **No DPoP, no back-channel-logout, no SET/CAEP, no discovery in the bare HTTP clients** (see §2.3). |
| JOSE / JWT verification, JWKS, claims, **clock injection**, SET parsing | **joserfc** (already a hard dep of Authlib ≥1.7) | `joserfc>=1.7.5` (release commit 2026-08-29; exact PyPI latest not confirmed (U)) | `JWTClaimsRegistry(now=<int|callable>, leeway=…)` gives clean clock injection (V source). `authlib.jose` is **deprecated since Authlib 1.7.0**. |
| Unverified token *analysis* (hostile / malformed tokens) | **own ~40-line base64url+json decoder** (stdlib), with joserfc only for *verified* paths | — | Zero dependency surprises when inspecting `alg:none`, odd `typ`, oversized parts; joserfc's `jws.extract_compact()` also works unverified (V source) but pulls registry/alg policy into the analysis path. |
| HTTP client for IdP admin + probes | **httpx2** (Pydantic-stewarded continuation of httpx) | `httpx2==2.13.1` (2026-09-23) | **Authlib 1.8.0 now builds its httpx integration on `httpx2`, not `httpx`** (breaking change, V). Async, strict timeouts, HTTP/2 optional, BSD-3. Schemathesis keeps using `requests` internally (V). |
| OpenAPI/GraphQL fuzzing foundation | **Schemathesis** (mandated) | `schemathesis==4.30.1` | Deps verified from `pyproject.toml` @ tag `v4.30.1`: **`requests>=2.22,<3`**, anyio, click, hypothesis, jsonschema_rs, pyrate-limiter, pytest, PyYAML, rich, werkzeug … — **no httpx/httpx2 runtime dep** (dropped in 4.22.0). |
| WebSocket client | **websockets** if Python floor ≥3.11, else **aiohttp** | `websockets` 17.x (BSD-3, Py ≥3.11); `aiohttp` 3.14.5 (Apache-2.0) | See §4.3 (floor conflict). |
| SET / SSF / CAEP parsing | **write a thin parser on joserfc** | — | No maintained Python SET/SSF library found (searched PyPI/GitHub; only Go `go-secevent` v0.1.0 and an in-repo Java module) (U: absence not proof). Spec rules in §3.4. |
| Persistence | stdlib `sqlite3` (WAL) behind a repository interface | — | Not researched beyond stdlib (U); no new dependency. |
| Scheduling | asyncio/anyio-based own scheduler; **avoid APScheduler 4 alphas** | APScheduler 3.11.3 stable if a library is wanted | APScheduler 4.0 is still pre-release (`4.0.0a6`, Apr-2025) (V\*). Probe timing needs precise, clock-injectable control (I). |
| Evidence encryption | **cryptography** (AES-256-GCM via `AESGCM`; Fernet for convenience) | `cryptography>=45.0.1` floor (Authlib), latest 50.0.x (3P/V\*) | Already a mandatory dependency of Authlib → zero extra footprint; dual-licensed `Apache-2.0 OR BSD-3-Clause` (V\*). |

---

## 1. Authlib — facts

| Fact | Value | Tag | Source |
|---|---|---|---|
| Current version | **1.8.0**, released **2026-08-30** (PyPI "Data verified … Aug 30, 2026"); docs "Release v1.8.0" | V | [L1], [L2] |
| License | **BSD-3-Clause** (PyPI) + optional commercial license ("Authlib offers two licenses") | V | [L1] |
| Python | `>=3.10`; classifiers 3.10–3.14, CPython+PyPy; 1.7.0 dropped 3.9 and added 3.14 | V | [L1], [L3] |
| Hard dependencies | `cryptography>=45.0.1`, `joserfc>=1.6.1` | V | [L4] |
| Release cadence | 1.6.0 (2025-05-23) → 1.8.0 (2026-08-30): **17 releases in ~15 months** (1.6.0–1.6.12, 1.7.0–1.7.2, 1.8.0). Gap 1.7.2 (2026-05-06) → 1.8.0 (2026-08-30) ≈ 4 months; unreleased fixes on `main` (e.g., async `parse_id_token` returning `None`, 2026-10-10). PyPI list shows 1.6.8 on 2026-02-14, changelog says 02-17 (trivial mismatch). | V | [L1], [L3], [L5] |
| Activity / health | Latest commits 2026-10-09/10 by ≥3 distinct committers (maintainer + Éloi Rivard + external PRs). Recent security-relevant fixes: Starlette-client CSRF (1.6.11), unvalidated `redirect_uri` redirects (1.6.10/1.7.1), cleartext-URI `userinfo` loopback bypass (1.8.0), size limits for JWS/JWE decode (1.6.5). deps.dev: ~5k stars, 568 forks (project metadata as of 2026-10-04). **PyPI shows 1 maintainer (`lepture`)** → bus-factor risk. | V / V\* | [L5], [L3], [L6] |
| Async | `authlib.integrations.httpx_client.AsyncOAuth2Client`, `AsyncAssertionClient` (+ sync `OAuth2Client`, `AssertionClient`) — **now powered by `httpx2`** | V | [L3], [L7] |
| Revocation / introspection | `OAuth2Client.revoke_token(url, token=None, token_type_hint=None, body=None, auth=None, headers=None, **kw)` and `introspect_token(...)` — both return the **raw HTTP response** (no parsing, no exception on error status). `revocation_endpoint_auth_method` separate from token-endpoint method. Compliance hooks exist for `revoke_token_request` / `introspect_token_request`. Async client "works the same… add `await`" (signature of async revoke not read: U). | V (source) | [L8], [L7] |
| Refresh | `refresh_token(url, refresh_token, …)`; `ensure_active_token()` auto-refreshes when token is within **`leeway=60` s** of expiry; `update_token` callback | V | [L8] |
| PKCE | `code_challenge_method` — **only `S256`** supported by client; RFC 7636 listed | V | [L8], [L1] |
| Token endpoint auth | default `client_secret_basic` if a secret is given, else `none`; `client_secret_jwt` and `private_key_jwt` via `register_client_auth_method(ClientSecretJWT/PrivateKeyJWT(token_endpoint))` (RFC 7523); 1.7.2 fixed `PrivateKeyJWT` with EC keys (ES256) and allows non-default algs (RS384) | V | [L8], [L7], [L3] |
| OIDC | OpenID Connect Core/Discovery/Dynamic Client Registration (checked in README), RP-Initiated Logout 1.0 added in 1.7.0 (provider-side); framework clients load discovery via `load_server_metadata` (`authlib/integrations/base_client/*`) — the plain `OAuth2Client`/`AsyncOAuth2Client` take explicit endpoint URLs (docs examples) | V / I | [L1], [L3], [L9] |
| Other RFCs | 6749, 6750, 7009, 7523, 7591/7592, 7636, 7662, 8414, 8628, 9068, 9101 (JAR), 9207 (issuer id) | V | [L1] |
| **Not supported / not found** | **DPoP (RFC 9449)** — 0 code-search hits in `authlib/authlib` and `authlib/joserfc`; **OIDC Back-Channel Logout / logout-token validation** — 0 hits for backchannel/back-channel/global-token-revocation; **RFC 8693 token exchange** — absent from the feature list; **SET/CAEP/SSF**; Okta/Auth0/Entra **admin APIs**; browser/session-cookie handling | V (absence in README/changelog/code search) — code search could be incomplete → confirm before relying | [L1], [L3], [L10] |
| `authlib.jose` deprecation | **Deprecated starting 1.7.0** (emits deprecation warnings; 1.7.1 fixed spurious warning on import). Affected modules: `oauth2.rfc7523`, `rfc7591`, `rfc7592`, `rfc9068`, `rfc9101`, `oidc.core` now use joserfc; exceptions are now `joserfc.errors.*`; raw str/bytes keys must become `OctKey/RSAKey/ECKey/OKPKey/KeySet`; `get_jwt_config` split into `resolve_client_private_key`/`get_client_claims`/`get_client_algorithm`. **No removal version published** in the docs read. | V | [L11], [L3] |
| Key behaviors that affect RevocationGap | (1) `_handle_token_hint`: with `token=None` the client revokes/introspects its **stored refresh_token first, else access_token**; (2) `ensure_active_token()` refreshes when the token is within `leeway` (default 60 s) of expiry — the HTTP-client wrappers are expected to call it before each request (wrapper code not read: U), so assume silent auto-refresh; (3) `fetch_token` raises on non-JSON bodies and parses `error` into `OAuth2Error`; (4) revoke/introspect don't raise on 4xx/5xx. | V | [L8] |

---

## 2. Authlib — how RevocationGap should use it (and not)

### 2.1 Use
* Public/confidential **code + PKCE** (S256) and **client_credentials**/**refresh_token** grants against Keycloak/Okta/Auth0/Entra via `AsyncOAuth2Client`.
* `revoke_token()` / `introspect_token()` for RFC 7009/7662 endpoints (Keycloak, Okta `/revoke` `/introspect`, Auth0 `/oauth/revoke`).
* `PrivateKeyJWT` for **Okta service-app admin tokens** (Okta requires `private_key_jwt` for Okta-scoped tokens, V\* in OKTA.md) and for Keycloak/Entra client assertions.
* RFC 8414/OIDC **metadata models** (`AuthorizationServerMetadata`) only for validation; fetch discovery documents yourself (explicit, cacheable, clock-injected).

### 2.2 Wrap, don't expose
* Build a `TokenIssuer` facade: set `leeway=0` and **never let the client auto-refresh** (`ensure_active_token`) while probing — use the client only to *obtain* tokens, then send probes with a plain `httpx2` request carrying the bearer token (so refresh/rotation side-effects remain explicit and recorded).
* Always pass `token=` and `token_type_hint=` explicitly to `revoke_token/introspect_token` (avoid the stored-token default).
* Treat `revoke_token()` responses as **not evidence** (RFC 7009 + Okta always 200).
* Add compliance hooks to log every request/response (redacted) to the evidence store.

### 2.3 Gaps to fill in RevocationGap itself
| Gap | Plan |
|---|---|
| **DPoP (RFC 9449)** — Okta API-Services apps may require it (3P note); Okta/Entra/Keycloak may offer it | Implement a small `DPoPSigner` on joserfc (`typ=dpop+jwt`, `jwk` header, `htm`, `htu`, `iat`, `jti`, `ath`, nonce handling). Or disable the requirement on lab apps. |
| **Back-channel logout receiver** (Auth0, Keycloak, Okta OIDC) | Tiny ASGI endpoint + logout-token validator on joserfc (checks: signature, `iss`, `aud`, `iat` freshness (Auth0 tokens last ~120 s), `events` member `http://schemas.openid.net/event/backchannel-logout`, **no `nonce`**, `sub` or `sid`, `jti` replay cache). Auth0 sample shows exactly these checks (V [A6]). |
| **Global-token-revocation sender/receiver** (Okta UL ↔ Auth0) | Sender: POST + signed JWT `typ=global-token-revocation+jwt` (claims per Okta doc, V [O6]). Receiver stub for lab apps. |
| **SET/CAEP/SSF** | see §3.4 |
| **Token exchange (RFC 8693) / ID-JAG (XAA)** | out of Authlib; custom grant request via `fetch_token(grant_type=…)` with explicit params (U feasibility) or raw httpx2. |
| **Browser flows / SSO-cookie sessions** | Not in scope of Authlib; needs a driven browser (Playwright etc. — not researched here (U)). |

---

## 3. JOSE / JWT / SET libraries

### 3.1 joserfc
* Repo `authlib/joserfc`; BSD-3-Clause (3P stats site); Authlib requires `>=1.6.1`; recent commits 2026-09-13 (KeySet equality fix), 2026-09-09 (compact value size validation), 2026-08-29 release commit **1.7.5**; PyPI aggregator pages lag (they show 1.7.1/1.7.2) so confirm exact latest at pin time (U). Single maintainer (`lepture`) plus occasional contributors (V commits) [L12].
* **Clock injection (V, source `src/joserfc/_rfc7519/claims.py`)**: `JWTClaimsRegistry(now: int | Callable[[], int] | None = None, leeway: int = 0, **claims)`; `exp/nbf/iat` compare against `self.now ± leeway`. This enables deterministic "token expired?" analysis at a *simulated* time and lets the product's `Clock` drive validation.
* **Verified decode**: `jwt.decode(value, key, algorithms=…, registry=…)` **always verifies the signature**; claims are validated *separately* with `JWTClaimsRegistry.validate(claims)` (V source `src/joserfc/jwt.py`). So expiry/audience enforcement is explicit — good for "what would a strict RS do?" simulations.
* **Unverified extraction**: `joserfc.jws.extract_compact(value, payload=None, registry=None)` returns a `CompactSignature` with `.headers()`/payload without signature verification (V source `src/joserfc/jws.py`; behavior w.r.t. `alg:none`, size limits U). Prefer own decoder for hostile input.
* Typed keys (`OctKey/RSAKey/ECKey/OKPKey/KeySet`), explicit `algorithms=` allow-list, `crit` validation, size limits — aligned with RFC 8725 (Authlib migration guide says keys must be explicit types "for security reasons") (V [L11]).
* Supports JWE too (needed for encrypted tokens, e.g., Okta access-token encryption keys event types exist (V [O32])).

### 3.2 PyJWT
* Latest documented: **2.15.1** (stable docs); `jwt.decode(token, options={"verify_signature": False})`, `jwt.decode_complete(...)`, `jwt.get_unverified_header()` exist (V [L13]); `leeway` supported, **no documented `now`/clock parameter** (I — signature is `decode(jwt, key, algorithms, options, verify, detached_payload, audience, subject, issuer, leeway)` (V)). Time compared to `datetime.now(utc)`; clock injection requires freezing time in tests (I).
* Known issue class: **options-dict mutation regression** — reusing one `options` dict across calls where an earlier call set `verify_signature=False` can silently disable claim checks later; reported present since PR #1045 through 2.13.0 (3P Veracode advisory; fix status unknown (U)) [L14]. Another reminder to never share option dicts.
* 2026 hardening changelog: empty HMAC keys rejected, PyJWK `alg` must match JWK alg, `b64=false` strictness (V\* [L13b]).
* License MIT (U — not fetched).
* **Verdict:** don't add; Authlib already ships joserfc; two JOSE stacks double attack surface. Optionally use PyJWT only as an *independent cross-check oracle* in tests (I).

### 3.3 Others considered
* `python-jose` — 3.5.0 (May 2025), MIT, requires `ecdsa/pyasn1/rsa`; historically weak maintenance (3P stats) → **reject** (V\* [L15]).
* `okta-jwt-verifier` 0.5.0 (May 2026, Apache-2.0) — Okta-only convenience; not needed (V\*).

### 3.4 SET / SSF / CAEP parsing — what the spec requires (V)
Implement on joserfc; requirements verified from the specs:
* SET = JWT with explicit typing `typ: secevent+jwt` (SSF "MUST use explicit typing"); `events` claim maps event-type URI → object; **SSF SETs MUST NOT contain `sub` or `exp`**; `iss` MUST match the stream's issuer; `aud` single or array; top-level `sub_id` (RFC 9493 formats: `iss_sub`, `email`, `opaque`, `phone_number`, `complex`, `jwt_id`, …) (V [L16], [L17]).
* CAEP 1.0 events relevant here: `session-revoked`, `token-claims-change`, `credential-change`, `assurance-level-change`, `device-compliance-change`, `session-established`, `session-presented`, `risk-level-change` (V [L17], 3P [L18]).
* **Compatibility trap:** Okta's published SET examples carry `subject` *inside the event* and **no top-level `sub_id`/`txn`** (V [O19]) — SSF 1.0 requires transmitters to include top-level `sub_id`, while CAEP lets legacy events use event-level `subject`. The parser must accept both and normalize.
* Delivery: push RFC 8935, poll RFC 8936; verification event type `…/ssf/event-type/verification` with `state` echo (V [L16]).
* Timing: RFC 8417 §5.4 warns revocation SETs can arrive before/after the re-login that caused them (V [O42]) → the test oracle must correlate by `txn`/timestamps, not arrival order.
* No transmitter/receiver library needed for Auth0 (no SSF, 3P) or Keycloak (SSF transmitter experimental behind `Profile.Feature.SSF`, merged 2026-05-12, targeting 26.7.0 — 3P [L19], keycloak.org post [L20]).

---

## 4. HTTP, WebSocket, scheduling, persistence, crypto

### 4.1 HTTP client — httpx2 vs requests
| | **httpx2 2.13.1** | requests |
|---|---|---|
| Status | Pydantic-stewarded continuation of `httpx` after "limited activity"; first release 2026-05-11/12 (`2.0.0`), **monthly+ releases through 2.13.1 (2026-09-23)**; BSD-3; Py ≥3.10 (classifiers to 3.15); single PyPI maintainer (Kludex) under Pydantic org (V) | ubiquitous, sync-only (3P) |
| Fit | async + sync, strict timeouts, HTTP/2 extra, `ws` extra exists (WebSocket; semantics (U)), deps `httpcore2`, `h11`, `anyio`, `truststore` (OS trust store — good for corporate labs), `idna` | Schemathesis dependency anyway |
| Authlib | **1.8.0 requires httpx2 for `authlib.integrations.httpx_client`** (V); Authlib's `requests` integration still available | yes |
| Schemathesis | supports validating **httpx2 responses** in `Case.validate_response` since 4.25.1 (V\*); its own test extras include `httpx` and `httpx2>=2.12.0` (V) | native |
| Risk | young fork (5 months old); API ≈ httpx (rename `httpx`→`httpx2`) | — |

**Recommendation:** `httpx2` for adapters/probes/WebSocket-free admin calls (async, explicit timeouts, event hooks for evidence capture), `requests` only transitively through Schemathesis. Do **not** depend on the original `httpx` (Authlib dropped it; Schemathesis dropped it). Pin exact versions and a hash-locked lockfile.

### 4.2 Okta/Auth0 SDKs
* `okta` (Python SDK) 3.4.4 (2026-07-01), Apache-2.0, Py ≥3.10, async, generated from the OpenAPI spec, 429 retry built in (V\* [O38]); `okta-client-python` 0.2.0 alpha (V\*). **Recommendation:** do not adopt — adapters need exact headers (`Prefer: respond-async`), raw rate-limit headers and byte-level evidence capture; implement a thin REST adapter and use the SDK only as a reference/oracle. (I)
* Auth0 Python SDK: not evaluated (U); same reasoning.

### 4.3 WebSocket client
| Lib | Version/license | Python | Notes |
|---|---|---|---|
| **websockets** | 17.x (libraries.io shows 17.1; pypistats 17.0.1), **BSD-3-Clause**; PyPI data verified 2026-10-03 | **≥3.11** (classifiers 3.11–3.15) | asyncio + threading (`websockets.sync`) + trio + Sans-I/O; RFC 6455/7692; "100% branch coverage" claim; pre-compiled wheels for Linux/macOS/Windows (V\*) |
| aiohttp | 3.14.5, Apache-2.0 | ≥3.9? (U) | client+server WebSockets built in; large dependency footprint; PyPI attestation 2026-10-11 |
| httpx2[ws] | extra exists (V) | ≥3.10 | semantics/maturity unknown (U) — evaluate before use |
| websocket-client | latest released 2026-08-31, Apache-2.0, "4 - Beta", Py ≥3.10 | ≥3.10 | sync-only, no permessage-deflate |

**Floor conflict:** Authlib/Schemathesis/httpx2 accept 3.10, `websockets` 17 requires 3.11. Python 3.10 reaches end-of-life in **October 2026** (I — from PEP 619, not re-verified) → recommend **Python floor 3.11** (test 3.11–3.14) and **websockets**. If 3.10 must stay: aiohttp.

### 4.4 Scheduling
APScheduler **3.11.3** is the stable line (PyPI attestation 2026-06-28); 4.0 is still alpha (`4.0.0a6`, 2025-04-27) and warns "do NOT use in production" (V\* [L21]). RevocationGap's probe schedule (T+0, T+5 s, T+30 s … with jitter and injected clocks) is simple enough for an `anyio` task group + monotonic `Clock` abstraction (I); persist schedules in SQLite.

### 4.5 Persistence
stdlib `sqlite3` (WAL mode, `PRAGMA user_version` migrations) — not researched further (U); Schemathesis does not impose a DB.

### 4.6 Evidence encryption
`cryptography` — required by Authlib (`>=45.0.1`); license `Apache-2.0 OR BSD-3-Clause`; PyPI data verified 2026-09-30; Snyk reports latest **50.0.2** (3P); changelog shows recent CVE fixes (CVE-2026-39892 buffer handling, CVE-2026-34073 name constraints, CVE-2026-26007 binary-curve checks) → **keep it patched, pin floor `>=` the latest patch** (V\* [L22]). Use `AESGCM` (256-bit key, unique 96-bit nonce per record, AAD = evidence-id+schema version); derive key from passphrase with Scrypt (available in `cryptography.hazmat.primitives.kdf.scrypt`) or from OS keyring; Argon2id availability not confirmed (U). Fernet is acceptable for simple blobs.

---

## 5. Schemathesis ↔ RevocationGap HTTP stack (dependency facts)

Verified from `pyproject.toml` at tag **v4.30.1** (SHA of file `b12ab971…`) [L23]:
* `license = "MIT"`, `requires-python >=3.10`, classifiers 3.10–3.14 (+PyPy).
* Runtime deps: `anyio>=4.5,<5`, `click>=8.0,<9`, `harfile>=0.5.0,<1.0`, `hypothesis>=6.130.12,<7`, `hypothesis_graphql>=0.13.2,<1`, `jsonschema_rs>=0.58.6,<0.59.0`, `pyrate-limiter>=4.0,<5.0`, `pytest>=8.4,<10`, `PyYAML>=5.1,<7.0`, **`requests>=2.22,<3`**, `rich>=13.9.4`, `tomli` (<3.11), `typing-extensions>=4.12.2`, `werkzeug>=0.16.0,<4`.
* `httpx`/`httpx2` appear only in the `tests` extra; changelog 4.22.0 (2026-06-30): "Drop the unnecessary `httpx` dependency" (V\* [L24]); 4.25.1 adds support for validating `httpx2` responses (V\* [L25]).
* Built-in pacing: `pyrate-limiter` dependency; `--rate-limit` option; "automatic 429 retries honoring `Retry-After` with `--rate-limit=auto`" (V\* changelog) → **share one rate-limit budget** between Schemathesis traffic and RevocationGap admin/probe calls (e.g., wrap both in the same `pyrate_limiter.Limiter` instance) so Okta/Auth0 limits (OKTA.md/AUTH0.md) are respected globally.
* Implication: RevocationGap's own client (`httpx2`) and Schemathesis' `requests` produce **two connection pools/cookie jars/proxy configs**; centralize TLS trust, proxy and timeout settings in one config object and pass them to both.

---

## 6. Version/license/maintenance evidence table

| Package | Version (accessed 2026-10-12) | License | Python | Maintenance evidence | Tag |
|---|---|---|---|---|---|
| Authlib | 1.8.0 (2026-08-30) | BSD-3-Clause (+commercial) | ≥3.10 | 17 releases/15 mo; commits 2026-10-10; 1 PyPI maintainer | V |
| joserfc | ≥1.7.5 (release commit 2026-08-29) | BSD-3-Clause (3P) | (U) | commits 2026-09-13; aggregators lag | V / 3P |
| httpx2 | 2.13.1 (2026-09-23) | BSD-3-Clause | ≥3.10 | 16 stable releases (2.0.0→2.13.1) in ~4.5 mo; Pydantic org; 1 PyPI maintainer | V |
| schemathesis | 4.30.1 | MIT | ≥3.10 | tag v4.30.1 file read; frequent releases (475+ releases) | V / 3P |
| requests | (not pinned here) | Apache-2.0 (U) | — | dep of Schemathesis | U |
| PyJWT | 2.15.1 (docs) | MIT (U) | (U) | active; 2026 security hardening; options-mutation advisory | V\* / 3P |
| websockets | 17.x (2026-10 PyPI data) | BSD-3-Clause | ≥3.11 | PyPI verified 2026-10-03 | V\* |
| aiohttp | 3.14.5 (docs) | Apache-2.0 | (U) | PyPI attestation 2026-10-11 | V\* |
| cryptography | 50.0.x (3P); PyPI data verified 2026-09-30 | Apache-2.0 OR BSD-3-Clause | ≥3.9 | recurrent CVE fixes → patch aggressively | V\* / 3P |
| APScheduler | 3.11.3 stable / 4.0 alpha | MIT (U) | — | 4.0 pre-release only | V\* |
| okta (SDK) | 3.4.4 (2026-07-01) | Apache-2.0 | ≥3.10 | Okta-maintained | V\* |

---

## 7. Open uncertainties

| ID | Question | Resolution |
|---|---|---|
| L-U1 | Exact latest PyPI versions of `joserfc` and `websockets` (aggregators disagree) | `pip index versions` at lock time. |
| L-U2 | Whether Authlib `AsyncOAuth2Client` exposes async `revoke_token/introspect_token` with identical signatures; `OAuth2Token.is_expired` clock source | Read `authlib/integrations/httpx_client/oauth2_client.py` / `authlib/oauth2/rfc6749/wrappers.py`. |
| L-U3 | `joserfc.jws.extract_compact` behavior for `alg:none`/oversized input | Read `_rfc7797/compact.py`; fuzz. |
| L-U4 | Python SET/SSF library existence | broader PyPI search (`secevent`, `ssf`, `caep`). |
| L-U5 | `httpx2[ws]` WebSocket API maturity | read httpx2 docs. |
| L-U6 | Authlib removal date for `authlib.jose` | track `docs.authlib.org/en/stable/upgrades/`. |
| L-U7 | PyJWT options-mutation advisory fix version | read advisory/GitHub issue. |
| L-U8 | Python 3.10 EOL date | python.org release schedule. |
| L-U9 | Argon2id availability in `cryptography` | docs. |

---

## Source key (this file)

| ID | URL | Note |
|---|---|---|
| L1 | https://pypi.org/project/Authlib/ | fetched; version, license, features, release list |
| L2 | https://docs.authlib.org/ | fetched; "Release v1.8.0", Py3.10+ |
| L3 | https://docs.authlib.org/en/stable/upgrades/changelog.html | fetched |
| L4 | https://github.com/authlib/authlib (file `pyproject.toml` @ tag `v1.8.0`, via GitHub API tool) | deps |
| L5 | GitHub API `list_commits` authlib/authlib (latest 2026-10-10) and authlib/joserfc | commit activity |
| L6 | https://deps.dev/pypi/authlib | search excerpt (stars/forks as of Oct 4, 2026) |
| L7 | https://docs.authlib.org/en/stable/oauth2/client/http/httpx.html | fetched ("OAuth 2.0 for HTTPX2") |
| L8 | GitHub API file `authlib/oauth2/client.py` @ `main` (sha a0fdaeba…) | read in full |
| L9 | GitHub code search `load_server_metadata` in `authlib/integrations/base_client` | 4 files |
| L10 | GitHub code search "DPoP" in authlib/authlib and authlib/joserfc; "backchannel" in authlib/authlib | 0 hits |
| L11 | https://docs.authlib.org/en/stable/upgrades/jose.html | fetched ("joserfc migration") |
| L12 | https://github.com/authlib/joserfc ; https://pypistats.com/packages/joserfc ; https://socket.dev/pypi/package/joserfc | search excerpts + API commits |
| L13 | https://pyjwt.readthedocs.io/en/stable/api.html ; https://pyjwt.readthedocs.io/en/stable/usage.html | search excerpts |
| L13b | https://github.com/jpadilla/pyjwt/releases | search excerpt |
| L14 | https://sca.analysiscenter.veracode.com/vulnerability-database/security/pyjwtdecode-reintroduces-options-dict/python/sid-212615 | 3P advisory |
| L15 | https://pypistats.org/packages/python-jose ; https://pypi.org/project/okta-jwt-verifier/ | excerpts |
| L16 | https://openid.net/specs/openid-sharedsignals-framework-1_0-final.html ; https://openid.github.io/sharedsignals/openid-sharedsignals-framework-1_0.txt | SSF 1.0 (29 Aug 2025) |
| L17 | https://openid.net/specs/openid-caep-1_0-final.html | CAEP 1.0 |
| L18 | https://sharedsignals.guide/ | 3P guide |
| L19 | https://skycloak.io/blog/keycloak-caep-shared-signals-continuous-access/ | 3P |
| L20 | https://www.keycloak.org/2026/07/experimental-ssf-support | vendor blog (excerpt) |
| L21 | https://pypi.org/project/APScheduler/ | excerpt |
| L22 | https://pypi.org/project/cryptography/ ; https://security.snyk.io/package/pip/cryptography ; https://github.com/pyca/cryptography/blob/main/CHANGELOG.rst | excerpts |
| L23 | GitHub API file `pyproject.toml` @ tag `v4.30.1` of schemathesis/schemathesis | read in full |
| L24 | https://github.com/schemathesis/schemathesis/blob/master/CHANGELOG.md | search excerpt (4.22.0 drops httpx; rate-limit auto) |
| L25 | https://newreleases.io/project/pypi/schemathesis/release/4.25.1 | excerpt (httpx2 response validation) |
| L26 | https://pypi.org/project/httpx2/ ; https://github.com/pydantic/httpx2 | fetched (PyPI) / excerpt |
| L27 | https://pypi.org/project/websockets/ ; https://libraries.io/pypi/websockets ; https://pypi.org/project/aiohttp/ ; https://docs.aiohttp.org/en/stable/ ; https://pypi.org/project/websocket-client/ | excerpts |
