---
id: RG-P02-003
title: "Credential, session and token lifecycle model"
phase: "02"
package: core
module_ids: [MOD-CORE-CREDENTIAL_LIFECYCLE]
status: DRAFT
depends_on: [RG-P02-002]
requirements: [FR-TEMP-005, FR-IDP-003, FR-IDP-005, FR-IDP-006, FR-EXP-005, FR-EXP-009, FR-PRB-003, FR-SEC-005, FR-EVD-003]
interfaces_defined: [IF-CORE-CREDGRAPH]
interfaces_used: [IF-CORE-CLOCK, IF-CORE-SERIAL, IF-CORE-AUTHSTATE]
schemas_defined: [SCH-CREDENTIAL]
schemathesis_touchpoints: []
---

# RG-P02-003 — Credential, session and token lifecycle model

> Scope: the *secret-free description* of each credential under test (token, cookie, key), the sessions they belong to, their parent/child and family relations, their derived expiry bound, and a lifecycle state machine for each credential. Parsing JWTs (RG-P04-003), acquiring credentials (RG-P04-002/-005), injecting them into requests (RG-P05-003) and the revocation event (RG-P02-004) are elsewhere.

## 1. Module identifier and name

| Item | Value |
|---|---|
| Element | RG-P02-003 — Credential, session and token lifecycle model |
| Package / modules | `rg_core.model.credential` (models), `rg_core.credential.graph`, `.lifecycle`, `.expiry`, `.settle` (pure functions) |
| Module id | `MOD-CORE-CREDENTIAL_LIFECYCLE` |
| Schemas | `SCH-CREDENTIAL`: `Credential`, `Session`, `TokenClaims`, `TokenHeader`, `AcquisitionBracket`, `CredentialState`, `CredentialStateRecord`, `ExpiryBound` |
| Interface | new `IF-CORE-CREDGRAPH` (`CredentialGraph`, `expiry_bound`, `fold_lifecycle`, `settle_check`) |

## 2. Phase and requirement references

| Requirement | Realised by |
|---|---|
| FR-TEMP-005 credential model with type, format, binding, issuance, expiry, generation, parent/child, session membership, lifecycle states (issued, in-use, rotated, expired, revoked-claimed, revoked-observed) | §8, §11, §12.2 |
| FR-IDP-003 JWT analysis consumes an allow-listed claim model with `exp/iat/nbf/jti/sid/aud` | §8.3 `TokenClaims` (the decoder itself: RG-P04-003) |
| FR-IDP-005 disposable token family per probe slot | `family_root_ref`, `slot_key`, INV-8 |
| FR-IDP-006 session-cookie credentials, per-identity isolation | `CredentialType.session_cookie`, `Session`, INV-9 |
| FR-EXP-005 settle interval | §12.5 `settle_check` |
| FR-EXP-009 several credentials per event | `CredentialGraph` (§7.2) |
| FR-PRB-003, FR-SEC-005 | models hold fingerprints/handles only |
| FR-EVD-003 | `derivation` on lifecycle records |

Validity rules realised: **TV-09** (natural expiry vs revocation needs `exp`/`iat` and a sibling control → `ExpiryBound`, `unaffected_siblings`), **TV-12** (probe-side-effect isolation: family per slot), **TV-15** (≥ 1 s settle after minting), TV-02/TV-10 support (credential roles); SV-007 (revoking client = issuing client → `client_ref`), SV-027 (granted scope incl. `offline_access` → `scope_granted`), SV-032 note (cookie attributes are not server validity → `expiry_basis`). Scenarios: SCN-02/03/04/08/10.

## 3. Purpose and user/security value

The product's central claim — "this token kept working N seconds after the change" — is wrong if the credential was about to expire anyway, if the probe used a different client or session than the revoked one, if a refresh probe rotated the very token another observation depends on, or if the token was minted in the same second as the revocation. These are *relational* facts about credentials. This module represents them as data (fingerprints, lineage, session membership, expiry as a bracketed local-time interval, lifecycle state) so that the engine can **refuse** invalid designs before arming (settle, family isolation), and the analysis can **explain** outcomes (natural expiry vs enforcement, sibling control selection) without ever touching secret material.

## 4. Explicit responsibilities

- **RESP-1** Define `Credential` (frozen field names of DATA-MODEL §7 plus additive fields) with the allowed `(type, format)` matrix and validators.
- **RESP-2** Define `TokenClaims`/`TokenHeader`: the allow-listed, bounded, secret-free decoded view of a JWT, with `exp/iat/nbf` as `RemoteInstant`s.
- **RESP-3** Define `Session` and the `session_ref` derivation rule.
- **RESP-4** Define the lifecycle states, the legal transition relation, `CredentialStateRecord` and `fold_lifecycle`.
- **RESP-5** Define `CredentialGraph`: lineage, family, session membership, sibling selection, and its validity checks.
- **RESP-6** Define `expiry_bound`: the credential's expiry as a bracketed *local monotonic* interval from `expires_in` and/or `exp` + `ClockOffset`.
- **RESP-7** Define `settle_check` (TV-15 / FR-EXP-005) with its proof sketch.
- **RESP-8** State fingerprint, id-prefix and secret-freedom rules.

## 5. Out-of-scope responsibilities

| Excluded item | Owner |
|---|---|
| Acquiring tokens, refresh/rotation calls, session login flows | RG-P04-002, RG-P04-005, RG-P05-003 |
| Decoding/verifying JWTs, building `TokenClaims` from raw tokens | RG-P04-003 |
| Holding secret material (`CredentialMaterial`, `Secret`) | RG-P04-001 contract, RG-P11-001 |
| The revocation event and which credentials it `affects` (selector semantics) | RG-P02-004 |
| Whether a credential *should* be rejected after an event | RG-P02-005 |
| Probe-slot allocation and scheduling | RG-P05-001, RG-P05-008 |
| Estimating `ClockOffset` | RG-P08-002 |
| Persistence | RG-P03-008 |

## 6. Dependencies and prerequisites

- RG-P02-001 (`TimeInstant`, `RemoteInstant`, `ClockOffset`, `remote_to_local_wall_interval`, `mono_delta`), RG-P02-002 (`IdnId`, `PrvId` usage; `Identity`), RG-P03-002 (`Model`, `Provenance`, `Int64`, `Count`, `Label`, `ShortText`, `Sha256Digest`, `CrdId`, `fingerprint_of`).
- DATA-MODEL §2.4 (fingerprint rule), §3 (enums `CredentialType`, `CredentialFormat`, `SenderBinding`), §7, §9.1.
- Libraries: pydantic v2 only. No I/O, no clock reads.

## 7. External and internal interfaces

### 7.1 Id and fingerprint rules

