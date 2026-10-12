---
id: RG-P02-009
title: "Outcome classification rules"
phase: "02"
package: core
module_ids: [MOD-CORE-OUTCOME_CLASSIFICATION]
status: DRAFT
depends_on: [RG-P02-005, RG-P02-006, RG-P02-007]
requirements: [FR-ANA-005, FR-ANA-006, FR-ANA-007, FR-ANA-012, FR-TEMP-010, FR-TEMP-011, FR-EXP-003, FR-EVD-002, FR-EVD-003, NFR-REL-002, NFR-TEST-001, NFR-TEST-002]
interfaces_defined: [IF-ANA-CLASSIFY]
interfaces_used: [IF-ANA-EXPECT, IF-CORE-OBSERVATION, IF-CORE-EVENTORDER, IF-CORE-CREDGRAPH, IF-EXP-MACHINE, IF-CORE-SERIAL]
schemas_defined: [SCH-CLASSIFY]
schemathesis_touchpoints: []
---

# RG-P02-009 — Outcome classification rules

> Scope: the **deterministic, table-driven rules** that turn one exposure result (window summary, resolved expectation, confidence, controls, validation evidence) into exactly one `OutcomeClass` **per requested `PolicyProfile`**, with recorded rationale. Computing the exposure window is RG-P08-004; scoring confidence RG-P08-005; assembling `Finding` objects, fingerprints, deduplication and mechanism attribution RG-P08-006/-007; vendor baselines RG-P08-008. This element owns `IF-ANA-CLASSIFY` (the rules) and `SCH-CLASSIFY`.

## 1. Module identifier and name

| Item | Value |
|---|---|
| Element | RG-P02-009 — Outcome classification rules |
| Package / modules | `rg_core.analysis.classify` (`rules`, `facts`, `engine`, `validation`, `matrix`), `rg_core.model.classify` |
| Module id | `MOD-CORE-OUTCOME_CLASSIFICATION` |
| Schemas | `SCH-CLASSIFY`: `ClassificationRule`, `Condition`, `RationaleStep`, `FpCheck`, `Classification`, `ClassificationMatrix`, `ClassifyContext`, `IndependentValidation` |
| Interface | `IF-ANA-CLASSIFY` — `OutcomeClassifier` (`classify`, `classify_matrix`) |
| Algorithm id | `rg.classify.rules@1.0.0` (recorded with every result; `rules_digest` of the rule table) |

## 2. Phase and requirement references

| Requirement | Realised by |
|---|---|
| FR-ANA-005 exactly one outcome class per profile by published deterministic rules over (window, expectation set, confidence, controls); `vulnerable` needs MUST-level expectation, valid controls, second-oracle or repetition confirmation, confidence ≥ medium | §11.1 rule table, R-21/R-22, §12.2 |
| FR-ANA-006 profiles; each classification records its profile; re-analysis under another profile creates a new record | `Classification.profile`, `classify_matrix`, §10 |
| FR-ANA-007 false-positive rules before emitting `vulnerable`: natural expiry vs revocation, cached-response exclusion, rate-limit windows, probe malformation, client-auth failure, unsupported capability | §11.3 FP-01…FP-12 mapped to rules |
| FR-ANA-012 explanation cites standard/vendor source | `expectation.source` string and `RationaleStep.cites` (mechanism attribution is RG-P08-006) |
| FR-TEMP-010/011 bounds and tail semantics consumed | `WindowSummary` (§8.2) |
| FR-EXP-003 controls gate | R-03 |
| FR-EVD-002 recomputation, FR-EVD-003 derivation labelling, NFR-REL-002 determinism | pure function; `derivation=calculated`; §11.2 INV-1 |
| NFR-TEST-001 branch coverage and mutation score on the classification module; NFR-TEST-002 | §22 boundary/mutation suite, golden dataset |

