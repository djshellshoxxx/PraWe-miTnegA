# Auth0 — revocation / session / token-invalidation behavior and admin API surface

Draft for `docs/02-RESEARCH/providers/AUTH0.md` · Access date for every URL: **2026-10-12** · Author: providers-b research agent

**Evidence tags.** (V) read in a vendor page fetched with `web_fetch` this session (Auth0 docs were fetched as their `.md` renderings). (V\*) vendor page seen only as a `web_search` excerpt (page not fetched in full). (3P) community / support-center / blog / SDK-doc text. (I) inferred. (U) unverified / from memory. Source IDs `[An]` → table at the end of this file (also in SOURCES.md).

---

## 0. TL;DR for adapter / test-plan authors

1. **Auth0 states that JWT access tokens cannot be revoked before `exp`**; only refresh tokens (and sessions/grants) can (V/3P) [A2, A3]. Default AT lifetime **86 400 s (24 h)**, max 2 592 000 s (30 d), configurable per API (V\*) [A15]. A "still-usable unexpired JWT" is therefore *expected semantics* on Auth0 unless the resource server adds its own check.
2. **No RFC 7662 introspection endpoint** is documented; a community moderator points to an open feature request (3P) [A20]. Observation must be done by: (a) calling the protected API, (b) exercising the refresh-token grant at `/oauth/token`, (c) Management API reads (Enterprise-only for sessions/refresh-tokens), (d) tenant logs.
3. **Revocation surface by plan** (V) [A1, A4, A6, A11]:
   * *Free:* `POST /oauth/revoke` (Authentication API, refresh tokens only), `PATCH /api/v2/users/{id}` `blocked`, grants API (`/api/v2/grants`), device-credentials API, password-change, 1-day log retention, **no** log streams, **no** Sessions API, **no** refresh-token Management API, **no** Back-Channel Logout, **no** role management.
   * *Enterprise:* Sessions API (`/api/v2/sessions`, `/api/v2/users/{id}/sessions`), refresh-token API (`/api/v2/refresh-tokens/{id}`, `/api/v2/users/{id}/refresh-tokens`), OIDC Back-Channel Logout, Private Key JWT client auth, Continuous Session Protection, 30-day logs, load testing (with prior written approval).
4. **Refresh-token DELETEs and session DELETEs via Management API are asynchronous and "eventually consistent"** (V) [A1, A4]; `/oauth/revoke` is documented as immediate (V) [A1]. Session termination does **not** revoke refresh tokens (V) [A4].
5. **Rotation + reuse detection**: reuse of a previously invalidated RT revokes the whole family issued since (V) [A1]; configurable *rotation overlap/leeway* window during which breach detection does not apply (V\*) [A17]; log type `ferrt` records reuse (3P blog) [A22].
6. **Blocking a user (`PATCH /users/{id}` `blocked=true`)**: documented effect is login rejection (`user is blocked`, log type `f`) (V) [A5]. **The docs do not say what happens to existing sessions/tokens/refresh grants** → primary candidate for empirical test (U1).
7. **Universal Logout / Global Token Revocation (Okta Workforce → Auth0)** is supported on **all plans incl. Free** (pricing table) and revokes Auth0 sessions + refresh tokens, optionally fanning out Back-Channel Logout; **access tokens are not revoked** — "user loses access as soon as current AT expires" (V) [A7, A11].
8. **Pen-test / load-test policy:** security testing of Auth0 infrastructure is allowed only for **paid** subscriptions with ≥7 days' written notice; load testing only for **Enterprise** with approval; DoS forbidden; stay within published rate limits (V) [A12, A13]. A Free-tenant RevocationGap lab is **not covered** by the policy's wording → get written clearance / use a paid dev tenant for adversarial campaigns (I).
9. Free **Management API limit is 2 req/s** (burst 2), Authentication API 300/min, `/oauth/token` 30/s, `/userinfo` 5/min per user (V) [A8] — plan serial, paced admin calls.

---

## (a) Verified behavior

