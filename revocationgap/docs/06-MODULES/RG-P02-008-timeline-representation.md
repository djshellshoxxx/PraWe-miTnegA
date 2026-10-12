---
id: RG-P02-008
title: "Timeline representation"
phase: "02"
package: core
module_ids: [MOD-CORE-TIMELINE_REPRESENTATION]
status: DRAFT
depends_on: [RG-P02-006]
requirements: [FR-EVD-008, FR-TEMP-007, FR-TEMP-003, FR-EVD-004, FR-EVD-003, FR-RPT-003, FR-RPT-002, FR-GUI-002, NFR-REL-001, NFR-PERF-007, NFR-PERF-006, FR-EXP-008]
interfaces_defined: [IF-CORE-TIMELINE]
interfaces_used: [IF-CORE-CLOCK, IF-CORE-SERIAL, IF-CORE-STORE, IF-CORE-EVENTORDER, IF-CORE-OBSERVATION]
schemas_defined: [SCH-TIMELINE]
schemathesis_touchpoints: []
---

# RG-P02-008 — Timeline representation

> Scope: the gap-free, totally ordered, tamper-evident per-experiment **timeline** (`TimelineEntry`, `Timeline`): entry kinds and typed payloads, ordering and out-of-order rules, the single-writer protocol (including atomic co-commit with state transitions), queries, export formats and the pure projection used by reports and the live GUI. Evidence blobs are RG-P08-001; the derived markers `L`/`D`/bounds are RG-P08-004 (the projection only overlays them); persistence of the rows is RG-P03-008.

## 1. Module identifier and name

| Item | Value |
|---|---|
| Element | RG-P02-008 — Timeline representation |
| Package / modules | `rg_core.model.timeline`, `rg_core.timeline` (`writer`, `index`, `verify`, `project`, `export`) |
| Module id | `MOD-CORE-TIMELINE_REPRESENTATION` |
| Schemas | `SCH-TIMELINE`: `TimelineEntry`, payload models per kind, `Timeline`, `TimelineQuery`, `TimelineVerification`, `TimelineView` |
| Interface | new `IF-CORE-TIMELINE` (`TimelineWriter`, `TimelineIndex`, `verify_timeline`, `project_timeline`, JSONL/CSV export) |

## 2. Phase and requirement references

| Requirement | Realised by |
|---|---|
| FR-EVD-008 gap-free ordered timeline of state transitions, revocation anchors, observations, operator actions, clock anomalies, notes; queryable by time range and credential; exportable | §8, §12.3 query, §12.5 export |
| FR-TEMP-007 total order `(monotonic instant, sequence number)`; duplicated/delayed/out-of-order events recorded, not discarded | §11 ordering invariants, `external_event` kind |
| FR-TEMP-003 `clock_anomaly` timeline entry on wall step | payload `ClockAnomaly` (RG-P02-001 §8.7), §10 |
| FR-EVD-004 integrity: detect modified, missing or reordered records | per-entry hash chain, `verify_timeline` (the evidence-item chain itself is RG-P08-001) |
| FR-EVD-003 derivation labelling | `derivation` per entry |
| FR-RPT-002 CSV timelines (v1.x), FR-RPT-003 timeline visualisation, FR-GUI-002 live timeline via SSE | §12.5 CSV export, §12.4 projection, §10 live feed |
| NFR-REL-001 durable before the engine acts, NFR-PERF-007 size, NFR-PERF-006 memory | §10.2 atomic co-commit, §17 budgets |
| FR-EXP-008 recovery from durable records | §12.6 recovery of writer state (`resume_state`) |

Validity rules and threats realised: TV-08 (monotonic ordering), **TM-26** (evidence tampering/repudiation — tamper-evident chain), TM-28 (clock anomalies visible), TM-34 (bounded growth), TM-11/TM-12 (untrusted strings: bounded, escaped by renderers), SV-004 (report `t_first_reject`, polling interval, attempt count). Workflows: WF-01 step 6 (live timeline), WF-10 (review/export), WF-11 (recovery).

## 3. Purpose and user/security value

The timeline is the single narrative of a run: *what happened, in what order, with which clock*. Analysis does not depend on it (it consumes observations and events directly) — the timeline exists so that a human or an auditor can reconstruct the run, so that recovery can find the last durable fact, and so that tampering or loss is **detectable**: a missing seq, a reordered entry or an edited payload breaks the hash chain. It also makes clock trouble visible *in context* (a `clock_anomaly` row between two probes), which is what lets an assessor judge a surprising exposure interval.

## 4. Explicit responsibilities

- **RESP-1** Define `TimelineEntry` (frozen field names of DATA-MODEL §7 plus additive fields) and the typed payload for every kind.
- **RESP-2** Define the ordering contract: gap-free `seq`, total order `(mono_ns, seq)`, the `occurred_at`/`out_of_order` rule, epoch changes, and which kinds may follow the final state.
- **RESP-3** Define the per-entry hash chain and `verify_timeline`.
- **RESP-4** Define the single-writer protocol `TimelineWriter` (stamping inside the serialisation point; atomic co-commit with a state transition; bounded size).
- **RESP-5** Define `TimelineQuery` semantics (by seq, effective time, credential, target, kind) and `TimelineIndex`.
- **RESP-6** Define the pure `project_timeline` view model (lanes, markers) consumed by RG-P08-011 and the GUI.
- **RESP-7** Define canonical JSONL and CSV exports.
- **RESP-8** Define writer-state recovery from the last durable entry.

## 5. Out-of-scope responsibilities

| Excluded item | Owner |
|---|---|
| SQLite schema, transactions, durability policy (`append_timeline`) | RG-P03-008 (`IF-CORE-STORE`) |
| Evidence items and the evidence hash chain / manifest root digest | RG-P08-001 |
| Exposure windows, `L`/`D` markers, uncertainty (overlaid by the projection) | RG-P08-004 |
| SVG/HTML/CSV rendering, wording | RG-P08-011 |
| SSE transport and GUI widgets | RG-P10-004/-005 |
| Live CLI text timeline formatting | RG-P10-003 |
| Event bus fan-out of timeline events | RG-P03-007 |
| State-transition semantics | RG-P02-007 |

## 6. Dependencies and prerequisites