Validity rules and risks realised: **TV-01, TV-02** (controls), **TV-04** (revoke not proof), **TV-09** (natural expiry), **TV-10** (capabilities), **TV-11** (profile and bands recorded), **TV-13** (429/5xx), **TV-14** (cache), **TV-17** (malformed/client-auth), **TV-22** (no `vulnerable` from unknown/inferred mechanism), **TV-23** (independent validation), TM-13, R-001, R-014; ADR-0010; STANDARDS-REFERENCE §3 (taxonomy), SV-001, SV-006, SV-010 … SV-016, SV-018 … SV-021, SV-024, SV-025, SV-030, SV-032, SV-033, SV-034, SV-043, SV-046, SV-047, SV-048, SV-055. Scenarios: SCN-01…SCN-15 (every scenario's expected/vulnerable behaviour maps to rows of §11.1).

## 3. Purpose and user/security value

The classification decides whether a person is told "this is a vulnerability". ADR-0010 and R-001 make the failure mode explicit: the same behaviour (a JWT accepted until `exp` after logout) is conformant under RFC 9068 and a defect under ASVS V7.4.1 for application sessions. This module makes that distinction *mechanical*: an ordered rule table over named facts, evaluated per profile, where every `vulnerable` requires (a) a MUST-level, strongly-evidenced, mode-independent-or-declared expectation, (b) a verdict that the measured lower bound `X_lo` exceeds the ambiguous band, (c) valid controls, (d) an independent confirmation, (e) a verified state change and (f) confidence ≥ medium. Every other path ends in a class that says what is actually known: `enforced`, `expected`, `documented_delay`, `risky_config`, `needs_verification` or `inconclusive`. Every decision is recorded as numbered rationale steps so a reviewer can replay it by hand.

## 4. Explicit responsibilities

- **RESP-1** Define the classifier inputs (`WindowSummary`, resolved expectation, `Confidence`, `ControlSummary`, `ValidationEvidence`, clock/probe flags) and outputs (`Classification`, `ClassificationMatrix`).
- **RESP-2** Define the **ordered rule list R-01…R-27 with precedence**, stage semantics and exact predicates, as data (`ClassificationRule`).
- **RESP-3** Define precisely: `enforced`, `expected`, `documented_delay`, `risky_config`, `vulnerable`, `needs_verification`, `inconclusive`.
- **RESP-4** Define the independent-validation requirement for `vulnerable` (TV-23) and the downgrade reasons when unmet.
- **RESP-5** Define the profile-matrix computation (shared gates, independent per-profile classification).
- **RESP-6** Define rationale-step recording, false-positive checks (FP-01…FP-12) and the tolerance/band record (TV-11).
- **RESP-7** Provide golden worked classification examples (GF-01…GF-15) with exact numeric inputs and outputs, used as the golden dataset.
- **RESP-8** Specify the property/boundary/mutation tests and invariants that protect the rule table.

## 5. Out-of-scope responsibilities

| Excluded item | Owner |
|---|---|
| `ExposureWindow` computation, `L`/`D` selection, flapping/censoring detection | RG-P08-004 |
| Confidence scoring pipeline (catalogue/caps are RG-P02-006) | RG-P08-005 |
| Expectation resolution and verdict algebra (called, not re-implemented) | RG-P02-005 |
| `Finding` assembly, fingerprints, duplicate detection, mechanism attribution (TV-22), reproducibility scoring | RG-P08-006, RG-P08-007 |
| Running repetitions / second oracles (evidence production) | RG-P08-007 (reproducibility), RG-P04-004/RG-P05-007 (oracles/controls) |
| Risk/impact scoring | RG-P08-010 |
| Report wording | RG-P08-011 |
| Terminal-state mapping | RG-P02-007 (`disposition`) |
| Vendor baselines content | RG-P08-008 |

## 6. Dependencies and prerequisites

RG-P02-005 (`ExpectationSet.resolve`, `evaluate`, `ResolvedExpectation`, `VerdictResult`, bands), RG-P02-006 (`ObservationView`, `Confidence`, control semantics, factor catalogue), RG-P02-007 (`disposition`, `FindingSummary`), transitively RG-P02-001…004 (`ExpiryBound`, `AnchorInterval`, `Tri`, `OutcomeClass`/`PolicyProfile` enums from DATA-MODEL §3). RG-P03-002 (`Model`, `Document`, `Provenance`, `Label`, `ShortText`, `Sha256Digest`, `digest`). Pure Python + pydantic v2; no I/O, no clock, no randomness.

## 7. External and internal interfaces

### 7.1 `OutcomeClassifier` — IF-ANA-CLASSIFY (`rg_core.analysis.classify`)

Normative signature (INTERFACE-CONTRACTS §3), refined by additive keyword parameters:

```python
class OutcomeClassifier(Protocol):                          # sync, pure, deterministic, thread-safe
    def classify(self, window: ExposureWindow | WindowSummary, expectations: ExpectationSet, confidence: Confidence,
                 profile: PolicyProfile, ctx: ClassifyContext) -> Classification: ...

def classify_matrix(window: ExposureWindow | WindowSummary, expectations: ExpectationSet, confidence: Confidence,
                    profiles: Sequence[PolicyProfile], ctx: ClassifyContext) -> ClassificationMatrix: ...   # §12.4
def rule_table() -> tuple[ClassificationRule, ...]: ...                                                        # §11.1 as data
def rules_digest() -> Sha256Digest: ...
def window_summary(w: ExposureWindow) -> WindowSummary: ...                                                    # projection (§8.2); RG-P08-004 must supply the fields
def check_classification(c: Classification, ctx: ClassifyContext, confidence: Confidence) -> None: ...         # post-condition invariants (RGE-INTERNAL-0904)
def validate_rule_table() -> None: ...                                                                          # import-time self-check (RGE-INTERNAL-0902)
```

`classify` accepts an `ExposureWindow` (SCH-WINDOW, RG-P08-004) or its summary projection `WindowSummary` (the fields the classifier is allowed to read); passing the full window is converted with `window_summary`. Idempotent; no side effects; no state.

### 7.2 Error codes (block 0900–0999 (RG-P03-005 §8.3))

| Code | Name | Raised by |
|---|---|---|
| RGE-INTERNAL-0901 | `classify_input_invalid` — inconsistent inputs (`x_hi < x_lo`, `x_lo < 0`, clock/epoch mismatch between window and expiry bound, `anchor.valid` contradicting event state) | `classify` |
| RGE-INTERNAL-0902 | `rule_table_invalid` — table fails its self-check (duplicate id, order gap, unknown fact, unreachable rule, missing fallback) | `validate_rule_table` |
| RGE-CONFIG-0903 | `profile_request_invalid` — empty profile list, duplicate profiles, profile outside `PolicyProfile` | `classify_matrix` |
| RGE-INTERNAL-0904 | `classification_invariant_violation` — result breaks an invariant of §11.2 (e.g. `vulnerable` without MUST/validation) | `check_classification` |
| RGE-CONFIG-0905 | `classify_config_invalid` — tolerance out of range (e.g. `enforced_tolerance_ns < 2 s`) | config validation |

## 8. Data structures and schemas

Conventions as RG-P02-001 §8 (frozen `Model`s; `Int64` ns; validator messages begin with the RGE code; `None` omitted). `Classification` and `ClassificationMatrix` are `Document`s (`SCHEMA_ID` `classification`, `classification_matrix`; `1.0`) with `Provenance` (`derivation="calculated"`).

### 8.1 `ClassificationRule` (the rule table is data; §11.1 is its human form)

| Field | Type | Constraint | Description |
|---|---|---|---|
| `id` | Label | `^R-[0-9]{2}$`, unique, order = numeric | |
| `stage` | `Literal["G","E","A","V","F"]` | | gate, enforcement, applicability, verdict, fallback |
| `name` | Slug | | |
| `when` | `tuple[Condition, ...]` | conjunction; empty only for the fallback | |
| `outcome` | `OutcomeClass` | | class emitted when `when` holds |
| `effects` | `RuleEffects` | | `applicability: applicable\|not_applicable`, `vulnerable_candidate: bool`, `reason_code: Label` |
| `cites` | `tuple[Label, ...]` | ≤ 8 | `SV-006`, `TV-10`, `DATA-MODEL §4`, … |
| `version` | Count | | |

`Condition`: `fact: FactName`, `op ∈ {eq, ne, gt, ge, lt, le, in, is_null, not_null}`, `value: bool | int | Label | tuple[Label,...] | ConfigRef` (`ConfigRef` = name of a configuration constant, e.g. `enforced_tolerance_ns`). **Closed fact catalogue** (computed by `facts.extract`, §12.1):

| Fact | Type | Definition |
|---|---|---|
| `ack.state`, `ack.rejection_reason` | enum / Label | latest `RevocationEvent` version |
| `anchor.valid`, `anchor.sound` | bool | `AnchorInterval.valid`, `.upper_bound_sound` (RG-P02-004) |
| `controls.state` | `pass`, `fail_positive`, `fail_negative`, `fail_negative_indistinct`, `fail_sibling`, `fail_foreign`, `missing_required` | `ControlSummary.state` (RG-P02-006 §12.5) |
| `controls.failed` | Label \| null | name of the failed control |
| `probe.invalid_only` | bool | every post-anchor attempt of the credential is `indeterminate` with reason `malformed_request` or `client_auth_failure` |
| `clock.integrity_fail` | bool | `ClockFlags.mono_regression ∨ kind_mixed ∨ cross_epoch_unbounded` |
| `samples.usable_post` | Count | usable (`confirmed`/`denied`, not cache-served) attempts with `s ≥ A_req` |
| `window.censored`, `window.provisional`, `window.flapping`, `window.rate_limit_overlap` | bool | RG-P08-004 flags (rate-limit overlap: an `rate_limited`/`http_5xx` pause overlaps `[s_L, r_D]`, or `[s_L, horizon end]` when censored) |
| `window.x_lo_ns`, `window.x_hi_ns` | Int64 \| null | `X_lo`, `X_hi` (DATA-MODEL §4) |
| `expiry.explains_denial` | bool | `ExpiryBound` reliable ∧ `D` exists ∧ `r_D ≥ e_lo − natural_expiry_margin_ns` |
| `expect.status` | enum | `ResolvedExpectation.status` (RG-P02-005) |
| `expect.form`, `expect.strength`, `expect.source_type` | enum | of the resolved rule |
| `expect.blockers_empty` | bool | `ResolvedExpectation.blockers == ()` |
| `verdict` | enum | `evaluate(...)` result (`within`, `beyond_grace`, `violates`, `undetermined`, `not_evaluable`) — `null` when `expect.status ≠ resolved` |
| `probe.category` | enum | `ProbeCategory` of the window's probe |
| `credential.type`, `credential.lifetime_s` | enum / Count \| null | |
| `validation.independent` | bool | `IndependentValidation.valid` (§12.3) |
| `change.verified` | `true`, `false`, `unknown` | `change_verified` (RG-P02-004) |
| `confidence.level` | `ConfidenceLevel` | RG-P02-006 |

### 8.2 Inputs

`WindowSummary` (projection of `ExposureWindow`): `credential_ref`, `target_ref`, `event_ref`, `x_lo_ns`, `x_hi_ns`, `censored`, `provisional_denial`, `flapping`, `l_send_mono_ns`, `l_recv_mono_ns` (both `None` iff no `L`), `d_recv_mono_ns`, `horizon_end_mono_ns`, `rate_limit_overlap`, `usable_post_samples`, `clock_id`, `epoch`, `anchor: AnchorSummary{valid, quality, upper_bound_sound, a_req_mono_ns, a_ack_mono_ns}`.
`ClassifyContext`: `key_parts` (`credential_type`, `format`, `validation_mode`, `event_kind`), `resolve_ctx: ResolveContext` (RG-P02-005 facts + `mode_source`), `expiry: ExpiryBound | None`, `credential_lifetime_s`, `probe_category`, `controls: ControlSummary`, `clock: ClockFlags{mono_regression, kind_mixed, cross_epoch_unbounded, wall_step_overlap}`, `probe_invalid_only`, `event: EventSummary{ack_state, rejection_reason}`, `state_change_verified: Tri`, `validation: ValidationEvidence`, `config: ClassifyConfig`.
`ControlSummary`: `state` (fact table), `failed_control: Label | None`, `required: tuple[ControlRole,…]`, `negative_distinct: bool`.
`ValidationEvidence`: `oracle: Literal["agree","disagree","none","unsupported"]`, `oracle_obs_ref: ObsId | None`, `oracle_probe_kind: ProbeKind | None`, `oracle_after_violation_threshold: bool`, `repetitions_agreeing: Count` (independent trials **including this one** whose window verdict is `violates` under the same rule), `repetitions_disagreeing: Count`.

### 8.3 Outputs

`RationaleStep`: `step: Count` (1-based), `rule_id: Label`, `stage`, `name: Slug`, `inputs: tuple[(Label, bool|Int64|Label), …]` (≤ 6, only facts the rule reads), `result: bool` (did `when` hold), `effect: Literal["continue","terminate"]`, `cites: tuple[Label,…]`, `derivation: Literal["calculated"]`. Steps are recorded for **every rule evaluated in order up to and including the rule that fires** (≤ 27).
`FpCheck`: `id` (`FP-01`…), `rule_id`, `result: Literal["pass","triggered","not_applicable"]`, `values: tuple[(Label, bool|Int64|Label),…]`.
`IndependentValidation`: `second_oracle: bool`, `repetition: bool`, `repetitions_agreeing`, `repetitions_disagreeing`, `valid: bool` (computed §12.3).
`Classification`:

| Field | Type | Description |
|---|---|---|
| `schema_version`, `derivation`, `produced_by` | | `calculated` |
| `credential_ref`, `target_ref`, `event_ref` | ids | window identity |
| `profile` | `PolicyProfile` | frozen name; **recorded in every classification** (TV-11) |
| `outcome` | `OutcomeClass` | exactly one |
| `rule_id` | Label | the rule that fired |
| `applicability` | `applicable \| not_applicable` | `not_applicable` ⇒ outcome `expected`, never a finding (SV-044) |
| `expectation` | `ExpectationRef{status, rule_id?, tier?, strength?, source?: str (canonical string), set_digest, blockers}` | what the verdict was compared with |
| `verdict` | enum \| None | `evaluate` verdict |
| `vulnerable_candidate` | bool | `true` for R-22 (a MUST-level violation that failed a confirmation condition) |
| `downgrade_reasons` | `tuple[Label,…]` | for R-22: `blocker:<label>`, `validation_missing`, `change_not_verified`, `change_verification_unknown`, `confidence_below_minimum` (this order) |
| `independent_validation` | `IndependentValidation` | frozen name `Finding.independent_validation` |
| `confidence_level` | `ConfidenceLevel` | echo |
| `bands` | `BandRecord{enforced_tolerance_ns, natural_expiry_margin_ns, skew, propagation, declared: (grace, ambiguous), risk_lifetime_s}` | TV-11: values in force |
| `rationale_steps` | `tuple[RationaleStep,…]` | frozen name `Finding.rationale_steps` |
| `fp_checks` | `tuple[FpCheck,…]` | §11.3 (feeds `Finding.false_positive_risks`) |
| `algorithm_id`, `rules_digest` | str, `Sha256Digest` | `rg.classify.rules@1.0.0` + table digest |

`ClassificationMatrix`: `window_identity`, `profiles: tuple[PolicyProfile,…]` (request order; first = primary), `results: tuple[Classification,…]` (same order), `matrix: Mapping[PolicyProfile, OutcomeClass]` (frozen `Finding.profile_matrix`), `shared_gate: Label | None` (the gate rule R-01…R-06 that terminated *all* profiles, if any).

```json
{"schema_version": "1.0", "credential_ref": "crd_01M4QJ0D1MP1XPA7Z3DJ8FSSZ5", "target_ref": "tgt_01M4QJ0B1WF5KZNWJ47TAN9ZT2",
 "event_ref": "rev_01M4QJ25K0E0ZBGJ09TQM83XSS", "profile": "protocol", "outcome": "enforced", "rule_id": "R-07", "applicability": "applicable",
 "expectation": {"status": "no_expectation", "rule_id": "exr.protocol.session.none", "tier": "protocol", "strength": "ID",
                 "source": "standard:STD-029§intro", "set_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000", "blockers": []},
 "vulnerable_candidate": false, "downgrade_reasons": [],
 "independent_validation": {"second_oracle": false, "repetition": false, "repetitions_agreeing": 0, "repetitions_disagreeing": 0, "valid": false},
 "confidence_level": "high",
 "bands": {"enforced_tolerance_ns": "5000000000", "natural_expiry_margin_ns": "60000000000", "skew": ["60000000000", "300000000000"],
           "propagation": ["30000000000", "120000000000"], "declared": ["5000000000", "30000000000"], "risk_lifetime_s": 3600},
 "rationale_steps": [
  {"step": 1, "rule_id": "R-01", "stage": "G", "name": "capability-unsupported", "inputs": [["ack.state", "acknowledged"]], "result": false, "effect": "continue", "cites": ["TV-10"], "derivation": "calculated"},
  {"step": 2, "rule_id": "R-02", "stage": "G", "name": "anchor-unavailable", "inputs": [["anchor.valid", true]], "result": false, "effect": "continue", "cites": ["SV-006"], "derivation": "calculated"},
  {"step": 3, "rule_id": "R-03", "stage": "G", "name": "controls-failed", "inputs": [["controls.state", "pass"]], "result": false, "effect": "continue", "cites": ["TV-01", "TV-02"], "derivation": "calculated"},
  {"step": 4, "rule_id": "R-04", "stage": "G", "name": "probe-invalid", "inputs": [["probe.invalid_only", false]], "result": false, "effect": "continue", "cites": ["TV-17"], "derivation": "calculated"},
  {"step": 5, "rule_id": "R-05", "stage": "G", "name": "clock-integrity", "inputs": [["clock.integrity_fail", false]], "result": false, "effect": "continue", "cites": ["TM-28"], "derivation": "calculated"},
  {"step": 6, "rule_id": "R-06", "stage": "G", "name": "no-usable-samples", "inputs": [["samples.usable_post", 11]], "result": false, "effect": "continue", "cites": ["TV-07"], "derivation": "calculated"},
  {"step": 7, "rule_id": "R-07", "stage": "E", "name": "enforced", "inputs": [["window.x_hi_ns", "1040000000"], ["window.flapping", false], ["window.censored", false], ["anchor.sound", true], ["expiry.explains_denial", false]], "result": true, "effect": "terminate", "cites": ["ADR-0010", "SV-011"], "derivation": "calculated"}],
 "fp_checks": [{"id": "FP-01", "rule_id": "R-07", "result": "pass", "values": [["expiry.explains_denial", false]]}],
 "algorithm_id": "rg.classify.rules@1.0.0", "rules_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
 "derivation": "calculated", "produced_by": {"component": "rg_core.analysis.classify", "version": "1.0"}}
```

(Digest values are placeholders of the right shape; `inputs` values that are `Int64` appear as decimal strings in JSON.)

## 9. Inputs, outputs, and validation rules

| # | Rule | Code |
|---|---|---|
| VR-1 | `window.x_lo_ns ≥ 0`; `x_hi_ns` is `None` or `≥ x_lo_ns`; `censored ⇔ x_hi_ns is None` (unless `provisional_denial`, where `x_hi_ns` is present); `l_send/l_recv` both `None` or both set with `l_send ≤ l_recv` | RGE-INTERNAL-0901 |
| VR-2 | window, anchor, expiry bound and observations share `(clock_id, epoch)` | RGE-INTERNAL-0901 |
| VR-3 | `anchor.valid` is consistent with `event.ack_state` (`valid ⇔ ack_state ∈ {acknowledged, observed}`) | RGE-INTERNAL-0901 |
| VR-4 | `profiles` non-empty, unique, members of `PolicyProfile` | RGE-CONFIG-0903 |
| VR-5 | `ClassifyConfig` ranges: `enforced_tolerance_ns ≥ 2 000 000 000`; `natural_expiry_margin_ns ≥ 2 000 000 000`; `risk_lifetime_s ≥ 60`; `min_repetitions ≥ 2`; `vulnerable_min_confidence ∈ {medium, high}` | RGE-CONFIG-0905 |
| VR-6 | rule table self-check (§11.1: ids contiguous `R-01…R-27`, every fact name in the catalogue, last rule is the unconditional fallback, no rule shadowed by an earlier identical `when`) | RGE-INTERNAL-0902 |
| VR-7 | post-conditions §11.2 INV-3…INV-9 on every produced `Classification` | RGE-INTERNAL-0904 |

## 10. Detailed execution behavior

1. **Inputs assembled by RG-P08-006** per `(credential, target, event)`: window (RG-P08-004), `Confidence` (RG-P08-005), controls/validation evidence (RG-P05-007, RG-P08-007), `ExpectationSet` composed at `VALIDATED` (RG-P02-005 §10), context facts.
2. **`classify_matrix(profiles)`**: compute the *shared* facts once (`facts.extract` for profile-independent facts); evaluate gates R-01…R-06 once — if one fires every profile gets that outcome with the same steps; otherwise for each profile resolve the expectation (`ExpectationSet.resolve` + `evaluate`) and run stages E, A, V (R-07 onward) independently.
3. **Per profile `classify`**: evaluate rules in order; record a `RationaleStep` per evaluated rule; the first rule whose `when` holds fires; compute `downgrade_reasons`, `fp_checks`, `bands`; run `check_classification` (post-conditions) before returning.
4. **Terminal state.** The engine passes the primary profile's outcomes to `ExperimentMachine.disposition` (RG-P02-007): all `inconclusive` ⇒ terminal `INCONCLUSIVE`, else `COMPLETE`.
5. **Re-analysis.** A different profile or newer rules/baselines ⇒ call again; the earlier `Classification` is never modified (FR-ANA-006, ADR-0013). `rules_digest` and `algorithm_id` identify the table used.
6. **Time.** The classifier reads no clock; all quantities are `Int64` ns of the run clock.

## 11. State transitions and invariants

### 11.1 The ordered rule table (normative; `rule_table()` returns exactly this)

Evaluation is **first-match-wins in ascending id order**. Stage G rules (R-01…R-06) are *profile-independent gates*; E (R-07, R-08) *enforcement*; A (R-09…R-13) *expectation applicability*; V (R-14…R-26) *verdict mapping*; F (R-27) *fallback*. `τ` = `enforced_tolerance_ns`; `risk` = `risk_lifetime_s`; `margin` = `natural_expiry_margin_ns`.

| ID | Stage | Name | `when` (all conditions) | Outcome · effects | Cites |
|---|---|---|---|---|---|
| R-01 | G | capability-unsupported | `ack.state = rejected` ∧ `ack.rejection_reason = "unsupported_capability"` | `expected`, applicability `not_applicable` (reason `capability_unsupported`) | TV-10, SV-018, SV-044, FR-ANA-007 |
| R-02 | G | anchor-unavailable | `anchor.valid = false` | `inconclusive` (reason `anchor_unavailable`; no exposure claim) | SV-006, DATA-MODEL §4, TV-06 |
| R-03 | G | controls-failed | `controls.state ≠ pass` | `inconclusive` (reason `control_failed:<controls.failed>`) | TV-01, TV-02, SV-001, DATA-MODEL §9.5, TM-13 |
| R-04 | G | probe-invalid | `probe.invalid_only = true` | `inconclusive` (reason `probe_invalid`) | TV-17, SV-003, SV-008, SV-049 |
| R-05 | G | clock-integrity | `clock.integrity_fail = true` | `inconclusive` (reason `clock_integrity`) | TM-28, DATA-MODEL §9.8 |
| R-06 | G | no-usable-samples | `samples.usable_post = 0` | `inconclusive` (reason `no_usable_samples`) | TV-07, SV-047 |
| R-07 | E | enforced | `window.censored = false` ∧ `window.provisional = false` ∧ `window.flapping = false` ∧ `anchor.sound = true` ∧ `window.x_hi_ns ≤ τ` ∧ `expiry.explains_denial = false` | `enforced` | ADR-0010, SV-011 |
| R-08 | E | expiry-confound | as R-07 but `expiry.explains_denial = true` | `expected` (reason `natural_expiry_not_excluded`: enforcement not demonstrated) | TV-09, SV-010, SV-011 |
| R-09 | A | not-applicable | `expect.status = not_applicable` | `expected`, applicability `not_applicable` | TV-10, SV-018, SV-044 |
| R-10 | A | undecided-expectation | `expect.status ∈ {unresolved, conflict, unknown_precondition}` | `needs_verification` (reason `expectation_<status>`) | R-001, TV-22, TV-10 |
| R-11 | A | liveness-default | `expect.status = no_expectation` ∧ `probe.category = connection_liveness` | `needs_verification` (open-connection survival) | SV-055, TF R-014 |
| R-12 | A | no-expectation-long-lived | `expect.status = no_expectation` ∧ `credential.type = access_token` ∧ `credential.lifetime_s > risk` ∧ `window.x_lo_ns > τ` | `risky_config` (reason `lifetime_above_recommended`) | SV-012, SV-013, RFC 6750 §5.3 |
| R-13 | A | no-expectation | `expect.status = no_expectation` | `expected` | SV-012, SV-024, SV-030, SV-034 |
| R-14 | V | within-long-lived | `verdict = within` ∧ `expect.form = until_exp` ∧ `credential.type = access_token` ∧ `credential.lifetime_s > risk` | `risky_config` | SV-012, SV-013 |
| R-15 | V | within-declared | `verdict = within` ∧ `expect.source_type ∈ {vendor_doc, operator}` | `documented_delay` | SV-012, SV-016, charter §2 |
| R-16 | V | within-standard | `verdict = within` | `expected` | SV-010, SV-011, SV-012, SV-015 |
| R-17 | V | beyond-should | `verdict = beyond_grace` ∧ `expect.strength = SHOULD` | `risky_config` | SV-013 |
| R-18 | V | beyond-other | `verdict = beyond_grace` | `needs_verification` (reason `beyond_grace_ambiguous`) | SV-010, SV-015 |
| R-19 | V | violates-should | `verdict = violates` ∧ `expect.strength = SHOULD` | `risky_config` | SV-013 |
| R-20 | V | violates-may | `verdict = violates` ∧ `expect.strength = MAY` | `needs_verification` (reason `declared_window_exceeded`) | SV-012, SV-037 |
| R-21 | V | violates-must-confirmed | `verdict = violates` ∧ `expect.strength = MUST` ∧ `expect.blockers_empty` ∧ `validation.independent` ∧ `change.verified = true` ∧ `confidence.level ≥ vulnerable_min_confidence` | `vulnerable` | TV-23, TV-04, SV-010, SV-015, SV-019, SV-032, SV-033, DATA-MODEL §9.6 |
| R-22 | V | violates-must-candidate | `verdict = violates` ∧ `expect.strength = MUST` | `needs_verification`, `vulnerable_candidate = true`, `downgrade_reasons` per §8.3 | TV-23, TV-04, TV-22 |
| R-23 | V | undetermined-polluted | `verdict = undetermined` ∧ `window.rate_limit_overlap` | `inconclusive` (reason `rate_limited_window`) | TV-13, SV-043 |
| R-24 | V | undetermined-censored | `verdict = undetermined` ∧ `window.x_hi_ns is_null` | `inconclusive` (reason `horizon_insufficient`) | TV-07, FR-TEMP-011 |
| R-25 | V | undetermined-localisation | `verdict = undetermined` | `needs_verification` (reason `localisation_ambiguous`: denser probing would decide) | SV-047, SV-004 |
| R-26 | V | not-evaluable | `verdict = not_evaluable` | `needs_verification` (reason `expiry_unreliable`) | TV-09 |
| R-27 | F | fallback | (always) | `needs_verification` (reason `internal_fallback`; **must be unreachable**, §11.2 INV-2) | — |

Because `verdict` is `null` unless `expect.status = resolved`, rules R-14…R-26 can only fire for resolved rules; R-10 and R-13 absorb the other statuses before them.

### 11.2 Definitions and invariants

**Class definitions (exact predicates).**
- **`enforced`** ⇔ R-07: gates passed (valid controls, valid anchor, usable samples), the window is complete (`D` confirmed by the tail, no flapping), the anchor's upper bound is sound, and **`X_hi ≤ τ`** (the measured upper bound of continued access is within the tolerance, default 5 s, never below 2 s, SV-047) and the denial is **not** explained by natural expiry (`D` is not within `margin` of the credential's expiry lower bound). No expectation is required: enforcement is a statement about the measurement alone.
- **`expected`** ⇔ R-01/R-08/R-09/R-13/R-16: continued access (or its absence) is what the *standard-sourced* rule or the absence of any rule permits; or a test is not applicable. Never a finding.
- **`documented_delay`** ⇔ R-15: verdict `within` for a resolved rule whose **source is a vendor document or an operator declaration** (`vendor_doc`/`operator`). Standards alone never produce it (charter §2).
- **`risky_config`** ⇔ R-12/R-14/R-17/R-19: behaviour permitted or SHOULD-level but beyond a recommended bound (access-token lifetime above `risk`; SHOULD-level rule exceeded). Not a defect.
- **`vulnerable`** ⇔ R-21: all of — MUST-level expectation in the requested profile with no blockers (strong evidence tag, declared mode or mode-independent rule, no conflict, known preconditions); verdict `violates` (`X_lo` > `deadline + ambiguous`, or accepted after `exp + ambiguous`); valid controls; **independent validation** (§12.3); `change.verified = true`; confidence ≥ `vulnerable_min_confidence` (default `medium`).
- **`needs_verification`** ⇔ R-10/R-11/R-18/R-20/R-22/R-25/R-26/R-27: evidence is consistent with a defect or insufficiently decisive, but a rule, expectation, validation or localisation requirement is unmet. `vulnerable_candidate=true` marks R-22.
- **`inconclusive`** ⇔ R-02…R-06/R-23/R-24: a validity precondition failed or evidence is insufficient (failed controls, unacknowledged revocation, rate-limit pollution, horizon too short).

