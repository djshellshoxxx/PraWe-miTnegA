# Keycloak — revocation / session / token-invalidation behaviour and admin API surface
Draft for `docs/02-RESEARCH/providers/KEYCLOAK.md` · researched 2026-10-12 · author: providers-a agent

**Current stable at access date: Keycloak 26.8.0 (released 2026-10-01)** — [K-REL]; only the latest minor is supported (26.7 EOL 2026-10-01 per third-party tracker eosl.date; Keycloak itself publishes no EOL dates). Container tag: `quay.io/keycloak/keycloak:26.8.0` [K-DOCKER].

## 0. Evidence legend (every row below carries one)
| Tag | Meaning |
|---|---|
| **V-doc** | stated in an official page fetched this session (URL in legend) |
| **V-src** | read in Keycloak source at git tag `26.8.0` (github.com/keycloak/keycloak) |
| **V-lab** | observed by me on a real Keycloak 26.8.0 (`start-dev`, H2, single node, localhost) — scripts in `lab/`, fixtures in `fixtures/` |
| **I** | inferred from the above, not directly observed |
| **U** | unverified / not found in primary sources |

**Important scope limit of V-lab:** single node, persistent-user-sessions (default in 26.8), HTTP, no reverse proxy, no cluster. Nothing in this file proves multi-node propagation timing.

Source IDs (full list with versions in `SOURCES.md`):
- K-REL https://www.keycloak.org/2026/10/keycloak-2680-released
- K-ADM https://www.keycloak.org/docs/latest/server_admin/index.html (26.8.0) — sections "Managing user sessions", "Session and token timeouts", "Offline access", "OIDC Logout", "Event listener"
- K-REST https://www.keycloak.org/docs-api/latest/rest-api/index.html
- K-OIDC https://www.keycloak.org/securing-apps/oidc-layers
- K-TX https://www.keycloak.org/securing-apps/token-exchange
- K-SSF https://www.keycloak.org/securing-apps/ssf-support
- K-CACHE https://www.keycloak.org/server/caching
- K-HEALTH https://www.keycloak.org/observability/health
- K-IMP https://www.keycloak.org/server/importExport
- K-CONT https://www.keycloak.org/server/containers
- K-DOCKER https://www.keycloak.org/getting-started/getting-started-docker
- K-UPG https://www.keycloak.org/docs/latest/upgrading/index.html
- K-FEAT https://www.keycloak.org/server/features
- SRC = `https://github.com/keycloak/keycloak/blob/26.8.0/` + path (paths given per row; `services/src/main/java/org/keycloak/...` abbreviated `svc/`)

---
## 1. (a) Verified behaviour

### 1.1 Token / session lifetimes — realm defaults (V-lab: `GET /admin/realms/{realm}` on a fresh realm, 26.8.0)
| Setting (RealmRepresentation field) | Default | UI name / notes | Source |
|---|---|---|---|
| `accessTokenLifespan` | 300 s | "Access Token Lifespan" | V-lab; names V-doc K-ADM "Tokens tab" |
| `accessTokenLifespanForImplicitFlow` | 900 s | implicit flow only | V-lab |
| `ssoSessionIdleTimeout` | 1800 s | "SSO Session Idle"; refreshed by auth or refresh-token request | V-lab, K-ADM |
| `ssoSessionMaxLifespan` | 36000 s | "SSO Session Max" | V-lab, K-ADM |
| `ssoSessionIdleTimeoutRememberMe` / `…MaxLifespanRememberMe` | 0 (= use non-remember values) | only if Remember-me enabled | V-lab, K-ADM |
| `clientSessionIdleTimeout` / `clientSessionMaxLifespan` | 0 (= inherit SSO values) | per-client override in client Advanced tab; "should be shorter than SSO" | V-lab, K-ADM |
| `offlineSessionIdleTimeout` | 2 592 000 s (30 d) | offline token must be used at least this often | V-lab, K-ADM |
| `offlineSessionMaxLifespanEnabled` / `offlineSessionMaxLifespan` | false / 5 184 000 s (60 d) | max only applies when Enabled | V-lab, K-ADM |
| `clientOfflineSessionIdleTimeout` / `clientOfflineSessionMaxLifespan` | 0 | client override; Max only honoured if realm flag enabled | V-lab, K-ADM |
| `revokeRefreshToken` | false | "Revoke Refresh Token" (rotation) | V-lab |
| `refreshTokenMaxReuse` | 0 | extra reuses allowed when rotation on | V-lab |
| `accessCodeLifespan` / `…Login` / `…UserAction` | 60 / 1800 / 300 s | auth-code & login-flow timers | V-lab |
| `notBefore` | 0 | realm "Revocation" policy timestamp (epoch **seconds**) | V-lab |
| `eventsEnabled`, `adminEventsEnabled` | false, false | must be enabled for event telemetry | V-lab |
| `sslRequired` | `external` | HTTP allowed only from private/localhost; set `none` for lab | V-lab |

- Refresh-token `exp` tracks session limits: with idle=1800 `refresh_expires_in`=1800; with idle=60 → 60 (V-lab). Offline RT `exp` ≈ now+30 d (V-lab).
- Access token lifetime is independent of session state: a 3600 s AT stays *locally* valid after its session is gone (V-lab, all scenarios below).
- **No idle grace window** observed on 26.8.0: with SSO idle=60 s, introspection flipped to `active:false` and the session vanished from `GET /users/{id}/sessions` between t+10 s and t+65 s (V-lab exp7c; not bisected further). K-ADM documents a 2-minute window "only … if persistent user sessions are not active"; V-src `AuthenticationManager.isSessionValid` applies the window only when feature `persistent-user-sessions` and `clusterless` are both off. Volatile sessions are deprecated since 26.8 (K-CACHE).