| # | Topic | Behavior | Tag | Source |
|---|---|---|---|---|
| A1 | JWT AT revocation | "JWT access tokens cannot be revoked. They are valid until they expire" ; only refresh tokens can be revoked; use short-lived ATs. Access and ID tokens "cannot be revoked in the same way as cookies with session IDs". | V (docs) / V\* (support) | [A3], [A2] |
| A2 | AT lifetime | Per-API "Token Expiration" default 86 400 s, max 2 592 000 s (30 d); min 1 s (support KB); tokens for the `…/mfa` audience limited to 10 min. | V\* / 3P | [A15], [A23] |
| A3 | RT lifetimes | Two optional app-level settings: **maximum** (absolute) lifetime — fixed at issuance, *not* changed by later app-setting edits; **idle (inactivity)** lifetime — renewed on each exchange, reflects current app settings, must be ≤ maximum. Setting a max turns non-expiring RTs into expiring ones at next exchange (irreversible). With rotation the absolute lifetime applies to the whole token family. Actions can override max lifetime at issuance/refresh. | V\* / 3P | [A16], [A16b] |
| A4 | RT rotation & reuse detection | Rotation: every exchange returns a new RT. Reuse of an *invalidated* RT ⇒ all RTs issued since that RT are revoked immediately (user must re-auth). *Rotation Overlap Period* (seconds): within it a new RT is issued and breach detection doesn't apply; only the immediately previous RT may be reused, the second-to-last triggers detection. Log type `ferrt` ("reused refresh token detected"). | V (reuse) / V\* (overlap) / 3P (log type) | [A1], [A17], [A22] |
| A5 | Revoke an RT — Authentication API | "Revoke a refresh token" endpoint (`POST /oauth/revoke` (U path; endpoint named in docs)) — validates client credentials, checks the token was issued to that client, then invalidates it "immediately"; **public clients may call without secret if `token_endpoint_auth_method = none`**. "Each revocation request invalidates all the tokens that have been issued for the same authorization grant." Tenant setting *Refresh Token Revocation Deletes Grant* (off by default for tenants created after 13-Jan-2021): on ⇒ revoking an RT deletes the underlying grant and thus all RTs for that user+app+audience; off ⇒ only that RT (e.g., device unlink). (The two statements overlap ambiguously — see U3.) | V | [A1] |
| A6 | Revoke an RT — Management API | Enterprise-only endpoints: `GET /api/v2/refresh-tokens/{id}`, `DELETE /api/v2/refresh-tokens/{id}`, `GET /api/v2/users/{id}/refresh-tokens`, `DELETE /api/v2/users/{id}/refresh-tokens`; scopes `read:refresh_tokens`, `delete:refresh_tokens`. **DELETEs run asynchronously, eventually consistent** ("not immediately revoked when the command finishes"). RTs issued ≥ 21-Sep-2023 (22-Feb-2024 in US-3) carry `session_id`; older RTs have `null`. Older equivalent: `GET/DELETE /api/v2/device-credentials` (`read:`/`delete:device_credentials`, `type=refresh_token`). | V + 3P (scopes from blog) | [A1], [A18] |
| A7 | Device flow caveat | For device-authorization flow, revoking the RT forces re-authorization only after the *current AT expires* and the app tries the revoked RT. | V | [A1] |
| A8 | Sessions API | Enterprise-only. `GET /api/v2/sessions/{id}` (`read:sessions`), `DELETE /api/v2/sessions/{id}` (`delete:sessions`), `GET /api/v2/users/{id}/sessions` (`read:sessions`), `DELETE /api/v2/users/{id}/sessions` (`delete:sessions`). Session id == `sid` claim of ID/Logout tokens. **Delete session operations are asynchronous and eventually consistent.** "Refresh tokens can remain active after a session has expired or been deleted, or after the user logs out." A separate session-revoke operation that also revokes the session's RTs exists (`POST /api/v2/sessions/{id}/revoke`, path (U); 3P SDK issue/hexdocs). Session deletion triggers Back-Channel Logout via the `session-deleted` initiator. | V (+3P) | [A4], [A18] |
| A9 | Block user | `PATCH /api/v2/users/{id}` `{"blocked": true}` (admin block; no expiry; unblocking via `blocked:false`; password reset via Management API also clears the admin block). A blocked user attempting login is redirected with `error=unauthorized&error_description=user is blocked` and a Failed Login (`f`) log. Brute-force-protection blocks are separate. **No statement about existing sessions, ATs or RTs.** | V | [A5] |
| A10 | Grants API | `GET /api/v2/grants` (filters user_id/client_id/audience; `read:grants`), `DELETE /api/v2/grants/{id}` and `DELETE /api/v2/grants?user_id=…` (`delete:grants`) — "when a grant is revoked, so are all tokens issued in the context of that grant" (concept page). | V\* (API pages, PHP SDK doc) + V (concept) | [A19], [A1] |
| A11 | OIDC Back-Channel Logout | Enterprise-only. Auth0 POSTs a signed **Logout Token** (`iss`, `sub`, `aud`, `iat`, `exp` ≈ iat+120 s, `jti`, `events{"http://schemas.openid.net/event/backchannel-logout":{}}`, `sid`, `trace_id`) to each registered RP URL (must be TLS, reachable from the IdP, validate per OIDC spec; RP should accept only known `sid`s and trusted tenants; Auth0 outbound IPs allow-listable). Requests are queued asynchronously; "during high load there may be a slight delay… handle eventual consistency". Expected RP response 200 (400 on invalid). | V | [A6] |
| A12 | Universal Logout | Auth0 implements Global Token Revocation (draft-parecki-oauth-global-token-revocation) for Okta-Workforce / OIDC / SAML connections: endpoint `https://{domain}/oauth/global-token-revocation/connection/{connectionName}`, `iss_sub` subject, JWT validated with the same key set as the upstream ID tokens/assertions. Effect: terminates all Auth0 sessions of the user, revokes Auth0-issued RTs, optionally triggers BCL. **Latency per doc:** browser apps lose access at next session poll; RT apps "as soon as their current access token expires, ranging from a few seconds up to the maximum access token lifetime". Not for ATs. UL requests visible in tenant logs; log-stream-able. | V | [A7] |
| A13 | Federated session ceiling | Auth0 honors an upstream `session_expiry` claim (IPSIE SL1 profile) on Okta/OIDC enterprise connections: session lifetime ceiling = min(IdP claim, tenant absolute expiry, Action-set expiry). | V\* | [A26] |
| A14 | RBAC at token issuance | With RBAC enabled for an API, `scope` in the AT = intersection of requested and the user's assigned permissions at issuance; optional `permissions` claim; Actions modifying scopes override RBAC. Docs read do **not** say issued tokens are updated when roles/permissions change (I: they aren't — JWT is immutable; re-issuance via refresh/login re-evaluates). Role *management* is not on the Free plan. | V\* + I | [A21], [A11] |
| A15 | Introspection | No documented RFC 7662 endpoint; Auth0 community thread asks why Auth0 doesn't provide one and a moderator points to an open feature request. | 3P | [A20] |
| A16 | Token vault / XAA | Cross App Access (XAA, ID-JAG) is **Early Access** for Enterprise / B2B Pro / B2B Essential; ID-JAG exchanges at `/oauth/token` rate-limited to ≤50 % of tenant Authentication-API limit (Free table lists 5/s); Auth0 can be Resource-App and/or Requesting-App with Okta as IdP. Revocation semantics of XAA tokens not documented in the page read. | V | [A14], [A8] |
| A17 | Logs | Tenant logs are "not real-time… you may see some delays"; retention Starter/Free 1 d, B2C/B2B Essentials 5 d, Professional 10 d, Enterprise 30 d. `GET /api/v2/logs`: ≤100/request; **by checkpoint** (`from`+`take`, ordered by `log_id`, unbounded, follow `Link: next`; ordering by `log_id` deliberately avoids skipping due to "Auth0 system delays") or **by search** (`q`, `page`, `per_page`, ≤1 000 results). Also `/api/v2/logs/{id}`, `/api/v2/users/{id}/logs`. Mgmt-API calls can be correlated by sending `X-Correlation-ID` (first 64 chars logged). Log streams (`/api/v2/log-streams`: statuses active/paused/suspended) not on Free; Essentials 1, Professional/Enterprise 2 (3 on request); non-2xx webhook responses can suspend a stream (3P). | V (+3P) | [A9], [A10], [A11], [A27] |
| A18 | Rate limits (Free) | Authentication API 300 burst / 300 per min; `/oauth/token` 30/s; `/userinfo` 10 burst, 5/min per user; `/.well-known/jwks.json` 20/s; `/oidc/register` 5/s; ID-JAG exchange 5/s; **Management API 2 burst / 2 per second**; per-endpoint overrides (e.g., key rotation 5/day). Essentials/Professional/Enterprise tables exist (not fetched). Custom per-application rate-limit policies exist (page not fetched). | V | [A8] |
| A19 | Plan matrix | Free: 25 000 MAU, 1 tenant, 3 admins, 1 Enterprise connection + unlimited "Okta connections", **Private Key JWT, BCL, Continuous Session Protection: Enterprise only**; **Role Management: Essentials+**; "Integration with Okta Universal Logout: Included" on all plans; M2M tokens 1 000 included on Free (5 000 on Professional+). | V | [A11-pricing] |