**Invariants (testable; enforced by `check_classification`):**
- **INV-1 (determinism/purity)** `classify` is a pure function of its inputs; equal inputs ⇒ byte-identical `Classification` (including steps); no randomness, clock or I/O.
- **INV-2 (totality)** For every consistent input exactly one rule fires; the fallback R-27 is unreachable (proved by bounded enumeration over the discrete fact space in TST-RG-P02-009-03).
- **INV-3 (`vulnerable` preconditions; DATA-MODEL §9.6)** `outcome = vulnerable` ⇒ `expectation.status = resolved`, `strength = MUST`, `blockers = ()`, `verdict = violates`, `controls.state = pass`, `independent_validation.valid`, `change.verified = true`, `confidence ≥ vulnerable_min_confidence`.
- **INV-4** `outcome = enforced` ⇒ `¬censored ∧ ¬provisional ∧ ¬flapping ∧ anchor.sound ∧ x_hi ≤ τ ∧ controls pass`.
- **INV-5** `outcome = documented_delay` ⇒ `verdict = within` ∧ rule source ∈ {vendor_doc, operator}; a standard-only rule never yields it.
- **INV-6** `outcome = inconclusive` ⇒ the firing rule ∈ {R-02…R-06, R-23, R-24}; R-01 and R-09 yield `expected` with `applicability = not_applicable`.
- **INV-7 (R-001)** A credential whose resolved rule is `until_exp` (local JWT) is never `vulnerable` unless `s_L > e_hi + ambiguous` (accepted more than 300 s by default after its own expiry) — "an unexpired JWT remaining usable" cannot be `vulnerable` on that fact alone.
- **INV-8** `expectation.status ≠ resolved` ⇒ `outcome ≠ vulnerable`; an unknown/inferred mode on a mode-dependent rule, a weak evidence tag, a conflict or an unknown precondition always yield blockers/status that exclude R-21.
- **INV-9** `classify_matrix`: gate outcomes (R-01…R-06) are identical across profiles; results of profile *p* do not depend on the other requested profiles; `matrix[p] = results[p].outcome`.
- **INV-10 (monotonicity)** For fixed facts with all gates passed and a resolved rule of strength `MUST` or `MAY`, or `no_expectation`, raising `x_lo` (and `x_hi` consistently) never lowers the severity rank (`enforced 0 < expected 1 < documented_delay 2 < risky_config 3 < needs_verification 4 < vulnerable 5`) among non-`inconclusive` outcomes; lowering confidence or removing validation never raises it. (Excluded by design: `SHOULD`-level rules, where the *uncertain* `undetermined` region maps conservatively to `needs_verification` (4) while the *certain* `beyond_grace`/`violates` regions map to `risky_config` (3) — certainty may lower the label, never hide it.)
- **INV-11** Every `Classification` carries `profile`, `bands`, `algorithm_id`, `rules_digest` and ≥ 1 `RationaleStep`; the last step has `effect = terminate` and `result = true`; earlier steps have `result = false`.
- **INV-12** No rule outcome depends on `mechanism_hints`, response bodies or free text (inputs are the typed facts of §8.1 only).