RG-P02-001 (`TimeInstant`, `RemoteInstant`, `ClockAnomaly`), RG-P02-004 (`RevocationEvent` versions, `ArrivalFlag`), RG-P02-006 (`Observation`, `ObservationView`, outcomes, control roles), RG-P02-003 (`CredentialStateRecord`), RG-P02-007 (`Transition`) — payloads reference, never redefine them. RG-P03-002 (`Model`, `Document`, `Provenance`, `canonical_json`, `chain_digest`, typed ids `TlnId`…), `IdFactory`, `Clock`. DATA-MODEL §7 (`TimelineEntry`), §9.3. Pure Python + pydantic v2; no I/O (the writer calls the injected `TimelineSink`).

## 7. External and internal interfaces

### 7.1 `TimelineWriter` — IF-CORE-TIMELINE (`rg_core.timeline`)

```python
class TimelineSink(Protocol):                                  # implemented by ExperimentStore adapter (RG-P03-008)
    async def append(self, exp_id: str, entry: TimelineEntry) -> None: ...          # durable before return (IF-CORE-STORE.append_timeline)

class TimelineWriter:                                          # exactly one per experiment; loop-bound; NOT thread-safe
    def __init__(self, experiment_id: str, clock: Clock, ids: IdFactory, sink: TimelineSink, *,
                 resume: WriterState | None = None, max_entries: int = 500_000) -> None: ...
    async def append(self, kind: TimelineKind, payload: Model, *, ref: TimelineRef | None = None,
                     credential_ref: str | None = None, target_ref: str | None = None,
                     occurred_at: TimeInstant | None = None, occurred_at_claimed: RemoteInstant | None = None,
                     derivation: Derivation = Derivation.observed, summary: str | None = None) -> TimelineEntry: ...
    def exclusive(self) -> "AsyncContextManager[ExclusiveWriter]": ...            # §10.2 co-commit with a transition
    @property
    def state(self) -> WriterState: ...                                           # (last_seq, last_at, last_digest, epoch, closed)
    def close(self) -> None: ...                                                  # after the final transition; only notes may follow via reopen_for_notes()

class ExclusiveWriter:
    def build(self, kind: TimelineKind, payload: Model, **kw: Any) -> TimelineEntry: ...    # assigns seq/at/digest, does not persist
    def commit_built(self, entry: TimelineEntry) -> None: ...                                # advance writer state after the store transaction succeeded

class TimelineIndex:                                           # in-memory index over a loaded timeline (pure)
    def __init__(self, entries: Iterable[TimelineEntry]) -> None: ...                       # validates via verify_timeline (RGE-STORE-0804 on chain break)
    def query(self, q: TimelineQuery) -> tuple[TimelineEntry, ...]: ...                      # RGE-CONFIG-0806
    def last(self, kind: TimelineKind | None = None) -> TimelineEntry | None: ...

def verify_timeline(entries: Sequence[TimelineEntry], *, strict_chain: bool = True) -> TimelineVerification: ...   # §12.2 (never raises on violations)
def project_timeline(index: TimelineIndex, windows: Sequence[WindowMarkers], opts: ProjectionOptions) -> TimelineView: ...   # §12.4 pure
def to_jsonl(entries: Sequence[TimelineEntry]) -> bytes: ...                                # canonical, deterministic
def to_csv(entries: Sequence[TimelineEntry]) -> bytes: ...                                  # §12.5
def effective_at(e: TimelineEntry) -> tuple[int, int]: ...                                  # (start_mono, end_mono) used for time-range queries
```

Behaviour summary: `append` is `async`; it serialises under an internal `asyncio.Lock` only for *stamping and enqueue* (sequence, `at = clock.now()`, digest), awaits durability **outside** the lock, and returns the persisted entry. Cancellation after enqueue but before durability returns `CancelledError` to the caller; the entry may still become durable (it is then visible via recovery; the writer state is already advanced). Idempotency: not idempotent (each call creates an entry).

### 7.2 Error codes (block 0800–0899 (RG-P03-005 §8.3))

| Code | Name | Raised by |
|---|---|---|
| RGE-INTERNAL-0801 | `timeline_entry_invalid` — kind/payload/ref mismatch, bounds, grammar | `TimelineEntry` validator, `append` |
| RGE-STORE-0802 | `timeline_quota_exceeded` — `max_entries` reached (engine turns it into `ABORTED(quota_exceeded)`, TM-34) | `append` |
| RGE-TIMING-0803 | `timeline_order_violation` — `at` earlier than the previous entry's `at` within one epoch; epoch change without a `process_restart` anomaly entry | `append`, `verify_timeline` |
| RGE-STORE-0804 | `timeline_chain_broken` — gap, duplicate, reorder, digest mismatch on load | `TimelineIndex`, `verify_timeline(strict)` |
| RGE-INTERNAL-0805 | `timeline_writer_misuse` — append after `close`, nested/forgotten `exclusive`, `commit_built` of a stale entry | writer |
| RGE-CONFIG-0806 | `timeline_query_invalid` — malformed query (negative limit, reversed range, unknown kind) | `TimelineQuery`, `query` |

## 8. Data structures and schemas

Conventions as RG-P02-001 §8 (frozen `Model`s; `Int64` ns; validator messages begin with the RGE code; `None` omitted). `TimelineEntry` is a `Document` (`SCHEMA_ID="timeline_entry"`, `1.0`) with `Provenance`.

### 8.1 `TimelineEntry`

| Field | Type | Constraint | Description |
|---|---|---|---|
| `schema_version` | SchemaVersion | `"1.0"` | |
| `id` | `TlnId` | | frozen name |
| `experiment_ref` | `ExpId` | constant within a timeline | additive |
| `seq` | Count | ≥ 1; gap-free per experiment | frozen name |
| `at` | `TimeInstant` | non-decreasing in `mono_ns` along `seq` within one `(clock_id, epoch)` | frozen name; **writer time**: `Clock.now()` read inside the writer's serialisation point |
| `kind` | `TimelineKind` | closed enum (§8.2) | frozen name |
| `ref` | `TimelineRef \| None` | grammar per kind | frozen name; the record this entry points at |
| `payload` | per-kind model | discriminated by `kind` | typed, bounded, secret-free |
| `credential_ref` | `CrdId \| None` | | for queries by credential |
| `target_ref` | `TgtId \| None` | | |
| `occurred_at` | `TimeInstant \| None` | same clock/epoch as `at`; `mono ≤ at.mono`; only for `operator_action` | when the underlying fact happened, if earlier than the writer time |
| `occurred_at_claimed` | `RemoteInstant \| None` | `source=operator_entry`; **assumed** | operator-typed time (never used for ordering) |
| `out_of_order` | bool | `true` iff `occurred_at` is present and `occurred_at.mono < previous.at.mono` | DATA-MODEL §9.3 marker |
| `summary` | ShortText | ≤ `timeline.summary_max_chars` (200) | deterministic human text generated from the payload (§12.1) unless supplied by `operator_action` |
| `derivation` | `Derivation` | `observed` for facts captured by RG; `assumed` for operator-asserted; `calculated` for derived notes | frozen name |
| `prev_digest` | `Sha256Digest \| None` | `None` only for `seq = 1` | additive |
| `digest` | `Sha256Digest` | `= chain_digest(prev_digest, canonical(entry without digest))` | additive |
| `produced_by` | `ProducedBy` | | provenance |