### 1.2 What happens to *already-issued* tokens after each event (V-lab unless noted; "local JWT" = signature+exp+iss check only)
Setup: password-grant login (client `tester`, AT lifespan 3600 s), audience mapper adds resource-server client `rs` to `aud`, introspection by `rs`. Each row is one fresh login → action → observe.

| Event / admin call | Local JWT verification | `POST …/token/introspect` | `GET …/userinfo` | Refresh token | Other observed effects |
|---|---|---|---|---|---|
| **Disable user** `PUT /users/{id} {"enabled":false}` | still valid until `exp` | `{"active":false}` (event `user_disabled`) | 401 | `invalid_grant` "User disabled" | Session **stays** in `GET /users/{id}/sessions`; new login "Account disabled"; **re-enabling revives the same AT and RT** (introspect true again, refresh 200). No backchannel-logout (BCL) sent (V-lab exp4). |
| **Delete session** `DELETE /sessions/{sid}` (offline: `?isOffline=true`) | valid until exp | inactive (`user_session_not_found`) | 401 | "Session not active" | BCL sent to client `backchannel.logout.url` in ≈35 ms (logout_token with `sid`). No CAEP SET (see §1.6). |
| **Logout user** `POST /users/{id}/logout` (**POST, not DELETE**) | valid until exp | inactive | 401 | "Session not active" | Sets **user `notBefore`=now** (seconds) then removes all *online* sessions; BCL sent; CAEP session-revoked SET emitted. |
| **Remove realm role** `DELETE /users/{id}/role-mappings/realm` | AT still embeds role | **active:true, and `realm_access.roles` shows the *current* roles (removed role gone)** | 200 | 200; **new AT has role removed** | Session untouched; no BCL; no SSF event. |
| **Remove group membership** `DELETE /users/{id}/groups/{gid}` | AT still embeds group role | active:true; roles recomputed (group role gone) | 200 | 200; new AT without group role | as above |
| **Admin password reset** `PUT /users/{id}/reset-password` | valid | **active:true** | 200 | **200** (RT keeps working) | Old password rejected for new logins; existing sessions/tokens NOT invalidated; CAEP credential-change SET emitted. |
| **Realm not-before** `PUT /admin/realms/{realm} {"notBefore":<epoch s>}` | valid until exp | inactive | 401 | "Stale token" | Applies to every token with `iat < notBefore`. |
| **`POST /admin/realms/{realm}/push-revocation`** | n/a | n/a | n/a | n/a | Returns 200 `{}`. **Does not set not-before**; only notifies clients that have an Admin URL (V-src `RealmAdminResource.pushRevocation` → `ResourceAdminManager.pushRealmRevocationPolicy`). |
| **`POST /admin/realms/{realm}/logout-all`** | valid | inactive | 401 | "Session not active" | **No OIDC backchannel logout token sent** (V-lab: 0 hits at BCL receiver); only clients with legacy Admin URL are notified (V-src). Does not set not-before. |
| **Revoke access token** `POST /revoke` (`token_type_hint=access_token`) | valid | that `jti` inactive | 401 | **RT of same session still refreshes (200)** and yields a fresh valid AT | Other sessions' ATs unaffected. jti stored for `max(exp-now+1,10)` s (V-src `TokenRevocationEndpoint.revokeAccessToken`). |
| **Revoke refresh token** `POST /revoke` (`refresh_token`) | valid | **all ATs of that client session inactive** (`user_session_not_found`) | 401 | "Session not active" | Client session detached; user session removed if it was the last client (V-src `DefaultRefreshTokenProvider.revokeToken`). Also revokes user consent for the client (V-doc K-OIDC). |
| **RT reuse, rotation on** (`revokeRefreshToken=true`, maxReuse 0) | valid | after replay: **both old and new ATs of that session inactive** | 401 | replay of used RT → `invalid_grant` "Maximum allowed refresh token reuse exceeded"; the *legitimate newest* RT then fails "Session doesn't have required client" | Reuse detection **detaches the client session** (family kill) (V-src `AbstractRefreshTokenProvider.validateTokenReuseForRefresh`, V-lab). With `refreshTokenMaxReuse=2`: statuses [200,200,200,400] for 4 uses of the same RT. |
| **Delete user** `DELETE /users/{id}` | valid | inactive | 401 | "Session not active" | CAEP/RISC `account-purged` SET emitted (admin API only). |
| **Offline token** (scope `offline_access`) vs `POST /users/{id}/logout` | valid | **inactive if offline RT `iat` < user notBefore; active if issued in the same wall-clock second** | 401 / 200 resp. | "Stale token" / 200 resp. | **Same-second boundary** (see §5). Online-only session removal does not remove the offline session. |
| Offline token vs RP-initiated `GET /logout?id_token_hint=` | valid | **active** | 200 | **200** | Matches K-ADM "offline token is valid after a user logout". |
| Offline token vs `DELETE /sessions/{sid}` without `isOffline=true` | valid | active | 200 | 200 | `DELETE` returned **404** because the login created only an *offline* session — must pass `?isOffline=true`. |
| Offline token vs `DELETE /sessions/{sid}?isOffline=true` | valid | inactive | 401 | "Offline user session not found" | |
| Offline token vs disable user | valid | inactive | 401 | "User disabled" | |
| Offline token vs realm notBefore | valid | inactive | 401 | "Stale token" | |
| Offline token vs `DELETE /users/{id}/consents/{clientId}` | valid | inactive | 401 | "Offline user session not found" | revokes the offline session. |
| Offline token vs removing realm role `offline_access` from user | valid | inactive | n/t | "Offline session invalid because offline access not granted anymore" | V-lab + V-src. |
| **Session idle expiry** (idle=60 s) | valid | inactive | 401 | "Token is not active" / session not active | see §1.1 |
| **Client-credentials AT** (service-account, **no `sid`**, no RT) | valid | active; **flips inactive if service-account user disabled, client disabled, or realm notBefore advanced**; **stays active after `POST /users/{sa}/logout`** | n/t | none issued | Session-less tokens are not killed by session logout. Same holds for token-exchange *delegation* tokens (transient session, no `sid`) (V-doc K-TX). |
| **Natural expiry** | `exp` | `active:false` right after `exp` (t+11 s with 10 s lifespan) | 401 | — | V-lab exp7 |