### 11.3 False-positive reduction rules (FR-ANA-007) and where they act

| ID | False-positive risk | Rule(s) | Recorded values |
|---|---|---|---|
| FP-01 | natural expiry mistaken for revocation (TV-09, SV-010/011) | R-07 condition `expiry.explains_denial = false`; R-08 | `expiry.explains_denial`, margin |
| FP-02 | cache-served response treated as access/denial (TV-14, SV-048) | excluded upstream (`cache_served` ⇒ `indeterminate`, RG-P02-006 INV-6); counted in CF-15; `samples.usable_post` counts only usable attempts | `cache_served_count` |
| FP-03 | rate-limit/5xx window mistaken for denial or hiding access (TV-13, SV-043) | R-23; confidence CF-07 | `window.rate_limit_overlap` |
| FP-04 | malformed probe (400 `invalid_request`, wrong presentation) (TV-17, SV-003/009) | R-04 | `probe.invalid_only` |
| FP-05 | client-authentication failure (401 `invalid_client`) (TV-17, SV-008/049) | R-04 | idem |
| FP-06 | unsupported capability (TV-10, SV-018/044) | R-01, R-09 | `ack.rejection_reason`, `expect.status` |
| FP-07 | control failure or identical responses (TV-01/02, TM-13) | R-03 | `controls.state`, `controls.failed` |
| FP-08 | single-run artefact (TV-23(b), TV-21) | R-21 requires `validation.independent`; R-22 otherwise | `validation.*` |
| FP-09 | revocation call "success" not proof of state change (TV-04, SV-005) | R-21 requires `change.verified = true`; R-22 | `change.verified` |
| FP-10 | mechanism/mode unknown or inferred (TV-22) | R-10; blockers `mode_*` in R-22 | `expect.status`, blockers |
| FP-11 | weak source evidence (RESEARCH-REGISTER evidence rule) | blocker `evidence_tag:*` ⇒ R-22 | blockers |
| FP-12 | unsound anchor upper bound (receipt-only external events) | R-07 requires `anchor.sound`; `evaluate` never returns `within` (RG-P02-005 INV-10) | `anchor.sound` |

