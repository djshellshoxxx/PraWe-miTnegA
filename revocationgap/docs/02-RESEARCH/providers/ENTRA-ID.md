# Microsoft Entra ID — revocation / session / token-invalidation behaviour and Graph administrative surface
Draft for `docs/02-RESEARCH/providers/ENTRA-ID.md` · researched 2026-10-12 · author: providers-a agent

**No Entra tenant was available to me.** Everything below is either read from Microsoft Learn / the live public OIDC metadata endpoint, or explicitly marked inferred/unverified. There are **no lab-observed Entra behaviours** in this file; every timing claim is the vendor's own caveat. Items an adapter author must confirm in a real developer tenant are collected in §6.

## 0. Evidence legend
| Tag | Meaning |
|---|---|
| **V-doc** | stated on a Microsoft Learn / Microsoft page fetched this session (page "last updated" date from the page footer is given in SOURCES.md) |
| **V-live** | observed by me on a public Microsoft endpoint on 2026-10-12 (no tenant needed) |
| **V-3p** | third-party source (blog / Q&A) — context only, never used as sole basis |
| **I** | inferred |
| **U** | unverified / not found in primary sources |

Source IDs (full URLs in `SOURCES.md`; base `https://learn.microsoft.com/en-us/`):
E-CAE `entra/identity/conditional-access/concept-continuous-access-evaluation` (upd. 2026-04-08) · E-CAE-S `…/concept-continuous-access-evaluation-strict-enforcement` (2026-03-24) · E-CAE-W `…/concept-continuous-access-evaluation-workload` (2026-04-23) · E-CAE-T `…/howto-continuous-access-evaluation-troubleshoot` (2026-03-24) · E-DEVCAE `entra/identity-platform/app-resilience-continuous-access-evaluation` (2024-11-21) · E-CLAIMS `entra/identity-platform/claims-challenge` (2024-04-12) · E-SECCAE `security/zero-trust/develop/secure-with-cae` (2025-02-25) · E-AT `entra/identity-platform/access-tokens` (2025-05-14) · E-CTL `entra/identity-platform/configurable-token-lifetimes` (2026-04-24) · E-RT `entra/identity-platform/refresh-tokens` (2025-11-05) · E-REVACC `entra/identity/users/users-revoke-access` (2026-06-19) · E-OIDC `entra/identity-platform/v2-protocols-oidc` (2026-06-30) · E-ROPC `entra/identity-platform/v2-oauth-ropc` (2025-02-07) · E-CC `entra/identity-platform/v2-oauth2-client-creds-grant-flow` · E-CA-OVERVIEW `entra/identity/conditional-access/overview` (2026-04-27) · E-LOGLAT `entra/identity/monitoring-health/reference-log-latency` (2024-09-27) · E-RETENTION `entra/identity/monitoring-health/reference-reports-data-retention` · E-RES `entra/identity/conditional-access/resilience-defaults` · E-BACKUP `entra/architecture/backup-authentication-system` · E-DISC = live `https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration` · G-* = Graph API reference pages `graph/api/…` · DEV-FAQ `office/developer-program/microsoft-365-developer-program-faq` (2026-09-08) · MSRC-ROE `https://www.microsoft.com/en-us/msrc/pentest-rules-of-engagement`.

---
## 1. (a) Verified behaviour

### 1.1 Token lifetimes and CAE-lengthened tokens
| Topic | Statement | Evidence / source |
|---|---|---|
| Default access-token lifetime | Random per token **60–90 minutes (75 on average)**; varies by client, resource and whether Conditional Access is enabled. Tenants without Conditional Access: default **2 hours** for clients such as Teams/Microsoft 365. | V-doc E-AT "Token lifetime"; E-CTL |
| Configurable token lifetime (CTL) | Policy object via **Graph only** (no portal). Property `AccessTokenLifetime` — **min 10 min (`00:10:00`), max 1 day (`23:59:59`)**; affects access, ID **and SAML** tokens. Org-level policy beats app-level. Not for managed identities or personal-account apps. | V-doc E-CTL; Graph `tokenLifetimePolicy` |
| CTL ignored by CAE | "the configurable token lifetime policy isn't honored for clients negotiating CAE-aware sessions." | V-doc E-CAE "Token lifetime" |
| CAE token lifetime | "up to **28 hours**" (E-CAE, E-SECCAE); E-AT says default long-lived range "**20 to 28 hours**"; workload-identity CAE tokens "up to **24 hours**" (E-CAE-W); CTL doc says "24–28 hours". **Docs disagree slightly — treat as 20–28 h.** MSAL proactively refreshes at roughly half-life (E-SECCAE). Non-CAE-capable clients keep the 1 h default (E-CAE). | V-doc |
| CAE "short-token" fallback | One-hour token **without** instant IP enforcement when: MFA-trusted-IP / country-based locations in use; sum of IP ranges > 5 000; resource-seen IP differs from Entra-seen IP but Entra side is allowed (standard mode). | V-doc E-CAE "Supported location policies", "Named location limitations", "Exception for IP address variations" |
| Refresh-token lifetime | **24 h** for SPAs (redirect URI type `spa`) and email-OTP flows; **90 days** for everything else. Sliding: "MaxInactiveTime 90 days"; single/multi-factor max age "until-revoked". Not configurable since 2021-01-30. | V-doc E-RT, E-CTL |
| Refresh-token rotation | "Refresh tokens replace themselves with a fresh token upon every use. The Microsoft identity platform **doesn't revoke old refresh tokens** when used to fetch new access tokens." ⇒ **no reuse detection / no family kill**. | V-doc E-RT |
| What revokes refresh tokens | Table in E-RT: user/admin password change or reset (revokes password-based tokens/cookies; non-password-based tokens survive except for some admin-reset paths and confidential client tokens), user self-revoke, **admin "revoke all refresh tokens"** (revokes all classes), single sign-out (cookie classes). Password *expiry* does not revoke. B2B: not revoked in resource tenant — revoke in home tenant. | V-doc E-RT "Token revocation" |
| SSO-session tokens | Non-persistent session cookies: max inactive 24 h; persistent 90 d; extended on use. | V-doc E-CTL |
| App-only (client-credentials) tokens | No refresh token is issued in this flow. | V-doc E-CC |