`TimelineRef`: `{ref_type: Literal["observation","revocation","transition","credential_state","operator_action","evidence"], id: str, version: Count | None}`; grammar: `observation` → `obs_…`; `revocation` → `rev_…` + `version`; `transition` → experiment id + transition `seq`; `credential_state` → `crd_…`; `operator_action` → `act_<n>`; `evidence` → `evd_…`.

### 8.2 `TimelineKind` and payloads

| `kind` | Payload model (bounded, secret-free) | `ref` | Written by |
|---|---|---|---|
| `state_transition` | `{from_state, to_state, trigger, transition_id, reason_code, recovery: bool}` | `transition` | commit path of every transition (RG-P02-007 §10.2); the first entry (`seq = 1`) is the creation `∅ → DRAFT` |
| `revocation` | `{event_ref, version, kind, ack_state, actor, ack_source?, anchor_quality?, anchor_width_ns?}` | `revocation` | action framework / manual channel (each event version) |
| `observation` | `{obs_ref, credential_ref?, phase, category, outcome, s_ns, r_ns, lateness_ns}` | `observation` | probe runner via sink |
| `clock_anomaly` | `ClockAnomaly` (RG-P02-001 §8.7) | — | engine guard |
| `operator_action` | `{action: Label, operator: Label?, note: ShortText?, marker: Literal["M1","M2"]?}`; actions: `arm_confirmed`, `go`, `disarm`, `abort`, `manual_start`, `manual_ack`, `recovery_choice`, `note` | `operator_action` | CLI/GUI via engine |
| `credential_state` | `CredentialStateRecord` (RG-P02-003 §8.5) | `credential_state` | engine |
| `external_event` | `{event_ref, version, source_name, flags: SortedSet[ArrivalFlag], dedup_key?}` | `revocation` | event ingestion (RG-P04-011/P06-008) |
| `control_result` | `{role, credential_ref?, passed: bool, reason: Label, obs_refs: tuple[ObsId,…] (≤ 8)}` | — | baseline/control gate |
| `cleanup_action` | `{ledger_ref, action: Label, result: Literal["ok","failed","skipped","already_restored"], residual: bool}` | — | cleanup phase |
| `system_note` | `{code: Label, text: ShortText}`; codes include `report_emitted`, `export_done`, `quota_warning`, `lab_manifest`, `recovery_applied` | optional `evidence` | any component |

Extension kinds are **not** allowed (the enum is closed; plugins use `system_note` codes) so that every reader can interpret every entry.

### 8.3 `Timeline`, `TimelineQuery`, `TimelineVerification`, `WriterState`

`Timeline` = `tuple[TimelineEntry, ...]` ordered by `seq` (a view; not a persisted wrapper).
`TimelineQuery`: `seq_from?`, `seq_to?` (inclusive, `Count`), `kinds?: SortedSet[TimelineKind]`, `credential_ref?`, `target_ref?`, `effective_from_mono_ns?`, `effective_to_mono_ns?` (closed range on `effective_at`), `clock_id?`, `epoch?`, `limit: Count` (default 1000, max 10 000), `order: "seq"|"effective"` (default `seq`). Validators (`RGE-CONFIG-0806`): ranges ordered, `limit ≥ 1`, effective range requires `clock_id`/`epoch` or defaults to the experiment's current epoch.
`TimelineVerification`: `ok: bool`, `entries: Count`, `violations: tuple[Violation,…]` (`code`, `seq`, `detail: ShortText`; ≤ 100), `last_seq`, `last_digest`.
`WriterState`: `last_seq: Count`, `last_at: TimeInstant | None`, `last_digest: Sha256Digest | None`, `epoch: str | None`, `closed: bool`, `final_seen: bool`.

### 8.4 JSON example (JSONL lines shown pretty-printed; digests are placeholders computed by the fixture)

```json
{"schema_version": "1.0", "id": "tln_01M4QJ2FBG1HYGCPWPQ5E6EYCN", "experiment_ref": "exp_01M4QJ0B00M9S346Q3D25VT4F5", "seq": 12,
 "at": {"wall_ns": "1791796860000800000", "mono_ns": "260000800000", "clock_id": "system", "read_cost_ns": "400", "epoch": "a1b2c3d4"},
 "kind": "revocation", "ref": {"ref_type": "revocation", "id": "rev_01M4QJ25K0E0ZBGJ09TQM83XSS", "version": 1},
 "payload": {"event_ref": "rev_01M4QJ25K0E0ZBGJ09TQM83XSS", "version": 1, "kind": "account_disabled", "ack_state": "pending", "actor": "rg"},
 "summary": "revocation account_disabled requested (v1 pending)", "derivation": "observed",
 "prev_digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
 "digest": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
 "produced_by": {"component": "rg_core.timeline", "version": "1.0"}}
```

## 9. Inputs, outputs, and validation rules