## 12. Core algorithms and pseudocode

### 12.1 `classify` (per profile)

```
def classify(window, expectations, confidence, profile, ctx):
    w = window_summary(window); check_inputs(w, ctx)                       # RGE-INTERNAL-0901
    key = ExpectationKey(ctx.credential_type, ctx.format, ctx.validation_mode, ctx.event_kind, profile)
    resolved = expectations.resolve(key, ctx.resolve_ctx, config=ctx.config.expectation)
    verdict = None
    if resolved.status == resolved_:
        verdict = evaluate(resolved, w.as_window_facts(), ctx.expiry, config=ctx.config.expectation).verdict
    facts = extract_facts(w, ctx, resolved, verdict, confidence)           # closed catalogue §8.1
    steps = []
    for rule in RULES:                                                    # R-01 … R-27, ascending
        holds = all(eval_condition(c, facts, ctx.config) for c in rule.when)     # empty `when` holds (fallback)
        steps.append(RationaleStep(len(steps)+1, rule, inputs=read_facts(rule, facts), result=holds, effect="terminate" if holds else "continue"))
        if holds: break
    out = build_classification(rule, steps, resolved, verdict, w, ctx, confidence, facts)
    check_classification(out, ctx, confidence)                             # RGE-INTERNAL-0904
    return out
```

`extract_facts` computes: `anchor.*` from `AnchorSummary`; `controls.*` from `ControlSummary`; `probe.invalid_only`, `clock.integrity_fail` (= `mono_regression ∨ kind_mixed ∨ cross_epoch_unbounded`; a `wall_step_overlap` is **not** a gate — it lowers confidence via CF-08); `samples.usable_post`; window flags; `expiry.explains_denial = (ctx.expiry is not None and ctx.expiry.reliable and w.d_recv_mono_ns is not None and w.d_recv_mono_ns ≥ ctx.expiry.lo_mono_ns − natural_expiry_margin_ns)`; expectation facts from `resolved`; `change.verified`, `confidence.level`.

### 12.2 `downgrade_reasons` for R-22 (deterministic order)

```
reasons  = ["blocker:" + b for b in sorted(resolved.blockers)]
reasons += ["validation_missing"] if not validation.independent
reasons += ["change_not_verified"] if change.verified == false else ["change_verification_unknown"] if change.verified == unknown else []
reasons += ["confidence_below_minimum"] if confidence.level < vulnerable_min_confidence
```
`vulnerable_candidate = true` (R-22 only); the report tells the operator which confirmation to obtain (second oracle, repetition, independent state read).

### 12.3 Independent validation (TV-23(b))

`IndependentValidation.valid` ⇔ `second_oracle_ok ∨ repetition_ok` where
- `second_oracle_ok` ⇔ `oracle = agree` ∧ the oracle observation's probe **kind/category differs** from the probe that produced `L` (e.g. introspection/userinfo/session-liveness/second protected endpoint vs the resource call) ∧ it was taken at or after `A_ack + deadline + ambiguous` (`oracle_after_violation_threshold`) and confirms continued validity (`access_confirmed` or oracle verdict `active`). An oracle that *disagrees* never validates and (via CF-12 `cap_low`) blocks R-21.
- `repetition_ok` ⇔ `repetitions_agreeing ≥ min_repetitions` (default 2, counting this run) ∧ `repetitions_disagreeing = 0`; each repetition used a fresh credential family/session (TV-12/TV-18) and yielded verdict `violates` under the same rule.
The classifier **consumes** this evidence; producing it (running a second trial, calling an oracle) is the job of RG-P08-007/RG-P05-007. A MUST-level `violates` without it ends in R-22.

### 12.4 `classify_matrix`

```
shared = [extract profile-independent facts once]
for rule in R-01..R-06: if holds(rule, shared): return same Classification (profile=p) for every requested p   # shared_gate = rule.id
results = [classify(window, expectations, confidence, p, ctx) for p in profiles]
return ClassificationMatrix(profiles, results, matrix={r.profile: r.outcome for r in results}, shared_gate=None)
```

### 12.5 Golden worked classifications (the golden dataset)

All values in seconds on one monotonic clock (integers in the dataset); `A_req`, `A_ack` as stated; `τ = 5 s`, `margin = 60 s`, `risk = 3600 s`; bands: skew 60/300, propagation 30/120, declared 5/30; confidence `high` unless stated; controls pass unless stated. `X_lo = max(0, s_L − A_ack)`, `X_hi = r_D − A_req`.

