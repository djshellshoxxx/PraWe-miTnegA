# SOURCES — providers-a (Keycloak, Microsoft Entra ID)
Access date for everything: **2026-10-12**. "Fetched" = full page body retrieved and read this session (saved as text under `raw/`, HTML dropped). Page dates are the vendor's "Last updated" footer where present.
Fetch method: `web_fetch` where the URL had been surfaced by search; otherwise plain HTTP GET (curl) of the same public URL (sandbox has internet) — content identical, saved in `raw/`. Evidence tags are defined in KEYCLOAK.md / ENTRA-ID.md.

## A. Keycloak

### A1. Official documentation (version 26.8.0 unless noted)
| ID | URL | Version/date | Used for |
|---|---|---|---|
| K-REL | https://www.keycloak.org/2026/10/keycloak-2680-released | 26.8.0, 2026-10-01 | current version, SSF changes, stateless supported, token-exchange delegation, bug list |
| K-REL-search | https://www.keycloak.org/2026/09/keycloak-2674-released, …/2026/05/keycloak-2662-released, …/2026/04/keycloak-2660-released (web_search excerpts only; not fetched in full) | 26.7.4 / 26.6.2 / 26.6.0 | version history context |
| K-VER-3p | https://endoflife.date/keycloak, https://eosl.date/eol/product/keycloak/, https://www.versio.io/en/product-release-end-of-life-eol-keycloak-keycloak.html (search excerpts) | 2026-10 | support policy ("only latest minor") — third-party |
| K-DOCS | https://www.keycloak.org/documentation ; https://www.keycloak.org/guides | 26.8.0 | guide index |
| K-ADM | https://www.keycloak.org/docs/latest/server_admin/index.html | 26.8.0 | timeouts, sessions, offline, revocation, logout, events, roles |
| K-REST | https://www.keycloak.org/docs-api/latest/rest-api/index.html | 26.8.0 | exact admin paths |
| K-OIDC | https://www.keycloak.org/securing-apps/oidc-layers | 26.8.0 | endpoints (introspect, revoke, logout), validating tokens |
| K-TX | https://www.keycloak.org/securing-apps/token-exchange | 26.8.0 | token exchange v2 + revocation notes |
| K-SSF | https://www.keycloak.org/securing-apps/ssf-support | 26.8.0 | SSF transmitter, delivery, endpoints |
| K-CACHE | https://www.keycloak.org/server/caching | 26.8.0 | cache/invalidation, persistent/volatile/stateless sessions |
| K-HEALTH | https://www.keycloak.org/observability/health | 26.8.0 | health endpoints |
| K-IMP | https://www.keycloak.org/server/importExport | 26.8.0 | realm import/export, `--import-realm` |
| K-CONT | https://www.keycloak.org/server/containers | 26.8.0 | container run, start-dev warning |
| K-DOCKER | https://www.keycloak.org/getting-started/getting-started-docker | 26.8.0 | `quay.io/keycloak/keycloak:26.8.0 start-dev` |
| K-PROD | https://www.keycloak.org/server/configuration-production | 26.8.0 | production notes (fetched; skimmed) |
| K-UPG | https://www.keycloak.org/docs/latest/upgrading/index.html | 26.8.0 | breaking changes (introspection audience check in 26.6.2) |
| K-FEAT | https://www.keycloak.org/server/features | 26.8.0 | feature flags / defaults |
| K-MGMT | https://www.keycloak.org/server/management-interface | 26.8.0 | management port (fetched; skimmed) |
| K-DPoP | https://www.keycloak.org/securing-apps/dpop | 26.8.0 | fetched, not analysed in depth |
| K-SPEC | https://www.keycloak.org/securing-apps/specifications | 26.8.0 | fetched, not analysed in depth |
| K-ADMV2 | https://www.keycloak.org/admin-api/admin-api-v2 ; https://www.keycloak.org/admin-api/querying | 26.8.0 | fetched, not analysed (admin API v2 preview) |

