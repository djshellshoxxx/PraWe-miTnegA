---
id: RG-P02-001
title: "Time and clock model"
phase: "02"
package: core
module_ids: [MOD-CORE-TIME_AND_CLOCK_MODEL]
status: DRAFT
depends_on: [RG-P01-004, RG-P03-001]
requirements: [FR-TEMP-001, FR-TEMP-002, FR-TEMP-003, FR-LAB-004, FR-EVD-007, NFR-PERF-002, NFR-REL-002, NFR-TEST-003, NFR-MNT-001, NFR-MNT-002]
interfaces_defined: [IF-CORE-CLOCK, IF-CORE-CLOCKGUARD]
interfaces_used: []
schemas_defined: [SCH-TIME]
schemathesis_touchpoints: []
---

# RG-P02-001 — Time and clock model

> Scope reminder: this element fixes the *time vocabulary* every other element uses (`TimeInstant`, `RemoteInstant`, `ClockDomain`, `ClockOffset`, `TimeInterval`), the `Clock` port with its two local implementations (`SystemClock`, `VirtualClock`), startup calibration, wall-step detection and the lint rule RG-LINT-001. The scheduler that *waits* on a clock is RG-P03-006; the algorithm that *estimates* a `ClockOffset` is RG-P08-002.

## 1. Module identifier and name

| Item | Value |
|---|---|
| Element | RG-P02-001 — Time and clock model |
| Package / modules | `rg_core.time` (`rg_core.time.model`, `.system_clock`, `.virtual`, `.guard`, `.calibrate`), port `rg_core.ports.time.Clock` |
| Module id | `MOD-CORE-TIME_AND_CLOCK_MODEL` |
| Schemas | `SCH-TIME`: `TimeInstant`, `RemoteInstant`, `ClockDomain`, `ClockOffset`, `TimeInterval`, plus the additive records `ClockCalibration` and `ClockAnomaly` |
| Interfaces | `IF-CORE-CLOCK` (`Clock`, `SystemClock`, `VirtualClock`, `VirtualClockDriver`); new `IF-CORE-CLOCKGUARD` (`WallStepDetector`) |
| Lint rule | `RG-LINT-001` (ban on direct time/sleep calls — policy here, tooling in RG-P03-005 §12.7) |

## 2. Phase and requirement references

| Requirement | Realised by |
|---|---|
| FR-TEMP-001 dual-clock instants | §8.1 `TimeInstant`, §7 `Clock.now()`, §12.2 paired read |
| FR-TEMP-002 remote timestamps / offsets | §8.2–8.4 `RemoteInstant`, `ClockDomain`, `ClockOffset`; §12.6 interval conversion |
| FR-TEMP-003 wall-step detection | §7.3 `WallStepDetector`, §12.3, §18 `time.wall_step_tolerance_ns` |
| FR-LAB-004 clock skew/jump injection | §7.2 `VirtualClockDriver.jump_wall/set_wall_rate_ppm` (hooks consumed by RG-P09-004 and RG-P03-006) |
| FR-EVD-007 run manifest | §8.6 `ClockCalibration` is a manifest member |
| NFR-PERF-002 timing precision | §12.1 calibration rejecting a monotonic source whose measured granularity exceeds 1 ms |
| NFR-REL-002 determinism, NFR-TEST-003 no wall sleeps | §7.2 `VirtualClock` (advances only through its driver), §11 INV-9…11 |
| NFR-MNT-001 `rg_core` purity; NFR-MNT-002 strict typing (all models fully typed; mypy `--strict` clean) | §10.7 (only `rg_core.time.system_clock` reads OS clocks), §13.3 lint policy |

Threats and validity rules realised: **TM-28** (time-source manipulation; wall steps, virtual/real mixing), **TV-08** (monotonic + wall stamps, no verdict from sub-resolution differences), TV-24 (remote times are never silently local), R-007 (clock misalignment), ADR-0006, ADR-0014 (virtual results never mixed with real).

## 3. Purpose and user/security value

Every number the product publishes is a difference of two instants (DATA-MODEL §4). If those instants come from a wall clock that can step (NTP, VM resume, operator), the published exposure interval is silently wrong; if they come from a clock with 15.6 ms ticks the localisation width `W` is silently wider than reported. This module makes both failure modes *impossible to ignore*: durations come only from one monotonic clock; wall time is carried alongside for display and joins; the pairing error of every wall/mono reading is recorded; the monotonic source is calibrated at startup and rejected if too coarse; wall steps become `clock_anomaly` records that lower confidence (RG-P02-006 factor CF-08); remote timestamps are a *different type* that cannot be subtracted from local instants by accident. The same `Clock` port lets the lab replace time with a deterministic virtual timeline, making hour-long token lifetimes testable in milliseconds.

## 4. Explicit responsibilities

- **RESP-1** Define `TimeInstant`, `ClockDomain`, `RemoteInstant`, `ClockOffset`, `TimeInterval` field-by-field with validators, JSON form (int64 as decimal strings) and schema version `1.0`.
- **RESP-2** Define the `Clock` port (frozen signatures, INTERFACE-CONTRACTS §3) and implement `SystemClock` on `time.perf_counter_ns` (mono) and `time.time_ns` (wall).
- **RESP-3** Specify the paired-read procedure (mono, wall, mono → `read_cost_ns`) and the exact meaning of `mono_ns` and `wall_ns` in a `TimeInstant`.
- **RESP-4** Specify startup calibration (granularity, monotonicity, read cost) and its pass/fail rule, producing a `ClockCalibration` record for the run manifest.
- **RESP-5** Specify wall-step detection (`WallStepDetector`, default tolerance 50 ms) and the `ClockAnomaly` record.
- **RESP-6** Implement `VirtualClock` + `VirtualClockDriver`: virtual mono advances only via the driver (the scheduler), wall derived from a configured epoch, plus wall-jump and wall-rate injection hooks.
- **RESP-7** Define the process-epoch rule: `mono_ns` values are comparable only within `(clock_id, epoch)`; a restart creates a new epoch and recovery must treat cross-epoch spans as anomalies.
- **RESP-8** Specify the **policy and ban list of RG-LINT-001** (which time/sleep constructs are forbidden, which single module may read OS time) and the additions to the tooling of RG-P03-005 §12.7.
- **RESP-9** Provide the pure helper `remote_to_local_wall_interval` (type-level conversion of a `RemoteInstant` through a `ClockOffset`) so that no other element re-derives the formula.

## 5. Out-of-scope responsibilities

| Excluded item | Owner |
|---|---|
| Waiting, timers, lateness recording, virtual event loop | RG-P03-006 scheduler |
| Estimating `ClockOffset` from `Date` brackets/event pairs, discarding inconsistent samples (SV-048) | RG-P08-002 |
| Using anomalies to lower confidence; the confidence factor catalogue | RG-P02-006 (taxonomy), RG-P08-005 (scoring) |
| Writing `clock_anomaly` timeline entries and their ordering | RG-P02-008 (entry schema), engine P03-010 (emission) |
| Exposure bounds `X_lo/X_hi` | RG-P08-004 |
| Lint tooling (`ruff` `TID251` config, `tools/rglint.py`, scope/allow-list/suppression mechanics, CI jobs) | RG-P03-005 §12.7 (+ CI wiring RG-P12-001); this spec defines the ban list |
| Persistence of instants (SQLite INTEGER columns) | RG-P03-008 |
| Canonical JSON and int64-string codec implementation | RG-P03-002 (this spec states the wire rule) |
| Error class hierarchy (`RgError`) | RG-P03-005 |

## 6. Dependencies and prerequisites

- Specs: PRD (FR-TEMP-*, NFR-PERF-002), DATA-MODEL §2.2/§4/§9, INTERFACE-CONTRACTS §3 (`Clock`), ADR-0006/0014. No other module spec.
- Libraries: stdlib only plus `pydantic>=2` (ADR-0007) for models. `secrets` (epoch token). No third-party time library (`freezegun`, `time-machine` rejected, §25 DEC-6).
- Environment: Python ≥ 3.11 (ADR-0002). `time.perf_counter_ns` and `time.time_ns` available (stdlib since 3.7).
- Used by: every element that stamps an event; RG-P03-006 (scheduler), RG-P05-004 (transport stamps), RG-P06-009 (anchors), RG-P08-002, RG-P09-004.

## 7. External and internal interfaces

### 7.1 `Clock` port — IF-CORE-CLOCK (`rg_core.ports.time`)

```python
class Clock(Protocol):                       # synchronous reads are thread-safe; async methods are loop-bound
    kind: ClockKind                           # frozen
    clock_id: str                             # "system" | "virtual:<run_id>"           (additive)
    epoch: str | None                         # 8-hex process epoch for system clocks; None for virtual (additive)
    resolution_ns: int                        # measured mono granularity (calibration) or 1 for virtual (additive)
    loop_granularity_ns: int                  # measured granularity of the clock asyncio timers use (time.monotonic); 0 for virtual (additive; consumed by RG-P03-006)
    def wall_ns(self) -> int: ...             # frozen
    def mono_ns(self) -> int: ...             # frozen
    def now(self) -> TimeInstant: ...         # frozen; paired read, one call per instant
    async def sleep(self, ns: int) -> None: ...            # frozen
    async def sleep_until(self, mono_ns: int) -> None: ... # frozen
```

