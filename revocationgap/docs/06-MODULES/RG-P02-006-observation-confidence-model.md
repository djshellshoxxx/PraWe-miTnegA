---
id: RG-P02-006
title: "Observation and confidence model"
phase: "02"
package: core
module_ids: [MOD-CORE-OBSERVATION_CONFIDENCE_MODEL]
status: DRAFT
depends_on: [RG-P02-004]
requirements: [FR-TEMP-009, FR-TEMP-010, FR-TEMP-011, FR-ANA-003, FR-ANA-004, FR-EXP-003, FR-EVD-001, FR-EVD-003, NFR-PERF-001, NFR-PERF-007]
interfaces_defined: [IF-CORE-OBSERVATION]
interfaces_used: [IF-CORE-CLOCK, IF-CORE-SERIAL, IF-CORE-EVENTORDER, IF-CORE-CREDGRAPH]
schemas_defined: [SCH-OBSERVATION]
schemathesis_touchpoints: []
---

# RG-P02-006 — Observation and confidence model

> Scope: what one probe attempt *means* for analysis (`Observation`, its outcome semantics, which fields analysis may rely on), the exact algebra of the exposure-interval **uncertainty decomposition**, the taxonomy of **uncertainty components**, and the catalogue of **confidence factors** with their caps. The exposure algorithm itself (selecting `L`, `D`, computing windows) is RG-P08-004; the numeric scoring pipeline is RG-P08-005; the assertion engine that produces outcomes is RG-P05-006; result normalisation is RG-P05-010.

## 1. Module identifier and name

| Item | Value |
|---|---|
| Element | RG-P02-006 — Observation and confidence model |
| Package / modules | `rg_core.model.observation`, `rg_core.analysis.obsview`, `rg_core.analysis.uncertainty`, `rg_core.analysis.factors` |
| Module id | `MOD-CORE-OBSERVATION_CONFIDENCE_MODEL` |
| Schemas | `SCH-OBSERVATION`: `Observation`, `AssertionOutcome`, `MechanismHint`, `ObservationError`, `ObservationView`, `UncertaintyComponent`, `ConfidenceFactor`, `Confidence` |
| Interface | new `IF-CORE-OBSERVATION` (`observation_view`, `relation_to_anchor`, `verify_decomposition`, `decompose_width` reference oracle, factor catalogue) |

## 2. Phase and requirement references

| Requirement | Realised by |
|---|---|
| FR-TEMP-009 Observation with intended time, send/recv instants, lateness, outcome, assertion results, mechanism hints, evidence ref; confidence from enumerated recorded factors | §8.1, §12.4 catalogue |
| FR-TEMP-010 exposure bounds exactly as DATA-MODEL §4 | §12.2 identity (this spec states the algebra the bounds obey; RG-P08-004 computes them) |
| FR-TEMP-011 confirmation tail semantics | §12.3 tail-counting contract for observations |
| FR-ANA-003 reported width equals the algebraic sum of components | §8.5, §12.2 `verify_decomposition` |
| FR-ANA-004 confidence from control validity, sample count/spacing, lateness, retries/429, clock anomalies, repetition, oracle agreement, deterministic rules per factor | §12.4 |
| FR-EXP-003 baseline/control gate | §12.5 control semantics |
| FR-EVD-001 evidence reference; FR-EVD-003 derivation labelling | `exchange_ref`, `derivation` |
| NFR-PERF-001 lateness recorded on every observation | `scheduling_lateness_ns`, CF-06 |
| NFR-PERF-007 ≤ 2 KiB metadata per observation | §17 budget and TST |

Validity rules realised: **TV-05** (explicit assertions; 200 alone never confirms), TV-07 (confirmation tail, flapping), TV-13 (429/5xx ⇒ indeterminate), TV-14 (cache-served ⇒ indeterminate), TV-17 (malformation/client-auth ⇒ indeterminate), TV-21 (repetition), TV-23 (oracle agreement as a recorded factor), TV-22 (hints only support attribution), TM-13 (identical responses), SV-009, SV-043, SV-047, SV-048, SV-049. Scenarios: all.

## 3. Purpose and user/security value

An observation is the atomic *fact* of the product. If the model lets an HTTP 200, a cache hit, a 429 pause or a transport timeout masquerade as "access confirmed" or "denial", every downstream number is wrong. This module fixes (a) what each `ProbeOutcome` entails about the unknown enforcement instant `T_deny` and what it does **not**, (b) the small set of fields analysis is allowed to read (so evidence can be re-analysed under a newer algorithm without trusting free text), (c) the *exact* additive decomposition of the reported interval width into named components — the guarantee behind charter SC-02 "no hidden slack" — and (d) a finite, auditable catalogue of confidence factors whose caps make "high confidence" mechanically impossible when controls fail, the clock stepped, the schedule was rate-limited, or enforcement flapped.

## 4. Explicit responsibilities

- **RESP-1** Define `Observation` (frozen field names of DATA-MODEL §7 plus additive fields), its validators and the outcome↔field coupling rules.
- **RESP-2** Define the entailment semantics of each `ProbeOutcome` for `T_deny` and the reliance matrix (fields analysis may/may not use) via `ObservationView`.
- **RESP-3** Define `relation_to_anchor` (pre / ambiguous / post) and the usability predicate for bounds.
- **RESP-4** Define the confirmation-tail counting contract (which attempts count as consecutive) for RG-P08-004.
- **RESP-5** Define the uncertainty-component taxonomy, the **exact decomposition identity** (including the `max(0,·)` clamp, the no-`L` case and remote-clock components) with proof and worked examples, and `verify_decomposition`.
- **RESP-6** Define `ConfidenceFactor`/`Confidence` and the catalogue of factors CF-01…CF-21 with measurable inputs, thresholds and level caps.
- **RESP-7** Define control semantics (what a control observation must show to pass).

## 5. Out-of-scope responsibilities

| Excluded item | Owner |
|---|---|
| Choosing `L`/`D`, applying `N_confirm`/`T_confirm`, producing `ExposureWindow` | RG-P08-004 (uses §12.2/§12.3 here) |
| Scoring pipeline implementing the catalogue (`ConfidenceScorer`) | RG-P08-005 |
| Assertion evaluation, `access_confirmed`/`access_denied` decision logic | RG-P05-006 (semantics of the result here) |
| Normalising raw HTTP/WS exchanges, `NormalizedExchange`, cache (`Age`) and rate-limit detection | RG-P05-010, RG-P05-009 |
| Control probes execution and gate | RG-P05-007 (semantics here) |
| Scheduler lateness measurement | RG-P03-006 (value recorded here) |
| Persistence | RG-P03-008 |
| Classification | RG-P02-009 |
| Clock offset estimation | RG-P08-002 |

## 6. Dependencies and prerequisites

RG-P02-001 (`TimeInstant`, `RemoteInstant`, `mono_delta`), RG-P02-003 (credential refs, roles, `ExpiryBound`), RG-P02-004 (`AnchorInterval`, `RevocationKind`, `StateChange`/`Tri`), RG-P03-002 (`Model`, `Document`, `Provenance`, `Int64`, `Count`, `SortedSet`, `Label`, `ObsId`, `PrbId`, `AttId`, `EvdId`, `TgtId`). DATA-MODEL §3 (`ProbeOutcome`, `ProbeCategory`, `ProbeKind`, `ControlKind`, `ConfidenceLevel`), §4, §7, §9.1–9.2. `AssertionResult` fields follow INTERFACE-CONTRACTS §3 (`assertion_id`, `passed`, `role`). Pure Python + pydantic v2.

## 7. External and internal interfaces

### 7.1 IF-CORE-OBSERVATION (`rg_core.analysis`)

All synchronous, pure, deterministic, thread-safe.