| # | Fixture | Inputs | Per-profile result (rule) |
|---|---|---|---|
| **GF-01** | **Immediate-enforcement session store** | session cookie (`app_own_session`), mode `session_store`, event `session_terminated`; `A = (1000.000, 1000.180)`; no `L`; first post-event attempt denied: `D = (1001.000, 1001.040)`, tail 11 denials to 1011; `X_lo = 0`, `X_hi = 1.040` | `protocol`: `enforced` (R-07; expectation `no_expectation` is irrelevant); `asvs_5_l1`: `enforced` (R-07) |
| **GF-02** | **Per-call introspection** | opaque AT, mode `introspection`, event `access_token_revoked`, `capability.at_revocation = true`; `A = (1000.000, 1000.180)`; `L = (1005.000, 1005.040)`; `D = (1006.000, 1006.060)`; `X_lo = 4.820`, `X_hi = 6.060` (> τ, so not enforced); rule `exr.protocol.introspect.at-revoked` `must_deny_by(0)`, band propagation | `protocol`: verdict `within` (`6.060 ≤ 30`) ⇒ `expected` (R-16; propagation delay tolerated, RFC 7009 §2.1). With operator rule `must_deny_by(0)` MUST, band declared: `X_lo = 4.82 ≤ 5 < X_hi = 6.06` ⇒ `undetermined` ⇒ `needs_verification` (R-25: denser probing decides). Variant GF-02b (first post-event `L = (1000.500, 1000.540)`, `D = (1002.000, 1002.060)`, `X_hi = 2.060`): `enforced` (R-07) |
| **GF-03** | **Introspection cache TTL 60 s; expectation "may allow until TTL"** | opaque AT (lifetime 300 s, minted `[900.000, 900.180]` ⇒ expiry bound `[1200.000, 1201.180]`), mode `introspection_cached`, event `access_token_revoked`; operator rule `exr.operator.cache-60` `may_allow_until(60 s)`, MAY, band declared, source `operator:rs-owner`; `A = (1000.000, 1000.180)`; `L = (1050.000, 1050.040)`; `D = (1052.000, 1052.050)`; `X_lo = 49.820`, `X_hi = 52.050` | `protocol` (rule `exr.protocol.cached.until-exp`): `until_exp` within (`r_L = 1050.04 ≤ 1200 + 60`) ⇒ `expected` (R-16). `operator`: `within` (`52.05 ≤ 60 + 5`) and source `operator` ⇒ **`documented_delay`** (R-15). Variant GF-03b (`L = (1066.000, 1066.040)`, `D = (1070.000, 1070.050)`, `X_lo = 65.820`): operator verdict `beyond_grace` (`65.82 > 65`, `≤ 90`) ⇒ `needs_verification` (R-18); protocol still `expected` |
| **GF-04** | **Local JWT validated until `exp`** | JWT AT, lifetime 900 s minted `[400.000, 400.180]` ⇒ expiry bound `[1300.000, 1301.180]`, mode `jwt_local`, event `account_disabled`, `issuer_role = application_own_session`; `A = (1000.000, 1000.180)`; probes every 30 s; `L = (1290.000, 1290.040)`; `D = (1320.000, 1320.050)`; `X_lo = 289.820`, `X_hi = 320.050` | `protocol`: `until_exp` within ⇒ **`expected`** (R-16; lifetime 900 ≤ 3600). `asvs_5_l1` (rule `exr.asvs5.account-disable`, `must_deny_by(0)` MUST, band propagation): `289.82 > 120` ⇒ `violates`. **GF-04A** (repetitions agreeing = 2, disagreeing = 0; `change.verified = true` via `read_state` delta ok; confidence high): **`vulnerable`** (R-21; ASVS V7.4.2). **GF-04B** (single trial): **`needs_verification`** (R-22, `vulnerable_candidate = true`, `downgrade_reasons = ["validation_missing"]`). Variant GF-04C (`issuer_role = third_party_issued`): the ASVS rule's precondition is false ⇒ chain falls to `protocol` ⇒ `expected` under both profiles |
| **GF-05** | **Refresh token accepted after revocation** | refresh token (opaque), event `refresh_token_revoked` acknowledged (`A = (2000.000, 2000.150)`); preconditions `revocation.acknowledged_no_5xx`, `revocation.same_client`, `credential.directly_targeted` true; refresh probes every 5 s all `access_confirmed` until horizon: `L = (2295.000, 2295.080)`, `D = None` (censored); `X_lo = 294.850`, `X_hi = None`; introspection oracle of the RT reports `inactive` (state change verified); repetition: 2 agreeing trials with fresh families | `protocol`: rule `exr.protocol.rt-revoked.deny` MUST (STD-003 §2, tag V, mode-independent ⇒ no blockers): `294.85 > 120` ⇒ `violates` ⇒ **`vulnerable`** (R-21). `asvs_5_l1`: same rule via the chain ⇒ `vulnerable` |
| **GF-06** | **Flapping enforcement** | opaque AT, `introspection`, event `access_token_revoked`; replicas disagree: accepted/denied alternate until `L = (1150.000, 1150.040)`, final stable denial `D = (1151.000, 1151.060)`; `flapping = true`; `X_lo = 149.820`, `X_hi = 151.060`; verdict `violates`; repetition 2 agreeing, change verified; **confidence `low`** (CF-13 `cap_low`) | `protocol`: `needs_verification` (R-22, `vulnerable_candidate = true`, `downgrade_reasons = ["confidence_below_minimum"]`); R-07 is excluded by `flapping`. |
| **GF-07** | **Censored: no denial by the horizon** | as GF-03 (cache TTL 60 s) but the observation horizon ends at 1040.000: `L = (1039.800, 1039.840)`, `D = None`; `X_lo = 39.620`, `X_hi = None` | `protocol`: until_exp within ⇒ `expected` (R-16). `operator`: `x_lo = 39.62 ≤ 65`, `x_hi` null ⇒ `undetermined`, censored ⇒ **`inconclusive`** (R-24, `horizon_insufficient`). (Contrast GF-05: censoring does not block `vulnerable` when `X_lo` alone exceeds the ambiguous band.) |
| **GF-08** | **Failed negative control** | any scenario; garbage-credential control returned `access_confirmed` on the baseline (or identical responses for valid and garbage tokens) ⇒ `controls.state = fail_negative`, `controls.failed = negative_garbage` | all profiles: `inconclusive` (R-03, reason `control_failed:negative_garbage`); `shared_gate = R-03` |
| **GF-09** | **Rate-limit-polluted window** | `introspection`, event `access_token_revoked`; `L = (1010.000, 1010.040)`; attempts 1011…1100 are `429 Retry-After` (indeterminate, pauses); `D = (1101.000, 1101.050)` after tail; `X_lo = 9.820`, `X_hi = 101.050`; rule MUST propagation (30/120) ⇒ `undetermined` (`X_lo ≤ 30 < X_hi`); `window.rate_limit_overlap = true`; confidence `low` (CF-07 `cap_low`) | `protocol`: `inconclusive` (R-23, `rate_limited_window`) — the 429 span makes the bracket uninformative (TV-13), not a denial |
| **GF-10** | **Unknown validation mode** | opaque AT, mode `unknown` (`mode_source = unknown`), event `account_disabled`; accepted through the horizon: `L = (1600.000, 1600.040)`, `X_lo = 599.820`, censored | `protocol`: no rule matches a mode-specific key ⇒ `expect.status = unresolved` ⇒ **`needs_verification`** (R-10) — never `vulnerable` |
| **GF-11** | **Unsupported capability** | event `access_token_revoked` rejected with `unsupported_token_type` (RFC 7009) ⇒ `ack.state = rejected`, `ack.rejection_reason = unsupported_capability` | all profiles: **`expected`**, applicability `not_applicable` (R-01; never a finding, SV-018/SV-044). (Manual-revocation variant with `capability.at_revocation = false` and a valid anchor: rule `exr.protocol.at-revoke.unsupported` ⇒ R-09 `expected`, `not_applicable`) |
| **GF-12** | **Long-lived JWT (risky configuration)** | JWT AT lifetime 86 400 s, mode `jwt_local`, event `account_disabled`; accepted through a 1 h horizon: `L = (4590.000, 4590.040)`, censored; `X_lo = 3589.820` | `protocol`: `until_exp` within but lifetime 86 400 > 3600 ⇒ **`risky_config`** (R-14; RFC 6750 §5.3 SHOULD ≤ 1 h, SV-013); `asvs_5_l1` (third-party-issued token): same |
| **GF-13** | **JWT accepted long after `exp`** | as GF-04 (expiry bound `[1300.000, 1301.180]`) but `L = (1700.000, 1700.040)`, `D = (1730.000, 1730.050)`; `s_L = 1700 > 1301.18 + 300 = 1601.18` ⇒ `violates`; repetition 2 agreeing; change verified | `protocol`: **`vulnerable`** (R-21; RFC 7519 §4.1.4 MUST, SV-010) — the only way a local-JWT credential becomes `vulnerable` (INV-7) |
| **GF-14** | **Natural-expiry confound** | JWT lifetime 100 s ⇒ expiry bound `[1002.000, 1003.180]`, event `session_terminated`; `D = (1001.000, 1001.040)`, `X_hi = 1.040`; `r_D = 1001.04 ≥ 1002.0 − 60` ⇒ `expiry.explains_denial = true` | `protocol`: **`expected`** (R-08): the token was about to expire; enforcement is not demonstrated (compare GF-01) |
| **GF-15** | **Unacknowledged revocation (503)** | revoke call failed with 503 ⇒ `ack.state = rejected`/`indeterminate`, `anchor.valid = false` | all profiles: `inconclusive` (R-02, `anchor_unavailable`; SV-006) |

**Rationale path example (GF-04A, profile `asvs_5_l1`).** Steps: R-01 false (`ack.state=acknowledged`); R-02 false; R-03 false; R-04 false; R-05 false; R-06 false (`samples.usable_post = 14`); R-07 false (`x_hi = 320.050 s > τ`); R-08 false; R-09 false (`expect.status = resolved`); R-10 false; R-11 false; R-12 false; R-13 false; R-14 false (`verdict = violates`); R-15 false; R-16 false; R-17 false; R-18 false; R-19 false (`strength = MUST`); R-20 false; **R-21 true** (`blockers_empty`, `validation.independent`, `change.verified = true`, `confidence = high ≥ medium`) ⇒ `vulnerable`, 21 steps, last `terminate`. GF-04B stops at **R-22** (21 false, 22 true) with `downgrade_reasons = ["validation_missing"]`.

## 13. Internal functions, methods, or service operations

```python
def extract_facts(w: WindowSummary, ctx: ClassifyContext, resolved: ResolvedExpectation, verdict: Verdict | None, conf: Confidence) -> Mapping[FactName, FactValue]: ...
def eval_condition(c: Condition, facts: Mapping[FactName, FactValue], cfg: ClassifyConfig) -> bool: ...         # closed ops; null-safe (comparisons with null are false except is_null)
def read_facts(rule: ClassificationRule, facts: Mapping[FactName, FactValue]) -> tuple[tuple[Label, FactValue], ...]: ...   # ≤ 6, rule's own facts
def downgrade_reasons(resolved: ResolvedExpectation, v: ValidationEvidence, change: Tri, conf: Confidence, cfg: ClassifyConfig) -> tuple[Label, ...]: ...
def independent_validation(v: ValidationEvidence, cfg: ClassifyConfig) -> IndependentValidation: ...
def fp_checks(facts: Mapping[FactName, FactValue], fired: ClassificationRule) -> tuple[FpCheck, ...]: ...
def severity_rank(o: OutcomeClass) -> int | None: ...                                    # for INV-10 tests; None for inconclusive
def _level_ge(a: ConfidenceLevel, b: ConfidenceLevel) -> bool: ...                       # none < low < medium < high
def _bands_record(cfg: ClassifyConfig) -> BandRecord: ...
```

## 14. Error handling and failure recovery

| Failure | Detection | Handling | Recovery | Code |
|---|---|---|---|---|
| Inconsistent window/anchor/expiry inputs | `check_inputs` | raise; analysis step fails as an internal error (never a class) | fix upstream | RGE-INTERNAL-0901 |
| Rule table corrupted/unreachable fallback | `validate_rule_table` at import | process cannot start | fix table | RGE-INTERNAL-0902 |
| Empty/duplicate profile list | `classify_matrix` | raise | caller fix | RGE-CONFIG-0903 |
| Produced class violates an invariant | `check_classification` | raise before returning; never persists a wrong class | bug fix | RGE-INTERNAL-0904 |
| Tolerance below the 2 s floor | config validation | reject config | operator | RGE-CONFIG-0905 |
| Missing optional evidence (no oracle, no repetition) | facts default | `validation.independent = false` ⇒ R-22 | run confirmation | — (not an error) |
| Expectation unresolved/conflict | status | class `needs_verification` (R-10) | add declaration/baseline | — |

The classifier never "guesses": absence of evidence maps to the conservative class, never to `vulnerable`.

## 15. Security requirements and trust boundaries

- **Dual-use/accuracy (R-001, TV-23):** `vulnerable` is reachable only through R-21's conjunction; INV-3/INV-7/INV-8 are asserted after every classification, so a table or caller bug cannot silently inflate severity.
- **Untrusted inputs:** facts derive from target responses and operator files; the classifier consumes only typed enums/ints/bools (INV-12) — no body, header or free-text content, so hostile responses (TM-13) and injected strings (TM-11/12) cannot influence outcomes except through validated assertions upstream.
- **Operator rules:** operator-profile outcomes are labelled by profile and `operator` source; they never alter the `protocol` classification of the same window (INV-9).
- **Auditability (TM-26):** `rules_digest` + `algorithm_id` + rationale steps + band record make every class reproducible from stored evidence (FR-EVD-002).
- **Secrets:** none touched.

## 16. Concurrency, asynchronous behavior, and resource ownership

Pure functions over immutable inputs ⇒ safe from any thread/task; no shared mutable state (the rule table is an immutable module-level tuple loaded and validated at import). Memory per call ≈ 30 `RationaleStep`s (< 10 KiB). No I/O, locks, executors or cancellation points.

## 17. Performance and resource requirements

Proposals validated by `BM-CLS-1`: `classify` ≤ 300 µs per (window, profile) including expectation resolution for the shipped sets; `classify_matrix` for 3 profiles ≤ 1 ms; 10 000 windows × 3 profiles ≤ 10 s. Rationale: analysis runs once per run (≤ a few hundred windows); the budget only protects batch re-analysis in historical comparison (RG-P08-009).