---

## (b) Adapter capability matrix

### b1. Actions

| RevocationGap verb | Exact call | Privilege (Management API access token via client-credentials) | Plan | Sync? | Notes |
|---|---|---|---|---|---|
| Block / unblock user | `PATCH /api/v2/users/{id}` body `{"blocked":true|false}` | `update:users` (U — scope not read; standard) | all | sync | Effect on existing tokens/sessions = U1. |
| Revoke RT by value | `POST /oauth/revoke` (`client_id`, `token`, optional `client_secret`) | client credentials of the RT's client (none for public clients) | all | immediate (V) | May delete grant depending on tenant toggle (A5). Authlib `revoke_token()` applicable; endpoint auth `client_secret_post/basic/none`. |
| Revoke one RT by id | `DELETE /api/v2/refresh-tokens/{id}` | `delete:refresh_tokens` | Enterprise | **async** | Find id via `GET /api/v2/users/{id}/refresh-tokens` (`read:refresh_tokens`). |
| Revoke all RTs of user | `DELETE /api/v2/users/{id}/refresh-tokens` | `delete:refresh_tokens` | Enterprise | **async** | |
| Delete device credential (legacy RT revoke) | `DELETE /api/v2/device-credentials/{id}` | `delete:device_credentials` | plan not stated (I: lower plans) | (U) | |
| Terminate session | `DELETE /api/v2/sessions/{id}` / `DELETE /api/v2/users/{id}/sessions` | `delete:sessions` | Enterprise | **async** | Doesn't revoke RTs (A8). BCL fan-out via `session-deleted` initiator. |
| Terminate session + RTs | `POST /api/v2/sessions/{id}/revoke` (U) | `delete:sessions` (+RT scope?) (U) | Enterprise | (U) | verify path in lab. |
| Revoke grant(s) | `DELETE /api/v2/grants/{id}` / `DELETE /api/v2/grants?user_id=` | `delete:grants` | all | (U) | Revokes all tokens for the grant (V concept). |
| Remove role / permission | `DELETE /api/v2/users/{id}/roles` body `{"roles":[…]}` (3P old docs); role permission delete: `DELETE /api/v2/roles/{id}/permissions` (U) | `update:users` / `update:roles` (U) | Essentials+ | sync | AT permissions stay until expiry (I); next RT exchange / login re-evaluates. |
| Delete user | `DELETE /api/v2/users/{id}` | `delete:users` (U) | all | (U) | avoid as default verb (loses audit & test fixtures). |
| Force re-login at upstream (Okta) | via Okta UL → `POST /oauth/global-token-revocation/connection/{name}` (signed by Okta) | — | all | async | Test harness can *impersonate* Okta only with a federated Okta/OIDC connection whose JWKS the harness controls (I; needs lab OIDC IdP) |
| Password change | `PATCH /api/v2/users/{id}` password (also clears admin block) / change-password ticket | `update:users` | all | sync | Auth0's "Post Change Password" Action can revoke RTs if the tenant implements it (3P forum) — config-dependent. |