```python
def observation_view(o: Observation) -> ObservationView: ...                                   # §8.2 projection
def relation_to_anchor(o: ObservationView, a: AnchorInterval) -> Relation: ...                 # pre | ambiguous | post (§12.1)
def is_usable_for_bounds(o: ObservationView) -> bool: ...                                      # §12.1
def decompose_width(a: AnchorInterval, l: ObservationView | None, d: ObservationView | None,
                    *, clock_offset_ns: int = 0) -> tuple[UncertaintyComponent, ...]: ...      # REFERENCE ORACLE for tests (§12.2); production algorithm: RG-P08-004
def verify_decomposition(components: Sequence[UncertaintyComponent], x_lo_ns: int, x_hi_ns: int) -> None: ...   # RGE-INTERNAL-0606
def factor_catalog() -> Mapping[str, FactorSpec]: ...                                           # CF-01…CF-21 (§12.4)
def apply_caps(factors: Sequence[ConfidenceFactor]) -> ConfidenceLevel: ...                     # level = min of caps (§12.4)
def control_passes(o: ObservationView, kind_or_phase: ControlRole) -> bool: ...                 # §12.5
def denial_family_matches(kind: RevocationKind | str, family: DenialFamily) -> bool: ...        # §12.6
```

Error codes (block 0600–0699 (RG-P03-005 §8.3)):

| Code | Name | Raised by |
|---|---|---|
| RGE-CONFIG-0601 | `observation_invalid` (id/field grammar, bounds, list sizes) | `Observation` validator |
| RGE-TIMING-0602 | `observation_time_invalid` (`t_send_start.mono > t_recv_end.mono`; clocks/epochs differ; `intended_at` after send start) | validator (DATA-MODEL §9.2) |
| RGE-TIMING-0603 | `lateness_invalid` (`scheduling_lateness_ns` negative or ≠ `t_send_start.mono − intended_at.mono` unless `dispatch_lateness` semantics apply) | validator |
| RGE-CONFIG-0604 | `outcome_inconsistent` (outcome vs assertions/denial signal/error/reasons coupling, §9) | validator |
| RGE-CONFIG-0605 | `confidence_factor_invalid` (unknown factor id; effect not allowed for the factor; duplicate factor) | `Confidence` validator |
| RGE-INTERNAL-0606 | `decomposition_mismatch` (Σ additive components ≠ `x_hi − x_lo`) | `verify_decomposition` |

## 8. Data structures and schemas

Conventions as RG-P02-001 §8 (frozen `Model`s; `Int64` ns; validator messages begin with the RGE code; `None` omitted). `Observation` is a `Document` (`SCHEMA_ID="observation"`, `1.0`) with `Provenance` (`derivation="observed"`).

### 8.1 `Observation`

| Field | Type | Constraint | Default | Description |
|---|---|---|---|---|
| `schema_version` | SchemaVersion | `"1.0"` | | |
| `id` | `ObsId` | | required | frozen name |
| `experiment_ref` | `ExpId` | | required | DATA-MODEL §9.1 |
| `probe_ref` | `PrbId` | | required | frozen name |
| `attempt_ref` | `AttId` | | required | additive: the wire-attempt id (`att_`); `attempt_no` counts them |
| `attempt_no` | Count | ≥ 1; increments per `(probe_ref, credential_ref)` in send order | required | frozen name |
| `credential_ref` | `CrdId \| None` | `None` only for `control_kind ∈ {none_credential, garbage_credential}` | required | frozen name |
| `target_ref` | `TgtId` | | required | additive |
| `phase` | `Literal["control","baseline","observe"]` | | required | runner phase (IF-PROBE-RUNNER) |
| `category` | `ProbeCategory` | | required | `resource_access`, `credential_oracle`, `connection_liveness`, `control` |
| `kind` | `ProbeKind` | | required | |
| `control_kind` | `ControlKind \| None` | required iff `category=control` | None | |
| `intended_at` | `TimeInstant` | `mono ≤ t_send_start.mono`; same clock/epoch | required | frozen name; when the schedule meant to send |
| `t_send_start`, `t_recv_end` | `TimeInstant` | `t_send_start.mono ≤ t_recv_end.mono`; same clock/epoch (DATA-MODEL §9.2) | required | frozen names; `[s_i, r_i]` |
| `scheduling_lateness_ns` | Int64 | ≥ 0; `= t_send_start.mono − intended_at.mono` | required | frozen name (end-to-end send lateness: timer + executor queue + preparation) |
| `dispatch_lateness_ns` | Int64 \| None | ≥ 0 | None | additive: timer-only lateness from `ScheduledResult` (RG-P03-006) |
| `outcome` | `ProbeOutcome` | | required | frozen name |
| `indeterminate_reason` | `IndeterminateReason \| None` | required iff `outcome=indeterminate` | None | §8.3 |
| `not_sent_reason` | `NotSentReason \| None` | required iff `outcome=not_sent` | None | §8.3 |
| `error` | `ObservationError \| None` | required iff `outcome=transport_error` | None | frozen name |
| `assertion_results` | `tuple[AssertionOutcome, ...]` | ≤ 16 | `()` | frozen name; id/role/passed only (detail lives in the exchange evidence) |
| `denial_signal` | `DenialSignal \| None` | required iff `outcome=access_denied` | None | frozen name |
| `mechanism_hints` | `tuple[MechanismHint, ...]` | ≤ 8 | `()` | frozen name |
| `exchange_ref` | `EvdId \| None` | `None` iff `outcome=not_sent` | None | frozen name; DATA-MODEL §9.1 |
| `server_date` | `RemoteInstant \| None` | `source=http_date_header` | None | frozen name |
| `connection_reused` | bool \| None | | None | frozen name |
| `http_status` | int \| None | 100…599 | None | additive; informational (§8.2: not a reliance field) |
| `cache_served` | bool | | false | additive: positive `Age` observed (TV-14) |
| `retry_of` | `AttId \| None` | | None | additive: earlier attempt this retried |
| `derivation`, `produced_by` | provenance | `observed` | | |

`AssertionOutcome`: `assertion_id: Label`, `role: Literal["positive_access","denial_signal","guard"]`, `passed: bool`.
`MechanismHint`: `hint: MechanismHintKind`, `source: Label`, `value: Label | Int64 | None` — kinds: `jwt_exp_passed`, `www_authenticate_invalid_token`, `cache_age_header`, `retry_after_present`, `set_cookie_cleared`, `redirect_to_login`, `ws_close_code`, `introspection_inactive`, `refresh_invalid_grant`, `same_response_as_negative_control`.
`ObservationError`: `kind: Literal["timeout_connect","timeout_read","dns","tls","reset","protocol","other"]`, `code: Label`, `retryable: bool`.

```json
{"schema_version": "1.0", "id": "obs_01M4QJ2AF8SS6YS3C4DWA7N360", "experiment_ref": "exp_01M4QJ0B00M9S346Q3D25VT4F5",
 "probe_ref": "prb_01M4QJ0CEW5GQAPENECFSECZP1", "attempt_ref": "att_01M4QJ2AF98VCD1GDJFMGT83PX", "attempt_no": 7,
 "credential_ref": "crd_01M4QJ0CYG4MNPZX45HY43KWJR", "target_ref": "tgt_01M4QJ0B1WF5KZNWJ47TAN9ZT2",
 "phase": "observe", "category": "resource_access", "kind": "http_request",
 "intended_at":  {"wall_ns": "1791796863000000000", "mono_ns": "263000000000", "clock_id": "system", "read_cost_ns": "400", "epoch": "a1b2c3d4"},
 "t_send_start": {"wall_ns": "1791796863002400000", "mono_ns": "263002400000", "clock_id": "system", "read_cost_ns": "400", "epoch": "a1b2c3d4"},
 "t_recv_end":   {"wall_ns": "1791796863045000000", "mono_ns": "263045000000", "clock_id": "system", "read_cost_ns": "400", "epoch": "a1b2c3d4"},
 "scheduling_lateness_ns": "2400000", "outcome": "access_denied", "denial_signal": "www_authenticate_invalid_token",
 "assertion_results": [{"assertion_id": "assert.status-200-marker", "role": "positive_access", "passed": false},
                       {"assertion_id": "assert.www-auth-invalid-token", "role": "denial_signal", "passed": true}],
 "mechanism_hints": [{"hint": "www_authenticate_invalid_token", "source": "assert.www-auth-invalid-token"}],
 "exchange_ref": "evd_01M4QJ2AFJDY0YP57RCYBVN5SX", "connection_reused": true, "http_status": 401, "cache_served": false,
 "derivation": "observed", "produced_by": {"component": "rg_probe.runner", "version": "1.0"}}
```

