# Research Register

## 1. Research documents

| Doc | Content | Evidence base | Source register |
|---|---|---|---|
| [SCHEMATHESIS-INTEGRATION.md](SCHEMATHESIS-INTEGRATION.md) | Upstream capabilities, adapter boundary, hazards, tests | Executed against 4.30.1; source reading; official Python API reference | in-document |
| [STANDARDS-REFERENCE.md](STANDARDS-REFERENCE.md) | STD-001…035, SV-001…058 validity rules, expected-enforcement taxonomy | RFC/spec fetches (V/S/U tags) | [sources/SOURCES-standards.md](sources/SOURCES-standards.md) |
| [COMPETITIVE-ANALYSIS.md](COMPETITIVE-ANALYSIS.md), [PRIOR-ART-ACADEMIC.md](PRIOR-ART-ACADEMIC.md) | Tool matrix, differentiation, academic lessons | repo clones, wheel read, fetches | [sources/SOURCES-competitive.md](sources/SOURCES-competitive.md) |
| [providers/KEYCLOAK.md](providers/KEYCLOAK.md), [providers/ENTRA-ID.md](providers/ENTRA-ID.md) | Provider behaviour + capability matrices | Keycloak **observed on a live 26.8.0 instance**; Entra docs + live metadata probes | [sources/SOURCES-providers-a.md](sources/SOURCES-providers-a.md) |
| [providers/OKTA.md](providers/OKTA.md), [providers/AUTH0.md](providers/AUTH0.md), [providers/AUTHLIB-AND-LIBS.md](providers/AUTHLIB-AND-LIBS.md) | Provider behaviour, library evaluation | vendor docs (some API refs only via search excerpts, tag V*) | [sources/SOURCES-providers-b.md](sources/SOURCES-providers-b.md) |
| [TECHNICAL-FEASIBILITY.md](TECHNICAL-FEASIBILITY.md) | Feasibility, stack decisions, risk register | integration of above | — |

Evidence rule for specifications: a module spec may state provider/standard behaviour as fact only when the cited research row is tagged V / V-doc / V-src / V-lab. Rows tagged S, V*, 3P, I or U must be written as assumptions in section 26 of the spec and covered by a lab/contract test that can falsify them.

## 2. Verified facts that changed the design (traceable decisions)

| # | Finding | Source | Design consequence |
|---|---|---|---|
| RF-1 | Keycloak user logout is `POST …/users/{id}/logout`; strict `iat < notBefore` at 1 s resolution | KEYCLOAK.md (V-lab) | Adapter uses correct endpoint; ≥1 s settle rule (R-008) |
| RF-2 | Keycloak: disable/session-delete/logout/notBefore ⇒ introspection inactive, userinfo 401, refresh fails; local JWT verification valid until exp | KEYCLOAK.md (V-lab) | Expected-enforcement expectations keyed by *validation mode* of the resource server |
| RF-3 | Re-enabling a disabled Keycloak user revives old tokens | KEYCLOAK.md (V-lab) | Restoration/reactivation scenario (SC reactivation) is a genuine inconsistency class |
| RF-4 | Entra v2 metadata has no `revocation_endpoint`/`introspection_endpoint`; `/revoke` 404 | ENTRA-ID.md (V live probe) | Capability discovery must not assume RFC 7009/7662 |
| RF-5 | Entra revokeSignInSessions never revokes access tokens; CAE only for CAE-capable clients | ENTRA-ID.md (V-doc) | CAE capability flag; outcome `DOC_DELAY` |
| RF-6 | Okta revoking RT kills its ATs; revoking AT leaves RT; `/revoke` always 200 | OKTA.md (V) | Cascade expectations in enforcement model; independent oracle rule SV-005 |
| RF-7 | Auth0 JWT access tokens "cannot be revoked", no introspection endpoint; Sessions/RT Management API Enterprise-only | AUTH0.md (V) | Capability matrix flags; Free-tier limited scenarios |
| RF-8 | Authlib httpx integration needs `httpx2`; `authlib.jose` deprecated | AUTHLIB-AND-LIBS.md (V) | requests-based stack; joserfc |
| RF-9 | No examined tool measures a temporal window; OIDF SSF tests check delivery not enforcement | COMPETITIVE §0 (V) | Product differentiation (D1–D7) |
| RF-10 | ASVS 5.0.0 V7.4.1/V7.4.2 require terminated sessions/tokens to stop working for application sessions | STANDARDS §2 (V via mirror) | Policy profiles; default `protocol` |
| RF-11 | Schemathesis master docs ≠ 4.30.1 wheel | COMPETITIVE §2.5 (V) | Specs written against wheel only |

## 3. Unresolved research items

| ID | Item | Applies until resolved | Owner element |
|---|---|---|---|
| RQ-1 | RFC 6749 §5.2/§6/§10.4 primary text (only snippets read) | Treat `invalid_grant` as *likely* refresh failure signature; do not classify on it alone (use provider adapter mapping) | P04-002 |
| RQ-2 | OIDC Core §11/§12 offline_access, RFC 8705/8693/8417/8935/8936, OIDC Session Management, RFC 6265bis primary text | Mark dependent rules NEEDS_VERIFICATION | P04-004, P04-011, P04-005 |
| RQ-3 | NIST SP 800-63B-4 exact numbers (snippets), 63C-4 unread; NIST IR 8587 body | Provide as configurable policy values with source "snippet; verify" | P08-008 |
| RQ-4 | Okta: does `DELETE /users/{id}/sessions?oauthTokens=true` revoke custom-AS tokens? Okta suspension/group-removal token effects; scopes for lifecycle ops | Measure in operator tenant; baseline unknown | P04-009 |
| RQ-5 | Auth0: effect of `blocked=true` on existing sessions/tokens/`/userinfo`; revoke-session+RT call path; self-service ToS | Baseline unknown until measured | P04-010 |
| RQ-6 | Keycloak multi-node/cluster propagation, reverse proxy, Docker image path, UI `ssf-events` listener enablement | Lab is single-node; multi-node scenario deferred to P09-006 design | P09-006 |
| RQ-7 | Entra: observed time-to-401 at Graph/custom API; AADSTS codes after revoke; `xms_rl` claim existence | Documented-delay classification only | P04-008 |
| RQ-8 | Python 3.10 EOL date; exact latest PyPI versions of joserfc/websockets/cryptography | Pin at build time | P13-001 |
| RQ-9 | Schemathesis: `stream=True`/body-size limit through `Case.call`; GraphQL subscription non-support; thread-safety stress | Spec uses RG-side caps and treats ST calls as thread-confined per identity session | P05-005, P05-012 |
| RQ-10 | Burp/ZAP licence/edition limits, caep.dev, Google RISC, Auth0 SSF | No claims made | P14-001 |