Contract:

| Method | Behaviour | Errors |
|---|---|---|
| `wall_ns()` | `time.time_ns()` (system) or the virtual wall function §7.2. Never used for durations. | none |
| `mono_ns()` | `time.perf_counter_ns()` (system) or virtual mono. Non-decreasing across happens-before-ordered calls. | `RGE-TIMING-0102` if a regression is detected by the optional runtime check `strict_mono=True` (default false; the cost is one comparison) |
| `now()` | §12.2 paired read; returns an immutable `TimeInstant`. | none |
| `sleep(ns)` | `ns <= 0` returns immediately (after one cooperative yield). Postcondition: `mono_ns()` at return ≥ entry `mono_ns()` + `ns`. | `RGE-CANCELLED-*` (RG-P03-005) on cancellation; `RGE-TIMING-0110` for an unattached virtual clock |
| `sleep_until(t)` | Postcondition: `mono_ns() >= t` at return (never early). `t` in the past returns after one yield. | as above |

`SystemClock.sleep_until` is a re-check loop: `while (r := t - mono_ns()) > 0: await asyncio.sleep(r / 1e9)`. The loop exists because `asyncio` timers may fire up to one loop-clock resolution early (RG-P03-006 §12.4); it guarantees "never early" by the same clock that stamps observations. The scheduler (not `Clock.sleep`) is the production waiting primitive for probes; `Clock.sleep` exists for adapters and settle intervals and for the virtual clock to expose waiting to the same virtual timeline.

Thread-safety: `wall_ns/mono_ns/now` are callable from any thread (worker threads stamp `t_send_start`/`t_recv_end` through `now()`, ADR-0004); results of concurrent calls from different threads are ordered only up to `read_cost_ns` (§11 INV-3). `sleep*` must be awaited on the loop that owns the run. Idempotent and side-effect free except `sleep*`.

### 7.2 Implementations (`rg_core.time.system_clock`, `rg_core.time.virtual`)

```python
class SystemClock:                                         # kind=system, clock_id="system"
    def __init__(self, *, mono_source: Callable[[], int] = time.perf_counter_ns,
                 wall_source: Callable[[], int] = time.time_ns,
                 loop_source: Callable[[], int] = time.monotonic_ns,   # only measured (granularity), never used for stamps
                 epoch: str | None = None,                  # None → secrets.token_hex(4)
                 calibration: ClockCalibration | None = None,
                 strict_mono: bool = False) -> None: ...
    @classmethod
    def calibrated(cls, config: TimeConfig) -> "SystemClock": ...  # runs §12.1, raises RGE-TIMING-0101/0102/0103

class VirtualClockDriver:                                  # capability object; only the scheduler holds it
    def advance_to(self, mono_ns: int) -> None: ...        # RGE-TIMING-0108 if < current
    def jump_wall(self, delta_ns: int) -> None: ...        # step wall, leave mono (FR-LAB-004)
    def set_wall_rate_ppm(self, ppm: int) -> None: ...     # wall runs at (1e6+ppm)/1e6 of mono (slew injection)
    def attach_sleeper(self, sleeper: Callable[[int], Awaitable[None]]) -> None: ...  # once; RGE-TIMING-0109 if repeated

class VirtualClock:                                        # kind=virtual, clock_id="virtual:<run_id>"
    @classmethod
    def create(cls, run_id: str, *, epoch_wall_ns: int, start_mono_ns: int = 0,
               read_cost_ns: int = 0) -> tuple["VirtualClock", VirtualClockDriver]: ...
```

Virtual wall function (exact integer arithmetic): with anchor `(wall_a, mono_a, ppm)` initialised to `(epoch_wall_ns, start_mono_ns, 0)`,

```
wall(mono) = wall_a + ((mono - mono_a) * (1_000_000 + ppm)) // 1_000_000
jump_wall(d):          wall_a := wall(mono_now) + d ; mono_a := mono_now      # re-anchor, ppm unchanged
set_wall_rate_ppm(p):  wall_a := wall(mono_now)     ; mono_a := mono_now ; ppm := p
```

`VirtualClock` has no way to move time: `sleep(ns)`/`sleep_until(t)` register a timer through the attached sleeper (the `VirtualScheduler`, RG-P03-006; the sleeper receives the **absolute** mono target `t`, or `mono_ns() + ns`) and suspend. `read_cost_ns` is a configured constant (default 0) reported in every `now()` so that tests can exercise the pairing-error path.

### 7.3 `WallStepDetector` — IF-CORE-CLOCKGUARD (`rg_core.time.guard`)

```python
class WallStepDetector:                                    # sync, single-owner (the engine's guard task); not thread-safe
    def __init__(self, clock_id: str, epoch: str | None, *, tolerance_ns: int = 50_000_000,
                 divergence_bound_ns: int = 250_000_000, slew_allowance_ppm: int = 0) -> None: ...
    def observe(self, instant: TimeInstant) -> ClockAnomaly | None: ...   # §12.3
    @property
    def max_divergence_ns(self) -> int: ...                # max |θ − θ_ref| seen (θ = wall_ns − mono_ns)
    @property
    def divergence_exceeded(self) -> bool: ...
```

`observe` raises `RGE-TIMING-0104` when `instant.clock_id/epoch` differ from the detector's. The *engine* (RG-P03-010) feeds it from a guard task (`time.guard_interval_ms`, default 1000) **and** from every probe stamp; the detector itself does no I/O and no waiting.

### 7.4 Pure helpers (`rg_core.time.ops`)

```python
def mono_delta(a: TimeInstant, b: TimeInstant) -> int:                 # b.mono_ns - a.mono_ns; RGE-TIMING-0104 on clock/epoch mismatch
def require_same_clock(*xs: TimeInstant) -> None: ...                  # RGE-TIMING-0104 / RGE-TIMING-0105 (system vs virtual)
def remote_to_local_wall_interval(r: RemoteInstant, off: ClockOffset) -> tuple[int, int]: ...  # §12.6; RGE-TIMING-0107
def format_iso(wall_ns: int) -> str: ...                               # display only: 'YYYY-MM-DDTHH:MM:SS.nnnnnnnnnZ'
```

### 7.5 Error codes (category `TIMING` unless stated; code block 0100–0199, RG-P03-005 §8.3)

| Code | Name | Raised by | Retryable |
|---|---|---|---|
| RGE-TIMING-0101 | `clock_resolution_insufficient` (measured granularity > `time.max_resolution_ns`) | calibration | no |
| RGE-TIMING-0102 | `monotonic_regression` | calibration; `strict_mono` | no |
| RGE-TIMING-0103 | `clock_not_advancing` (read cap reached before enough distinct readings) | calibration | no |
| RGE-TIMING-0104 | `clock_mismatch` (instants from different `clock_id` or `epoch`) | `mono_delta`, `require_same_clock`, detector, `TimeInterval` | no |
| RGE-TIMING-0105 | `clock_kind_mixed` (virtual and system instants in one analysis set; DATA-MODEL §9.8) | `require_same_clock` | no |
| RGE-TIMING-0106 | `wall_step_fatal` (`time.on_wall_step=fail`) | engine via detector result | no |
| RGE-TIMING-0107 | `offset_unavailable` (`ClockOffset.method=none` or unbounded uncertainty used where a bound is required) | `remote_to_local_wall_interval` | no |
| RGE-TIMING-0108 | `virtual_clock_backwards` | driver | no |
| RGE-TIMING-0109 | `virtual_driver_misuse` (second `attach_sleeper`) | driver | no |
| RGE-TIMING-0110 | `virtual_clock_unattached` (`sleep` before a sleeper is attached) | `VirtualClock.sleep*` | no |
| RGE-CONFIG-0111 | `invalid_time_config` | `TimeConfig` validation | no |
| RGE-TIMING-0120…0127 | model validation codes (§9; 0127 = `virtual_rate_invalid`, `set_wall_rate_ppm(p)` with `p ≤ −10⁶`) | model validators, driver | no |

## 8. Data structures and schemas

Conventions (DATA-MODEL §1, RG-P03-002 §7.1): every type below derives from `rg_core.model.base.Model` (frozen, `extra="forbid"`, strict); they are *embedded values* and inherit the `schema_version` (`"1.0"`) of the containing `Document`. `ClockCalibration` is the only type here that is also persisted stand-alone (inside the run manifest). Every nanosecond quantity is declared `Int64` (python `int`; JSON **decimal string** `^-?[0-9]+$`, `x-rg-format: int64`; JSON numbers are rejected, RG-P03-002 E7), counts are `Count`. Optional fields that are `None` are omitted from JSON (`exclude_none`). Validators raise `ValueError("<RGE code>: <reason>")`; because `SchemaRegistry` strips pydantic context, the **code is the prefix of the issue message** (`ValidationIssue.message`) and the wrapped error is `RGE-STORE-0020`.