Source-level confirmation of the mechanics (V-src, tag 26.8.0):
- Introspection (`svc/protocol/oidc/AccessTokenIntrospectionProvider.java`): signature → client enabled + realm/client not-before + `IS_ACTIVE` + `revokedTokens` jti check → *online/offline user-session lookup* (`svc/util/UserSessionUtil.findValidSession`) → `TokenManager.isUserValid` (user exists, `isEnabled()`, **user** not-before) → offline-access still granted → audience check.
- Userinfo (`svc/protocol/oidc/endpoints/UserInfoEndpoint.java`): same family (realm/client not-before, revoked jti, session, `userModel.isEnabled()`, `validateUserNotBefore`). Requires `openid` scope in the token.
- Refresh (`TokenManager.validateToken` + `AbstractRefreshTokenProvider`): session valid, user enabled, client session valid, realm+client+**user** not-before ("Stale token"), consent still present, offline access still granted; roles/groups are recomputed into the new AT (→ role removal takes effect at next refresh).
- `NotBeforeCheck.test`: `if (t.getIat() < notBefore) throw` — strict `<` on **integer seconds** ⇒ tokens whose `iat` equals the not-before second **survive** (V-lab confirmed on both realm and user level).
- Session-less tokens: `findValidSession` with `token.getSessionId()==null` and a session type that allows transient sessions returns a transient session instead of an error ⇒ client-credentials / delegation tokens only depend on user-enabled + not-before + client state.

### 1.3 Endpoint semantics (paths relative to `/realms/{realm}/protocol/openid-connect/`)
| Endpoint | Verified behaviour | Source |
|---|---|---|
| `token/introspect` | Confidential client auth only. Returns RFC 7662 body; **inactive → only `{"active":false}`** (no reason; reason only in server events). **Since 26.6.2 the authenticated (introspecting) client must be in the token's `aud`, else `active:false`**; opt-out attribute `allow-token-introspection-without-audience-check` (server-wide or per client) is deprecated. Active response claims depend on mappers flagged "Add to token introspection". Response reflects *current* user roles, not the token's embedded roles. | V-doc K-OIDC, K-UPG "Migrating to 26.6.2"; V-lab; V-src |
| `userinfo` | Bearer AT; 401 with empty body on any failure; requires `openid` scope. | V-lab, V-src |
| `revoke` (RFC 7009) | Client-authenticated; accepts access and refresh tokens; token must be issued to the authenticated client else 400 "Unmatching clients"; undecodable token → **HTTP 200 with an `invalid_token` error body** (V-src `TokenRevocationEndpoint.checkToken`, status OK by design). Success → 200 empty. Discovery advertises `revocation_endpoint`. | V-doc K-OIDC; V-src; V-lab |
| `logout` | RP-initiated (`id_token_hint`, `client_id`, `post_logout_redirect_uri`) → ends SSO session, sends BCL/front-channel; direct `POST` with `refresh_token`+client creds is a **legacy non-standard** form (works: 204, session killed) not recommended by docs. | V-doc K-OIDC/K-ADM; V-lab |
| Backchannel logout (client attrs `backchannel.logout.url`, `backchannel.logout.session.required`, `backchannel.logout.revoke.offline.tokens`) | Keycloak POSTs `application/x-www-form-urlencoded logout_token=<JWT>`; observed claims: `iss, aud=<client>, sub, sid, jti, iat, exp(=iat+120 s), typ:"Logout", events:{"http://schemas.openid.net/event/backchannel-logout":{}}`. Fired by: admin `POST users/{id}/logout`, `DELETE sessions/{sid}`, RP-initiated logout. **Not** fired by: disable user, role/group removal, password reset, `logout-all`, not-before. If no BCL URL and no Admin URL, nothing is sent (V-doc). | V-lab (exp4), V-doc K-ADM "OIDC Logout" |
| Discovery `/.well-known/openid-configuration` | Advertises `introspection_endpoint`, `revocation_endpoint`, `end_session_endpoint`, `backchannel_logout_supported:true`, `backchannel_logout_session_supported:true`, `frontchannel_logout_supported:true`, `check_session_iframe`, `jwks_uri`, `pushed_authorization_request_endpoint`, grant types incl. token-exchange, jwt-bearer, device_code, CIBA. | V-lab |
| `certs` (JWKS) | Local-validation keys. K-CACHE: the server's local key cache (for *external* keys) expires hourly by default; RS client libraries choose their own JWKS cache TTL (a stale JWKS cache matters only for key rotation, not revocation). | V-doc K-OIDC, K-CACHE |
| `token` grant `urn:ietf:params:oauth:grant-type:token-exchange` | Standard token exchange V2 is **on by default**; client must enable "Standard token exchange" and be confidential; never creates a new user session; revoking access-token1 does **not** revoke the exchanged access-token2, but does revoke exchanged refresh tokens/client session chain. | V-doc K-TX (sections "Revocation") |

