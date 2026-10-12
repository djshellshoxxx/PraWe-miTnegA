---
id: RG-P02-002
title: "Identity and permission state model"
phase: "02"
package: core
module_ids: [MOD-CORE-IDENTITY_PERMISSION_STATE]
status: DRAFT
depends_on: [RG-P02-001]
requirements: [FR-TEMP-004, FR-REV-003, FR-REV-004, FR-REV-011, FR-IDP-014, FR-EXP-001, FR-SEC-005, FR-EVD-003]
interfaces_defined: [IF-CORE-AUTHSTATE]
interfaces_used: [IF-CORE-CLOCK, IF-CORE-SERIAL]
schemas_defined: [SCH-IDENTITY]
schemathesis_touchpoints: []
---

# RG-P02-002 — Identity and permission state model

> Scope: the *state* side of "state over time": who a synthetic test principal is (`Identity`), what that principal is allowed at one instant (`AuthorizationState`: account status + effective grants), and the pure algebra over states (`diff`, `apply_change`, `expected_delta`, `verify_delta`). Credentials and sessions are RG-P02-003; the change event itself is RG-P02-004.

## 1. Module identifier and name

| Item | Value |
|---|---|
| Element | RG-P02-002 — Identity and permission state model |
| Package / modules | `rg_core.model.identity` (models), `rg_core.identity.ops` (pure functions) |
| Module id | `MOD-CORE-IDENTITY_PERMISSION_STATE` |
| Schemas | `SCH-IDENTITY`: `Identity`, `AccountStatus`, `GrantKind`, `GrantSource`, `Grant`, `AuthorizationState`, `AuthorizationDelta`, `IdentityChange` |
| Interface | new `IF-CORE-AUTHSTATE` (`AuthorizationStateOps`, §7.2) |

## 2. Phase and requirement references

| Requirement | Realised by |
|---|---|
| FR-TEMP-004 identity/permission state; every tested change is a transition between two states | §8 models, §7.2 `diff`/`apply_change`, §11 |
| FR-REV-003 account disablement/deletion/re-enable; FR-REV-004 role/group/entitlement removal and restore | §12.2 effect table (`IDENTITY_EFFECT`) |
| FR-REV-011 independent verification of the change | §12.4 `verify_delta` (consumed by `RevocationAction.verify`, RG-P06-001) |
| FR-IDP-014 synthetic-only | §9 VR-1 (`is_synthetic` must be `true`), `scope_identity_id` link to RG-P11-002 |
| FR-EXP-001 secret-free spec | `Identity.secrets` holds `SecretHandle`s only |
| FR-SEC-005, FR-EVD-003 | no secret material; each captured state carries `derivation` + `produced_by` |

Threat/validity items realised: **TM-05(c)** (action only on declared-synthetic identities: unrepresentable otherwise), **TM-11/TM-14** (control characters in identity names rejected at the boundary), TV-18 (fresh identities per scenario: `Identity.origin` records provisioning), R-006. Scenarios served: SCN-01 (role removal), SCN-02 (account disablement), SCN-05/-14 (privilege change, reactivation), SCN-10 (service identity).

## 3. Purpose and user/security value

An exposure interval is only meaningful relative to a *defined change of authorization state*. This module gives that change a precise before/after form so that (a) the scenario author states "remove role `rg-group`" as a delta, not prose; (b) after the revocation action the engine can check **independently** (FR-REV-011) that the provider state really changed as intended — a revoke call whose effect cannot be seen in `read_state` must not anchor a measurement (TV-04, SV-005); (c) the model can predict *derived* effects (group removal drops group-derived roles) so unexpected extra or missing changes are reported instead of silently contaminating the experiment; (d) only synthetic, scope-declared identities can be represented, closing a whole class of "disabled the wrong user" failures (R-006, TM-05).

## 4. Explicit responsibilities

- **RESP-1** Define `Identity` (frozen field names of DATA-MODEL §7) with validators, including the mandatory `is_synthetic = true`.
- **RESP-2** Define `AccountStatus`, `GrantKind`, `GrantSource`, `Grant` with a canonical `grant_key` and canonical ordering.
- **RESP-3** Define `AuthorizationState` (frozen field names) with a content digest and provenance.
- **RESP-4** Define the legal `AccountStatus` transition relation.
- **RESP-5** Define `AuthorizationDelta` and the pure `diff(before, after)`.
- **RESP-6** Define the identity-plane effect table (`IDENTITY_EFFECT`) mapping every base `RevocationKind` to its effect on `AuthorizationState` (status change, grant removal, grant addition, or none) and implement `apply_change` / `expected_delta` including derived-grant (`via`) closure.
- **RESP-7** Define `verify_delta(expected, actual)` returning a typed verification result used by revocation actions.
- **RESP-8** State id/prefix rules (`idn_`) and grammar limits for every text field.

## 5. Out-of-scope responsibilities

| Excluded item | Owner |
|---|---|
| Reading provider state (`AdminControl.read_state`), mapping provider fields to `AccountStatus`/`Grant` | RG-P04-001 contract; adapters RG-P04-007…010 |
| Credential/session/token model and lifecycle | RG-P02-003 |
| `RevocationEvent`, `StateChange`, ack states, ordering | RG-P02-004 |
| Scope document, allow-list of synthetic identities, tenant confirmation | RG-P11-002 |
| Secret storage and resolution of `SecretHandle` | RG-P11-001 (`IF-CORE-SECRETS`) |
| Provisioning/cleanup actions (create/delete synthetic user) | RG-P06-003, RG-P06-010 |
| Canonical JSON, digest primitives, `Model` base | RG-P03-002 |
| Judging whether continued access is acceptable | RG-P02-005 / RG-P02-009 |