`Credential.id` is `crd_<ULID>` from `IdFactory.new("crd")`. `fingerprint` is `"fp:" + sha256(material)[:12]` computed by `SecretResolver.fingerprint` / `fingerprint_of(material)` at acquisition time, grammar `^fp:[0-9a-f]{12}$`; 48 bits are enough to distinguish the credentials of one experiment (collision probability for 100 credentials ≈ 2×10⁻¹¹) and too few to recover the material. Fingerprints must be unique within an experiment (INV-10); on collision the acquirer must re-mint (`RGE-CONFIG-0306`). `session_ref` is `"ses:" + fingerprint_of(<kind>|<provider_ref>|<session material>)[3:]` (12 hex), computed by the adapter that holds the session id/cookie; no prefix beyond `ses:` is registered with `IdFactory` (sessions are value entities keyed by their fingerprint, DATA-MODEL §2.1 stays unchanged).

### 7.2 `CredentialGraph` and pure functions — IF-CORE-CREDGRAPH (`rg_core.credential`)

All synchronous, pure, thread-safe, deterministic.

```python
class CredentialGraph:                                         # immutable index; construction validates (RGE-CONFIG-0306)
    def __init__(self, credentials: Iterable[Credential], sessions: Iterable[Session] = ()) -> None: ...
    def get(self, ref: str) -> Credential: ...                  # KeyError → RGE-INTERNAL-0309
    def of_identity(self, identity_ref: str) -> tuple[Credential, ...]: ...
    def children(self, ref: str) -> tuple[Credential, ...]: ...             # direct children by parent_ref
    def descendants(self, ref: str) -> tuple[Credential, ...]: ...          # transitive, deterministic order (BFS by id)
    def ancestors(self, ref: str) -> tuple[Credential, ...]: ...            # nearest parent first
    def family(self, ref: str) -> tuple[Credential, ...]: ...               # all credentials with the same family_root_ref
    def session_members(self, session_ref: str) -> tuple[Credential, ...]: ...
    def unaffected_siblings(self, subject: str, affected: AbstractSet[str]) -> tuple[Credential, ...]: ...   # §12.4
    def by_role(self, role: CredentialRole) -> tuple[Credential, ...]: ...

def expiry_bound(c: Credential, *, offset: ClockOffset | None = None, receipt_theta_slack_ns: int = 0,
                 expires_in_slack_ns: int = 1_000_000_000) -> ExpiryBound | None: ...    # §12.1; None if no reliable basis
def fold_lifecycle(credential_ref: str, records: Sequence[CredentialStateRecord]) -> CredentialState: ...   # §12.2; RGE-CONFIG-0305
def check_lifecycle(records: Sequence[CredentialStateRecord]) -> tuple[LifecycleViolation, ...]: ...      # non-raising
def settle_check(credentials: Iterable[Credential], a_req: TimeInstant, settle_ns: int) -> SettleCheck: ...   # §12.5; RGE-TIMING-0104 on clock mismatch
def require_settle(check: SettleCheck) -> None: ...                                                       # RGE-CONFIG-0307
```

Error codes (block 0300–0399 (RG-P03-005 §8.3)):

| Code | Name | Raised by |
|---|---|---|
| RGE-CONFIG-0301 | `credential_invalid` (id/fingerprint/generation/field grammar, `acquired.finished_at < started_at`) | `Credential` validator |
| RGE-CONFIG-0302 | `credential_type_format_invalid` (not in the matrix §8.2) | `Credential` validator |
| RGE-CONFIG-0303 | `token_claims_invalid` (claims on non-JWT, non-allow-listed claim, bounds, `exp` not a `RemoteInstant` of domain `idp`/`target`) | `TokenClaims` validator |
| RGE-CONFIG-0304 | `session_invalid` | `Session` validator |
| RGE-CONFIG-0305 | `lifecycle_transition_illegal` | `fold_lifecycle` |
| RGE-CONFIG-0306 | `credential_graph_invalid` (cycle, missing parent, duplicate fingerprint, family/slot violation, cross-identity parent) | `CredentialGraph` constructor |
| RGE-CONFIG-0307 | `settle_not_satisfied` | `require_settle` |
| RGE-INTERNAL-0309 | `credential_ref_unknown` | `CredentialGraph.get` |

Clock mismatches inside `settle_check`/`expiry_bound` raise `RGE-TIMING-0104` (RG-P02-001).

## 8. Data structures and schemas

Conventions as in RG-P02-001 §8 (frozen `Model`s; `Int64` ns quantities; validator messages prefixed by the RGE code; `None` omitted from JSON). `Credential` and `Session` are `Document`s (`SCHEMA_ID` `credential`, `session`; version `1.0`) with `Provenance` (acquired credentials are `observed`; scenario-declared placeholders for externally supplied tokens are `assumed`).

### 8.1 Enumerations (additive to DATA-MODEL §3)

```python
class CredentialState(str, Enum):   # FR-TEMP-005; rank in parentheses
    issued="issued"(0); in_use="in_use"(1); rotated="rotated"(2); expired="expired"(3); revoked_claimed="revoked_claimed"(4); revoked_observed="revoked_observed"(5)
class CredentialRole(str, Enum):    # role of the credential in the experiment
    probe_subject="probe_subject"; sibling_control="sibling_control"; foreign_control="foreign_control"; baseline_only="baseline_only"
class IssuerRole(str, Enum):        # whose credential is it, for expectation applicability (ASVS V7.4 applies to the application's own sessions)
    third_party_issued="third_party_issued"; application_own_session="application_own_session"; unknown="unknown"
class ExpiryBasis(str, Enum):
    jwt_exp_claim="jwt_exp_claim"; expires_in="expires_in"; introspection_exp="introspection_exp"; cookie_attribute="cookie_attribute"; none="none"
class SessionKind(str, Enum):
    idp_sso="idp_sso"; app_session="app_session"; oauth_grant="oauth_grant"; ws_connection="ws_connection"
```

### 8.2 `Credential`