### 1.4 Admin REST API — exact calls (base `/admin/realms/{realm}`; bearer = admin token; empirical permission matrix V-lab exp8 using service accounts holding exactly one realm-management role)
| Action | Call | Body | OK status | Minimum `realm-management` role (V-lab) |
|---|---|---|---|---|
| Admin token | `POST /realms/master/protocol/openid-connect/token` `grant_type=password client_id=admin-cli …` **or** client_credentials of a client whose service account holds roles (preferred; fixture `rg-admin`) | form | 200 | — |
| Create user | `POST /users` | `{"username","enabled":true,"email","firstName","lastName","emailVerified":true,"credentials":[{"type":"password","value":"…","temporary":false}]}` (`{"username","enabled"}` alone also accepted) | 201 + `Location: …/users/{id}` | `manage-users` |
| Find user | `GET /users?username=&exact=true` | — | 200 | `manage-users` ✔ (`view-users` also 200; `manage-realm` 403) |
| Disable / enable | `PUT /users/{id}` | `{"enabled":false}` (partial body OK) | 204 | `manage-users` |
| List user sessions | `GET /users/{id}/sessions` → `[ {id,username,userId,ipAddress,start,lastAccess,clients:{uuid:clientId}} ]` (epoch **ms**); offline: `GET /users/{id}/offline-sessions/{clientUuid}`; per client: `GET /clients/{uuid}/user-sessions`, `/offline-sessions`, `/session-count` | — | 200 | `view-users` |
| Kill all online sessions of user (+ user not-before=now) | `POST /users/{id}/logout` | none | 204 | `manage-users` |
| Kill one session | `DELETE /sessions/{sessionId}?isOffline=false\|true` | none | 204 / 404 | `manage-users` |
| Kill all realm sessions | `POST /logout-all` | none | 200 `GlobalRequestResult` | `manage-users` (V-src `auth.users().requireManage()`) |
| Set realm not-before | `PUT /` (realm root) | `{"notBefore": <epoch s>}` (partial update OK; `0` clears) | 204 | `manage-realm` |
| Push revocation to adapters | `POST /push-revocation`; client-level `POST /clients/{uuid}/push-revocation` | none | 200 | `manage-realm` (realm) / `manage-clients` (client; V-src) |
| Client not-before | `PUT /clients/{uuid}` `{"notBefore":…}` | | 204 | `manage-clients` (I) |
| Remove realm role mapping | `DELETE /users/{id}/role-mappings/realm` | `[{"id","name"}]` | 204 | `manage-users` |
| Remove client role mapping | `DELETE /users/{id}/role-mappings/clients/{client-uuid}` | `[RoleRepresentation]` | 204 | `manage-users` (I; same code path) |
| Remove group role mapping | `DELETE /groups/{gid}/role-mappings/realm` (or `/clients/{uuid}`) | `[RoleRepresentation]` | 204 | `manage-users` (I) |
| Remove group membership | `DELETE /users/{id}/groups/{groupId}` (add: `PUT …`) | none | 204 | `manage-users` |
| Reset password | `PUT /users/{id}/reset-password` | `{"type":"password","value":"…","temporary":false}` | 204 | `manage-users` |
| Revoke consent / offline grant | `DELETE /users/{id}/consents/{clientId}` | none | 204 | `manage-users` (V-src `requireManage(user)`) |
| Delete user | `DELETE /users/{id}` | none | 204 | `manage-users` (V-src) |
| Read login events | `GET /events?type=&user=&client=&dateFrom=&dateTo=&first=&max=` | — | 200 | `view-events` |
| Read admin events | `GET /admin-events?operationTypes=&resourceTypes=&resourcePath=&dateFrom=&dateTo=&max=` | — | 200 | `view-events` |
| Configure events | `GET/PUT /events/config` (`eventsEnabled, eventsListeners, enabledEventTypes, adminEventsEnabled, adminEventsDetailsEnabled`) | | 200/204 | `view-events` read ✔; write `manage-events` (I) |
| Client for SSF receiver | see §1.6 | | | |
Negative results (V-lab): `manage-users` gets 403 on realm PUT, push-revocation, all events endpoints; `view-users` gets 403 on every mutation; `manage-realm` alone cannot read users; `view-events` alone cannot read users/sessions. **Lab-grade least privilege for a RevocationGap "actor" identity = `manage-users` + `manage-realm` (+ `view-events`)**; for the *observer* identity = `view-users` + `view-events`.
Doc shorthand check: the task brief mentioned `DELETE /users/{id}/logout`; the REST reference and source (`UserResource.logout`, `@POST`) show it is **`POST`** [K-REST "POST /admin/realms/{realm}/users/{user-id}/logout"].

