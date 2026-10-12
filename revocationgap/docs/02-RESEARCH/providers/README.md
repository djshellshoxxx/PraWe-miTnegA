# Identity Provider and Library Research — Index (RG-P00-005)

| Provider / library | Doc | Evidence | Lab feasibility |
|---|---|---|---|
| Keycloak 26.8.0 (current stable 2026-10-12) | [KEYCLOAK.md](KEYCLOAK.md) | Live-observed (V-lab), source (V-src), docs | Free, offline, CI-friendly; `lab-assets/keycloak/` + `research-scripts/keycloak-lab/` |
| Microsoft Entra ID | [ENTRA-ID.md](ENTRA-ID.md) | Docs + live metadata probes; **nothing observed in a tenant** | Operator tenant only |
| Okta | [OKTA.md](OKTA.md) | Docs (some API refs via search excerpts only) | Operator org; free org limits + ToS |
| Auth0 | [AUTH0.md](AUTH0.md) | Docs | Operator tenant; Enterprise-only features |
| Authlib + complementary libraries | [AUTHLIB-AND-LIBS.md](AUTHLIB-AND-LIBS.md) | PyPI/GitHub/docs/source | n/a |

**Capability summary used by RG-P04-001** (details and evidence tags in the per-provider docs):

| Capability | Keycloak | Entra | Okta | Auth0 | Generic OIDC |
|---|---|---|---|---|---|
| RFC 7009 revocation endpoint | yes | **no** (404) | yes (always 200) | yes (`/oauth/revoke`, refresh tokens) | discoverable (`revocation_endpoint`) |
| RFC 7662 introspection | yes (aud rule since 26.6.2) | **no** | yes | **no** (JWT) | discoverable |
| Admin API: disable user | yes | yes (Graph `accountEnabled`) | yes (lifecycle) | yes (`blocked`) | n/a |
| Admin API: kill sessions | yes | `revokeSignInSessions` (RT only) | yes | Enterprise-only | n/a |
| Role/group removal via API | yes | yes (Graph) | yes | yes | n/a |
| SSF/CAEP | experimental transmitter | CAE (not SSF) | transmitter, 2 events | receiver (Universal Logout) | n/a |

Evidence rule: see `../RESEARCH-REGISTER.md` §1.
