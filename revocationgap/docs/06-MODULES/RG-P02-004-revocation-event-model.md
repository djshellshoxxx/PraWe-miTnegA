---
id: RG-P02-004
title: "Revocation event model and event ordering"
phase: "02"
package: core
module_ids: [MOD-CORE-REVOCATION_EVENT_MODEL]
status: DRAFT
depends_on: [RG-P02-003]
requirements: [FR-TEMP-006, FR-TEMP-007, FR-REV-002, FR-REV-009, FR-REV-010, FR-REV-011, FR-REV-012, FR-EXP-005, FR-EVD-003]
interfaces_defined: [IF-CORE-EVENTORDER]
interfaces_used: [IF-CORE-CLOCK, IF-CORE-SERIAL, IF-CORE-AUTHSTATE, IF-CORE-CREDGRAPH]
schemas_defined: [SCH-REVOCATION]
schemathesis_touchpoints: []
---

# RG-P02-004 — Revocation event model and event ordering

> Scope: the immutable record of "the state change under test" (`RevocationEvent`), its versioned acknowledgment lifecycle, the **anchor** it contributes to the measurement (`A_req`, `A_ack`, their quality and soundness), the independent-verification record (`StateChange`), the registry of base kinds, and the ordering and anomaly semantics for events (duplicate, delayed, out-of-order). Executing a revocation is RG-P06-001…; recording the anchors at run time is RG-P06-009; correlating provider logs is RG-P08-003.

## 1. Module identifier and name

| Item | Value |
|---|---|
| Element | RG-P02-004 — Revocation event model and event ordering |
| Package / modules | `rg_core.model.revocation` (models), `rg_core.revocation.anchor`, `.ordering`, `.kinds`, `.verification` |
| Module id | `MOD-CORE-REVOCATION_EVENT_MODEL` |
| Schemas | `SCH-REVOCATION`: `RevocationEvent`, `AffectSelector`, `ManualMarkers`, `EventRelation`, `AnchorInterval`, `StateChange`, `EventOrderKey`, `KindInfo` |
| Interface | new `IF-CORE-EVENTORDER` (anchor/ordering/kind/verification pure functions, §7.2) |

## 2. Phase and requirement references

| Requirement | Realised by |
|---|---|
| FR-TEMP-006 event model with kind, subject, affected credentials, `requested_at`, `acknowledged_at`, ack state, actor, claimed effective time, restoration ref | §8.1 |
| FR-TEMP-007 total order `(monotonic instant, sequence)`; duplicated/delayed/out-of-order recorded, not discarded | §8.5 `EventOrderKey`, §12.4 `analyze_arrivals` |
| FR-REV-002 manual M1/M2 anchoring, operator-asserted times `assumed` | §8.3 `ManualMarkers`, §12.1 |
| FR-REV-009 externally observed events, `ack_state=observed`, anchor uncertainty from receipt latency and clock offset | §12.1 external branch |
| FR-REV-010 `requested_at` immediately before dispatch, `acknowledged_at` immediately after acceptance; failed ack ⇒ `inconclusive` | §11 ack lifecycle, §8.1 coupling rules |
| FR-REV-011 independent verification | §8.6 `StateChange`, §12.5 `change_verified` |
| FR-REV-012 restoration ledger reference | `restoration_ref` |
| FR-EXP-005 settle interval (consumer side) | kind registry note; check lives in RG-P02-003 |
| FR-EVD-003 derivation labelling | `requested_at_basis`, `ack_source`, provenance |

Validity rules realised: **TV-06** (anchor = acknowledgment with request→ack uncertainty; manual M1→M2), **TV-04** (acknowledgment is not proof: `change_verified`), **TV-24** (provider logs never the time-of-event source), TV-08 (time via `TimeInstant`), SV-004, SV-005, SV-006, SV-040 (`event_timestamp` = change time, `iat` = creation time). Scenarios: SCN-12, SCN-13, SCN-14 (event ordering and reactivation), all others (every scenario has an event).

## 3. Purpose and user/security value

Every exposure bound is `X_lo = max(0, s_L − A_ack)`, `X_hi = r_D − A_req` (DATA-MODEL §4). If the anchor is wrong the interval is wrong *and looks precise*. This module therefore models the anchor as data with an explicit **quality** and a **soundness flag**: an event whose request instant was measured right before dispatch (`rg_bracketed`) supports both bounds; an event merely *received* from outside (`observed_receipt_only`) supports only the lower bound, because the change may have happened earlier than we heard of it — so the upper-bound claim, and any "enforced"/"within window" verdict that depends on it, are forbidden downstream. It also records acknowledgment as a *versioned lifecycle* (a 200 from an admin API is a claim; an independent read is evidence), and gives duplicated, delayed and reordered events a first-class representation, which is exactly what SCN-12/SCN-13 test in targets.

## 4. Explicit responsibilities

- **RESP-1** Define `RevocationEvent` (frozen field names of DATA-MODEL §7 + additive fields), id rule `rev_`, kind grammar (base kinds + `x.<vendor>.<name>`), actor/ack coupling and the version chain.
- **RESP-2** Define `AffectSelector` variants and `resolve_affected(event, graph)`.
- **RESP-3** Define the acknowledgment lifecycle (`pending → acknowledged | rejected | indeterminate`, `indeterminate → acknowledged | rejected` by verification, `observed`) and `ack_source`.
- **RESP-4** Define `AnchorInterval` and `anchor_interval(event, offset)`: values, quality, soundness, validity, for RG-executed, manual and external events.
- **RESP-5** Define `ManualMarkers` (M1/M2, operator-asserted time as `assumed`).
- **RESP-6** Define `EventOrderKey`, `EventRelation`, dedup key semantics, `analyze_arrivals` and the `ArrivalFlag` vocabulary.
- **RESP-7** Define `StateChange` and `change_verified` (true/false/unknown) used by classification gate B9.
- **RESP-8** Publish the base `RevocationKind` registry (`KindInfo`: plane, default selector, restoration, notes) and extension-kind validation.

## 5. Out-of-scope responsibilities

| Excluded item | Owner |
|---|---|
| Executing actions, `plan/execute/verify/restore`, restoration ledger entries | RG-P06-001 (IF-REV-ACTION), RG-P06-010 |
| Stamping `requested_at`/`acknowledged_at` around the wire call; correlation of anchors with provider logs | RG-P06-009 (IF-REV-ANCHOR), RG-P08-003 |
| Manual-acknowledgment UX and timeouts | RG-P06-002, RG-P10-003 |
| Receiving SETs / provider event streams, signature verification, `jti` dedup at ingestion | RG-P04-011, RG-P06-008 |
| Clock offset estimation | RG-P08-002 |
| Exposure bounds and window computation | RG-P08-004 |
| What access *should* look like after the event | RG-P02-005 |
| Persistence and timeline entries for events | RG-P03-008, RG-P02-008 |
| Identity-plane effect algebra | RG-P02-002 (reused here) |

## 6. Dependencies and prerequisites