| Field | Type | Constraint | Default | Description |
|---|---|---|---|---|
| `schema_version` | SchemaVersion | `"1.0"` | | |
| `id` | `CrdId` | `crd_` + ULID | required | frozen name |
| `experiment_ref` | `ExpId` | | required | owning experiment (DATA-MODEL §9.1) |
| `identity_ref` | `IdnId` | | required | frozen name |
| `type` | `CredentialType` | | required | frozen name |
| `format` | `CredentialFormat` | `(type, format)` ∈ matrix below | required | frozen name |
| `binding` | `SenderBinding` | | `none` | frozen name |
| `binding_key_fp` | str \| None | `fp:` grammar; required iff `binding ≠ none` | None | fingerprint of the DPoP key / certificate (proofs are regenerated per probe, TV-03) |
| `fingerprint` | str | `^fp:[0-9a-f]{12}$` | required | frozen name |
| `issued_at` | `RemoteInstant \| None` | `source ∈ {jwt_claim, provider_api_field}` | None | frozen name; server-side issuance time if known |
| `expires_at` | `RemoteInstant \| None` | same | None | frozen name; server-side expiry if known |
| `expiry_basis` | `ExpiryBasis` | `jwt_exp_claim` ⇒ `expires_at` set and `format=jwt`; `expires_in` ⇒ `lifetime_s` set | `none` | which fact bounds the expiry; `cookie_attribute` is a client hint, **not** server validity (SV-032) |
| `lifetime_s` | Count \| None | ≤ 31 536 000 × 10 | None | AS-declared `expires_in` seconds |
| `acquired` | `AcquisitionBracket` | `started_at ≤ finished_at`, same clock | required | request/response bracket of the minting call (IF-IDP-ACQUIRE `started_at/finished_at`) |
| `generation` | Count | | 0 | frozen name. Refresh tokens: rotation count since the first RT of the family. Access/ID tokens: generation of the parent RT at issuance. |
| `parent_ref` | `CrdId \| None` | must exist in the graph; same `identity_ref`; not self | None | frozen name; credential used to obtain this one (RT → AT; RT_n → RT_{n+1}) |
| `family_root_ref` | `CrdId` | equals own `id` iff `parent_ref is None`; otherwise equals parent's `family_root_ref` | own id | token-family identity (TV-12) |
| `slot_key` | Label \| None | | None | probe slot this family is dedicated to (refresh/oracle isolation); all members of a family share one `slot_key` |
| `session_ref` | str \| None | `^ses:[0-9a-f]{12}$` | None | frozen name |
| `client_ref` | Label \| None | | None | OAuth client the credential was issued to (SV-007: the revoking client must be this client) |
| `scope_granted` | `SortedSet[Label]` | ≤ 32, each ≤ 64 chars | empty | granted scopes from the token response (SV-027 `offline_access`) |
| `flow` | Label | e.g. `password`, `client_credentials`, `session_cookie_form` | required | acquisition flow id (IF-IDP-CAPS `AcquisitionFlow` values) |
| `issuer_role` | `IssuerRole` | | `unknown` | applicability of application-session rules |
| `role` | `CredentialRole` | | `probe_subject` | role in the experiment |
| `claims_allowlist` | `TokenClaims \| None` | non-null only if `format=jwt` | None | frozen name |
| `derivation`, `produced_by` | provenance mixin | | | |

**(type, format) matrix** (RGE-CONFIG-0302 otherwise): `access_token`: jwt, opaque, other · `refresh_token`: opaque, jwt, other · `id_token`: jwt · `session_cookie`: cookie · `api_key`: opaque, other · `service_credential`: opaque, other, jwt.

Validators: V-C1 ids/grammar/ranges (0301); V-C2 matrix (0302); V-C3 binding ⇔ `binding_key_fp` (0301); V-C4 basis consistency (0301); V-C5 `claims_allowlist` only for jwt (0303).

```json
{"schema_version": "1.0", "id": "crd_01M4QJ0CYG4MNPZX45HY43KWJR", "experiment_ref": "exp_01M4QJ0B00M9S346Q3D25VT4F5",
 "identity_ref": "idn_01M4QJ0B34V37E3S3E28JT97KB", "type": "access_token", "format": "jwt", "binding": "none",
 "fingerprint": "fp:3fa91c07d2be",
 "issued_at":  {"value_ns": "1791796800000000000", "domain": {"id": "idp:prv_01M4QJ0B1J6CQ643DZVMXXQKFB", "kind": "idp"}, "resolution_ns": "1000000000", "source": "jwt_claim",
                "local_receipt": {"wall_ns": "1791796800180000000", "mono_ns": "200180000000", "clock_id": "system", "read_cost_ns": "400", "epoch": "a1b2c3d4"}},
 "expires_at": {"value_ns": "1791797100000000000", "domain": {"id": "idp:prv_01M4QJ0B1J6CQ643DZVMXXQKFB", "kind": "idp"}, "resolution_ns": "1000000000", "source": "jwt_claim",
                "local_receipt": {"wall_ns": "1791796800180000000", "mono_ns": "200180000000", "clock_id": "system", "read_cost_ns": "400", "epoch": "a1b2c3d4"}},
 "expiry_basis": "jwt_exp_claim", "lifetime_s": 300,
 "acquired": {"started_at":  {"wall_ns": "1791796800000000000", "mono_ns": "200000000000", "clock_id": "system", "read_cost_ns": "400", "epoch": "a1b2c3d4"},
              "finished_at": {"wall_ns": "1791796800180000000", "mono_ns": "200180000000", "clock_id": "system", "read_cost_ns": "400", "epoch": "a1b2c3d4"}},
 "generation": 0, "family_root_ref": "crd_01M4QJ0CYG4MNPZX45HY43KWJR", "session_ref": "ses:9c2d41ab07ee",
 "client_ref": "rg-tester", "scope_granted": ["openid"], "flow": "password", "issuer_role": "third_party_issued", "role": "probe_subject",
 "claims_allowlist": {"header": {"alg": "RS256", "typ": "JWT", "kid": "k1"}, "claims": {"iss": "http://localhost:8080/realms/rgap", "sub": "rg-alice", "aud": ["rg-rs"], "azp": "rg-tester", "sid": "7a1d3c52-0be4", "jti": "d41d8cd9"},
                      "claim_names_present": ["aud","azp","exp","iat","iss","jti","sid","sub","typ"]},
 "derivation": "observed", "produced_by": {"component": "rg_idp.oidc", "version": "1.0"}}
```

(In the example both `local_receipt` instants equal the end of the minting bracket, because `iat`/`exp` arrive in the token response.)

### 8.3 `TokenClaims`, `TokenHeader`

`TokenHeader`: `alg` (Label, e.g. `RS256`, `none`), `typ` (Label | None), `kid` (ShortText | None).
`TokenClaims`: `header`; `claims: Mapping[Label, ClaimValue]` where `ClaimValue = str(≤256) | int | bool | tuple[str(≤256), ...](≤16)`; ≤ 32 entries; keys must be in `credential.claims_allowlist_paths` (§18; dotted paths such as `realm_access.roles` are flattened to a string-list value); `claim_names_present: SortedSet[Label]` (≤ 128 **names only** of every top-level claim in the token, including non-allow-listed); `other_claims_digest: Sha256Digest | None` (digest of the canonical JSON of the non-allow-listed claims, for "did anything else change between two tokens" tests); `exp`, `iat`, `nbf: RemoteInstant | None` (source `jwt_claim`, domain `idp` or `target`, `resolution_ns ≤ 10⁹`; fractional NumericDates give finer resolution).
Validators (0303): allow-list membership; value bounds; `exp` ≥ `iat` when both present is **not** enforced (hostile tokens exist; the analysis flags it); `alg=none` is representable (the decoder reports it; RG never trusts it).