### 1.5 Events, listeners, timestamps (V-lab unless noted)
- Login/user events (`GET /events`) carry `time` = server epoch **ms**, `type`, `userId`, `sessionId`, `clientId`, `ipAddress`, `error`, `details{reason, token_id, grant_type…}`. Admin events carry `time`, `operationType` (CREATE/UPDATE/DELETE/ACTION), `resourceType`, `resourcePath`, `representation` (when "include representation" on) and `authDetails`.
- **Default stored event types do NOT include** `REFRESH_TOKEN(_ERROR)`, `INTROSPECT_TOKEN(_ERROR)`, `USER_INFO_REQUEST(_ERROR)`; default set contains LOGIN, LOGOUT, CODE_TO_TOKEN, CLIENT_LOGIN, REVOKE_GRANT, UPDATE_PASSWORD, RESET_PASSWORD… A tester must `PUT /events/config` to add the observation types; `REFRESH_TOKEN_ERROR`/`INTROSPECT_TOKEN_ERROR` carry a human `reason` (e.g. "User disabled", "Client 'rs' is not in the token audience", "Maximum allowed refresh token reuse exceeded") and error code (`user_disabled`, `user_session_not_found`, `invalid_token`) — the **only** way to learn *why* an introspection returned `active:false`.
- Delay between API action and event visibility: events written synchronously in the request transaction; observed event→action offsets of 30–40 ms (V-lab). Admin-event `DELETE USER_SESSION` for session deletes; `UPDATE USER` for disable; `ACTION USER` for logout/reset-password; `DELETE GROUP_MEMBERSHIP`, `DELETE REALM_ROLE_MAPPING`.
- Built-in listeners: `jboss-logging` (log category `org.keycloak.events`; errors at WARN, success at DEBUG unless `--spi-events-listener--jboss-logging--success-level=info`) and `email` [V-doc K-ADM "Event listener"]. Server log line format observed: `type="INTROSPECT_TOKEN_ERROR", realmName=…, clientId=…, userId=…, sessionId=…, error="user_disabled", reason="…", token_id=…` with ms timestamp (V-lab).
- Event store export: realm export does **not** include events, persisted sessions or revoked tokens (V-doc K-IMP).
- Custom SPI event listeners are possible (`EventListenerProvider`) — V-doc K-ADM; not exercised.

### 1.6 Shared Signals (SSF / CAEP / RISC) — **native, transmitter only, experimental**
(V-doc K-SSF + K-REL; V-lab exp6b). *Conflicts with third-party blog posts (andrewdoering.org, 2026) that say Keycloak has no native SSF transmitter — those are stale relative to 26.7/26.8; I trust the vendor docs + lab.*
- Feature flag `--features=ssf` ("experimental … Do not use this feature in production environments" K-SSF). CAEP session & credential events shipped in 26.7; RISC account-disabled/-enabled added in 26.8 (K-REL). **Keycloak is a Transmitter only** ("Keycloak plays the Transmitter role") — no receiver.
- Enable per realm: realm attribute `ssf.transmitterEnabled=true` (else 404). Discovery: `GET /realms/{realm}/.well-known/ssf-configuration` (V-lab 200; JSON has `delivery_methods_supported` [RFC 8935 push, RFC 8936 poll + legacy RISC URIs], `configuration_endpoint`, `status_endpoint`, `add_subject_endpoint`, `remove_subject_endpoint`, `verification_endpoint`, `default_subjects:"NONE"`).
- Receiver = ordinary OIDC client with attribute `ssf.enabled=true` (+ `ssf.defaultSubjects=ALL|NONE`, `ssf.validPushUrls`); scopes `ssf.read`,`ssf.manage` auto-created at enable and must be assigned as optional scopes to the receiver client. Receiver registers stream: `POST /realms/{realm}/ssf/transmitter/streams` body `{"delivery":{"method":"urn:ietf:rfc:8936"},"events_requested":[…],"description":"…"}` → 201 with `stream_id` and generated poll URL `…/ssf/transmitter/receivers/{clientId}/streams/{streamId}/poll`. Poll: `POST <poll-url>` `{"maxEvents":50,"returnImmediately":true,"ack":[jti…]}` → `{"sets":{jti: <JWS SET>},"moreAvailable":bool}`. Long-polling parsed but **not honoured** (always immediate) (V-doc).
- I had to add `ssf-events` to the realm's `eventsListeners` for SETs to flow (Keycloak's own integration tests do the same); whether the Admin-UI "Realm settings → SSF" toggle adds it automatically is **U**.
- **Observed SET emission** (V-lab, poll delivery, default_subjects ALL, SET `iat` has 1-s granularity):
  | Trigger | SET emitted? | Details |
  |---|---|---|
  | `POST /users/{id}/logout` | **Yes** CAEP `session-revoked` | `sub_id` = complex{user iss_sub, session opaque `ALL`}; `initiating_entity:"user"`, `reason_admin.en:"User logout"` even though an **admin** did it (mislabelled) |
  | RP-initiated `GET /logout` | **Yes** `session-revoked` | session id = actual sid |
  | `DELETE /sessions/{sid}` | **No** | admin-event only, no user LOGOUT event |
  | `PUT /users/{id} enabled=false` | **Yes** RISC `account-disabled` | `reason:"disabled-by-admin"`, `initiating_entity:"admin"` |
  | `PUT …/reset-password` | **Yes** CAEP `credential-change` | `change_type:"update"`, `credential_type:"password"` |
  | role mapping removal / group membership removal | **No** | no SSF event type exists for authorization changes |
  | `DELETE /users/{id}` | **Yes** RISC `account-purged` | admin API / account console only (K-SSF) |
  | not-before PUT, `/revoke`, refresh-token reuse | **not tested** (U) |
- Delivery caveats: PUSH uses an outbox drained every 30 s by default (`outbox-drainer-interval`), 8 attempts with exponential backoff then DEAD_LETTER (kept 30 d); push URLs must be https and non-loopback unless `allow-insecure-push-targets`; POLL has no drain delay. Admin can inject synthetic events (`POST /admin/realms/{realm}/ssf/clients/{clientId}/events/emit`).
- Experimental ⇒ event structure "revised" in 26.8 (K-REL): adapters must pin 26.8.x and version-gate.