RG-P02-001 (`TimeInstant`, `RemoteInstant`, `ClockOffset`, `remote_to_local_wall_interval`, `mono_delta`), RG-P02-002 (`AuthorizationDelta`, `DeltaVerification`, `identity_effect`), RG-P02-003 (`CredentialGraph`, `CredentialRole`), RG-P03-002 (`Model`, `Document`, `Provenance`, `ExtKind`, `RevId`, `Sha256Digest`, `Label`, `ShortText`). DATA-MODEL §2.1, §3 (`RevocationKind`, `AckState`, `ActionClass`), §4, §7, §9.4. Pure Python + pydantic v2; no I/O.

## 7. External and internal interfaces

### 7.1 Id rules

`RevocationEvent.id` = `rev_<ULID>` (`IdFactory.new("rev")`), stable across versions; `(id, version)` is the record key. `action_ref` grammar `^(rev\.[a-z0-9_-]{1,32}\.[a-z0-9_-]{1,32}|manual)(#sha256:[0-9a-f]{64})?$` (action descriptor slug per DATA-MODEL §2.1, optional plan digest; `manual` for operator events). `restoration_ref` is a ledger entry label `^ledger:[0-9]{1,6}$` assigned by RG-P06-001/-010.

### 7.2 Functions — IF-CORE-EVENTORDER (`rg_core.revocation`)

All synchronous, pure, deterministic, thread-safe.

```python
def kind_info(kind: RevocationKind | str) -> KindInfo: ...                                  # §8.7; unknown x.* → generic KindInfo(plane=signal… see §12.6)
def validate_kind(kind: str) -> RevocationKind | str: ...                                    # RGE-CONFIG-0408
def next_version(prev: RevocationEvent, *, ack_state: AckState, acknowledged_at: TimeInstant | None = None,
                 ack_source: AckSource | None = None, **evidence: Any) -> RevocationEvent: ...      # RGE-CONFIG-0402
def anchor_interval(ev: RevocationEvent, *, offset: ClockOffset | None = None, theta_slack_ns: int = 0) -> AnchorInterval: ...   # §12.1; never raises for invalid anchors
def require_anchor(a: AnchorInterval) -> AnchorInterval: ...                                  # RGE-CONFIG-0403 if not valid
def resolve_affected(ev: RevocationEvent, graph: CredentialGraph) -> AffectResolution: ...    # RGE-CONFIG-0404
def order_key(ev: RevocationEvent, seq: int) -> EventOrderKey: ...
def analyze_arrivals(items: Sequence[ArrivalItem], *, offsets: Mapping[str, ClockOffset],
                     late_threshold_ns: int = 5_000_000_000) -> ArrivalAnalysis: ...           # §12.4
def change_verified(sc: StateChange, ev: RevocationEvent, graph: CredentialGraph) -> Tri: ...    # §12.5; Tri = true | false | unknown
```

Error codes (block 0400–0499 (RG-P03-005 §8.3)):

| Code | Name | Raised by |
|---|---|---|
| RGE-CONFIG-0401 | `event_invalid` (grammar, actor/ack coupling, field presence) | `RevocationEvent` validator |
| RGE-CONFIG-0402 | `ack_transition_illegal` (version chain violation) | `next_version` / validator |
| RGE-CONFIG-0403 | `anchor_not_available` (`ack_state ∉ {acknowledged, observed}`) | `require_anchor` |
| RGE-CONFIG-0404 | `affects_unresolvable` (selector names an unknown credential/session/identity) | `resolve_affected` |
| RGE-TIMING-0405 | `ack_before_request` (`acknowledged_at.mono < requested_at.mono`) | validator, `next_version` |
| RGE-CONFIG-0406 | `manual_markers_invalid` | `ManualMarkers` validator |
| RGE-CONFIG-0407 | `state_change_invalid` | `StateChange` validator |
| RGE-CONFIG-0408 | `kind_invalid` (not a base kind and not matching the extension grammar) | `validate_kind` |

Cross-clock arithmetic raises `RGE-TIMING-0104` (RG-P02-001).

## 8. Data structures and schemas

Conventions as RG-P02-001 §8 (frozen `Model`s, `Int64` ns, validator messages prefixed by code, `None` omitted). `RevocationEvent` and `StateChange` are `Document`s (`SCHEMA_ID` `revocation_event`, `state_change`, version `1.0`) with `Provenance`.

### 8.1 `RevocationEvent`

| Field | Type | Constraint | Default | Description |
|---|---|---|---|---|
| `schema_version` | SchemaVersion | `"1.0"` | | |
| `id` | `RevId` | | required | frozen name |
| `version` | Count | ≥ 1 | 1 | additive; record version (immutability: updates are new versions) |
| `experiment_ref` | `ExpId` | | required | |
| `kind` | `ExtKind[RevocationKind]` | base value or `^x\.[a-z0-9][a-z0-9-]{0,30}\.[a-z][a-z0-9_]{0,62}$` | required | frozen name |
| `subject_identity_ref` | `IdnId` | | required | frozen name |
| `affects` | `tuple[AffectSelector, ...]` | 1…`event.max_affects` (64) | required | frozen name (`[CredentialRef \| scope]`), see §8.2 |
| `requested_at` | `TimeInstant` | | required | frozen name; = **`A_req`** (`.mono_ns`) |
| `requested_at_basis` | `Literal["measured","operator_entry","aligned_event_time","receipt"]` | coupled to actor (below) | required | additive; how `requested_at` was obtained |
| `acknowledged_at` | `TimeInstant \| None` | same clock/epoch as `requested_at`; `mono ≥ requested_at.mono` | None | frozen name; = **`A_ack`** |
| `ack_state` | `AckState` | | required | frozen name |
| `ack_source` | `AckSource \| None` | required iff `acknowledged_at` present | None | additive: `provider_reply`, `verification_read`, `operator_confirm`, `receipt` |
| `actor` | `Literal["rg","operator","external"]` | | required | frozen name |
| `action_ref` | str | §7.1 grammar | required | frozen name |
| `manual` | `ManualMarkers \| None` | required iff `actor=operator` | None | M1/M2 and operator-asserted data |
| `provider_event_time` | `RemoteInstant \| None` | | None | frozen name; provider-reported time of the change (or log/creation time per `provider_time_semantics`) |
| `provider_time_semantics` | `Literal["change_time","creation_time","log_time"] \| None` | required iff `provider_event_time` set | None | additive; SV-040: CAEP `event_timestamp` = `change_time`; SET `iat` = `creation_time`; admin/audit log time = `log_time` |
| `claimed_effective_at` | `RemoteInstant \| None` | | None | frozen name; vendor-claimed effect time (e.g. Keycloak `notBefore`) — cross-check only |
| `restoration_ref` | str \| None | `ledger:` grammar | None | frozen name |
| `dedup_key` | ShortText \| None | ≤ 128 | None | provider event id / SET `jti` (external events) |
| `source_name` | Label \| None | | None | event source (`ssf:kc-transmitter`) for external events |
| `relations` | `tuple[EventRelation, ...]` | ≤ 8 | `()` | §8.4 |
| `request_evidence_ref`, `ack_evidence_ref` | `EvdId \| None` | | None | admin request/response exchange evidence |
| `rejection_reason` | Label \| None | only when `ack_state=rejected` | None | e.g. `http_403`, `provider_error`; the value **`unsupported_capability`** is reserved: the action framework (RG-P06-001) sets it when the adapter raises `RGE-PROVIDER-UNSUPPORTED` or the provider answers `unsupported_token_type`; RG-P02-009 rule R-01 maps it to `expected`/not-applicable (TV-10) |
| `derivation` | `Derivation` | `observed` (rg/external), `assumed` for operator-asserted fields (carried in `manual`) | `observed` | provenance mixin |
| `produced_by` | `ProducedBy` | | required | |