### A2. Source code (tag `26.8.0`, https://github.com/keycloak/keycloak/blob/26.8.0/…) — raw copies in `raw/src/`
`services/src/main/java/org/keycloak/protocol/oidc/TokenManager.java` · `…/AccessTokenIntrospectionProvider.java` · `…/endpoints/UserInfoEndpoint.java` · `…/endpoints/TokenRevocationEndpoint.java` · `…/endpoints/LogoutEndpoint.java` · `…/grants/RefreshTokenGrantType.java` · `…/refresh/DefaultRefreshTokenProvider.java`, `AbstractRefreshTokenProvider.java` · `services/src/main/java/org/keycloak/services/util/UserSessionUtil.java` · `…/managers/AuthenticationManager.java` · `…/resources/admin/UserResource.java`, `UsersResource.java`, `RealmAdminResource.java`, `RoleMapperResource.java`, `ClientResource.java`, `ClientsResource.java` · `server-spi/src/main/java/org/keycloak/models/UserManager.java` · `server-spi-private/…/SessionExpirationUtils.java` · `services/…/managers/RealmManager.java` · `ssf/tests/base/src/test/java/org/keycloak/tests/ssf/transmitter/SsfTransmitterPollDeliveryTests.java` (request shapes for SSF poll) · `ssf/core/src/main/java/org/keycloak/ssf/event/**` (event type URIs) · `ssf/core/…/Ssf.java`.
Repository file listing used to locate paths: GitHub git-trees API for tag 26.8.0.

### A3. Lab evidence (this session, Keycloak 26.8.0 zip distribution, `start-dev`, single node, Java 21)
`lab/README-lab.md`, `lab/exp1–exp9.py`, `lab/exp7.out`, `lab/exp7c.out`, `lab/bcl_server.py` (+`bcl.log`), `lab/kc.log` (server log of first run), `fixtures/revocationgap-lab-realm.json` (verified import). Download: https://github.com/keycloak/keycloak/releases/download/26.8.0/keycloak-26.8.0.zip. Docker daemon unavailable in sandbox → container path untested.

### A4. Third-party (context only, contradicted where noted)
- https://andrewdoering.org/blog/2026/authzen-shared-signals-framework-part-4-implementation/ and part-2/part-1 (web_search excerpts): claim "Keycloak has no native SSF transmitter" — **contradicted by K-SSF/K-REL and lab** (stale).
- https://skycloak.io/blog/keycloak-25-released-new-features-and-enhancements/ (excerpt): version history.

## B. Microsoft Entra ID / Graph