### 8.2 `ObservationView` — what analysis may rely on

Analysis (RG-P08-004, -005, RG-P02-009) consumes **only** this projection (computed by `observation_view`):

| Field | Source | Reliance |
|---|---|---|
| `obs_id`, `credential_ref`, `target_ref`, `attempt_no`, `phase`, `category`, `kind`, `control_kind` | Observation | identity and grouping |
| `outcome` | Observation | the only evidence of acceptance/denial |
| `s_ns`, `r_ns` | `t_send_start.mono_ns`, `t_recv_end.mono_ns` | the **only** time inputs to bounds (DATA-MODEL §4) |
| `intended_ns`, `lateness_ns`, `dispatch_lateness_ns` | | confidence factors (CF-06) |
| `clock_id`, `epoch` | | same-clock checks |
| `cache_served`, `indeterminate_reason`, `not_sent_reason`, `denial_family` (from `denial_signal`) | | usability/exclusion rules, CF-07/15/16 |
| `read_cost_ns_send`, `read_cost_ns_recv` | | diagnostics only |

**Analysis MUST NOT rely on:** response bodies/headers (they are evidence, re-judged by assertions, not by analysis); `http_status` alone (TV-05); `mechanism_hints` for any bound or verdict (they support *explanations* only, TV-22); `wall_ns` for any duration (DATA-MODEL §2.2 rule 1); `server_date` except through RG-P08-002 alignment; free text of any kind.

### 8.3 Enumerations (additive)

```python
class IndeterminateReason(str, Enum):
    no_marker="no_marker"             # 2xx/expected status but required positive marker absent and no denial signal (TV-05)
    http_5xx="http_5xx"; rate_limited="rate_limited"      # TV-13 (429 or Retry-After)
    cache_served="cache_served"       # positive Age (TV-14)
    malformed_request="malformed_request"      # 400 invalid_request etc. (TV-17)
    client_auth_failure="client_auth_failure"  # 401 invalid_client, wrong presentation (TV-17, SV-049)
    ambiguous_status="ambiguous_status"        # 403/404 without a recognised signal (SV-009)
    redirect_not_followed="redirect_not_followed"; partial_assertions="partial_assertions"; body_truncated="body_truncated"
class NotSentReason(str, Enum): rate_limit="rate_limit"; scope_denied="scope_denied"; cancelled="cancelled"; shutdown="shutdown"; budget_exhausted="budget_exhausted"; pause_window="pause_window"
class DenialFamily(str, Enum): credential_rejected="credential_rejected"; insufficient_privilege="insufficient_privilege"; session_ended="session_ended"; handshake_rejected="handshake_rejected"
class DenialSignal(str, Enum):    # recognised denial signals (SV-009, SV-049, SV-050, SV-055)
    www_authenticate_invalid_token="www_authenticate_invalid_token"; http_401="http_401"; http_403_insufficient_scope="http_403_insufficient_scope"; http_403="http_403"
    oauth_invalid_grant="oauth_invalid_grant"; introspection_inactive="introspection_inactive"; userinfo_401="userinfo_401"; redirect_to_login="redirect_to_login"
    session_expired_marker="session_expired_marker"; ws_handshake_rejected="ws_handshake_rejected"; ws_close_policy="ws_close_policy"; application_marker="application_marker"
```

`DenialSignal → DenialFamily`: `www_authenticate_invalid_token, http_401, oauth_invalid_grant, introspection_inactive, userinfo_401 → credential_rejected`; `http_403_insufficient_scope, http_403 → insufficient_privilege`; `redirect_to_login, session_expired_marker, application_marker → session_ended`; `ws_handshake_rejected, ws_close_policy → handshake_rejected`.

### 8.4 `ConfidenceFactor` and `Confidence`

`FactorEffect ∈ {none, cap_medium, cap_low, cap_none}`. `ConfidenceFactor`: `id` (`^CF-[0-9]{2}$`, in the catalogue), `name` (Label), `value` (`bool | Int64 | Label | float-free ratio as per-mille Int64`), `effect: FactorEffect` (must be one the catalogue allows for that id), `rule_ref: Label` (e.g. `CF-07.r2`), `note: ShortText | None`. `Confidence` (`Model`): `level: ConfidenceLevel`, `factors: tuple[ConfidenceFactor, ...]` (unique ids, ≤ 24, ordered by id), `caps_applied: SortedSet[Label]`, `algorithm_id` (`rg.confidence.rules@1.0.0`), `derivation="calculated"`. Validator (`RGE-CONFIG-0605`): `level == apply_caps(factors)`.

### 8.5 `UncertaintyComponent`

| Field | Type | Description |
|---|---|---|
| `kind` | `UncertaintyKind` | `probe_spacing`, `response_latency_d`, `anchor_request_to_ack`, `clock_offset` (**additive**); `scheduling_lateness_l`, `scheduling_lateness_d`, `read_cost_pairing`, `timestamp_resolution` (**non-additive diagnostics**) |
| `ns` | Int64 | ≥ 0 |
| `additive` | bool | `true` ⇒ counted in Σ |
| `refs` | `tuple[str, ...]` (≤ 4) | ids of the observations/event that determine it |
| `derivation` | `Derivation` | `calculated` |

`ExposureWindow.uncertainty_components[]` (RG-P08-004, SCH-WINDOW) is `tuple[UncertaintyComponent, ...]` exactly as defined here.

## 9. Inputs, outputs, and validation rules

Outcome ↔ field coupling (**RGE-CONFIG-0604**), derived from DATA-MODEL §3 and TV-05/13/14/17:

| `outcome` | Required | Forbidden / constraints |
|---|---|---|
| `access_confirmed` | `assertion_results` non-empty; **every** `positive_access` assertion has `passed=true` and at least one exists; no `denial_signal` assertion passed | `denial_signal`, `indeterminate_reason`, `not_sent_reason`, `error` all absent; `cache_served=false` |
| `access_denied` | `denial_signal` present; at least one `denial_signal`-role assertion `passed=true`; **no** `positive_access` assertion passed | `indeterminate_reason`, `not_sent_reason`, `error` absent; `cache_served=false` |
| `indeterminate` | `indeterminate_reason` | `denial_signal`, `not_sent_reason`, `error` absent; `cache_served=true` ⇒ reason `cache_served`; reason `rate_limited` ⇒ `http_status ∈ {429, …}` or a `retry_after_present` hint |
| `transport_error` | `error` | `denial_signal`, `indeterminate_reason`, `not_sent_reason` absent; `http_status` absent |
| `not_sent` | `not_sent_reason`; `t_send_start == t_recv_end` | `exchange_ref`, `http_status`, `denial_signal`, `error`, `assertion_results` absent |

| # | Rule | Code |
|---|---|---|
| VR-1 | id/field grammar, list bounds (`assertion_results ≤ 16`, `mechanism_hints ≤ 8`), `credential_ref=None` only for none/garbage controls, `control_kind` iff `category=control` | RGE-CONFIG-0601 |
| VR-2 | `t_send_start.mono ≤ t_recv_end.mono`; same `(clock_id, epoch)` for `intended_at`, send, recv; `intended_at.mono ≤ t_send_start.mono` | RGE-TIMING-0602 |
| VR-3 | `scheduling_lateness_ns ≥ 0` and equal to `t_send_start.mono − intended_at.mono` | RGE-TIMING-0603 |
| VR-4 | outcome coupling table above | RGE-CONFIG-0604 |
| VR-5 | `Confidence`: factor ids in catalogue, one per id, effect allowed, `level == apply_caps(...)` | RGE-CONFIG-0605 |
| VR-6 | decomposition identity (reference/verification function) | RGE-INTERNAL-0606 |

## 10. Detailed execution behavior