### 1.7 Resource-server validation models and what they imply
| Model | Keycloak guidance | Consequence for revocation |
|---|---|---|
| Local JWT verify (JWKS `certs`) | K-OIDC "Validating access tokens": tokens are JWS and "you can locally validate"; downside of introspection is a network call per request. | Access stays possible until `exp` after disable / delete / logout / role removal / password reset / not-before / token revoke (V-lab). **This is expected protocol semantics**, documented: K-ADM says "Sign out all active sessions does not revoke outstanding access tokens. Outstanding tokens must expire naturally." Only a not-before check by the RS itself (legacy adapter) helped; modern libraries don't. |
| Introspection (`token/introspect`) | Required for any state-aware check | Reflects disable/delete/logout/session expiry/not-before/jti revocation/role changes **immediately on a single node** (V-lab); needs the RS client in `aud` (≥26.6.2); returns no reason. |
| `userinfo` as validity probe | not documented as a validator | behaves like introspection for state checks (V-lab) but returns 401 with empty body; needs `openid` scope. |
| Lightweight access tokens | feature of client scope/policy | introspection can return the full claims; `use-lightweight-access-token` is ignored by exchange in older versions (fixed in 26.8 notes) — U for impact. |
| DPoP / mTLS-bound tokens | https://www.keycloak.org/securing-apps/dpop (fetched, not analysed in depth) | binding does not change revocation timing (I). |

### 1.8 Operational facts for the lab
- Docker quick start (V-doc K-DOCKER): `docker run -p 127.0.0.1:8080:8080 -e KC_BOOTSTRAP_ADMIN_USERNAME=admin -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin quay.io/keycloak/keycloak:26.8.0 start-dev`. (Docker daemon was **not available** in my sandbox, so I ran the identical 26.8.0 zip distribution: `bin/kc.sh start-dev` — start ≈13 s, ~16 GB host not stressed; Java 21.)
- `start-dev`: H2 file DB, HTTP enabled, relaxed hostname; K-CONT: "strictly avoided in production … insecure defaults". Production: `start` (+ `--hostname`, TLS or `--http-enabled`, DB, proxy settings) K-PROD/K-CONT. Management interface (health/metrics) on **port 9000** by default (K-HEALTH); health enabled via build option `--health-enabled=true`; endpoints `/health/started`, `/health/live`, `/health/ready`, `/health` returning 200/503 JSON (V-doc; V-lab `GET :9000/health` → `{"status":"UP",…}`).
- Realm import fixtures (V-doc K-IMP): put `<realm>-realm.json` into `/opt/keycloak/data/import` (container) or `data/import` and start with `--import-realm` (strategy IGNORE_EXISTING). **Verified with `fixtures/revocationgap-lab-realm.json`** (realm `rgap`: client `rg-tester` (direct grants + audience mapper → `rg-rs`), resource server `rg-rs`, actor `rg-admin` service account with realm-management roles, user `rg-alice`, roles `rg-direct`/`rg-group`, group `rg-g1`, events incl. REFRESH/INTROSPECT/USERINFO enabled). Imported users get no `default-roles-*`/`offline_access` composite — add `offline_access` role explicitly for offline-token tests.
- Features: `token-exchange-standard:v2` default-on, `persistent-user-sessions:v1` default-on, `stateless:v1` off by default (promoted to supported in 26.8; DB-as-source-of-truth), `ssf:v1` experimental/off, `logout-all-sessions:v1` deprecated ("logs out only regular sessions") (K-FEAT).
- **Clock/Date**: **Keycloak 26.8.0 `start-dev` responses carry no `Date` header** (V-lab on discovery, token, JWKS endpoints). Do not rely on `Date` for server-time; behind a proxy it may be added (U).

### 1.9 Measuring server-side time (recipe)
1. Event `time` (epoch ms, server clock) from `GET /events` / `GET /admin-events` for the *action* and for each *observation* request (needs the event types enabled, §1.5).
2. `iat` / `exp` / `auth_time`: integer seconds from the server clock. **`auth_time` was absent** from password-grant tokens (V-lab); expect it on browser/auth-code logins (I). A freshly minted token's `iat` is a free server-clock probe (1-s resolution).
3. Session `start` / `lastAccess` in `GET /users/{id}/sessions` (ms).
4. Client-side: record monotonic send/receive times around each request; estimate offset = server event `time` − midpoint of the request.
5. BCL receiver: arrival time vs action time measured on one clock (lab: ≈33–37 ms on localhost).

---
## 2. (b) Adapter capability matrix

### 2.1 Revocation / state-change actions ("actor" role)
| Capability | Call | Privilege | Takes effect for | Side effects the adapter must record |
|---|---|---|---|---|
| create user / set password | `POST /users` | manage-users | n/a | user id from `Location` |
| disable / re-enable user | `PUT /users/{id}` | manage-users | introspect/userinfo/refresh immediately (single node); local JWT unaffected | session persists; re-enable resurrects tokens |
| end all online sessions (+user not-before) | `POST /users/{id}/logout` | manage-users | online AT (introspect), RT, offline tokens issued **before** the current second | BCL to clients with `backchannel.logout.url`; CAEP SET |
| end one session | `DELETE /sessions/{sid}[?isOffline=true]` | manage-users | that session | BCL; no SET |
| end all sessions of realm | `POST /logout-all` | manage-users | online sessions | no BCL (V-lab) |
| set realm not-before | `PUT /` `{"notBefore":now}` | manage-realm | all tokens with `iat<now` incl. offline, client-credentials | none; push needed only for adapters |
| remove role / group role mapping / membership | `DELETE …/role-mappings/…`, `DELETE /users/{id}/groups/{gid}` | manage-users | next refresh (new AT); introspection immediately reflects roles | no logout; embedded roles in old AT remain |
| admin password reset | `PUT /users/{id}/reset-password` | manage-users | new logins only | existing tokens/sessions unaffected; CAEP credential-change |
| revoke token (client-side) | `POST /revoke` (client creds) | confidential client | AT jti (introspect/userinfo only) or whole client session (RT) | consent revoked on RT revoke |
| revoke consent/offline grant | `DELETE /users/{id}/consents/{client}` | manage-users | offline session | — |
| delete user | `DELETE /users/{id}` | manage-users | all | `account-purged` SET |
| client disable | `PUT /clients/{uuid}` `{"enabled":false}` | manage-clients | introspect inactive for that client's tokens (V-lab for `rs` CC token) | — |
| token exchange (to create derived tokens) | `grant_type=…token-exchange` | client with "Standard token exchange" | derived token follows subject session; AT2 not revoked by revoking AT1 | — |