### 8.4 `Session`

| Field | Type | Constraint | Description |
|---|---|---|---|
| `schema_version`, `derivation`, `produced_by` | | | |
| `session_ref` | str | `^ses:[0-9a-f]{12}$` | §7.1 |
| `kind` | `SessionKind` | | |
| `identity_ref` | `IdnId` | | |
| `provider_ref` | `PrvId` | | |
| `established_at` | `TimeInstant` | | |
| `fingerprint` | str | `fp:` grammar | fingerprint of the session id/cookie |
| `parent_session_ref` | str \| None | | SSO session that spawned an app/oauth session |

```json
{"schema_version": "1.0", "session_ref": "ses:9c2d41ab07ee", "kind": "idp_sso", "identity_ref": "idn_01M4QJ0B34V37E3S3E28JT97KB",
 "provider_ref": "prv_01M4QJ0B1J6CQ643DZVMXXQKFB", "established_at": {"wall_ns": "1791796800100000000", "mono_ns": "200100000000", "clock_id": "system", "read_cost_ns": "400", "epoch": "a1b2c3d4"},
 "fingerprint": "fp:9c2d41ab07ee", "derivation": "observed", "produced_by": {"component": "rg_idp.oidc", "version": "1.0"}}
```

### 8.5 `AcquisitionBracket`, `ExpiryBound`, `CredentialStateRecord`, `SettleCheck`

- `AcquisitionBracket`: `started_at`, `finished_at` (`TimeInstant`, same clock/epoch, ordered).
- `ExpiryBound`: `basis: ExpiryBasis`, `lo_mono_ns`, `hi_mono_ns` (`Int64`, local mono of the run clock; `lo ≤ hi`), `clock_id`, `epoch`, `reliable: bool` (`basis ∈ {jwt_exp_claim, introspection_exp, expires_in}`), `sources_conflict: bool`, `width_ns` (computed).
- `CredentialStateRecord`: `credential_ref`, `state: CredentialState`, `at: TimeInstant`, `basis: Literal["clock","event","observation","operator"]`, `cause_ref: str | None` (`rev_…`, `obs_…`, `tln_…`), `moot: bool = False` (set when `revoked_claimed` is recorded for an already-expired credential), `derivation: Derivation`. Embedded in timeline entries of kind `credential_state` (RG-P02-008).
- `SettleCheck`: `ok: bool`, `required_ns`, `slack_ns` (`a_req.mono − newest.finished_at.mono − required_ns`; negative ⇒ violation), `newest_credential_ref`.

## 9. Inputs, outputs, and validation rules

| # | Rule | Code |
|---|---|---|
| VR-1 | id/fingerprint/session/generation grammar; `acquired.finished_at ≥ started_at`, same clock; binding ⇔ key fingerprint | RGE-CONFIG-0301 |
| VR-2 | `(type, format)` in the matrix | RGE-CONFIG-0302 |
| VR-3 | claims only on JWT; only allow-listed names; bounds; time claims are `RemoteInstant`s | RGE-CONFIG-0303 |
| VR-4 | `Session` grammar and fingerprint | RGE-CONFIG-0304 |
| VR-5 | lifecycle sequence obeys §11 (strictly rank-increasing; `revoked_observed` only after `revoked_claimed`) | RGE-CONFIG-0305 |
| VR-6 | graph: acyclic parents, parents exist and share identity, `family_root_ref` consistent, fingerprints unique, one `slot_key` per family, no two probe slots in one family, session members share `identity_ref` | RGE-CONFIG-0306 |
| VR-7 | `require_settle(check)` requires `check.ok` | RGE-CONFIG-0307 |
| VR-8 | cross-clock/epoch arithmetic (`settle_check`, `expiry_bound`) | RGE-TIMING-0104 |

Inputs are never mutated; outputs are new frozen values.

## 10. Detailed execution behavior

1. **Acquisition (engine).** After `CredentialAcquirer.acquire`, the engine builds one `Credential` per `CredentialMaterial`: `fingerprint` from the secret, `acquired` from the result's `started_at/finished_at`, `expiry_basis`/`lifetime_s`/`expires_at` from the token response and the decoder (`TokenClaims` from RG-P04-003), `family_root_ref` = own id for roots, `slot_key` for refresh families dedicated to a probe slot. `Credential`s are persisted as evidence (`kind="credential"`); the `Secret` stays in memory only.
2. **Graph.** The engine builds a `CredentialGraph` per experiment at the end of `BASELINING` setup and before `ARMED` (validation failures keep the run out of `ARMED`).
3. **Roles.** The scenario designates which credentials are `probe_subject`, `sibling_control` (an unaffected credential of the same type/format/client; §12.4), `foreign_control` (another identity), or `baseline_only`. Missing required sibling controls are a pre-arm failure (RG-P02-007 guard), not a silent downgrade.
4. **Settle.** At the `ARMED → REVOKING` guard the engine calls `settle_check(all_credentials, a_req_candidate, settle_ns)`; if `slack_ns < 0` it waits (`Clock.sleep`) for `−slack_ns` and re-checks.
5. **Expiry bound.** After baselining the engine computes `expiry_bound(c, offset=ClockOffset-for-idp)` for each credential and stores it in the run's derived records (`derivation=calculated`); the exposure analysis and classifier read it (TV-09).
6. **Lifecycle.** The engine appends `CredentialStateRecord`s: `issued` (acquisition), `in_use` (first `access_confirmed` baseline), `rotated` (refresh consumed it; successor created with `parent_ref` = old RT), `expired` (clock passed `hi_mono_ns` — a *claimed* expiry, `basis="clock"`), `revoked_claimed` (an acknowledged `RevocationEvent` whose affected set contains the credential), `revoked_observed` (stable denial `D` exists or an independent oracle reports inactive). No state is ever removed; the current state is `fold_lifecycle`.
7. **Time.** Every instant is a `TimeInstant` of the run clock or a `RemoteInstant` with its receipt instant; this module reads no clock.

## 11. State transitions and invariants

### 11.1 Lifecycle relation