## 18. Configuration and defaults

| Field | Type | Default | Range | Env var | Notes |
|---|---|---|---|---|---|
| `classify.enforced_tolerance_ns` (τ) | int | 5 000 000 000 | 2 000 000 000 … 600 000 000 000 | `RG_CLASSIFY_ENFORCED_TOLERANCE_NS` | floor 2 s (SV-047) |
| `classify.natural_expiry_margin_ns` | int | 60 000 000 000 | 2 000 000 000 … 3 600 000 000 000 | `RG_CLASSIFY_NATURAL_EXPIRY_MARGIN_NS` | default = skew tolerance |
| `classify.risk_lifetime_s` | int | 3600 | 60 … 31 536 000 | `RG_CLASSIFY_RISK_LIFETIME_S` | RFC 6750 §5.3 SHOULD ≤ 1 h (SV-013) |
| `classify.min_repetitions` | int | 2 | 2 … 20 | `RG_CLASSIFY_MIN_REPETITIONS` | counts the current run |
| `classify.vulnerable_min_confidence` | enum `medium\|high` | `medium` | | `RG_CLASSIFY_VULNERABLE_MIN_CONFIDENCE` | FR-ANA-005 (≥ medium) |
| `expectation.*` (six band values) | | see RG-P02-005 §18 | | | recorded in `bands` |

Precedence: defaults < file < env < CLI; invalid ⇒ `RGE-CONFIG-0905`. Values in force are recorded in every `Classification.bands` and in the run manifest.

## 19. Logging, observability, and evidence requirements

Events: `classification.done` {`credential_ref`, `target_ref`, `profile`, `outcome`, `rule_id`, `vulnerable_candidate`}, `classification.matrix` {`matrix`, `shared_gate`}. Metrics: `classification_total{outcome,rule}`. Evidence/derived: `Classification`/`ClassificationMatrix` stored as derived records (`derivation=calculated`) referencing the window, expectation-set digest and `rules_digest`; report tables print `profile`, bands (TV-11) and the rationale steps. No redaction needs.

## 20. Platform compatibility

Pure Python, integer arithmetic; no locale/timezone/float dependence; identical results on Windows/Linux/macOS (golden dataset executed on all three CI runners).

## 21. Edge cases and invalid inputs

| # | Case | Expected behaviour |
|---|---|---|
| E-1 | `x_hi_ns` exactly `τ` (5 000 000 000) | R-07 holds (inclusive) ⇒ `enforced` |
| E-2 | `x_hi_ns = τ + 1` | R-07 false; flows to A/V stages |
| E-3 | `x_lo = deadline + grace` exactly | verdict not `beyond_grace` (strict `>`; RG-P02-005 E-13) |
| E-4 | `confidence.level = medium` with `vulnerable_min_confidence = high` | R-22, reason `confidence_below_minimum` |
| E-5 | `change.verified = unknown` | R-22, reason `change_verification_unknown` |
| E-6 | oracle `disagree` + 2 agreeing repetitions | `validation.independent = true` by repetition but confidence capped `low` by CF-12 ⇒ R-22 |
| E-7 | `expect.status = no_expectation`, `credential.type = refresh_token`, lifetime 30 days, access continues | R-13 `expected` (R-12 applies only to access tokens, SV-024) |
| E-8 | connection-liveness probe, rule `no_expectation` | R-11 `needs_verification` |
| E-9 | external-event anchor `observed_receipt_only`, immediate denial | R-07 blocked (`anchor.sound=false`); verdict never `within`; typically `undetermined` ⇒ R-25/R-24 |
| E-10 | `wall_step_overlap = true` only | no gate; confidence `low` (CF-08) ⇒ `vulnerable` impossible (R-22), other classes unchanged |
| E-11 | `mono_regression = true` | R-05 `inconclusive` |
| E-12 | profile list `[protocol, protocol]` | `RGE-CONFIG-0903` |
| E-13 | `x_hi_ns < x_lo_ns` | `RGE-INTERNAL-0901` |
| E-14 | two profiles resolving to different rules for one window | independent results; matrix shows both |
| E-15 | `ack.state = observed` (external event) with valid anchor | gates pass; classification proceeds |
| E-16 | no `L`, no `D` (all attempts indeterminate) | R-06 `inconclusive` (`samples.usable_post = 0`) |
| E-17 | resolved rule `until_exp` with unreliable expiry (cookie) | verdict `not_evaluable` ⇒ R-26 `needs_verification` |

## 22. Unit and integration test requirements

| ID | Condition | Expected observation |
|---|---|---|
| TST-RG-P02-009-01 | **Golden dataset**: GF-01…GF-15 (+ variants 02b, 03b, 04A/B/C) as fixtures with exact integer inputs; run `classify_matrix` | outcomes and rule ids exactly as §12.5 tables; rationale steps count as listed for GF-04A/B; run on Linux, Windows, macOS |
| TST-RG-P02-009-02 | Rule-table self-check: ids contiguous, facts in catalogue, fallback last, no shadowed rule; `rules_digest` stable; table equals the reference JSON | `validate_rule_table` passes; mutated tables (duplicate id, unknown fact, missing fallback) raise `RGE-INTERNAL-0902` |
| TST-RG-P02-009-03 | **Totality/unreachable fallback**: exhaustive enumeration over the discrete fact space (booleans, enums, bucketed ints at boundaries `{0, τ−1, τ, τ+1, large}`) | exactly one rule fires for every consistent assignment; R-27 never fires (INV-2) |
| TST-RG-P02-009-04 | **Boundary/mutation suite** (NFR-TEST-001): for every constant and comparison in R-07, R-12, R-14, R-21 and the verdict regions, evaluate at `value−1`, `value`, `value+1` ns (or ≥/> flips) | class flips exactly at the documented side; every operator mutation (`<`↔`≤`, `>`↔`≥`, `and`↔`or`, constant ±1) is killed by ≥ 1 test (mutation score ≥ 70 % gate on `rg_core.analysis.classify`, target 90 %) |
| TST-RG-P02-009-05 | INV-3 property (Hypothesis): random consistent inputs; whenever `outcome = vulnerable` assert the conjunction of INV-3 | holds for all generated inputs |
| TST-RG-P02-009-06 | INV-4/5/6/7/8 properties: `enforced`/`documented_delay`/`inconclusive` preconditions; local-JWT never `vulnerable` unless `s_L > e_hi + a`; unresolved/conflict/mode-inferred never `vulnerable` | holds |
| TST-RG-P02-009-07 | INV-10 monotonicity for `MUST`/`MAY`/`no_expectation` rules: fix facts, sweep `x_lo` upward in steps and `confidence`/validation downward; plus an explicit SHOULD-rule fixture documenting the allowed `needs_verification → risky_config` step | severity rank non-decreasing (non-inconclusive); confidence/validation reductions never raise the class; the SHOULD fixture matches the stated exception |
| TST-RG-P02-009-08 | INV-9 matrix independence: classify `[protocol]`, `[asvs_5_l1]`, `[protocol, asvs_5_l1, operator]` and permutations | each profile's result identical in all call forms; gates shared |
| TST-RG-P02-009-09 | R-001 regression: JWT `jwt_local` accepted until `exp` (and up to `exp + 60 s`), under all profiles without an app-session rule; then `exp + 301 s` | `expected` / `expected`; `vulnerable` only beyond the ambiguous band with validation |
| TST-RG-P02-009-10 | Independent-validation table: oracle agree/disagree/none/unsupported × kind same/different × before/after threshold × repetitions (0…3 agree, 0/1 disagree) | `valid` per §12.3; disagreeing oracle never validates |
| TST-RG-P02-009-11 | Downgrade-reason ordering for R-22 with all combinations of blockers/validation/change/confidence | deterministic order per §12.2 |
| TST-RG-P02-009-12 | FP-01…FP-12 coverage: one fixture per FP rule shows `fp_checks` entry `triggered` with the stated rule | mapping table §11.3 reproduced |
| TST-RG-P02-009-13 | Rationale invariants: every result has ≥ 1 step, last terminates, earlier steps false, steps ≤ 27, inputs ≤ 6 and typed | INV-11 |
| TST-RG-P02-009-14 | Determinism: serialise results of the golden dataset twice and across processes; shuffle input mapping orders | byte-identical canonical JSON (INV-1) |
| TST-RG-P02-009-15 | Config validation: τ < 2 s, margin < 2 s, `min_repetitions = 1`, `vulnerable_min_confidence = low` | `RGE-CONFIG-0905` |
| TST-RG-P02-009-16 | Input validation VR-1…VR-3 (`x_hi < x_lo`, clock mismatch, `anchor.valid` vs event state) | `RGE-INTERNAL-0901` |
| TST-RG-P02-009-17 | Integration (lab virtual time, mock services of RG-P09-003): run the five shipped enforcement profiles (immediate session store, per-call introspection, introspection cache TTL 60 s, local JWT until `exp`, flapping replicas) under `protocol` and `asvs_5_l1`/`operator` | classes equal the golden classes of GF-01, GF-02, GF-03, GF-04, GF-06; repeated runs identical (NFR-REL-002) |
| TST-RG-P02-009-18 | Integration: vulnerable lab variants (refresh token accepted after RT revocation; JWT service accepting past `exp + 300 s`) with repetition evidence from two runs | `vulnerable` for both; without the second run `needs_verification` |
| TST-RG-P02-009-19 | Terminal mapping: feed primary-profile outcomes into `ExperimentMachine.disposition` for GF-08, GF-15 (all `inconclusive`) and mixed sets | `INCONCLUSIVE` / `COMPLETE` (RG-P02-007 INV-10) |