### 8.1 `ClockKind` and `TimeInstant`

```python
class ClockKind(str, Enum): system = "system"; virtual = "virtual"; remote = "remote"   # remote: reserved, no Clock implements it in v1
```

| Field | Type | Constraint | Default | Description |
|---|---|---|---|---|
| `wall_ns` | Int64 | `0 ≤ v < 2⁶³` | required | ns since 1970-01-01T00:00:00Z per the local wall clock at the pairing instant. Display and cross-system joins only (rule 2). |
| `mono_ns` | Int64 | `0 ≤ v < 2⁶³` | required | local monotonic ns, arbitrary origin; the **midpoint** of the bracketing monotonic reads (§12.2). Comparable only within the same `(clock_id, epoch)`. |
| `clock_id` | str | `^(system\|virtual:[A-Za-z0-9._-]{1,64})$` | required | clock identity. |
| `read_cost_ns` | Int64 | `0 ≤ v ≤ 10⁹` | 0 | `m1 − m0` of the paired read; `\|true wall/mono pairing error\| ≤ ⌈read_cost_ns/2⌉`. |
| `epoch` | str \| None | `^[0-9a-f]{8}$` or null; **required non-null iff `clock_id == "system"`** | None | process-instance token of a `SystemClock`; additive field. A restarted process has a new epoch, so `mono_ns` of old and new epochs must not be subtracted. |

Validators: V-T1 range (`RGE-TIMING-0120`); V-T2 `clock_id` pattern (`RGE-TIMING-0122`); V-T3 epoch present iff system (`RGE-TIMING-0122`); V-T4 `read_cost_ns` range (`RGE-TIMING-0120`); V-T5 string-int parsing (`RGE-TIMING-0121`).

Derived (computed, not stored): `theta_ns = wall_ns − mono_ns` (wall-minus-mono offset, used by the guard); `pairing_error_ns = (read_cost_ns + 1) // 2`.

```json
{"wall_ns": "1791796800123456789", "mono_ns": "5000000000190", "clock_id": "system", "read_cost_ns": "380", "epoch": "a1b2c3d4"}
```

### 8.2 `ClockDomain`

| Field | Type | Constraint | Description |
|---|---|---|---|
| `id` | str | one of `local` · `target:<host>` · `idp:<prv_id>` · `event-source:<name>` | host = lower-case DNS name or bracketed IPv6/IPv4 literal, no port, ≤ 253 chars; `<prv_id>` matches `prv_[0-9A-HJKMNP-TV-Z]{26}`; `<name>` matches `[a-z0-9][a-z0-9_.-]{0,63}` |
| `kind` | `Literal["local","target","idp","event_source"]` | must agree with the `id` prefix (`local`↔`local`, `target:`↔`target`, `idp:`↔`idp`, `event-source:`↔`event_source`) | |

Validators: V-D1 grammar and prefix/kind agreement (`RGE-TIMING-0123`). Example: `{"id": "idp:prv_01M4QJ0B1J6CQ643DZVMXXQKFB", "kind": "idp"}`.

### 8.3 `RemoteInstant`

| Field | Type | Constraint | Description |
|---|---|---|---|
| `value_ns` | Int64 | `0 ≤ v < 2⁶³` | ns since epoch **as reported** (UTC). Never assumed accurate. |
| `domain` | `ClockDomain` | `kind != "local"` | the clock authority that produced the value |
| `resolution_ns` | Int64 | `1 ≤ v ≤ 10⁹` | quantisation of the reported value; truncation semantics: the true time lies in `[value_ns, value_ns + resolution_ns)` |
| `source` | enum | `http_date_header, jwt_claim, idp_event_log, idp_admin_event, caep_event, provider_api_field, operator_entry` | provenance |
| `local_receipt` | `TimeInstant` | required | when RG received it (same clock as the run) |

Validators: V-R1 `http_date_header` ⇒ `resolution_ns == 1_000_000_000` and `domain.kind ∈ {target, idp}`; V-R2 `jwt_claim` ⇒ `domain.kind == "idp"` (or `target` for an RS-issued session JWT) and `resolution_ns ≤ 1_000_000_000` (fractional NumericDate allowed); V-R3 `caep_event` ⇒ `domain.kind == "event_source"`; V-R4 `idp_event_log`/`idp_admin_event` ⇒ `domain.kind == "idp"`; V-R5 `operator_entry` ⇒ any non-`local` kind **and** the containing record's `derivation` must be `assumed` (enforced by the record owner; the validator only checks the kind); V-R6 all violations raise `RGE-TIMING-0124`.

```json
{"value_ns": "1791796807000000000", "domain": {"id": "target:rs.lab.test", "kind": "target"}, "resolution_ns": "1000000000",
 "source": "http_date_header",
 "local_receipt": {"wall_ns": "1791796807412000000", "mono_ns": "5007300000000", "clock_id": "system", "read_cost_ns": "410", "epoch": "a1b2c3d4"}}
```

### 8.4 `ClockOffset`

Estimate of `(remote_clock − local_wall_clock)`.

| Field | Type | Constraint | Description |
|---|---|---|---|
| `domain` | `ClockDomain` | `kind != "local"` | |
| `offset_ns` | Int64 | `\|v\| < 2⁶²` | positive = remote clock ahead of local wall clock |
| `uncertainty_ns` | Int64 | `0 ≤ v ≤ UNBOUNDED_NS` where `UNBOUNDED_NS = 2⁶²` | half-width `u` of the offset interval `[offset − u, offset + u]` |
| `method` | enum | `http_date_bracket, event_pair, ntp_reference, operator_declared, none` | |
| `samples` | Count | `≥ 0` | number of samples used |
| `estimated_at` | `TimeInstant` | required | when the estimate was made |

Validators (`RGE-TIMING-0125`): V-O1 `method == none` ⇒ `offset_ns == 0`, `samples == 0`, `uncertainty_ns == UNBOUNDED_NS`; V-O2 `method != none` ⇒ `uncertainty_ns < UNBOUNDED_NS`; V-O3 `http_date_bracket` ⇒ `samples ≥ 1`; V-O4 `operator_declared` ⇒ `samples == 0`. The lower bound `uncertainty_ns ≥ 500 ms` for `http_date_bracket` (STANDARDS-REFERENCE STD-027 note) is *not* validated here — it is an algorithmic property of RG-P08-002 and is tested there.

### 8.5 `TimeInterval`

| Field | Type | Constraint | Description |
|---|---|---|---|
| `start`, `end` | `TimeInstant` | same `clock_id` **and** `epoch`; `start.mono_ns ≤ end.mono_ns` | local interval |

Validators: V-I1 clock/epoch equality and V-I2 ordering both raise `RGE-TIMING-0126`. Derived: `duration_ns = end.mono_ns − start.mono_ns`; `contains(mono_ns)`; `overlaps(other)` (closed intervals).

### 8.6 `ClockCalibration` (additive; run-manifest member)

| Field | Type | Description |
|---|---|---|
| `clock_id`, `epoch` | str | identity of the calibrated clock |
| `mono_source` / `wall_source` | str | `"perf_counter_ns"`, `"time_ns"` (names, for the manifest) |
| `reported_mono_resolution_ns` | Int64 \| None | from `time.get_clock_info("perf_counter").resolution` × 10⁹, informational only (never used for the pass/fail decision) |
| `measured_mono_granularity_ns` | Int64 | smallest positive difference between successive distinct monotonic readings (§12.1) |
| `measured_wall_granularity_ns` | Int64 | same for the wall source |
| `asyncio_loop_clock_granularity_ns` | Int64 | same procedure for `time.monotonic_ns` (the source of `asyncio` loop time); informational, never rejects; exposed as `Clock.loop_granularity_ns` so the scheduler can bias its timers (RG-P03-006 §12.2) |
| `read_cost_median_ns`, `read_cost_p99_ns`, `read_cost_max_ns` | Int64 | statistics of 1 000 paired reads |
| `distinct_changes_mono` | Count | number of distinct readings observed (≥ 8 required) |
| `passed` | bool | `granularity ≤ time.max_resolution_ns ∧ no regression` |
| `reasons` | tuple[Label, ...] | machine codes, e.g. `["read_cost_p99_high"]` (warnings) or the failing code |
| `python`, `platform` | str | `sys.version_info` summary, `sys.platform` |

### 8.7 `ClockAnomaly` (additive; payload of timeline kind `clock_anomaly`, RG-P02-008)

| Field | Type | Description |
|---|---|---|
| `kind` | enum | `wall_step`, `mono_regression`, `process_restart`, `virtual_wall_jump`, `suspend_gap` |
| `detected_at` | `TimeInstant` | the instant at which the detector observed it |
| `previous` | `TimeInstant` \| None | the previous accepted observation |
| `step_ns` | Int64 | signed `Δθ = θ_now − θ_prev` (positive: wall moved forward relative to mono); 0 for `mono_regression` |
| `tolerance_ns` | Int64 | tolerance in force |
| `cumulative_divergence_ns` | Int64 | `θ_now − θ_ref` |
| `spans` | `TimeInterval` \| None | `[previous, detected_at]` — measurements overlapping this span are affected (RG-P02-006 CF-08) |