Rank: `issued 0 < in_use 1 < rotated 2 < expired 3 < revoked_claimed 4 < revoked_observed 5`. A record sequence (ordered by `(at.mono_ns, seq)` of the carrying timeline entry) is legal iff each next state has a **strictly greater rank** than the current one, except `in_use → in_use` (repeat use, no record is written) and with the extra constraint that `revoked_observed` requires the immediately preceding state to be `revoked_claimed`.

| from \ to | in_use | rotated | expired | revoked_claimed | revoked_observed |
|---|---|---|---|---|---|
| `issued` | ✔ | ✔ | ✔ | ✔ | — |
| `in_use` | = | ✔ | ✔ | ✔ | — |
| `rotated` | — | — | ✔ | ✔ | — |
| `expired` | — | — | — | ✔ (`moot=true`) | — |
| `revoked_claimed` | — | — | — | — | ✔ |
| `revoked_observed` | — | — | — | — | — (absorbing) |

Natural expiry of an already-revoked credential is not a state change: `expired_by(t)` is a derived predicate (`t > expiry_bound.hi_mono_ns`), recorded as an annotation, never as a lifecycle record.

### 11.2 Invariants

- **INV-1** `family_root_ref == id` iff `parent_ref is None`; otherwise equals the parent's root.
- **INV-2** `parent_ref` chains are acyclic and stay within one `identity_ref`.
- **INV-3** `fold_lifecycle` is a pure function of the ordered record list; rank never decreases along a legal sequence.
- **INV-4** `revoked_observed` is preceded immediately by `revoked_claimed`.
- **INV-5** `expiry_bound` returns `lo ≤ hi`; when two sources are consistent the result is their intersection (width ≤ the tighter source); when disjoint, the union with `sources_conflict=true`.
- **INV-6** `reliable` is `false` for `cookie_attribute` and `none`; the classifier may not use unreliable bounds for `until_exp` verdicts.
- **INV-7** A generation-`g` refresh token has an ancestor chain of exactly `g` refresh tokens of the same family.
- **INV-8** All members of a family share `slot_key`; a probe slot's family is used by no other slot (TV-12).
- **INV-9** Members of one `session_ref` share `identity_ref`; a cookie jar (credential of type `session_cookie`) belongs to exactly one identity (FR-IDP-006).
- **INV-10** Fingerprints are unique within an experiment.
- **INV-11** No model field can hold secret material: allowed strings are grammar-checked ids, fingerprints, ≤ 256-char allow-listed claim values (which are non-secret by construction of the allow-list).
- **INV-12** `settle_check.ok ⇔ a_req.mono − max(finished_at.mono) ≥ settle_ns`.

## 12. Core algorithms and pseudocode

### 12.1 `expiry_bound`

```
def expiry_bound(c, offset=None, receipt_theta_slack_ns=0, expires_in_slack_ns=1_000_000_000):
    cands = []
    if c.lifetime_s is not None and c.expiry_basis != cookie_attribute:
        L = c.lifetime_s * 1_000_000_000
        route A (expires_in):   lo = c.acquired.started_at.mono + L ;  hi = c.acquired.finished_at.mono + L + expires_in_slack_ns
    if c.expires_at is not None and c.expiry_basis != cookie_attribute and offset is not None \
       and offset.method != none and offset.domain == c.expires_at.domain:
        (wlo, whi) = remote_to_local_wall_interval(c.expires_at, offset)               # RG-P02-001 §12.6
        theta = c.expires_at.local_receipt.wall_ns - c.expires_at.local_receipt.mono_ns    # wall→mono map at receipt
        slack = pairing_error(receipt) + receipt_theta_slack_ns                             # + detector divergence if a wall step occurred
        route B (exp claim):    lo = wlo - theta - slack ;  hi = whi - theta + slack
    if not cands: return None
    lo = max(lo_i); hi = min(hi_i)
    if lo <= hi: conflict = False else: lo = min(lo_i); hi = max(hi_i); conflict = True
    return ExpiryBound(basis=<tightest source basis>, lo, hi, reliable=..., sources_conflict=conflict)
```

All route-B arithmetic stays in `Int64`; `receipt_theta_slack_ns` is the engine-supplied `WallStepDetector.max_divergence_ns` observed between receipt and use (0 if none).

**Worked example.** Credential of §8.2: minting bracket `[200 000 000 000, 200 180 000 000]` ns, `lifetime_s = 300`.
Route A: `lo = 200 000 000 000 + 300 000 000 000 = 500 000 000 000`; `hi = 200 180 000 000 + 300 000 000 000 + 1 000 000 000 = 501 180 000 000` (width 1.18 s: 0.18 s response bracket + 1 s `expires_in` truncation slack).
Route B: `exp = 1 791 797 100 s` ⇒ `value_ns = 1 791 797 100 000 000 000`, `resolution = 10⁹`; offset (IdP vs local wall) `+40 ms ± 600 ms`. RG-P02-001 §12.6: `centre = 1 791 797 099 960 000 000`, wall interval `[1 791 797 099 360 000 000, 1 791 797 101 560 000 000]`. Receipt `θ = 1 791 796 800 180 000 000 − 200 180 000 000 = 1 791 796 600 000 000 000`, so mono interval `[499 360 000 000, 501 560 000 000]` (slack 200 ns ignored at this scale).
Combination: `lo = max(500.000, 499.360) = 500.000 s`, `hi = min(501.180, 501.560) = 501.180 s` (mono, run clock), consistent ⇒ `ExpiryBound(lo=500 000 000 000, hi=501 180 000 000, sources_conflict=false, reliable=true)`. If the offset had been `+3 s ± 0.6 s` (a skewed IdP), route B would be `[496.4 s, 498.6 s]` (offset subtracted: `1 791 797 100 − 3 ∓ 0.6 (+1 s resolution on the upper end)`) and disjoint from route A `[500.000 s, 501.180 s]` ⇒ `sources_conflict=true`, bound = union, and RG-P02-006 CF-10 records the large offset.

### 12.2 `fold_lifecycle`

```
def fold_lifecycle(ref, records):
    cur = None
    for r in sorted(records, key=(r.at.mono_ns, r.seq)):
        check r.credential_ref == ref
        if cur is None: cur = r.state; require r.state == issued (else CONFIG-0305)
        else:
            if r.state == in_use and cur == in_use: continue
            if rank(r.state) <= rank(cur): raise CONFIG-0305
            if r.state == revoked_observed and cur != revoked_claimed: raise CONFIG-0305
            if r.state == revoked_claimed and cur == expired: require r.moot
            cur = r.state
    return cur
```

**Worked example.** Records `issued@200.18 s`, `in_use@201.0 s (baseline access_confirmed)`, `revoked_claimed@260.0 s (rev_… acked)`, `revoked_observed@262.4 s (stable denial)` ⇒ final `revoked_observed`. Sequence `issued, revoked_observed` ⇒ `RGE-CONFIG-0305` (observed without claimed). Sequence `issued, expired@500 s, revoked_claimed@510 s` ⇒ legal only with `moot=true`.