| # | Rule | Code |
|---|---|---|
| VR-1 | `kind` ↔ payload model ↔ `ref_type` coupling per §8.2; `credential_ref` required for `observation`/`credential_state` payloads that carry one; payload bounds (`obs_refs ≤ 8`, `summary ≤ 200`, `note ≤ 256`) | RGE-INTERNAL-0801 |
| VR-2 | `occurred_at` only on `operator_action`; same clock/epoch as `at`; `occurred_at.mono ≤ at.mono`; `out_of_order` iff `occurred_at.mono < previous.at.mono` | RGE-INTERNAL-0801 |
| VR-3 | `at.mono_ns ≥ previous.at.mono_ns` within one `(clock_id, epoch)`; a new epoch requires an intervening `clock_anomaly(process_restart)` entry | RGE-TIMING-0803 |
| VR-4 | `seq` equals `last_seq + 1`; `prev_digest` equals the previous `digest`; `digest` recomputes | RGE-STORE-0804 (on load/verify), RGE-INTERNAL-0805 (at append) |
| VR-5 | entries after the final transition limited to `system_note` and `operator_action(note)` | RGE-INTERNAL-0805 |
| VR-6 | entry count ≤ `max_entries` | RGE-STORE-0802 |
| VR-7 | `TimelineQuery` well-formed | RGE-CONFIG-0806 |
| VR-8 | the first entry is `state_transition` `∅ → DRAFT` at `seq = 1` | RGE-STORE-0804 (verify) |

## 10. Detailed execution behavior

### 10.1 Append (all kinds except transition co-commit)

1. Caller (engine, runner sink, adapters) calls `writer.append(kind, payload, …)`.
2. Under the writer lock: validate payload and `ref`; `at = clock.now()`; check `at.mono ≥ last_at.mono` (same epoch) else `RGE-TIMING-0803`; check epoch rule; set `seq = last_seq + 1`; compute `out_of_order` (if `occurred_at`); generate `summary`; `id = ids.new("tln")`; `prev_digest = last_digest`; `digest = chain_digest(prev_digest, canonical(entry − digest))`; advance writer state **tentatively**; enqueue to `sink` (FIFO).
3. Release the lock; `await` the sink's durability future. If the sink fails (`STORE` error) the writer state is rewound **only if no later entry has been enqueued**, otherwise the writer enters a *poisoned* state: every later `append` raises the original store error and the engine fails the run (`FailureReason.store_error`) — the durable prefix is intact and recoverable (§12.6).
4. Return the entry; the engine/event bus publishes `timeline.entry` for live viewers (RG-P03-007) **after** durability (GUI never shows what is not durable).

### 10.2 Atomic co-commit with a state transition (RG-P02-007 §10.2)

```
async with writer.exclusive() as w:                  # blocks other appenders for the duration of one transition commit (≤ 20 ms target)
    entry = w.build("state_transition", payload, ref=transition_ref)      # assigns seq/at/digest, no I/O
    await store.transition(exp_id, frm, to, at, trigger=…, records=[entry, …])   # one SQLite transaction (CCR-3)
    w.commit_built(entry)                            # only now does writer state advance
```
If the transaction fails, nothing was consumed: `build` was pure with respect to writer state, so no seq gap appears and appenders resume with the same `last_seq`.

### 10.3 Stamping rules (which clock, when)

`at` is the instant of **entry creation inside the writer** (monotone by construction). Observation entries carry the observation's own send/receive instants in the payload (`s_ns`, `r_ns`); revocation entries carry the anchor instants in the event record. Analysis never reads `at` (it reads observations/events), so lock-wait jitter cannot enter a measurement. For queries and drawing, `effective_at(entry)` is: observation → `(s_ns, r_ns)`; `operator_action` with `occurred_at` → `(occurred_at.mono, occurred_at.mono)`; everything else → `(at.mono, at.mono)`.

### 10.4 Clock anomalies and restarts

The engine publishes each `ClockAnomaly` (RG-P02-001) as a `clock_anomaly` entry immediately. On crash recovery the new process creates a writer with `resume=WriterState` from the last durable entry; before any other entry it appends `clock_anomaly(process_restart)` whose `previous` is the last durable instant of the old epoch; only then may entries with the new epoch follow (VR-3).

### 10.5 Live viewing

Viewers subscribe to the event bus (RG-P03-007) for `timeline.entry` events and use `TimelineIndex.query` with `seq_from = last_seen + 1` to catch up after reconnect (SSE `Last-Event-ID` = last seq), so the live view is lossless even when the bus drops non-critical events.

## 11. State transitions and invariants

The timeline is append-only; the writer has states `OPEN → CLOSED` (`close()` after the final transition) and `CLOSED → NOTES_ONLY` (`reopen_for_notes()` for post-hoc `system_note`/`operator_action(note)`).

- **INV-1** `seq` of a stored timeline is exactly `1…n` (gap-free, strictly increasing, no duplicates) and `seq = 1` is the creation `state_transition`.
- **INV-2** Within one `(clock_id, epoch)`, `at.mono_ns` is non-decreasing along `seq`.
- **INV-3** Every change of `epoch` or `clock_id` along `seq` is preceded by a `clock_anomaly(process_restart)` entry (`clock_id` never changes within an experiment: DATA-MODEL §9.8).
- **INV-4** `out_of_order = true` ⇔ the entry is an `operator_action` with `occurred_at.mono < previous.at.mono`; `at` itself never decreases.
- **INV-5** `digest_i = chain_digest(digest_{i−1}, canonical(entry_i without digest))`, `prev_digest_i = digest_{i−1}`, `prev_digest_1 = None`.
- **INV-6** Modifying any field of any entry, deleting an entry, duplicating or reordering entries makes `verify_timeline` report a violation.
- **INV-7** Every `state_transition` entry's payload `(from_state, to_state)` equals the corresponding `Transition` record and `from_state` of entry *k+1* equals `to_state` of entry *k* among transition entries.
- **INV-8** Every `observation` entry references an existing `Observation` of the same experiment with equal `s_ns/r_ns/outcome` (referential check performed by `verify` when observations are supplied).
- **INV-9** After the final transition only `system_note` and `operator_action(note)` entries appear.
- **INV-10** All entries of a timeline share one `experiment_ref`.
- **INV-11** Payloads and summaries contain no secret material and no control characters; renderers escape on output.
- **INV-12** `to_jsonl` is deterministic: equal timelines ⇒ equal bytes; `to_jsonl(entries)` parsed and re-serialised is a fixed point.

## 12. Core algorithms and pseudocode

### 12.1 Summary generation (deterministic templates, ≤ 200 chars)