## 6. Dependencies and prerequisites

- RG-P02-001: `TimeInstant` (state capture time), `RemoteInstant` (grant expiry).
- RG-P03-002 (`IF-CORE-SERIAL`): `Model`, `Document`, `Provenance`, `Int64`, `Count`, `Label`, `ShortText`, `SortedSet`, `SecretHandle`, typed ids (`IdnId`, `PrvId`), `digest`.
- DATA-MODEL §2.1 (id prefixes), §3 (`RevocationKind`, `Derivation`), §7 (entity summary), §9 (invariants).
- Libraries: pydantic v2 only. No I/O.

## 7. External and internal interfaces

### 7.1 Models — see §8. Id prefix rule

`Identity.id` is `idn_<ULID>` created by `IdFactory.new("idn")` (RG-P03-002) when the scenario is instantiated or the experiment provisions the principal; it never derives from `external_subject` (the provider's subject id may be recycled or secret-adjacent). `provider_ref` is `prv_<ULID>`.

### 7.2 `AuthorizationStateOps` — IF-CORE-AUTHSTATE (`rg_core.identity.ops`)

All functions are synchronous, pure, deterministic, thread-safe, idempotent; none reads a clock (the caller passes `TimeInstant`s).

```python
def canonical_grants(grants: Iterable[Grant]) -> tuple[Grant, ...]: ...                    # sort by grant_key; RGE-CONFIG-0206 on duplicate key
def state_digest(identity_ref: str, account_status: AccountStatus, grants: Sequence[Grant]) -> Sha256Digest: ...

def diff(before: AuthorizationState, after: AuthorizationState) -> AuthorizationDelta: ...  # RGE-INTERNAL-0208 if identity_ref differs

def identity_effect(kind: RevocationKind | str) -> IdentityEffect: ...                     # table §12.2; unknown x.* kinds → IdentityEffect.none

def apply_change(state: AuthorizationState, change: IdentityChange, *, at: TimeInstant) -> AuthorizationState: ...
    # model prediction; RGE-CONFIG-0207 (illegal status transition), RGE-CONFIG-0209 (precondition failed)

def expected_delta(state: AuthorizationState, change: IdentityChange) -> AuthorizationDelta: ...   # diff(state, apply_change(state, change, at=state.captured_at))

def verify_delta(expected: AuthorizationDelta, before: AuthorizationState, actual_after: AuthorizationState,
                 *, allow_extra_removals: bool = False) -> DeltaVerification: ...           # §12.4; never raises on mismatch
def legal_status_transition(frm: AccountStatus, to: AccountStatus) -> bool: ...             # §11 table
```

Error codes (block 0200–0299 (RG-P03-005 §8.3); category in the name):

| Code | Name | Raised by |
|---|---|---|
| RGE-CONFIG-0201 | `identity_not_synthetic` (`is_synthetic != true`) | `Identity` validator |
| RGE-CONFIG-0202 | `identity_field_invalid` (subject/labels/secrets grammar or bounds, control characters) | `Identity` validator |
| RGE-CONFIG-0204 | `grant_invalid` (kind/namespace/name grammar, `\|` in a key part, bad `via`/expiry combination) | `Grant` validator |
| RGE-CONFIG-0205 | `state_invalid` (status/grants inconsistent, e.g. `deleted` with grants; `via` pointing to an absent grant) | `AuthorizationState` validator |
| RGE-CONFIG-0206 | `duplicate_grant` (two grants with equal `grant_key`) | `canonical_grants`, `AuthorizationState` validator |
| RGE-CONFIG-0207 | `status_transition_illegal` | `apply_change` |
| RGE-INTERNAL-0208 | `state_identity_mismatch` (`diff`/`verify_delta` on different identities) | ops |
| RGE-CONFIG-0209 | `change_precondition_failed` (removing a grant the state lacks, restoring a grant already present, re-enabling an active account) | `apply_change` |
| RGE-CONFIG-0210 | `change_invalid` (`IdentityChange` shape inconsistent with its kind) | `IdentityChange` validator |

(Handle-grammar failures use `RGE-CONFIG-0020` from RG-P03-002.) Cancellation: not applicable (sync, pure).

## 8. Data structures and schemas

Conventions as in RG-P02-001 §8: models derive from `Model`; ns quantities `Int64`; validator messages begin with the RGE code; JSON omits `None`. `AuthorizationState` is a `Document` (`SCHEMA_ID="authorization_state"`, version `1.0`) with the `Provenance` mixin because it is an observed/derived record that is persisted as evidence; `Identity`, `Grant`, `AuthorizationDelta`, `IdentityChange` are embedded values.

### 8.1 Enumerations

```python
class AccountStatus(str, Enum):      # DATA-MODEL §8 names the enum; values fixed here
    active="active"; disabled="disabled"; suspended="suspended"; locked="locked"; deleted="deleted"; unknown="unknown"
class GrantKind(str, Enum):
    role="role"; group="group"; scope="scope"; entitlement="entitlement"; app_role="app_role"; permission="permission"
class GrantSource(str, Enum):
    direct="direct"; group="group"; composite="composite"; default="default"; policy="policy"
class IdentityEffect(str, Enum):
    status="status"; grant_remove="grant_remove"; grant_add="grant_add"; none="none"
```

| `AccountStatus` | Meaning (provider-neutral) | Typical provider mapping (informative; normative in adapter specs) |
|---|---|---|
| `active` | principal may authenticate and be authorised | Keycloak `enabled=true`; Entra `accountEnabled=true` |
| `disabled` | administratively blocked, reversible, existing sessions *not implied* ended | Keycloak `enabled=false` (V-lab, KEYCLOAK.md §1.2); Entra `accountEnabled=false`; Auth0 `blocked=true` (assumed, RQ-5) |
| `suspended` | temporary hold distinct from disabled | Okta `SUSPENDED` (assumed, RQ-4) |
| `locked` | temporarily locked by brute-force/lockout policy | Keycloak temporary lockout (assumed) |
| `deleted` | principal no longer exists; **terminal for the `Identity` id** | any provider delete |
| `unknown` | provider read failed or status unmapped; never used as a precondition for a verdict | — |

### 8.2 `Identity`

| Field | Type | Constraint | Default | Description |
|---|---|---|---|---|
| `id` | `IdnId` | `idn_` + 26-char ULID | required | stable RG id |
| `provider_ref` | `PrvId` | | required | owning provider instance |
| `external_subject` | ShortText | 1–256 chars, no control chars (`\p{Cc}`), NFC-normalised | required | provider-side subject/username (synthetic) |
| `labels` | `Mapping[Label, ShortText]` | ≤ 32 entries, value ≤ 64 chars | `{}` | scenario annotations (`role:"admin-test"`) |
| `is_synthetic` | `Literal[True]` | must be `true` (RGE-CONFIG-0201) | required | explicit declaration (TM-05 c) |
| `secrets` | `Mapping[Label, SecretHandle]` | ≤ 16 entries, handle grammar | `{}` | `{ "password": "secret:env:RG_ALICE_PASSWORD" }`; **never material** |
| `origin` | `Literal["declared","provisioned"]` | | `declared` | `provisioned` ⇒ created by this experiment (appears in restoration ledger); TV-18 forbids re-enabling provisioned identities as cleanup |
| `scope_identity_id` | `Label \| None` | | None | id of the matching `identities[]` entry in the scope document (RG-P11-002) |
| `display_name` | ShortText \| None | | None | UI only |

```json
{"id": "idn_01M4QJ0B34V37E3S3E28JT97KB", "provider_ref": "prv_01M4QJ0B1J6CQ643DZVMXXQKFB",
 "external_subject": "rg-alice", "labels": {"persona": "rg-lab-user"}, "is_synthetic": true,
 "secrets": {"password": "secret:env:RG_ALICE_PASSWORD"}, "origin": "declared", "scope_identity_id": "alice"}
```

### 8.3 `Grant`

| Field | Type | Constraint | Default | Description |
|---|---|---|---|---|
| `kind` | `ExtKind[GrantKind]` | enum or `x.<vendor>.<name>` | required | |
| `namespace` | Label \| None | no `\|` | None | client id / resource / app (e.g. `rg-rs`); None = realm/tenant-wide |
| `name` | ShortText | 1–128 chars, no `\|`, no control chars | required | role/group/scope/entitlement name |
| `source` | `GrantSource` | | `direct` | how the grant entered the *effective* set |
| `via` | str \| None | a `grant_key` of another grant in the same state; required iff `source ∈ {group, composite}` | None | parent grant (group → role it carries; composite role → child) |
| `expires_at` | `RemoteInstant \| None` | `source` = provider field | None | time-bounded grants (e.g. just-in-time elevation); judged by RG-P08-002, not here |

**`grant_key`** (computed): `"<kind>|<namespace or ''>|<name>"`; example `"role|rg-rs|rg-group"`. Canonical ordering: byte-wise ascending `grant_key`. Validators: V-G1 grammar/`|` ban (RGE-CONFIG-0204); V-G2 `via` rules (0204).

```json
{"kind": "role", "namespace": "rg-rs", "name": "rg-group", "source": "group", "via": "group||rg-g1"}
```

### 8.4 `AuthorizationState` (Document + Provenance)

| Field | Type | Constraint | Default | Description |
|---|---|---|---|---|
| `schema_version` | SchemaVersion | `"1.0"` | | |
| `identity_ref` | `IdnId` | | required | frozen name |
| `account_status` | `AccountStatus` | | required | frozen name |
| `grants` | `tuple[Grant, ...]` | ≤ `identity.max_grants_per_state`; unique `grant_key`; stored in canonical order; every `via` resolves inside the tuple | `()` | **effective** grants (frozen name) |
| `captured_at` | `TimeInstant` | | required | frozen name; instant the read (or declaration) completed |
| `source` | `Literal["provider_read","scenario_declared","derived_model"]` | | required | frozen name |
| `provider_state_token` | ShortText \| None | | None | provider ETag/version if exposed (informational) |
| `state_digest` | `Sha256Digest` | equals `state_digest(...)` of this content | computed | content identity; excludes `captured_at`/provenance, so equal states captured at different times have equal digests |
| `derivation` | `Derivation` | `observed` for `provider_read`, `assumed` for `scenario_declared`, `calculated` for `derived_model` (validated) | derived | provenance mixin |
| `produced_by` | `ProducedBy` | | required | e.g. `{component: "idp.keycloak", version: "1.0"}` |

Validators: V-S1 `deleted` ⇒ `grants == ()` (RGE-CONFIG-0205); V-S2 unique keys (0206); V-S3 `via` resolves (0205); V-S4 `state_digest` matches (0205); V-S5 derivation/source coupling (0205).

```json
{"schema_version": "1.0", "identity_ref": "idn_01M4QJ0B34V37E3S3E28JT97KB", "account_status": "active",
 "grants": [
  {"kind": "group", "name": "rg-g1", "source": "direct"},
  {"kind": "role", "namespace": "rg-rs", "name": "rg-direct", "source": "direct"},
  {"kind": "role", "namespace": "rg-rs", "name": "rg-group", "source": "group", "via": "group||rg-g1"}],
 "captured_at": {"wall_ns": "1791796800123456789", "mono_ns": "5000000000190", "clock_id": "system", "read_cost_ns": "380", "epoch": "a1b2c3d4"},
 "source": "provider_read", "state_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
 "derivation": "observed", "produced_by": {"component": "idp.keycloak", "version": "1.0"}}
```

(The digest value in the example is a placeholder of the correct shape; the test fixture computes the real digest.)

### 8.5 `AuthorizationDelta`, `IdentityChange`, `DeltaVerification`

`AuthorizationDelta`: `status_from`, `status_to` (`AccountStatus`), `grants_added`, `grants_removed` (`tuple[Grant,...]`, canonical order, disjoint by key). Empty delta ⇔ `status_from == status_to` and both tuples empty.

`IdentityChange`: `kind: ExtKind[RevocationKind]`; `grant_key: str | None` (required for `role_removed`, `group_removed`, `entitlement_removed`); `restored: tuple[Grant,...]` (required non-empty for `role_restored`; the model does **not** re-derive composites on restore because the provider's expansion rules are adapter knowledge — callers pass the full set to be added); `note: ShortText | None`. Validator V-C1 (RGE-CONFIG-0210) enforces the per-kind required fields.

`DeltaVerification`: `ok: bool`, `status_ok: bool`, `missing_removals: tuple[str,...]` (grant keys expected removed but present), `missing_additions`, `unexpected_additions` (keys present after but neither before nor expected), `unexpected_removals` (keys absent after, present before, not expected), `notes: tuple[ShortText,...]` (≤ 8).

## 9. Inputs, outputs, and validation rules

| # | Rule | Code |
|---|---|---|
| VR-1 | `Identity.is_synthetic` is `true` | RGE-CONFIG-0201 |
| VR-2 | `external_subject` non-empty, ≤ 256, NFC, no control characters; `labels` ≤ 32 entries/≤ 64-char values; `secrets` ≤ 16 handles matching the handle grammar (grammar failures `RGE-CONFIG-0020`) | RGE-CONFIG-0202 |
| VR-3 | `Grant` field grammar; `\|` forbidden in `namespace`/`name`; `via` iff source ∈ {group, composite}; `kind` is a base value or `x.<vendor>.<name>` | RGE-CONFIG-0204 |
| VR-4 | `AuthorizationState`: `deleted` ⇒ no grants; all `via` resolve; digest matches; derivation matches source | RGE-CONFIG-0205 |
| VR-5 | no two grants share a `grant_key` | RGE-CONFIG-0206 |
| VR-6 | `apply_change` obeys `legal_status_transition` | RGE-CONFIG-0207 |
| VR-7 | `diff`/`verify_delta` only between states of one `identity_ref` | RGE-INTERNAL-0208 |
| VR-8 | change preconditions hold on the input state (§12.2 column "precondition") | RGE-CONFIG-0209 |
| VR-9 | `IdentityChange` carries the fields its kind requires | RGE-CONFIG-0210 |
| VR-10 | number of grants ≤ `identity.max_grants_per_state` | RGE-CONFIG-0205 |

Outputs are new frozen values; inputs are never mutated.

## 10. Detailed execution behavior

1. **Declaration.** The scenario/experiment spec declares `Identity` objects (secret handles only). The scope document must list each `scope_identity_id` as synthetic (RG-P11-002); `Identity` validation alone does not establish authorisation — it only makes non-synthetic principals unrepresentable.
2. **Baseline capture.** During `BASELINING` the engine calls `AdminControl.read_state(identity)` (or builds a `scenario_declared` state for providers without a read API, flagged `assumed`) and stores the `AuthorizationState` as evidence; `captured_at` is the `Clock.now()` taken after the read returns.
3. **Planning.** For a planned `RevocationKind`, `expected_delta(state, change)` is evaluated during dry-run (`VALIDATED`): precondition failures (`RGE-CONFIG-0209`, e.g. "remove a role Alice does not hold") are reported with the other dry-run problems (FR-EXP-002).
4. **Verification.** After execution the action's `verify()` reads the state again and calls `verify_delta(expected, before, after)`; the result feeds `RevocationEvent` verification evidence (RG-P02-004 `StateChange`). A mismatch never raises: it is data (`ok=false`) that lowers confidence (RG-P02-006 CF-18) and is shown in the report.
5. **Restoration.** `role_restored`/`account_reenabled` use the same algebra to compute the expected post-restore state; TV-18 forbids using `account_reenabled` as inter-experiment cleanup for provisioned identities (the cleanup is delete + recreate with a fresh id).
6. **Time.** All instants are `TimeInstant`s of the run's clock; the module never reads time.

## 11. State transitions and invariants

### 11.1 `AccountStatus` transition relation (`legal_status_transition(frm, to)`)

| from \ to | active | disabled | suspended | locked | deleted | unknown |
|---|---|---|---|---|---|---|
| `active` | = | ✔ | ✔ | ✔ | ✔ | ✔ |
| `disabled` | ✔ | = | ✔ | — | ✔ | ✔ |
| `suspended` | ✔ | ✔ | = | — | ✔ | ✔ |
| `locked` | ✔ | ✔ | — | = | ✔ | ✔ |
| `deleted` | — | — | — | — | = | ✔ |
| `unknown` | ✔ | ✔ | ✔ | ✔ | ✔ | = |

`=` is an identity (no change). `deleted` is absorbing except for `unknown` (a failed read). Re-creation of a deleted principal is a **new** `Identity` (new `idn_` id), never a transition.

### 11.2 Invariants

- **INV-1** `AuthorizationState.grants` is in canonical order with unique `grant_key`s; `state_digest` is a function of `(identity_ref, account_status, grants)` only.
- **INV-2** `deleted` ⇒ no grants.
- **INV-3** Every `via` key resolves to a grant in the same state, and the `via` relation is acyclic (depth ≤ 8).
- **INV-4** `diff(a, a)` is the empty delta; `diff(a, b)` has disjoint `grants_added`/`grants_removed` key sets.
- **INV-5** For all valid `(state s, change c)` accepted by `apply_change`: `diff(s, apply_change(s, c)) == expected_delta(s, c)`, and applying the delta's removals/additions and status to `s` reproduces `apply_change(s, c)` (round-trip).
- **INV-6** Removing a grant also removes every grant whose `via` chain reaches it (closure), and nothing else.
- **INV-7** `apply_change` never yields an illegal status transition (§11.1).
- **INV-8** `Identity.is_synthetic` is always `true` in every valid `Identity`.
- **INV-9** `verify_delta(expected, before, after).ok` is `true` when `after == apply_change(before, change)`; it is `false` if any listed removal is still present, any listed addition is absent, the status differs, or an unexpected addition appears.
- **INV-10** All functions are pure: equal inputs ⇒ equal outputs; no argument is mutated.

## 12. Core algorithms and pseudocode

### 12.1 Canonicalisation and digest

```
canonical_grants(gs):  keys = [g.grant_key for g in gs]; if dup(keys): raise CONFIG-0206; return tuple(sorted(gs, key=grant_key))
state_digest(i, s, gs): digest({"identity_ref": i, "account_status": s, "grants": [g.model_dump(mode="json") for g in canonical_grants(gs)]},
                               domain="rg.state.v1")        # domain registered by CONTRACT CHANGE REQUEST CCR-2 (§26)
```

### 12.2 Identity-plane effect table (`IDENTITY_EFFECT`)

| `RevocationKind` | Effect | Status transition | Grant operation | Precondition |
|---|---|---|---|---|
| `account_disabled` | status | `active\|suspended\|locked → disabled` | none | status ∈ {active, suspended, locked} |
| `account_deleted` | status | `* → deleted` | clears all grants | status ≠ deleted |
| `account_reenabled` | status | `disabled\|suspended\|locked → active` | none | status ∈ {disabled, suspended, locked} |
| `service_identity_disabled` | status | as `account_disabled` | none | as above |
| `role_removed` | grant_remove | none | remove `grant_key` + `via` closure; key must be `kind=role` | grant present |
| `group_removed` | grant_remove | none | remove group + closure (group-carried roles) | grant present, `kind=group` |
| `entitlement_removed` | grant_remove | none | remove key + closure; kind ∈ {entitlement, scope, app_role, permission} | grant present |
| `role_restored` | grant_add | none | add `IdentityChange.restored` | none of `restored` present |
| `session_terminated`, `sessions_terminated_all`, `refresh_token_revoked`, `access_token_revoked`, `grant_revoked`, `logout_rp_initiated`, `logout_back_channel`, `password_reset`, `password_changed`, `credential_reset`, `not_before_pushed`, `service_credential_rotated`, `conditional_access_changed`, `device_compliance_changed`, `external_signal` | none | none | none | none (credential/policy/signal plane; effect is on credentials, RG-P02-003/-004) |
| `x.<vendor>.<name>` | none | none | none | none (an adapter may register an effect function through the plugin API; default is `none`) |

### 12.3 `apply_change`

```
def apply_change(s, c, at):
    eff = identity_effect(c.kind)
    status = s.account_status; grants = list(s.grants)
    if eff is status:
        to = {account_disabled: disabled, service_identity_disabled: disabled, account_deleted: deleted, account_reenabled: active}[c.kind]
        check precondition column else CONFIG-0209
        if not legal_status_transition(status, to): raise CONFIG-0207
        status = to; if to is deleted: grants = []
    elif eff is grant_remove:
        root = c.grant_key; if root not in keys(grants): raise CONFIG-0209
        doomed = closure(root)            # fixpoint: {root} ∪ {g | g.via ∈ doomed}
        grants = [g for g in grants if g.key not in doomed]
    elif eff is grant_add:
        if any(g.key in keys(grants) for g in c.restored): raise CONFIG-0209
        grants += c.restored; (validate via-resolution after insertion; CONFIG-0205)
    return AuthorizationState(identity_ref=s.identity_ref, account_status=status, grants=canonical_grants(grants),
                              captured_at=at, source="derived_model", derivation="calculated", produced_by=PRODUCER)
```

**Worked example 1 — group removal with derived role.** State `S0` of `rg-alice` (§8.4 example): grants `{group||rg-g1 (direct), role|rg-rs|rg-direct (direct), role|rg-rs|rg-group (group, via group||rg-g1)}`, status `active`.
`IdentityChange(kind=group_removed, grant_key="group||rg-g1")` ⇒ `closure = {group||rg-g1, role|rg-rs|rg-group}`; predicted state `S1`: grants `{role|rg-rs|rg-direct}`, status `active`; `expected_delta`: `status_from=status_to=active`, `grants_removed=[group||rg-g1, role|rg-rs|rg-group]`, `grants_added=[]`. (The lab realm fixture in KEYCLOAK.md §1.8 defines exactly this identity: realm `rgap`, user `rg-alice`, roles `rg-direct`/`rg-group`, group `rg-g1`; V-lab.)
**Worked example 2 — disablement.** `account_disabled` on `S0`: status `active → disabled`, grants unchanged; delta has empty grant lists and `status_from=active`, `status_to=disabled`.
**Worked example 3 — illegal.** `account_reenabled` on `S0` (status `active`): precondition fails ⇒ `RGE-CONFIG-0209`; `account_disabled` applied to a `deleted` state ⇒ `RGE-CONFIG-0209` (precondition) — `legal_status_transition(deleted, disabled)` is `False` (`RGE-CONFIG-0207` if the precondition check is bypassed).

### 12.4 `verify_delta`

```
def verify_delta(exp, before, after, allow_extra_removals=False):
    require same identity
    status_ok   = (after.account_status == exp.status_to)
    keys_b, keys_a = keys(before.grants), keys(after.grants)
    want_rm  = keys(exp.grants_removed);  want_add = keys(exp.grants_added)
    missing_removals  = sorted(want_rm  & keys_a)
    missing_additions = sorted(want_add - keys_a)
    unexpected_add = sorted((keys_a - keys_b) - want_add)
    unexpected_rm  = sorted((keys_b - keys_a) - want_rm)
    ok = status_ok and not missing_removals and not missing_additions and not unexpected_add \
         and (allow_extra_removals or not unexpected_rm)
```

**Worked example 4.** Expected delta of example 1; actual read after the admin call returns grants `{role|rg-rs|rg-direct}` ⇒ `ok=True`. If the provider keeps `role|rg-rs|rg-group` (stale cache or non-cascading removal) ⇒ `missing_removals=["role|rg-rs|rg-group"]`, `ok=False` (the revocation did not do what the scenario claims; the experiment's exposure claim must say so). If the provider additionally dropped `role|rg-rs|rg-direct` ⇒ `unexpected_rm=["role|rg-rs|rg-direct"]`, `ok=False` unless `allow_extra_removals=True` (used for providers whose group removal cascades through composites the model cannot see).

## 13. Internal functions, methods, or service operations

```python
def _closure(grants: Sequence[Grant], root_key: str) -> frozenset[str]: ...      # fixpoint over `via`; depth ≤ 8 else RGE-CONFIG-0205
def _resolve_via(grants: Sequence[Grant]) -> None: ...                            # validates INV-3 (acyclic, resolvable)
def _status_after(kind: str, status: AccountStatus) -> AccountStatus: ...        # table §12.2
def _key(g: Grant) -> str: ...                                                    # "<kind>|<namespace or ''>|<name>"
def _producer() -> ProducedBy: ...                                                # {component: "rg_core.identity", version: <pkg version>}
```

## 14. Error handling and failure recovery

| Failure | Detection | Handling | Recovery | Code |
|---|---|---|---|---|
| Non-synthetic identity in spec | model validation | spec rejected at load/dry-run | operator corrects spec | RGE-CONFIG-0201 |
| Planned change impossible on current state | `apply_change` preconditions | reported in dry-run, experiment stays `DRAFT` | fix scenario or state | RGE-CONFIG-0209 |
| Provider state read fails | adapter raises PROVIDER error (RG-P04-001) | engine records `account_status=unknown` state with `derivation=observed` and `source=provider_read`, **or** fails baselining per policy | retry (bounded) | n/a here |
| Post-change delta mismatch | `verify_delta.ok == false` | recorded as evidence; CF-18 lowers confidence; no exception | report shows mismatch | none |
| Duplicate/ill-formed grants from adapter | validators | adapter bug surfaced as `RGE-STORE-0020` when persisted | fix adapter | RGE-CONFIG-0204/0205/0206 |
| Cross-identity `diff` call | ops guard | raise | caller bug | RGE-INTERNAL-0208 |

Partial failure: all operations are atomic pure functions; nothing is partially applied.

## 15. Security requirements and trust boundaries

- **Trust boundary:** `Identity` and `Grant` text originates from operator files and provider responses (untrusted): length, character class and `|`-ban validators are the first line against log/terminal/markup injection (TM-11, TM-12, TM-14) and key-collision tricks (`role|x|a` vs a crafted name).
- **TM-05 (c)/R-006:** non-synthetic principals cannot be constructed; `scope_identity_id` ties each identity to a scope allow-list entry that `ScopeEnforcer` checks before any action.
- **Secrets:** `Identity.secrets` stores handles only; the module never resolves them; handle strings that fail the grammar are rejected without echoing the value (RG-P03-002).
- **Provenance:** states read from providers are `observed`; scenario-declared are `assumed` (shown as such in reports, FR-EVD-003); model predictions are `calculated`.
- **Information disclosure:** `labels` and `display_name` are shown in the GUI; they are escaped by renderers (TM-12) and bounded here.

## 16. Concurrency, asynchronous behavior, and resource ownership

All values are immutable; all functions pure ⇒ safe from any thread/task. No locks, I/O or executors. Memory bound: `identity.max_grants_per_state` (default 5000) × ≈ 150 B; `_closure` is O(n·depth) with depth ≤ 8. No cancellation points.

## 17. Performance and resource requirements

Proposals, validated by `BM-IDSTATE-1` (RG-P12-004): `canonical_grants` + `state_digest` for 5 000 grants ≤ 25 ms; `apply_change`/`verify_delta` for 5 000 grants ≤ 10 ms; typical experiments have < 50 grants (negligible). Rationale: states are captured at most a few times per experiment; budgets guard pathological enterprise principals only.

## 18. Configuration and defaults

| Field | Type | Default | Range | Env var | Failure behaviour |
|---|---|---|---|---|---|
| `identity.max_grants_per_state` | int | 5000 | 1 … 100 000 | `RG_IDENTITY_MAX_GRANTS_PER_STATE` | `RGE-CONFIG-0205` on a state exceeding it |
| `identity.max_labels` | int | 32 | 0 … 64 | `RG_IDENTITY_MAX_LABELS` | `RGE-CONFIG-0202` |
| `identity.max_via_depth` | int | 8 | 1 … 16 | `RG_IDENTITY_MAX_VIA_DEPTH` | `RGE-CONFIG-0205` |

Precedence: defaults < file < env < CLI (RG-P03-003). Config is read once at composition.

## 19. Logging, observability, and evidence requirements

Events: `identity.state_captured` {`identity_ref`, `account_status`, `grant_count`, `state_digest`, `source`}; `identity.delta_verified` {`identity_ref`, `kind`, `ok`, `missing_removals_n`, `unexpected_n`}. Evidence items: each `AuthorizationState` is stored as an `EvidenceItem(kind="authorization_state")`; the `DeltaVerification` result is stored as a derived record `derivation=calculated`, algorithm id `rg.identity.verify_delta@1`. Redaction: `external_subject` and `labels` are not secrets and are logged; `secrets` handles are logged only as the handle string (never resolved material). No metric labels contain identity names (cardinality/privacy).

## 20. Platform compatibility

Pure Python; no platform-specific behaviour. Text normalisation uses NFC (`unicodedata`), identical on all platforms; sorting is byte-wise on UTF-8 `grant_key`, independent of locale (never `locale.strxfrm`). JSON encoding UTF-8.

## 21. Edge cases and invalid inputs

| # | Case | Expected behaviour |
|---|---|---|
| E-1 | `Identity(is_synthetic=False)` | `RGE-CONFIG-0201` |
| E-2 | `external_subject` containing `\x1b[31m` or `\n` | `RGE-CONFIG-0202` |
| E-3 | `Grant.name = "a\|b"` | `RGE-CONFIG-0204` |
| E-4 | two grants `role\|\|x` and `role\|\|x` | `RGE-CONFIG-0206` |
| E-5 | `via` pointing to a missing grant | `RGE-CONFIG-0205` |
| E-6 | `via` cycle (A via B, B via A) | `RGE-CONFIG-0205` |
| E-7 | `deleted` state with grants | `RGE-CONFIG-0205` |
| E-8 | `role_removed` for a group key | `RGE-CONFIG-0210` |
| E-9 | `group_removed` on a state without that group | `RGE-CONFIG-0209` |
| E-10 | `account_deleted` then `account_reenabled` on the result | `RGE-CONFIG-0209` (deleted is absorbing) |
| E-11 | `role_restored` with an empty `restored` | `RGE-CONFIG-0210` |
| E-12 | `diff` of states of different identities | `RGE-INTERNAL-0208` |
| E-13 | extension kind `x.entra.cae_policy_changed` | `identity_effect` ⇒ `none`; empty delta |
| E-14 | grant with `expires_at` already past the state's capture | valid; expiry judged elsewhere |
| E-15 | state with 5 001 grants and default limit | `RGE-CONFIG-0205` |

## 22. Unit and integration test requirements

| ID | Condition | Expected observation |
|---|---|---|
| TST-RG-P02-002-01 | Validators table: E-1…E-8, E-11, E-15 | each fails with its code as message prefix; via the registry the wrapped code is `RGE-STORE-0020` |
| TST-RG-P02-002-02 | `AuthorizationState` JSON round-trip of §8.4 (digest recomputed by fixture) | equality; `exclude_none`; grants in canonical order regardless of input order |
| TST-RG-P02-002-03 | `state_digest` property: permuting grants/changing `captured_at`/`produced_by` | digest unchanged; changing any status/grant changes it |
| TST-RG-P02-002-04 | Worked example 1 (`group_removed`) | `expected_delta.grants_removed == [group\|\|rg-g1, role\|rg-rs\|rg-group]`, resulting grants `{role\|rg-rs\|rg-direct}` |
| TST-RG-P02-002-05 | Worked example 2 (`account_disabled`) and examples 3 (`account_reenabled` on active, `disabled` on deleted) | delta as stated; `RGE-CONFIG-0209` for the illegal ones |
| TST-RG-P02-002-06 | Status relation exhaustive 6×6 against §11.1 | `legal_status_transition` equals the table (incl. `deleted→unknown` only) |
| TST-RG-P02-002-07 | Hypothesis: random valid states and valid changes; INV-5 round trip, INV-6 closure minimality, INV-4 | all hold; `diff(s, apply_change(s, c))` equals `expected_delta` |
| TST-RG-P02-002-08 | Hypothesis: random `via` forests (depth ≤ 8) and random removal roots | removed set equals independent reference closure; no grant outside the closure removed |
| TST-RG-P02-002-09 | `verify_delta` worked example 4: matches / stale role / extra removal with and without `allow_extra_removals` | `ok` True / False (`missing_removals`) / False (`unexpected_rm`) / True |
| TST-RG-P02-002-10 | `identity_effect` completeness: every base `RevocationKind` (DATA-MODEL §3) has a table row; `x.*` ⇒ none | no KeyError; table has exactly the enum members |
| TST-RG-P02-002-11 | Purity: functions called twice, inputs deep-compared before/after, run under threads | identical outputs, inputs unchanged |
| TST-RG-P02-002-12 | Secret canary: `Identity.secrets` with a handle whose name embeds a canary string; dump + repr + log | only the handle string appears; no resolved material path exists (no resolver import) |
| TST-RG-P02-002-13 | Control-character fuzz of `external_subject`, `labels`, `Grant.name` (Hypothesis `text()` incl. category Cc/Cf/Cs) | rejected or NFC-normalised; never accepted with Cc characters |
| TST-RG-P02-002-14 | Integration (lab, virtual time): mock IdP admin call `group_removed`, then `read_state` | `verify_delta(...).ok` True; with the lab fault "stale group-role" (RG-P09-004) ⇒ False with the stale key |

## 23. Mocking and test fixtures

Doubles: scripted `AdminControl.read_state` returning prepared `AuthorizationState`s (`rg_core.testing.idstate`); the lab mock IdP (RG-P09-002) for TST-14. Fixtures: `fixtures/identity/alice_s0.json` (§8.4 example with real digest), `fixtures/identity/via_forests.json` (hand-built depth 1…8 forests), `fixtures/identity/invalid_*.json` (E-cases). Random generators for Hypothesis live in `rg_core.testing.strategies.identity`.

## 24. Objective acceptance criteria

- **AC-RG-P02-002-01** No `Identity` with `is_synthetic != true`, with control characters in text fields, or with out-of-bound labels/secrets can be constructed or loaded; each violation yields the specified code (verified by TST-RG-P02-002-01, TST-RG-P02-002-13).
- **AC-RG-P02-002-02** `AuthorizationState` serialises canonically (grants sorted, `None` omitted) and its `state_digest` depends only on `(identity_ref, account_status, grants)` (verified by TST-RG-P02-002-02, TST-RG-P02-002-03).
- **AC-RG-P02-002-03** For every base `RevocationKind` the effect table yields the documented delta, group/composite removal removes exactly the `via` closure, and illegal changes fail with `RGE-CONFIG-0209/0207` (verified by TST-RG-P02-002-04, TST-RG-P02-002-05, TST-RG-P02-002-06, TST-RG-P02-002-08, TST-RG-P02-002-10).
- **AC-RG-P02-002-04** `diff`, `apply_change`, `expected_delta` satisfy the round-trip and purity invariants on randomised inputs (verified by TST-RG-P02-002-07, TST-RG-P02-002-11).
- **AC-RG-P02-002-05** `verify_delta` reports success exactly when the observed after-state matches the prediction and classifies stale, missing and extra changes as specified (verified by TST-RG-P02-002-09, TST-RG-P02-002-14).
- **AC-RG-P02-002-06** No resolved secret material is reachable from any type or function of the module (verified by TST-RG-P02-002-12).

## 25. Research sources and engineering rationale

Sources: DATA-MODEL §2.1/§3/§7/§9; PRD FR-TEMP-004, FR-REV-003/004/011, FR-IDP-014; THREAT-MODEL TM-05/TM-11/TM-14, TV-04, TV-18; STANDARDS-REFERENCE SV-005, SV-033 (account disable vs sessions); KEYCLOAK.md §1.2/§1.8 (disable semantics; lab realm fixture `rgap` with `rg-alice`, `rg-direct`, `rg-group`, `rg-g1`; V-lab); RF-3 (re-enable revives old tokens ⇒ TV-18 rule).

- **DEC-1 Model *effective* grants with a `via` link, not raw assignments.** Chosen because the observable question is "what may the principal do now", and provider reads return effective sets; `via` lets the model predict cascades. Rejected: raw direct assignments only (cannot predict group → role cascade; every provider differs); full provider role-graph model (adapter knowledge, unbounded). Verification: TST-04/07/08.
- **DEC-2 Restore does not re-derive composites.** Chosen: the caller supplies the grants to add. Rejected: model-side composite expansion (needs provider semantics; would claim knowledge the project has not researched, FR-IDP-013). Verification: TST-05, E-11.
- **DEC-3 `deleted` is absorbing; recreation = new id.** Aligns with TV-18 and with providers that cannot undelete; prevents "re-enable" cleanup bugs (RF-3). Verification: TST-06, E-10.
- **DEC-4 Verification is data, not an exception.** `verify_delta` returns `DeltaVerification`; the exposure analysis must still be able to run and label the mismatch. Rejected: raising on mismatch (would convert a measurement fact into a tool failure).
- **DEC-5 Digest excludes `captured_at` and provenance** so identical states captured at different instants compare equal; required for "state unchanged across baseline" checks. Verification: TST-03.
- **DEC-6 `|` as key separator with a ban in parts** rather than escaping: unambiguous, human-readable in evidence, trivially sortable. Rejected: JSON-array keys (unreadable), `:` separator (appears in Entra app-role values).

## 26. Remaining uncertainties or assumptions

| # | Assumption | Evidence tag | Falsifying test |
|---|---|---|---|
| A-1 | Provider `read_state` returns *effective* grants including group-derived roles for Keycloak (the adapter flattens via role-mapping composite endpoints) | I (KEYCLOAK.md documents the endpoints; effective-set read not exercised) | TST-RG-P02-002-14 against the Keycloak lab (RG-P09-006) |
| A-2 | `suspended`/`locked` are distinct, adapter-mappable statuses for Okta/Keycloak; Okta/Auth0 mappings are assumptions (RQ-4/RQ-5) | U | adapter contract tests RG-P04-009/-010 |
| A-3 | A single `GrantKind` set is expressive enough for Entra app roles and Okta entitlements | I | adapter specs; extension kinds `x.*` are the escape hatch |
| A-4 | `via` depth ≤ 8 covers real role hierarchies | I | TST-RG-P02-002-08 boundary at 8 and 9; configurable |
| A-5 | **CCR-2 (contract change request to RG-P03-002):** `DigestDomain` must include `"rg.state.v1"`; until applied, `state_digest` cannot be computed through the documented API | — | `specgate`/review check of RG-P03-002 `DigestDomain` |

## 27. Maintainability, portability, and future extension requirements

- **Versioning:** `AuthorizationState` `1.0`; adding optional fields is minor; changing `grant_key` grammar or the digest composition is major (all stored `state_digest`s and `StateChange` references depend on it).
- **Extension points:** adapters may register an identity-effect function for `x.<vendor>.<name>` kinds through `IF-CORE-PLUGIN` (default `none`); new `GrantKind`s via `x.*`; additional statuses require a DATA-MODEL change (enumeration is closed).
- **Reuse:** the state algebra is provider-independent and reusable for any "who-can-do-what at time t" tooling (state-transition engine, master-prompt reusable component).
- **Deprecation:** none yet. Forward compatibility: unknown `GrantSource`/`GrantKind` values in stored documents of a *higher minor* version are rejected by the registry (RG-P03-002 V4) rather than guessed.
