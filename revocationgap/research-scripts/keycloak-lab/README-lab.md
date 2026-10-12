# Lab scripts (Keycloak 26.8.0, run 2026-10-12, start-dev on localhost:8080)
Reproduce: download keycloak-26.8.0.zip from GitHub releases, `KC_BOOTSTRAP_ADMIN_USERNAME=admin KC_BOOTSTRAP_ADMIN_PASSWORD=admin bin/kc.sh start-dev --features=ssf`.
- setup.py/setup2.py: create realm `lab`, clients tester/rs, user alice, roles, group (kclab.py = helper lib).
- exp1..exp8: behaviour matrix (disable, session delete, user logout, role/group removal, password reset, notBefore, revoke, refresh-token reuse, offline, delete user, client_credentials, backchannel logout, events, SSF, admin permission matrix).
- exp7.py / exp7c.py: access-token expiry and SSO idle timeout timing (exp7b was contaminated by a concurrent run and deleted).
- exp9.py: re-run against fixtures/revocationgap-lab-realm.json (`--import-realm`): offline tokens vs user notBefore, same-second boundary, offline role removal, Date header, discovery fields.
Note: the first run of exp3 reported that offline refresh survived POST users/{id}/logout; that was a same-second artefact (iat == notBefore passes). exp9 supersedes it.