| kind | Template |
|---|---|
| `state_transition` | `"{transition_id} {from}→{to} ({trigger}{:reason_code})"` |
| `revocation` | `"revocation {kind} {action} (v{version} {ack_state})"` |
| `observation` | `"{phase} {outcome} cred {fp-less id tail} lat {r−s}ms"` (credential shown by the last 6 characters of its id; latency in whole ms) |
| `clock_anomaly` | `"{kind} step {step_ns/1e6:+d}ms"` (integer arithmetic) |
| `operator_action` | operator text (bounded) or `"{action}"` |
| `control_result` | `"control {role} {passed\|failed}: {reason}"` |
| `cleanup_action` | `"cleanup {action}: {result}"` |
| others | `"{code}"` / state names |

Control characters are removed; text is truncated at the character limit on a code-point boundary with a trailing `…`.

### 12.2 `verify_timeline`

```
def verify_timeline(entries, strict_chain=True):
    v = []; prev = None
    for i, e in enumerate(entries, start=1):
        if e.seq != i:                                    v += gap_or_duplicate_or_reorder(e.seq, i)
        if e.experiment_ref != entries[0].experiment_ref: v += mixed_experiment
        if prev:
            if same_epoch(prev.at, e.at) and e.at.mono_ns < prev.at.mono_ns: v += at_decreased
            if epoch_changed(prev.at, e.at) and not seen_restart_anomaly_between: v += epoch_without_anomaly
        if strict_chain:
            if e.prev_digest != (prev.digest if prev else None): v += prev_digest_mismatch
            if e.digest != chain_digest(e.prev_digest, canonical(e without digest)): v += digest_mismatch
        if e.kind == operator_action and e.occurred_at: expect(e.out_of_order == (e.occurred_at.mono_ns < prev.at.mono_ns))
        if final_seen and e.kind not in (system_note, operator_action): v += entry_after_final
        prev = e
    if entries and not (entries[0].kind == state_transition and entries[0].payload.from_state is None): v += bad_first_entry
    return TimelineVerification(ok = not v, ...)
```

**Worked example (tamper detection).** Timeline of 5 entries with digests `d1…d5`. (a) Edit entry 3's `payload.outcome` from `access_denied` to `access_confirmed`: recomputed `digest_3 ≠ d3` ⇒ violation `digest_mismatch@3` (and because `d4` was derived from `d3`, `prev_digest_mismatch` is *not* reported for 4 — only the edited entry fails, localising the tamper). (b) Delete entry 3: entries are now `1,2,4,5` ⇒ `gap@4` and `prev_digest_mismatch@4`. (c) Swap entries 3 and 4: `reorder@3`, `reorder@4`, digest mismatches. (d) Replace the whole tail with a consistent recomputed chain: not detectable by the chain alone — mitigated by recording the root/last digest in the manifest at `ANALYZING` and in the audit log (RG-P08-001/RG-P11-002, TM-26; design is tamper-*evident*, not tamper-proof).

### 12.3 Query semantics (`TimelineIndex.query`)

Filters are conjunctive. `seq` range inclusive. Effective-time range uses **interval overlap**: an entry matches iff `[eff_start, eff_end]` intersects `[from, to]` (closed), so an observation whose bracket straddles a boundary is returned. `credential_ref` matches entries whose `credential_ref` equals it, plus `revocation` entries whose event `affects` resolution contains it (resolved by the caller via `affected_credentials` supplied in the query context; the index stores, not resolves). Ordering `seq` (default) or `effective` = `(eff_start, seq)` — stable and total. `limit` truncates after ordering and the result includes `next_seq` for pagination. Complexity: O(log n + k) by sorted arrays on `seq` and `eff_start`, per-credential/kind postings.
**Worked example.** Entries (seq: kind, effective): 1 transition @0.0; 2 observation `[1.000, 1.040]`; 3 observation `[2.000, 2.040]`; 4 operator_action `occurred_at` 1.5, written (at) 2.5 → `out_of_order=true`; 5 observation `[3.000, 3.040]`. Query effective `[1.020, 2.010]` ⇒ entries 2 (overlaps 1.020–1.040), 3 (overlaps at 2.000–2.010), 4 (point 1.5). Order by `effective`: 2, 4, 3; by `seq`: 2, 3, 4.

### 12.4 `project_timeline` (view model for FR-RPT-003 / FR-GUI-002)

Input: `TimelineIndex`, `WindowMarkers` per (credential, target) — `{credential_ref, target_ref, a_req_ns, a_ack_ns, l_ref?, d_ref?, x_lo_ns, x_hi_ns?, expiry_lo_ns?, expiry_hi_ns?, deadline_ns?}` (from RG-P08-004/-P02-005; the projection never computes them) — and `ProjectionOptions{origin: "a_req"|"first_entry", include_kinds, max_points_per_lane}`.
Output `TimelineView`: `axis{clock_id, epoch, origin_mono_ns}`; `lanes: tuple[Lane]` one per credential (+ one "controls" lane + one "events" lane); `Lane.points: tuple[Point{x0, x1, outcome, obs_ref}]` with `x = mono − origin` in ns; `markers: tuple[Marker{kind ∈ {a_req, a_ack, last_access, first_denial, exposure_lo, exposure_hi, expiry_lo, expiry_hi, deadline, clock_anomaly, state_transition, manual_m1, manual_m2}, x, ref}]`; `downsampled: bool` (when a lane exceeds `max_points_per_lane` the projection keeps all non-`access_confirmed`/`access_denied` transitions and the first/last of each run of identical outcomes, never dropping `L`, `D` or points adjacent to markers).
**Worked example.** Origin `a_req = 260.000 s`; lane for the subject credential: points `[263.002, 263.045]` denied etc.; markers `a_req x=0`, `a_ack x=0.180 s`, `last_access x=3.000 s`, `first_denial x=4.000 s`, `exposure_lo x=2.820 s`, `exposure_hi x=4.060 s` — all integer ns offsets; deterministic ordering `(x, kind rank, ref)`.

### 12.5 Exports

**JSONL** (`timeline.jsonl`): one canonical JSON object per line (RG-P03-002 `canonical_json`, `\n` terminated, UTF-8, no BOM), entries by `seq`; integers as strings; this is the *only* export that is hash-verifiable.
**CSV** (`timeline.csv`, v1.x FR-RPT-002): header `seq,kind,at_wall_ns,at_mono_ns,epoch,effective_start_mono_ns,effective_end_mono_ns,credential_ref,target_ref,out_of_order,summary,digest`; RFC 4180 quoting; fields starting with `= + - @ TAB CR` are prefixed with `'` (CSV injection defence, TM-12); `summary` already control-character-free.