## 23. Mocking and test fixtures

No doubles: pure functions over data. Fixtures: `fixtures/classify/golden_gf01…gf15.json` (inputs + expected `Classification` + expected steps), `rule_table_reference.json`, `fact_space_boundaries.json` (TST-03), `validation_table.json`, `downgrade_orders.json`. Hypothesis strategies: `rg_core.testing.strategies.classify` (consistent `WindowSummary`/`ClassifyContext` generator respecting VR-1…VR-3). Lab ground truth for TST-17/18: enforcement profiles of RG-P09-003 with known `T_deny`.

## 24. Objective acceptance criteria

- **AC-RG-P02-009-01** The classifier maps every golden fixture GF-01…GF-15 (including variants) to the documented class and rule per profile, with identical results on Linux, Windows and macOS (verified by TST-RG-P02-009-01, TST-RG-P02-009-14).
- **AC-RG-P02-009-02** The rule table is total, ordered, self-consistent and its fallback is provably unreachable; mutated tables are rejected (verified by TST-RG-P02-009-02, TST-RG-P02-009-03).
- **AC-RG-P02-009-03** `vulnerable` is emitted only when all of MUST-level strongly-evidenced expectation, `violates` verdict, valid controls, independent validation, verified state change and confidence ≥ medium hold; the local-JWT, unknown-mode, weak-evidence, conflict and unknown-precondition cases can never yield `vulnerable` (verified by TST-RG-P02-009-05, TST-RG-P02-009-06, TST-RG-P02-009-09, TST-RG-P02-009-10, TST-RG-P02-009-11).
- **AC-RG-P02-009-04** Class boundaries flip exactly at the documented thresholds (`τ`, bands, risk lifetime, expiry bounds) and the suite kills ≥ 70 % of operator/constant mutations of the classification module (verified by TST-RG-P02-009-04).
- **AC-RG-P02-009-05** Classification is monotone in evidence of continued access and independent across requested profiles (verified by TST-RG-P02-009-07, TST-RG-P02-009-08).
- **AC-RG-P02-009-06** Every result carries its profile, bands, algorithm id, rules digest and a complete, internally consistent rationale; each FP-01…FP-12 rule is demonstrably active (verified by TST-RG-P02-009-12, TST-RG-P02-009-13).
- **AC-RG-P02-009-07** Invalid inputs and configurations are rejected with the specified codes (verified by TST-RG-P02-009-15, TST-RG-P02-009-16).
- **AC-RG-P02-009-08** In the virtual-time lab the shipped enforcement profiles and vulnerable variants classify as the golden classes, deterministically, and map to the correct terminal experiment state (verified by TST-RG-P02-009-17, TST-RG-P02-009-18, TST-RG-P02-009-19).

## 25. Research sources and engineering rationale

Sources: ADR-0010 (taxonomy, profiles, `vulnerable` requirements); STANDARDS-REFERENCE §3 (expected-enforcement taxonomy), §4 (SV-001, SV-006, SV-010 … SV-016, SV-018 … SV-021, SV-024/025/030, SV-032 … SV-034, SV-043, SV-046, SV-047, SV-048, SV-055), STD-029 (ASVS V7.4.1/V7.4.2, tag V via mirror), STD-003/004/005/007 (V); THREAT-MODEL TV-01…TV-25 (esp. 02, 04, 09, 10, 11, 13, 14, 17, 22, 23), TM-13, SCN-01…15; PRD FR-ANA-005/006/007, NFR-TEST-001; charter §2 (class definitions, anchoring rules), glossary; TECHNICAL-FEASIBILITY R-001 (critical), R-004, R-014; DATA-MODEL §3/§4/§9.5–9.6.

- **DEC-1 Ordered first-match rule table as data** with a closed fact catalogue. Chosen: reviewable line by line against the SV rules, exhaustively testable (TST-03), recorded step by step, replaceable per rules version (`rules_digest`). Rejected: scoring/weighting (opaque, non-reproducible, cannot satisfy TV-23 conjunction), decision trees in code (not auditable), ML classification (non-deterministic, unexplainable). Verification: TST-01/02/03.
- **DEC-2 Gates before expectation; `enforced` before expectation.** Measurement validity (controls, anchor, clock, samples) must hold for *any* statement, including "enforced"; and enforcement is a property of the measurement alone, so a missing expectation cannot hide it. Rejected: evaluating expectations first (an unexplained rule status would mask a clearly enforced result). Verification: TST-01 GF-01.
- **DEC-3 `enforced` threshold on `X_hi`, not `X_lo`.** Only `X_hi ≤ τ` *proves* that continued access lasted at most τ; `X_lo` small with wide `X_hi` (sparse probing) proves nothing (GF-02 operator case: R-25). Rejected: `X_lo ≤ τ` (would certify enforcement from sparse samples; contradicts TV-07/SV-047). Verification: TST-04.
- **DEC-4 `documented_delay` requires a vendor/operator source.** Standards alone never produce it (charter §2 rule); a documented window is a *claim by the operator of the target* that is being checked. Verification: INV-5, TST-06.
- **DEC-5 MUST violations default to `needs_verification` unless confirmed** (R-22) rather than to `vulnerable` with a warning flag. The cost of a false vulnerability (R-001, TV-23) exceeds the cost of asking for one more confirmation; `vulnerable_candidate` + `downgrade_reasons` tell the operator exactly what is missing. Rejected: emitting `vulnerable` with low-confidence label. Verification: TST-05/11.
- **DEC-6 Local JWT cannot become `vulnerable` except past `exp + ambiguous`** under the protocol rule; application-session semantics come only from the ASVS profile and only when the credential is declared `application_own_session` (STANDARDS-REFERENCE STD-029 intro). Verification: GF-04/GF-12/GF-13, TST-09.
- **DEC-7 Per-profile results are independent**, never "the worst of" or "the best of" (reports show the matrix; ADR-0010). Rejected: aggregating into one class (hides policy dependence, the product's core point). Verification: TST-08.
- **DEC-8 Rate-limit pollution → `inconclusive` only when it makes the verdict undetermined**; polluted windows whose `X_lo` alone decides remain classifiable (the bound is still entailed). Verification: GF-09 vs GF-05.
- **DEC-9 Unsupported capability is `expected`/not-applicable, not `inconclusive`** (TV-10: "NOT_APPLICABLE/EXPECTED, never VULN"); it is not an evidence failure. Verification: GF-11.

## 26. Remaining uncertainties or assumptions

| # | Assumption | Evidence tag | Falsifying test |
|---|---|---|---|
| A-1 | Default thresholds (τ = 5 s, margin 60 s, risk 3600 s, 2 repetitions) are appropriate; they are policy proposals, not standard numbers (SV-047; RFC 6750 §5.3 is SHOULD) | proposal | threshold sweeps on lab and Keycloak runs (RG-P12); all configurable and recorded |
| A-2 | The rejection label `unsupported_capability` is set by the action framework (RG-P06-001) when an adapter raises `RGE-PROVIDER-UNSUPPORTED` or the provider answers `unsupported_token_type` | design (contract between RG-P06-001 and this spec) | RG-P06-001 contract test; otherwise GF-11 degrades to `inconclusive` (R-02) |
| A-3 | `ExposureWindow` (RG-P08-004) exposes the fields of `WindowSummary` incl. `rate_limit_overlap`, `provisional_denial`, `usable_post_samples` | frozen DATA-MODEL §4 + this spec | RG-P08-004 conformance suite reuses the golden inputs |
| A-4 | A second oracle of a *different probe kind* is available for most MUST-level checks; otherwise repetition (2 runs) is the practical path | design | scenario catalog review (RG-P07-002/-003) |
| A-5 | ASVS V7.4.1/V7.4.2 apply to the application's own session tokens only (STD-029 scope; intro text S) | V (requirement text) / S (scope) | spec re-read by RG-P08-008 / audit RG-P15 |
| A-6 | RFC 7009 propagation delay is unquantified, so the propagation band (30 s/120 s) is a policy default | V (STD-003) | none (policy); configurable |
| A-7 | `needs_verification` is the right class for flapping that also violates a MUST (non-monotone enforcement is not covered by any standard) | design (WF-01 F5: "NEEDS_VERIFICATION or per rules") | operator review of flapping reports (WF-09) |
| A-8 | The golden numbers in §12.5 are consistent with RG-P02-005 §12.3 and RG-P02-006 §12.2 | verified by prototype calculation during authoring | TST-RG-P02-009-01 (executable) |
| A-9 | `expiry.explains_denial` margin = skew tolerance (60 s) is adequate for servers with clocks running slightly ahead | I | lab clock-skew injection (RG-P09-004) |

## 27. Maintainability, portability, and future extension requirements

- **Versioning:** the rule table has `version` per rule and a table `rules_digest`; any change of a predicate, outcome or order bumps `algorithm_id` (`rg.classify.rules@1.x`), historical `Classification`s keep the version they were computed with, and history comparison (RG-P08-009) flags results computed under different versions. Adding a profile adds expectation rules (RG-P02-005), not classifier rules. Changing an *outcome* of an existing rule is major.
- **Extension points:** new facts (additive catalogue entries), new rules inserted at a stage with explicit renumbering through a migration of `rule_table_reference.json`; new outcome classes require an ADR-0010 amendment; plugins cannot add rules (the classifier is not a plugin point, by design — classification integrity).
- **Reuse:** the table-driven engine (`facts` → ordered conditions → rationale) is independent of identity semantics and reusable as a generic explainable rule engine (master-prompt reusable component "confidence/evidence analysis library").
- **Deprecation:** deprecated rules remain in the digest history with `deprecated=true` and are never evaluated by the current algorithm id.