**Coupling rules (RGE-CONFIG-0401 unless stated):**

| actor | `ack_state` allowed | `requested_at_basis` | `ack_source` | other |
|---|---|---|---|---|
| `rg` | `pending, acknowledged, rejected, indeterminate` | `measured` | `provider_reply` or `verification_read` | `action_ref` ≠ `manual` |
| `operator` | `pending, acknowledged, rejected, indeterminate` | `operator_entry` | `operator_confirm` | `manual` present; `action_ref = manual` |
| `external` | `observed` only | `aligned_event_time` (requires `provider_event_time.semantics=change_time`) or `receipt` | `receipt` | `acknowledged_at` = receipt instant; `dedup_key`/`source_name` recommended |

State-field presence: `pending` ⇒ no `acknowledged_at`; `acknowledged`/`observed` ⇒ `acknowledged_at` present; `rejected` ⇒ no `acknowledged_at`, `rejection_reason` present; `indeterminate` ⇒ no `acknowledged_at`. Time order: `acknowledged_at.mono ≥ requested_at.mono` (`RGE-TIMING-0405`).

```json
{"schema_version": "1.0", "id": "rev_01M4QJ25K0E0ZBGJ09TQM83XSS", "version": 2, "experiment_ref": "exp_01M4QJ0B00M9S346Q3D25VT4F5",
 "kind": "account_disabled", "subject_identity_ref": "idn_01M4QJ0B34V37E3S3E28JT97KB",
 "affects": [{"selector": "identity", "identity_ref": "idn_01M4QJ0B34V37E3S3E28JT97KB"}],
 "requested_at":    {"wall_ns": "1791796860000000000", "mono_ns": "260000000000", "clock_id": "system", "read_cost_ns": "400", "epoch": "a1b2c3d4"},
 "requested_at_basis": "measured",
 "acknowledged_at": {"wall_ns": "1791796860180000000", "mono_ns": "260180000000", "clock_id": "system", "read_cost_ns": "400", "epoch": "a1b2c3d4"},
 "ack_state": "acknowledged", "ack_source": "provider_reply", "actor": "rg", "action_ref": "rev.account.disable",
 "restoration_ref": "ledger:3",
 "derivation": "observed", "produced_by": {"component": "rg_idp.keycloak", "version": "1.0"}}
```

### 8.2 `AffectSelector` (discriminated on `selector`)

| `selector` | Fields | Resolves to (in a `CredentialGraph`) |
|---|---|---|
| `credential` | `credential_ref` | that credential |
| `session` | `session_ref` | `graph.session_members(session_ref)` |
| `family` | `family_root_ref` | `graph.family(root)` |
| `identity` | `identity_ref` | `graph.of_identity(identity_ref)` |
| `client_grant` | `identity_ref`, `client_ref` | credentials of the identity with `client_ref` |
| `credential_type` | `identity_ref`, `type` | credentials of the identity with that `CredentialType` |
| `scope` | `scope_kind: tenant\|realm\|service`, `scope_id: Label` | all credentials of all identities of that provider scope (realm-wide not-before, conditional access) |
| `unknown` | — | the empty set (external events whose subject cannot be mapped) |

`AffectResolution` = `{targeted: frozenset[CrdId], via_session: frozenset[CrdId], unresolved: tuple[ShortText,...]}`; `targeted` is the **claimed directly-targeted set** (what the provider says it revoked). It does **not** include cascades (an access token minted from a revoked refresh token is *not* targeted by `refresh_token_revoked`; whether it should stop working is an expectation, RG-P02-005, keyed by event kind and credential type — classification facts use `credential.directly_targeted`).

### 8.3 `ManualMarkers`

| Field | Type | Constraint | Description |
|---|---|---|---|
| `m1` | `TimeInstant` | **= `requested_at`** | operator pressed "starting revocation" |
| `m2` | `TimeInstant \| None` | `m2.mono ≥ m1.mono`; same clock | operator pressed "acknowledged" (= `acknowledged_at`) |
| `operator_asserted_time` | `RemoteInstant \| None` | `source=operator_entry` | vendor-console timestamp typed by the operator; **`assumed`**, never an anchor |
| `console_note` | ShortText \| None | | e.g. console path / response text (redacted by renderers) |

Validators (RGE-CONFIG-0406): `m1 == requested_at`; `m2 == acknowledged_at` when both set; ordering. Probes sent in `[m1, m2]` are *ambiguous* (the change may or may not be effective yet); the exposure formulas already neutralise them (`X_lo = max(0, s_L − A_ack)`, §12.1 worked example 2).

### 8.4 `EventRelation`

`kind: Literal["restores","duplicates","supersedes","caused_by"]`, `target_ref: RevId`. `restores`: a `role_restored`/`account_reenabled` event undoing target; `duplicates`: an external event repeating target's `dedup_key`; `supersedes`: a later version of the same logical change from another source; `caused_by`: e.g. a `logout_back_channel` event caused by a `session_terminated`. Relations are descriptive; the engine never executes them.

### 8.5 `EventOrderKey`