### 12.6 Writer-state recovery

On startup `resume_state(entries)` takes the last durable entry: `last_seq`, `last_at`, `last_digest`, `epoch`, `final_seen`. If the last entry is *after* the last durable store state (cannot happen: entries are durable before the engine acts) nothing special is needed; if the process crashed between *enqueue* and *durability*, the entry is simply absent and `last_seq` is the durable value — no gap, because the sequence is allocated only inside the lock *and* the writer state is rebuilt from the store, not from memory. The writer then appends `clock_anomaly(process_restart)` (§10.4).

## 13. Internal functions, methods, or service operations

```python
def _build_entry(w: WriterState, kind, payload, ref, now: TimeInstant, ids: IdFactory, **kw) -> tuple[TimelineEntry, WriterState]: ...   # pure
def _summary(kind: TimelineKind, payload: Model) -> str: ...
def _entry_digest(entry_without_digest: Mapping[str, JsonValue], prev: Sha256Digest | None) -> Sha256Digest: ...
def _effective_at(e: TimelineEntry) -> tuple[int, int]: ...
def _same_epoch(a: TimeInstant, b: TimeInstant) -> bool: ...
def _csv_safe(field: str) -> str: ...
def _downsample(points: Sequence[Point], keep: AbstractSet[str], cap: int) -> tuple[Point, ...]: ...
```

## 14. Error handling and failure recovery

| Failure | Detection | Handling | Recovery | Code |
|---|---|---|---|---|
| Store append fails | sink raises `STORE` | writer rewinds (if last) or poisons; engine → `FAILED(store_error)` | startup recovery from the durable prefix | RGE-STORE-* |
| Quota reached | count ≥ `max_entries` | raise; engine → `ABORTED(quota_exceeded)` + cleanup | raise quota / re-run | RGE-STORE-0802 |
| `at` goes backwards | `append` check | raise; indicates clock misuse (e.g. mixed clocks) | fix producer | RGE-TIMING-0803 |
| Chain broken on load | `TimelineIndex` | refuse to load for analysis/report (evidence-integrity failure); `rg report verify` shows violations | restore from backup/bundle | RGE-STORE-0804 |
| Append after close | writer state | raise | caller bug | RGE-INTERNAL-0805 |
| Payload/kind mismatch | validator | raise | producer bug | RGE-INTERNAL-0801 |
| Cancellation during append | `CancelledError` | entry may be durable; writer state consistent; caller sees cancellation | recovery reads durable prefix | RGE-CANCELLED (not a failure) |

## 15. Security requirements and trust boundaries

- **TM-26 (tamper-evident):** per-entry chain + root digest recorded elsewhere; verification on every load for reports/export; documented limits (§12.2d).
- **TM-28:** clock anomalies and restarts are first-class entries; mixed clocks cannot be appended (VR-3).
- **TM-11/TM-12 (injection):** `summary`/`note`/`text` are bounded, control-character-free, never interpreted as markup; CSV export defends against formula injection; renderers HTML-escape.
- **TM-34 (resource exhaustion):** bounded entries and bounded payloads; quota ⇒ clean abort.
- **Secrets:** payloads contain ids, enums, ints and bounded text only (INV-11); operator notes are user text and pass the redactor before persistence (RG-P03-004).
- **Untrusted inputs:** `operator_action.note`, `system_note.text` (plugins) are the only free-text sources; both are length-bounded and sanitised at the boundary.

## 16. Concurrency, asynchronous behavior, and resource ownership

One `TimelineWriter` per experiment, owned by the run-scope coordinator; callers on the same event loop use `await append`. Worker threads (probe workers) **never** call the writer: they hand observations to the runner, which appends from the loop thread. `exclusive()` serialises a transition commit against concurrent appenders (a bounded wait; appenders queue on the same lock). The sink's queue is bounded and lossless (backpressure: `append` awaits). Memory: `TimelineIndex` ≈ 600 B/entry → 10 000 observations + 500 other entries ≈ 6 MiB (NFR-PERF-006). Cancellation: see §14.

## 17. Performance and resource requirements

Proposals validated by `BM-TL-1`: `append` stamping+digest ≤ 150 µs; sustained 500 appends/s with the SQLite sink in batched mode (NFR-PERF-005 budget: ≤ 15 % of a core at 50 probes/s); average persisted entry ≤ 700 B (observation entries; the observation record itself is ≤ 2 KiB, RG-P02-006) ⇒ 10 000 observations ≈ 7 MB timeline; `verify_timeline` of 10 000 entries ≤ 1 s; `project_timeline` of 10 000 points ≤ 200 ms (NFR-PERF-008 report budget). Rationale: the chain hash (sha256 over ≈ 600 B) dominates and is ≈ 2 µs.

## 18. Configuration and defaults

| Field | Type | Default | Range | Env var | Notes |
|---|---|---|---|---|---|
| `timeline.max_entries` | int | 500 000 | 1 000 … 10 000 000 | `RG_TIMELINE_MAX_ENTRIES` | quota ⇒ `RGE-STORE-0802` |
| `timeline.summary_max_chars` | int | 200 | 40 … 512 | `RG_TIMELINE_SUMMARY_MAX_CHARS` | |
| `timeline.query_default_limit` | int | 1000 | 1 … 10 000 | `RG_TIMELINE_QUERY_DEFAULT_LIMIT` | |
| `timeline.query_max_limit` | int | 10 000 | 100 … 100 000 | `RG_TIMELINE_QUERY_MAX_LIMIT` | |
| `timeline.max_points_per_lane` | int | 5000 | 100 … 100 000 | `RG_TIMELINE_MAX_POINTS_PER_LANE` | projection downsampling (§12.4) |
| `timeline.verify_on_load` | bool | true | | `RG_TIMELINE_VERIFY_ON_LOAD` | `false` only for the live GUI incremental reads; reports/exports always verify |

Precedence: defaults < file < env < CLI; invalid ⇒ `RGE-CONFIG-0806` at load.

## 19. Logging, observability, and evidence requirements

Events: `timeline.entry` {`experiment_ref`, `seq`, `kind`, `summary`} (published after durability; payload excludes bodies), `timeline.verify` {`entries`, `ok`, `violations_n`}, `timeline.quota` {`entries`, `max`}. Metrics: `timeline_entries_total{kind}`, `timeline_append_ms`. Evidence: the timeline itself is part of the evidence bundle (`timeline.jsonl`, with the last digest in the manifest, RG-P08-001); each entry is `derivation=observed` unless stated. Redaction: payloads are secret-free by construction; free text passes the redactor.

