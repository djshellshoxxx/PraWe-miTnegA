---
id: RG-P02-005
title: "Expected enforcement model"
phase: "02"
package: core
module_ids: [MOD-CORE-EXPECTED_ENFORCEMENT_MODEL]
status: DRAFT
depends_on: [RG-P02-004]
requirements: [FR-TEMP-008, FR-ANA-006, FR-ANA-010, FR-ANA-007, FR-ANA-012, FR-EXP-001, FR-EVD-002, FR-EVD-003]
interfaces_defined: [IF-ANA-EXPECT]
interfaces_used: [IF-CORE-CLOCK, IF-CORE-SERIAL, IF-CORE-CREDGRAPH, IF-ANA-BASELINE]
schemas_defined: [SCH-EXPECTATION]
schemathesis_touchpoints: []
---

# RG-P02-005 — Expected enforcement model

> Scope: *what should happen* — typed, sourced, profile-scoped rules keyed by (credential type, format, validation mode, event kind, policy profile); the resolution procedure that turns a key plus known facts into exactly one `ResolvedExpectation` (or an explicit "none/unresolved/conflict/unknown-precondition"); and the **verdict algebra** that compares a resolved rule with measured exposure bounds. Classifying the verdict into an `OutcomeClass` is RG-P02-009; shipping vendor baselines (Keycloak, generic) is RG-P08-008.

## 1. Module identifier and name

| Item | Value |
|---|---|
| Element | RG-P02-005 — Expected enforcement model |
| Package / modules | `rg_core.model.expectation`, `rg_core.expectation.{resolve,verdict,sources,coreset}` |
| Module id | `MOD-CORE-EXPECTED_ENFORCEMENT_MODEL` |
| Schemas | `SCH-EXPECTATION`: `EnforcementExpectation`, `MatchPattern`, rule forms, `Precondition`, `ExpectationSource`, `ExpectationSet`, `ResolvedExpectation`, `WindowFacts`, `VerdictResult` |
| Interface | new `IF-ANA-EXPECT` (`ExpectationResolver`, `evaluate`) |
| Shipped data | core rule sets `core.protocol@1`, `core.asvs5@1` (§12.5) |

## 2. Phase and requirement references

| Requirement | Realised by |
|---|---|
| FR-TEMP-008 rules keyed by (type, format, mode, event, profile) with strength, deadline/validity rule and cited source | §8, §12.1 |
| FR-ANA-006 profiles `protocol`, `vendor_doc`, `asvs_5_l1/l2/l3`, `nist_aal2/aal3`, `operator`; re-analysis under another profile creates a new record | §8.7 profile chains; resolution is a pure function of `(set, key, facts)` so a new profile ⇒ a new `ResolvedExpectation` |
| FR-ANA-010 baselines are data, replaceable by plugins | §12.6 baseline contract, `ExpectationSet.merge` |
| FR-ANA-007 unsupported capability ⇒ not-applicable, never `vulnerable` | `no_expectation{not_applicable}` + preconditions (SV-018, SV-044) |
| FR-ANA-012 explanation cites standard/vendor source | `ExpectationSource` + `source_string` |
| FR-EXP-001 secret-free spec; operator expectations are part of the spec digest | `origin="operator"` rules inside `ExperimentSpec` |
| FR-EVD-002/003 recomputation & derivation labelling | pure functions; `derivation="assumed"` on rules (premises, §8.1) |

Validity rules and risks realised: **TV-10** (capabilities discovered, absent capability ⇒ not applicable), **TV-11** (profile and skew bands recorded), **TV-22** (no mechanism claim from an unknown validation mode), **R-001** (an unexpired JWT remaining usable is never `vulnerable` on that fact alone), R-009 (baseline drift ⇒ versioned sets). Standards rules encoded: SV-010/011/012/013, SV-015/016/018/019/020/021, SV-024/025/030, SV-032/033/034, SV-046, SV-047, SV-052, SV-055.

## 3. Purpose and user/security value

"Token still works after logout" is a defect under one policy and the normal consequence of RFC 9068 under another (RF-10). The product's credibility rests on *never* conflating them. This module makes the premise explicit and machine-checkable: every expectation names its source (a standard section, a vendor document with a retrieval date, or an operator declaration), its strength (MUST/SHOULD/MAY/ID), its profile, and the facts under which it applies (e.g. "only if the AS supports access-token revocation", "only for the application's own session tokens"). Resolution is deterministic and conservative: an unknown validation mode (for mode-dependent rules), unknown preconditions, weak evidence or conflicting sources can never yield a MUST-level verdict that is eligible for `vulnerable`.

## 4. Explicit responsibilities

- **RESP-1** Define `EnforcementExpectation` (frozen field names of DATA-MODEL §7 plus `id`, `match`, `preconditions`, `version`) and the four rule forms `must_deny_by`, `may_allow_until`, `until_exp`, `no_expectation`.
- **RESP-2** Define typed `ExpectationSource` (`standard`, `vendor_doc`, `operator`) with evidence tags, and the canonical string forms (`standard:STD-003§2`, `vendor_doc:<url>@<date>`, `operator:<name>`).
- **RESP-3** Define `ExpectationSet` (a versioned collection) with `merge`, and the profile inheritance chains.
- **RESP-4** Define the resolution procedure: candidate selection, specificity, precedence between sources, conflict detection, precondition evaluation (three-valued), unknown/inferred validation-mode handling, evidence caps.
- **RESP-5** Define the verdict algebra `evaluate(resolved, window_facts, expiry_bound) → within | beyond_grace | violates | undetermined | not_evaluable` with the tolerance bands and worked numeric examples.
- **RESP-6** Ship the core `protocol` and `asvs_5` rule sets grounded in STANDARDS-REFERENCE §3/§4 with evidence tags.
- **RESP-7** Define how vendor baselines (RG-P08-008) and operator rules plug in (`IF-ANA-BASELINE` → `ExpectationSet`).

## 5. Out-of-scope responsibilities

| Excluded item | Owner |
|---|---|
| Mapping verdicts to `OutcomeClass`, gates, false-positive rules, independent-validation requirement | RG-P02-009 |
| Computing `X_lo/X_hi/W`, `ExposureWindow` | RG-P08-004 |
| Vendor/provider baselines (Keycloak, Entra, Okta, Auth0, generic) | RG-P08-008 (`IF-ANA-BASELINE`) |
| Discovering provider capabilities (`at_revocation`, …) | RG-P04-001 (`ProviderCapabilities`) |
| Inferring the validation mode from evidence | RG-P08-006 (this spec only defines how an *inferred* mode is treated) |
| Scenario syntax for operator expectations | RG-P07-001 |
| Config file parsing | RG-P03-003 |
| Report wording | RG-P08-011 |

## 6. Dependencies and prerequisites

RG-P02-004 (`RevocationKind` registry, `AnchorInterval`), RG-P02-003 (`ExpiryBound`, `CredentialType/Format`, `IssuerRole`), RG-P02-001 (`Int64` ns conventions), RG-P03-002 (`Model`, `Document`, `Slug`, `Label`, `ShortText`, `SortedSet`, `Sha256Digest`, `ExtKind`). DATA-MODEL §3 (`PolicyProfile`, `ValidationMode`), §7 (`EnforcementExpectation` summary). STANDARDS-REFERENCE §3–§4 as the content source. Pure Python + pydantic v2; no I/O, no clock.

## 7. External and internal interfaces

### 7.1 `ExpectationResolver` and `evaluate` — IF-ANA-EXPECT (`rg_core.expectation`)

All synchronous, pure, deterministic, thread-safe.