### 2.2 Observation endpoints ("probe" role) — what the adapter may call *as the post-change access attempt*
| Probe | Auth | Distinguishes | Cost/limits |
|---|---|---|---|
| RS call with AT (local JWT) | none | only `exp` | models real "RS with local validation" |
| `token/introspect` | confidential client in `aud` | active/inactive only | event `reason` needed for why |
| `userinfo` | AT | 200/401 | requires `openid` |
| `token` refresh grant | client + RT | precise `error_description` (User disabled / Session not active / Stale token / reuse exceeded / offline not granted) | **has side effects**: rotates RT if `revokeRefreshToken`, touches session idle, mints roles-refreshed AT. Use a dedicated probe token copy. |
| password/ROPC login | user creds | "Account disabled", "Invalid user credentials" | ROPC deprecated by RFC 9700; enable "Direct access grants" on lab client |
| `GET /users/{id}/sessions`, `/offline-sessions/…` | view-users | whether session exists (disable keeps it) | |
| `GET /users/{id}` | view-users | `enabled`, `notBefore` | |
| Realm `GET /` | manage-realm/view-realm | `notBefore`, lifespans | |

### 2.3 Event/telemetry sources and latency
| Source | Content | Latency (documented / observed) |
|---|---|---|
| `GET /events` | user/token events incl. errors with `reason` | synchronous; ms (V-lab); needs event types enabled |
| `GET /admin-events` | admin REST actions with representation | synchronous; ms (V-lab) |
| `jboss-logging` log lines | same events, WARN for errors | immediate |
| Backchannel-logout receiver (tester-hosted) | `logout_token` | 33–37 ms on localhost (V-lab); no documented SLA |
| SSF poll/push | SETs | poll: ≤1.5 s observed incl. my wait; push: outbox drainer default **30 s** (V-doc) |
| Prometheus/health on :9000 | metrics, readiness | n/a |

---
## 3. (c) Documented enforcement delays / propagation windows (document's own caveats)
- Access tokens are bearer JWTs; outstanding tokens expire naturally after "Sign out all active sessions" (K-ADM "Signing out all active sessions"). Pushing a not-before only reaches clients "with the Keycloak OIDC client adapter" and "does not work for other adapters" (K-ADM) — the legacy adapters are removed in current releases (K-UPG mentions legacy adapters removed) ⇒ push-revocation is effectively a no-op for modern RS (I).
- "Consider using Back-Channel Logout … more reliable" than front-channel; front-channel depends on browser/iframes/CSP (K-ADM). If no BCL/Admin URL, "Keycloak will not propagate logout to the client" and the app session "remains valid for the short time after Keycloak SSO session logout" until the short AT lifespan ends; the next refresh fails (K-ADM "OIDC Logout").
- Idle timeouts: "a two-minute window" applies only "if persistent user sessions are not active" (K-ADM) — not observed on 26.8 default (V-lab).
- Offline tokens: "valid after a user logout"; "never expires" but must be used within Offline Session Idle (30 d default) and optionally Offline Session Max (60 d) (K-ADM). Admin console can revoke via Consents tab or revocation policy.
- Caches: users/realms/clients/authorization/keys are **local caches per node**, invalidated through the replicated `work` cache whose "entries/messages … are very short-lived"; key cache expires every 1 h; session data is DB-backed with an embedded Infinispan cache (10 000 entries/node default) (K-CACHE). **No numeric cross-node propagation delay is documented** ⇒ treat as U; in `stateless` mode the DB is source of truth (K-CACHE).
- Token exchange: "the administrator must ensure that access tokens are short-lived" because revoking access-token1 does not revoke access-token2 (K-TX).
- SSF PUSH: ≥30 s outbox cycle + backoff (K-SSF). Experimental.
- "Remember me" disable: sessions invalidated lazily ("when a cookie or token associated with an invalid session is used, or asynchronously in the background") (K-ADM).
- Bug-tracker items in 26.8 release notes touching session/revocation consistency (K-REL): #51127 "cache-miss unconditionally re-hydrates cache from DB, resurrecting deleted sessions" (persistent sessions), #52038 "client session note removals not persisted". Treat session-delete-then-resurrect as a *known bug class* to look for (I).