### b2. Observation endpoints

| Need | Call | Notes |
|---|---|---|
| RT still valid? | `POST /oauth/token` `grant_type=refresh_token` | Authoritative. Failure shape `invalid_grant`. **Consumes/rotates the RT** if rotation on — use disposable RT copies per probe. 30/s limit on Free. |
| AT accepted by RS? | call the API | only truth for JWT validation behavior. |
| User profile still reachable with AT? | `GET /userinfo` | Rate-limited 5/min per user on Free; does it honor block? (U2). |
| Session alive? | `GET /api/v2/sessions/{id}` (Enterprise) or silent auth `/authorize?prompt=none` with the SSO cookie | latter needs browser/cookie jar. |
| RT/grant exists? | `GET /api/v2/refresh-tokens/{id}` (Enterprise), `GET /api/v2/grants?user_id=…` | |
| User blocked? | `GET /api/v2/users/{id}` → `blocked` | |
| Events | `GET /api/v2/logs?from=<log_id>&take=100` (checkpoint) | send `X-Correlation-ID` on admin calls to find resulting logs; `read:logs` (+`read:logs_users` for user logs, 3P). |
| JWKS | `GET /.well-known/jwks.json` | 20/s Free. |
| Discovery | `GET /.well-known/openid-configuration` (U — not fetched; assumed) | |