```python
class ExpectationSet(Document):                       # §8.6
    def resolve(self, key: ExpectationKey, ctx: ResolveContext, *, config: ExpectationConfig) -> ResolvedExpectation: ...   # §12.2
    def merge(self, *others: "ExpectationSet", set_id: str) -> "ExpectationSet": ...                                        # RGE-CONFIG-0503
    def digest(self) -> Sha256Digest: ...
    def rules_for(self, profile: PolicyProfile) -> tuple[EnforcementExpectation, ...]: ...

def profile_chain(profile: PolicyProfile) -> tuple[PolicyProfile, ...]: ...                       # §8.7
def evaluate(resolved: ResolvedExpectation, window: WindowFacts, expiry: ExpiryBound | None,
             *, config: ExpectationConfig) -> VerdictResult: ...                                 # §12.3; RGE-CONFIG-0507
def source_string(src: ExpectationSource) -> str: ...                                             # canonical text form
def parse_source(text: str) -> ExpectationSource: ...                                             # RGE-CONFIG-0504
def core_protocol_set() -> ExpectationSet: ...                                                    # shipped data §12.5
def core_asvs5_set() -> ExpectationSet: ...
```

Baseline plug-in (owned by RG-P08-008): `BaselineProvider.expectations(provider, target, profile) -> ExpectationSet` (INTERFACE-CONTRACTS §3). The engine composes the run's effective set as `core_protocol_set().merge(core_asvs5_set(), *baselines, operator_set, set_id="run.<exp>")` and stores its digest in the manifest.

Error codes (block 0500–0599 (RG-P03-005 §8.3)):

| Code | Name | Raised by |
|---|---|---|
| RGE-CONFIG-0501 | `expectation_invalid` (id/field grammar, strength/form coupling, ≤ limits) | model validators |
| RGE-CONFIG-0502 | `rule_form_invalid` (negative deadline; `grace > ambiguous`; `band` inconsistent; `until_exp` with a deadline) | `RuleForm` validators |
| RGE-CONFIG-0503 | `expectation_set_conflict` (duplicate rule id in `merge`; rule profile not allowed for the set `origin`) | `merge`, `ExpectationSet` validator |
| RGE-CONFIG-0504 | `source_invalid` (std id/URL/date/evidence-tag grammar; unparsable canonical string) | `ExpectationSource`, `parse_source` |
| RGE-CONFIG-0505 | `precondition_invalid` (unknown fact name; operator/value type mismatch) | `Precondition` validator |
| RGE-CONFIG-0506 | `resolve_context_invalid` (facts of the wrong type; `mode_source` missing) | `resolve` |
| RGE-CONFIG-0507 | `verdict_input_invalid` (`x_hi < x_lo`; `x_lo < 0`; mismatched clock/epoch of window and expiry) | `evaluate` |
| RGE-PLUGIN-0508 | `baseline_profile_not_allowed` (a baseline supplies `protocol`/`asvs_*`/`nist_*` rules) | `merge` |

## 8. Data structures and schemas

Conventions as RG-P02-001 §8 (frozen `Model`s; `Int64` ns; validator messages begin with the RGE code; `None` omitted). `ExpectationSet` is a `Document` (`SCHEMA_ID="expectation_set"`, `1.0`) with `Provenance` (`derivation="assumed"`: expectations are *premises*, not observations — reports label them so, FR-EVD-003).

### 8.1 `EnforcementExpectation`

| Field | Type | Constraint | Default | Description |
|---|---|---|---|---|
| `id` | Slug | `^exr\.[a-z0-9][a-z0-9._-]{0,62}$`, unique in a set | required | e.g. `exr.protocol.rt-revoked.deny` |
| `version` | Count | ≥ 1 | 1 | rule revision (R-009) |
| `profile` | `PolicyProfile` | | required | frozen name; the tier the rule lives in (§8.7) |
| `credential_type` / `format` / `validation_mode` / `event_kind` | via `match` (below) | | | frozen key components; each may be a wildcard |
| `match` | `MatchPattern` | | required | the key pattern |
| `rule` | `RuleForm` | discriminated on `form` | required | frozen name (§8.3) |
| `strength` | `ExpectationStrength` | `MUST, SHOULD, MAY, ID`; `no_expectation` ⇒ `ID` | required | frozen name |
| `source` | `ExpectationSource` | | required | frozen name (§8.4) |
| `preconditions` | `tuple[Precondition, ...]` | ≤ 8 | `()` | all must be non-false to apply (§8.5) |
| `notes` | ShortText | ≤ 256 | `""` | rationale shown in reports |
| `derivation` | `Literal["assumed"]` | | `assumed` | premise |

### 8.2 `MatchPattern`

| Field | Type | Constraint | Description |
|---|---|---|---|
| `credential_types` | `SortedSet[CredentialType]` | empty ⇒ wildcard | |
| `formats` | `SortedSet[CredentialFormat]` | empty ⇒ wildcard | |
| `validation_modes` | `SortedSet[ValidationMode]` | empty ⇒ wildcard; a rule that lists `unknown`/`opaque_unknown` explicitly matches only those | |
| `event_kinds` | `SortedSet[ExtKind[RevocationKind]]` | empty ⇒ wildcard | |

`specificity(match) = [credential_types≠∅] + [formats≠∅] + [validation_modes≠∅] + [event_kinds≠∅]` (0…4). A key `(t, f, m, e)` matches iff each non-empty component contains the key value.

### 8.3 `RuleForm` (discriminated on `form`)

| `form` | Fields | Semantics (`X` = unknown continued-access duration, DATA-MODEL §4) |
|---|---|---|
| `must_deny_by` | `deadline_ns: Int64 ≥ 0`, `band`, `grace_ns?`, `ambiguous_ns?` | the target MUST have stopped accepting the credential by `E + deadline`; tolerated up to `deadline + grace` |
| `may_allow_until` | `bound: Literal["duration","never"]`, `deadline_ns` (required iff `duration`), `band`, `grace_ns?`, `ambiguous_ns?` | acceptance is permitted up to `deadline`; beyond it the rule is breached to the degree the rule's `strength` states; `never` = no bound (verdict always `within`, e.g. `offline_access` refresh tokens after logout, SV-027) |
| `until_exp` | `band` (default `skew`), `grace_ns?`, `ambiguous_ns?` | acceptance is permitted until the credential's own expiry (DATA-MODEL's `may_allow_until(exp)`); acceptance after `exp + grace` breaches it |
| `no_expectation` | `reason: Label`, `not_applicable: bool = false` | the standard/source is silent (ID) or the tested capability does not exist (`not_applicable`, SV-018/SV-044) |

`band ∈ {skew, propagation, declared}` selects the default `(grace, ambiguous)` pair from configuration (§18): `skew` = (60 s, 300 s) (SV-010/SV-047, RFC 7519 "a few minutes"); `propagation` = (30 s, 120 s) (unquantified AS/RS propagation delay, RFC 7009 §2.1, SV-015); `declared` = (5 s, 30 s) (a window the vendor/operator has *stated*). Per-rule `grace_ns`/`ambiguous_ns` override the band. Validator (`RGE-CONFIG-0502`): `2 000 000 000 ≤ grace ≤ ambiguous`; `must_deny_by` and `may_allow_until(duration)` need `deadline_ns`; `until_exp` and `may_allow_until(never)` have none.
Note on DATA-MODEL `may_allow_until(Duration|exp|never)`: the JSON discriminator `until_exp` is the serialisation of `may_allow_until(exp)`; no frozen name changes.

### 8.4 `ExpectationSource` (discriminated on `type`)

| `type` | Fields | Canonical string |
|---|---|---|
| `standard` | `std_id` (`^STD-[0-9]{3}$`), `section` (ShortText, e.g. `§2`), `sv_ids` (`SortedSet[Label]`, e.g. `SV-019`), `evidence_tag` | `standard:STD-003§2` |
| `vendor_doc` | `provider` (Label), `url` (https, ≤ 512), `retrieved_on` (`YYYY-MM-DD`), `doc_version` (ShortText?), `evidence_tag` | `vendor_doc:<url>@<retrieved_on>` |
| `operator` | `declared_by` (Label), `declared_on` (`YYYY-MM-DD`), `note` (ShortText?) | `operator:<declared_by>` |