### 12.3 Graph construction checks

`CredentialGraph.__init__`: index by id; verify each `parent_ref` exists and shares identity; detect cycles by iterative path-walk with visited set (length ≤ 64); recompute roots and compare with `family_root_ref`; check generation chain (INV-7); check `slot_key` uniformity per family and slot→family injectivity; check fingerprint uniqueness; check session membership identity. All violations list the offending ids in `details`.

### 12.4 `unaffected_siblings(subject, affected)`

```
S = graph.get(subject)
same_shape = lambda c: (c.type, c.format, c.client_ref, c.binding, c.issuer_role) == (S.type, S.format, S.client_ref, S.binding, S.issuer_role)
different   = lambda c: c.identity_ref != S.identity_ref or c.session_ref != S.session_ref   # other principal, or other session of the same principal
return tuple(c for c in sorted(credentials, key=id)
             if c.id != subject and c.id not in affected and same_shape(c) and different(c)
             and c.role in (sibling_control, probe_subject))
```

Semantics (charter glossary "sibling control"): a credential of the same shape that is **not** covered by the event and should therefore keep working; if it stops working during observation, the outage/natural-expiry explanation applies and the experiment is `inconclusive` (RG-P02-009 control rule). Worked example: event = `session_terminated` for session `ses:9c2d…`; credentials A (affected, subject), B (same identity, other session `ses:11aa…`, same client) and C (other identity) ⇒ siblings = `{B, C}` if both have role `sibling_control|probe_subject`; for `account_disabled` of identity X, B is *affected* (same identity), so only C qualifies.

### 12.5 `settle_check`

```
def settle_check(creds, a_req, settle_ns):
    newest = argmax(c.acquired.finished_at.mono_ns for c in creds)       # same clock/epoch as a_req else TIMING-0104
    slack = a_req.mono_ns - newest.acquired.finished_at.mono_ns - settle_ns
    return SettleCheck(ok = slack >= 0, required_ns=settle_ns, slack_ns=slack, newest_credential_ref=newest.id)
```

**Worked example (TV-15).** Newest credential finished minting at mono `200 180 000 000`; planned `A_req = 200 900 000 000`; `settle_ns = 1 000 000 000` ⇒ `slack = 200 900 000 000 − 200 180 000 000 − 1 000 000 000 = −280 000 000` ⇒ `ok=False`; the engine sleeps 280 ms and re-checks; at `A_req = 201 180 000 000` ⇒ `slack = 0`, `ok=True`.
*Why ≥ 1 s suffices* (for providers that test `iat < notBefore` at whole-second resolution, KEYCLOAK.md §1 / R-008): the token's `iat` is the floor to a second of a server time `t_m ≤ finished_at`; `notBefore` is the floor of a server time `t_r ≥ A_req_server`; with `A_req − finished_at ≥ 1 s` on one clock, `t_r ≥ t_m + 1 s` ⇒ `⌊t_r⌋ ≥ ⌊t_m⌋ + 1 > iat`, so the strict inequality holds. Valid for a single-node server clock; multi-node skew is out of this proof (§26 A-3).

## 13. Internal functions, methods, or service operations

```python
def _rank(s: CredentialState) -> int: ...
def _validate_family(by_id: Mapping[str, Credential]) -> None: ...          # INV-1/2/7/8
def _walk_parents(by_id, start: str, limit: int = 64) -> list[str]: ...      # cycle-safe
def _flatten_claims(raw: Mapping[str, Any], paths: Sequence[str]) -> dict[str, ClaimValue]: ...   # dotted-path extraction (used by RG-P04-003 via this module)
def _pairing_error(t: TimeInstant) -> int: ...                               # (read_cost_ns + 1)//2
def _intersect_or_union(intervals: Sequence[tuple[int, int]]) -> tuple[int, int, bool]: ...
```

## 14. Error handling and failure recovery

| Failure | Detection | Handling | Recovery | Code |
|---|---|---|---|---|
| Invalid credential record from an adapter | validators | reject; acquisition step fails (`AUTH`/`INTERNAL` per RG-P04-002) | fix adapter | 0301–0303 |
| Graph inconsistent (cycle, shared slot) | graph ctor | experiment cannot leave `BASELINING` | fix scenario/slot allocation | 0306 |
| Settle not satisfied at arm/revoke | `settle_check` | wait and re-check; `require_settle` raises only if the engine configured `fail` | none needed | 0307 |
| No reliable expiry basis | `expiry_bound` returns None | classifier treats expiry as unknown (no natural-expiry exclusion; `until_exp` rule inapplicable) | provide `expires_in`/JWT | — |
| ClockOffset unavailable | route B skipped | route A only | — | — |
| Lifecycle record out of order | `fold_lifecycle` | raise in strict contexts; `check_lifecycle` returns violations for audit | engine bug fix | 0305 |

Partial-failure semantics: all functions are pure and atomic.

## 15. Security requirements and trust boundaries

- **Secret freedom (TM-07, FR-SEC-005):** no field can carry token/cookie/password material; `claims_allowlist` is allow-list-only with bounded values; `sid`/`jti` are stored because they are identifiers carried inside tokens (non-secret by protocol), but the *token* is represented by its 48-bit fingerprint only. Test TST-12 plants a canary secret in a JWT and asserts it appears in no model, dump, repr or log.
- **Untrusted inputs:** claims come from tokens produced by the target/IdP (hostile possible): size/shape bounds, no nested objects, no unbounded lists, control characters rejected at `ShortText` (TM-11/TM-12).
- **TM-13 / TV-02 support:** `CredentialRole` makes controls explicit so that "all credentials yield the same response" is detectable.
- **TV-12:** the family/slot invariants prevent a refresh probe from consuming a token another observation depends on.
- **Isolation (FR-IDP-006, TM-07):** `INV-9` makes cross-identity cookie-jar sharing unrepresentable.

## 16. Concurrency, asynchronous behavior, and resource ownership

Immutable values and pure functions ⇒ thread/task safe. `CredentialGraph` is immutable after construction; lookups O(1)/O(k). Memory: ≤ `credential.max_credentials` (default 512) × ≈ 2 KiB. No I/O, executors or cancellation points.

## 17. Performance and resource requirements

Proposals, validated by `BM-CRED-1`: graph construction for 512 credentials ≤ 20 ms; `expiry_bound` ≤ 20 µs; `fold_lifecycle` for 20 records ≤ 20 µs. Rationale: one graph per experiment; expiry bounds computed once per credential; nothing here is on the probe hot path.