`clock_id`, `epoch` (from `requested_at`), `mono_ns` (`requested_at.mono_ns`), `seq` (`Count`: the experiment-timeline sequence number of the event's first entry, RG-P02-008). Total order = lexicographic `(mono_ns, seq)` within one `(clock_id, epoch)`; cross-epoch comparison raises `RGE-TIMING-0104`. Equal `mono_ns` is resolved by `seq` (FR-TEMP-007).

### 8.6 `StateChange` (independent verification record)

| Field | Type | Constraint | Description |
|---|---|---|---|
| `schema_version`, `derivation`, `produced_by` | | `derivation=observed` or `calculated` | |
| `event_ref` | `RevId` | | |
| `event_version` | Count | | version of the event verified |
| `before_ref`, `after_ref` | `Sha256Digest \| None` | `state_digest` values of RG-P02-002 states | states bracketing the change (identity-plane kinds) |
| `delta_verification` | `DeltaVerification \| None` | | RG-P02-002 §8.5 |
| `oracle_checks` | `tuple[OracleCheck, ...]` | ≤ 32 | independent credential-plane checks |
| `verified_by` | `Literal["read_state","oracle","operator","none"]` | | |
| `verified_at` | `TimeInstant \| None` | present iff `verified_by ≠ none` | |

`OracleCheck`: `credential_ref`, `op` (`introspect\|userinfo\|refresh_check\|session_liveness\|read_state`), `verdict` (`active\|inactive\|error\|unsupported\|not_checked`), `at: TimeInstant`, `evidence_ref: EvdId | None`. Validators (RGE-CONFIG-0407): `verified_by=read_state` ⇒ `delta_verification` present; `verified_by=oracle` ⇒ ≥ 1 check with verdict ∈ {active, inactive}; `verified_by=none` ⇒ no `verified_at`.

### 8.7 `AnchorInterval`, `KindInfo`

`AnchorInterval` (computed, not persisted): `event_ref`, `a_req_mono_ns`, `a_ack_mono_ns \| None`, `width_ns \| None` (`a_ack − a_req`), `clock_id`, `epoch`, `valid: bool` (`ack_state ∈ {acknowledged, observed}`), `quality: AnchorQuality`, `upper_bound_sound: bool`, `notes: tuple[Label,...]`.

```python
class AnchorQuality(str, Enum):
    rg_bracketed="rg_bracketed"; manual_bracketed="manual_bracketed"; verification_bracketed="verification_bracketed"
    observed_aligned="observed_aligned"; observed_receipt_only="observed_receipt_only"; none="none"
```

`KindInfo`: `kind`, `plane: Literal["identity","credential","policy","signal"]`, `default_selector: str`, `restorable: bool`, `restoration_note: ShortText`. **Registry of base kinds:**

| kind | plane | default selector | restorable | note |
|---|---|---|---|---|
| `account_disabled`, `service_identity_disabled` | identity | identity | yes (`account_reenabled`) | re-enable revives old tokens in Keycloak (RF-3, V-lab) ⇒ TV-18: never use as inter-experiment cleanup |
| `account_deleted` | identity | identity | no | recreate = new identity |
| `account_reenabled` | identity | identity | — | it is itself a restoration; used by SCN-14 |
| `role_removed`, `group_removed`, `entitlement_removed` | identity | identity | yes (`role_restored`) | |
| `role_restored` | identity | identity | — | |
| `session_terminated` | credential | session | no | |
| `sessions_terminated_all` | credential | identity | no | |
| `refresh_token_revoked`, `access_token_revoked` | credential | credential | no | |
| `grant_revoked` | credential | client_grant | no | |
| `logout_rp_initiated`, `logout_back_channel` | credential | session | no | |
| `password_reset`, `password_changed`, `credential_reset`, `service_credential_rotated` | credential | identity (or credential for service secrets) | no | effect on existing tokens is provider-specific (KEYCLOAK.md: admin reset invalidates nothing, V-lab) |
| `not_before_pushed` | credential | scope | yes (re-push earlier) | whole-second `iat < notBefore` (R-008) |
| `conditional_access_changed`, `device_compliance_changed` | policy | identity | yes | `mutate_policy` action class |
| `external_signal` | signal | unknown→resolved | — | actor `external`, `ack_state=observed` |
| `x.<vendor>.<name>` | `KindInfo` supplied by the adapter; default `signal` | unknown | — | |

Invariant link to RG-P02-002: `plane == "identity"` ⇔ `identity_effect(kind) != none`.

## 9. Inputs, outputs, and validation rules

| # | Rule | Code |
|---|---|---|
| VR-1 | field grammar, actor/ack/basis/source coupling table (§8.1), presence rules per `ack_state` | RGE-CONFIG-0401 |
| VR-2 | `next_version`: same `id`, `version = prev + 1`, `kind/subject/affects/requested_at/actor/action_ref` unchanged; `prev.ack_state ∈ {pending, indeterminate}`; allowed `ack_state` transitions per §11.1 | RGE-CONFIG-0402 |
| VR-3 | `require_anchor` only for `acknowledged`/`observed` events | RGE-CONFIG-0403 |
| VR-4 | every selector resolves in the supplied graph | RGE-CONFIG-0404 |
| VR-5 | `acknowledged_at.mono ≥ requested_at.mono`, same clock/epoch | RGE-TIMING-0405 |
| VR-6 | `ManualMarkers` consistency | RGE-CONFIG-0406 |
| VR-7 | `StateChange` presence rules | RGE-CONFIG-0407 |
| VR-8 | `validate_kind`: base member or extension grammar | RGE-CONFIG-0408 |
| VR-9 | `provider_event_time.semantics` required with `provider_event_time`; `change_time` required for `requested_at_basis=aligned_event_time` | RGE-CONFIG-0401 |
| VR-10 | `requested_at`, `acknowledged_at`, markers share `clock_id` and `epoch` (DATA-MODEL §9.8) | RGE-TIMING-0104 |

## 10. Detailed execution behavior

**Automated (`actor=rg`).** (1) Write-ahead: the action framework (RG-P06-001) appends the restoration-ledger entry and persists `RevocationEvent` **version 1** (`ack_state=pending`, `requested_at = clock.now()` taken immediately before dispatch, `requested_at_basis=measured`) *before* dispatching the request (crash recovery depends on it, RG-P02-007 recovery table). (2) On the provider's acceptance reply the action stamps `acknowledged_at = clock.now()` immediately after the reply is received and persists **version 2** (`acknowledged`, `ack_source=provider_reply`). A reply that is an error persists `rejected` (`rejection_reason`), a timeout/cancellation persists `indeterminate`. (3) `verify()` (independent read, RG-P02-002 §12.4 / oracle) persists a `StateChange`; for an `indeterminate` event whose verification shows the change took effect, **version 3** `acknowledged` with `ack_source=verification_read` and `acknowledged_at` = the verification instant (sound: the change existed no later than that read).
**Manual (`actor=operator`).** The engine persists version 1 `pending` with `requested_at = M1` when the operator presses "starting"; on "acknowledged" persists version 2 with `acknowledged_at = M2`, `ack_source=operator_confirm`. A confirmation timeout persists `indeterminate`. Operator-typed vendor timestamps live only in `manual.operator_asserted_time` (`assumed`).
**External (`actor=external`).** The ingestion element builds one event per distinct `(source_name, dedup_key)` with `ack_state=observed`, `acknowledged_at = receipt instant`, and `requested_at` per §12.1 (aligned or receipt). Duplicates are recorded as separate events with `relations=[duplicates → first]`, not dropped.
**Ordering.** Events are totally ordered by `order_key`; the timeline writer assigns `seq` (RG-P02-008). Time is read only by the callers; this module's functions are pure.

## 11. State transitions and invariants

### 11.1 Acknowledgment lifecycle (version chain)

| from `ack_state` | to | trigger | `ack_source` | Result |
|---|---|---|---|---|
| (none) | `pending` | action about to dispatch / operator "starting" | — | version 1 |
| (none) | `observed` | external event received | `receipt` | version 1 (terminal) |
| `pending` | `acknowledged` | provider acceptance / operator "acknowledged" | `provider_reply` / `operator_confirm` | terminal for anchoring |
| `pending` | `rejected` | provider error reply, operator "failed" | — | terminal; no exposure claim |
| `pending` | `indeterminate` | timeout, cancellation, ambiguous reply | — | resolvable |
| `indeterminate` | `acknowledged` | independent verification shows the change took effect | `verification_read` | terminal (anchor quality `verification_bracketed`) |
| `indeterminate` | `rejected` | independent verification shows no change | — | terminal |

All other transitions are illegal (`RGE-CONFIG-0402`). `acknowledged`, `rejected`, `observed` are terminal.

### 11.2 Invariants

- **INV-1** `acknowledged_at.mono ≥ requested_at.mono`; same `(clock_id, epoch)`.
- **INV-2** `ack_state ∈ {acknowledged, observed}` ⇔ `acknowledged_at` present (and `ack_source` present).
- **INV-3** Version chain: same `id`; versions `1…n` consecutive; immutable fields unchanged across versions.
- **INV-4** `actor=external` ⇒ `ack_state=observed`; `actor=operator` ⇒ `manual` present and `m1 == requested_at`.
- **INV-5** `anchor_interval(ev).valid ⇔ ack_state ∈ {acknowledged, observed}`; when valid, `a_req ≤ a_ack` and `width = a_ack − a_req ≥ 0`.
- **INV-6 (soundness)** `upper_bound_sound` is `False` iff `quality ∈ {observed_receipt_only, none}`; for all other qualities `A_req ≤ E ≤ A_ack` is the stated model assumption (hypothesis-level, DATA-MODEL §4).
- **INV-7** A `RemoteInstant` (`provider_event_time`, `claimed_effective_at`, `operator_asserted_time`, `log_time`/`creation_time` semantics) never determines `a_req`/`a_ack` except `change_time` semantics via a bounded `ClockOffset` (TV-24).
- **INV-8** `order_key` is a strict total order on the events of one experiment/epoch; equal `mono_ns` ⇒ ordered by `seq`.
- **INV-9** `(source_name, dedup_key)` identifies one logical external event; second and later arrivals are flagged `duplicate`, never removed.
- **INV-10** `plane(kind) == identity ⇔ identity_effect(kind) != none`.
- **INV-11** `change_verified` is `true` only if an independent read/oracle supports it; an acknowledgment alone yields `unknown`.

## 12. Core algorithms and pseudocode

### 12.1 `anchor_interval`

```
def anchor_interval(ev, offset=None, theta_slack_ns=0):
    if ev.ack_state not in (acknowledged, observed): return AnchorInterval(valid=False, quality=none, upper_bound_sound=False, ...)
    a_ack = ev.acknowledged_at.mono_ns
    if ev.actor == rg:       a_req = ev.requested_at.mono_ns;  q = rg_bracketed if ev.ack_source == provider_reply else verification_bracketed
    elif ev.actor == operator: a_req = ev.manual.m1.mono_ns;   q = manual_bracketed
    else:                    # external
        pt = ev.provider_event_time
        if pt and ev.provider_time_semantics == change_time and offset bounded and offset.domain == pt.domain:
            (wlo, whi) = remote_to_local_wall_interval(pt, offset)                      # RG-P02-001 §12.6
            theta = pt.local_receipt.wall_ns - pt.local_receipt.mono_ns
            cand = wlo - theta - pairing_error(pt.local_receipt) - theta_slack_ns       # earliest plausible change instant, run-clock mono
            if cand <= a_ack:  a_req = cand; q = observed_aligned
            else:              a_req = a_ack; q = observed_receipt_only; note "event_time_in_future"
        else:                  a_req = a_ack; q = observed_receipt_only
    sound = q != observed_receipt_only
    return AnchorInterval(a_req, a_ack, width=a_ack - a_req, valid=True, quality=q, upper_bound_sound=sound)
```

**Worked example 1 (RG automated, §8.1 event).** `A_req = 260 000 000 000`, `A_ack = 260 180 000 000` ⇒ `width = 180 000 000 ns (0.18 s)`, `quality = rg_bracketed`, sound. With a later `L` at `s_L = 263 000 000 000` and `D` at `r_D = 264 060 000 000`: `X_lo = 263.000 − 260.180 = 2.820 s`, `X_hi = 264.060 − 260.000 = 4.060 s` (algebra in RG-P02-006 §12).
**Worked example 2 (manual).** `M1 = 1 000.0 s`, `M2 = 1 042.5 s` ⇒ `A_req = 1000.0`, `A_ack = 1042.5`, `width = 42.5 s`, `manual_bracketed`. A probe sent at `1 020.0 s` that is still `access_confirmed` has `s_L − A_ack = −22.5 s` ⇒ contributes `X_lo = max(0, −22.5) = 0` (ambiguous window neutralised); a probe at `1 060.0 s` still accepted gives `X_lo = 17.5 s`.
**Worked example 3 (external CAEP).** SET `event_timestamp` (semantics `change_time`) `= 1 791 796 800 s`, resolution 1 s; domain `event-source:kc-transmitter`; `ClockOffset` `0 ± 0.3 s`; received at wall `1 791 796 807.4 s`, mono `207.4 s` ⇒ `θ = 1 791 796 600 s`. Wall interval `[799.7, 801.3 + …)` (`value − 0.3`, `value + 0.3 + 1`), `cand = 1 791 796 799.7 − 1 791 796 600 = 199.7 s`; `A_ack = 207.4 s` ⇒ `observed_aligned`, `A_req = 199.7 s`, `width = 7.7 s` (= 7.4 s delivery latency + 0.3 s lower offset uncertainty), sound. If only the SET `iat` (`creation_time`) is available: `A_req = A_ack = 207.4 s`, `observed_receipt_only`, `upper_bound_sound = False` ⇒ downstream may use `X_lo` but must not derive `X_hi`-based claims.

### 12.2 `resolve_affected`

For each selector, query the graph as in §8.2; unions are returned as frozen sets; an unknown id yields `RGE-CONFIG-0404`; `scope` selectors expand over all identities in the graph with the same `provider_ref` (identity → provider mapping supplied by the graph's credentials' `Session`s/identities); results are deterministic (sorted ids).

### 12.3 `next_version`

Validates §11.1 and INV-3, copies immutable fields, sets `version = prev.version + 1`, applies `ack_state`/`acknowledged_at`/`ack_source`/evidence refs, re-runs validators (including `RGE-TIMING-0405`).

### 12.4 `analyze_arrivals` (duplicated / delayed / out-of-order)

Input `ArrivalItem` = `(event: RevocationEvent, seq: int)` for external events in **arrival order**. For each item compute the local-time interval of its provider time when `provider_time_semantics == change_time` and a bounded offset exists for its domain: `[lo_i, hi_i]` (mono domain, via §12.1's conversion without the `+res` extension on `lo`).

```
flags[i] = {}
seen = {}                                   # (source_name, dedup_key) -> first index
for i in arrival order:
    k = (e_i.source_name, e_i.dedup_key)
    if k in seen: flags[i] += duplicate; duplicate_of[i] = seen[k]
    else: seen[k] = i
    if interval_i known and a_ack_i - lo_i > late_threshold_ns: flags[i] += delayed     # delivery latency lower bound
for each pair (j < i) in arrival order, both intervals known, neither a duplicate:
    if hi_i < lo_j:  flags[i] += out_of_order; inversions += (j, i)      # i is certainly older but arrived later
    elif overlap(i, j): flags[i] += order_indeterminate
```

`ArrivalFlag ∈ {duplicate, delayed, out_of_order, order_indeterminate, event_time_in_future}`. `ArrivalAnalysis` = per-item flags, `duplicate_of`, `inversions`, and two derived orders: `by_receipt` (arrival order) and `by_event_time` (sorted by interval midpoint, ties/overlaps flagged), so a scenario (SCN-13) can state which final state is *intended* (event-time order) and compare it with what the target enforces.

**Worked example.** Offsets 0 ± 0.3 s. Arrivals (mono receipt): E1 `session-revoked` change-time 100.0 s (res 1 s) received 100.4 s; E2 same `jti` as E1 received 100.9 s; E3 `credential-change` change-time 90.0 s received 103.0 s.
Intervals: E1 `[99.7, 101.3]`; E3 `[89.7, 91.3]`. Flags: E2 `duplicate` (of E1); E3: `a_ack − lo = 103.0 − 89.7 = 13.3 s > 5 s` ⇒ `delayed`; `hi_E3 = 91.3 < lo_E1 = 99.7` ⇒ `out_of_order` (older event delivered after a newer one), inversion `(E1, E3)`. `by_receipt = [E1, E2, E3]`, `by_event_time = [E3, E1]` (E2 excluded as duplicate). If E1 and E3 had change-times 100.0 and 100.5 the intervals `[99.7, 101.3]`/`[100.2, 101.8]` overlap ⇒ `order_indeterminate` for both — no ordering verdict is invented.

### 12.5 `change_verified`

```
def change_verified(sc, ev, graph) -> Tri:
    plane = kind_info(ev.kind).plane
    if sc.verified_by == none: return unknown
    if plane == identity:   return true if sc.delta_verification and sc.delta_verification.ok else false
    if plane == credential:
        targeted = resolve_affected(ev, graph).targeted
        v = [c.verdict for c in sc.oracle_checks if c.credential_ref in targeted and c.verdict in (active, inactive)]
        if not v: return unknown
        return true if all(x == inactive for x in v) else false          # any 'active' for a targeted credential ⇒ false (the revoke did not take effect at the authority)
    return true if sc.verified_by == operator else unknown               # policy / signal planes
```

Rationale: `RFC 7009`/Okta-style endpoints answer 200 for garbage (SV-005); only an independent oracle verdict can prove the authority changed state. A `false` result is a *finding about the test* (the revoke failed), never a vulnerability by itself.

### 12.6 Extension kinds

`kind_info("x.vendor.name")` returns the `KindInfo` registered by the adapter plugin (RG-P03-009) or the default `KindInfo(plane="signal", default_selector="unknown", restorable=False)`; `identity_effect` of an extension kind is `none` unless the plugin supplies an effect (RG-P02-002 §27).

## 13. Internal functions, methods, or service operations

```python
def _pairing_error(t: TimeInstant) -> int: ...                       # (read_cost_ns + 1)//2
def _external_interval(ev: RevocationEvent, offset: ClockOffset, theta_slack_ns: int) -> tuple[int, int] | None: ...   # mono interval or None
def _immutable_fields(ev: RevocationEvent) -> tuple[Any, ...]: ...   # for INV-3 comparison
def _dedup_key(ev: RevocationEvent) -> tuple[str | None, str | None]: ...
def _tri_all(verdicts: Iterable[str]) -> Tri: ...
```

## 14. Error handling and failure recovery

| Failure | Detection | Handling | Recovery | Code |
|---|---|---|---|---|
| Provider error reply | action framework builds `rejected` version | no anchor; experiment ends `inconclusive` via the funnel (RG-P02-007/-009) | cleanup per ledger | RGE-CONFIG-0401 only if malformed |
| Reply lost/cancelled | `indeterminate` version | verification attempt; if shows change ⇒ version `acknowledged` (`verification_read`) | else cleanup | — |
| Acknowledgment earlier than request (clock bug, wrong order of stamps) | validator | reject record; action fails `INTERNAL` | fix stamping | RGE-TIMING-0405 |
| Selector refers to unknown credential | `resolve_affected` | dry-run error | fix scenario | RGE-CONFIG-0404 |
| Duplicate/out-of-order external events | `analyze_arrivals` | flags in evidence, not errors | — | — |
| External event with `creation_time` only | `anchor_interval` | `observed_receipt_only`; upper-bound claims disabled | supply `change_time` source | — |
| Crash between version 1 and dispatch | recovery table (RG-P02-007) | version 1 `pending` found; provider read decides: applied ⇒ `indeterminate→acknowledged(verification_read)`; not applied ⇒ `rejected` | restore ledger | — |

## 15. Security requirements and trust boundaries

- **TM-28/TV-08:** all anchors are local `TimeInstant`s of one clock; `RemoteInstant`s are untrusted data and cannot become anchors except through the explicit, bounded, `change_time` path (INV-7).
- **TV-24:** provider log times (`log_time`) and SET creation times never act as time-of-event sources; `claimed_effective_at` is a cross-check only.
- **TV-04/SV-005:** acknowledgment ≠ proof — `change_verified` is `unknown` without independent evidence; classification gate B9 (RG-P02-009) refuses `vulnerable` unless `true`.
- **TM-19…21 (event receivers):** external events carry attacker-influenceable fields (`dedup_key`, provider times); bounds on lengths, duplicate handling that never discards, and soundness flags prevent a forged/old event from tightening a measurement.
- **TM-05:** `subject_identity_ref` must equal the identity the action targeted (checked by RG-P06-001 against the scope; recorded here).
- **Secrets:** none stored; evidence refs point to redacted exchanges.

## 16. Concurrency, asynchronous behavior, and resource ownership

Immutable values and pure functions ⇒ thread-safe. Event versions are appended by the single timeline/store writer (RG-P03-008). `analyze_arrivals` is O(n²) in the number of external events with known intervals (n ≤ `event.max_events_analyzed`, default 2000). No I/O or cancellation points.

## 17. Performance and resource requirements

Proposals validated by `BM-EVT-1`: `anchor_interval` ≤ 20 µs; `resolve_affected` over 512 credentials ≤ 1 ms; `analyze_arrivals` with 500 events ≤ 50 ms. Rationale: executed once per event or at analysis time.

## 18. Configuration and defaults

| Field | Type | Default | Range | Env var | Notes |
|---|---|---|---|---|---|
| `event.max_affects` | int | 64 | 1 … 1024 | `RG_EVENT_MAX_AFFECTS` | selector count |
| `event.late_delivery_threshold_ns` | int | 5 000 000 000 | 0 … 3 600 000 000 000 | `RG_EVENT_LATE_DELIVERY_THRESHOLD_NS` | `delayed` flag threshold |
| `event.max_events_analyzed` | int | 2000 | 10 … 100 000 | `RG_EVENT_MAX_EVENTS_ANALYZED` | `analyze_arrivals` bound; excess ⇒ analysis truncated with note |
| `event.require_change_time_for_alignment` | bool | true | | `RG_EVENT_REQUIRE_CHANGE_TIME_FOR_ALIGNMENT` | `false` would allow creation-time alignment and is **rejected** at load (reserved; keeps INV-7) |

Precedence: defaults < file < env < CLI; invalid ⇒ `RGE-CONFIG-0401` at load.

## 19. Logging, observability, and evidence requirements

Events: `revocation.requested` {`event_ref`, `kind`, `actor`, `version`}, `revocation.acknowledged` {`event_ref`, `ack_state`, `ack_source`, `anchor_width_ns`, `quality`}, `revocation.anomaly` {`event_ref`, `flags`}, `revocation.verified` {`event_ref`, `result`: true|false|unknown}. Metrics: `anchor_width_ns` histogram. Evidence: each event version is an append-only record + timeline entry (kind `revocation`); `StateChange` is an evidence-linked derived record; `AnchorInterval` is derived (`calculated`, algorithm `rg.revocation.anchor@1`). Redaction: `manual.console_note` and `operator_asserted_time` are user-typed; renderers escape; no secrets.

## 20. Platform compatibility

Pure Python; integer arithmetic only. Operator-typed timestamps are parsed by the UX layer into UTC `RemoteInstant`s (no local timezone semantics in this module).

## 21. Edge cases and invalid inputs

| # | Case | Expected behaviour |
|---|---|---|
| E-1 | `actor=external`, `ack_state=acknowledged` | `RGE-CONFIG-0401` |
| E-2 | `pending` with `acknowledged_at` set | `RGE-CONFIG-0401` |
| E-3 | `acknowledged_at` 1 ns before `requested_at` | `RGE-TIMING-0405` |
| E-4 | `next_version` from `acknowledged` | `RGE-CONFIG-0402` |
| E-5 | `next_version` changing `kind` | `RGE-CONFIG-0402` |
| E-6 | `rejected` without `rejection_reason` | `RGE-CONFIG-0401` |
| E-7 | operator event with `m1 ≠ requested_at` | `RGE-CONFIG-0406` |
| E-8 | `aligned_event_time` with `creation_time` semantics | `RGE-CONFIG-0401` |
| E-9 | external event, `ClockOffset.method=none` | `observed_receipt_only`; no exception |
| E-10 | alignment candidate later than receipt (offset overshoot) | `observed_receipt_only` + note `event_time_in_future` |
| E-11 | `kind="x.Vendor.Name"` (uppercase) | `RGE-CONFIG-0408` |
| E-12 | selector `session` with unknown ref | `RGE-CONFIG-0404` |
| E-13 | duplicate external event arriving after the original was `relations`-linked | flagged `duplicate`; both kept |
| E-14 | `change_verified` with `verified_by=none` | `unknown` |
| E-15 | `change_verified`: one targeted oracle `active`, one `inactive` | `false` |
| E-16 | events from different epochs ordered | `RGE-TIMING-0104` |

## 22. Unit and integration test requirements

| ID | Condition | Expected observation |
|---|---|---|
| TST-RG-P02-004-01 | Coupling-table fuzz: all combinations of actor × ack_state × presence of `acknowledged_at`, `ack_source`, `manual`, basis | valid iff in §8.1 table; invalid ones fail with the stated code |
| TST-RG-P02-004-02 | Version chain: legal chains `pending→acknowledged`, `pending→indeterminate→acknowledged`, `pending→indeterminate→rejected`; illegal ones (E-4, E-5, from terminal) | accept / `RGE-CONFIG-0402` |
| TST-RG-P02-004-03 | Worked example 1 (RG automated) | `quality=rg_bracketed`, `a_req=260 000 000 000`, `width=180 000 000`, `upper_bound_sound=True` |
| TST-RG-P02-004-04 | Worked example 2 (manual) incl. `X_lo` contributions for probes at 1 020 s and 1 060 s | `manual_bracketed`, width 42.5 s; `X_lo` 0 and 17.5 s via the DATA-MODEL formula |
| TST-RG-P02-004-05 | Worked example 3 (external aligned) and creation-time variant; E-9, E-10 | `observed_aligned` `a_req=199 700 000 000`, width 7.7 s; `observed_receipt_only` with `upper_bound_sound=False` |
| TST-RG-P02-004-06 | Property (Hypothesis): random valid events ⇒ `a_req ≤ a_ack` and `width = a_ack − a_req`; `valid ⇔ ack_state ∈ {acknowledged, observed}` | INV-5 |
| TST-RG-P02-004-07 | INV-7 negative: `log_time`/`creation_time` provider times and `claimed_effective_at` varied wildly | `anchor_interval` output unchanged (except aligned `change_time` case) |
| TST-RG-P02-004-08 | `resolve_affected`: each selector variant on a fixture graph (session members, family, identity, client_grant, credential_type, scope, unknown) | exact sets; cascade not included (`refresh_token_revoked` does not target the AT); unknown ref ⇒ `RGE-CONFIG-0404` |
| TST-RG-P02-004-09 | `analyze_arrivals` worked example; overlap variant (100.0/100.5) | flags `duplicate`, `delayed`, `out_of_order`; orders `[E1,E2,E3]`/`[E3,E1]`; overlap ⇒ `order_indeterminate` |
| TST-RG-P02-004-10 | Property: permuting arrival order never changes `by_event_time` or the set of duplicates (except which copy is "first") | holds |
| TST-RG-P02-004-11 | `order_key` total order: random events with equal `mono_ns` and distinct `seq`; cross-epoch pair | strict order by `(mono, seq)`; `RGE-TIMING-0104` |
| TST-RG-P02-004-12 | `change_verified` truth table: identity plane (delta ok/not ok), credential plane (inactive / active / mixed / none), policy plane with/without operator, `verified_by=none` | `true/false/unknown` per §12.5 |
| TST-RG-P02-004-13 | Kind registry completeness: every base `RevocationKind` has `KindInfo`; INV-10 against `identity_effect`; extension grammar accept/reject (E-11) | complete and consistent |
| TST-RG-P02-004-14 | `StateChange` validators E-… (`verified_by` ↔ evidence presence) | `RGE-CONFIG-0407` |
| TST-RG-P02-004-15 | Integration (lab virtual time): RG automated disable with injected 180 ms admin latency; manual M1/M2 flow; scripted CAEP delivery with duplicate and reorder | anchors equal the injected latencies exactly; flags as injected; chain persisted/reloaded identical |
| TST-RG-P02-004-16 | Crash-recovery fixture: persisted version 1 `pending` only; provider read says applied / not applied | `next_version` yields `acknowledged(verification_read)` with `verification_bracketed` / `rejected`; chain valid |

## 23. Mocking and test fixtures

Doubles: `ScriptedAdminControl` (rg_lab) with configurable reply latency/errors; scripted `EventSource` delivering SETs with duplicates/reordering (RG-P09-004); `VirtualClock`. Fixtures: `fixtures/revocation/events_v1_v2.json` (§8.1), `manual_m1_m2.json`, `caep_arrivals.json` (§12.4 example), `graph_for_selectors.json`, `state_change_truth_table.json`. Hypothesis strategies in `rg_core.testing.strategies.revocation`.

## 24. Objective acceptance criteria

- **AC-RG-P02-004-01** Every actor/ack-state combination outside the coupling table is rejected with the specified code; legal version chains are accepted and illegal ones rejected with `RGE-CONFIG-0402` (verified by TST-RG-P02-004-01, TST-RG-P02-004-02).
- **AC-RG-P02-004-02** `anchor_interval` reproduces the worked-example values for RG-automated, manual and external events, and never uses `log_time`/`creation_time`/claimed times as anchors (verified by TST-RG-P02-004-03, TST-RG-P02-004-04, TST-RG-P02-004-05, TST-RG-P02-004-06, TST-RG-P02-004-07).
- **AC-RG-P02-004-03** `upper_bound_sound` is `False` exactly for receipt-only/none anchors and `True` otherwise (verified by TST-RG-P02-004-05, TST-RG-P02-004-06).
- **AC-RG-P02-004-04** Duplicated, delayed and out-of-order external events are flagged with the specified flags, none is discarded, and no ordering verdict is produced for overlapping intervals (verified by TST-RG-P02-004-09, TST-RG-P02-004-10).
- **AC-RG-P02-004-05** Event ordering is a strict total order on `(mono_ns, seq)` within an epoch and refuses cross-epoch comparison (verified by TST-RG-P02-004-11).
- **AC-RG-P02-004-06** `change_verified` returns `true` only with independent evidence and `unknown` for bare acknowledgments (verified by TST-RG-P02-004-12, TST-RG-P02-004-14).
- **AC-RG-P02-004-07** In the virtual-time lab the recorded anchors equal the injected request/acknowledgment latencies exactly and crash-recovery of a `pending` event yields the specified versions (verified by TST-RG-P02-004-15, TST-RG-P02-004-16).
- **AC-RG-P02-004-08** `resolve_affected` returns exactly the directly targeted credentials per selector and excludes cascades; the kind registry is complete and consistent with RG-P02-002 (verified by TST-RG-P02-004-08, TST-RG-P02-004-13).

## 25. Research sources and engineering rationale

Sources: DATA-MODEL §3/§4/§9.4; PRD FR-TEMP-006/007, FR-REV-002/009/010/011/012; THREAT-MODEL TV-04/06/24, SCN-12/13/14, TM-19…21; STANDARDS-REFERENCE SV-004 (time zero = acknowledgment), SV-005, SV-006 (503 ⇒ failed step), SV-038/SV-040 (CAEP `event_timestamp` = underlying change time; optional; `iat` = SET creation), SV-037; USER-WORKFLOWS WF-04 (M1/M2), WF-08; KEYCLOAK.md (re-enable revives tokens; V-lab); charter glossary (*anchor*, *acknowledgment*).

- **DEC-1 Anchor quality + soundness flag** rather than a single "uncertainty" number. Chosen: the failure mode of receipt-only anchors is *unsoundness* of the upper bound, not extra width; encoding it as a boolean makes the downstream rule mechanical (RG-P02-009). Rejected: widening by a guessed delivery latency (hidden slack, SC-02); excluding external events (loses SCN-12/-13). Verification: TST-05/07.
- **DEC-2 Versioned immutable events** (same id, `version`) rather than mutable rows: consistent with DATA-MODEL §1 ("updates are new records referencing predecessors") and with write-ahead recovery. Rejected: separate "ack" entity (splits a single semantic object). Verification: TST-02/16.
- **DEC-3 `indeterminate → acknowledged` only via independent verification, anchored at the verification instant.** Sound because the change exists no later than the read that observes it; looser than an ack reply but never wrong. Rejected: promoting on any later provider reply.
- **DEC-4 Manual anchor = M2 with request M1** (FR-REV-002, WF-04); operator-typed vendor times stay `assumed`. Verification: TST-04.
- **DEC-5 Selectors resolve to the *directly targeted* set; cascades are expectations.** Rejected: baking RFC 7009 cascade semantics (RT→AT MAY) into the model — that is provider/profile-dependent (STD-003 §2.1, Okta RF-6).
- **DEC-6 Arrival analysis uses interval separation, not point comparison.** With `Date`/NumericDate resolution and offset uncertainty a point comparison would manufacture orderings (SV-047). Verification: TST-09.
- **DEC-7 `change_verified` three-valued** (true/false/unknown) so "not checked" never silently counts as verified (TV-04). Verification: TST-12.

## 26. Remaining uncertainties or assumptions

| # | Assumption | Evidence tag | Falsifying test |
|---|---|---|---|
| A-1 | The change takes effect inside `[A_req, A_ack]` for RG-executed requests (DATA-MODEL §4 `E`) | hypothesis-level (frozen assumption) | lab ground-truth containment test SC-01 (RG-P12/P09): mock IdP records its internal effective instant; TST-RG-P02-004-15 checks it lies in the anchor |
| A-2 | Operator performs the change between M1 and M2 | assumed | none possible in software; reported as `assumed` in reports |
| A-3 | CAEP `event_timestamp` is the time of the underlying change (SV-040: CAEP per-event text; optional) | V-doc (CAEP 1.0 read, STANDARDS STD-023 V) | conformance test against a transmitter that sets `event_timestamp` ≠ change time (TST in RG-P04-011) |
| A-4 | SSF/Keycloak events carry `jti` usable as `dedup_key` | I (Keycloak SSF experimental, KEYCLOAK.md §1.6) | TST-RG-P02-004-15 with the lab transmitter |
| A-5 | Provider-side `verification_read` reflects effect no earlier than the actual effect (read-your-writes inverse) | I | lab fault "stale read" (RG-P09-004) must produce `rejected`/unknown, not false anchors |
| A-6 | An `indeterminate` outcome for a provider call implies the call may or may not have been applied (at-least-once ambiguity) | I | fault-injection test in RG-P06-001 |

## 27. Maintainability, portability, and future extension requirements

- **Versioning:** `revocation_event`/`state_change` `1.0`; new optional fields minor; new `AckSource`/`AnchorQuality` members minor only if downstream treats unknown members as `unsound`. Changing the coupling table or the version-chain rules is major.
- **Extension points:** adapter-registered `x.<vendor>.<name>` kinds with `KindInfo`/effect functions; new `AffectSelector` variants (additive discriminator values); additional `ArrivalFlag`s.
- **Reuse:** `anchor_interval`/`analyze_arrivals` are provider-independent and reusable in any event-correlation tool (master-prompt "event correlation engine").
- **Deprecation:** none yet; the `observed_receipt_only` mode is expected to be rare once adapters expose change times.