### b3. Event / telemetry sources and latency

| Source | Latency (documented) | Caveat |
|---|---|---|
| Tenant logs API | "not real-time… some delays" (no figure) | Free: 1-day retention; checkpoint API ordered by `log_id`. |
| Log Streams (HTTP webhook, Datadog, Splunk, EventBridge…) | "near real-time" (V [A-cat] — no figure) | Not on Free; ≤2–3 streams; non-2xx ⇒ suspended; stream `status` observable. |
| Back-Channel Logout | queued; "slight delay under high load" | Enterprise; RP endpoint must be internet-reachable TLS → lab needs a tunnel/public host. |
| Universal Logout | next session poll / AT expiry (doc) | Free plan eligible. |
| SSF/CAEP | **Auth0 has no SSF transmitter/receiver** (3P blog: "no SSF capabilities at all… only link is UL bridge via GTR") (3P — not vendor-confirmed) | Don't build an Auth0 SSF adapter. |
| Actions (Post-Login / Post-Change-Password / Credentials-Exchange) | synchronous in pipeline | Custom Actions in the lab can themselves revoke RTs/sessions — document "no Actions" precondition. |

---

## (c) Documented enforcement delays / propagation windows (with doc caveats)

| Mechanism | Window | Caveat | Tag |
|---|---|---|---|
| Access token (JWT) after block/RBAC/session/RT change | until `exp`: default 24 h, ≤30 d (configurable; tenant-chosen) | "cannot be revoked"; no introspection endpoint | V\*/V [A3, A15] |
| `/oauth/revoke` | immediate | tenant "deletes grant" toggle changes blast radius | V [A1] |
| Management API RT DELETE | eventually consistent (unquantified) | "not immediately revoked when command finishes" | V [A1, A18] |
| Management API session DELETE | eventually consistent (unquantified) | RTs survive | V [A4] |
| Back-channel logout delivery | queued; delay under load | RP must be reachable | V [A6] |
| Universal Logout effect | next `checksession` poll (browser) / ≤ max AT lifetime (RT apps) | doesn't revoke ATs | V [A7] |
| RT rotation overlap | configurable seconds | within window breach detection off | V\* [A17] |
| Log availability | unquantified delay | no real-time guarantee | V [A9] |
| Absolute RT lifetime | fixed at issuance | later config change doesn't shorten existing RTs | V\* [A16] |
| Idle RT lifetime | evaluated with current app setting at each exchange | — | V\* [A16] |

---

## (d) Lab / test feasibility, cost, ToS

* **Free tenant** ($0, no card; custom domain needs card): 25 000 MAU, 3 admins, 1 tenant, 5 Actions/Forms, **1 enterprise connection** + unlimited Okta connections, 1 000 M2M tokens (Management-API tokens are M2M tokens — cache them ≤ their `expires_in`, default 24 h, to avoid burning the quota — (I)), Mgmt API 2 req/s, log retention 1 day, no log streams (V [A11-pricing], [A8], [A9]).
* **What the Free lab *can* test:** AT lifetime semantics, RT revoke/rotation/reuse detection/overlap, absolute/idle lifetimes, grants revocation, user block, password change, UL receiver (via OIDC/Okta connection), JWKS rotation, `/userinfo`.
* **What it cannot:** Sessions API, refresh-token Management API (use `/oauth/revoke` or device-credentials instead), Back-Channel Logout, Private Key JWT client auth, role management (Essentials+), log streaming, long log retention, Continuous Session Protection. These need an **Enterprise** (or at least Essentials/Professional for roles/streams) tenant — price "Contact us" for Enterprise (V [A11-pricing]).
* **ToS / policy constraints** (V [A12, A13]): penetration testing requires a **paid** subscription, ≥7 days' notice via Support Center with dates, source IPs, tooling, RPS, two contacts; tests restricted to your own tenant; Management and Authentication APIs may be tested, **not the Dashboard**; no DoS/volumetric; must conform to rate-limit policy; not during change-freeze periods; Auth0 may block the tenant/source if unreachable. Load testing: Enterprise only, written approval ≥2 weeks ahead, 2 h window, off-peak per region, Auth0 may suspend access on violation. ⇒ **RevocationGap must default to a rate-limited "conformance" mode** (≤ published limits, serial admin calls) and gate "adversarial" modes behind an explicit "I have clearance" acknowledgement per tenant. (Auth0's general self-service ToS not fetched — U4.)
* **Back-channel testing needs a public HTTPS endpoint** reachable by Auth0 (V [A6]) → ship an optional tunnel recipe; localhost-only labs can't receive BCL.
* **Okta↔Auth0 chain test** (Okta UL → Auth0 GTR) needs an Okta org with ITP/EA UL (not in the Integrator Free Plan) — see OKTA.md.