## 18. Configuration and defaults

| Field | Type | Default | Range | Env var | Notes |
|---|---|---|---|---|---|
| `credential.claims_allowlist_paths` | list[str] | `["iss","sub","aud","azp","client_id","scope","scp","sid","jti","typ","auth_time","acr","amr","ver","roles","groups","realm_access.roles","resource_access.*.roles"]` | ≤ 64 entries, `[A-Za-z0-9_.*-]{1,64}` | `RG_CREDENTIAL_CLAIMS_ALLOWLIST_PATHS` (comma list) | role-like claims are included so snapshot semantics (SCN-01) are inspectable; `*` matches one path segment |
| `credential.expires_in_slack_ns` | int | 1 000 000 000 | 0 … 10 000 000 000 | `RG_CREDENTIAL_EXPIRES_IN_SLACK_NS` | truncation slack for `expires_in` |
| `credential.min_settle_ns` | int | 1 000 000 000 | 1 000 000 000 … 600 000 000 000 | `RG_CREDENTIAL_MIN_SETTLE_NS` | floor; adapters may require more (RG-P04-007); lowering below 1 s is rejected |
| `credential.settle_on_violation` | enum `wait\|fail` | `wait` | | `RG_CREDENTIAL_SETTLE_ON_VIOLATION` | `fail` ⇒ `RGE-CONFIG-0307` |
| `credential.max_credentials` | int | 512 | 1 … 5000 | `RG_CREDENTIAL_MAX_CREDENTIALS` | graph size bound |

Precedence: defaults < file < env < CLI; invalid values `RGE-CONFIG-0301` at load (shared config validation, RG-P03-003).

## 19. Logging, observability, and evidence requirements

Events: `credential.registered` {`credential_ref`, `type`, `format`, `fingerprint`, `role`, `family_root_ref`}; `credential.state` {`credential_ref`, `state`, `basis`}; `credential.settle_wait` {`slack_ns`}; `credential.expiry_bound` {`credential_ref`, `lo_mono_ns`, `hi_mono_ns`, `conflict`}. Evidence: `Credential`/`Session` documents (`kind="credential"|"session"`), lifecycle records as timeline entries, `ExpiryBound` as derived record `algorithm=rg.credential.expiry_bound@1`. Redaction: fingerprints and ids are loggable; claim *values* are logged only for the allow-listed `sub`, `aud`, `azp`, `scope`; never raw tokens.

## 20. Platform compatibility

Pure Python; no platform behaviour. Integer arithmetic only (no float ns). Sorting by `crd_` id string (ULID, ASCII) is platform independent.

## 21. Edge cases and invalid inputs

| # | Case | Expected behaviour |
|---|---|---|
| E-1 | `type=id_token, format=opaque` | `RGE-CONFIG-0302` |
| E-2 | opaque token with `claims_allowlist` set | `RGE-CONFIG-0303` |
| E-3 | `expiry_basis=jwt_exp_claim` but `expires_at=None` | `RGE-CONFIG-0301` |
| E-4 | refresh token whose `parent_ref` is an access token of another identity | `RGE-CONFIG-0306` |
| E-5 | parent cycle A→B→A | `RGE-CONFIG-0306` |
| E-6 | two credentials with equal fingerprints | `RGE-CONFIG-0306` |
| E-7 | two probe slots sharing a `family_root_ref` | `RGE-CONFIG-0306` |
| E-8 | `expires_in = 0` | `lifetime_s=0`; `expiry_bound` hi/lo = bracket; valid |
| E-9 | route B offset from a different domain than the claim | route B skipped |
| E-10 | `settle_check` with an empty credential set | `ok=True`, `newest_credential_ref=None` |
| E-11 | `a_req` from another epoch | `RGE-TIMING-0104` |
| E-12 | lifecycle `issued` repeated | `RGE-CONFIG-0305` |
| E-13 | cookie credential with `Expires` attribute only | `expiry_basis=cookie_attribute`, `reliable=false` |
| E-14 | claim value 300 chars | `RGE-CONFIG-0303` |
| E-15 | `alg:none` token | representable; flagged by RG-P04-003; no special handling here |

## 22. Unit and integration test requirements

| ID | Condition | Expected observation |
|---|---|---|
| TST-RG-P02-003-01 | Validator table E-1, E-2, E-3, E-8, E-14 | codes as stated |
| TST-RG-P02-003-02 | Round-trip JSON of §8.2/§8.4 examples (Hypothesis for field combos) | equality; no `None` serialised; ints as strings |
| TST-RG-P02-003-03 | `expiry_bound` worked example (route A, route B, intersection) | `lo=500 000 000 000`, `hi=501 180 000 000`, `sources_conflict=false` |
| TST-RG-P02-003-04 | `expiry_bound` with skewed offset `+3 s ± 0.6 s` | disjoint ⇒ union, `sources_conflict=true`; cookie_attribute ⇒ `reliable=false`; no basis ⇒ None |
| TST-RG-P02-003-05 | Property: for random acquisition brackets and `expires_in`, route A `hi − lo = (r − s) + slack` and `lo ≤ hi` | INV-5 holds |
| TST-RG-P02-003-06 | Lifecycle table exhaustive 6×6 sequences via `check_lifecycle` | legal set equals §11.1; `revoked_observed` only after `revoked_claimed`; `moot` rule |
| TST-RG-P02-003-07 | Worked example 12.2 sequences | final state / `RGE-CONFIG-0305` as stated |
| TST-RG-P02-003-08 | Graph: lineage RT₀→RT₁→AT, family, descendants order, session members | exact tuples; cycle/shared-slot/duplicate-fp/cross-identity ⇒ `RGE-CONFIG-0306` |
| TST-RG-P02-003-09 | Property: random forests; `family` = same-root set; INV-1/2/7 | holds; generation equals ancestor RT count |
| TST-RG-P02-003-10 | `unaffected_siblings` worked example for `session_terminated` and `account_disabled` | `{B, C}` vs `{C}` |
| TST-RG-P02-003-11 | `settle_check` worked example slack −280 ms then 0; empty set; cross-epoch | `ok` False/True; `RGE-TIMING-0104` |
| TST-RG-P02-003-12 | Secret canary: JWT whose payload carries a planted secret in a non-allow-listed claim and in a 300-char allow-listed claim | non-allow-listed appears only as a name; long value rejected; canary absent from dump/repr/log |
| TST-RG-P02-003-13 | Disposable-family isolation: refresh probe slots A and B with distinct families; then A and B sharing a root | accepted / `RGE-CONFIG-0306` |
| TST-RG-P02-003-14 | Integration (lab virtual time): acquire 3 credentials, settle wait, revoke session, fold lifecycle from timeline | states `revoked_claimed` then `revoked_observed` for the affected, `in_use` for siblings; expiry bound contains the lab-known true expiry instant |