1. **Creation (probe runner, RG-P05-014).** The runner builds the `Observation` after the transport returns: `intended_at` from the schedule, `t_send_start`/`t_recv_end` from `Clock.now()` taken in the worker adjacent to the wire call (RG-P05-004), `scheduling_lateness_ns = t_send_start.mono − intended_at.mono`, outcome from the assertion engine (RG-P05-006) after normalisation (RG-P05-010: cache-served and rate-limit detection), `exchange_ref` to the redacted exchange evidence. It is persisted append-only before the engine reacts (NFR-REL-001).
2. **Views.** Analysis calls `observation_view` per observation; nothing else of the record is read by analysis.
3. **Decomposition.** RG-P08-004 computes bounds and components; its tests compare against `decompose_width`; at run time the exposure calculator asserts `verify_decomposition` before publishing (an internal error otherwise — a published width that is not the sum of its parts is a bug, never a rounding).
4. **Confidence.** RG-P08-005 evaluates each factor of the catalogue from the window, observations, event and controls and builds the `Confidence`; `apply_caps` is the only place the level is computed.
5. **Time.** All instants are `TimeInstant`s of the run clock; this module reads no clock.

## 11. State transitions and invariants

Observations are immutable and have no lifecycle. Invariants:

- **INV-1** `t_send_start.mono ≤ t_recv_end.mono`; `intended_at.mono ≤ t_send_start.mono`; one `(clock_id, epoch)` per observation (DATA-MODEL §9.2).
- **INV-2** `scheduling_lateness_ns = t_send_start.mono − intended_at.mono ≥ 0`.
- **INV-3** Outcome coupling (§9) holds; `access_confirmed` ⇒ *all* required positive assertions passed and none of the denial assertions; `access_denied` ⇒ a recognised signal and *no* positive assertion passed (DATA-MODEL §3).
- **INV-4** `not_sent` observations have `t_send_start == t_recv_end` and no exchange evidence.
- **INV-5** `attempt_no` is strictly increasing in send order per `(probe_ref, credential_ref)`; retries are new attempts (`retry_of`), never edits.
- **INV-6** `cache_served=true` ⇒ `outcome=indeterminate` with reason `cache_served` (never confirmed, never denied; TV-14).
- **INV-7** `ObservationView` is a total function of one `Observation`; it contains no body/header/free-text field.
- **INV-8 (decomposition identity)** For any anchor `(A_req, A_ack)` with `A_req ≤ A_ack`, any `L` with `s_L ≥ A_req` (or none) and any `D` with `s_D > s_L` (or after `A_req`) and `r_D ≥ s_D`: `Σ additive components = X_hi − X_lo` **exactly** (integers), with `X_lo = max(0, s_L − A_ack)` (0 if no `L`) and `X_hi = r_D − A_req`.
- **INV-9** Non-additive components never enter the sum; additive components are non-negative.
- **INV-10** `Confidence.level = min(caps)`; with no caps the level is `high`; a factor with effect `cap_none` makes the level `none`.
- **INV-11** A confidence level can only be lowered by adding a factor; adding factors never raises it (monotonicity; property test).
- **INV-12** Compact canonical `Observation` JSON (no bodies) has a mean size ≤ 2 048 bytes over the generated corpus and no single observation exceeds 4 096 bytes (NFR-PERF-007 budget; TST-RG-P02-006-13).

## 12. Core algorithms and pseudocode

### 12.1 Outcome semantics and relation to the anchor

For attempt *i* with bracket `[s_i, r_i]` (the target evaluated the request at an unknown instant `t_i ∈ [s_i, r_i]`) and the unknown enforcement onset `T_deny` (DATA-MODEL §4):

| Outcome | Entailment (under the model assumption of monotone enforcement within the confirmation tail) | What it does **not** entail |
|---|---|---|
| `access_confirmed` | the target accepted at `t_i`; hence `T_deny ≥ s_i` | nothing about the time of acceptance within `[s_i, r_i]`; nothing about other credentials |
| `access_denied` | the target rejected at `t_i`; hence `T_deny ≤ r_i` | that the rejection is *because of* the event (natural expiry, outage — controls/expiry rules decide) |
| `indeterminate` | nothing (no usable inference) | neither acceptance nor denial; the attempt is *skipped* by bound selection |
| `transport_error` | nothing | idem |
| `not_sent` | nothing; no request existed | idem |