## 20. Platform compatibility

Pure Python. JSONL uses `\n` line endings on every platform (no `os.linesep`); CSV uses `\r\n` per RFC 4180 and is written in binary mode by the app layer. Timestamps in exports are integers (no locale/timezone formatting); the display layer may use `format_iso` (UTC) from RG-P02-001.

## 21. Edge cases and invalid inputs

| # | Case | Expected behaviour |
|---|---|---|
| E-1 | Two observation entries appended in the same nanosecond | distinct `seq`; `at` equal; order by `seq` |
| E-2 | `at` from the clock earlier than previous `at` (same epoch) | `RGE-TIMING-0803` |
| E-3 | `operator_action` with `occurred_at` later than `at` | `RGE-INTERNAL-0801` |
| E-4 | `operator_action` backdated 90 s | `at` non-decreasing; `occurred_at` earlier; `out_of_order=true` |
| E-5 | `observation` payload with `credential_ref` absent for a control with no credential | valid (`control_kind none/garbage`) |
| E-6 | entry after final transition: `observation` | `RGE-INTERNAL-0805` |
| E-7 | entry after final transition: `system_note(report_emitted)` | accepted (writer in NOTES_ONLY) |
| E-8 | restart without `clock_anomaly(process_restart)` | `RGE-TIMING-0803` |
| E-9 | `limit = 0` in a query | `RGE-CONFIG-0806` |
| E-10 | query range reversed | `RGE-CONFIG-0806` |
| E-11 | `append` cancelled after enqueue | entry durable on recovery; `last_seq` consistent |
| E-12 | transition commit fails | no seq consumed; next append reuses `last_seq + 1` |
| E-13 | 10 000 appends from 100 tasks | strictly increasing seq, no gaps, chain valid |
| E-14 | summary containing `\n` or ANSI escape | removed |
| E-15 | CSV summary starting with `=` | prefixed `'` |
| E-16 | timeline with `x.vendor.kind` entry | rejected (closed enum) |
| E-17 | `TimelineIndex` over a log with a deleted entry | `RGE-STORE-0804` |

## 22. Unit and integration test requirements

| ID | Condition | Expected observation |
|---|---|---|
| TST-RG-P02-008-01 | Concurrency: 100 tasks × 100 appends on one writer with an in-memory sink | seq `1…10 000` gap-free; `at.mono` non-decreasing; chain valid (E-13, INV-1/2/5) |
| TST-RG-P02-008-02 | Payload/kind/ref coupling table for all 10 kinds (valid and invalid combos) | `RGE-INTERNAL-0801` for invalid |
| TST-RG-P02-008-03 | Clock misuse: injected clock returning smaller mono; epoch change with/without `process_restart` entry | `RGE-TIMING-0803`; accepted only with the entry (E-2, E-8) |
| TST-RG-P02-008-04 | Backdated operator action (E-4) and invalid `occurred_at` (E-3) | `out_of_order=true`, `at` non-decreasing; error for E-3 |
| TST-RG-P02-008-05 | Tamper detection worked example (a)–(c): edit payload, delete, swap | violations as stated; (d) replace-tail passes chain but fails manifest root comparison (fixture) |
| TST-RG-P02-008-06 | Hypothesis: random timelines then random single mutations (edit/delete/duplicate/reorder/insert) | `verify_timeline` never returns ok for a mutated timeline (INV-6); ok for unmutated |
| TST-RG-P02-008-07 | Atomic co-commit with a fault-injecting store (fail before/after record insert; kill) | no seq gap; writer state unchanged on failure; transition + timeline entry both present or both absent (E-12) |
| TST-RG-P02-008-08 | Poisoned writer: sink fails on entry *k* while *k+1* already enqueued | later appends raise the store error; durable prefix verifies |
| TST-RG-P02-008-09 | Query semantics worked example (§12.3) incl. pagination `next_seq` and credential filter | results/orders as stated |
| TST-RG-P02-008-10 | Query validators E-9, E-10; limits max | `RGE-CONFIG-0806` |
| TST-RG-P02-008-11 | Post-final rules (E-6, E-7); `reopen_for_notes` | as stated |
| TST-RG-P02-008-12 | Quota: `max_entries = 100` | the 101st append raises `RGE-STORE-0802`; chain of the first 100 valid |
| TST-RG-P02-008-13 | Projection worked example (§12.4) with `WindowMarkers` from RG-P02-006 E1; downsampling keeps `L`/`D` | marker x-offsets `0, 180 000 000, 3 000 000 000, 4 000 000 000, 2 820 000 000, 4 060 000 000`; deterministic order |
| TST-RG-P02-008-14 | Export determinism: JSONL bytes identical across two serialisations and across platforms (golden file); CSV injection (E-15), summary sanitisation (E-14) | byte-identical; sanitised |
| TST-RG-P02-008-15 | Recovery: kill process after random append, rebuild `WriterState` from the store, append `process_restart` then new entries | continuous seq; chain valid; `verify` ok |
| TST-RG-P02-008-16 | Integration (lab virtual time): full SCN-02 run; compare `state_transition` entries with `Transition` records (INV-7) and `observation` entries with observations (INV-8) | referential checks pass; timeline size within budget (≤ 700 B/entry average) |
| TST-RG-P02-008-17 | Live catch-up: subscriber drops events (bus `drop_oldest`), reconnects with last seq | `query(seq_from=last+1)` returns exactly the missing entries (lossless view) |

## 23. Mocking and test fixtures

Doubles: `InMemoryTimelineSink` (with failure/kill hooks), fault-injecting store transaction fake, `VirtualClock` for stamping. Fixtures: `fixtures/timeline/entries_5.json` (tamper cases), `query_example.json` (§12.3), `projection_e1.json` (§12.4), `golden_timeline.jsonl` (export determinism), `csv_injection.json`. Hypothesis strategies: `rg_core.testing.strategies.timeline` (valid timelines; mutation operators).

## 24. Objective acceptance criteria