---

## (e) Pitfalls producing false positives / false negatives

1. **"Revoked AT still works" is expected** (V [A3]); classify as *documented enforcement delay* unless the target API claims opaque/introspected tokens. Don't count it against Auth0.
2. **Eventually-consistent Management API deletes**: probing immediately after a 204 may show "still valid" → use bounded retry windows; record `t_call`, `t_first_denied`; never conclude "not revoked" from a single early probe (V [A1, A4]).
3. **Session delete ≠ RT revoke** (V [A4]); a surviving RT after `DELETE …/sessions` is *documented*, not a bug.
4. **Rotation overlap & reuse detection side-effects**: replaying an old RT can revoke the whole family (V [A1]) and poison later probes; keep per-probe disposable token families.
5. **Tenant toggle "Refresh Token Revocation Deletes Grant"** changes what `/oauth/revoke` kills; record the setting in the run manifest (V [A1]).
6. **Pre-Sept-2023 RTs have `session_id=null`** → session-linked revocation cannot cover them (V [A1]).
7. **`/oauth/revoke` returns 200 for unknown tokens?** (RFC 7009 behavior; Auth0 specifics not read — U5). Verify via the refresh grant, not the revoke response.
8. **Rate-limit/429 confusion**: Mgmt API 2 req/s on Free; probes + admin calls share the limit; Authentication-API `/userinfo` is only 5/min per user.
9. **Logs are delayed and retention is 1 day on Free** → evidence collection must pull logs promptly or via log stream (Essentials+).
10. **Block-user semantics unknown** (U1) — don't assert "defect" for surviving tokens; classify "needs verification" until a lab baseline exists.
11. **Custom Actions** (e.g., post-change-password revoke, scope overrides) alter outcomes — record the tenant's Action inventory (3P [A21]).
12. **Federation chains**: Auth0 → upstream IdP sessions — an upstream session may silently re-issue Auth0 tokens after Auth0-side revocation (I); `session_expiry` handling (V\* [A26]) only for Okta/OIDC connections.
13. **Free-plan M2M quota (1 000 tokens)** — token-per-probe designs exhaust it (V [A11-pricing]).

---

## (f) Open uncertainties

| ID | Question | Resolution path |
|---|---|---|
| U1 | Effect of `blocked=true` on existing sessions, ATs, RT exchanges, `/userinfo` | Lab matrix; ask Auth0 support. |
| U2 | Does `/userinfo` honor block/session/RT revocation? | Lab. |
| U3 | Exact scope of `/oauth/revoke` ("all tokens for the same grant" vs toggle) | Lab with toggle on/off. |
| U4 | Self-service ToS text re security testing on Free tenants | Read Okta MSA/Auth0 self-service terms; legal review. |
| U5 | `/oauth/revoke` response for unknown/expired tokens | Lab. |
| U6 | Exact path/scopes of "revoke session + RTs" (`POST /api/v2/sessions/{id}/revoke`?) | Fetch Management API OpenAPI `https://auth0.com/docs/oas/management/v2/management-api-oas.json` (listed in llms.txt) and diff; exact scopes for `users` PATCH, roles, grants. |
| U7 | Rate-limit response headers (`x-ratelimit-*`) and Essentials/Enterprise numbers | Fetch rate-limit pages (URLs known from llms.txt). |
| U8 | Log-stream delivery latency numbers; log type codes for UL/refresh/block | Fetch log catalog (dynamic page) / OpenAPI `logs-schema.json`. |
| U9 | XAA revocation semantics (ID-JAG / resource tokens) | EA docs; lab. |
| U10 | Whether `/v2/logout` and OIDC `/oidc/logout` terminate RTs (docs page fetch failed) | fetch `log-users-out-of-auth0` page. |

