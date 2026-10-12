# Okta — revocation / session / token-invalidation behavior and admin API surface

Draft for `docs/02-RESEARCH/providers/OKTA.md` · Access date for every URL: **2026-10-12** · Author: providers-b research agent

**Evidence tags.** (V) read in a vendor page fetched with `web_fetch` this session. (V\*) vendor page whose body is JS-rendered (Okta API reference): `web_fetch` returned only metadata, so the statement comes from the vendor-page excerpt in a `web_search` result for that exact URL. (3P) community / support-forum / SDK / third-party text. (I) inferred. (U) unverified / from memory. Source IDs `[On]` → table at the end of this file (also in SOURCES.md).

**Scope note.** Everything below is about *Okta Workforce Identity* (orgs on `*.okta.com`). Okta Customer Identity = Auth0 → see AUTH0.md.

---

## 0. TL;DR for adapter / test-plan authors

1. Okta **access tokens are JWTs (RS256)**; the org AS hard-codes AT 60 min / ID 60 min / RT 90 d; a custom AS lets you set AT 5 min–24 h and RT lifetime + idle window; ID token is always 60 min (V) [O3].
2. Okta *does* document explicit revocation semantics: revoking a refresh token also kills its access token; revoking only an access token leaves the RT usable; `/revoke` always answers 200 even for junk tokens (V) [O1]. **Revocation is only visible to a caller that asks Okta** (`/introspect` or Okta-validated paths); a resource server validating the JWT locally keeps accepting it until `exp` (V statement that remote validation fails after revoke [O5]; 3P anecdotes of "introspect says inactive but API still accepts" [O34]).
3. Documented auto-revocation triggers: user deactivation/deletion, authorization-server config change/delete, client deactivated/changed/unassigned/deleted (V) [O3]. **Suspension, group-membership removal and password change are NOT listed there** → expected-semantics for those must be *measured* (U).
4. Management API calls that matter: `DELETE /api/v1/users/{userId}/sessions?oauthTokens=true`, `POST /api/v1/users/{id}/lifecycle/{suspend|unsuspend|deactivate}`, `DELETE /api/v1/groups/{groupId}/users/{userId}`, `DELETE /api/v1/sessions/{sessionId}`, `POST /oauth2/v1/global-token-revocation` (scope `okta.universalLogout.manage`). Exact paths/scopes in §2.
5. **Universal Logout (UL)** = Okta → app server-to-server "global token revocation" call (draft-parecki-oauth-global-token-revocation). Okta's own docs say the app is expected to revoke refresh tokens + session cookies, **not** access tokens (V) [O6]. Full UL (ITP policies, generic SAML/OIDC) needs Identity Threat Protection; Adaptive-MFA orgs only get a *manual*, rate-limited console action (V) [O9, O8].
6. **Okta SSF transmitter emits only two CAEP events**: `session-revoked` (from `user.session.end`) and `credential-change` (MFA-factor lifecycle + password reset/update). It does *not* emit anything for suspend/deactivate/group removal (V) [O19]. Okta as SSF **receiver** requires ITP (limited support for Adaptive-MFA orgs) and is push-only (V/V\*) [O20, O21].
7. **No latency number is published** for System Log availability or event hooks; docs only say "near real-time", delays "rare but possible", at-least-once, may be out of order (V) [O12, O23]. Pace probes with headers, never with assumed constants.
8. Free **Integrator Free Plan**: 10 active users, Workflows 5, no Org2Org, no email automation, deactivated after 90 days w/o sign-in, ToS forbids attacking/stressing Okta and un-consented benchmarking (V) [O17, O18]. ITP/SSF-receiver are not in its feature list (V) [O18] → test them only via an ITP trial/paid org (U).

---

## (a) Verified behavior