## 23. Mocking and test fixtures

Doubles: scripted `CredentialAcquirer` (rg_lab mock IdP, RG-P09-002) with configurable `expires_in`, rotation; `VirtualClock` for acquisition brackets. Fixtures: `fixtures/credential/jwt_at.json`, `refresh_family.json` (RT₀→RT₁, AT), `skewed_idp_offset.json`, `forests.json`. Hypothesis strategies in `rg_core.testing.strategies.credential`.

## 24. Objective acceptance criteria

- **AC-RG-P02-003-01** Every credential model rejects invalid `(type, format)`, claims on non-JWT tokens, non-allow-listed or oversized claims and malformed fingerprints/ids with the specified codes, and no secret canary is reachable from any serialised form (verified by TST-RG-P02-003-01, TST-RG-P02-003-02, TST-RG-P02-003-12).
- **AC-RG-P02-003-02** `expiry_bound` returns the stated local-mono interval for the worked example, uses intersection when sources agree and union with `sources_conflict` when they disagree, and marks cookie/unknown bases unreliable (verified by TST-RG-P02-003-03, TST-RG-P02-003-04, TST-RG-P02-003-05).
- **AC-RG-P02-003-03** The lifecycle relation accepts exactly the transitions of §11.1 and `fold_lifecycle` yields the specified states (verified by TST-RG-P02-003-06, TST-RG-P02-003-07).
- **AC-RG-P02-003-04** `CredentialGraph` rejects cycles, cross-identity parents, duplicate fingerprints and shared probe-slot families, and answers lineage/family/session/sibling queries per the worked examples (verified by TST-RG-P02-003-08, TST-RG-P02-003-09, TST-RG-P02-003-10, TST-RG-P02-003-13).
- **AC-RG-P02-003-05** `settle_check` reports `slack_ns` exactly as `a_req − newest_finish − settle_ns` and refuses cross-epoch comparisons (verified by TST-RG-P02-003-11).
- **AC-RG-P02-003-06** In the virtual-time lab, lifecycle states derived from the experiment timeline match the injected revocation and the computed expiry bound contains the true expiry (verified by TST-RG-P02-003-14).

## 25. Research sources and engineering rationale

Sources: DATA-MODEL §2.4/§3/§7/§9; PRD FR-TEMP-005, FR-IDP-003/005/006, FR-EXP-005; THREAT-MODEL TV-02/03/09/12/15, TM-07/13; STANDARDS-REFERENCE SV-007, SV-010 (skew bands; `Date`/`exp` resolution), SV-027, SV-032; KEYCLOAK.md §1.8 (strict `iat < notBefore`, whole seconds, V-lab); TECHNICAL-FEASIBILITY R-008; charter glossary (*sibling control*, *baseline*).

- **DEC-1 Expiry as a bracketed *local monotonic* interval.** Chosen because `expires_in` can be bracketed with no clock alignment at all (the token was issued inside the request bracket) and `exp` needs only an interval-valued offset. Rejected: a point `exp` converted with an offset point estimate (would hide ≥ 0.5 s `Date`/NumericDate resolution, SV-047); using wall time directly (wall steps, TM-28). Verification: TST-03/04/05/14.
- **DEC-2 Dominance-rank lifecycle rather than free graph.** Chosen: strictly increasing ranks make illegal histories trivially checkable and make expiry-after-revocation an annotation. Rejected: a full DFA with every edge (more states to test, same semantics). Verification: TST-06/07.
- **DEC-3 `revoked_claimed` vs `revoked_observed` split mirrors the product's epistemic rule** (acknowledgment is not proof of enforcement, SV-005). Verification: TST-07/14.
- **DEC-4 Family root + slot key** instead of a first-class "family" entity (no new id prefix; DATA-MODEL §2.1 is frozen). Verification: TST-08/09/13.
- **DEC-5 Claims allow-list by dotted path** rather than storing whole claim sets (secret/PII leakage, TM-07; size, NFR-PERF-007) while still keeping the role-like claims needed for snapshot-semantics analysis (SCN-01). Rejected: hashing all claims only (no explainability).
- **DEC-6 `expiry_basis=cookie_attribute` is unreliable by construction** (client-side attribute, SV-032 note). Verification: TST-04/E-13.
- **DEC-7 Session is a value entity** keyed by fingerprint (no `ses_` ULID prefix) to avoid a frozen-contract change. Alternative: add the prefix (cleaner ids) — noted as CCR option in §26.

## 26. Remaining uncertainties or assumptions

| # | Assumption | Evidence tag | Falsifying test |
|---|---|---|---|
| A-1 | `expires_in` equals the server's `exp − issue time` truncated to whole seconds, so true remaining lifetime ∈ `[L, L+1 s)` plus the request bracket | I (RFC 6749 §5.1 not read in full: STD-001 §5 is S) | lab test comparing `expires_in` with decoded `exp − iat` on the mock IdP and Keycloak (RG-P09-006): TST-RG-P02-003-14 asserts containment; a miss shows the slack is too small |
| A-2 | Token issuance instant lies inside the request/response bracket of the minting call | I | TST-RG-P02-003-14 (mock IdP stamps its own `iat` on the virtual clock) |
| A-3 | Single-node server clock for the settle proof; multi-node skew can violate it | U (RQ-6) | multi-node lab profile (P09-006) |
| A-4 | `jti`/`sid` values are non-secret identifiers | I (RFC 7519 §4.1.7; OIDC `sid` is an identifier) | review of provider docs per adapter; configurable allow-list lets operators remove them |
| A-5 | 48-bit fingerprints are collision-free enough per experiment; collision handled by re-mint | I | property test over 10⁶ random fingerprints (expect ≤ 1 collision per 10¹⁰) |
| A-6 | Optional CCR-6: introduce prefix `ses` in DATA-MODEL §2.1 if reviewers prefer ULID session ids over fingerprint keys | — | design review; no test |

## 27. Maintainability, portability, and future extension requirements

- **Versioning:** `credential`/`session` documents `1.0`; additive fields are minor. Changing the lifecycle ranks or the `session_ref` derivation is major (stored timelines depend on them).
- **Extension points:** new `ExpiryBasis` values (e.g. `token_exchange_exp`) are additive enum members; new `CredentialRole`s for scenario packs likewise; adapters may add `claims_allowlist_paths` via config.
- **Reuse:** the credential graph + lifecycle are independent of RevocationGap's probes and usable in any token-forensics tool.
- **Deprecation:** `IssuerRole.unknown` is expected to shrink as adapters declare roles; no removal planned.