`EvidenceTag` (closed): `V`, `V-doc`, `V-src`, `V-lab` (**strong**: verified primary text/doc/source/lab observation) and `S`, `I`, `U`, `V*`, `3P` (**weak**: snippet/inference/unverified/secondary; in STANDARDS-REFERENCE and the provider docs `S` means *snippet-level*). `operator` sources carry no tag (the operator's policy is authoritative for the `operator` profile). **Evidence cap rule:** a rule whose source evidence tag is weak contributes the blocker `evidence_tag:<tag>` to any resolution that selects it (§12.2) — such a rule can describe a violation but can never justify `vulnerable`.

### 8.5 `Precondition` and the fact catalogue

`Precondition{fact, op, value}` with `op ∈ {eq, ne, gt, ge, lt, le, in}`; `value` is `bool | int | str | tuple[str,...]`. Evaluation is **three-valued** (`true | false | unknown`); a missing fact is `unknown`. Closed fact names (`RGE-CONFIG-0505` otherwise):

| Fact | Type | Provided by |
|---|---|---|
| `capability.at_revocation`, `capability.rt_revocation`, `capability.introspection`, `capability.backchannel_logout` | bool | `ProviderCapabilities` (RG-P04-001) / adapter probes (`unsupported_token_type`, SV-018) |
| `credential.directly_targeted` | bool | `resolve_affected(...).targeted` (RG-P02-004) |
| `credential.app_own_session` | bool | `Credential.issuer_role == application_own_session` (`unknown` if `issuer_role=unknown`) |
| `credential.lifetime_s` | int | `Credential.lifetime_s` |
| `credential.binding` | str | `Credential.binding` |
| `credential.scope.offline_access` | bool | `Credential.scope_granted` (unknown if the token response had no `scope`, SV-027) |
| `client.confidential` | bool | scenario/provider |
| `revocation.acknowledged_no_5xx` | bool | revoke step acknowledged and no 5xx (SV-006) |
| `revocation.same_client` | bool | revoking client = issuing client (SV-007) |
| `rotation.enabled` | bool | adapter capability/observation |
| `probe.category` | str ∈ `resource_access\|credential_oracle\|connection_liveness` | probe definition |

### 8.6 `ExpectationSet`

| Field | Type | Constraint | Description |
|---|---|---|---|
| `schema_version`, `derivation`, `produced_by` | | | provenance |
| `set_id` | Slug | e.g. `core.protocol`, `baseline.keycloak.admin-guide`, `run.exp_…` | |
| `version` | ShortText | | e.g. `1` or `26.8@2026-10-12` |
| `origin` | `Literal["core","baseline","operator","merged"]` | profile restrictions: `core` any; `baseline` only `vendor_doc`; `operator` only `operator`; `merged` any | |
| `rules` | `tuple[EnforcementExpectation, ...]` | ≤ `expectation.max_rules`; unique ids; canonical order by `id` | |
| `rules_digest` | `Sha256Digest` | computed over canonical rules | manifest reference |

### 8.7 Profile inheritance (`profile_chain`)

Rules are looked up tier by tier; the first tier that yields a candidate wins (profile-specific rules override inherited ones).

| Requested profile | Tiers searched in order |
|---|---|
| `protocol` | `protocol` |
| `vendor_doc` | `vendor_doc`, `protocol` |
| `asvs_5_l1` | `asvs_5_l1`, `protocol` |
| `asvs_5_l2` | `asvs_5_l2`, `asvs_5_l1`, `protocol` |
| `asvs_5_l3` | `asvs_5_l3`, `asvs_5_l2`, `asvs_5_l1`, `protocol` |
| `nist_aal2` | `nist_aal2`, `protocol` |
| `nist_aal3` | `nist_aal3`, `nist_aal2`, `protocol` |
| `operator` | `operator`, `vendor_doc`, `protocol` |

(ASVS levels are cumulative: an L1 requirement is authored once under `asvs_5_l1`; an L2-only requirement under `asvs_5_l2`.)

### 8.8 `ResolveContext`, `ResolvedExpectation`, `WindowFacts`, `VerdictResult`

- `ExpectationKey`: `credential_type`, `format`, `validation_mode`, `event_kind`, `profile`.
- `ResolveContext`: `mode_source: Literal["declared","inferred","unknown"]`, `facts: Mapping[FactName, bool|int|str]` (absent ⇒ unknown).
- `ResolvedExpectation`: `status ∈ {resolved, no_expectation, not_applicable, unresolved, conflict, unknown_precondition}`, `rule: EnforcementExpectation | None`, `tier: PolicyProfile | None`, `strength: ExpectationStrength | None`, `blockers: tuple[Label,...]` (reasons `vulnerable` is forbidden: `evidence_tag:S`, `mode_inferred`, `mode_unknown`), `conflicts: tuple[Slug,...]`, `trace: tuple[TraceStep,...]` (every tier/rule examined and why accepted/rejected), `bands: (deadline_ns, grace_ns, ambiguous_ns) | None`, `profile`, `set_digest`.
- `WindowFacts` (minimal projection of RG-P08-004's `ExposureWindow` — RG-P08-004 must be able to produce it): `x_lo_ns: Int64`, `x_hi_ns: Int64 | None`, `l_send_mono_ns`, `l_recv_mono_ns` (`Int64 | None`; `None` ⇔ no `L`), `anchor_upper_bound_sound: bool`, `clock_id`, `epoch`.
- `VerdictResult`: `verdict ∈ {within, beyond_grace, violates, undetermined, not_evaluable}`, `deadline_ns`, `grace_ns`, `ambiguous_ns`, `band`, `inputs` (the numbers compared), `explanation: ShortText` (generated, deterministic).

```json
{"id": "exr.protocol.rt-revoked.deny", "version": 1, "profile": "protocol",
 "match": {"credential_types": ["refresh_token"], "event_kinds": ["refresh_token_revoked"]},
 "rule": {"form": "must_deny_by", "deadline_ns": "0", "band": "propagation"},
 "strength": "MUST",
 "source": {"type": "standard", "std_id": "STD-003", "section": "§2", "sv_ids": ["SV-019"], "evidence_tag": "V"},
 "preconditions": [{"fact": "revocation.acknowledged_no_5xx", "op": "eq", "value": true},
                   {"fact": "revocation.same_client", "op": "eq", "value": true},
                   {"fact": "credential.directly_targeted", "op": "eq", "value": true}],
 "notes": "RT revocation MUST be supported (RFC 7009 §2); a revoked RT must fail with invalid_grant after the unquantified propagation delay", "derivation": "assumed"}
```

## 9. Inputs, outputs, and validation rules

| # | Rule | Code |
|---|---|---|
| VR-1 | `EnforcementExpectation` grammar: id pattern; `no_expectation` ⇒ `strength=ID`; every other form ⇒ `strength ∈ {MUST, SHOULD, MAY}` | RGE-CONFIG-0501 |
| VR-2 | `RuleForm`: `2 s ≤ grace ≤ ambiguous` (SV-047: no timing verdict from differences below ≈ 2 s); deadline presence per form (`until_exp` and `may_allow_until(never)` carry none); band in enum | RGE-CONFIG-0502 |
| VR-3 | `ExpectationSet`: unique ids, canonical order, `origin`↔profile restrictions, ≤ `max_rules`, digest consistency | RGE-CONFIG-0503 |
| VR-4 | `merge`: no duplicate ids across inputs; baselines may only supply `vendor_doc` rules | RGE-CONFIG-0503 / RGE-PLUGIN-0508 |
| VR-5 | `ExpectationSource` grammar (STD id, https URL ≤ 512, ISO date, evidence tag in the closed set; `vendor_doc`/`standard` require a tag) | RGE-CONFIG-0504 |
| VR-6 | `Precondition` fact name in the catalogue and `op`/`value` type-compatible | RGE-CONFIG-0505 |
| VR-7 | `resolve`: `mode_source` present; fact values of catalogue types | RGE-CONFIG-0506 |
| VR-8 | `evaluate`: `0 ≤ x_lo ≤ x_hi` when `x_hi` present; same `(clock_id, epoch)` for window and expiry bound | RGE-CONFIG-0507 |
| VR-9 | operator sources are accepted only in sets with `origin ∈ {operator, merged}` | RGE-CONFIG-0503 |

## 10. Detailed execution behavior

1. **Compose (engine, `VALIDATED`).** Build the run's `ExpectationSet` (core + ASVS + baselines selected by provider/target/profile + operator rules from the spec); validation errors are dry-run problems (FR-EXP-002). Persist the set (or its digest + baseline ids) in the manifest.
2. **Resolve (analysis, `ANALYZING`).** For each `(credential, target, event)` and each requested profile: assemble `ExpectationKey` (credential type/format from `Credential`; validation mode from `Target.validation_mode`, `mode_source=declared`, or the analysis-inferred mode with `mode_source=inferred`; event kind from the `RevocationEvent`) and `ResolveContext.facts` from capabilities, credential, event and probe data; call `resolve`.
3. **Evaluate.** Call `evaluate(resolved, window_facts, expiry_bound)`; hand `(resolved, verdict)` to RG-P02-009.
4. **Re-analysis.** Under a different profile or a newer baseline, steps 2–3 are re-run with the new inputs; stored results of the earlier run are never modified (FR-ANA-006).
5. **Time.** This module reads no clock; all quantities are `Int64` ns of the run clock.

## 11. State transitions and invariants

The module is stateless; sets are immutable values. Resolution status lattice (for documentation and tests): `resolved` / `no_expectation` / `not_applicable` are *decided*; `unresolved` (no candidate), `conflict`, `unknown_precondition` are *undecided* and force a non-`vulnerable` outcome downstream.

- **INV-1** `resolve` is a pure function of `(set digest, key, ctx, config)`; equal inputs ⇒ equal `ResolvedExpectation` including `trace`.
- **INV-2** The winning rule's tier is the first tier of `profile_chain(profile)` that has a candidate whose preconditions are not `false`.
- **INV-3** A rule never applies when any precondition evaluates `false`; when the chosen rule has an `unknown` precondition the status is `unknown_precondition`.
- **INV-4** If two or more candidates of the winning tier tie on `(len(preconditions), specificity, source authority rank)` and differ in `(form, deadline, band, strength)`, the status is `conflict` (listing the ids); identical duplicates collapse.
- **INV-5** `status=resolved` with `strength=MUST` and `blockers=()` is the *only* resolution from which RG-P02-009 may emit `vulnerable`.
- **INV-6** An explicitly listed unknown validation mode (`unknown`, `opaque_unknown`) matches only rules with an empty `validation_modes` set or that list that mode; mode-specific rules never match it.
- **INV-7** `mode_source ≠ declared` adds the blocker `mode_inferred`/`mode_unknown` to a resolution **only when the winning rule's `validation_modes` set is non-empty** (the rule's applicability depends on the mode); a mode-independent rule such as `exr.protocol.rt-revoked.deny` (empty set) is not weakened by an unknown mode. The blocker never changes which rule wins.
- **INV-8** `evaluate` returns exactly one of the five verdicts; the verdict regions for `must_deny_by`/`may_allow_until(duration)` are disjoint and exhaustive (§12.3).
- **INV-9** Increasing `x_lo` (others fixed) never moves the verdict from a worse region to a better one; decreasing `x_hi` never worsens it (monotonicity; property test).
- **INV-10** `anchor_upper_bound_sound=false` ⇒ `evaluate` never returns `within` for deadline rules.
- **INV-11** Every shipped core rule has a source with a non-empty `std_id` and a recorded evidence tag; a rule citing a weak tag always resolves with the `evidence_tag:<tag>` blocker (so it can never justify `vulnerable`).

## 12. Core algorithms and pseudocode

### 12.1 Key and facts

`key = (credential.type, credential.format, target.validation_mode, event.kind, profile)`; facts as in §8.5. Unknown/absent ⇒ three-valued `unknown`.

### 12.2 `resolve`

```
def resolve(set, key, ctx, cfg):
    trace = []
    for tier in profile_chain(key.profile):
        cands = []
        for r in set.rules_for(tier):
            if not matches(r.match, key):                          trace += (r.id, "no_match"); continue
            tv = [eval_pre(p, ctx.facts) for p in r.preconditions]  # three-valued
            if any(v is False for v in tv):                        trace += (r.id, "precondition_false"); continue
            cands.append((r, any(v is unknown for v in tv)))
        if cands: break
    else:
        return ResolvedExpectation(status=unresolved, trace=trace)         # no tier produced a candidate
    ranked = sort(cands, key = (-len(r.preconditions), -specificity(r.match), source_rank(r.source), r.id))   # source_rank: operator 0 < vendor_doc 1 < standard 2
    top = [c for c in ranked if same_rank_class(c, ranked[0])]          # equal (#preconditions, specificity, source rank)
    distinct = unique(top, key=(form, deadline, band, grace, ambiguous, strength))
    if len(distinct) > 1:    return ResolvedExpectation(status=conflict, conflicts=ids(top), trace=trace)
    r, unk = ranked[0]
    blockers = []
    if weak(r.source.evidence_tag): blockers += "evidence_tag:" + tag
    if r.match.validation_modes and ctx.mode_source == "inferred": blockers += "mode_inferred"
    if r.match.validation_modes and ctx.mode_source == "unknown":  blockers += "mode_unknown"
    if unk:                    return ResolvedExpectation(status=unknown_precondition, rule=r, tier=tier, blockers=blockers, ...)
    if r.rule.form == no_expectation: status = not_applicable if r.rule.not_applicable else no_expectation
    else:                      status = resolved
    return ResolvedExpectation(status, rule=r, tier=tier, strength=r.strength, blockers=blockers,
                               bands=(deadline, grace or band default, ambiguous or band default), trace=trace)
```

Source rank puts operator-authored rules before vendor documents before standards *within one tier*; because tiers are profile-scoped (§8.7) this ordering matters only for `merged` sets that place an operator and a vendor rule in the same tier (e.g. a vendor baseline pinned by an operator override in profile `vendor_doc`).

**Worked example R1 (profile switching).** Key `(access_token, jwt, jwt_local, account_disabled)`.
- profile `protocol`: chain `[protocol]`; rule `exr.protocol.jwt-until-exp` (access_token/jwt/jwt_local, any event) → `resolved`, `until_exp`, `MUST`, source `standard:STD-005§4.1.4` (V), blockers `()`.
- profile `asvs_5_l1`, facts `{credential.app_own_session: true}`: tier `asvs_5_l1` candidate `exr.asvs5.account-disable` (preconditions true) → `resolved`, `must_deny_by(0)`, `MUST`, source `standard:STD-029§V7.4.2` (V).
- profile `asvs_5_l1`, `credential.app_own_session` **false** (third-party-issued token): the ASVS rule is excluded (`precondition_false`); the tier yields no candidate; the next tier `protocol` yields the JWT rule → `until_exp` (the application is not responsible for third-party tokens, STANDARDS-REFERENCE STD-029).
- same, fact **absent**: ASVS rule is a candidate with an unknown precondition → status `unknown_precondition` (downstream: never `vulnerable`).
**Worked example R2 (unknown validation mode).** Key `(access_token, opaque, unknown, access_token_revoked, protocol)`, `capability.at_revocation=true`: `exr.protocol.opaque-introspect.at-revoked` requires `validation_modes={introspection}` → no match (INV-6); `exr.protocol.at-revoke.unsupported` has precondition `capability.at_revocation == false` → `precondition_false`; no candidates ⇒ `unresolved`. For `(refresh_token, opaque, unknown, refresh_token_revoked, protocol)` the rule `exr.protocol.rt-revoked.deny` has empty `validation_modes` (mode-independent) ⇒ `resolved`, MUST, and **no** mode blocker even with `mode_source=unknown` (RFC 7009 §2 requires RT revocation whatever the resource server does). Had the rule been mode-specific (e.g. `exr.protocol.introspect.at-revoked`, modes `{introspection}`) matched through an *inferred* mode, the blocker `mode_inferred` would be attached and a violation could not become `vulnerable`.
**Worked example R3 (conflict).** Operator set contains `exr.operator.cache-60` (`may_allow_until` 60 s, declared band, MAY) and `exr.operator.cache-300` (`may_allow_until` 300 s, MAY) with identical match patterns and no preconditions: same specificity, same rank, different deadlines ⇒ `conflict` listing both ids. Adding a precondition `credential.lifetime_s ≥ 600` to the second gives it more preconditions ⇒ it wins when the fact is true and is excluded when false (no conflict).

### 12.3 `evaluate` — the verdict algebra

Let `(d, g, a)` = `ResolvedExpectation.bands` (`deadline`, `grace`, `ambiguous`), `X_lo`, `X_hi` from `WindowFacts`.

**Deadline forms** (`must_deny_by`, `may_allow_until(duration)`):

```
if X_hi is not None and X_hi <= d + g and anchor_upper_bound_sound:   verdict = within
elif X_lo > d + a:                                                      verdict = violates
elif X_lo > d + g:                                                      verdict = beyond_grace
else:                                                                   verdict = undetermined      # X_lo <= d+g and (X_hi is None or X_hi > d+g or anchor unsound)
```

Exhaustive and disjoint: if `X_lo > d+g` the verdict is `beyond_grace` or `violates`; otherwise `X_lo ≤ d+g` and the verdict is `within` iff `X_hi ≤ d+g` (and sound), else `undetermined`. `may_allow_until(never)` ⇒ `within`.

**`until_exp`** with `ExpiryBound [e_lo, e_hi]` (local mono, RG-P02-003) and `L = [s_L, r_L]` (the last confirmed access attempt):

```
if expiry is None or not expiry.reliable:                  verdict = not_evaluable
elif L is None or r_L <= e_lo + g:                         verdict = within             # every acceptance happened no later than expiry + grace
elif s_L > e_hi + a:                                       verdict = violates           # accepted for certain more than `a` after expiry
elif s_L > e_hi + g:                                       verdict = beyond_grace
else:                                                      verdict = undetermined       # expiry/acceptance intervals straddle the grace boundary
```

`no_expectation` ⇒ `not_evaluable`.

**Worked example V1 — `must_deny_by(0)`, band propagation (g = 30 s, a = 120 s), X in seconds:**

| `(X_lo, X_hi)` | Verdict | Reason |
|---|---|---|
| (4.820, 6.060) | `within` | `6.060 ≤ 30` |
| (49.820, 52.050) | `beyond_grace` | `49.82 > 30` and `≤ 120` |
| (149.820, 151.060) | `violates` | `149.82 > 120` |
| (4.820, 101.050) | `undetermined` | `X_lo ≤ 30 < X_hi` |
| (294.850, None) | `violates` | censored but `X_lo > 120` |
| (4.820, None) | `undetermined` | censored, `X_lo ≤ 30` |
| (4.820, 6.060) with `anchor_upper_bound_sound=false` | `undetermined` | INV-10 |

**Worked example V2 — `may_allow_until(60 s)`, band declared (g = 5 s, a = 30 s):** (49.820, 52.050) → `within` (`52.05 ≤ 65`); (66.0, 70.0) → `beyond_grace` (`66 > 65`, `≤ 90`); (95.0, 96.0) → `violates` (`95 > 90`); (59.0, None) → `undetermined`.
**Worked example V3 — `until_exp`, `ExpiryBound = [1300.000, 1301.180] s`, band skew (g = 60 s, a = 300 s):**

| `L = (s_L, r_L)` | Verdict | Reason |
|---|---|---|
| (1290.000, 1290.040) | `within` | `1290.04 ≤ 1300 + 60` |
| (1359.900, 1360.100) | `undetermined` | `r_L > 1360.000` (not within) and `s_L ≤ 1301.18 + 60 = 1361.18` |
| (1360.000 − 0.040, 1360.000) | `within` | boundary `r_L = e_lo + g` exactly (inclusive) |
| (1400.000, 1400.040) | `beyond_grace` | `1400 > 1361.18` and `≤ 1601.18` |
| (1700.000, 1700.040) | `violates` | `1700 > 1301.18 + 300 = 1601.18` |
| `L = None` | `within` | no acceptance after the event |
| cookie credential (`reliable=false`) | `not_evaluable` | INV-6 of RG-P02-003 |

### 12.4 Specificity, precedence and conflict rules (summary)

1. Tier order by profile chain (§8.7). 2. Within a tier: more `preconditions` first (a rule that states the situation it applies to — e.g. `probe.category == connection_liveness` — beats a broader rule that does not), then higher key `specificity`, then source rank (operator < vendor_doc < standard — smaller wins), then lexicographic `id` for *determinism only*. 3. Candidates equal in the first three keys but different in rule content ⇒ `conflict` (never silently pick). 4. Strength is **not** a tie-breaker (a MUST and a MAY rule at the same specificity conflict: neither is silently preferred, because preferring MUST would manufacture vulnerabilities and preferring MAY would hide them).

### 12.5 Shipped core rule sets

`core.protocol@1` (profile `protocol`; source tags are those of STANDARDS-REFERENCE §2; bands in the third column):

| Rule id | Match (types / formats / modes / events) | Rule · strength · band | Source (tag) | Preconditions |
|---|---|---|---|---|
| `exr.protocol.rt-revoked.deny` | refresh_token / * / * / refresh_token_revoked | `must_deny_by(0)` · MUST · propagation | STD-003 §2; SV-019 (V) | `revocation.acknowledged_no_5xx`, `revocation.same_client`, `credential.directly_targeted` |
| `exr.protocol.rt-other.none` | refresh_token / * / * / * | `no_expectation(rt_other_events)` · ID | STD-008 §4.14.2 (V); SV-024/SV-030 | — |
| `exr.protocol.jwt-until-exp` | access_token / jwt / jwt_local / * | `until_exp` · MUST · skew | STD-005 §4.1.4, STD-007 §4; SV-010/SV-012 (V) | — |
| `exr.protocol.introspect.at-revoked` | access_token / * / introspection / access_token_revoked | `must_deny_by(0)` · MUST · propagation | STD-004 §4, STD-003 §2; SV-015 (V) | `capability.at_revocation == true`, `revocation.acknowledged_no_5xx` |
| `exr.protocol.at-revoke.unsupported` | access_token / * / * / access_token_revoked | `no_expectation(at_revocation_unsupported, not_applicable)` · ID | STD-003 §2; SV-018 (V) | `capability.at_revocation == false` |
| `exr.protocol.introspect.other` | access_token / * / introspection / * | `no_expectation(no_standard_for_event)` · ID | STD-004 (V); SV-015 | — |
| `exr.protocol.cached.until-exp` | access_token / * / introspection_cached / * | `until_exp` · MUST · skew | STD-004 §2.2/§4 "MUST NOT cache beyond exp"; SV-016 (V) | — |
| `exr.protocol.at-from-rt.none` | access_token / * / * / refresh_token_revoked | `no_expectation(cascade_optional)` · ID | STD-003 §2.1; SV-020/SV-021 (V) | — |
| `exr.protocol.idtoken.none` | id_token / jwt / * / * | `no_expectation(id_token_not_a_session)` · ID | STD-014 §2 NOTE; SV-052 (V) | — |
| `exr.protocol.bcl-session` | session_cookie / cookie / session_store / logout_back_channel | `must_deny_by(0)` · MUST · propagation | STD-017 §2.7; SV-025 (V) | `capability.backchannel_logout == true` |
| `exr.protocol.session.none` | session_cookie / * / * / * | `no_expectation(session_semantics_app_defined)` · ID | STD-029 intro; SV-032/033 are profile-level | — |
| `exr.protocol.reenable.none` | * / * / * / account_reenabled | `no_expectation(reactivation_policy_dependent)` · ID | SCN-14; KEYCLOAK.md §1.2 (V-lab) | — |
| `exr.protocol.liveness.none` | * / * / * / * | `no_expectation(open_connection_semantics_undefined)` · ID | STD-026 (S); SV-055 | `probe.category == connection_liveness` |

`core.asvs5@1` (profiles as stated; source `standard:STD-029` with evidence tag `V` via the OWASP Cornucopia mirror of ASVS 5.0.0, STANDARDS-REFERENCE STD-029; strengths are ASVS "shall" requirements ⇒ MUST *within the profile*):

| Rule id | Profile | Match (events) | Rule · strength · band | Preconditions |
|---|---|---|---|---|
| `exr.asvs5.session-termination` | `asvs_5_l1` | * / * / * / `{session_terminated, sessions_terminated_all, logout_rp_initiated, logout_back_channel}` | `must_deny_by(0)` · MUST · propagation (V7.4.1; SV-032) | `credential.app_own_session == true` |
| `exr.asvs5.account-disable` | `asvs_5_l1` | * / * / * / `{account_disabled, account_deleted, service_identity_disabled}` | `must_deny_by(0)` · MUST · propagation (V7.4.2; SV-033) | `credential.app_own_session == true` |
| `exr.asvs5.password-change` | `asvs_5_l2` | * / * / * / `{password_changed, password_reset, credential_reset}` | `no_expectation(option_only)` · ID (V7.4.3; SV-034) | `credential.app_own_session == true` |

NIST profiles ship no revocation-event rules (the AAL reauthentication limits of SV-058 are session-lifetime policies tested by scenarios, evidence tag S, RQ-3); their tiers are empty and inherit `protocol`. Vendor rules (Keycloak "introspection reflects disable immediately", Auth0 "JWT access tokens cannot be revoked", Entra CAE windows) belong to RG-P08-008 baselines with `vendor_doc` sources.

### 12.6 Baseline and operator plug-in

- **Baseline contract.** `BaselineProvider.expectations(provider, target, profile)` returns an `ExpectationSet` with `origin="baseline"` whose rules are only `profile="vendor_doc"` and carry `vendor_doc` sources with `retrieved_on` and a strong `evidence_tag` (V-doc/V-lab) when the provider doc was read; rules based on snippets carry weak tags and therefore blockers. A baseline for Keycloak would say, for `(access_token, *, introspection, account_disabled)`, `must_deny_by(0)` with band `declared` and source `vendor_doc:<KEYCLOAK.md anchor>` (V-lab); a generic baseline supplies no rules (unresolved ⇒ `needs_verification`, never `vulnerable`).
- **Operator rules** appear in the experiment spec as `ExpectationSet(origin="operator")` with `operator` sources (`declared_by`, `declared_on`); they live in profile `operator` and are audited in the report as `assumed` premises.
- **Merging** (`merge`): union by rule id; duplicate id ⇒ `RGE-CONFIG-0503`; a baseline carrying a non-`vendor_doc` rule ⇒ `RGE-PLUGIN-0508`; result `origin="merged"`, `rules_digest` recomputed.

## 13. Internal functions, methods, or service operations

```python
def matches(m: MatchPattern, key: ExpectationKey) -> bool: ...
def specificity(m: MatchPattern) -> int: ...
def eval_pre(p: Precondition, facts: Mapping[str, Any]) -> bool | None: ...             # True/False/None(unknown)
def source_rank(s: ExpectationSource) -> int: ...                                         # operator 0, vendor_doc 1, standard 2
def is_weak(tag: EvidenceTag) -> bool: ...
def band_defaults(band: Band, cfg: ExpectationConfig) -> tuple[int, int]: ...             # (grace_ns, ambiguous_ns)
def resolved_bands(rule: EnforcementExpectation, cfg: ExpectationConfig) -> tuple[int, int, int]: ...   # (deadline, grace, ambiguous)
def _verdict_deadline(d: int, g: int, a: int, w: WindowFacts) -> Verdict: ...
def _verdict_until_exp(g: int, a: int, w: WindowFacts, e: ExpiryBound) -> Verdict: ...
def _rules_by_tier(rules: Sequence[EnforcementExpectation]) -> Mapping[PolicyProfile, tuple[EnforcementExpectation, ...]]: ...   # built once per set
```

## 14. Error handling and failure recovery

| Failure | Detection | Handling | Recovery | Code |
|---|---|---|---|---|
| Malformed rule/set in baseline or operator input | model validators on load | reject whole set (no partial load); dry-run lists all problems | fix input | 0501–0505 |
| Duplicate rule ids on merge | `merge` | reject merge | rename | 0503 |
| Baseline supplies non-vendor profile | `merge` | reject; plugin flagged | fix plugin | RGE-PLUGIN-0508 |
| Facts of wrong type | `resolve` | raise; analysis step fails with `INTERNAL`-grade bug report | fix caller | 0506 |
| Inconsistent window facts (`x_hi < x_lo`) | `evaluate` | raise | fix RG-P08-004 | 0507 |
| No rule / conflict / unknown precondition | resolution status | *not an error*: status recorded; downstream caps outcome | supply declaration/baseline | — |

## 15. Security requirements and trust boundaries

- **Untrusted inputs:** operator rules and third-party baselines are data from files/plugins (TM-22): schema-validated, bounded (`max_rules`, text lengths), never executed (no expression evaluation — preconditions are closed-vocabulary triples, TM-14).
- **Anti-false-positive controls (R-001, TV-10, TV-23(c)):** the evidence cap, mode-source blockers, three-valued preconditions and conflict-never-resolved-by-strength rules make `vulnerable` unreachable from weak, unknown or contradictory premises.
- **Operator-rule abuse:** an operator can declare any expectation; the report shows operator premises as `assumed` with the declarer and date (FR-EVD-003), and operator-profile results are never merged into the `protocol` result.
- **Supply chain (TM-23/TM-22):** baselines are plugins; their `rules_digest` and `baseline_id` enter the manifest so a changed baseline is visible in history comparisons (FR-HIST).
- **Secrets:** none.

## 16. Concurrency, asynchronous behavior, and resource ownership

Immutable sets; `resolve`/`evaluate` pure ⇒ safe from any thread/task. `ExpectationSet` builds a per-tier index once at construction (O(R)); `resolve` is O(rules in the tiers examined). Memory ≤ `expectation.max_rules` (default 5000) × ≈ 1 KiB. No I/O, locks or cancellation points.

## 17. Performance and resource requirements

Proposals, validated by `BM-EXP-1`: `resolve` over the shipped sets (≈ 16 rules) ≤ 50 µs; over 5 000 rules ≤ 5 ms; `evaluate` ≤ 10 µs; `merge` of 5 000 rules ≤ 200 ms. Rationale: resolution runs once per (credential × profile) at analysis time.

## 18. Configuration and defaults

| Field | Type | Default | Range | Env var | Notes |
|---|---|---|---|---|---|
| `expectation.skew_tolerance_ns` | int | 60 000 000 000 | 0 … 3 600 000 000 000 | `RG_EXPECTATION_SKEW_TOLERANCE_NS` | band `skew` grace (SV-010/SV-047); **printed in every report** (TV-11) |
| `expectation.skew_ambiguous_ns` | int | 300 000 000 000 | ≥ tolerance | `RG_EXPECTATION_SKEW_AMBIGUOUS_NS` | band `skew` ambiguous |
| `expectation.propagation_grace_ns` | int | 30 000 000 000 | 0 … 3 600 000 000 000 | `RG_EXPECTATION_PROPAGATION_GRACE_NS` | band `propagation` grace (SV-015 default 30 s) |
| `expectation.propagation_ambiguous_ns` | int | 120 000 000 000 | ≥ grace | `RG_EXPECTATION_PROPAGATION_AMBIGUOUS_NS` | band `propagation` ambiguous |
| `expectation.declared_grace_ns` | int | 5 000 000 000 | 0 … 600 000 000 000 | `RG_EXPECTATION_DECLARED_GRACE_NS` | band `declared` grace |
| `expectation.declared_ambiguous_ns` | int | 30 000 000 000 | ≥ grace | `RG_EXPECTATION_DECLARED_AMBIGUOUS_NS` | band `declared` ambiguous |
| `expectation.max_rules` | int | 5000 | 16 … 100 000 | `RG_EXPECTATION_MAX_RULES` | set size bound |

Constraints: every `*_grace_ns` ≥ 2 000 000 000 and every `*_ambiguous_ns` ≥ its grace (SV-047: no timing verdict from differences below ≈ 2 s resolution) — violations `RGE-CONFIG-0502` at load. The six band values plus `max_rules` form the frozen `ExpectationConfig` model passed to `resolve`/`evaluate`. Precedence: defaults < file < env < CLI < per-rule overrides.

## 19. Logging, observability, and evidence requirements

Events: `expectation.resolved` {`key`, `profile`, `status`, `rule_id`, `tier`, `strength`, `blockers`, `conflicts`}; `expectation.evaluated` {`rule_id`, `verdict`, `x_lo_ns`, `x_hi_ns`, `d`, `g`, `a`}. Evidence/derived records: `ResolvedExpectation` and `VerdictResult` are stored as derived records (`derivation=calculated`, algorithm `rg.expectation.resolve@1` / `rg.expectation.evaluate@1`) referencing the set digest; the run manifest records the effective set digest, the baseline ids/versions, and the three band pairs in force. Reports print the sources (`source_string`) and the bands. No secrets or redaction needs.

## 20. Platform compatibility

Pure Python, integer arithmetic. Dates are ISO `YYYY-MM-DD` strings validated by regex (no locale parsing). Sorting is byte-wise ASCII on ids. No platform behaviour.

## 21. Edge cases and invalid inputs

| # | Case | Expected behaviour |
|---|---|---|
| E-1 | Set with duplicate rule ids | `RGE-CONFIG-0503` |
| E-2 | `must_deny_by` with negative deadline | `RGE-CONFIG-0502` |
| E-3 | `grace_ns > ambiguous_ns`, or `grace_ns` below 2 s | `RGE-CONFIG-0502` |
| E-4 | Precondition fact `capability.foo` | `RGE-CONFIG-0505` |
| E-5 | `vendor_doc` source with `http://` URL | `RGE-CONFIG-0504` |
| E-6 | Baseline set containing an `asvs_5_l1` rule | `RGE-PLUGIN-0508` |
| E-7 | Key with `validation_mode=unknown`, only mode-specific rules exist | `status=unresolved` |
| E-8 | Two operator rules, same specificity, different deadlines | `status=conflict` |
| E-9 | Chosen rule has unknown precondition | `status=unknown_precondition` |
| E-10 | Rule with weak evidence tag `S` selected | `blockers=("evidence_tag:S",)`, status still `resolved` |
| E-11 | `evaluate` with `x_hi < x_lo` | `RGE-CONFIG-0507` |
| E-12 | `evaluate` for `until_exp` with `ExpiryBound.reliable=false` | `not_evaluable` |
| E-13 | `X_lo = d + g` exactly | not `beyond_grace` (strict `>`); `undetermined` unless `within` |
| E-14 | `X_hi = d + g` exactly with sound anchor | `within` (inclusive) |
| E-15 | `may_allow_until(never)` | `within` always |
| E-16 | Profile `asvs_5_l3` with an L1-only rule in the set | rule reachable through chain `l3 → l2 → l1` |
| E-17 | Two profiles requested for one window | two independent resolutions; no shared state |

## 22. Unit and integration test requirements

| ID | Condition | Expected observation |
|---|---|---|
| TST-RG-P02-005-01 | Model validators E-1…E-6 and source grammar table | codes as stated |
| TST-RG-P02-005-02 | JSON round-trip and canonical digest stability of `core.protocol@1` and `core.asvs5@1`; permutation of rule order | identical `rules_digest`; equality after round-trip |
| TST-RG-P02-005-03 | Worked example R1 (four cases) | statuses/rules/tiers/blockers as stated |
| TST-RG-P02-005-04 | Worked example R2 (unknown mode: opaque AT unresolved; RT resolved with no mode blocker; mode-specific rule via inferred mode carries `mode_inferred`) | as stated |
| TST-RG-P02-005-05 | Worked example R3 conflict, then precondition-disambiguated variant; strength not a tie-breaker (MUST vs MAY at equal rank) | `conflict` / winner; MUST-vs-MAY ⇒ `conflict` |
| TST-RG-P02-005-06 | Profile chains: all eight profiles; L3 sees L1/L2 rules; `operator` sees vendor_doc and protocol | tiers searched per §8.7 (assert from `trace`) |
| TST-RG-P02-005-07 | Verdict tables V1, V2, V3 (every row) | verdicts as tabulated |
| TST-RG-P02-005-08 | Boundary/mutation tests: for each of `d+g`, `d+a`, `e_lo+g`, `e_hi+g`, `e_hi+a` test values `−1, 0, +1 ns` around the boundary | region changes exactly at the documented inclusive/exclusive side (E-13, E-14) |
| TST-RG-P02-005-09 | Property (Hypothesis): random `(d,g,a,X_lo,X_hi)` | exactly one verdict (INV-8); monotonicity INV-9; unsound anchor never `within` (INV-10) |
| TST-RG-P02-005-10 | Three-valued preconditions truth table (`eq/ne/gt/ge/lt/le/in` × true/false/missing) | as per three-valued logic |
| TST-RG-P02-005-11 | `merge`: duplicate ids, baseline with non-vendor profile, operator source in a core set | `RGE-CONFIG-0503` / `RGE-PLUGIN-0508` |
| TST-RG-P02-005-12 | Evidence-cap: rule with tag `S` vs `V` selected for the same key | blocker present only for `S` |
| TST-RG-P02-005-13 | Source string round-trip (`standard:STD-003§2`, `vendor_doc:https://…@2026-10-12`, `operator:alice`) and invalid strings | equality; `RGE-CONFIG-0504` |
| TST-RG-P02-005-14 | Core-set audit: every rule has std id + tag; every weak-tag rule resolves with its evidence blocker; REQ items (1) RT revocation, (2) JWT `exp`, (3) introspection of revoked tokens and (5) back-channel logout of STANDARDS-REFERENCE §3 "Reading the table" each map to exactly one shipped MUST rule; items (4) public-client RT rotation and (6) paused-SSF-stream are not event-kind expectations and are listed as out-of-model (scenario checks RG-P07-002/RG-P04-011) | audit passes (INV-11) |
| TST-RG-P02-005-15 | Config bounds: grace < 2 s rejected; bands printed in the manifest fixture | `RGE-CONFIG-0502`; manifest contains the six band values |
| TST-RG-P02-005-16 | Integration (lab virtual time, RG-P09-003 profiles): resolve + evaluate for the five shipped lab enforcement profiles with known ground truth | verdict equals the profile's ground-truth region |

## 23. Mocking and test fixtures

No doubles needed beyond data. Fixtures: `fixtures/expectation/core_protocol_v1.json`, `core_asvs5_v1.json`, `operator_conflict.json`, `baseline_bad_profile.json`, `verdict_tables.json` (V1–V3), `source_strings.json`, `window_facts_property_seeds.json`. Hypothesis strategies in `rg_core.testing.strategies.expectation`. Lab ground truth: the mock services' declared enforcement profile (RG-P09-003) supplies the expected verdict region for TST-16.

## 24. Objective acceptance criteria

- **AC-RG-P02-005-01** All malformed rules, sets, sources and preconditions are rejected with the specified codes and no partial set is ever loaded (verified by TST-RG-P02-005-01, TST-RG-P02-005-11, TST-RG-P02-005-13).
- **AC-RG-P02-005-02** `resolve` is deterministic, honours profile chains, specificity, source rank, preconditions (three-valued) and returns `unresolved`/`conflict`/`unknown_precondition` exactly as specified, including for unknown and inferred validation modes (verified by TST-RG-P02-005-03, TST-RG-P02-005-04, TST-RG-P02-005-05, TST-RG-P02-005-06, TST-RG-P02-005-10).
- **AC-RG-P02-005-03** `evaluate` returns exactly one verdict per input, matches every row of the V1–V3 tables, is monotone in the bounds, flips exactly at the documented boundaries, and never returns `within` for an unsound anchor (verified by TST-RG-P02-005-07, TST-RG-P02-005-08, TST-RG-P02-005-09).
- **AC-RG-P02-005-04** Weak-evidence, mode-dependent (unknown/inferred mode), conflicting or unknown-precondition resolutions always carry blockers/status that forbid a `vulnerable` outcome downstream (verified by TST-RG-P02-005-04, TST-RG-P02-005-05, TST-RG-P02-005-12).
- **AC-RG-P02-005-05** The shipped core sets carry a standard section and evidence tag per rule and cover the event-kind REQ items (1), (2), (3), (5) of STANDARDS-REFERENCE §3 with exactly one MUST rule each, listing items (4) and (6) as out-of-model (verified by TST-RG-P02-005-14, TST-RG-P02-005-02).
- **AC-RG-P02-005-06** The six tolerance values in force are configurable within validated ranges and recorded in the manifest (verified by TST-RG-P02-005-15).
- **AC-RG-P02-005-07** In the virtual-time lab the verdict region for each shipped enforcement profile equals the profile's ground truth (verified by TST-RG-P02-005-16).

## 25. Research sources and engineering rationale

Sources: STANDARDS-REFERENCE §3 (enforcement taxonomy; REQ/REC/MAY/ID legend), §4 (SV-010 … SV-016, SV-018 … SV-021, SV-024, SV-025, SV-030, SV-032 … SV-034, SV-046, SV-047, SV-052, SV-055), STD-029 (ASVS 5.0.0 V7.4.1/V7.4.2/V7.4.3, verbatim via Cornucopia mirror, tag V), STD-003/004/005/007/017 (V), STD-026 (S); KEYCLOAK.md §1.7 (validation-mode table, V-lab); ADR-0010; TECHNICAL-FEASIBILITY R-001, R-009; PRD FR-TEMP-008, FR-ANA-006/010; charter §2 (class rules).

- **DEC-1 Rules as data with closed-vocabulary preconditions**, not code or an expression language. Rejected: Python/CEL expressions (injection surface, TM-14; non-deterministic review), hard-coded tables in the classifier (cannot be replaced by baseline plug-ins, FR-ANA-010). Verification: TST-02/10/14.
- **DEC-2 Tiered profile chains instead of flat precedence numbers.** A profile-specific rule must override an inherited one regardless of specificity; flat scoring would let a very specific protocol rule beat a general ASVS rule. Rejected: single global priority field. Verification: TST-03/06.
- **DEC-3 Strength is not a conflict tie-breaker** (§12.4). Verification: TST-05.
- **DEC-4 Three bands (skew, propagation, declared)** rather than one tolerance: the three families have different provenance (RFC 7519 leeway; unquantified propagation delay; stated windows) and SV-010/SV-015 give different defaults. All values are configurable and printed (TV-11). Verification: TST-07/15.
- **DEC-5 Verdict regions defined on the *entailed bounds* `[X_lo, X_hi]`** only (no point estimate), so the verdict is exactly as strong as the measurement (NG-12, FR-TEMP-010). `undetermined` is a first-class outcome rather than a coin-flip. Verification: TST-07/08/09.
- **DEC-6 `until_exp` evaluated in local-mono time against the credential's `ExpiryBound`** rather than as an X-deadline: expiry is an absolute instant, not an offset from `E`. Rejected: converting `exp` into a duration from `A_ack` (would hide the expiry-interval uncertainty). Verification: TST-07 (V3).
- **DEC-7 Evidence cap through blockers**, not by downgrading `strength`: strength is a property of the *source's wording*; evidence quality is a property of *our knowledge of the source* (RESEARCH-REGISTER evidence rule). Keeping them separate lets reports say both. Verification: TST-12.
- **DEC-8 Expectations are `derivation=assumed` premises.** Verification: schema test in TST-02.

## 26. Remaining uncertainties or assumptions

| # | Assumption | Evidence tag | Falsifying test |
|---|---|---|---|
| A-1 | Default bands (60/300 s skew; 30/120 s propagation; 5/30 s declared) are reasonable policy defaults; they are *not* standard numbers (SV-047) | policy proposal | lab sweeps in TST-16 and RG-P12 regression suite; users may override |
| A-2 | ASVS 5.0.0 V7.4.1/V7.4.2 apply only to the application's own sessions/tokens (STD-029 intro, secondary text S) | V (requirement text via Cornucopia mirror) / S (scope intro) | review against the ASVS source by RG-P08-008/P15 audit |
| A-3 | RFC 7009 §2.1 propagation delay is unquantified, so a grace is needed for `refresh_token_revoked` | V (STD-003) | none (policy) — the value is configurable |
| A-4 | RFC 9700 §4.14.2 rules (MAY revoke RTs on password change) are as quoted in STANDARDS-REFERENCE | V to §4.14 | spec re-read in RG-P04-004 |
| A-5 | `STD-014` §2 NOTE (ID-token `exp` unrelated to session lifetime) read only to §3.3.2 | V partial | OIDC Core re-read (RQ-2) |
| A-6 | WebSocket rule evidence STD-026 is snippet-level (S) | S | RFC 6455 full read (RQ-2) — mitigated: rule is `no_expectation` |
| A-7 | `ExposureWindow` (RG-P08-004) can supply `WindowFacts` exactly (`x_lo`, `x_hi`, `L` send/recv times, anchor soundness) | frozen DATA-MODEL §4 | RG-P08-004 contract test (CCR if a field is missing) |
| A-8 | Operator-profile semantics (operator > vendor_doc > protocol) match user expectation | design | usability review WF-02/WF-09 |

## 27. Maintainability, portability, and future extension requirements

- **Versioning:** `expectation_set` `1.0`; rule `version` increments on any change of form/strength/source; set `version` and `rules_digest` enter the manifest; baselines carry provider version + retrieval date (R-009). Adding a rule form (e.g. `must_deny_after_event_count`) is a minor additive discriminator value and requires an `evaluate` branch plus new tests; adding a fact name is additive.
- **Extension points:** baselines (`IF-ANA-BASELINE`), operator sets, new profiles (enum change in DATA-MODEL + a chain entry), new bands via configuration.
- **Reuse:** the resolver/verdict algebra is independent of RevocationGap's probes and can serve any "declared vs observed enforcement" comparison (master-prompt reusable component: confidence/evidence analysis library).
- **Deprecation:** retired rules are kept with `version` bumped and `notes` stating replacement for one minor release; history comparison (RG-P08-009) joins on rule id + version.