### 1.2 Entra-side revocation primitives (Graph)
| Primitive | Semantics (vendor wording paraphrased) | Evidence |
|---|---|---|
| `POST /users/{id\|upn}/revokeSignInSessions` | Invalidates all refresh tokens issued to applications **and session cookies** by resetting `signInSessionsValidFromDateTime` to now. "After you call revokeSignInSessions, there might be a **small delay of a few minutes** before tokens are revoked." Not applicable to external users (they sign in at home tenant). Returns `200 {"@odata.context":…Edm.Boolean,"value":true}`. | V-doc G-revoke |
| `POST /users/{id}/invalidateAllRefreshTokens` (beta) | Older equivalent resetting `refreshTokensValidFromDateTime`; "won't be promoted to GA — use revokeSignInSessions". | V-doc G-invalidate |
| What it does **not** do | Does not invalidate already-issued access tokens: "For applications using access tokens, the user loses access when the access token expires" (E-REVACC) — except at CAE-enabled Microsoft resources, which receive the revocation as a critical event (E-CAE). | V-doc E-REVACC, E-CAE |
| Observation property | `GET /users/{id}?$select=signInSessionsValidFromDateTime,refreshTokensValidFromDateTime` — "Any refresh tokens or session tokens issued before this time are invalid"; read-only, reset only by revokeSignInSessions. Gives the *authoritative revocation timestamp* (use for time-of-action instead of client clock). | V-doc G-user-res |
| Disable user | `PATCH /users/{id} {"accountEnabled":false}`. Blocks new token issuance; existing access tokens live until `exp` unless the resource is CAE-enabled; the doc recommends *also* revoking sessions and disabling devices. | V-doc G-user-update, E-REVACC |
| Delete user | `DELETE /users/{id}` → soft-delete container 30 days (restorable, incl. group memberships). | V-doc G-user-delete |
| Session cookies of apps | "Microsoft Entra ID can't directly revoke a session token issued by an application" — app must revoke its own sessions. | V-doc E-REVACC |