```json
{"kind": "wall_step",
 "detected_at": {"wall_ns": "1791796802330000000", "mono_ns": "102000000000", "clock_id": "system", "read_cost_ns": "400", "epoch": "a1b2c3d4"},
 "previous":    {"wall_ns": "1791796801030000000", "mono_ns": "101000000000", "clock_id": "system", "read_cost_ns": "400", "epoch": "a1b2c3d4"},
 "step_ns": "300000000", "tolerance_ns": "50000000", "cumulative_divergence_ns": "330000000"}
```

## 9. Inputs, outputs, and validation rules

| # | Rule | Code |
|---|---|---|
| VR-1 | `wall_ns`, `mono_ns`, `value_ns` ∈ `[0, 2⁶³)`; `read_cost_ns` ∈ `[0, 10⁹]` | RGE-TIMING-0120 |
| VR-2 | integer fields in JSON must be decimal strings (numbers ≥ 2⁵³ rejected) | RGE-TIMING-0121 |
| VR-3 | `clock_id`/`epoch` grammar and system⇔epoch coupling | RGE-TIMING-0122 |
| VR-4 | `ClockDomain` grammar and kind/prefix agreement | RGE-TIMING-0123 |
| VR-5 | `RemoteInstant` source/domain/resolution consistency (V-R1…V-R5) | RGE-TIMING-0124 |
| VR-6 | `ClockOffset` consistency (V-O1…V-O4) | RGE-TIMING-0125 |
| VR-7 | `TimeInterval` same clock/epoch and `start ≤ end` | RGE-TIMING-0126 |
| VR-8 | Subtraction/ordering of instants across `(clock_id, epoch)` is refused by `mono_delta`/`require_same_clock` | RGE-TIMING-0104 |
| VR-9 | Mixing `system` and `virtual:*` instants in one analysis set is refused | RGE-TIMING-0105 |
| VR-10 | `TimeConfig` ranges (§18) | RGE-CONFIG-0111 |

Inputs of the runtime operations: `Clock.now()` takes no input; `WallStepDetector.observe(TimeInstant)`; `VirtualClockDriver.advance_to(int)`. Outputs are immutable models. Validators put the code at the start of the `ValueError` message (it survives in `ValidationIssue.message`, RG-P03-002 §9 V5); `SchemaRegistry.load_*` (RG-P03-002) converts the failure to `RgError(RGE-STORE-0020)` whose `details.issues` carry the model code; instants produced by `Clock.now()` are valid by construction and re-validated only at the persistence boundary.

## 10. Detailed execution behavior