- **AC-RG-P02-008-01** A timeline written concurrently by many tasks is gap-free from 1, strictly increasing in `seq`, non-decreasing in `at.mono_ns` within an epoch, and hash-chained (verified by TST-RG-P02-008-01, TST-RG-P02-008-02, TST-RG-P02-008-03).
- **AC-RG-P02-008-02** Out-of-order operator actions are recorded with `occurred_at` and `out_of_order=true` without ever decreasing `at`; epoch changes require a `process_restart` anomaly entry (verified by TST-RG-P02-008-03, TST-RG-P02-008-04).
- **AC-RG-P02-008-03** `verify_timeline` detects every single edit, deletion, duplication, reordering or insertion of entries and reports the first affected `seq` (verified by TST-RG-P02-008-05, TST-RG-P02-008-06).
- **AC-RG-P02-008-04** A state transition and its timeline entry are committed atomically; a failed commit consumes no sequence number; a poisoned writer leaves a verifiable durable prefix (verified by TST-RG-P02-008-07, TST-RG-P02-008-08, TST-RG-P02-008-15).
- **AC-RG-P02-008-05** Queries by seq, effective-time overlap, credential, target and kind return the specified results and orders; malformed queries are rejected (verified by TST-RG-P02-008-09, TST-RG-P02-008-10, TST-RG-P02-008-17).
- **AC-RG-P02-008-06** The quota, post-final rules and entry-count bound hold and fail with the specified codes (verified by TST-RG-P02-008-11, TST-RG-P02-008-12).
- **AC-RG-P02-008-07** The projection yields deterministic, integer-offset lanes and markers and preserves `L`, `D` and anchor-adjacent points when downsampling (verified by TST-RG-P02-008-13).
- **AC-RG-P02-008-08** JSONL export is byte-deterministic and CSV export neutralises formula injection and control characters (verified by TST-RG-P02-008-14).
- **AC-RG-P02-008-09** On a full lab run the timeline agrees with the transition log and the observations, and averages ≤ 700 bytes per entry (verified by TST-RG-P02-008-16).

## 25. Research sources and engineering rationale

Sources: DATA-MODEL §7 (`TimelineEntry`), §9.3 (seq/at invariant), §9.8; PRD FR-EVD-008, FR-TEMP-003/007, FR-EVD-004, FR-RPT-002/003, FR-GUI-002; THREAT-MODEL TM-26, TM-28, TM-34, TM-12; SYSTEM-ARCHITECTURE §5 (bounded queues; evidence queues never lossy), §7 (store: append-only facts); STANDARDS-REFERENCE SV-004 (report first rejection, interval, attempts); RG-P03-002 (`chain_digest`, canonical JSON).

- **DEC-1 `at` is writer time; backdating via `occurred_at`.** DATA-MODEL §9.3 allows `at` to decrease only for explicit `occurred_at` operator entries; keeping `at` monotone and moving the earlier time into a separate field gives the same information with a *stronger* invariant (INV-2 has no exception) and cheap verification. Rejected: storing backdated `at` (breaks sorted-by-seq = sorted-by-time scans). Verification: TST-04.
- **DEC-2 Per-entry hash chain** (using `chain_digest`) rather than a Merkle tree: appends are O(1), verification is linear, and localisation of a tamper is exact. Rejected: no chain (violates FR-EVD-004/TM-26); Merkle (unneeded random access proofs). Verification: TST-05/06.
- **DEC-3 Single writer with `exclusive()` co-commit** instead of multi-writer + store-assigned seq: guarantees the "transition and its timeline entry are one transaction" property without relying on SQL sequence semantics, and keeps seq allocation deterministic under the virtual clock. Rejected: store-assigned seq (seq not known until commit, complicating the hash chain). Verification: TST-07.
- **DEC-4 Closed `TimelineKind` enum**: every reader (GUI, CSV, bundle import) can interpret all entries; plugin extension via `system_note` codes. Rejected: open `x.*` kinds (importers could not render them safely, TM-15). Verification: TST-02, E-16.
- **DEC-5 Projection is pure and overlays derived markers supplied by analysis** — keeps ADR-0013 separation (facts vs derivations): the timeline holds facts; `L`/`D`/bounds are derived records. Verification: TST-13.
- **DEC-6 Live view reads the durable store for catch-up** rather than trusting the lossy bus: the GUI is never ahead of durability and never silently misses an entry. Verification: TST-17.

## 26. Remaining uncertainties or assumptions

| # | Assumption | Evidence tag | Falsifying test |
|---|---|---|---|
| A-1 | `chain_digest`/`canonical_json` of RG-P03-002 are stable across platforms/Python versions (golden digests) | design (RG-P03-002 tests) | TST-RG-P02-008-14 golden file on Linux/Windows/macOS CI |
| A-2 | Holding the writer lock during one transition commit (≤ 20 ms) does not violate NFR-PERF-001 lateness budgets (probe sends do not use the writer) | proposal | benchmark BM-TL-1 + lateness histogram during transitions (RG-P12-004) |
| A-3 | Average observation timeline entry ≤ 700 B | estimate | TST-RG-P02-008-16 measures it; the bound is a proposal |
| A-4 | A single writer per experiment is sufficient for future distributed workers if workers stream observations to the coordinator (SYSTEM-ARCHITECTURE §11) | design | RG-P14-001 design review |
| A-5 | CCR-3 (store `transition(..., trigger, runtime_patch, records)`) is accepted by RG-P03-008 | design | RG-P03-008 spec review |
| A-6 | Operator-typed times are wall-only (`RemoteInstant`, `operator_entry`) and never needed for ordering | design | WF-04 UX test (RG-P10-003) |

## 27. Maintainability, portability, and future extension requirements

- **Versioning:** `timeline_entry` `1.0`; new payload fields are additive minor; new kinds require a DATA-MODEL change and a minor bump with readers rejecting unknown kinds of a higher minor (RG-P03-002 V4). The digest composition (`rg.chain.v1`) is frozen; changing it is major with migration (chains of old runs remain verifiable with the old algorithm id stored in the manifest).
- **Extension points:** additional exports (SARIF/JUnit are report-level, RG-P08-011), additional projection marker kinds (additive), `system_note` codes (free namespace by dotted prefix), alternate sinks (e.g. a distributed coordinator).
- **Reuse:** `TimelineWriter`/`verify_timeline`/`project_timeline` have no provider dependence and are reusable as a generic tamper-evident event-log component (master-prompt "secure evidence serialization").
- **Deprecation:** none yet; deprecated payload fields stay readable for one minor release.