## 4. (d) Lab / CI feasibility
- **Fully free, offline-capable:** Apache-2.0 server, single container (start-dev ≈13 s on 4 vCPU), no external services. Everything in §1 was reproduced with the zip distribution on a 4-vCPU/16 GB box. Recommended CI: `quay.io/keycloak/keycloak:26.8.0` pinned (digest-pin for reproducibility), `start-dev --import-realm --features=ssf --health-enabled=true`, wait on `:9000/health/ready`, import `fixtures/revocationgap-lab-realm.json`.
- ToS/cost: none; Quay anonymous pull rate limits (U). Docker was unavailable in my sandbox so the *container* path is untested by me (the distribution is identical).
- Determinism aids: set `accessTokenLifespan` realm to ≥ test duration (e.g. 3600) so natural expiry never masks a gap; or set it to 10–30 s to *test* natural-expiry classification.
- Multi-node/cluster behaviour (cache invalidation windows, stateless/multi-cluster) needs ≥2 nodes + shared DB — not covered; separate lab profile required.
- SSF needs `--features=ssf` at start/build; the SSF *receiver* side must be implemented by RevocationGap (poll delivery avoids needing an https push endpoint).
- Wall time: idle-timeout and expiry tests need real sleeps (≥ timeout); use small realm values (min allowed idle/lifespan accepted: 10 s lifespan and 60 s idle worked).

## 5. (e) Pitfalls causing false positives / false negatives
1. **Same-second not-before boundary (FN-for-tester / FP-for-defect):** `iat < notBefore` strict, integer seconds. A token minted in the same second as `POST /users/{id}/logout` or realm `notBefore` PUT remains valid — introspect true, offline refresh 200 (V-lab: gap 0 s → 200, gap 1.2 s → "Stale token"). Always wait ≥1 s (plus skew) between minting the probe token and issuing the revocation, and never mint "post-revocation control" tokens in the same second.
2. **Introspection `active:false` ≠ revoked.** Causes unrelated to revocation: introspecting client not in `aud` (≥26.6.2), wrong client auth, token expired, token not issued by this realm, client disabled, `iss` mismatch via hostname/frontend-URL. Baseline-check every probe token *before* the action with the same RS client (control row).
3. **Disable ≠ logout.** After `enabled=false` the session persists and re-enabling revives old tokens (V-lab). A tester that re-enables the user for cleanup can create a false "token works again" finding; use fresh users per scenario.
4. **Refresh probe side effects:** with rotation on, a probe refresh consumes the RT; a second probe is then a reuse event that **kills the session** (family kill) and contaminates later observations. Reuse detection also makes the *latest legitimate* RT fail. Without rotation, a probe refresh extends session idle time.
5. **Offline vs online:** `POST /users/{id}/logout` and `DELETE /sessions/{sid}` only touch online sessions unless `?isOffline=true`/not-before applies; offline tokens survive RP logout (documented). Login with `offline_access` creates *only* an offline session (so non-offline `DELETE` → 404).
6. **Session-less tokens** (client_credentials, delegation exchange) have no `sid`; session logout cannot kill them. Don't flag as defect (I).
7. **Role removal takes effect at next refresh, not at once, for local-JWT RS** — expected; introspection already shows new roles. Compare `realm_access` in introspection vs embedded token.
8. **Admin password reset does not revoke anything** (V-lab) although CAEP `credential-change` fires — classify as "expected Keycloak semantics / risky config" not vendor bug; Keycloak has a per-credential-change option only via Account console (U).
9. **`POST /push-revocation` does not set not-before** and `POST /logout-all` sends no BCL token — wrong mental model yields FN in "notified RP" checks.
10. **Event types missing by default** (REFRESH/INTROSPECT/USERINFO) ⇒ empty telemetry ≠ no request.
11. **No `Date` header** in dev responses; skew between tester and server clocks (1-s `iat` resolution) corrupts delay math.
12. **Experimental SSF**: `initiating_entity` mislabel for admin logout; poll long-poll ignored; `default_subjects` NONE default ⇒ no events unless the receiver client/ user is subscribed (set `ALL`).
13. Hostname/frontend-URL: issuer must match what the RS validates; in `start-dev` the issuer follows the request host (`localhost` vs `127.0.0.1` yield different `iss`) (I).
14. **Version drift:** introspection audience check (26.6.2), SSF event model (26.7→26.8), stateless/volatile sessions (deprecated 26.8) — pin version in every result record.

## 6. (f) Open uncertainties
- Multi-node (Infinispan/embedded or stateless/DB) propagation delay for user-disable, role removal, not-before: **no documented numbers**; needs a 2-node lab. (U)
- Whether the revoked-jti set (`/revoke` access token) replicates immediately across nodes / survives restart (providers `InfinispanRevokedTokenProvider`, JPA persister exist in source tree; behaviour not tested). (U)
- Exact minimum role for `POST /logout-all`, client-level role mapping removal, `PUT /clients/{uuid}` (inferred from source/same code path, not exercised). (I)
- Whether `ssf-events` listener is auto-registered by the Admin-UI SSF toggle. (U)
- SSF behaviour for not-before / `/revoke` / reuse-detection (no event expected; untested). (U)
- Browser-flow (authorization-code) `auth_time`, `sid`, SSO-cookie interactions with admin logout, front-channel logout, `login_hint`-driven re-auth, and CIBA/device flows: not exercised (all lab logins used direct grant). (U)
- Lightweight access tokens and `Accept: application/jwt` introspection, DPoP/mTLS-bound tokens: behaviour under revocation not tested. (U)
- Keycloak behind a reverse proxy: Date header, hostname/issuer. (U)
- Container image (not zip) start-up flags in CI (`--health-enabled` is build-time; requires `kc.sh build` or the optimized image workflow) — lab used `start-dev` which auto-builds. (U)
- FGAP v2 (fine-grained admin permissions) alters required permissions; lab used legacy role-based admin permissions only. (U)