### B1. Microsoft Learn (all https://learn.microsoft.com/en-us/…)
| ID | Path | Page date |
|---|---|---|
| E-CAE | entra/identity/conditional-access/concept-continuous-access-evaluation | 2026-04-08 |
| E-CAE-S | entra/identity/conditional-access/concept-continuous-access-evaluation-strict-enforcement | 2026-03-24 |
| E-CAE-W | entra/identity/conditional-access/concept-continuous-access-evaluation-workload | 2026-04-23 |
| E-CAE-T | entra/identity/conditional-access/howto-continuous-access-evaluation-troubleshoot | 2026-03-24 |
| E-CAE-RES | entra/architecture/resilience-with-continuous-access-evaluation | 2023-10-23 (fetched, thin) |
| E-SECCAE | security/zero-trust/develop/secure-with-cae | 2025-02-25 |
| E-DEVCAE | entra/identity-platform/app-resilience-continuous-access-evaluation | 2024-11-21 |
| E-CLAIMS | entra/identity-platform/claims-challenge | 2024-04-12 |
| E-AT | entra/identity-platform/access-tokens | 2025-05-14 |
| E-CTL | entra/identity-platform/configurable-token-lifetimes | 2026-04-24 |
| E-RT | entra/identity-platform/refresh-tokens | 2025-11-05 |
| E-REVACC | entra/identity/users/users-revoke-access | 2026-06-19 |
| E-OIDC | entra/identity-platform/v2-protocols-oidc | 2026-06-30 |
| E-ROPC | entra/identity-platform/v2-oauth-ropc | 2025-02-07 |
| E-CC | entra/identity-platform/v2-oauth2-client-creds-grant-flow | 2026-01-30 |
| E-CA-OVERVIEW | entra/identity/conditional-access/overview | 2026-04-27 |
| E-LOGLAT | entra/identity/monitoring-health/reference-log-latency | 2024-09-27 |
| E-RETENTION | entra/identity/monitoring-health/reference-reports-data-retention | 2026-03-25 |
| E-RES (excerpt) | entra/identity/conditional-access/resilience-defaults | search excerpt only |
| E-BACKUP (excerpt) | entra/architecture/backup-authentication-system | search excerpt only |
| E-CA-SESSION (excerpt) | entra/identity/conditional-access/concept-conditional-access-session | search excerpt only |
| E-APPPROXY-CAE (excerpt) | entra/identity/app-proxy/concept-continuous-access-evaluation | search excerpt only |
| G-revoke | graph/api/user-revokesigninsessions | 2025-07-23 |
| G-invalidate | graph/api/user-invalidateallrefreshtokens | 2025-07-23 |
| G-user-update | graph/api/user-update | 2026-07-04 |
| G-user-post | graph/api/user-post-users | 2024-10-23 |
| G-user-delete | graph/api/user-delete | 2025-07-23 |
| G-user-res | graph/api/resources/user | 2026-04-20 |
| G-group-delmember | graph/api/group-delete-members | 2024-05-24 |
| G-approle-user-del | graph/api/user-delete-approleassignments | 2025-07-23 |
| G-ca-post / -update / -delete | graph/api/conditionalaccessroot-post-policies ; conditionalaccesspolicy-update ; conditionalaccesspolicy-delete | 2024-10-18 / 2026-03-07 / 2025-07-23 |
| G-tlp / -create / -assign | graph/api/resources/tokenlifetimepolicy ; tokenlifetimepolicy-post-tokenlifetimepolicies ; application-post-tokenlifetimepolicies | 2024-05-24 / 2025-07-23 / 2025-07-23 |
| G-manageddevice | graph/api/resources/intune-devices-manageddevice | 2025-04-16 |
| G-device-update | graph/api/device-update | 2025-07-23 |
| G-signin-list / G-signin-res | graph/api/signin-list ; graph/api/resources/signin | 2025-11-04 / 2025-11-28 |
| DEV-FAQ | office/developer-program/microsoft-365-developer-program-faq | 2026-09-08 |
| DEV-PROG | office/developer-program/microsoft-365-developer-program | 2026-09-08 |
| DEV-VS (excerpt) | office/developer-program/join-with-visual-studio | search excerpt only |
| PENTEST (excerpt) | azure/security/fundamentals/pen-testing | search excerpt only |

### B2. Other Microsoft
- **E-DISC (live)** https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration — fetched 2026-10-12 05:53 UTC, response headers saved `raw/en-disco.hdr`, body `raw/en-disco.json`. Probes: `POST https://login.microsoftonline.com/common/oauth2/v2.0/revoke` → 404; `POST …/oauth2/v2.0/introspect` → 400 `AADSTS900144 … 'continuation_token'`.
- **MSRC-ROE** https://www.microsoft.com/en-us/msrc/pentest-rules-of-engagement — fetched in full via web_fetch 2026-10-12 (testing own tenant allowed/encouraged; DoS and excessive-traffic automated testing prohibited).
- Attempt to fetch `learn.microsoft.com/en-us/entra/identity/monitoring-health/reference-reports-latencies` → 404 (page replaced by `reference-log-latency`).

### B3. Third-party (context only)
- https://andrewdoering.org/blog/2026/authzen-shared-signals-framework-part-3-microsoft/ (search excerpt): no public Microsoft doc on Entra as SSF transmitter.
- https://petrasecurity.substack.com/p/o365-mgmt-api-latencies-pt1-entra-id ; https://learn.microsoft.com/en-us/answers/questions/5816219/… (search excerpts): empirical sign-in-log latency ≈5–7 min.
- Microsoft Q&A threads on Developer Program eligibility (search excerpts).

## C. Items I could not verify (not stated as fact anywhere)
`xms_rl` (Entra); Entra SSF/CAEP transmit/receive; Entra back-channel logout; Entra non-interactive sign-in coverage in Graph v1.0; Entra `AADSTS` codes for post-revoke refresh; multi-node Keycloak propagation; Keycloak behaviour behind a proxy; container image run (Docker unavailable).