### 1.3 Continuous Access Evaluation (CAE)
| Aspect | Verified statement | Evidence |
|---|---|---|
| Mechanism | Resource provider (RP) subscribes to Entra events; rejects a still-unexpired token with **HTTP 401 + `WWW-Authenticate` claims challenge**; client re-requests token with the challenge. Described as "an industry standard based on … CAEP" but the documented loop is **Entra ↔ Microsoft resources only**. | V-doc E-CAE, E-SECCAE |
| Critical event evaluation (works in any tenant; no CA policy needed) | (1) user account deleted/disabled, (2) password changed/reset, (3) MFA enabled for user, (4) admin explicitly revokes all refresh tokens, (5) high user risk by ID Protection. | V-doc E-CAE |
| Conditional Access policy evaluation | Exchange Online, SharePoint Online, Teams, **MS Graph** sync key CA policies (IP-named-location based) for in-service evaluation. CAE only understands **IP-based named locations** (not MFA trusted IPs or country locations). | V-doc E-CAE |
| Documented latency | Critical events: "near real time, but **latency of up to 15 minutes** might be observed because of event propagation time; however, IP locations policy enforcement is instant." | V-doc E-CAE (intro) |
| Policy / group-membership changes | "could take **up to one day** to be effective" (replication to RPs); some policy-update optimisation → **two hours**; to force immediacy: revoke sessions. | V-doc E-CAE "Limitations" |
| Re-enable after disable | "latency before the account is recognized as enabled": SharePoint Online & Teams ≈15 min; **Exchange Online ≈35–40 min**. | V-doc E-CAE |
| Supported clients/RPs | Matrix in E-CAE: Outlook (all platforms) ↔ Exchange/SharePoint supported; Office web apps **not** supported (1-h tokens when CA set); OneDrive partly; Teams "partially supported" (calls/chat don't adhere to IP policies); Azure Government (GCC High/DoD) for Exchange. | V-doc E-CAE tables |
| Not covered | **Guest users**: "CAE doesn't support Guest user accounts. CAE revocation events and IP based Conditional Access policies aren't enforced instantaneously." Co-authoring in Office: revocation after closing doc/app or 1 h with CA IP policy (15 min if SPO admin shortens). Push notifications are not IP-evaluated. | V-doc E-CAE |
| Disable / customise | CAE is auto-enabled via Conditional Access; admin can **Disable** in a CA policy session control (only works with "All resources", no conditions). | V-doc E-CAE, CA session doc (search excerpt) |
| Sign-in log field | "Is CAE Token" filter in sign-in logs; workload SP sign-ins show "Continuous access evaluation" field. | V-doc E-CAE-T, E-CAE-W |
| Strict location enforcement (**preview**) | Mode "Strictly enforce location policies": access blocked immediately if the IP seen by the RP isn't allowed by the CA policy; needs dedicated enumerable egress IPs for both Entra and all RPs; sign-in log filter "IP address (seen by resource)". Default = Standard mode (falls back to a 1-h token when Entra-seen IP is allowed). | V-doc E-CAE-S |
| Workload identities (service principals) | CAE for single-tenant service principals; **only for requests to Microsoft Graph**; revocation events: service principal **disable, delete, high SP risk**; LLT up to 24 h; opt-in via `cp1`; needs Workload Identities Premium to author CA policies for SPs; multitenant/3rd-party SaaS and managed identities out of scope. | V-doc E-CAE-W |
| Application Proxy CAE | A separate CAE implementation with similar triggers (user disabled/deleted, password change, MFA enabled, revoke tokens, high risk); beta Graph property `isContinuousAccessEvaluationEnabled`. | V-doc (search excerpt of app-proxy CAE page) |

### 1.4 Claims-challenge flow (client side), `xms_cc`, `cp1`
- Opt-in: client must declare capability `cp1` in its token requests: claims parameter `{"access_token":{"xms_cc":{"values":["cp1"]}}}` (MSAL: `client_capabilities=["cp1"]` / `WithClientCapabilities` / `clientCapabilities`). "An application won't receive claims challenges (and won't be able to use … CAE tokens) unless it declares … `cp1`." — V-doc E-CLAIMS, E-DEVCAE, E-CAE-W.
- Resource API can learn whether the caller is capable by requesting the **optional claim `xms_cc`** in its app manifest; token then carries `"xms_cc":["cp1"]` — V-doc E-CLAIMS.
- Challenge format (RFC 6750-style): `HTTP 401` + `WWW-Authenticate: Bearer realm="", authorization_uri="https://login.microsoftonline.com/common/oauth2/authorize", error="insufficient_claims", claims="<base64 JSON>"`. Example CAE revocation challenge decodes to `{"access_token":{"nbf":{"essential":true,"value":"1604106651"}}}` (my decode of the doc's example); a CA authentication-context challenge decodes to `{"access_token":{"acrs":{"essential":true,"value":"cp1"}}}`. `claims` must be base64-decoded and forwarded in the `claims` parameter of the next `/authorize` or silent token request until a token is obtained. Required header parts: type `Bearer`, `authorization_uri`, `error="insufficient_claims"`, `claims`; all in the **same** `WWW-Authenticate` header; multiple headers may be present — V-doc E-CLAIMS, E-DEVCAE.
- Apps that don't handle challenges "might repeatedly retry an API call using a token that is technically valid but is revoked due to CAE" (E-DEVCAE) — a real false-positive source for a tester.
- **`xms_rl`: not found** in any fetched Microsoft page nor via search; I cannot confirm it exists as a documented claim/parameter. Treat as **U**; do not implement.

### 1.5 "Resilience defaults" (Conditional Access) and the backup authentication system
- During an Entra primary-service outage the **Backup Authentication Service** can issue access tokens for *existing sessions* (not new sessions, not guests). With *resilience defaults* enabled (default for all policies), conditions that can't be evaluated in real time use data collected at session start (e.g. role membership). Disabling resilience defaults on a policy makes unevaluable conditions block access. — V-doc E-RES (search excerpt of learn page) / E-BACKUP.
- The backup system "can't perform fresh revocation checks"; relies on the CRL state at last backup; needs a successful authentication within **3 days** with same app/device; "If you need to revoke before this backup expires, you should explicitly revoke the session". — V-doc E-BACKUP (search excerpt).
- Relevance: only during outages; a revocation tester should record `Token issuer type == Microsoft Entra Backup Auth` in sign-in logs and treat such windows as *inconclusive*.

### 1.6 How resource APIs validate Entra tokens, and what that implies
- Web APIs "must validate access tokens"; validate signature against JWKS from the OIDC metadata (`jwks_uri`), `iss`, `aud` (must be one of the API's App ID URIs), `tid`/signing-key issuer for multi-tenant — V-doc E-AT "Validate tokens". Clients must treat access tokens as opaque; tokens for Microsoft Graph are proprietary and not validatable by apps (E-AT).
- Default = **local JWT validation** ⇒ everything in §1.1–1.3 about "access token remains valid until `exp`" applies to custom APIs; **no CAE-style push exists for third-party/custom APIs in the documentation I found** (CAE-enabled resources are Microsoft services; E-SECCAE says "CAE-enabled Microsoft resources"). Custom APIs that want revocation must introspect (not offered by Entra — §1.7), call Graph (`signInSessionsValidFromDateTime`, `accountEnabled`), or keep short sessions (U whether any supported subscription path exists for custom RPs).
- Tenant/identity state per request is *not* re-checked by Entra for custom APIs: after `accountEnabled=false` + `revokeSignInSessions`, a JWT issued earlier is still accepted by a local validator until `exp` (60–90 min, up to 28 h for CAE-capable client+resource combos; custom APIs are not CAE resources) — I (from E-REVACC + E-AT).

### 1.7 Protocol surface: OIDC discovery, revoke, introspect, userinfo, logout (V-live E-DISC fetched 2026-10-12; `cache-control: max-age=86400`)
Fields present in `https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration`: `issuer` (`https://login.microsoftonline.com/{tenantid}/v2.0` template), `authorization_endpoint`, `token_endpoint`, `device_authorization_endpoint`, `userinfo_endpoint` (**`https://graph.microsoft.com/oidc/userinfo`**), `end_session_endpoint` (`…/oauth2/v2.0/logout`), `jwks_uri` (`…/discovery/v2.0/keys`), `frontchannel_logout_supported: true`, `http_logout_supported: true`, `token_endpoint_auth_methods_supported` [`client_secret_post, private_key_jwt, client_secret_basic, self_signed_tls_client_auth`], `response_types_supported`, `response_modes_supported` [query, fragment, form_post], `subject_types_supported` [pairwise], `id_token_signing_alg_values_supported` [RS256], `scopes_supported` [openid, profile, email, offline_access], `claims_supported` (sub, iss, aud, exp, iat, auth_time, acr, nonce, preferred_username, name, tid, ver, at_hash, c_hash, email, cloud_* …), `request_uri_parameter_supported: false`, `mtls_endpoint_aliases`, `tls_client_certificate_bound_access_tokens: true`, `kerberos_endpoint`, `rbac_url`, `tenant_region_scope`, `msgraph_host`.
**Absent:** `revocation_endpoint`, `introspection_endpoint`, `backchannel_logout_supported`, `backchannel_logout_session_supported`, `check_session_iframe`, `grant_types_supported`, `code_challenge_methods_supported`, `pushed_authorization_request_endpoint`, `jwks`-embedded keys.
Live probes (V-live): `POST /common/oauth2/v2.0/revoke` → **HTTP 404**; `POST /common/oauth2/v2.0/introspect` → HTTP 400 `AADSTS900144 … must contain … 'continuation_token'` — i.e. that path belongs to the *native-authentication* API family and is **not an RFC 7662 introspection endpoint** (the 400 is not evidence of an introspection capability; U for the native-auth documentation). **Conclusion: Entra v2.0 exposes no RFC 7009 revocation endpoint and no RFC 7662 introspection endpoint** (discovery + live probe; the Learn page E-SECCAE describes introspection as an *alternative pattern*, not an Entra feature). Session/refresh revocation is admin/user-driven via Graph or the user-facing "revoke sessions".
Logout: front-channel `end_session_endpoint` only (browser redirect to clear the Entra session; apps with `frontchannel_logout_uri` registered are notified); **no back-channel logout token** advertised (absence from metadata; U whether per-app back-channel logout exists for SAML/OIDC in app registration — not verified).

### 1.8 Graph operations to drive/observe state changes (v1.0 unless noted)
| Action | Call | App permission (least privileged per doc) | Notes / evidence |
|---|---|---|---|
| Create test user | `POST /users` | `User.Create` (higher: `User.ReadWrite.All`, `Directory.ReadWrite.All`) | V-doc G-user-post |
| Disable/enable user | `PATCH /users/{id}` `{"accountEnabled":false}` | `User.EnableDisableAccount.All` **+** `User.Read.All` (higher: `User.ReadWrite.All`, `Directory.ReadWrite.All`) | V-doc G-user-update. "In app-only scenarios in addition to Graph permissions, the app must be assigned a higher privileged administrator role" **when the target is an admin** (property is "subject to sensitive action restrictions"). |
| Revoke refresh tokens + session cookies | `POST /users/{id}/revokeSignInSessions` | `User.RevokeSessions.All` (delegated and application) | V-doc G-revoke; also Directory/User.ReadWrite.All delegated. Delegated callers need e.g. User Administrator-class role (U exact list for revoke). |
| Reset password | `PATCH /users/{id}` `passwordProfile` | `User-PasswordProfile.ReadWrite.All`; app-only also needs ≥ User Administrator role | V-doc G-user-update. |
| Remove group member | `DELETE /groups/{gid}/members/{uid}/$ref` (204) | `GroupMember.ReadWrite.All` (higher: `Group.ReadWrite.All`, `Directory.ReadWrite.All`) | V-doc G-group-delmember; **not possible for dynamic-membership groups**; role-assignable groups restrict delegated roles. |
| Remove app-role assignment from user | `DELETE /users/{id}/appRoleAssignments/{assignmentId}` (204) | `AppRoleAssignment.ReadWrite.All` | V-doc G-approle-user-del. Token `roles` claim in already-issued tokens is unaffected until expiry (I). |
| Delete user | `DELETE /users/{id}` | `User.ReadWrite.All` (I) | 30-day soft delete (V-doc G-user-delete). |
| Conditional Access policy CRUD | `POST/PATCH/DELETE /identity/conditionalAccess/policies[/{id}]` | `Policy.Read.All` **and** `Policy.ReadWrite.ConditionalAccess` (create/update docs list `Application.Read.All`+`Policy.ReadWrite.ConditionalAccess` as the higher-privileged alternative; create doc notes a "known permissions issue" that "may require consent to multiple permissions") | V-doc G-ca-post/update/delete. **Requires Entra ID P1** ("Using this feature requires Microsoft Entra ID P1 licenses" E-CA-OVERVIEW). When licenses lapse existing policies can be read/deleted but not updated. |
| Token-lifetime policy | `POST /policies/tokenLifetimePolicies`; assign `POST /applications/{id}/tokenLifetimePolicies/$ref` | `Policy.ReadWrite.ApplicationConfiguration` (+ `Application.ReadWrite.OwnedBy` or `.All` for assignment) | V-doc G-tlp-create/assign. |
| Device compliance (Intune) | `managedDevice` resource: actions `retire`, `wipe`, `remoteLock`, `rebootNow`, etc.; `complianceState` is **read-only**. Entra `device.isCompliant` / `isManaged` "can only be updated by Intune … or an approved MDM app for Windows". | n/a | V-doc G-manageddevice, G-device-update. **There is no documented Graph call to flip a device's compliance state directly**; practical automation needs a real/virtual enrolled device and a compliance policy change (U feasibility in CI). Disabling the Entra device object (`PATCH /devices/{id} {"accountEnabled":false}`, `Device.ReadWrite.All`) is automatable and is the documented step in E-REVACC. |
| Observe sign-ins | `GET /auditLogs/signIns` | `AuditLog.Read.All` (+ role Reports Reader/Security Reader/Global Reader; CA details need `Policy.Read.*`) | V-doc G-signin-list. v1.0 page documents *interactive* sign-ins "and successful federated sign-ins"; non-interactive/service-principal sign-ins live in separate log categories (beta/portal) — U exact v1.0 coverage. |
| Observe audit | `GET /auditLogs/directoryAudits` | `AuditLog.Read.All` | U (not fetched). |
| Observe revocation timestamp | `GET /users/{id}?$select=signInSessionsValidFromDateTime,accountEnabled` | `User.Read.All` | V-doc G-user-res (properties require `$select`). |

### 1.9 Sign-in / audit log latency and retention
- No numeric SLA is published now. E-LOGLAT: latency depends on type/amount of data and the pipeline (log processors → storage queue → partner services such as Azure Monitor/Graph); Log Analytics routing "up to **three days**"; new storage/SIEM sink ≈24 h; `signInActivity` (last sign-in) "might take up to **24 hours** to update". V-doc.
- Retention: audit logs and sign-ins **7 days (Free)**, **30 days (P1/P2)**; Graph activity logs only via diagnostic settings. V-doc E-RETENTION.
- Empirical numbers exist only from third parties (≈5–7 min typical, long tail >1 h; Petra Security blog, MS Q&A) — V-3p, not for spec use except as a hint.

### 1.10 Shared Signals / CAEP status
- Microsoft's CAE is described as "based on" the OpenID CAEP profile, but **I found no Microsoft documentation of Entra acting as an SSF/CAEP transmitter to external receivers, nor accepting SSF events** (no `/.well-known/ssf-configuration` documented). A 2026 third-party analysis reaches the same conclusion ("no public Microsoft documentation describes how to configure Entra as a CAEP/SSF transmitter", V-3p andrewdoering.org). Status: **U/likely not offered** — do not claim support. Interop fact: Microsoft CAE is a closed loop between Entra and Microsoft resources (V-doc E-CAE/E-SECCAE).

---
## 2. (b) Adapter capability matrix

### 2.1 State-change ("actor") capabilities
| Capability | Call | Least privilege (app-only) | Direct effect on already-issued tokens |
|---|---|---|---|
| Disable user | `PATCH /users/{id}` accountEnabled=false | `User.EnableDisableAccount.All`+`User.Read.All` | New tokens/refresh fail; access tokens valid to `exp`; CAE RPs reject within ≤15 min (critical event) |
| Revoke refresh tokens/sessions | `POST /users/{id}/revokeSignInSessions` | `User.RevokeSessions.All` | Refresh tokens + cookies invalid after "a few minutes"; access tokens valid to `exp` except CAE RPs (≤15 min) |
| Delete user | `DELETE /users/{id}` | `User.ReadWrite.All` (I) | as disable + object gone; soft-deleted 30 d |
| Password reset | `PATCH /users/{id}` passwordProfile | `User-PasswordProfile.ReadWrite.All` + User Administrator role | revokes password-based refresh tokens (per E-RT table); CAE critical event |
| Group membership removal | `DELETE /groups/{id}/members/{id}/$ref` | `GroupMember.ReadWrite.All` | `groups` claim in issued tokens stale until `exp`; CAE/CA-policy effect up to 1 day (E-CAE) |
| App role assignment removal | `DELETE /users/{id}/appRoleAssignments/{id}` | `AppRoleAssignment.ReadWrite.All` | `roles` claim stale until `exp` (I) |
| CA policy create/update/delete | `…/identity/conditionalAccess/policies` | `Policy.Read.All` + `Policy.ReadWrite.ConditionalAccess` | applies at next token issuance; CAE RPs evaluate synced policy (≤1 day, 2 h optimised) |
| Token-lifetime policy | Graph `tokenLifetimePolicies` | `Policy.ReadWrite.ApplicationConfiguration` | affects tokens issued after assignment; ignored for CAE sessions |
| Disable device object | `PATCH /devices/{id}` accountEnabled=false | `Device.ReadWrite.All` | device-bound token issuance; (E-REVACC) |
| Intune retire/wipe | `managedDevice` actions | Intune scopes (not fetched) | device-level; not a token primitive |
| Token revoke / introspect | **none exists** | — | — |

### 2.2 Observation ("probe") capabilities
| Probe | How | Notes |
|---|---|---|
| Resource call with AT | target API (custom API: JWT local validation; Graph `GET /me` etc.) | For CAE: expect `401` + `WWW-Authenticate … error="insufficient_claims"` + `claims=` when revoked inside token lifetime (V-doc); only for a client that sent `cp1` |
| Token endpoint refresh | `POST /{tenant}/oauth2/v2.0/token grant_type=refresh_token` | error codes `invalid_grant` with `AADSTS` text (e.g. `AADSTS50173`/`AADSTS70043`/`AADSTS700082` families — **U**, codes not fetched); each use issues a new RT without invalidating the old one (V-doc E-RT) |
| Graph `GET /users/{id}?$select=accountEnabled,signInSessionsValidFromDateTime` | `User.Read.All` | authoritative revocation timestamp (V-doc) |
| Sign-in logs | `GET /auditLogs/signIns` | latency minutes–hours (§1.9); fields `ipAddress`, `conditionalAccessStatus`, `isInteractive`; CAE flags in portal/beta (U v1.0) |
| JWKS / discovery | `/{tenant}/v2.0/.well-known/openid-configuration` | key rollover; not revocation |
| `userinfo` | `https://graph.microsoft.com/oidc/userinfo` | Graph-hosted; subject to Graph CAE; not a validity oracle (U) |

### 2.3 Event / telemetry sources
| Source | Latency |
|---|---|
| Entra → CAE RP critical-event feed (not consumable by third parties) | ≤15 min documented (E-CAE) |
| Sign-in logs (portal/Graph) | no SLA; third-party typical 5–7 min; docs: Log Analytics up to 3 days; `signInActivity` ≤24 h |
| Audit logs `directoryAudits` | no SLA documented (U) |
| Diagnostic settings → Event Hub/Log Analytics/Storage | Log Analytics up to 3 days; new sink 24 h (E-LOGLAT) |
| SSF/CAEP stream | not offered (U) |

---
## 3. (c) Documented enforcement delays / propagation windows (vendor caveats)
| Window | Value | Source |
|---|---|---|
| Access token validity (default) | random 60–90 min (avg 75); 2 h for Teams/M365 clients w/o CA | E-AT |
| CAE long-lived token | up to 28 h (20–28 h default range; 24 h workload) | E-CAE, E-AT, E-CAE-W |
| CAE critical event propagation | "up to 15 minutes"; IP-location enforcement "instant" | E-CAE |
| revokeSignInSessions | "small delay of a few minutes" | G-revoke |
| CA policy / group-membership change at RPs | "up to one day"; optimised paths 2 h; revoke sessions to force | E-CAE |
| Re-enable after disable | SPO/Teams ≈15 min; Exchange ≈35–40 min | E-CAE |
| Refresh-token life | 24 h (SPA/email-OTP) / 90 d inactive; no reuse detection | E-RT |
| Backup-auth (outage only) | session metadata ≤3 days; no fresh revocation check | E-BACKUP |
| Log/Audit visibility | up to 24 h (`signInActivity`), up to 3 days (Log Analytics) | E-LOGLAT |
| Developer tenant lifetime | up to 90 days, renewable while actively developing | DEV-FAQ |
| App provisioning cycle (SaaS deprovisioning) | typically every 20–40 minutes | E-REVACC |
Also: "Microsoft may require tenants to be recreated every 90 days" (DEV-FAQ) — plan fixture re-provisioning.

## 4. (d) Lab / CI feasibility
| Question | Finding |
|---|---|
| Free test tenant? | **Microsoft 365 Developer Program** E5 sandbox: 25 licences (24 test users + admin), Entra ID P1/P2 & Intune included (DEV-FAQ license list), but **eligibility is now restricted** (Visual Studio Pro/Enterprise standard subscribers, ISV Success / MAICPP partners, Premier/Unified Support); self-service sign-up by an arbitrary developer is no longer guaranteed; setup requires a billing account (no charge unless add-ons purchased); sandbox lasts ≤90 days, renewable on "qualified developer activity"; one per member; "development purposes only" (DEV-FAQ, join-with-VS page). **Therefore a RevocationGap test tenant cannot be assumed available to every contributor/CI.** |
| Alternatives | (U — not verified in fetched docs) a free/trial Entra tenant created outside the Developer Program would be Entra **Free**: Conditional Access authoring needs P1 (E-CA-OVERVIEW) so CAE/CA-policy scenarios would be untestable, and sign-in/audit retention is 7 days (E-RETENTION). Trial P1/P2 terms not fetched. If Security Defaults/MFA are enforced, ROPC automation is blocked (I, from E-ROPC). |
| Automated token acquisition | ROPC works only for cloud-managed, password-based, **non-MFA** users in Entra tenants (not personal accounts, not federated w/o special HRD policy); Microsoft recommends against it and warns that "test rigs relying on ROPC will be locked out" as MFA spreads (E-ROPC). Client-credentials flow works for app-only tokens (no refresh token). Interactive auth-code flow needs a browser (Authlib local loopback or Playwright). CAE needs `cp1` → MSAL (Python `msal` supports `client_capabilities`; E-DEVCAE). |
| Graph automation | All §1.8 calls are app-only capable with the listed permissions + admin consent; target test users that are **non-admin** to avoid extra role requirements. |
| Policy / ToS | MSRC Rules of Engagement: testing is allowed (and explicitly "encouraged": test accounts/trial tenants; "Evaluating conditional access … policies on Microsoft Intune") **within your own tenant/assets**; prohibited: DoS, "network-intensive fuzzing or automated testing that generates excessive traffic", accessing others' data, post-exploit actions (MSRC-ROE). RevocationGap's call volume must stay modest; developer-subscription terms restrict use to development. Third parties need written authorisation from the tenant owner (Learn pen-testing page, search excerpt). |
| Cost | $0 for E5 developer sandbox if eligible; otherwise paid P1 (≈ per-user) — price not verified. |
| CI feasibility | **Not feasible as a default CI job** (eligibility, 90-day expiry, MFA/ROPC friction, log latency minutes–hours, 1-day CA propagation). Recommend: Entra tests are *opt-in, manually triggered, user-supplied tenant* with credentials via env/secret store; CI uses recorded/simulated Entra behaviour (documented-semantics unit tests + the live discovery document). |
| Device compliance | Needs an enrolled device (real or VM) + Intune policy; **not CI-friendly**; model as "manual/out-of-scope or simulated". |
| Delay-sensitive tests | CAE ≤15 min, CA changes ≤1 day, log latency up to hours ⇒ a single revocation experiment takes tens of minutes to hours; budget with polling and explicit `inconclusive` classification. |

## 5. (e) Pitfalls for a revocation tester
1. **JWT still valid ≠ defect.** Entra's documented model: access tokens stay valid until `exp` (60–90 min default); only CAE-enabled *Microsoft* resources reject early. A custom API doing local validation will accept a revoked user's token for up to ~90 min (28 h for CAE-capable client+resource, but custom APIs are not CAE resources). Classify as *documented enforcement delay / expected semantics*.
2. **CAE only triggers if the client opted in (`cp1`) and the resource is CAE-enabled.** A test client without `cp1` never sees a claims challenge and gets 1 h tokens: a "no 401 after revoke" result is then *expected*, not a gap. Conversely test clients that don't handle `insufficient_claims` may retry the dead token and look broken (E-DEVCAE).
3. **Refresh-token behaviour**: old RTs are not invalidated on use (no rotation enforcement) — replaying a used RT succeeding is expected (E-RT). `revokeSignInSessions` has "a few minutes" lag — poll, do not single-shot.
4. **Disable vs revoke:** disabling blocks new issuance but doesn't kill refresh tokens' *existing access tokens*; the doc recommends both. Re-enabling has 15 / 35–40-minute downstream latency (E-CAE), so cleanup re-enable can cause confusing false negatives in the next test; use fresh users per case.
5. **Group/role claims are baked into tokens**; group removal propagates to CAE-aware RPs "up to one day" and to custom APIs only at next token (E-CAE). `groups` overage (large memberships → Graph lookup) alters what the API sees (U not fetched).
6. **IP-based CAE**: instant enforcement requires named locations of type IP only; country or MFA-trusted IPs → 1-h token without instant check; shared/undefinable egress breaks results (E-CAE). A tester running from CI behind NAT, VPN or IPv6 will see mismatches ("IP address (seen by resource)").
7. **Guest/B2B users** are not covered by CAE and their refresh tokens aren't revoked in the resource tenant (E-CAE, E-RT).
8. **Backup authentication** during outages can mint tokens that ignore fresh revocation (E-BACKUP) → mark inconclusive.
9. **Sign-in logs are a lagging oracle** (minutes–hours; non-interactive refresh sign-ins may not appear in v1.0 `signIns`); never use them as the time-of-event source — use Graph `signInSessionsValidFromDateTime` and own client timestamps.
10. **No revocation/introspection endpoints**: a generic-OIDC adapter must not attempt `/revoke` or `/introspect` for Entra; probing them yields 404 / unrelated native-auth 400 (V-live). The discovery doc lacks `revocation_endpoint`/`introspection_endpoint` — adapters should key capability off discovery, not off vendor name.
11. **Token versions & audiences**: v1 vs v2 tokens (`ver` claim; E-AT validates v2 with the `/v2.0` metadata, remove `/v2.0` for v1) and the `aud` form depend on the API registration (U exact rule not fetched); Graph tokens are proprietary/opaque to apps (E-AT: "you can't validate tokens for Microsoft Graph"). A tester that tries to decode/validate Graph tokens will misclassify.
12. **ROPC/Security Defaults/MFA**: tenants with security defaults or CA-MFA break password-grant automation (E-ROPC); distinguish `AADSTS` auth failures (interaction required) from revocation outcomes.
13. **Sovereign clouds / national endpoints** differ (`login.microsoftonline.us`, `.cn`); discovery per cloud (U).
14. **`xms_rl`** appears in the brief but is undocumented in what I could fetch — do not key logic on it.

## 6. (f) Open uncertainties (need a real tenant or further fetches)
- Exact observed time-to-401 at Microsoft Graph and a custom API after `revokeSignInSessions` and after `accountEnabled=false` for CAE vs non-CAE clients (docs give ceilings only).
- Whether Microsoft Graph (as RP) returns the `insufficient_claims` challenge for *delegated* tokens after `revokeSignInSessions` within minutes for a plain test app declaring `cp1` — documented in principle (E-CAE-W for workload, E-CAE for users) but not verified by me.
- `xms_rl` (listed in task brief): no documentation found.
- Exact `AADSTS` error codes and `error_description` text returned by `/token` for refresh after revoke / disabled user / password reset (not fetched).
- Whether Entra offers back-channel logout for OIDC/SAML apps (app-registration `logoutUrl` semantic: front-channel only?) — not verified.
- Whether third-party/custom resource APIs can opt into CAE/critical-event feeds (docs describe only Microsoft resources).
- SSF/CAEP transmit/receive: no primary source found either way.
- `directoryAudits` event names and latency for accountEnabled/revoke/group/app-role changes (not fetched).
- Non-interactive/service-principal sign-in log retrieval via Graph v1.0 vs beta; presence of CAE flag fields in v1.0 `signIn` (v1.0 resource page lists no CAE property).
- Developer-program eligibility for individual contributors; trial P1 terms; whether CA policy writes via Graph work in Entra Free trial tenants (docs say P1 required).
- Intune compliance automation (policy assignment, virtual device enrolment) — only resource-type docs fetched.
- Disabled-user token behaviour for *application permissions* (app-only) after service-principal disable outside Graph (E-CAE-W covers only Graph RP).
- National-cloud differences; B2B/guest nuances; `groups` overage claim behaviour.