| # | Topic | Behavior | Tag | Source |
|---|---|---|---|---|
| A1 | AS types | Org AS: issuer `https://{org}`, tokens only for Okta APIs/SSO, content "subject to change"; custom AS (needs API Access Management; included in Integrator Free Plan): issuer `https://{org}/oauth2/{asId}`, `default` AS preconfigured but has no access policy in Free Plan org. Only the org AS can mint tokens with Okta API scopes. | V | [O4] |
| A2 | Lifetimes – org AS | Hard-coded: ID 60 min, access 60 min, refresh 90 days. | V | [O3] |
| A3 | Lifetimes – custom AS | Access token 5 min – 24 h (access policy rule); refresh: lifetime ≥ AT lifetime, idle window ≥ 10 min, max 5 years; ID token not configurable (60 min). Support KB: refresh lifetime 10 min–5 y or unlimited; idle ≤ 1825 days; when RT is rotated the *new RT keeps the old expiry*. | V (+3P KB) | [O3], [O30] |
| A4 | Policy evaluation time | Access-policy evaluation happens at initial authentication only; later policy changes don't affect a flow already past that point (e.g., code exchange). | V | [O3] |
| A5 | RT rotation | Rotation optional per app; default grace period for previous RT = 30 s (settable 0–60 s). A leeway of 0 does not mean instant invalidation — previous token is invalidated after the new one is returned. Reuse detection emits `app.oauth2.token.detect_reuse` / `app.oauth2.as.token.detect_reuse`. | V\* | [O29], [O32] |
| A6 | `/revoke` semantics | Revoking an access token does **not** revoke its refresh token; revoking a refresh token **does** revoke the associated access token. Revoking an invalid/expired/already-revoked token returns **200** (no info leak) → verify revocation by using the token (guide suggests e.g. GET `/users`). Endpoint is `POST {issuer}/v1/revoke` with client authentication (`oauth2/v1/revoke` = org AS; custom AS has `/oauth2/{asId}/v1/revoke`). Guide is flagged **Classic Engine** (OIE users are pointed to SDK sign-out guides). | V | [O1] |
| A7 | After revoke | Token goes on a deny-list; "subsequent remote validation attempts fail for the access token"; if RT invalidated, the corresponding access and ID tokens are invalidated too. | V | [O5] |
| A8 | Local JWT validation | Docs describe local validation (signature, `exp`, `aud`, `iss`) as valid for resource servers; introspection is the "remote" option giving immediate revocation status. Community reports: after `/revoke`, `/introspect` shows `active:false` yet a resource server still accepted the JWT (consistent with local validation). | V (docs) / 3P (reports) | [O5], [O39], [O34] |
| A9 | Implicit/auto revocation | Tokens are implicitly revoked by expiry **or** by a change at the source: *user deactivation or deletion*; AS configuration changed/deleted; client app deactivated/changed/unassigned/deleted. A deactivated client's tokens are "immediately and permanently" invalid; reactivation doesn't resurrect them. | V | [O3] |
| A10 | Suspension, group removal, password change | **Not stated** in the token docs fetched. Suspension doc only says suspended users can't sign in, keep group/app assignments. | V (absence) | [O3], [O24] |
| A11 | Clear user sessions – API | `DELETE /api/v1/users/{userId}/sessions` — revokes all active IdP sessions; optional `oauthTokens` (bool, default false) also revokes OIDC/OAuth **refresh and access** tokens issued to the user; `forgetDevices` (default true; "defaults to false in Classic Engine"). Note: *"doesn't clear the sessions created for web or native apps."* OAuth scope `okta.users.manage`. | V\* | [O2] |
| A12 | Clear user sessions – Admin Console | People → user → More Actions → Clear user sessions. Unticking the UL checkbox still revokes OIDC/OAuth refresh+access tokens and IdP sessions; ticking "Also include logout enabled apps and Okta API tokens" invokes UL. AMFA-only orgs: manual only, "with a rate limit". | V | [O9] |
| A13 | What UL clears | Admin-initiated clear-session: session cookies, refresh tokens, access tokens, plus state/password-reset/account-unlock tokens and SSWS API tokens. **Row "Custom authorization servers" is empty in all four policy columns** (meaning undocumented — see U1). Global-session-policy violation on multi-device users revokes only the violating device's artifacts. | V | [O7] |
| A14 | Sessions API | Only per-session ops exist in the Management API: `GET /api/v1/sessions/{id}` (scope `okta.sessions.read`), `DELETE /api/v1/sessions/{id}` (scope `okta.sessions.manage`, 204), `POST /api/v1/sessions/{id}/lifecycle/refresh`. **No "list sessions for user" endpoint** appears in the Sessions nav. | V\* | [O26] |
| A15 | User-scoped token mgmt | "User OAuth 2.0 Token Management": list/revoke refresh tokens for a user+client at `/api/v1/users/{userId}/clients/{clientId}/tokens[/{tokenId}]`; app-level: `GET/DELETE /api/v1/apps/{appId}/tokens[/{tokenId}]` ("Revoke all application tokens"). Token objects expose `status`, `created`, `expiresAt`, `issuer`, `clientId`, `userId`, `scopes`. User grants (consent) live under the "User Grants" tag. Scopes for these calls not captured (U2). | V\* | [O27], [O28] |
| A16 | User lifecycle | `POST /api/v1/users/{id}/lifecycle/suspend` (ACTIVE→SUSPENDED; suspended users can't sign in; group+app assignments retained), `…/unsuspend`, `…/deactivate?sendEmail=false` (async if `Prefer: respond-async`; `transitioningToStatus` = DEPROVISIONED while pending). Suspend/unsuspend "work with Okta-sourced users, not directory-sourced (AD)". | V\* | [O24] |
| A17 | Group membership removal | `DELETE /api/v1/groups/{groupId}/users/{userId}` (OKTA_GROUP type only; APP_GROUP is import-managed); scope `okta.groups.manage`. Group-rule-managed memberships: manual removal adds the user to the rule's exception list. | V\* (+3P) | [O25] |
| A18 | Global Token Revocation (Okta as receiver) | `POST https://{org}/oauth2/v1/global-token-revocation`, body `{"sub_id":{"format":"opaque","id":"00u…"}}`, scope `okta.universalLogout.manage`; revokes all tokens and sessions of the user incl. SSWS tokens; `iss_sub` for users authenticated via third-party IdP is **Early Access**. | V\* | [O11], [O37] |
| A19 | UL (Okta → app) protocol | Okta POSTs JSON `sub_id` (`email` or `iss_sub`) with `Authorization: Bearer <signed JWT>` (`typ: global-token-revocation+jwt`, claims jti/iss/sub/aud/exp(+5 min)/nbf(−5 min)/iat; signed with the same key as ID tokens/SAML). App should revoke **all refresh tokens + all session cookies**; revoking access tokens is *not required* ("may not be technically possible", e.g., JWT ATs, multi-DC). Status-only response: 204 success, 401/403, 400, 404 (user unknown), 422 (cannot log out). | V | [O6] |
| A20 | UL configuration | Generic SAML/OIDC apps: Logout section → "Okta system or admin initiates logout" → endpoint URL, signed-JWT auth, subject format; app must support GTR + signed JWT; not usable with Federation Broker Mode; Org2Org uses `https://{org}/oauth2/v1/global-token-revocation` with `iss_sub` only. Needs admin permission to manage apps and clear API tokens. | V | [O8] |
| A21 | UL gating | UL with ITP policies (session protection, entity risk) requires Identity Threat Protection; AMFA customers can only run the admin-initiated clear. Okta blog: AMFA customers get UL "with some restrictions". Generic SAML/OIDC UL was described by Auth0 docs as "early access" (needs enabling in the Okta org). | V | [O10], [O9], [O8] |
| A22 | SSF transmitter | Two CAEP events only. `session-revoked` ← `user.session.end`. `credential-change` ← `user.mfa.factor.{activate,deactivate,reset_all,suspend,unsuspend,update}`, `user.account.{reset_password,update_password}`. Max **10** SSF streams/org. SET example shows `iss_sub` subject, `reason_admin`, `event_timestamp` (ms). | V / V\* | [O19], [O22] |
| A23 | SSF receiver | Okta ingests SETs from security-events providers via `POST /api/v1/security-events-providers` (well-known URL or issuer+JWKS), **push only**; SETs appear as `security.events.provider.receive_event` and drive `user.risk.detect` → entity-risk policy → Workflows / session revocation / UL. Feature of ITP, "limited support" for Adaptive-MFA orgs; admin needs super-admin (or custom role "Manage shared signals framework receiver streams"). | V / V\* | [O20], [O21] |
| A24 | System Log API | `GET /api/v1/logs`. **Polling** (no `until`, ascending): returns every event ordered by *persistence time*, may be out of `published` order, infinite pages (`next` link always present). **Bounded** (`since`+`until`): ordered by `published`; "not all events may be present; some may be delayed; rare but possible". Follow `next` links — manual since/until paging may skip/duplicate. 30 s query timeout; 90-day retention; `q` ≤ 40 chars/keyword, ≤ 10 keywords. | V | [O12] |
| A25 | Event types relevant to revocation | `user.session.start`, `user.lifecycle.{activate,create,deactivate,suspend,unsuspend}`, `group.user_membership.{add,remove}`, `application.user_membership.{add,remove}`, `app.oauth2.as.token.revoke` (custom AS) / `app.oauth2.token.revoke[.implicit.{as,client,user}]` (org AS), `app.oauth2.as.token.detect_reuse`, `app.oauth2.as.token.grant.*`, `app.oauth2.as.consent.revoke*`, `user.risk.detect`, `security.events.provider.receive_event`, `policy.auth_reevaluate.{enforce,fail,action}`, `user.session.context.change`. `user.session.end` and `user.account.lock` are confirmed by support/community material (3P). **No System Log event is generated when a session merely expires** (idle/max lifetime); only explicit sign-out or admin revoke. | V (catalog/query guide) / 3P | [O12], [O32], [O33], [O20] |
| A26 | Correlation fields | `authenticationContext.externalSessionId` (same session), `transaction.id` (one operation), `authenticationContext.rootSessionId`; filter by API token: `transaction.detail.requestApiTokenId`. | V | [O12] |
| A27 | Event hooks | At-least-once delivery; network conditions can delay; may arrive batched/out of order → order by `data.events.published`; 25 active+verified hooks/org; ≤300 event types/hook; only `event-hook-eligible` types; one-time GET verification. Receivers with a ~3 s timeout/limited retries are reported by an Okta support engineer (3P). | V / 3P | [O23] |
| A28 | Rate limits – mechanism | Bucketed per endpoint-group and HTTP method; most counters = N req / minute, resets ~60 s but not wall-clock aligned; 429 `E0000047`; headers `X-Rate-Limit-Limit/Remaining/Reset` (reset = UTC epoch **seconds**). Warning/violation events in System Log; org-wide buckets shared by *all* clients. Default: each API token / OAuth service app may use ≤ **50 %** of a bucket. Public metadata endpoints (`/keys`, `.well-known/*`) are not limited. Per-user limit on `/oauth2/v1/token`: **4/s**; admin-console users 40 req/10 s/endpoint. | V | [O13], [O14], [O15], [O16] |
| A29 | Rate limits – numbers | Per-endpoint numbers are **not published on a static page**; only the Admin Console → Reports → Rate Limits dashboard lists them (org/plan/add-on dependent). Docs' own illustrative figure: `/api/v1/logs` 120 req/min (single token then ≤60). A free trial org was observed at 120 RPM for `/api/v1/logs` (3P). Integrator Free Plan has "limited per-minute rate limits". | V / 3P | [O15], [O40], [O18] |
| A30 | Auth for Management API | SSWS API token (inherits creating admin's rights; Okta "doesn't recommend") **or** OAuth 2.0 service app with `private_key_jwt` (only supported client auth for Okta-scoped tokens), client-credentials only, admin role(s) assigned to the app; only Super Admin can grant scopes; scopes are `okta.<resource>.read|manage`. Third-party connector docs: new API-Services apps often **require DPoP by default** (Okta docs for this not fetched). | V\* + 3P | [O31], [O35] |
| A31 | Free-plan facts | Integrator Free Plan: AMFA, Universal Directory, LCM, API Access Mgmt, Workflows (5) included; 10 active users; Org2Org not available; email templates/automation unavailable; no paid support; org deactivates if no sign-in for 90 days; sign-up needs unique business e-mail. | V | [O18] |

---

## (b) Adapter capability matrix

### b1. Revocation / state-change actions (API-driven)

| Action (RevocationGap verb) | Exact call | Privilege | Sync? | Notes |
|---|---|---|---|---|
| Disable user (soft) | `POST /api/v1/users/{id}/lifecycle/suspend` | OAuth `okta.users.manage` (3P connector doc [O35]; exact scope for lifecycle (U2)); admin role User Administrator or higher | sync | Okta-sourced users only; assignments retained; reversible via `…/unsuspend`. |
| Disable user (hard) | `POST /api/v1/users/{id}/lifecycle/deactivate?sendEmail=false` (+`Prefer: respond-async`) | same | async (poll user `status`) | Documented to revoke tokens (A9). Un-doable only via `lifecycle/activate` (status DEPROVISIONED→…; re-provisions). |
| Clear sessions only | `DELETE /api/v1/users/{userId}/sessions?oauthTokens=false&forgetDevices=…` | `okta.users.manage` | sync (204) | Doesn't clear app-created sessions (A11). |
| Clear sessions + tokens | same with `oauthTokens=true` | same | sync | Scope of "tokens" across org-AS vs custom-AS undocumented (U1). |
| Revoke single session | `DELETE /api/v1/sessions/{sessionId}` | `okta.sessions.manage` | sync (204) | Need session id (from System Log `externalSessionId` / login). |
| Revoke user's RTs per client | `DELETE /api/v1/users/{userId}/clients/{clientId}/tokens[/{tokenId}]` | scope U2 | sync | `GET` first (lists RTs w/ status/expiresAt). |
| Revoke token by value | `POST {issuer}/v1/revoke` (`token`, `token_type_hint`) | the **client's own** credentials | sync (always 200) | RT revoke ⇒ AT revoked; AT revoke ⇒ RT survives (A6). Authlib `revoke_token()` fits. |
| Remove group membership | `DELETE /api/v1/groups/{groupId}/users/{userId}` | `okta.groups.manage` + role covering the group (Group Administrator / custom resource set — 3P [O35]: *user lifecycle can succeed while group calls 403 if scope missing*) | sync (204) | OKTA_GROUP only; rule-managed groups → exception list. |
| Remove app assignment | `DELETE /api/v1/apps/{appId}/users/{userId}` (U — not fetched; event `application.user_membership.remove` confirmed) | `okta.apps.manage` (U) | sync | Docs list "client … unassigned" as revoking tokens (A9). |
| Global token revocation | `POST /oauth2/v1/global-token-revocation` `{sub_id:{format:opaque,id}}` | `okta.universalLogout.manage` | sync | Includes SSWS tokens; triggers UL fan-out to configured apps (V\*). |
| Trigger UL fan-out manually | Admin Console clear-sessions with UL box ticked (no public API found for this exact toggle (U3)); or Workflows card "Global Token Revocation" (V\* exists). | Super Admin / "clear user sessions" permission | — | AMFA-only orgs: manual + rate-limited. |
| Reset MFA / password | `POST /api/v1/users/{id}/lifecycle/reset_factors`, `…/reset_password`, `…/expire_password` (V\* Java SDK listing; scopes U) | `okta.users.manage` (U) | sync | Emits CAEP credential-change via SSF transmitter (A22). |
| Change policy/config | Authorization-server policy/rule, app deactivate (`application.lifecycle.deactivate`) | `okta.authorizationServers.manage` / `okta.apps.manage` (U) | sync | Documented implicit revocation triggers (A9). |

### b2. Observation endpoints

| Need | Endpoint | Auth | Notes |
|---|---|---|---|
| Is token still active per IdP? | `POST {issuer}/v1/introspect` (`token`, `token_type_hint`) | client auth (secret, or `private_key_jwt` assertion) | Returns `active`, `scope`, `exp`, `iat`, `sub`, `aud`, `iss`, `jti`, `client_id` (V 3P KB example [O41]). Introspection of RTs supported per docs ("access or refresh token", [O39]). Misc. forum reports of `active:false` for tokens minted by a different AS/client (3P) → always introspect on the *issuing* AS with the issuing/permitted client. |
| Is user object active? | `GET /api/v1/users/{id}` → `status` (`ACTIVE`, `SUSPENDED`, `DEPROVISIONED`, `LOCKED_OUT`, …; `transitioningToStatus` during async) | `okta.users.read` | Poll for async deactivate completion. |
| Session exists? | `GET /api/v1/sessions/{sessionId}` → `status`, `expiresAt`, `lastPasswordVerification`… (404/ACTIVE) | `okta.sessions.read` | No per-user session listing. |
| User's refresh tokens | `GET /api/v1/users/{userId}/clients/{clientId}/tokens` | scope U2 | shows status/expiry. |
| User info with AT | `GET {issuer}/v1/userinfo` | the AT | Does Okta re-check user status here? (U4 — measure.) |
| Events | `GET /api/v1/logs` polling (`since=<t0>` no `until`, follow `next`) | `okta.logs.read` | Filter `target.id eq "<userId>"` + `eventType`. |
| JWKS / discovery | `/oauth2/{as}/v1/keys`, `/.well-known/openid-configuration` | none, not rate-limited | cacheable; keys rotate (45/90-day mark per Okta doc [O3]). |

### b3. Event / telemetry sources and latency

| Source | What | Latency (documented) | Caveat |
|---|---|---|---|
| System Log API (poll) | all revocation-related event types (A25) | "near real-time" (V [O12]) — **no figure** | polling order = persistence time; bounded query may miss late events → use `next` links; re-query the window later. |
| Event Hooks | push of `event-hook-eligible` types | none documented; at-least-once, out of order, batched | public HTTPS endpoint + verification GET needed; 25 hooks cap. |
| Log Streaming (EventBridge/Splunk) | forward-only stream | none documented (3P: "near real time") | forwards only events after creation. |
| SSF transmitter → RevocationGap | CAEP `session-revoked`, `credential-change` | none documented | only 2 event types; max 10 streams; needs `ssf.manage`/`ssf.read` scopes on an app (3P blog [O43]); delivery method (push to a RevocationGap HTTPS endpoint **or** poll) is chosen in the stream config per that blog (3P; not confirmed in Okta docs read) — Okta's *receiver* side is push-only (V\*). |
| Inline hooks | synchronous token/registration/etc. hooks | n/a | **Token Inline Hook can alter minted tokens** (U — not fetched) — keep disabled in lab. |
| Workflows | event-triggered flows; actions include *Clear User Sessions*, *Global Token Revocation*, *Remove User from Group* (V\* cards exist [O36]) | none documented | Free plan: 5 flows. |

---

## (c) Documented enforcement delays / propagation windows (with the doc's caveats)

| Mechanism | Documented window | Doc's caveat | Tag |
|---|---|---|---|
| Access token (JWT) after any change | until `exp` (5 min–24 h custom AS; 60 min org AS) | Only introspection / Okta-validated paths see revocation; resource servers validating locally don't | V [O3, O5] |
| Refresh token after revoke / deactivate | "immediately" implied (deny-list) — no numeric SLA | Rotation grace window: previous RT stays valid up to 30 s (0–60 s configurable) after rotation → a *reuse test inside the grace window will succeed by design* | V\* [O29] |
| UL to downstream apps | **none documented**; "as fast as possible" | "Often not possible to instantaneously revoke… JWT access tokens… multiple independent data centers"; success response means *attempting*, not completed | V [O6] |
| Okta session after `DELETE …/sessions` | immediate (sync 204) — not further qualified | does not touch sessions created by web/native apps | V\* [O2] |
| System Log visibility | not quantified | delayed events "rare but possible"; polling order ≠ published order | V [O12] |
| SSF SET delivery | not quantified | RFC 8417 §5.4 timing caveat: a revocation SET may arrive before/after the re-login that caused it (spec text, general) | V (RFC) [O42] |
| Rate-limit counter reset | ~60 s windows, not wall-clock aligned | `X-Rate-Limit-Reset` authoritative; concurrent-limit headers are only "suggested" | V [O13, O16] |
| Key rotation of signing keys | 45/90-day cadence; keys endpoint may lag a rotation | cache JWKS but refetch on unknown `kid` | V [O3] |
| Custom-AS policy changes | evaluated at authentication, not re-evaluated mid-flow | existing tokens unaffected | V [O3] |

---

## (d) Lab / test feasibility, cost, ToS

* **Org.** Integrator Free Plan org (https://developer.okta.com/signup/): **$0**, 10 active users, 5 Workflows, AMFA + API Access Management included, no Org2Org, no email automation, "limited per-minute rate limits", no paid support, **org deactivates after 90 consecutive days without a user sign-in** (V [O17, O18]). ⇒ One lab org + 3–6 synthetic users is enough for revocation matrices; schedule a periodic sign-in (a RevocationGap "keep-alive") to avoid deactivation.
* **Not available on free:** ITP (Universal Logout policies, SSF receiver, entity-risk) — not in feature list; confirm with Okta sales/trial (U5). Manual UL from Admin Console is available with Adaptive MFA ("limited").
* **ToS clauses that constrain RevocationGap (Integrator Free Plan Agreement §2.4, §6, §11) [O17]:** no abusing/attacking Okta systems "intentionally or unintentionally"; no attempts at unauthorized access; no monitoring availability/performance "for … benchmarking … without Okta's prior written consent"; no use of features not expressly in the plan; Okta may terminate for "excessive burden"; intended for developing/testing *Integrations* for the Integrator's internal business purposes. **(I)** A temporal-authorization tester that only calls documented APIs at low rate against its own org is within the spirit, but timing campaigns that measure "propagation latency" could be read as performance monitoring → keep probes low-rate, document that they test *token validity semantics of your own app*, and obtain written Okta consent before publishing benchmark-style latency numbers about Okta.
* **Rate-limit budget for the lab.** Treat free-org buckets as small: read `X-Rate-Limit-*` on every response; global token-bucket limiter at ≤ 25 % of the smallest observed `Limit`; exponential back-off on 429 using `X-Rate-Limit-Reset` (epoch s, add 1 s jitter); never poll `/api/v1/logs` faster than once per ~5 s (limit may be as low as 120/min, single token ≤ 50 %); `/oauth2/v1/token` per-user 4/s.
* **Auth for admin adapter.** Prefer OAuth service app + `private_key_jwt` + least-privilege admin role. If DPoP is enforced on the service app and RevocationGap lacks a DPoP signer, either disable "Require DPoP" on that lab app (3P note [O35]) or use an SSWS token. SSWS tokens expire after 30 days idle and die with their creating admin (3P).
* **Classic vs OIE.** Docs fetched mix both; flag adapter capability `engine: classic|oie` (detectable via `GET /.well-known/okta-organization` (U) or feature probes) because `forgetDevices` default, revoke-guide applicability, ITP/SSF/UL are OIE-centric (V pieces above).

---

## (e) Pitfalls producing false positives / false negatives

1. **200 from `/revoke` proves nothing** (always 200) → must confirm by introspection *and* by calling the protected resource (V [O1]).
2. **Local-JWT resource servers** will accept a revoked AT until `exp`; flag as *documented enforcement delay* when the RS validates locally, as *defect* only if the RS claims introspection/phantom-token (V [O5], 3P [O34]).
3. **Rotation grace window (default 30 s).** Replaying an old RT <30 s after rotation succeeds legitimately; replay after >grace should fail and trigger reuse-detection (which may revoke the whole family → contaminating later probes) (V\* [O29]).
4. **Introspect on the wrong AS/client → `active:false` false negatives** (3P reports). Introspect at the issuer, with an allowed client.
5. **`oauthTokens=true` scope ambiguity** (custom vs org AS) — U1; an observed survivor of `DELETE /sessions?oauthTokens=true` may be a *documentation gap*, not a bug → classify "needs verification".
6. **Sessions "created for web or native apps" survive** `DELETE …/sessions` (V\* [O2]); the app's own cookie session is outside Okta's reach (UL / back-channel needed) (V [O6]).
7. **Event-hook / System Log ordering**: don't derive "revocation took N s" from `published` order alone; use `transaction.id` and your own monotonic send timestamp (V [O12], [O23]).
8. **No log for natural session expiry** (3P [O33]) → absence of `user.session.end` doesn't mean a session survived.
9. **Group claim staleness**: group membership changes are not listed as revocation triggers (A10) → AT/ID `groups` claims stay stale until next issuance; RT exchange re-evaluates (U6 — measure).
10. **Admin role vs scope**: OAuth scope present but admin role/resource-set lacking → 403 that looks like "feature unavailable" (3P [O35]); record the role assignment in the adapter config.
11. **Rate-limit contamination**: other tests in the same org share buckets; a 429 during a probe window invalidates the timing sample (V [O13]).
12. **Free-plan side effects**: org deactivates after 90 idle days; 10-user cap means user re-creation churn (deleted users must be deactivated first) — avoid "delete user" as the default revocation verb (V [O18]).
13. **`user.lifecycle.suspend` produces no SSF event**; a CAEP-driven oracle will see *nothing* for suspend/deactivate/group changes → never treat SSF silence as "not revoked" (V [O19]).
14. **UL "204" ≠ completed revocation** (V [O6]); verify downstream.

---

## (f) Open uncertainties (all need empirical lab confirmation or vendor clarification)

| ID | Question | Why it matters | Suggested resolution |
|---|---|---|---|
| U1 | Does `DELETE /api/v1/users/{id}/sessions?oauthTokens=true` (and Console "Clear sessions") revoke **custom-authorization-server** tokens? The UL revocations table has a blank row for "Custom authorization servers". | Defines expected-vs-defect for the main Okta revocation verb. | Lab: mint AT+RT from `default` custom AS, call API, introspect + call RS; ask Okta support. |
| U2 | OAuth scopes for lifecycle ops, user-token endpoints, apps `DELETE …/users/{id}` | Adapter privilege manifest must be exact | Read per-operation "OAuth 2.0 scope" lines in the (JS-rendered) API reference or the OpenAPI spec (`okta-management-openapi-spec`, `dist/current/management-minimal.yaml`, 3.4 MB — too large for this session) with a script. |
| U3 | Is there an API equivalent of the Console's "Also include logout enabled apps and Okta API tokens"? | UL orchestration | Check `POST /oauth2/v1/global-token-revocation` (A18) behavior with UL-configured apps. |
| U4 | Do `/userinfo` / introspection reflect *suspension* immediately? | Oracle choice | Lab. |
| U5 | Exact edition/entitlement for ITP, SSF receiver, generic SAML/OIDC UL in an Integrator Free org (OIE vs Classic too). | Whether a free lab can cover those | Ask Okta / trial org. |
| U6 | Does refresh-token exchange after group removal re-evaluate `groups` claim / client assignment? | RBAC-staleness findings | Lab. |
| U7 | UL supported-apps list (OIN) `universal-logout-supported-apps.htm` not fetched | which OIN apps can be used as UL targets | fetch later. |
| U8 | Token Inline Hook / token claim hooks effect on revocation tests | lab hygiene | document "no hooks" precondition. |
| U9 | Whether `X-Rate-Limit-*` values on free orgs match dashboard; per-endpoint numbers for `/users/{id}/sessions`, `/lifecycle/*`, `/groups/{g}/users/{u}` | pacing defaults | read dashboard in lab, store as adapter config. |

---

## Source key (this file)

| ID | URL | Note |
|---|---|---|
| O1 | https://developer.okta.com/docs/guides/revoke-tokens/main/ | fetched (V); Classic-Engine guide |
| O2 | https://developer.okta.com/docs/api/openapi/okta-management/management/tags/usersessions | JS-rendered; text from search excerpt (V\*) |
| O3 | https://developer.okta.com/docs/api/openapi/okta-oauth/guides/overview | fetched; "Last updated October 6, 2026" |
| O4 | https://developer.okta.com/docs/concepts/auth-servers/ | fetched |
| O5 | https://developer.okta.com/docs/concepts/token-lifecycles/ | fetched |
| O6 | https://developer.okta.com/docs/guides/oin-universal-logout-overview/ | fetched |
| O7 | https://help.okta.com/oie/en-us/content/topics/itp/universal-logout-revocations.htm | fetched |
| O8 | https://help.okta.com/oie/en-us/content/topics/itp/config-universal-logout.htm | fetched |
| O9 | https://help.okta.com/oie/en-us/content/topics/apps/universal-logout-amfa.htm | fetched |
| O10 | https://help.okta.com/oie/en-us/content/topics/itp/universal-logout.htm | fetched |
| O11 | https://developer.okta.com/docs/api/openapi/okta-oauth/oauth/globaltokenrevocation | metadata fetched + search excerpt (scope) |
| O12 | https://developer.okta.com/docs/reference/system-log-query/ | fetched |
| O13 | https://developer.okta.com/docs/reference/rate-limits/ | fetched |
| O14 | https://developer.okta.com/docs/reference/rl2-limits/ | fetched |
| O15 | https://developer.okta.com/docs/reference/rl2-token-oauth/ | search excerpt |
| O16 | https://developer.okta.com/docs/reference/rl2-monitor/ | search excerpt |
| O17 | https://developer.okta.com/terms/ | fetched (Integrator Free Plan Subscription Agreement) |
| O18 | https://developer.okta.com/docs/reference/org-defaults/ | fetched |
| O19 | https://developer.okta.com/docs/reference/ssf-transmitter-sets/ | fetched |
| O20 | https://help.okta.com/oie/en-us/content/topics/itp/configure-shared-signal-provider.htm | fetched |
| O21 | https://developer.okta.com/docs/guides/configure-ssf-receiver/main/ | search excerpt |
| O22 | https://developer.okta.com/docs/api/openapi/okta-management/management/tags/ssftransmitter | search excerpt (max 10 streams) |
| O23 | https://developer.okta.com/docs/concepts/event-hooks/ | search excerpt |
| O24 | https://developer.okta.com/docs/api/openapi/okta-management/management/tags/userlifecycle | search excerpt |
| O25 | https://developer.okta.com/docs/api/openapi/okta-management/management/tags/group/other/unassignuserfromgroup ; https://github.com/okta/okta-sdk-python/blob/master/docs/GroupApi.md | search excerpts (DELETE path confirmed by SDK doc) |
| O26 | https://developer.okta.com/docs/api/openapi/okta-management/management/tags/session/other/revokesession | search excerpt |
| O27 | https://developer.okta.com/docs/api/openapi/okta-management/management/tag/UserOAuth/ | search excerpt |
| O28 | https://developer.okta.com/docs/api/openapi/okta-management/management/tags/applicationtokens/other/revokeoauth2tokensforapplication | search excerpt |
| O29 | https://developer.okta.com/docs/guides/refresh-tokens/main/ | search excerpt |
| O30 | https://support.okta.com/help/s/article/refresh-token-expiration-behavior?language=en_US | search excerpt (support KB) |
| O31 | https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/main/ ; https://developer.okta.com/docs/guides/implement-oauth-for-okta/main/ ; https://developer.okta.com/docs/guides/set-up-oauth-api/main/ | search excerpts |
| O32 | https://developer.okta.com/docs/reference/api/event-types/ | fetched (output truncated at 1203 entries; only first part read) |
| O33 | https://support.okta.com/help/s/article/does-system-log-show-when-a-user-s-session-times-out-or-ends?language=en_US | search excerpt (3P-support) |
| O34 | https://devforum.okta.com/t/inactive-token-still-works/13460 ; https://devforum.okta.com/t/revoke-an-user-access-token/25381 | community anecdotes |
| O35 | https://www.elastic.co/docs/reference/kibana/connectors-kibana/okta-action-type | third-party; scopes/roles/DPoP note |
| O36 | https://help.okta.com/wf/en-us/content/topics/workflows/connector-reference/okta/actions/clearusersessions.htm ; https://help.okta.com/wf/en-us/content/topics/workflows/connector-reference/oktaitp/actions/globaltokenrevocation.htm | search excerpts |
| O37 | https://developer.okta.com/docs/api/openapi/okta-oauth/oauth/globaltokenrevocation/globaltokenrevocation | search excerpt |
| O38 | https://pypi.org/project/okta/ | okta SDK 3.4.4, Jul 1 2026, Apache-2.0, py≥3.10 (search excerpt) |
| O39 | https://developer.okta.com/docs/guides/validate-access-tokens/dotnet/main/ | search excerpt: introspection vs local validation |
| O40 | https://devforum.okta.com/t/what-is-ratelimit-for-system-logs-api-v1-logs/35056 | community: free trial `/api/v1/logs` = 120 RPM |
| O41 | https://support.okta.com/help/s/article/validate-tokens-with-public-key-private-key-signed-jwts-using-introspect-and-a-service-application-integration?language=en_US | introspection response example |
| O42 | https://datatracker.ietf.org/doc/rfc8417/ | RFC 8417 §5.4 timing issues |
| O43 | https://andrewdoering.org/blog/2026/authzen-shared-signals-framework-part-2-okta/ | third-party blog (ssf.manage / ssf.read scopes; ITP gating) — not vendor |