---

## Source key (this file)

| ID | URL | Note |
|---|---|---|
| A1 | https://auth0.com/docs/secure/tokens/refresh-tokens/revoke-refresh-tokens | fetched (V) |
| A2 | https://support.auth0.com/center/s/article/Invalidate-the-API-token-after-user-logout | search excerpt |
| A3 | https://dev.auth0.com/docs/secure/tokens/revoke-tokens | fetched (short page) |
| A4 | https://auth0.com/docs/manage-users/sessions/manage-user-sessions-with-auth0-management-api | fetched |
| A5 | https://auth0.com/docs/manage-users/user-accounts/block-and-unblock-users | fetched |
| A6 | https://auth0.com/docs/authenticate/login/logout/back-channel-logout | fetched |
| A7 | https://auth0.com/docs/authenticate/login/logout/universal-logout | fetched |
| A8 | https://auth0.com/docs/troubleshoot/customer-support/operational-policies/rate-limit-policy/rate-limit-configurations/free-public.md | fetched |
| A9 | https://auth0.com/docs/deploy-monitor/logs/log-data-retention.md | fetched |
| A10 | https://auth0.com/docs/deploy-monitor/logs/retrieve-log-events-using-mgmt-api.md | fetched |
| A11-pricing | https://auth0.com/pricing.md | fetched (plan/feature matrix) |
| A12 | https://auth0.com/docs/troubleshoot/customer-support/operational-policies/load-testing-policy.md | fetched |
| A13 | https://auth0.com/docs/troubleshoot/customer-support/operational-policies/penetration-testing-policy.md | fetched |
| A14 | https://auth0.com/docs/ai-agents-mcp/cross-app-access.md | fetched |
| A15 | https://dev.auth0.com/docs/secure/tokens/access-tokens/update-access-token-lifetime | search excerpt |
| A16 | https://auth0.com/docs/secure/tokens/refresh-tokens/configure-refresh-token-expiration | search excerpt |
| A16b | https://auth0.com/blog/achieving-a-seamless-user-experience-with-refresh-token-inactivity-lifetimes/ | blog excerpt |
| A17 | https://auth0.com/docs/secure/tokens/refresh-tokens/configure-refresh-token-rotation | search excerpt |
| A18 | https://auth0.com/blog/introducing-session-management-api/ | blog excerpt (scopes, async note) |
| A19 | https://auth0.com/docs/api/management/v2/grants/delete-grants-by-id ; https://auth0.com/docs/api/management/v2/grants/delete-grants-by-user-id ; https://auth0.github.io/auth0-PHP/classes/Auth0-SDK-API-Management-Grants.html | search excerpts |
| A20 | https://community.auth0.com/t/rfc-7662-support/69519 | community |
| A21 | https://auth0.com/docs/authorization/rbac/enable-role-based-access-control-for-apis | search excerpt |
| A22 | https://auth0.com/blog/refresh-token-security-detecting-hijacking-and-misuse-with-auth0/ | blog excerpt (`ferrt`) |
| A23 | https://support.auth0.com/center/s/article/Change-access-token-Expiration-Time ; https://support.auth0.com/center/s/article/What-is-the-minimum-lifetime-of-an-Access-Token | support excerpts |
| A26 | https://auth0.com/changelog | search excerpt (session_expiry / IPSIE) |
| A27 | https://auth0.com/docs/api/management/v2/log-streams/get-log-streams | search excerpt |
| — | https://auth0.com/docs/llms.txt | fetched: docs index incl. OpenAPI URLs (`/docs/oas/management/v2/management-api-oas.json`) |
| A-cat | https://auth0.com/docs/deploy-monitor/logs/log-event-type-codes.md | fetched (catalog is dynamic; only the `X-Correlation-ID` correlation guidance read) |
| 3P | https://andrewdoering.org/blog/2026/authzen-shared-signals-framework-part-2-okta/ | third-party: "Auth0 … no SSF capabilities" |