1. **Composition (engine, RG-P03-010).** `compose()` builds `SystemClock.calibrated(cfg.time)` for real runs (calibration failure aborts before any network action, state `DRAFT` unchanged) or `VirtualClock.create(run_id, epoch_wall_ns=cfg.lab.epoch_wall_ns)` for `--lab virtual`. The clock is injected into every port implementation; none reads OS time.
2. **Stamping.** Probe workers call `clock.now()` immediately before and after the wire call (RG-P05-004). Thread-safe, ≈ 2 monotonic + 1 wall reads, no allocation besides the model.
3. **Guarding.** The engine starts the guard task at run start (before `BASELINING`): every `time.guard_interval_ms` and on every probe stamp it calls `detector.observe(now)`; a returned `ClockAnomaly` is published as a timeline entry (kind `clock_anomaly`, derivation `observed`) and counted; with `time.on_wall_step="fail"` the engine raises `RGE-TIMING-0106` (the experiment moves to `FAILED` through RG-P02-007's fatal-error transition).
4. **Remote values.** Adapters/transports wrap every provider-supplied time in `RemoteInstant` (with `local_receipt = clock.now()` taken at receipt). Nothing outside RG-P08-002 and `remote_to_local_wall_interval` converts it.
5. **Virtual runs.** The `VirtualScheduler` owns the driver. Time moves only when the scheduler pops a timer (RG-P03-006 §12.6). Between pops, `now()` is constant, so every `read_cost_ns` is the configured constant and `t_recv_end − t_send_start` of an in-process probe is exactly the virtual latency the lab injected.
6. **Process restart.** A new process constructs a new `SystemClock` with a fresh `epoch`. Recovery (RG-P11-005) emits one `ClockAnomaly(kind=process_restart)` whose `previous` is the last durable instant of the old epoch; analysis treats any measurement spanning it as cross-epoch (confidence factor CF-08 caps at `low`; no `mono` subtraction is performed — only wall differences with an uncertainty of `wall_divergence_bound_ns`).
7. **`rg_core` purity.** `rg_core.time.system_clock` is the single module that touches OS time sources; it is the one allow-listed file of RG-LINT-001 (§13.3). `rg_core.time.model/ops/guard/virtual` are pure and contain no OS clock reads.

## 11. State transitions and invariants

`WallStepDetector` state: `(θ_prev, mono_prev, rc_prev, θ_ref, max_divergence, anomalies_count)`; transitions occur only inside `observe`.

| Event | From | Condition | To / output |
|---|---|---|---|
| first observation | empty | — | `θ_ref := θ_prev := θ`; no anomaly |
| observation | tracking | `\|Δθ\| ≤ tol + slew + slack` | update `θ_prev`; no anomaly |
| observation | tracking | `\|Δθ\| > tol + slew + slack` | emit `wall_step`; update `θ_prev` (θ_ref unchanged) |
| observation | tracking | `mono < mono_prev` | emit `mono_regression`; update `mono_prev` |

Invariants (testable):

- **INV-1** `TimeInstant.mono_ns` of a `SystemClock` never decreases across happens-before-ordered `now()` calls within one `(clock_id, epoch)`.
- **INV-2** For every `TimeInstant`: `0 ≤ read_cost_ns` and the wall value was sampled between the two bracketing monotonic reads; hence `|wall − wall_at(mono_ns)| ≤ ⌈read_cost_ns/2⌉` (up to wall-source granularity).
- **INV-3** For two instants obtained concurrently in different threads, `|Δmono|` ordering may invert only if the instants' read brackets overlap: `a.mono_ns > b.mono_ns` while `a` happened-before `b` is impossible.
- **INV-4** A detector never emits an anomaly when `|Δθ| ≤ tolerance_ns` and both read costs are 0 (boundary inclusive); it always emits one when `|Δθ| > tolerance_ns + ⌈(rc_prev+rc_cur)/2⌉ + slew`.
- **INV-5** `θ_ref` is fixed at the first observation; `cumulative_divergence_ns` equals `θ_now − θ_ref` exactly.
- **INV-6** `TimeInterval.start.mono_ns ≤ end.mono_ns` and equal `(clock_id, epoch)`.
- **INV-7** `RemoteInstant` and `TimeInstant` are different types; no operator on `TimeInstant` accepts a `RemoteInstant` (mypy-checked).
- **INV-8** `remote_to_local_wall_interval` returns `lo ≤ hi`; `hi − lo = 2·u + resolution_ns`.
- **INV-9** `VirtualClock.mono_ns()` changes only inside `VirtualClockDriver.advance_to`.
- **INV-10** `VirtualClock.advance_to(t)` with `t < now` raises and leaves the clock unchanged.
- **INV-11** A virtual `wall(mono)` is monotone in `mono` for `ppm > −10⁶`; a wall jump never changes `mono_ns()`.
- **INV-12** A `ClockCalibration.passed == True` implies `measured_mono_granularity_ns ≤ max_resolution_ns` and no regression was observed.

## 12. Core algorithms and pseudocode

### 12.1 Startup calibration (`calibrate`)

```
def calibrate(mono, wall, cfg, loop_mono=None) -> ClockCalibration:
    # (a) granularity + monotonicity of mono
    changes = []; prev = mono(); reads = 0
    while len(changes) < 8:
        cur = mono(); reads += 1
        if cur < prev:        raise TIMING-0102          # regression
        if cur > prev:        changes.append(cur - prev); prev = cur
        if reads > cfg.calibration_max_reads:  raise TIMING-0103   # default 20_000_000
    granularity = min(changes)
    # (b) same for wall (record only; never raises except regression is tolerated: wall may step)
    # (b') same for time.monotonic_ns → asyncio_loop_clock_granularity_ns (record only)
    # (c) read cost: 1000 × (m0=mono(); wall(); m1=mono()) → costs; median, p99, max
    passed = granularity <= cfg.max_resolution_ns          # default 1_000_000 (1 ms), NFR-PERF-002
    if not passed: raise TIMING-0101                       # details: granularity, source name
    reasons = ["read_cost_p99_high"] if p99 > cfg.max_read_cost_ns else []
```

Termination: a clock with 100 ns ticks sees a change on most reads (≤ ~20 reads); a 15.6 ms-tick clock needs ≈ 8 ticks ≈ 125 ms; a frozen clock hits the read cap after ≈ 1–2 s of CPython loop time and raises `RGE-TIMING-0103`. `min(changes)` is the smallest observed tick; on a 15.6 ms clock it is ≈ 15 600 000 ns > 1 ms ⇒ `RGE-TIMING-0101`. On a 1 ns clock the minimum is bounded below by interpreter call overhead (tens of ns), which is the effective resolution.

### 12.2 Paired read

```
def now(self) -> TimeInstant:
    m0 = self._mono()            # perf_counter_ns
    w  = self._wall()            # time_ns
    m1 = self._mono()
    cost = m1 - m0               # ≥ 0 (mono is non-decreasing)
    return TimeInstant(wall_ns=w, mono_ns=m0 + cost // 2, clock_id="system", epoch=self.epoch, read_cost_ns=cost)
```

**Worked example (paired read).** `m0 = 5 000 000 000 000`, `w = 1 791 796 800 123 456 789` (2026-10-12T09:20:00.123456789Z), `m1 = 5 000 000 000 380`. Then `cost = 380`, `mono_ns = 5 000 000 000 000 + 190 = 5 000 000 000 190`, `theta_ns = w − mono_ns = 1 791 791 800 123 456 599`, `pairing_error_ns = ⌈380/2⌉ = 190`. Interpretation: the wall value was sampled at some mono instant in `[…000, …380]`, i.e. within ±190 ns of the stored `mono_ns`; a later `θ` computed from another instant with `cost = 400` therefore carries an uncertainty of `190 + 200 = 390 ns`, which the detector adds to its tolerance (§12.3).
Why midpoint (DEC-2): storing `m0` or `m1` biases every send stamp early/late by up to `cost`; the midpoint halves the worst-case pairing error and preserves INV-1.

### 12.3 Wall-step detection

```
def observe(self, x):                      # x: TimeInstant of this detector's (clock_id, epoch)
    require same clock
    theta = x.wall_ns - x.mono_ns
    if self.prev is None: self.ref = self.prev_theta = theta; self.prev = x; return None
    if x.mono_ns < self.prev.mono_ns: anomaly = ClockAnomaly("mono_regression", ...); self.prev = x; return anomaly
    d_theta = theta - self.prev_theta
    dt_mono = x.mono_ns - self.prev.mono_ns
    slack   = (self.prev.read_cost_ns + x.read_cost_ns + 1) // 2
    allow   = self.tolerance_ns + (dt_mono * self.slew_ppm) // 1_000_000 + slack
    self.max_div = max(self.max_div, abs(theta - self.ref))
    if abs(d_theta) > allow: anomaly = ClockAnomaly("wall_step", step_ns=d_theta, tolerance_ns=self.tolerance_ns,
                                 cumulative_divergence_ns=theta - self.ref, spans=TimeInterval(self.prev, x))
    self.prev, self.prev_theta = x, theta
    return anomaly
```

**Worked example (wall step, tolerance 50 ms, slew 0).** Samples `(mono_ns, wall_ns)`:

| # | mono_ns | wall_ns | θ = wall − mono | Δθ vs previous | read costs | verdict |
|---|---|---|---|---|---|---|
| S1 | 100 000 000 000 | 1 791 796 800 000 000 000 | 1 791 796 700 000 000 000 | — | 400 | reference; no anomaly |
| S2 | 101 000 000 000 | 1 791 796 801 030 000 000 | 1 791 796 700 030 000 000 | +30 000 000 | 400 | `30 ms ≤ 50 ms + 400 ns` → none |
| S3 | 102 000 000 000 | 1 791 796 802 330 000 000 | 1 791 796 700 330 000 000 | +300 000 000 | 400 | `300 ms > 50 ms + 400 ns` → **`wall_step`, `step_ns=+300 000 000`, divergence `+330 000 000`** |
| S4 | 103 000 000 000 | 1 791 796 803 331 000 000 | 1 791 796 700 331 000 000 | +1 000 000 | 400 | none (successive comparison), but `max_divergence = 331 ms > 250 ms` ⇒ `divergence_exceeded = True` |

Gradual slewing: 700 samples spaced 1 s, each `Δθ = +0.4 ms`: no `wall_step` is ever emitted (0.4 ms ≪ 50 ms), `max_divergence` reaches 280 ms at sample 700 ⇒ `divergence_exceeded` becomes true (CF-08 info, not a step). Boundary: `Δθ = 50 000 000` with both read costs 0 ⇒ no anomaly; `Δθ = 50 000 001` ⇒ anomaly (INV-4).
Suspend/resume: on Linux `CLOCK_MONOTONIC` excludes suspend time, so a 30-minute suspend appears as `Δθ ≈ +1.8×10¹² ns` ⇒ `wall_step` (the same code path; `kind` may be refined to `suspend_gap` by the engine when `dt_mono` is small but `Δθ` is large and positive). Whether Windows QPC includes suspend time is not asserted (§26 A-4); both outcomes are detected by this procedure.

### 12.4 Virtual clock evolution

**Worked example.** `epoch_wall_ns = 1 791 792 000 000 000 000` (08:00:00Z), `start_mono = 0`. At `mono = 3 600 000 000 000` (virtual 1 h): `wall = 1 791 795 600 000 000 000` (09:00:00Z). `jump_wall(+2 s)`: anchor ← `(1 791 795 602 000 000 000, 3 600 000 000 000, 0)`. At `mono = 3 700 000 000 000`: `wall = 1 791 795 602 000 000 000 + 100 000 000 000 = 1 791 795 702 000 000 000`. `set_wall_rate_ppm(+500)` at that instant, then at `mono = 4 700 000 000 000` (+1000 s): `wall = 1 791 795 702 000 000 000 + (1 000 000 000 000 × 1 000 500) // 1 000 000 = 1 791 795 702 000 000 000 + 1 000 500 000 000 = 1 791 796 702 500 000 000`. A detector fed once per virtual second emits exactly one `wall_step(+2 000 000 000 ns)` at the first observation after the jump (and sets `divergence_exceeded`, since 2 s > 250 ms); during the +500 ppm phase it sees `Δθ = +0.5 ms` per second and emits nothing further.

### 12.5 Epoch rule

`SystemClock.epoch` is generated once per process. Two `TimeInstant`s with equal `clock_id` but different `epoch` are **not** mono-comparable. `mono_delta` raises `RGE-TIMING-0104`; callers that must compare across a restart use wall values and add `wall_divergence_bound_ns` as uncertainty (RG-P11-005, RG-P08-004 confidence).

### 12.6 `remote_to_local_wall_interval`

```
def remote_to_local_wall_interval(r, off):
    if off.method == none or off.uncertainty_ns >= UNBOUNDED_NS: raise TIMING-0107
    centre = r.value_ns - off.offset_ns                       # remote time expressed on the local wall clock
    lo = centre - off.uncertainty_ns                          # remote value is a truncation: true ∈ [v, v + res)
    hi = centre + off.uncertainty_ns + r.resolution_ns
    return (lo, hi)                                           # hi − lo = 2u + resolution (INV-8)
```

**Worked example.** `Date: Mon, 12 Oct 2026 09:20:07 GMT` ⇒ `value_ns = 1 791 796 807 000 000 000`, `resolution = 10⁹`; offset estimate `offset_ns = +120 000 000` (remote ahead by 120 ms), `uncertainty_ns = 600 000 000`. `centre = 1 791 796 806 880 000 000`; interval `[1 791 796 806 280 000 000, 1 791 796 808 480 000 000]` — width `2.2 s = 2·0.6 s + 1 s`. The result is *always* an interval; comparing it to a local probe instant is the job of RG-P08-002/-004, and any timing verdict narrower than this width is forbidden (TV-08, SV-047).

## 13. Internal functions, methods, or service operations

### 13.1 Module layout (`rg_core/time/`)

| Module | Contents |
|---|---|
| `model.py` | pydantic models §8, `UNBOUNDED_NS`, int64-string codec hooks |
| `ops.py` | `mono_delta`, `require_same_clock`, `remote_to_local_wall_interval`, `format_iso` |
| `system_clock.py` | `SystemClock` (**only** module reading OS time; RG-LINT-001 allow-listed) |
| `virtual.py` | `VirtualClock`, `VirtualClockDriver` |
| `guard.py` | `WallStepDetector` |
| `calibrate.py` | `calibrate(mono, wall, cfg)` (takes sources by injection) |
| `config.py` | `TimeConfig` (§18) |

### 13.2 Internal signatures

```python
def _paired_read(mono: Callable[[], int], wall: Callable[[], int]) -> tuple[int, int, int]: ...   # (wall, mono_mid, cost)
def _percentile(sorted_vals: Sequence[int], p: int) -> int: ...                                    # nearest-rank
def _theta(x: TimeInstant) -> int: ...                                                             # wall − mono
def _virtual_wall(anchor: _Anchor, mono: int) -> int: ...                                          # §7.2 formula
def _ulid_ms(clock: Clock) -> int: ...                                                             # wall_ns // 1_000_000, used by IdFactory (RG-P03-002)
```

### 13.3 RG-LINT-001 — direct-time-call ban (policy owned here; tooling owned by RG-P03-005 §12.7)

**Policy.** In the production packages `rg_core`, `rg_probe`, `rg_idp`, `rg_stbridge` and `revocationgap.{engine,service,store,config}` no code may read an OS clock or wait on one directly; every instant comes from `Clock.now()/wall_ns()/mono_ns()` and every wait from `Clock.sleep*`/`Scheduler` (ADR-0006). RG-P03-005 §12.7 specifies the implementation that enforces this policy — ruff `flake8-tidy-imports` `banned-api` (`TID251`, alias-aware; verified there with ruff 0.17.0) plus the stdlib-AST tool `tools/rglint.py` — together with the scope, allow-list mechanism, message format and fixtures `tests/lint/fixtures/lint001/`. This spec fixes the **ban list** the tools must realise and the allow-list entries that belong to the time model:

| Sub-rule | Banned expression | Realised by |
|---|---|---|
| RG-LINT-001 (base) | `time.time`, `time.time_ns`, `time.monotonic`, `time.monotonic_ns`, `time.perf_counter`, `time.perf_counter_ns`, `time.sleep`, `time.localtime`, `time.gmtime`, `datetime.datetime.now/utcnow/today`, `datetime.date.today`, `asyncio.sleep`, `asyncio.wait_for`, `asyncio.timeout`, `asyncio.timeout_at`, `threading.Timer`, `uuid.uuid1` | RG-P03-005 §12.7 `banned-api` table (as written there) |
| RG-LINT-001.b | calls named `call_later`/`call_at` (loop timers) | rglint `.b` (RG-P03-005) |
| **RG-LINT-001.c** (addition, CCR-4) | `time.process_time*`, `time.clock_gettime*`, `time.get_clock_info`, `loop.time()`, `datetime.datetime.fromtimestamp` without an explicit `tz`, `signal.alarm`, `signal.setitimer`, `sched.scheduler` | add to `banned-api` and rglint |
| **RG-LINT-001.d** (addition, CCR-4) | string literals that are SQL and contain `CURRENT_TIMESTAMP`, `CURRENT_DATE`, `datetime('now'`, `strftime('%s'` — times in SQL are bound parameters produced by the `Clock` | rglint (AST over string constants passed to `execute*`/module-level SQL constants) |

**Allow-list entries owned by this element:** `src/rg_core/time/system_clock.py` — the single reader of OS time (`perf_counter_ns`, `time_ns`, `get_clock_info`, `asyncio.sleep` in `SystemClock.sleep*`); every other module of `rg_core.time` (including `calibrate.py`, which receives its sources by injection) is checked. The scheduler's loop-timer allow-list (`.b`) is owned by RG-P03-006 (§13). A suppression anywhere else is itself a finding (RG-P03-005 §12.7).
**Fixtures added by this element:** `tests/lint/fixtures/lint001/bad_clock_extras.py` (one line per sub-rule `.c`/`.d`, incl. alias forms `from time import process_time as pt`, `import datetime as d; d.datetime.fromtimestamp(0)`, SQL `"... datetime('now') ..."`) and `ok_clock_extras.py` (bound-parameter SQL, `fromtimestamp(x, tz=timezone.utc)`).

## 14. Error handling and failure recovery

| Failure | Detection | Handling | Recovery | Code |
|---|---|---|---|---|
| Monotonic source coarser than 1 ms (e.g. a 15.6 ms Windows tick clock) | calibration §12.1 | refuse to construct `SystemClock.calibrated`; engine stays `DRAFT` | operator fixes platform/Python; config `time.max_resolution_ns` may be *raised* only to ≤ 50 ms with an audited override recorded in the manifest | RGE-TIMING-0101 |
| Monotonic source goes backwards | calibration or `strict_mono` | abort run | none (hardware/VM defect) | RGE-TIMING-0102 |
| Source does not advance | read cap | abort | none | RGE-TIMING-0103 |
| Wall step during run | `WallStepDetector` | `clock_anomaly` entry; confidence cap; with `on_wall_step=fail` the run fails | re-run | RGE-TIMING-0106 (fail mode only) |
| Cross-clock subtraction attempted | `mono_delta` | raise | caller bug fix | RGE-TIMING-0104 / 0105 |
| Virtual clock moved backwards | driver | raise, clock unchanged | scheduler bug fix | RGE-TIMING-0108 |
| `sleep` on virtual clock without scheduler | `VirtualClock.sleep` | raise | compose with scheduler | RGE-TIMING-0110 |
| Invalid persisted time record | model validators on load | reject record (partial documents never partially loaded) | restore from backup / re-run | RGE-TIMING-0120…0126 (wrapped as STORE by the loader) |
| Remote time with unbounded offset used as bound | `remote_to_local_wall_interval` | raise | use `method` with a bound or drop claim | RGE-TIMING-0107 |

Partial-failure semantics: calibration is all-or-nothing; the detector never raises on a *value* anomaly (it returns the anomaly), only on a programming error (clock mismatch).

## 15. Security requirements and trust boundaries

- **TM-28 (time-source manipulation).** Durations use one monotonic clock (§12.2); wall time is paired with a recorded pairing error; wall steps are detected (§12.3) and logged; virtual/real mixing is refused by `require_same_clock` (`RGE-TIMING-0105`) and `clock_id` is part of every instant (DATA-MODEL §9.8). The run manifest records `ClockCalibration` and clock kind (FR-EVD-007).
- **Hostile remote times.** `RemoteInstant` values are untrusted data (target `Date`, JWT claims, provider logs): validators bound ranges; a remote time never becomes a `TimeInstant`; conversions yield intervals and `RGE-TIMING-0107` on unbounded offsets (TV-24 support).
- **No secrets** appear in any type of this module.
- **Deterministic ids and replay.** Under `VirtualClock`, `IdFactory` (RG-P03-002) derives ULID time bits from `wall_ns` so replays produce identical ids (NFR-REL-002).
- **Lint as control.** RG-LINT-001 prevents a contributor or plugin author in the checked packages from re-introducing an unrecorded time source (R-007, TM-25 spirit); plugins are trusted code (TM-22) and are *not* sandboxed from calling `time` — documented residual.

## 16. Concurrency, asynchronous behavior, and resource ownership

- `SystemClock` is stateless apart from `epoch`/`calibration` (immutable); reads are lock-free and thread-safe.
- `VirtualClock` is **loop-thread only**; `VirtualClockDriver` is owned by exactly one `VirtualScheduler`; `advance_to` from another thread is a bug (guarded by RG-P03-006 thread check).
- `WallStepDetector` has a single owner (the engine guard coroutine plus probe-stamp feed serialised through the guard's queue); it holds O(1) state.
- No locks, executors, sockets or files are owned by this module. Cancellation: `sleep*` propagate `CancelledError` immediately; no partial state.
- Bounds: `ClockAnomaly` records per run are capped at `time.max_anomalies` (default 1 000); beyond the cap the detector keeps counting (`anomalies_count`) but stops emitting entries and sets `divergence_exceeded`.

## 17. Performance and resource requirements

Proposals (not measurements); validated by benchmark `BM-TIME-1` (RG-P12-004).

| Budget | Value (proposal) | Rationale | Validation |
|---|---|---|---|
| `now()` cost, Linux/Windows CPython 3.12 | median ≤ 2 µs, p99 ≤ 20 µs | three clock reads + one model construction use the unvalidated constructor path (`model_construct`) after calibration; stamps sit adjacent to the wire call and `read_cost_ns` must stay ≪ 1 ms | TST-RG-P02-001-04 (asserts p99 `read_cost_ns` < 1 ms), `BM-TIME-1` |
| Calibration time | ≤ 250 ms on a 100 ns–1 ns tick clock; ≤ 2 s worst case before `0103` | §12.1 termination argument | TST-RG-P02-001-05 |
| `observe()` cost | ≤ 5 µs | O(1) integer arithmetic | `BM-TIME-1` |
| Memory | `ClockAnomaly` list ≤ 1 000 × ≈ 1 KiB | §16 cap | TST-RG-P02-001-09 |

## 18. Configuration and defaults

`[time]` table (RG-P03-003 parses; this spec fixes semantics). Precedence: defaults < `revocationgap.toml` < env < CLI. Invalid values raise `RGE-CONFIG-0111` at load.

| Field | Type | Default | Range | Env var | Notes |
|---|---|---|---|---|---|
| `wall_step_tolerance_ns` | int | 50 000 000 | 1 000 000 … 5 000 000 000 | `RG_TIME_WALL_STEP_TOLERANCE_NS` | frozen default (DATA-MODEL §2.2 rule 4) |
| `wall_divergence_bound_ns` | int | 250 000 000 | ≥ tolerance … 3 600 000 000 000 | `RG_TIME_WALL_DIVERGENCE_BOUND_NS` | run flag threshold (TM-28) |
| `wall_slew_allowance_ppm` | int | 0 | 0 … 500 | `RG_TIME_WALL_SLEW_ALLOWANCE_PPM` | for sparse sampling only |
| `guard_interval_ms` | int | 1000 | 100 … 60 000 | `RG_TIME_GUARD_INTERVAL_MS` | guard-task cadence |
| `on_wall_step` | enum `record\|fail` | `record` | | `RG_TIME_ON_WALL_STEP` | `fail` ⇒ `RGE-TIMING-0106` |
| `max_resolution_ns` | int | 1 000 000 | 1 … 50 000 000 | `RG_TIME_MAX_RESOLUTION_NS` | NFR-PERF-002; values > 1 ms are recorded as overrides |
| `max_read_cost_ns` | int | 1 000 000 | 1 000 … 100 000 000 | `RG_TIME_MAX_READ_COST_NS` | warning threshold only |
| `calibration_max_reads` | int | 20 000 000 | 100 000 … 200 000 000 | `RG_TIME_CALIBRATION_MAX_READS` | bounds `0103` latency |
| `strict_mono` | bool | false | | `RG_TIME_STRICT_MONO` | per-read regression check |
| `max_anomalies` | int | 1000 | 10 … 100 000 | `RG_TIME_MAX_ANOMALIES` | §16 |
| `lab.epoch_wall_ns` | int | 1 791 792 000 000 000 000 | valid int64 | `RG_LAB_EPOCH_WALL_NS` | virtual clock epoch (owned by RG-P09-001, read here) |

## 19. Logging, observability, and evidence requirements

Events (structured, via RG-P03-004; names stable): `time.calibrated` {`clock_id`, `epoch`, `granularity_ns`, `read_cost_p99_ns`, `passed`}, `time.calibration_failed` {`code`, `granularity_ns`}, `time.clock_anomaly` {`kind`, `step_ns`, `cumulative_divergence_ns`}, `time.divergence_exceeded` {`max_divergence_ns`}. Metrics: `time_read_cost_ns` histogram (sampled 1 in 1000 stamps), `time_wall_steps_total`. Evidence: `ClockCalibration` and the clock kind enter the run manifest (FR-EVD-007); each `ClockAnomaly` becomes a timeline entry (RG-P02-008) with `derivation=observed`. Redaction: none required (no secrets); hostnames in `ClockDomain.id` are not redacted (they are target identifiers already in scope).

## 20. Platform compatibility

- **Linux:** `perf_counter_ns` ≈ `CLOCK_MONOTONIC` (excludes suspend; suspend shows up as a wall step); `time_ns` = `CLOCK_REALTIME`. Granularity typically ≈ 1 ns (effective ≈ call overhead).
- **Windows:** `perf_counter_ns` uses QueryPerformanceCounter (documented CPython behaviour); `time.monotonic` is **not** used because on CPython < 3.13 its tick is ≈ 15.6 ms (PRD NFR-PERF-002, tag U — falsifier: TST-RG-P02-001-06 run on a Windows runner). `time_ns` granularity may be ≈ 100 ns–15.6 ms (recorded, not rejected: wall is display only).
- **macOS:** both sources available; calibration decides acceptability; no special-casing.
- Encoding: ISO strings are ASCII; all JSON UTF-8. No file or lock use. Signals: none.
- `datetime.fromtimestamp` is banned without `tz`; display code uses `format_iso` (UTC only), so local timezone and DST never enter any record.

## 21. Edge cases and invalid inputs

| # | Case | Expected behaviour |
|---|---|---|
| E-1 | `read_cost_ns = 0` (virtual or ultra-fast clock) | valid; `pairing_error_ns = 0` |
| E-2 | `m1 == m0` and wall differs from last | valid; no special handling |
| E-3 | `wall_ns` smaller than previous instant's `wall_ns` | valid instant; the detector emits `wall_step` if `\|Δθ\|` exceeds the allowance |
| E-4 | JSON number ≥ 2⁵³ for `mono_ns` | rejected `RGE-TIMING-0121` |
| E-5 | `clock_id = "virtual:run 1"` (space) | rejected `RGE-TIMING-0122` |
| E-6 | system instant with `epoch = null` | rejected `RGE-TIMING-0122` |
| E-7 | `http_date_header` with `resolution_ns = 1` | rejected `RGE-TIMING-0124` |
| E-8 | `ClockOffset(method=none, uncertainty_ns=5)` | rejected `RGE-TIMING-0125` |
| E-9 | `TimeInterval` with `start.mono_ns > end.mono_ns` | rejected `RGE-TIMING-0126` |
| E-10 | instants from epochs `a1b2c3d4` and `0f0f0f0f` subtracted | `RGE-TIMING-0104` |
| E-11 | virtual instant minus system instant | `RGE-TIMING-0105` |
| E-12 | `sleep(0)` / `sleep(-5)` | one cooperative yield, returns |
| E-13 | `advance_to(t)` with `t` equal to current | no-op, no error |
| E-14 | `set_wall_rate_ppm(-1_000_000)` | rejected `RGE-TIMING-0127` (wall would stop/reverse; INV-11 needs `ppm > −10⁶`) |
| E-15 | detector fed instants out of mono order | `mono_regression` anomaly, state updated |
| E-16 | process restarts mid-experiment | new epoch; `process_restart` anomaly; no cross-epoch `mono` subtraction |

## 22. Unit and integration test requirements

| ID | Condition (inputs / fixtures) | Expected observation |
|---|---|---|
| TST-RG-P02-001-01 | Paired-read worked example with injected sources (`m0=5 000 000 000 000`, wall `1 791 796 800 123 456 789`, `m1=…380`) | `mono_ns = 5 000 000 000 190`, `read_cost_ns = 380`, `theta_ns = 1 791 791 800 123 456 599` |
| TST-RG-P02-001-02 | Hypothesis: arbitrary non-decreasing mono source sequences, 1 000 `now()` calls sequentially | INV-1 holds; `read_cost_ns ≥ 0`; `m0 ≤ mono_ns ≤ m1` |
| TST-RG-P02-001-03 | 8 threads × 10⁴ `now()` calls; record (thread-local order, global happens-before via barrier) | no happens-before-ordered inversion (INV-3) |
| TST-RG-P02-001-04 | Real `SystemClock` on CI runner: 10⁵ `now()` | p99 `read_cost_ns` < 1 000 000; all mono non-decreasing |
| TST-RG-P02-001-05 | Calibration with fake source ticking every 15 600 000 ns | `RGE-TIMING-0101` with `granularity_ns ≈ 15 600 000`; with 100 ns ticks → passed; frozen source → `RGE-TIMING-0103`; decreasing source → `RGE-TIMING-0102` |
| TST-RG-P02-001-06 | Calibration of the real `perf_counter_ns` on Linux, Windows and macOS runners | `passed == True`; granularity ≤ 1 ms (falsifier of assumption A-1/A-2) |
| TST-RG-P02-001-07 | Wall-step worked example S1…S4 | exactly one `wall_step` at S3 with `step_ns=+300 000 000`, `cumulative_divergence_ns=330 000 000`; `divergence_exceeded` after S3 |
| TST-RG-P02-001-08 | Boundary: `Δθ = 50 000 000` (costs 0) vs `50 000 001`; with costs 400/400 and `Δθ = 50 000 400` vs `50 000 401` | no anomaly / anomaly; no anomaly / anomaly (INV-4) |
| TST-RG-P02-001-09 | Slew: 700 samples at +0.4 ms each; then 2 000 anomalies injected | no `wall_step` in the slew phase; `divergence_exceeded` first true at sample 626 (250.4 ms > 250 ms); emission capped at `max_anomalies`, counter continues |
| TST-RG-P02-001-10 | VirtualClock worked example (§12.4) with jump and +500 ppm | wall values equal the stated integers exactly; `mono_ns()` unchanged by `jump_wall` (INV-11) |
| TST-RG-P02-001-11 | VirtualClock safety: `advance_to` backwards; second `attach_sleeper`; `sleep` before attach | `RGE-TIMING-0108`, `0109`, `0110`; clock state unchanged |
| TST-RG-P02-001-12 | Model validators: table of invalid values for each VR-1…VR-7 (e.g. E-4…E-9) | each fails with an issue whose message starts with the stated code (and `RGE-STORE-0020` when loaded through the registry) |
| TST-RG-P02-001-13 | Round-trip property (Hypothesis) of all models through canonical JSON | equality; integers serialised as strings; no float appears |
| TST-RG-P02-001-14 | `mono_delta`/`require_same_clock` across epochs and across system/virtual | `RGE-TIMING-0104` / `0105` |
| TST-RG-P02-001-15 | `remote_to_local_wall_interval` worked example; property: `hi − lo = 2u + resolution`; `method=none` | exact stated interval; INV-8; `RGE-TIMING-0107` |
| TST-RG-P02-001-16 | RG-LINT-001.c/.d fixtures (`bad_clock_extras.py`, `ok_clock_extras.py`, §13.3) through `tools/rglint.py`; the base-rule fixtures are RG-P03-005 TST-18 | exactly one finding per bad line (alias forms included), zero on the ok file |
| TST-RG-P02-001-17 | Whole-tree run of `ruff check` (TID251) and `tools/rglint.py --select RG-LINT-001` over `rg_core`, `rg_probe`, `rg_idp`, `rg_stbridge`, `revocationgap.{engine,service,store,config}` (CI gate) | zero findings; the only allow-listed file is `system_clock.py` |
| TST-RG-P02-001-18 | Determinism: two runs of a scripted virtual timeline (same seed, same driver calls) | byte-identical sequence of `TimeInstant` JSON |

## 23. Mocking and test fixtures

- **Injected sources:** `SystemClock(mono_source=…, wall_source=…)` with `FakeMono(sequence | tick_ns)` and `FakeWall` generators in `rg_core.testing.time`.
- **VirtualClock** itself is the primary double (with `VirtualScheduler` from RG-P03-006 for sleep tests).
- **Fixtures:** `fixtures/time/wallstep_s1_s4.json` (worked example samples), `fixtures/time/slew_700.json`, `fixtures/time/invalid_instants.json` (table for TST-12), `tests/lint/fixtures/rg001/` (§13.3).
- No network, no files; every test except 04/06/17 runs without real clock dependence.

## 24. Objective acceptance criteria

- **AC-RG-P02-001-01** `SystemClock.now()` returns instants whose `mono_ns` is the midpoint of the bracketing monotonic reads, whose `read_cost_ns` equals `m1 − m0`, and whose results never decrease along a happens-before chain, including under 8 concurrent threads (verified by TST-RG-P02-001-01, TST-RG-P02-001-02, TST-RG-P02-001-03, TST-RG-P02-001-04).
- **AC-RG-P02-001-02** Startup calibration rejects a monotonic source with measured granularity above 1 ms (`RGE-TIMING-0101`), rejects regressing and frozen sources (`0102`, `0103`), and passes the real `perf_counter_ns` on Linux, Windows and macOS CI runners (verified by TST-RG-P02-001-05, TST-RG-P02-001-06).
- **AC-RG-P02-001-03** The wall-step detector flags exactly the samples whose `|Δθ|` exceeds tolerance + slew + pairing slack (boundary-exact), reports the signed step and cumulative divergence, ignores slow slew, and caps emission at `max_anomalies` (verified by TST-RG-P02-001-07, TST-RG-P02-001-08, TST-RG-P02-001-09).
- **AC-RG-P02-001-04** `VirtualClock` time advances only through its driver; the wall function reproduces the specified integers exactly including jump and ppm injection; misuse raises `RGE-TIMING-0108/0109/0110` without state change (verified by TST-RG-P02-001-10, TST-RG-P02-001-11, TST-RG-P02-001-18).
- **AC-RG-P02-001-05** Every model validator in §8/§9 rejects its invalid inputs with the specified code, and all models round-trip through canonical JSON with int64 values as strings (verified by TST-RG-P02-001-12, TST-RG-P02-001-13).
- **AC-RG-P02-001-06** Instants from different epochs or clock kinds cannot be subtracted (`RGE-TIMING-0104/0105`), and a `RemoteInstant` converts to local time only as an interval of width `2u + resolution` (verified by TST-RG-P02-001-14, TST-RG-P02-001-15).
- **AC-RG-P02-001-07** The RG-LINT-001 tooling (RG-P03-005 §12.7 plus the additions of §13.3) reports every banned time/sleep construct, including aliased imports and SQL time literals, and the repository tree has zero findings outside `system_clock.py` (verified by TST-RG-P02-001-16, TST-RG-P02-001-17).

## 25. Research sources and engineering rationale

Sources: DATA-MODEL §2.2/§4/§9; ADR-0006, ADR-0014; PRD FR-TEMP-001…003, NFR-PERF-002; THREAT-MODEL TM-28, TV-08, TV-24; STANDARDS-REFERENCE STD-027/035 (`Date` resolution 1 s; evidence tag S) and SV-047/SV-048; TECHNICAL-FEASIBILITY R-007; SCHEMATHESIS-INTEGRATION U7 (`Response` has no timestamps — RG stamps itself).

- **DEC-1 Time source.** Chosen: `time.perf_counter_ns` for mono, `time.time_ns` for wall. Rejected: `time.monotonic[_ns]` (15.6 ms tick on Windows/Python < 3.13, NFR-PERF-002), `time.time` float (precision loss ≈ 240 ns at 1.8×10⁹ s), `datetime` objects (timezone footguns). Verification: TST-05/06.
- **DEC-2 Midpoint pairing.** Chosen: `mono_ns = m0 + cost//2`. Rejected: `m0` (biases early), `m1`, storing both (doubles size of every observation, NFR-PERF-007 ≤ 2 KiB). Verification: TST-01/02.
- **DEC-3 Process epoch field.** Chosen: additive `epoch` so mono values from different processes cannot be compared. Rejected: encoding the epoch inside `clock_id` (would change a frozen field's grammar); persisting a boot id (platform-specific). Verification: TST-14, E-16.
- **DEC-4 Successive-sample step detection plus a cumulative divergence flag.** Chosen over cumulative-only (cannot distinguish a step from long slew) and over slew-model fitting (needs sampling density guarantees). Verification: TST-07/08/09.
- **DEC-5 Lint = ruff `TID251` + `tools/rglint.py` (RG-P03-005).** Chosen because RG-P03-005 verified `TID251` alias handling with ruff 0.17.0 and already specifies the AST tool; this spec adds the sub-rules `.c`/`.d` that `banned-api` cannot express (SQL literals) instead of introducing a second linter. Rejected: a separate `lint_rg001.py` (duplicate tool), runtime monkey-patching of `time` (hidden global state). Verification: TST-16/17.
- **DEC-6 Own `VirtualClock`.** Rejected `freezegun`/`time-machine` (patch process-global time functions, unsafe with worker threads, do not influence `perf_counter` consumers consistently, and contradict "no hidden global state"); rejected SimPy `Environment.now` (cannot back real asyncio code; ADR-0006/REPO-ASSESSMENT §2).
- **DEC-7 `RemoteInstant` conversion yields an interval with truncation semantics** (`[v, v+res)`), because `Date` and NumericDate truncate (STD-027, SV-047). Verification: TST-15.
- **DEC-8 Tolerance default 50 ms** is frozen by DATA-MODEL; the pairing slack and optional slew allowance are refinements that keep the default behaviour when read costs are sub-µs.

## 26. Remaining uncertainties or assumptions

| # | Assumption | Evidence tag | Falsifying test |
|---|---|---|---|
| A-1 | `time.perf_counter_ns` granularity ≤ 1 ms on all supported platforms and CPython 3.11–3.14 | CPython docs claim; not measured here (U) | TST-RG-P02-001-06 (per-platform CI) |
| A-2 | `time.monotonic` on Windows CPython < 3.13 has ≈ 15.6 ms tick (PRD NFR-PERF-002 marks it U) | U | TST-RG-P02-001-05 with the real source on a Windows runner (informational; the design does not depend on it) |
| A-3 | `TID251` resolves aliased imports for the base ban list (asserted by RG-P03-005 A-4; verified there with ruff 0.17.0); the additions `.c`/`.d` rely on rglint's AST walk | V (author-run in RG-P03-005) / design | TST-RG-P02-001-16 (additions) and RG-P03-005 TST-18 (base) |
| A-4 | Whether Windows/macOS monotonic clocks include system-suspend time is unspecified here; the guard detects either behaviour as a wall step | U | manual VM suspend/resume test on each OS (`TST-RG-P12-0xx`, owner P12-002) |
| A-5 | `epoch` collisions (4 random bytes) are negligible for one workspace | I | property test: 10⁶ constructions, zero collisions expected; collision would only cause a missed cross-epoch refusal |
| A-6 | Midpoint pairing error bound `⌈cost/2⌉` holds when the OS clock call is not preempted between the three reads (preemption inflates `cost`, never hides error) | I | TST-RG-P02-001-04 with injected 5 ms stall asserts `read_cost_ns ≥ 5 ms` |
| A-7 | HTTP `Date` offset uncertainty ≥ 0.5 s is enforced by RG-P08-002, not here | I | RG-P08-002 test suite |

## 27. Maintainability, portability, and future extension requirements

- **Versioning:** `SCH-TIME` is `1.0`; adding optional fields is minor; changing int64-string wire form or `TimeInstant` semantics is major with a RG-P11-006 migration. `ClockKind.remote` is reserved for a future `RemoteClockView`.
- **Extension points:** additional `Clock` implementations (e.g. a PTP/GPS-disciplined clock) implement the same port and must pass the Clock conformance kit (`rg_core.testing.clock_conformance`, TST-01/02/03/10 parametrised); additional `RemoteInstant.source` values require a DATA-MODEL entry.
- **Reuse:** `rg_core.time` has no RevocationGap-specific dependency and is reusable as an embeddable "measurement clock" library (master-prompt reusable components: confidence/evidence analysis library).
- **Deprecation:** none yet; banned-call list in §13.3 is data (`rg001_rules.toml`) so new patterns can be added without code changes.
- **Portability:** adding a platform requires only a calibration pass; no platform branches exist in the model code.
