# SOURCES — providers-b research (Okta, Auth0, Authlib & libraries)

Access date for all entries: **2026-10-12**. Per-file source keys (IDs `On`, `An`, `Ln`) are authoritative; this file is the consolidated register plus fetch-quality notes.

**Method note.** `web_fetch` only retrieves URLs that appeared in the conversation (user/search results/links of fetched pages). Okta's *API reference* pages (`developer.okta.com/docs/api/openapi/okta-management/...`) are JS-rendered: `web_fetch` returns only page metadata, so their content (endpoint paths, scopes, parameters) is taken from the **vendor-page text returned in `web_search` excerpts for the same URL** and is tagged **V\***. Okta's OpenAPI spec (`okta/okta-management-openapi-spec`, `dist/current/management-minimal.yaml`, 3.47 MB) exists and would resolve all scope questions, but was too large to ingest in this session. GitHub files (Authlib, joserfc, Schemathesis) were read through the GitHub API tool at exact tags/SHAs. No curl/direct network fetching outside the sanctioned tools was used.

Tags: **V** fetched primary page · **V\*** primary page excerpt via search · **3P** third-party/community · **I** inferred · **U** unverified.

## Fetched in full (V)

| Org | URL |
|---|---|
| Okta | https://developer.okta.com/docs/guides/revoke-tokens/main/ |
| Okta | https://developer.okta.com/docs/guides/oin-universal-logout-overview/ |
| Okta | https://developer.okta.com/docs/concepts/auth-servers/ |
| Okta | https://developer.okta.com/docs/concepts/token-lifecycles/ |
| Okta | https://developer.okta.com/docs/api/openapi/okta-oauth/guides/overview |
| Okta | https://developer.okta.com/docs/reference/system-log-query/ |
| Okta | https://developer.okta.com/docs/reference/rate-limits/ |
| Okta | https://developer.okta.com/docs/reference/rl2-limits/ |
| Okta | https://developer.okta.com/docs/reference/org-defaults/ |
| Okta | https://developer.okta.com/terms/ (Integrator Free Plan Subscription Agreement) |
| Okta | https://developer.okta.com/docs/reference/ssf-transmitter-sets/ |
| Okta | https://developer.okta.com/docs/reference/api/event-types/ (first part only; output truncated) |
| Okta | https://help.okta.com/oie/en-us/content/topics/itp/universal-logout.htm |
| Okta | https://help.okta.com/oie/en-us/content/topics/itp/universal-logout-revocations.htm |
| Okta | https://help.okta.com/oie/en-us/content/topics/itp/config-universal-logout.htm |
| Okta | https://help.okta.com/oie/en-us/content/topics/apps/universal-logout-amfa.htm |
| Okta | https://help.okta.com/oie/en-us/content/topics/itp/configure-shared-signal-provider.htm |
| Auth0 | https://auth0.com/docs/secure/tokens/refresh-tokens/revoke-refresh-tokens |
| Auth0 | https://dev.auth0.com/docs/secure/tokens/revoke-tokens |
| Auth0 | https://auth0.com/docs/manage-users/sessions/manage-user-sessions-with-auth0-management-api |
| Auth0 | https://auth0.com/docs/manage-users/user-accounts/block-and-unblock-users |
| Auth0 | https://auth0.com/docs/authenticate/login/logout/back-channel-logout |
| Auth0 | https://auth0.com/docs/authenticate/login/logout/universal-logout |
| Auth0 | https://auth0.com/docs/troubleshoot/customer-support/operational-policies/rate-limit-policy/rate-limit-configurations/free-public.md |
| Auth0 | https://auth0.com/docs/troubleshoot/customer-support/operational-policies/load-testing-policy.md |
| Auth0 | https://auth0.com/docs/troubleshoot/customer-support/operational-policies/penetration-testing-policy.md |
| Auth0 | https://auth0.com/docs/deploy-monitor/logs/log-data-retention.md |
| Auth0 | https://auth0.com/docs/deploy-monitor/logs/retrieve-log-events-using-mgmt-api.md |
| Auth0 | https://auth0.com/docs/deploy-monitor/logs/log-event-type-codes.md |
| Auth0 | https://auth0.com/docs/ai-agents-mcp/cross-app-access.md |
| Auth0 | https://auth0.com/pricing.md |
| Auth0 | https://auth0.com/llms.txt ; https://auth0.com/docs/llms.txt (index; lists OpenAPI JSON URLs) |
| Libs | https://pypi.org/project/Authlib/ ; https://docs.authlib.org/ ; https://docs.authlib.org/en/stable/upgrades/changelog.html ; https://docs.authlib.org/en/stable/upgrades/jose.html ; https://docs.authlib.org/en/stable/oauth2/client/http/httpx.html |
| Libs | https://pypi.org/project/httpx2/ |
| Libs (GitHub API) | `authlib/authlib` `pyproject.toml`@v1.8.0, `authlib/oauth2/client.py`@main; `authlib/joserfc` `src/joserfc/jwt.py`, `_rfc7519/claims.py`, `jws.py`; `schemathesis/schemathesis` `pyproject.toml`@v4.30.1; Okta spec repo directory listing `dist/current` |

## Used via search excerpts (V\* / 3P)

Okta API reference pages (User Sessions, Sessions, User Lifecycle, Group unassign, User OAuth tokens, Application tokens, SSF Transmitter/Receiver/Security Event Tokens, Global Token Revocation) and guides (refresh-tokens, implement-oauth-for-okta[-serviceapp], set-up-oauth-api, event hooks concept, validate-access-tokens/dotnet), Okta support KBs (refresh token expiration, system-log session events, introspection via private_key_jwt), Okta Workflows connector cards, devforum threads; Auth0 doc/support/blog/community pages (access-token lifetime, refresh-token expiration/rotation, session-management blog, grants API, RBAC enablement, RFC 7662 thread, changelog); PyPI/aggregator excerpts for PyJWT, websockets, aiohttp, websocket-client, cryptography, APScheduler, okta SDK, python-jose, joserfc; SSF/CAEP specs (openid.net), RFC 7662/8417/9493 references, Keycloak SSF post, skycloak, sharedsignals.guide, pkg.go.dev go-secevent. Exact URLs are in the "Source key" of each deliverable.

## Not fetched / failed (candidates for follow-up)

* Okta OpenAPI spec file (too large) — would settle OKTA U2/U9.
* `https://developer.okta.com/docs/guides/validate-access-tokens/main/` (not in context), `help.okta.com/.../universal-logout-supported-apps.htm`.
* Auth0: `https://auth0.com/docs/authenticate/login/logout/log-users-out-of-auth0` (not in context), `https://auth0.com/docs/manage-users/sessions`, `https://auth0.com/_llms/en/manage-users.md` (not accessible), Authentication API `revoke-refresh-token` page, Management API OpenAPI JSON (`/docs/oas/management/v2/management-api-oas.json`), rate-limit pages for Essentials/Professional/Enterprise.
* `pypi.org/project/schemathesis/` (not in context → used GitHub `pyproject.toml` at the tag instead).
* PyPI project pages for joserfc, websockets, aiohttp, cryptography (version numbers from aggregator excerpts; confirm at lock time).