`relation_to_anchor(o, a)`: `pre` if `s_i < A_req`; `ambiguous` if `A_req ≤ s_i < A_ack` (the change may or may not be effective; such an `access_confirmed` contributes `max(0, s_i − A_ack) = 0` to `X_lo`); `post` if `s_i ≥ A_ack`. (`L`'s frozen definition uses `s_i ≥ A_req`.) `is_usable_for_bounds(o)` ⇔ `outcome ∈ {access_confirmed, access_denied}` ∧ `¬cache_served` ∧ `category ≠ control`.

### 12.2 The uncertainty decomposition (exact algebra)

Notation (all in local mono ns of one clock): `A_req ≤ A_ack`; `L` = last confirmed access with `s_L ≥ A_req` (or none); `D` = first stable denial after `L` (or after `A_req`).
Define the **bracket start** `s* = s_L` if `L` exists else `A_req`. Then
```
X_lo = max(0, s_L − A_ack)            (0 if no L)
X_hi = r_D − A_req
W    = r_D − s_L                      (localisation width; defined iff L exists)
```
and the four **additive components**
```
C_spacing  = s_D − s*                          (probe spacing at the bracket: gap between the last accepted and the first denied send)
C_latency  = r_D − s_D                         (response latency of the denial probe)
C_anchor   = min(s*, A_ack) − A_req            (request → acknowledgment uncertainty actually inside the measured interval)
C_clock    = min(C_anchor, δ_clock)            (the part of the anchor interval that is remote-clock offset uncertainty; δ_clock = 0 unless the anchor is `observed_aligned`)
```
with `C_anchor` reported as `C_anchor' = C_anchor − C_clock` and `C_clock` as separate components (their sum is `C_anchor`).

**Theorem (decomposition identity).** `X_hi − X_lo = C_spacing + C_latency + C_anchor' + C_clock`.
*Proof.* Case 1, `L` exists and `s_L ≥ A_ack`: `X_lo = s_L − A_ack`; `X_hi − X_lo = (r_D − A_req) − (s_L − A_ack) = (r_D − s_D) + (s_D − s_L) + (A_ack − A_req)`; here `min(s*, A_ack) = A_ack`. Case 2, `L` exists and `s_L < A_ack` (clamp): `X_lo = 0`; `X_hi − X_lo = r_D − A_req = (r_D − s_D) + (s_D − s_L) + (s_L − A_req)`; here `min(s*, A_ack) = s_L`. Case 3, no `L`: `s* = A_req`, `X_lo = 0`, `X_hi − X_lo = r_D − A_req = (r_D − s_D) + (s_D − A_req) + 0`, and `min(A_req, A_ack) − A_req = 0`. In every case the right-hand side is `C_latency + C_spacing + C_anchor`. ∎ (The identity of the task statement `(r_D − s_L) + (A_ack − A_req)` is Case 1; Cases 2–3 show that when the clamp is active the anchor term shrinks from `A_ack − A_req` to `s_L − A_req` — probes inside the acknowledgment window cannot pay for uncertainty that precedes them.)
Further: `C_spacing + C_latency = r_D − s*` (= `W` in Cases 1–2); `r_D − s_D` is the latency of the *denial* probe and `s_D − s_L` spans every intermediate indeterminate/transport/not-sent attempt; the latency of the *last accepted* probe (`r_L − s_L`) is **inside** `C_spacing` by construction (the bound uses `s_L`, the earliest possible acceptance instant).
**Remote-clock component.** Only when the anchor is `observed_aligned` (RG-P02-004 §12.1): `δ_clock = pairing_error + θ_slack + offset_uncertainty_lower_side` is the amount by which `A_req` was lowered below the nominal remote change instant; then `C_clock = min(C_anchor, δ_clock)` so both pieces are ≥ 0 even when the clamp truncates the anchor term. For `rg_bracketed`, `manual_bracketed`, `verification_bracketed` anchors `δ_clock = 0` (all instants are local; no clock offset enters — DATA-MODEL §4).
**Censored windows (`D` is None).** `X_hi = None`; the width is unbounded; the decomposition lists only `C_anchor'`, `C_clock` with an explicit marker `unbounded_above` and the identity is not applicable (`verify_decomposition` is skipped; the window states `censored=true`).
**Non-additive diagnostics.** `scheduling_lateness_l/d` (`lateness` of `L`, `D`), `read_cost_pairing` (`⌈cost/2⌉` of the four instants), `timestamp_resolution` (calibrated granularity, RG-P02-001) are reported but excluded from Σ: lateness is already *inside* the recorded `s` values (spacing is measured from actual send instants), pairing error and quantisation are ≤ the calibrated resolution (≤ 1 ms by gate) and are stated as the instrument resolution of every instant, never as hidden width.

**Worked examples (seconds; the code uses integer ns).**
**E1 — unclamped (Case 1).** `A_req = 100.000`, `A_ack = 100.180`; `L`: `s_L = 103.000, r_L = 103.040`; `D`: `s_D = 104.000, r_D = 104.060`. `X_lo = 103.000 − 100.180 = 2.820`; `X_hi = 104.060 − 100.000 = 4.060`; width `1.240`. Components: spacing `104.000 − 103.000 = 1.000`; latency `0.060`; anchor `A_ack − A_req = 0.180`; clock `0`. Sum `1.240` ✓; also `W = r_D − s_L = 1.060 = 1.000 + 0.060` ✓.
**E2 — clamp active (Case 2).** same probes, `A_ack = 103.500`: `X_lo = max(0, 103.000 − 103.500) = 0`; `X_hi = 4.060`; width `4.060`. Components: spacing `1.000`; latency `0.060`; anchor `min(103.000, 103.500) − 100.000 = 3.000` (not `3.500`); sum `4.060` ✓. (The 0.500 s by which the acknowledgment exceeds `s_L` is *not* part of the width: the probe at 103.000 may have preceded the effective change.)
**E3 — no `L` (Case 3).** `A_req = 100.000`, `A_ack = 100.180`; first post-event attempt is a denial: `s_D = 101.000, r_D = 101.050`; `X_lo = 0`, `X_hi = 1.050`; components: spacing `101.000 − 100.000 = 1.000` (anchor to first send), latency `0.050`, anchor `min(100.000, 100.180) − 100.000 = 0`; sum `1.050` ✓.
**E4 — manual anchor with ambiguity window.** `M1 = A_req = 1000.0`, `M2 = A_ack = 1042.5`; an access at `s = 1020.0` is `ambiguous` and *not* `L` only if a later access exists; suppose `L: s_L = 1060.0`, `D: s_D = 1065.0, r_D = 1065.2`: `X_lo = 17.5`, `X_hi = 65.2`, width `47.7 = 5.0 (spacing) + 0.2 (latency) + 42.5 (anchor)` ✓.
**E5 — external aligned anchor (RG-P02-004 worked example 3).** `A_req = 199.700`, `A_ack = 207.400`, `δ_clock = 0.3`; `L: s_L = 215.0`, `D: s_D = 216.0, r_D = 216.05`: `X_lo = 215.0 − 207.4 = 7.6`; `X_hi = 216.05 − 199.7 = 16.35`; width `8.75 = 1.0 + 0.05 + (7.7 − 0.3) + 0.3` ✓ (anchor' `7.4` = delivery latency, clock `0.3`).
**E6 — censored.** `D` None: `X_hi = None`; `X_lo = s_L − A_ack`; components `anchor'` and `clock` only; marker `unbounded_above`.

### 12.3 Confirmation-tail contract for observations

RG-P08-004 selects `D` per DATA-MODEL §4 (`N_confirm` consecutive denials, or denials spanning `T_confirm`). The observation-level semantics it must apply: (a) attempts are ordered by `(s_i, attempt_no)` per credential; (b) only **usable** attempts (`is_usable_for_bounds`) participate; (c) `indeterminate`, `transport_error` and `not_sent` attempts neither extend nor reset a run of denials — they are counted in a `skipped` tally recorded with the window (and feed CF-07); (d) a `cache_served` attempt is skipped like any indeterminate; (e) the time span of a run is measured from the first denial's `s` to the last denial's `r`; (f) a usable `access_confirmed` after a denial resets the run and marks `flapping` (DATA-MODEL §4); (g) if the horizon ends before the tail completes, `D` is *provisional* (CF-14). *(Decision DEC-4; RG-P08-004 must conform or file a change request.)*

### 12.4 Confidence-factor catalogue (CF-01 … CF-21)

Level = `min` of the caps of all evaluated factors (start `high`). `effect` is what the factor does when its **trigger** holds; thresholds are configuration (§18). A factor is *always* recorded (value + effect `none` when the trigger does not hold) so reports show what was checked.

| ID | Name | Input (measurable) | Trigger → effect | Rule ref / source |
|---|---|---|---|---|
| CF-01 | `controls_valid` | all required positive/negative/sibling/foreign controls passed (§12.5) | false → `cap_none` | TV-01/02, SV-001, DATA-MODEL §9.5 |
| CF-02 | `baseline_established` | ≥ 1 baseline `access_confirmed` per probe-subject credential | false → `cap_none` | FR-EXP-003 |
| CF-03 | `usable_samples_post_event` | number of usable post-anchor attempts for the credential | `< min_usable_samples` (3) → `cap_medium` | TV-07, SV-004 |
| CF-04 | `tail_state` | `confirmed` / `provisional` / `absent` (censored) | `provisional` → `cap_medium`; `absent` → `none` (X_lo still sound) | FR-TEMP-011 |
| CF-05 | `localization_width_ns` | `W` (or `r_D − A_req` without `L`) | informational (`none`); reported with precision label by RG-P08-011 | FR-TEMP-010 |
| CF-06 | `scheduling_lateness` | max `scheduling_lateness_ns` over `L`, `D` and the first two post-anchor attempts | `> lateness_cap_ns` (2 s) → `cap_medium`; `> lateness_warn_ns` (100 ms) → `none` + note | NFR-PERF-001 |
| CF-07 | `indeterminate_ratio` and rate-limit overlap | indeterminate+transport+not_sent attempts / all post-anchor attempts (per-mille); any `rate_limited`/`http_5xx` pause overlapping `[s_L, r_D]` | ratio `> 500‰` → `cap_medium`; overlap → `cap_low` | TV-13, SV-043 |
| CF-08 | `clock_anomaly_overlap` | `ClockAnomaly` spans (RG-P02-001 §8.7) overlapping `[A_req, r_D]` | `wall_step`/`suspend_gap`/`process_restart` → `cap_low`; `mono_regression` or virtual/system mix → `cap_none` | FR-TEMP-003, TM-28 |
| CF-09 | `anchor_quality` | `AnchorInterval.quality` | `observed_aligned`, `observed_receipt_only` → `cap_medium`; `none` → `cap_none`; others `none` | RG-P02-004 |
| CF-10 | `offset_uncertainty` | max of `ClockOffset.uncertainty_ns` used, or `ExpiryBound.sources_conflict` | `≥ offset_uncertainty_cap_ns` (1 s) or conflict → `cap_medium` | SV-047 |
| CF-11 | `repetition` | number of agreeing independent repetitions / disagreeing ones | disagreement among repetitions → `cap_low`; agreement count recorded (≥ 2 supports `vulnerable`, RG-P02-009) | TV-21 |
| CF-12 | `oracle_agreement` | independent oracle verdict vs probe verdict: `agree`, `disagree`, `none`, `unsupported` | `disagree` → `cap_low`; others `none` | TV-23 |
| CF-13 | `flapping` | non-monotonic enforcement observed | true → `cap_low` | TV-07, R-004 |
| CF-14 | `provisional_denial` | `D` provisional (horizon ended before the tail) | true → `cap_medium` | FR-TEMP-011 |
| CF-15 | `cache_served_excluded` | count and ratio of `cache_served` attempts among post-anchor attempts | ratio `> 500‰` → `cap_medium`; else `none` + count | TV-14, SV-048 |
| CF-16 | `denial_family_consistency` | `denial_family_matches(event.kind, D.denial_family)` (§12.6) | informational; false adds a report note | SV-009 |
| CF-17 | `time_basis` | `real` / `virtual` | informational (`virtual` labels the result lab-only; never mixed, DATA-MODEL §9.8) | ADR-0014 |
| CF-18 | `state_change_verified` | `Tri` from RG-P02-004 `change_verified` | `false` → `cap_low`; `unknown` → `cap_medium` | TV-04, SV-005 |
| CF-19 | `settle_respected` | `settle_check.ok` at the anchor (RG-P02-003) | false → `cap_low` | TV-15 |
| CF-20 | `sibling_stable` | sibling/foreign controls accepted/denied as expected through observation | false → `cap_none` | TV-09, TV-02 |
| CF-21 | `negative_distinct` | responses to negative controls differ from positive baseline | false → `cap_none` (identical answers) | TM-13, TV-02 |

`apply_caps`: `none` if any `cap_none`; else `low` if any `cap_low`; else `medium` if any `cap_medium`; else `high`. RG-P08-005 may add *numeric refinements within a level* (e.g. a score) but may not output a level above `apply_caps` of the recorded factors; it may add new factors only via a catalogue revision (new CF ids).
**Worked example.** Window of §12.2 E1 with controls valid, 12 usable post-anchor attempts, max lateness 120 ms, 2 of 14 attempts `rate_limited` outside `[s_L, r_D]`, RG-automated anchor, no anomalies, one run, no oracle: CF-01 true, CF-02 true, CF-03 12 → none, CF-04 `confirmed` → none, CF-06 120 ms → `none` + note (above warn, below cap), CF-07 ratio `143‰` → none, CF-08 none, CF-09 `rg_bracketed` → none, CF-11 repetition 1 → none, CF-12 `none` → none, CF-13 false, CF-18 `true` ⇒ level **high**. If a `wall_step` span of 0.3 s overlaps `[A_req, r_D]` (CF-08 → `cap_low`) the level is **low**; adding CF-18 `unknown` (`cap_medium`) does not raise it (INV-11).

### 12.5 Control semantics (what a control observation must show)

| Control role | Phase | Credential | Passes iff (usable observations) |
|---|---|---|---|
| positive control / baseline | `baseline` | probe subject | ≥ `baseline_min_samples` (default 2) `access_confirmed`, none `access_denied` |
| negative: none | `control` | `None` | all `access_denied` (denial family `credential_rejected`) and none `access_confirmed` |
| negative: garbage | `control` | `None` (synthetic garbage of the same shape) | same as none |
| sibling control | `observe` (and baseline) | unaffected sibling (RG-P02-003 §12.4) | every usable attempt `access_confirmed` from baseline through the end of observation |
| foreign identity | `control` | another identity's credential not authorised for the operation | all `access_denied` with family `insufficient_privilege` or `credential_rejected` |

A control with an `indeterminate` majority is *inconclusive* (does not pass). Negative controls must also be **distinct** from the positive baseline (CF-21): if the response signature (status + body hash class) of the negative control equals the baseline's, the control fails even if outcomes look "denied" (TM-13, TV-02).

### 12.6 Expected denial families per event kind (informational)

`denial_family_matches(kind, family)`: `role_removed`, `group_removed`, `entitlement_removed` → `insufficient_privilege` expected, `credential_rejected` tolerated with a note; `account_disabled`, `account_deleted`, `session_terminated`, `sessions_terminated_all`, `logout_*`, `refresh_token_revoked`, `access_token_revoked`, `password_*`, `credential_reset`, `not_before_pushed`, `grant_revoked`, `service_*` → `credential_rejected` or `session_ended` expected; `handshake_rejected` matches any (WebSocket). A mismatch never changes an outcome; it adds the note "denial family differs from the event's usual signature (SV-009)".

## 13. Internal functions, methods, or service operations

```python
def _denial_family(sig: DenialSignal) -> DenialFamily: ...
def _additive_sum(components: Sequence[UncertaintyComponent]) -> int: ...
def _bracket_start(a: AnchorInterval, l: ObservationView | None) -> int: ...          # s*
def _clock_component(a: AnchorInterval, c_anchor: int, delta_clock_ns: int) -> tuple[int, int]: ...   # (anchor', clock)
def _check_outcome_coupling(o: Observation) -> None: ...                              # VR-4
def _response_signature_equal(a: ObservationView, b: ObservationView) -> bool: ...      # CF-21 input is supplied by RG-P05-010 as a boolean on the control summary
```

## 14. Error handling and failure recovery

| Failure | Detection | Handling | Recovery | Code |
|---|---|---|---|---|
| Observation with send after receive | validator | reject; runner treats as `INTERNAL` | fix runner stamping | RGE-TIMING-0602 |
| Negative/unsorted lateness | validator | reject | fix scheduler wiring | RGE-TIMING-0603 |
| Outcome inconsistent with assertions (e.g. `access_confirmed` with a failed required assertion) | validator | reject; the assertion engine result must be corrected | fix RG-P05-006 | RGE-CONFIG-0604 |
| Decomposition mismatch | `verify_decomposition` before publish | abort analysis step with `INTERNAL` (never publish) | fix RG-P08-004 | RGE-INTERNAL-0606 |
| Unknown/duplicate confidence factor | `Confidence` validator | reject | fix scorer | RGE-CONFIG-0605 |
| Observation too large (lists beyond bounds) | validator | reject | fix producer | RGE-CONFIG-0601 |

Crash safety: an observation is written once (append-only); a crash mid-attempt yields no record for the in-flight attempt, which recovery records as interrupted/`not_sent` per RG-P02-007 (NFR-PERF-010).

## 15. Security requirements and trust boundaries

- **Untrusted data.** `denial_signal`, hints, status and `server_date` derive from target responses (TM-13 deception, TM-10 floods, TM-11/TM-12 markup): only enumerations and bounded identifiers are stored in the observation; raw content stays in redacted evidence; renderers escape.
- **TV-05 / TM-13 enforcement at the model level:** `access_confirmed` is unconstructible without every required positive assertion; `access_denied` requires a recognised signal; identical-response negative controls fail CF-21.
- **TV-22:** mechanism hints cannot influence bounds or classes — `ObservationView` excludes them.
- **No secrets:** no credential material, tokens or cookies appear; `credential_ref` is an id; `assertion_results` carry ids/booleans only.
- **TM-28:** all times are local `TimeInstant`s; `server_date` is a `RemoteInstant` that only RG-P08-002 may use.
- **Integrity:** observations are append-only and referenced by the timeline hash chain (RG-P02-008, RG-P08-001).

## 16. Concurrency, asynchronous behavior, and resource ownership

Immutable values, pure functions ⇒ thread/task safe. Observations are produced concurrently by probe workers but persisted through the single store writer (bounded, never lossy; RG-P03-008). Memory: one `ObservationView` ≈ 200 B; a 10 000-observation experiment holds views for analysis only (≈ 2 MB). No locks or cancellation points.

## 17. Performance and resource requirements

Proposals validated by `BM-OBS-1`: `Observation` metadata (compact JSON, excluding bodies) ≤ 2 KiB average (NFR-PERF-007; the §8.1 example measures below this budget — asserted by TST-RG-P02-006-13); `observation_view` ≤ 5 µs; `apply_caps` over 21 factors ≤ 10 µs; `decompose_width` ≤ 20 µs; model validation ≤ 100 µs per observation (stamps are on the hot path only via `Clock.now()`, not validation).

## 18. Configuration and defaults

| Field | Type | Default | Range | Env var | Notes |
|---|---|---|---|---|---|
| `observation.lateness_warn_ns` | int | 100 000 000 | 0 … 60 000 000 000 | `RG_OBSERVATION_LATENESS_WARN_NS` | CF-06 note threshold (≈ NFR-PERF-001 p99) |
| `observation.lateness_cap_ns` | int | 2 000 000 000 | ≥ warn | `RG_OBSERVATION_LATENESS_CAP_NS` | CF-06 cap threshold |
| `observation.min_usable_samples` | int | 3 | 1 … 100 | `RG_OBSERVATION_MIN_USABLE_SAMPLES` | CF-03 (matches `N_confirm` default) |
| `observation.indeterminate_ratio_cap_permille` | int | 500 | 0 … 1000 | `RG_OBSERVATION_INDETERMINATE_RATIO_CAP_PERMILLE` | CF-07 |
| `observation.cache_served_ratio_cap_permille` | int | 500 | 0 … 1000 | `RG_OBSERVATION_CACHE_SERVED_RATIO_CAP_PERMILLE` | CF-15 |
| `observation.offset_uncertainty_cap_ns` | int | 1 000 000 000 | 0 … 3 600 000 000 000 | `RG_OBSERVATION_OFFSET_UNCERTAINTY_CAP_NS` | CF-10 |
| `observation.baseline_min_samples` | int | 2 | 1 … 20 | `RG_OBSERVATION_BASELINE_MIN_SAMPLES` | §12.5 |

Precedence: defaults < file < env < CLI; invalid ⇒ `RGE-CONFIG-0601` at load. The thresholds in force are recorded in the run manifest (FR-EVD-007).

## 19. Logging, observability, and evidence requirements

Events: `observation.recorded` {`obs_id`, `credential_ref`, `outcome`, `phase`, `lateness_ns`, `latency_ns` (= `r − s`)}; `confidence.computed` {`window_ref`, `level`, `caps_applied`}; `analysis.decomposition_verified` {`window_ref`, `width_ns`}. Metrics: `scheduling_lateness_ns` histogram (all observations, NFR-PERF-001), `probe_latency_ns`, `indeterminate_total{reason}`. Evidence: observations are the primary facts; `UncertaintyComponent` lists and `Confidence` are derived records (`derivation=calculated`, algorithms `rg.uncertainty.decompose@1`, `rg.confidence.rules@1.0.0`). Redaction: observation metadata is secret-free by construction; exchange evidence is redacted at the persistence boundary (RG-P03-004).

## 20. Platform compatibility

Pure Python, integer arithmetic only (ratios as per-mille integers; no floats in any persisted or compared quantity). Compact JSON size depends only on field content (UTF-8). No platform behaviour.

## 21. Edge cases and invalid inputs

| # | Case | Expected behaviour |
|---|---|---|
| E-1 | `access_confirmed` with a required positive assertion `passed=false` | `RGE-CONFIG-0604` |
| E-2 | `access_confirmed` with zero positive assertions (HTTP 200 only) | `RGE-CONFIG-0604` (TV-05) |
| E-3 | `access_denied` with a passed positive assertion | `RGE-CONFIG-0604` |
| E-4 | `access_denied` without `denial_signal` | `RGE-CONFIG-0604` |
| E-5 | `not_sent` with `t_send_start ≠ t_recv_end` or an `exchange_ref` | `RGE-CONFIG-0604` |
| E-6 | `cache_served=true` with outcome `access_confirmed` | `RGE-CONFIG-0604` |
| E-7 | `scheduling_lateness_ns` = −1 | `RGE-TIMING-0603` |
| E-8 | `intended_at` later than `t_send_start` | `RGE-TIMING-0602` |
| E-9 | decomposition with `L` after `D` (`s_D ≤ s_L`) | `decompose_width` raises `RGE-INTERNAL-0606` (inputs violate the definitions) |
| E-10 | `A_ack = A_req` (zero-width anchor) | `C_anchor = 0`; identity holds |
| E-11 | `s_L = A_req` exactly | `L` valid (`s_i ≥ A_req`); `ambiguous` relation; `X_lo = 0` |
| E-12 | 25 assertion results | `RGE-CONFIG-0601` |
| E-13 | confidence factors CF-07 twice | `RGE-CONFIG-0605` |
| E-14 | negative control accepted (outcome `access_confirmed` for garbage credential) | observation valid; control fails (§12.5); CF-01 false |
| E-15 | negative-control outcome `access_denied` but response signature equal to baseline | control fails via CF-21 |
| E-16 | retry of a 429 attempt | new attempt with `retry_of`; the 429 stays `indeterminate/rate_limited` |

## 22. Unit and integration test requirements

| ID | Condition | Expected observation |
|---|---|---|
| TST-RG-P02-006-01 | Outcome-coupling table fuzz: all combinations of outcome × assertion pass/fail × denial_signal × reason × error × cache_served | valid iff §9 table; invalid ⇒ `RGE-CONFIG-0604` |
| TST-RG-P02-006-02 | Time validators E-5, E-7, E-8, cross-epoch observation | `RGE-TIMING-0602/0603` |
| TST-RG-P02-006-03 | `observation_view` completeness: reliance matrix; mutate every non-reliance field and compare views | views equal (INV-7); only listed fields appear |
| TST-RG-P02-006-04 | Decomposition worked examples E1–E6 (integer ns) | Σ additive = `X_hi − X_lo`; component values as stated; E6 marker `unbounded_above` |
| TST-RG-P02-006-05 | Property (Hypothesis): random `A_req ≤ A_ack`, random `L` (or none, with `s_L ≥ A_req`), `D` with `s_D > s_L`, `r_D ≥ s_D`; with/without `δ_clock` | INV-8/INV-9 hold exactly; clamp cases covered by generator (`s_L` below/above `A_ack`) |
| TST-RG-P02-006-06 | `verify_decomposition` negative: perturb one component by 1 ns; drop a component; include a non-additive one in Σ | `RGE-INTERNAL-0606` |
| TST-RG-P02-006-07 | `relation_to_anchor` boundaries: `s = A_req − 1, A_req, A_ack − 1, A_ack` | `pre`, `ambiguous`, `ambiguous`, `post` |
| TST-RG-P02-006-08 | Catalogue completeness: CF-01…CF-21 present; each factor's allowed effects; `apply_caps` truth table incl. monotonicity (INV-11) | as stated; adding factors never raises level |
| TST-RG-P02-006-09 | Confidence worked example (high; then `wall_step` overlap ⇒ low; adding CF-18 `unknown` keeps low) | levels as stated |
| TST-RG-P02-006-10 | Threshold boundaries for CF-03/06/07/10/15 (`threshold ±1`) | effect flips exactly at the documented side |
| TST-RG-P02-006-11 | Control semantics table: baseline/negative/sibling/foreign with passing and failing observation sets, indeterminate majority, identical-signature negative | pass/fail per §12.5; CF-01/CF-20/CF-21 values |
| TST-RG-P02-006-12 | Tail-counting contract fixture: sequences with interleaved 429/5xx/cache-served/not_sent between denials and an access after a denial | skipped tally and flapping flag as §12.3 (consumed by RG-P08-004 conformance suite) |
| TST-RG-P02-006-13 | Size budget: serialise the §8.1 example and a generated corpus (1 000 observations) with canonical JSON | example ≤ 2 048 bytes; corpus mean ≤ 2 048 bytes |
| TST-RG-P02-006-14 | Denial-family mapping and `denial_family_matches` table | per §8.3/§12.6; mismatch only adds a note |
| TST-RG-P02-006-15 | Integration (lab virtual time): lab service with known `T_deny` (RG-P09-003 profile "introspection per call") probed on a 1 s schedule | recorded observations satisfy INV-1/2; `T_deny ∈ [s_L, r_D]` from the entailments; decomposition identity holds on the computed window |
| TST-RG-P02-006-16 | Lateness: scheduler-injected 120 ms and 2.5 s lateness (RG-P03-006 virtual hooks) | `scheduling_lateness_ns` equals injected value exactly; CF-06 note / `cap_medium` |

## 23. Mocking and test fixtures

Doubles: `ScriptedTransport` + `ScriptedAssertionEngine` (rg_lab) producing observations with chosen outcomes; `VirtualClock`/`VirtualScheduler` for lateness injection. Fixtures: `fixtures/observation/obs_denied_401.json` (§8.1), `outcome_matrix.json`, `decomposition_cases.json` (E1–E6), `confidence_threshold_cases.json`, `tail_sequences.json`, `controls_cases.json`. Hypothesis strategies: `rg_core.testing.strategies.observation`, `.anchor_window`.

## 24. Objective acceptance criteria

- **AC-RG-P02-006-01** An `Observation` cannot be constructed with an outcome inconsistent with its assertions, signals, reasons, errors or cache flag, and cannot carry timestamps in the wrong order, from different clocks, or with negative/incorrect lateness (verified by TST-RG-P02-006-01, TST-RG-P02-006-02).
- **AC-RG-P02-006-02** Analysis reads observations only through `ObservationView`, which exposes no body, header, free text, hint or wall-time field (verified by TST-RG-P02-006-03).
- **AC-RG-P02-006-03** For every anchor, `L` (or none) and `D`, including the `max(0,·)` clamp and the no-`L` case, the additive components sum exactly to `X_hi − X_lo` in integer nanoseconds, and non-additive diagnostics never enter the sum (verified by TST-RG-P02-006-04, TST-RG-P02-006-05, TST-RG-P02-006-06).
- **AC-RG-P02-006-04** `relation_to_anchor` and the usability predicate classify attempts exactly at the `A_req`/`A_ack` boundaries (verified by TST-RG-P02-006-07).
- **AC-RG-P02-006-05** The confidence catalogue defines CF-01…CF-21 with triggers and caps; `apply_caps` is the minimum of caps and is monotone under added factors; thresholds flip exactly at their boundaries (verified by TST-RG-P02-006-08, TST-RG-P02-006-09, TST-RG-P02-006-10).
- **AC-RG-P02-006-06** Control semantics and the confirmation-tail contract are executable fixtures that RG-P05-007 and RG-P08-004 reproduce (verified by TST-RG-P02-006-11, TST-RG-P02-006-12).
- **AC-RG-P02-006-07** Observation metadata averages ≤ 2 048 bytes in canonical JSON (verified by TST-RG-P02-006-13).
- **AC-RG-P02-006-08** In the virtual-time lab the recorded observations bracket the known enforcement onset, the injected lateness is recorded exactly, and the decomposition identity holds on the resulting window (verified by TST-RG-P02-006-15, TST-RG-P02-006-16, TST-RG-P02-006-14).

## 25. Research sources and engineering rationale

Sources: DATA-MODEL §3 (ProbeOutcome semantics), §4 (all symbols), §9.1–9.2, §9.5; PRD FR-TEMP-009/010/011, FR-ANA-003/004, NFR-PERF-001/007; charter SC-02 ("no hidden slack"), glossary (*control*, *observation categories*); THREAT-MODEL TV-05/07/13/14/17/21/22/23, TM-13; STANDARDS-REFERENCE SV-004 (poll until stable rejection), SV-009 (rejection signals), SV-043 (429), SV-047 (no verdict from < 2 s / single sample), SV-048 (cache-served samples), SV-049 (refresh failure signature), SV-055 (WebSocket); TECHNICAL-FEASIBILITY R-003, R-004, R-016; SCHEMATHESIS-INTEGRATION U7 (`Response` has no timestamps, RG stamps adjacent to the wire call).

- **DEC-1 Decompose into four additive components plus non-additive diagnostics.** Chosen because the frozen bounds are differences of four recorded instants and the identity is then exact over integers; hidden slack (SC-02) is impossible by construction. Rejected: reporting a single "uncertainty" number (cannot be audited); including scheduling lateness in the sum (double counts: lateness already shifts `s_i`); including clock quantisation in the sum (below calibrated resolution; reported as instrument resolution). Verification: TST-04/05/06.
- **DEC-2 The anchor term is `min(s*, A_ack) − A_req`** (clamp-aware). Rejected: always `A_ack − A_req` (over-states uncertainty when the clamp is active and breaks the identity; the task statement's identity is Case 1). Verification: TST-04 (E2), TST-05.
- **DEC-3 Projection `ObservationView` as the only analysis input** — enables re-analysis from stored evidence with any algorithm version (ADR-0013) and prevents free-text/body dependence (TV-05, TV-22). Rejected: letting analysis read assertion detail. Verification: TST-03.
- **DEC-4 Indeterminate attempts neither extend nor reset a denial run** (they are *skipped*). Rationale: a 429/5xx says nothing about enforcement (TV-13); resetting would let rate limiting block the tail forever, extending would let an outage count as denial. Skipped attempts feed CF-07 so heavy pollution still lowers confidence. Rejected: treating indeterminate as a break (non-terminating under throttling) or as denial (TV-13). This is a binding contract for RG-P08-004. Verification: TST-12.
- **DEC-5 Confidence as `min` of caps over a finite catalogue.** Deterministic, auditable per factor (FR-ANA-004), monotone under added evidence of problems. Rejected: weighted-sum scores (opaque, non-monotone, threshold gaming). Verification: TST-08/09/10.
- **DEC-6 Per-mille integers for ratios** — no floats in persisted/compared values (NFR-REL-002 determinism across platforms). Verification: TST-10.
- **DEC-7 Controls pass criteria include response *distinctness*** (CF-21) — a WAF/target that answers identically to every token must yield `inconclusive` (TM-13). Verification: TST-11.
- **DEC-8 `scheduling_lateness_ns` defined end-to-end (`t_send_start − intended_at`)** with timer-only lateness additive: the end-to-end number is what affects the schedule's achieved spacing; the timer-only number diagnoses the scheduler (RG-P03-006). Verification: TST-16.

## 26. Remaining uncertainties or assumptions

| # | Assumption | Evidence tag | Falsifying test |
|---|---|---|---|
| A-1 | The target evaluates the credential at an instant inside the send/receive bracket `[s_i, r_i]` (DATA-MODEL §4) | hypothesis-level frozen assumption | lab ground-truth test TST-RG-P02-006-15 (mock service logs its evaluation instant); a service that evaluates before `s_i` (pre-validated connection) would be a counter-example |
| A-2 | Enforcement is monotone (accept then reject) around `T_deny` except for flapping, which the tail detects | hypothesis | flapping lab profile (RG-P09-003); real replicated services may violate it (R-004) |
| A-3 | Default thresholds (3 samples, 100 ms/2 s lateness, 500‰ ratios, 1 s offset) are sensible | proposal | threshold-sweep benchmarks and field results (RG-P12); all configurable and recorded |
| A-4 | A response is *cache-served* when a positive `Age` header is present (SV-048); caches that strip `Age` evade detection | S (RFC 9111 snippets) | lab fault "caching proxy without Age" (RG-P09-004) — would show as a false confirmed access; mitigation `Cache-Control: no-cache` where scope permits |
| A-5 | RG-P08-004 can implement §12.3 and produce `UncertaintyComponent`s per §12.2 | design | RG-P08-004 conformance tests reuse TST-04/05/12 fixtures |
| A-6 | Compact observation JSON stays ≤ 2 KiB with two assertions and one hint | measured on the example | TST-RG-P02-006-13 |
| A-7 | `δ_clock` for `observed_aligned` anchors is exactly `pairing_error + θ_slack + lower-side offset uncertainty` | design | TST-RG-P02-006-04 E5 + RG-P08-002 tests |

## 27. Maintainability, portability, and future extension requirements

- **Versioning:** `observation` `1.0`; additive optional fields minor; new `DenialSignal`/`IndeterminateReason`/`MechanismHintKind` members are minor but unknown members in a higher-minor document are rejected by the registry. The confidence catalogue is versioned by `algorithm_id` (`rg.confidence.rules@1.0.0`): adding a factor or changing a trigger/cap bumps it, and historical findings keep the version they were computed with (ADR-0013).
- **Extension points:** new factor ids (catalogue revision), new probe kinds (observation fields are kind-agnostic), new uncertainty kinds (additive components must keep INV-8 provable — a new additive component requires a proof update).
- **Reuse:** the decomposition algebra and `apply_caps` are independent of RevocationGap's transports and reusable in any interval-measurement tool (master-prompt "confidence/evidence analysis library").
- **Deprecation:** none yet; deprecated factors are retained with effect `none` for one minor release.
