---
id: RG-P03-006
title: "Scheduler abstraction and clock injection"
phase: "03"
package: core
module_ids: [MOD-CORE-SCHEDULER]
status: DRAFT
depends_on: [RG-P02-001, RG-P03-005]
requirements: [NFR-PERF-001, NFR-PERF-003, NFR-PERF-002, NFR-REL-002, NFR-REL-003, NFR-TEST-003, NFR-PLAT-001, NFR-MNT-001, FR-LAB-001, FR-LAB-004, FR-EXP-006, FR-TEMP-003]
interfaces_defined: [IF-CORE-SCHEDULER]
interfaces_used: [IF-CORE-CLOCK, IF-CORE-AIO, IF-CORE-ERR]
schemas_defined: []
schemathesis_touchpoints: []
---

# RG-P03-006 — Scheduler abstraction and clock injection

> Scope: the `Scheduler` port (`IF-CORE-SCHEDULER`) with its two implementations — `AsyncioScheduler` (real time) and `VirtualScheduler` with its **virtual-time event loop** (deterministic lab time) — the `ScheduledResult`/`TimerHandle` types, lateness recording, bounded timer count, cancellation, run-to-quiescence `drain`, the composition helpers `SystemRuntime`/`VirtualRuntime`, and the clock-fault injection hooks used by `rg_lab`. Clock reads and `VirtualClock` are RG-P02-001; task scopes, deadlines and error types are RG-P03-005; *what* is scheduled and when (probe schedules, backoff) is RG-P05-008.

## 1. Module identifier and name

| Item | Value |
|---|---|
| Element | RG-P03-006 — Scheduler abstraction and clock injection |
| Package / modules | `rg_core.scheduler`: `timer_queue.py` (shared core), `asyncio_scheduler.py`, `virtual.py` (`VirtualScheduler`, `VirtualEventLoop`, `VirtualSelector`), `runtime.py` (`SystemRuntime`, `VirtualRuntime`), `faults.py` (`FaultPlan`); port `rg_core.ports.time.Scheduler` |
| Module id | `MOD-CORE-SCHEDULER` |
| Interface | `IF-CORE-SCHEDULER` (`Scheduler`, `TimerHandle`, `ScheduledResult`) |
| Schemas | none persisted (`FaultPlan` is a lab-facing input model, §8.4) |
| Error block | `0060–0069` (RG-P03-005 §8.3) |

## 2. Phase and requirement references

| Requirement | Realised by |
|---|---|
| NFR-PERF-001 p95 scheduling lateness ≤ 25 ms, p99 ≤ 100 ms at ≤ 50 in-flight probes, recorded on every observation | `ScheduledResult.lateness_ns`, never-early guarantee, loop-granularity bias (§12.2), benchmark BM-SCHED-1 |
| NFR-PERF-002 timing precision | all due times are `perf_counter`-based `mono_ns` of the injected `Clock` (RG-P02-001); loop time is used only to *wake*, never to stamp |
| NFR-PERF-003 ≥ 200 concurrent in-flight probes | bounded timer/task count (default 10 000), O(log n) heap |
| NFR-REL-002 determinism; NFR-TEST-003 no wall-clock waits | `VirtualScheduler` + `VirtualEventLoop`: fixed `(due_mono_ns, submission_seq)` order, no real time |
| NFR-REL-003 bounded retries/queues | `sched.max_pending_timers`, `RGE-TIMING-0060` |
| FR-LAB-001 deterministic virtual-time lab (hours of token lifetime without wall waiting) | §12.4–12.6, worked example WE2 |
| FR-LAB-004 clock skew/jumps injected deterministically | `inject_wall_jump`, `inject_wall_rate`, `FaultPlan` (§7.3, §12.8) |
| FR-EXP-006 observation horizon/stop rules are timers | `call_at`/`run_at` on the run scope; cancellation §10.5 |
| FR-TEMP-003 wall-step visibility | jump injection exercises the detector of RG-P02-001 without touching timer order (INV-8) |
| NFR-PLAT-001, NFR-MNT-001 | §20 platform behaviour; `rg_core.scheduler` performs no I/O of its own (loop timers only) |

Decisions/risks: ADR-0006 (injectable `Clock`/`Scheduler`, own virtual time), ADR-0014 (lab dual mode), ADR-0004 (one event loop per run, thread offload), TECHNICAL-FEASIBILITY §2 ("own small Scheduler port with real and virtual implementations"; SimPy not usable for real I/O), R-016 (thread-offload jitter ⇒ lateness recorded), RG-P03-005 note on loop-timer granularity (§20). Threat/validity: TV-08 (stamps from the monotonic clock only), TM-28 (clock jumps), TM-34 (bounded resources).

## 3. Purpose and user/security value

Every post-revocation probe is sent at a *scheduled* instant, and the width of the exposure interval includes the gap between the last accepted and first denied send (RG-P02-006 §12.2). A scheduler that fires early, drifts, silently drops timers or runs in a nondeterministic order corrupts that interval; one that cannot be made deterministic makes the product untestable (R-003, R-016). This module provides (a) a real-time scheduler that **never fires early** by the same clock that stamps observations and records its own lateness, and (b) a virtual-time implementation that runs an entire 24-hour token-lifetime experiment — including third-party code that calls `asyncio.sleep` — deterministically in milliseconds, in the same asyncio event-loop model as production, so that the lab verifies the *real* engine and not a re-implementation.

## 4. Explicit responsibilities

- **RESP-1** Implement `Scheduler` (`call_at`, `run_at`, `drain` + additive `call_after`, `run_after`, `pending`, `stats`, `close`, `bind_scope`) per INTERFACE-CONTRACTS §3 for real and virtual time.
- **RESP-2** Define `ScheduledResult` and `TimerHandle` semantics, lateness definition and recording.
- **RESP-3** Implement `AsyncioScheduler` on `loop.call_at` with mono→loop mapping computed at arming time (no accumulated drift), the never-early guard, the coarse-timer bias, bounded batches and error isolation.
- **RESP-4** Implement `VirtualScheduler`/`VirtualEventLoop`/`VirtualSelector`: deterministic `(due_mono_ns, submission_seq)` order, time advance only at loop idleness, run-to-quiescence `drain`, deadlock and runaway detection, real-I/O/blocking-work detection.
- **RESP-5** Decide and justify how the virtual-time asyncio loop is built, comparing alternatives including SimPy (§25 DEC-1).
- **RESP-6** Define cancellation semantics (timer handles, `run_at` futures, scope cancellation, `drain`, `close`) and the bounded timer count.
- **RESP-7** Provide `SystemRuntime`/`VirtualRuntime` composition helpers so the engine's composition root can bind clock+scheduler+loop by `clock_kind`.
- **RESP-8** Provide the clock-fault injection hooks (`inject_wall_jump`, `inject_wall_rate`, `FaultPlan`) and the lateness-injection hook (`LatenessModel`) consumed by `rg_lab` (RG-P09-001/-004).

## 5. Out-of-scope responsibilities

| Excluded item | Owner |
|---|---|
| `Clock`, `VirtualClock`, `VirtualClockDriver`, calibration, wall-step detection | RG-P02-001 |
| `RunScope`, `Deadline`, executors, queues, abort protocol, `RgError` | RG-P03-005 |
| Probe schedules (dense→backoff, boundary-focused), stop rules, probe concurrency | RG-P05-008, RG-P05-014 |
| Rate limiting, retry backoff delays | RG-P05-009 |
| Event bus delivery | RG-P03-007 |
| Fault injection other than clock jumps/lateness (event reorder/duplication, response delays, connection drops, 429) | RG-P09-004 (builds on these hooks) |
| Mock services/IdP, in-process transports | RG-P09-002/-003 |
| Lab architecture, `--lab virtual` CLI wiring | RG-P09-001, RG-P10-001 |
| Experiment state machine timeouts evaluation | RG-P02-007 (`due_timeout`) — the engine arms them as timers through this port |
| Lint tooling (allow-list mechanics) | RG-P03-005 §12.7 (this spec states the entries it needs, §13.3) |

## 6. Dependencies and prerequisites

- RG-P02-001: `Clock`, `SystemClock` (incl. `loop_granularity_ns`), `VirtualClock`, `VirtualClockDriver` (`advance_to`, `jump_wall`, `set_wall_rate_ppm`, `attach_sleeper`), RGE-TIMING-01xx.
- RG-P03-005: `RunScope` (`spawn`, `token`, `on_drain`), `TaskRole`, `Deadline`, `wrap_unexpected`, `RgError`/`TimingError`/`InternalError`, error registry (block 0060–0069), lint rules RG-LINT-001/-002/-003.
- Python ≥ 3.11 (`asyncio.Runner(loop_factory=…)`, `TaskGroup`); stdlib `asyncio`, `selectors`, `heapq`, `itertools`, `math`. No third-party dependency (ADR-0003; aiotools/async-solipsism are not used, §25).
- The composition root (RG-P03-010) chooses the runtime by `Experiment.clock_kind` / `--lab virtual`.

## 7. External and internal interfaces

### 7.1 The port — IF-CORE-SCHEDULER (`rg_core.ports.time`)

```python
T = TypeVar("T")

@dataclass(frozen=True, slots=True)
class ScheduledResult(Generic[T]):                       # frozen contract: .value, .intended_ns, .started_ns
    value: T
    intended_ns: int                                     # the due_mono_ns requested by the caller (never changed, even if the timer was delayed)
    started_ns: int                                      # clock.mono_ns() read as the first statement of the scheduled coroutine
    finished_ns: int                                     # additive: clock.mono_ns() when the coroutine returned
    name: str
    @property
    def lateness_ns(self) -> int: ...                    # started_ns - intended_ns  (≥ 0 by INV-1)
    @property
    def duration_ns(self) -> int: ...                    # finished_ns - started_ns

class TimerHandle(Protocol):                             # frozen contract
    def cancel(self) -> None: ...                        # sync, idempotent, no effect after the timer fired
    @property
    def due_mono_ns(self) -> int: ...
    @property
    def name(self) -> str: ...                           # additive
    @property
    def cancelled(self) -> bool: ...                     # additive

class Scheduler(Protocol):                               # frozen contract + additive members
    clock: Clock
    def call_at(self, due_mono_ns: int, callback: Callable[[], Awaitable[None] | None], *, name: str) -> TimerHandle: ...
    def run_at(self, due_mono_ns: int, coro_factory: Callable[[], Awaitable[T]], *, name: str,
               role: TaskRole = TaskRole.scheduler) -> "asyncio.Future[ScheduledResult[T]]": ...
    async def drain(self, *, timeout_ns: int | None = None) -> None: ...

    # additive
    def call_after(self, delay_ns: int, callback: ..., *, name: str) -> TimerHandle: ...             # due = clock.mono_ns() + delay_ns
    def run_after(self, delay_ns: int, coro_factory: ..., *, name: str, role: TaskRole = ...) -> "asyncio.Future[ScheduledResult[T]]": ...
    def bind_scope(self, scope: RunScope) -> None: ...                                                # once; RGE-INTERNAL-0064 if rebinding
    def pending(self) -> tuple[TimerInfo, ...]: ...                                                    # snapshot sorted by (due, seq)
    def stats(self) -> SchedulerStats: ...
    def close(self) -> None: ...                                                                       # idempotent; also registered with scope.on_drain
```

Semantics shared by both implementations:

- **Time base.** `due_mono_ns` is an absolute value of `clock.mono_ns()` (same `clock_id`/epoch). A due time in the past (≤ now) is valid and dispatches at the next opportunity; lateness is recorded honestly.
- **Never early (INV-2).** A callback/coroutine is started only when `clock.mono_ns() ≥ due_mono_ns`.
- **Order.** Timers are dispatched in ascending `(due_mono_ns, submission_seq)`; `submission_seq` is a per-scheduler counter incremented by every `call_at`/`run_at`/`call_after`/`run_after` (INV-3). This is the **tie-break contract** of SYSTEM-ARCHITECTURE §5.
- **`call_at` callbacks** run synchronously on the loop thread at dispatch; if a callback returns an awaitable it is run as a task through `RunScope.spawn(role=scheduler, critical=False)`. Exceptions in callbacks never kill the scheduler (§14).
- **`run_at`** returns a loop-owned `asyncio.Future` that resolves with `ScheduledResult` when the coroutine returns, with the coroutine's `RgError` (or `wrap_unexpected(exc)` for foreign exceptions; `RGE-INTERNAL-0002`) when it raises, and is **cancelled** when the future is cancelled, the timer handle path is cancelled, or the scope cancels. `coro_factory` is called exactly once, at dispatch, inside the spawned task.
- **Thread-safety.** All methods must be called on the loop thread that owns the scheduler (`RGE-INTERNAL-0064` otherwise); worker threads hand work to the loop with `call_soon_threadsafe` (RG-P03-005 executors). `TimerHandle.cancel()` is loop-thread-only as well.
- **Idempotency.** `cancel`, `close` idempotent; `call_at`/`run_at` are not (each call creates a timer).
- **Cancellation of the caller.** Cancelling a task that awaits a `run_at` future cancels that future (and therefore the timer or the running coroutine).

### 7.2 Implementations and composition

```python
class AsyncioScheduler:                                  # real time; kind = "system"
    def __init__(self, clock: Clock, scope: RunScope, *, config: SchedulerConfig = SchedulerConfig(),
                 on_late: Callable[[str, int, int], None] | None = None) -> None
        # must be constructed inside the running loop (RGE-INTERNAL-0064); clock.kind must be system (RGE-INTERNAL-0065)

class VirtualScheduler:                                  # virtual time; kind = "virtual"
    def __init__(self, clock: VirtualClock, driver: VirtualClockDriver, *, config: SchedulerConfig = SchedulerConfig(),
                 lateness_model: LatenessModel | None = None) -> None
    def attach(self, loop: "VirtualEventLoop") -> None                                       # by VirtualRuntime
    def add_quiescence_guard(self, guard: Callable[[], str | None]) -> None                 # returns a reason string while blocking work is in flight (e.g. a real thread-pool call)
    def next_due_ns(self) -> int | None
    # fault/lateness hooks for rg_lab (§12.8)
    def inject_wall_jump(self, at_mono_ns: int, delta_ns: int, *, name: str = "fault.wall_jump") -> TimerHandle
    def inject_wall_rate(self, at_mono_ns: int, ppm: int, *, name: str = "fault.wall_rate") -> TimerHandle
    def schedule_faults(self, plan: "FaultPlan") -> tuple[TimerHandle, ...]
    def set_lateness_model(self, model: LatenessModel | None) -> None

LatenessModel = Callable[[TimerInfo], int]               # extra delay in ns (≥ 0) applied once, at the timer's first due dispatch

class VirtualRuntime:                                    # composition of clock + driver + scheduler + loop (lab, tests)
    clock: VirtualClock; driver: VirtualClockDriver; scheduler: VirtualScheduler; scope: RunScope | None
    @classmethod
    def create(cls, run_id: str, *, epoch_wall_ns: int, start_mono_ns: int = 0, config: SchedulerConfig = SchedulerConfig(),
               lateness_model: LatenessModel | None = None) -> "VirtualRuntime"
    def new_loop(self) -> "VirtualEventLoop"
    def run(self, main: Callable[["VirtualRuntime"], Awaitable[T]], *, scope_name: str = "run",
            budget: CancelBudget | None = None) -> T                                         # sync entry: asyncio.Runner(loop_factory=self.new_loop) + RunScope + main

class SystemRuntime:                                     # real runs (composition root)
    clock: SystemClock; scheduler: AsyncioScheduler
    @classmethod
    async def open(cls, time_config: TimeConfig, scope: RunScope, *, config: SchedulerConfig = SchedulerConfig()) -> "SystemRuntime"   # calibrates the clock (RG-P02-001), builds the scheduler
```

`VirtualRuntime.run` executes: `with asyncio.Runner(loop_factory=self.new_loop) as r: r.run(_main())` where `_main` enters `RunScope(scope_name, clock, budget)`, calls `scheduler.bind_scope(scope)`, registers `scope.on_drain(scheduler.close)` and awaits `main(self)`. A second `run` on the same `VirtualRuntime` is rejected (`RGE-INTERNAL-0064`): a runtime is single-use so a run's virtual timeline is never reused.

### 7.3 Error codes (block 0060–0069; names for the registry `ERROR_CODES`)

| Code | Name | Category | Retryable | Raised by |
|---|---|---|---|---|
| `RGE-TIMING-0060` | `TIMER_CAPACITY_EXCEEDED` | TIMING | no | `call_at/run_at/…` when `pending + running ≥ sched.max_pending_timers`; details `capacity`, `name` |
| `RGE-TIMING-0061` | `VIRTUAL_DEADLOCK` | TIMING | no | virtual loop idle with no timer, no drain waiter, main unfinished; details `tasks` (≤ 20 names), `virtual_now_ns` |
| `RGE-TIMING-0062` | `VIRTUAL_RUNAWAY` | TIMING | no | virtual events > `virtual_max_events`, > `virtual_max_events_per_instant` at one instant, or virtual span > `virtual_max_span_ns`; details `limit`, `value` |
| `RGE-INTERNAL-0063` | `VIRTUAL_REAL_IO_DETECTED` | INTERNAL | no | strict mode: real fds registered (sockets/pipes) or a quiescence guard reports blocking work when the loop would advance virtual time |
| `RGE-INTERNAL-0064` | `SCHEDULER_MISUSE` | INTERNAL | no | wrong thread/no running loop, use after `close`, rebinding the scope, `run_at` before `bind_scope`, second `VirtualRuntime.run`, nested `drain` from a scheduled task of the same scheduler in virtual mode |
| `RGE-INTERNAL-0065` | `SCHEDULER_CLOCK_MISMATCH` | INTERNAL | no | `AsyncioScheduler` with a virtual clock, `VirtualScheduler` with a system clock, `due` of another `clock_id`/epoch (when supplied as `TimeInstant`) |
| `RGE-INTERNAL-0066` | `INVALID_TIMER_ARGUMENT` | INTERNAL | no | `due` not an `int` in `[0, 2⁶²)`, delay < 0, `name` not matching `^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$`, `coro_factory` not callable |
| `RGE-INTERNAL-0067` | `VIRTUAL_LOOP_UNSUPPORTED` | INTERNAL | no | the platform cannot construct the selector-based loop (self-test failure at `VirtualRuntime.create`) |
| `RGE-CONFIG-0068` | `SCHEDULER_CONFIG_INVALID` | CONFIG | no | `SchedulerConfig` out of range |

Reused (not owned): `RGE-TIMING-0001 DEADLINE_EXCEEDED` (from `drain(timeout_ns)`), `RGE-INTERNAL-0002 UNEXPECTED_EXCEPTION` (foreign exception in a scheduled coroutine/callback), `RGE-INTERNAL-0004 SCOPE_MISUSE`, RG-P02-001 `RGE-TIMING-0104/0108/0109/0110`.

## 8. Data structures and schemas

### 8.1 `TimerInfo`, `SchedulerStats`

`TimerInfo` (frozen dataclass): `name`, `due_mono_ns`, `intended_mono_ns` (= original due), `seq`, `kind` (`"call"|"run"`), `role` (`TaskRole`), `lateness_applied` (bool).
`SchedulerStats`: `pending`, `running`, `dispatched_total`, `cancelled_total`, `errors_total`, `max_lateness_ns`, `lateness_buckets` (counts for `≤1 ms, ≤5 ms, ≤25 ms, ≤100 ms, ≤1 s, >1 s`), `wakeups_total`, `early_wakeups_total` (guard re-arms), `virtual_events_total` (virtual only).

### 8.2 `SchedulerConfig` (frozen pydantic `Model`; parsed by RG-P03-003)

| Field | Type | Default | Range | Meaning |
|---|---|---|---|---|
| `max_pending_timers` | int | 10 000 | 16 … 1 000 000 | bound on pending timers **plus** running scheduled coroutines |
| `max_dispatch_batch` | int | 256 | 1 … 100 000 | max timers dispatched per wake before yielding to the loop (fairness) |
| `late_warn_ns` | int | 100 000 000 | 0 … 60·10⁹ | lateness above which `on_late` fires and `scheduler.timer_late` is logged |
| `bias_loop_granularity` | bool | true | | add `Clock.loop_granularity_ns` to loop wake times (§12.2) |
| `compaction_min_cancelled` | int | 1000 | 16 … 1 000 000 | heap compaction trigger (with > 50 % cancelled) |
| `virtual_strict_io` | bool | true | | refuse to advance virtual time while real fds/blocking work exist |
| `virtual_max_events` | int | 10 000 000 | 1000 … 10⁹ | total dispatched virtual events |
| `virtual_max_events_per_instant` | int | 100 000 | 100 … 10⁷ | events at one virtual instant (zero-delay loops) |
| `virtual_max_span_ns` | int | 315 360 000 000 000 000 | 1 … 2⁶² | max virtual time advanced (≈ 10 years) |

### 8.3 Internal timer entry

`_Timer{due, seq, intended, name, kind, role, callback | coro_factory, future, cancelled, lateness_applied}` with `__lt__` on `(due, seq)`.

### 8.4 `FaultPlan` (lab input; secret-free; JSON/YAML in fixtures, RG-P09-005)

`FaultPlan(Model)`: `faults: tuple[TimedFault, …]` (≤ 1000); `TimedFault`: `at_mono_ns: Int64` (≥ 0), `fault: WallJump | WallRate` (discriminated on `kind`); `WallJump{kind: "wall_jump", delta_ns: Int64}` (|delta| ≤ 10¹⁵); `WallRate{kind: "wall_rate", ppm: Int}` (−999 999 … +10⁶; ppm ≤ −10⁶ rejected by RG-P02-001 `RGE-TIMING-0127`).

```json
{"faults": [
  {"at_mono_ns": "3600000000000", "fault": {"kind": "wall_jump", "delta_ns": "2000000000"}},
  {"at_mono_ns": "3700000000000", "fault": {"kind": "wall_rate", "ppm": 500}}]}
```

## 9. Inputs, outputs, and validation rules

| # | Rule | Code |
|---|---|---|
| VR-1 | `due_mono_ns` is an `int`, `0 ≤ due < 2⁶²`; `delay_ns ≥ 0`; `name` matches the grammar; callables are callable | RGE-INTERNAL-0066 |
| VR-2 | calls happen on the owning loop thread inside a running loop; scheduler not closed | RGE-INTERNAL-0064 |
| VR-3 | `pending + running < max_pending_timers` before accepting a timer | RGE-TIMING-0060 |
| VR-4 | scheduler/clock kind pairing (`AsyncioScheduler`↔system, `VirtualScheduler`↔virtual) | RGE-INTERNAL-0065 |
| VR-5 | `run_at` only after `bind_scope` (AsyncioScheduler binds at construction) | RGE-INTERNAL-0064 |
| VR-6 | `SchedulerConfig` ranges and `lateness_warn ≥ 0` | RGE-CONFIG-0068 |
| VR-7 | `LatenessModel` returns an `int ≥ 0` (violations raise at dispatch) | RGE-INTERNAL-0066 |
| VR-8 | virtual limits (`events`, `events per instant`, `span`) | RGE-TIMING-0062 |
| VR-9 | virtual idle with no work and no waiter | RGE-TIMING-0061 |
| VR-10 | strict I/O: no real fds beyond the loop's wake-up pair and no guard-reported work at an advance | RGE-INTERNAL-0063 |

## 10. Detailed execution behavior

### 10.1 `call_at` / `run_at` (both implementations)

1. Validate (VR-1…VR-5, VR-3). 2. `entry = queue.push(due, seq=next(counter), …)`; for `run_at` create `future = loop.create_future()` and register `future.add_done_callback(_on_future_done)`. 3. Real: `_rearm()` (§12.2). Virtual: nothing to arm (the selector consults `next_due()`, §12.5). 4. Return the handle (`TimerHandle` over the entry) or the future.

### 10.2 Dispatch (real) — see §12.2/12.3

On wake: re-read `clock.mono_ns()`; dispatch every timer with `due ≤ now` in `(due, seq)` order up to `max_dispatch_batch`; re-arm. For `run_at`: `RunScope.spawn(self._runner(entry), name=entry.name, role=entry.role, critical=False)`; the runner stamps `started_ns` as its first statement.

### 10.3 Lateness recording

`started_ns − intended_ns` is `ScheduledResult.lateness_ns`; the probe runner stores it as `Observation.dispatch_lateness_ns` (RG-P02-006) and derives `scheduling_lateness_ns = t_send_start.mono − intended_at.mono` itself. The scheduler additionally keeps the bucket histogram and calls `on_late(name, intended_ns, started_ns)` when above `late_warn_ns` (RG-P03-007 publishes `scheduling_lateness` metric events from this hook).

### 10.4 Virtual dispatch — see §12.5

### 10.5 Cancellation

- `TimerHandle.cancel()` marks the entry cancelled (lazy deletion), decrements `pending`, and for a `run_at` entry cancels its future. A cancelled entry is never dispatched.
- Cancelling the `run_at` **future** before dispatch cancels the timer; after dispatch it cancels the running task (`task.cancel()`); the coroutine receives native `CancelledError`.
- **Scope cancellation** (`RunScope.cancel`): scheduler tasks (role `scheduler`/`probe`) are front tasks and are cancelled by the scope. After `scope.token.cancelled` the scheduler **still fires `call_at` callbacks** (sync, cheap — they wake sleepers and sinks so drain cannot hang) but **does not start new `run_at` coroutines**: their futures are cancelled. `close()` (registered with `scope.on_drain`) cancels every remaining timer.
- `drain()` is cancellable; cancellation leaves timers untouched. `close()` is idempotent.

### 10.6 `drain`

Real: waits until `pending = 0 ∧ running = 0` (event-based, no polling); with `timeout_ns` it races a `Deadline` and raises `RGE-TIMING-0001`. Virtual: *run to quiescence* (§12.6).

## 11. State transitions and invariants

Scheduler: `NEW → BOUND → CLOSED` (`bind_scope` once; `close` terminal; calls after `CLOSED` raise `RGE-INTERNAL-0064`). Timer entry: `PENDING → DISPATCHED → (RUNNING → DONE | FAILED | CANCELLED)` or `PENDING → CANCELLED`.

- **INV-1** For every dispatched timer `started_ns ≥ intended_ns`; `ScheduledResult.lateness_ns ≥ 0`.
- **INV-2 (never early)** No callback/coroutine starts while `clock.mono_ns() < due_mono_ns` (real: guard §12.2; virtual: dispatch only after the clock reaches `due`).
- **INV-3 (order)** Dispatch order is the ascending order of `(due_mono_ns, submission_seq)`; timers with equal due run in submission order (FIFO); a timer submitted during dispatch with `due ≤ now` runs after all earlier-submitted timers of the same instant.
- **INV-4 (bounded)** `pending + running ≤ max_pending_timers` at all times.
- **INV-5** A cancelled timer's callback/factory is never invoked; `cancel()` is idempotent and has no effect after dispatch.
- **INV-6 (virtual time moves only at idleness)** `VirtualClock.mono_ns()` changes only inside `VirtualSelector.select` when the loop has no ready handle and no due scheduler timer (§12.5); between two selector idle points all tasks observe one constant `now`.
- **INV-7 (virtual determinism)** Given the same program, seed, timer submissions and lateness model, the sequence `(name, intended_ns, started_ns)` is identical across runs, Python 3.11–3.14 and operating systems.
- **INV-8 (wall independence)** Injected wall jumps/rates never change timer order, `due`, `started_ns` or `lateness_ns` (timers are mono-based).
- **INV-9** In virtual mode `lateness_ns` equals exactly the lateness model's value (0 without a model): `started_ns = due + extra`.
- **INV-10** `drain()` (virtual) returns only when no scheduler timer is pending and the loop is idle; it never returns while a due timer exists.
- **INV-11** No `rg_core.scheduler` module except `asyncio_scheduler.py` calls `loop.call_at/call_later`; none calls `time.*`, `asyncio.sleep`, `create_task`/`ensure_future` (RG-LINT-001/-003).
- **INV-12** Virtual-mode third-party timers (`asyncio.sleep`, `loop.call_later`) share the virtual timeline; at one instant scheduler timers are dispatched **before** loop timers.

## 12. Core algorithms and pseudocode

### 12.1 `TimerQueue` (shared core, `timer_queue.py`)

```
class TimerQueue:
    heap: list[_Timer]; seq = itertools.count(1); pending = 0; cancelled_in_heap = 0
    push(due, kind, payload...) -> _Timer:     e = _Timer(due, next(seq), ...); heappush(heap, e); pending += 1; return e
    peek_due() -> int | None:                  discard cancelled tops (lazy deletion); return heap[0].due if heap else None
    pop() -> _Timer:                           e = heappop(heap); pending -= 1; return e
    cancel(e):                                 if not e.cancelled and e.state is PENDING: e.cancelled = True; pending -= 1; cancelled_in_heap += 1; maybe_compact()
    maybe_compact():                           if cancelled_in_heap > max(compaction_min_cancelled, len(heap)//2): heap = [x for x in heap if not x.cancelled]; heapify(heap); cancelled_in_heap = 0
```
`_Timer.__lt__` compares `(due, seq)`; because `seq` is unique, the heap order is a **strict total order** (no ties) — the determinism of INV-3 does not depend on `heapq`'s unspecified handling of equal keys.

**Worked example WE1 (tie-break and past-due ordering).** Virtual time starts at 0 (seconds). Submissions: `A` due 5 (seq 1), `B` due 5 (seq 2), `C` due 3 (seq 3). At `t = 5`, `A`'s callback submits `D` due 5 (seq 4) and `E` due 4 (seq 5; already in the past). Heap keys `(due, seq)`: `C(3,3)`, `A(5,1)`, `B(5,2)`, then after `A` runs `D(5,4)` and `E(4,5)`. Pops: `C@3`, `A@5`, then `E(4,5) < B(5,2) < D(5,4)` ⇒ **`E@5`, `B@5`, `D@5`**. Order `C, A, E, B, D`; started instants `3, 5, 5, 5, 5`; lateness `E` = 5 − 4 = 1 s, all others 0. Rule: ties are FIFO by submission; a past-due timer sorts by its *original* due, so it precedes later-due timers even if submitted afterwards.

### 12.2 `AsyncioScheduler` arming, wake and the never-early guard

```
def _rearm(self):
    top = queue.peek_due()
    if top is None:                      cancel wake; armed_for = None; return
    if self.wake is not None and self.armed_for == top: return          # already armed for this due
    cancel wake
    delay_ns = top - clock.mono_ns()
    if delay_ns <= 0:                    self.wake = loop.call_soon(self._on_wake)                 # past due: no bias
    else:                                self.wake = loop.call_at(loop.time() + (delay_ns + self.bias_ns)/1e9, self._on_wake)   # bias = Clock.loop_granularity_ns
    self.armed_for = top

def _on_wake(self):
    self.wake = None; self.armed_for = None; stats.wakeups += 1
    n = 0
    while True:
        top = queue.peek_due(); now = clock.mono_ns()
        if top is None or top > now:     break                        # guard: never dispatch early
        if n >= cfg.max_dispatch_batch:  loop.call_soon(self._on_wake); return          # yield for fairness; keeps order
        self._fire(queue.pop(), now); n += 1
    if n == 0 and queue.peek_due() is not None: stats.early_wakeups += 1               # the loop clock fired early relative to perf_counter
    self._rearm()
```

The mono→loop mapping is **recomputed at every arming** from the current `(clock.mono_ns(), loop.time())` pair, so clock-source drift between `perf_counter` and the loop's `time.monotonic` is never accumulated: an early wake re-arms for the *remaining* delay. The bias exists because `asyncio` treats a timer as due when `when ≤ loop.time() + clock_resolution`, i.e. it may fire up to one resolution **early**; on Windows with CPython < 3.13 the resolution is ≈ 15.6 ms (NFR-PERF-002, tag U) and without the bias the guard would re-arm repeatedly in a busy loop. With `bias = loop_granularity_ns` the loop cannot consider the timer due before `loop.time() ≥ due_loop`, so the wake is at worst one tick *late* — which is recorded as lateness.
**Worked example WE3.** Windows/CPython 3.11, `loop_granularity_ns = 15 625 000`. Now `mono = 10.000000 s`, `loop.time() = 5000.0`; `call_at(due = 10.200000 s)`: `delay = 0.2 s`, `when = 5000.0 + 0.2 + 0.015625 = 5000.215625`. The loop's tick floors `loop.time()`; the timer becomes ready when `floor(loop.time()) + 0.015625 ≥ 5000.215625`, i.e. no earlier than real `10.2 s` and at most one tick (15.6 ms) later ⇒ `started ∈ [10.200, 10.2156] s`, lateness ∈ [0, 15.6 ms] — within NFR-PERF-001 (p95 ≤ 25 ms). On Linux `loop_granularity_ns ≈ 1`, bias negligible. If instead the loop clock ran 50 ppm slow, a 1 h timer would wake ≈ 180 ms early relative to `perf_counter`: the guard sees `top > now`, counts `early_wakeups`, re-arms for the remaining 180 ms + bias, never dispatching early.

### 12.3 Dispatch of a `run_at` entry

```
def _fire(self, e, now):
    if e.kind == "call":
        try:  r = e.callback()
        except Exception as x: self._record_error(e.name, x); return
        if inspect.isawaitable(r): self.scope.spawn(_await(r), name=e.name, role=scheduler, critical=False)
    else:
        if self.scope.token.cancelled: e.future.cancel(); return                  # no new coroutines after cancellation
        task = self.scope.spawn(self._runner(e), name=e.name, role=e.role, critical=False); self.running[e.seq] = task
async def _runner(self, e):
    started = clock.mono_ns()                                                      # first statement
    stats.record_lateness(started - e.intended); if started - e.intended > cfg.late_warn_ns: on_late(...)
    try:   value = await e.coro_factory()
    except asyncio.CancelledError: e.future.cancel(); raise
    except RgError as x:  e.future.set_exception(x) if not e.future.done()
    except Exception as x: e.future.set_exception(wrap_unexpected(x, where="scheduler.run_at:" + e.name)) if not e.future.done()
    else: e.future.set_result(ScheduledResult(value, e.intended, started, clock.mono_ns(), e.name)) if not e.future.done()
    finally: self.running.pop(e.seq, None); self._maybe_idle()
```
`critical=False` makes `RunScope` record unexpected failures in `scope.failures` rather than cancelling siblings; the caller observes the failure through the future.

### 12.4 Virtual-time loop: construction and the alternatives (decision DEC-1)

`VirtualEventLoop(asyncio.SelectorEventLoop)` constructed as `super().__init__(selector=VirtualSelector(real=selectors.DefaultSelector(), …))` with `time()` overridden to `clock.mono_ns() / 1e9`. `VirtualSelector` implements `selectors.BaseSelector` by delegation; only `select(timeout)` is special. No private attribute of the loop is patched; the loop calls `self._selector.select(timeout)` exactly as in production. Alternatives (full comparison in §25): (B) a purpose-built cooperative runner, (C) SimPy, (D) time-patching libraries, (E) third-party virtual-time loops.

### 12.5 `VirtualSelector.select(timeout)` — the only place virtual time advances

```
def select(self, timeout):                      # timeout: seconds | None | 0   (asyncio passes None when it has nothing scheduled and nothing ready)
    events = self.real.select(0)                # real wake-ups (call_soon_threadsafe self-pipe, signals) take priority
    if events: return events
    if self.sched.dispatch_due() > 0:           # due scheduler timers: run callbacks / spawn tasks in (due, seq) order
        return []                               # new work is ready: let the loop run it before time may advance
    if timeout == 0: return []                  # loop still has ready handles: not idle
    # ---- the loop is idle (nothing ready): time may advance ----
    self._check_strict_io()                     # RGE-INTERNAL-0063 if real fds / blocking work
    nxt = self.sched.next_due()
    target = None if timeout is None else clock.mono_ns() + ceil(timeout * 1e9)       # next loop timer (asyncio.sleep, call_later…)
    if nxt is not None and (target is None or nxt <= target): target = nxt              # scheduler timers use exact integers
    if target is None:                          # nothing will ever happen again
        if self.drain_waiters: wake them all; return []                                  # run-to-quiescence reached (§12.6)
        raise RGE-TIMING-0061 VIRTUAL_DEADLOCK(tasks=[names of not-done tasks])
    driver.advance_to(max(target, clock.mono_ns()))                                      # INV-6: the only advance
    self._count_instant(); check limits (RGE-TIMING-0062)
    self.sched.dispatch_due()                   # timers due at the new instant (loop timers fire on the loop's own pass)
    return []
```
Properties: (1) *Exactness*: scheduler timers are dispatched at precisely `due` (integers; no float round-trip) ⇒ `started_ns = due`. (2) *Order at one instant*: scheduler timers dispatch inside `select`; the tasks they wake are queued by `call_soon`/`Future.set_result` **before** the loop moves due loop-timers to its ready queue, so scheduler consequences precede third-party timers (INV-12). (3) *No same-instant re-arm loop*: a timer is never re-queued for the instant it just fired at (the hazard documented for another virtual-time loop, async-solipsism issue #10149, where a handler that fires exactly on time is treated as early and re-submitted forever); here the dispatch condition `due ≤ clock.mono_ns()` is evaluated on integers and the loop's own early-fire tolerance is irrelevant because scheduler timers are **not** loop timers. (4) *Float safety*: `loop.time() = mono_ns/1e9` is monotone; `ceil(timeout·1e9)` converts the loop's timer delay back to ns, so a loop timer is never skipped (advance ≥ requested).
`dispatch_due()` pops while `next_due ≤ now`, applying the **lateness model** once per timer (a timer whose model returns `extra > 0` is re-queued with `due' = due + extra`, same `seq`, `intended` unchanged, flag `lateness_applied`), and counts events against the runaway limits.

### 12.6 `drain()` (virtual: run to quiescence)

```
async def drain(self, *, timeout_ns=None):
    fut = loop.create_future(); selector.drain_waiters.append(fut)
    await fut                                   # completes only when the selector finds: no ready handle, no scheduler timer, no loop timer
    if self.errors: raise first error as RgError(RGE-INTERNAL-0002, details.count = n)       # callbacks that raised during the run
    if strict and self.running_forever(): note stuck coroutines (names) in stats — not an error (e.g. workers blocked on queues)
```
`timeout_ns` is accepted for protocol symmetry and ignored (virtual time cannot "time out" in wall time; the runaway limits bound it). Calling `drain` from a coroutine **spawned by this scheduler** is allowed (it simply waits); a second concurrent `drain` shares the quiescence event. A virtual run in which `main` is still unfinished at quiescence and nobody awaits `drain` raises `RGE-TIMING-0061` (deadlock) with the names of the blocked tasks (`asyncio.all_tasks()`).
**Worked example WE2 (24-hour token lifetime).** `VirtualRuntime.create("run-24h", epoch_wall_ns=1 791 792 000 000 000 000)`; the engine schedules one probe per second for 24 h: `for k in 0…86 399: scheduler.run_at(k·10⁹, probe, name=f"probe.{k}")`, a revocation at `t = 3600 s`, and `await scheduler.drain()`. Result: 86 400 dispatches in `(due, seq)` order; final `clock.mono_ns() = 86 399 000 000 000` (the last due) — nothing sleeps for wall time; `clock.wall_ns() = 1 791 792 000 000 000 000 + 86 399 000 000 000 = 1 791 878 399 000 000 000` (08:00:00Z + 23:59:59); every `ScheduledResult.lateness_ns = 0`. Wall-clock runtime is a benchmark (BM-SCHED-2), not a claim.

### 12.7 `VirtualClock.sleep` / `sleep_until` under the virtual scheduler

`VirtualScheduler` attaches `_sleeper(target_mono_ns)` to the driver: `fut = loop.create_future(); h = self.call_at(target, lambda: fut.done() or fut.set_result(None), name="clock.sleep"); try: await fut; finally: h.cancel()`. A cancelled sleeper therefore leaves no timer behind; `sleep(0)` yields once. Code that uses `asyncio.sleep` (third-party libraries; banned in RG code by RG-LINT-001) also runs on the virtual timeline because the loop's own `time()` is virtual.

### 12.8 Lateness and clock-fault injection

**Lateness model.** `LatenessModel(info: TimerInfo) -> int` is called once per timer at its first due dispatch. **Worked example WE4.** A probe timer due `100.000 s`, model returns `120 000 000 ns`: the entry is re-queued at `100.120 s` (same `seq`), dispatched there; `ScheduledResult(intended_ns = 100 000 000 000, started_ns = 100 120 000 000)`, `lateness_ns = 120 000 000`; the probe runner then records `scheduling_lateness_ns = t_send_start.mono − intended_at.mono = 120 000 000` (RG-P02-006 TST-16; CF-06 notes it, threshold 100 ms).
**Wall jump / rate.** `inject_wall_jump(at, d)` = `call_at(at, lambda: driver.jump_wall(d))`; `inject_wall_rate(at, ppm)` = `call_at(at, lambda: driver.set_wall_rate_ppm(ppm))`; both are ordinary timers ordered by `(at, seq)` — a fault scheduled before a probe at the same instant (lower `seq`) takes effect before that probe stamps `Clock.now()`. **Worked example WE5.** Plan of §8.4 on a run with probes at `t = 3598 … 3602 s` (1 s spacing): at `3600 s` the wall jumps +2 s; probe timers still start at exactly `3598, 3599, 3600, 3601, 3602 s` (INV-8); the probe at 3600 s (submitted after the fault) stamps `wall_ns = base + 3600 s + 2 s`; the detector of RG-P02-001 fed at each probe sees `Δθ = +2 000 000 000 ns` once (`wall_step`), none before/after; the experiment's exposure arithmetic (mono) is unchanged and its confidence drops per CF-08.

### 12.9 `SystemRuntime.open`

`clock = SystemClock.calibrated(time_config)` (RG-P02-001 §12.1; failure aborts before any network action), `scheduler = AsyncioScheduler(clock, scope)`, `scope.on_drain(scheduler.close)`. Refuses a `time_config` that selects the virtual clock (`RGE-INTERNAL-0065`).

## 13. Internal functions, methods, or service operations

### 13.1 Signatures

```python
def _validate_due(due: object) -> int: ...                       # RGE-INTERNAL-0066
def _check_thread(loop: asyncio.AbstractEventLoop) -> None: ...  # RGE-INTERNAL-0064
def _fire(self, e: _Timer, now: int) -> None: ...                # §12.3
async def _runner(self, e: _Timer) -> None: ...                  # §12.3
def _record_error(self, name: str, exc: Exception) -> None: ...  # bounded list (100), wrap_unexpected, metrics; virtual: re-raised by drain()
def _check_strict_io(self) -> None: ...                          # real fds beyond the wake-up pair; guards
def _count_instant(self, now: int) -> None: ...                  # runaway counters
def _maybe_idle(self) -> None: ...                               # real: set the drain event when pending == running == 0
def _bucket(lateness_ns: int) -> int: ...                        # histogram bucket
```

### 13.2 Module/import discipline

`timer_queue.py` is pure (no loop). `asyncio_scheduler.py` and `virtual.py` import `asyncio`, `selectors`; `virtual.py` additionally `heapq`-free (uses `TimerQueue`). Only `rg_core.time.system_clock` reads OS time; the scheduler reads time exclusively through `clock.mono_ns()`.

### 13.3 Lint allow-list entries required from RG-P03-005 §12.7 (CCR-5)

RG-LINT-001 sub-rule `.b` (loop timers `call_at/call_later`) must allow exactly one production file: `src/rg_core/scheduler/asyncio_scheduler.py` (`_rearm`). `VirtualScheduler` never calls loop timers. RG-LINT-003.b (`create_task`/`ensure_future`) needs no entry: every task is created through `RunScope.spawn`; `future` creation uses `loop.create_future()`. `asyncio.Runner` in `VirtualRuntime.run` is not covered by RG-LINT-002.i (it is called from a synchronous function).

## 14. Error handling and failure recovery

| Failure | Detection | Handling | Recovery | Code |
|---|---|---|---|---|
| Too many timers | capacity check | synchronous raise at the call site; nothing queued | caller backs off (probe concurrency bound, RG-P05-014) | RGE-TIMING-0060 |
| Callback raises | `_fire` | real: recorded (`errors_total`, `on_error`, log), scheduler continues; virtual: stored and raised at `drain()` | fix callback | RGE-INTERNAL-0002 (wrapped) |
| Scheduled coroutine raises | `_runner` | future gets the `RgError`/wrapped exception; `scope.failures` unaffected (critical=False) | caller handles | RGE-* of the cause / RGE-INTERNAL-0002 |
| Timer fires early vs perf_counter | guard | re-arm for remaining, `early_wakeups_total++` | none | — |
| Virtual deadlock | selector idle, no work | raise from `select` ⇒ `Runner.run` raises; message lists blocked tasks | fix test/scenario | RGE-TIMING-0061 |
| Virtual runaway (zero-delay loop, endless periodic) | counters | raise | fix scenario | RGE-TIMING-0062 |
| Real I/O or thread-pool work during virtual advance | strict-IO check / guards | raise (never silently advances time under in-flight real work) | compose inline executors/in-process transports | RGE-INTERNAL-0063 |
| Misuse (wrong thread, closed, rebind, second run) | checks | raise | fix caller | RGE-INTERNAL-0064 |
| Selector loop cannot be built | self-test in `VirtualRuntime.create` | raise | use real-time lab mode | RGE-INTERNAL-0067 |
| Scope cancelled while timers pending | token check | `run_at` coroutines not started (futures cancelled); sync callbacks still fire; `close` at drain | none | — |

Partial-failure semantics: a rejected call leaves the queue unchanged; dispatch of a batch is not transactional (timers already fired stay fired).

## 15. Security requirements and trust boundaries

- **Measurement integrity (TV-08, TM-28):** timers and lateness use only the injected monotonic clock; wall jumps cannot reorder or delay timers (INV-8); scheduler lateness is recorded rather than hidden (R-003).
- **Resource exhaustion (TM-34, TM-10):** bounded timer/task count; bounded error list; virtual runaway limits; heap compaction prevents unbounded growth from cancelled timers.
- **Lab isolation:** `VirtualScheduler`/`VirtualRuntime` are reachable only when the run's `clock_kind` is `virtual`; `SystemRuntime.open` refuses virtual configuration, so a live experiment can never run on virtual time (DATA-MODEL §9.8). Virtual runs label evidence `clock.kind=virtual` (RG-P02-001).
- **Untrusted input:** scheduled names are bounded and grammar-checked (they appear in logs/timeline); callbacks are RG-internal code (plugins schedule through the same API and are trusted, TM-22).
- **Secrets:** none handled.

## 16. Concurrency, asynchronous behavior, and resource ownership

- **Ownership:** one scheduler per run, owned by the run's composition (`SystemRuntime`/`VirtualRuntime`); one `TimerQueue` per scheduler; tasks created through the bound `RunScope`. The loop thread is the only thread that touches scheduler state (no locks).
- **Executors:** none owned; blocking work belongs to RG-P03-005 executors; in virtual mode the composition root uses inline executors (`rg_core.testing.InlineExecutorSet`) and registers a quiescence guard (`stats().running + queued == 0`) so virtual time can never advance while a real thread is busy.
- **Fairness/backpressure:** `max_dispatch_batch` yields to the loop between batches; `max_pending_timers` is a hard bound (producers must bound themselves).
- **Cancellation:** §10.5; cancel budgets are RG-P03-005's (`CancelBudget`).
- **Shutdown:** `close()` cancels the wake handle and pending timers; running scheduled coroutines end through the scope.

## 17. Performance and resource requirements

Proposals, validated by benchmarks (not claims):

| Budget | Value | Rationale | Validation |
|---|---|---|---|
| Real dispatch lateness | p95 ≤ 25 ms, p99 ≤ 100 ms at ≤ 50 in-flight probes (NFR-PERF-001) on Linux and Windows 11 | exposure width includes probe spacing; Windows tick bias ≤ 15.6 ms | BM-SCHED-1 (P12-004), TST-RG-P03-006-17/18 |
| `call_at` / dispatch cost | ≤ 5 µs insert, ≤ 10 µs dispatch per timer (heap, n ≤ 10⁴) | O(log n) | BM-SCHED-1 |
| Virtual throughput | ≥ 200 000 dispatches/s single core; 86 400-probe 24 h run ≤ 2 s | lab speed (FR-LAB-001) | BM-SCHED-2 |
| Memory | ≤ 400 B per pending timer ⇒ 10 000 timers ≤ 4 MiB | | BM-SCHED-3 |
| Early-wake overhead | ≤ 1 extra wake per timer on coarse-timer platforms | bias | TST-RG-P03-006-12 counters |

## 18. Configuration and defaults

`[scheduler]` table = `SchedulerConfig` (§8.2); env vars `RG_SCHED_<FIELD>`:

| Field | Env var | Failure behaviour |
|---|---|---|
| `max_pending_timers` | `RG_SCHED_MAX_PENDING_TIMERS` | out of range ⇒ `RGE-CONFIG-0068` at load |
| `max_dispatch_batch` | `RG_SCHED_MAX_DISPATCH_BATCH` | same |
| `late_warn_ns` | `RG_SCHED_LATE_WARN_NS` | same |
| `bias_loop_granularity` | `RG_SCHED_BIAS_LOOP_GRANULARITY` | same |
| `compaction_min_cancelled` | `RG_SCHED_COMPACTION_MIN_CANCELLED` | same |
| `virtual_strict_io` | `RG_SCHED_VIRTUAL_STRICT_IO` | disabling is allowed only with `--lab virtual` (RG-P09-001) and is recorded in the lab manifest |
| `virtual_max_events` | `RG_SCHED_VIRTUAL_MAX_EVENTS` | same |
| `virtual_max_events_per_instant` | `RG_SCHED_VIRTUAL_MAX_EVENTS_PER_INSTANT` | same |
| `virtual_max_span_ns` | `RG_SCHED_VIRTUAL_MAX_SPAN_NS` | same |

Precedence: defaults < `revocationgap.toml` < env < CLI (RG-P03-003). Virtual-only fields are ignored (with a warning) in real runs.

## 19. Logging, observability, and evidence requirements

Events: `scheduler.timer_late` {`name`, `intended_ns`, `started_ns`, `lateness_ns`} (only above `late_warn_ns`), `scheduler.capacity` {`pending`, `running`, `capacity`} (on rejection), `scheduler.callback_error` {`name`, `code`}, `scheduler.virtual_advance` (debug, sampled) {`from_ns`, `to_ns`}, `scheduler.virtual_end` {`events_total`, `virtual_span_ns`, `wakeups`}. Metrics: `scheduling_lateness_ns` histogram (all dispatches; feeds NFR-PERF-001), `scheduler_pending`, `scheduler_early_wakeups_total`. Evidence: the lateness of each probe is stored on its `Observation` (not here); the lab manifest records `clock.kind=virtual`, scheduler config and the virtual epoch (FR-EVD-007). No secrets; timer names are non-sensitive identifiers.

## 20. Platform compatibility

- **Linux/macOS:** loop clock ≈ ns granularity; `loop_granularity_ns` ≈ 1; default selector loops. Virtual loop uses `selectors.DefaultSelector` (epoll/kqueue) for the real wake-up pair only.
- **Windows:** default `ProactorEventLoop` for real runs (RG-P03-005 §20); `AsyncioScheduler` uses only `loop.call_at/call_soon/create_future` (available on Proactor). Loop time is `time.monotonic`; on CPython < 3.13 its granularity is reported ≈ 15.6 ms (NFR-PERF-002, tag U ⇒ A-3) ⇒ timers may be up to one tick late (bias, §12.2); falsifier TST-RG-P03-006-18. The virtual loop is always a **selector** loop (`asyncio.SelectorEventLoop` with `selectors.SelectSelector`), which supports the loop's socketpair wake-up on Windows; it never uses `add_signal_handler` (RG-LINT-003.a).
- **All:** no `set_event_loop_policy`/policy APIs; `asyncio.Runner(loop_factory=…)` (3.11+) is used instead; Python 3.14 policy deprecations do not apply. Free-threaded builds are unsupported (RG-P03-005 `RGE-INTERNAL-0003`).

## 21. Edge cases and invalid inputs

| # | Case | Expected behaviour |
|---|---|---|
| E-1 | `due` in the past | dispatch at next opportunity; lateness = `now − due` recorded |
| E-2 | `due = 0` virtual at start | dispatched at `t = 0` (first idle point), lateness 0 |
| E-3 | `due` as float / negative / ≥ 2⁶² | `RGE-INTERNAL-0066` |
| E-4 | two timers, equal due | FIFO by submission |
| E-5 | callback submits a timer for the current instant | runs in the same dispatch pass after earlier-submitted ones (INV-3), subject to `virtual_max_events_per_instant` |
| E-6 | cancel a timer from inside its own callback | no effect (already dispatched) |
| E-7 | cancel the earliest timer | re-arm to the next (real) / skipped (virtual) |
| E-8 | `run_at` future cancelled while the coroutine runs | `CancelledError` inside the coroutine; future cancelled; scope unaffected |
| E-9 | `run_at` factory raises synchronously | future gets the exception (wrapped if foreign) |
| E-10 | scope cancelled with 10 pending `run_at` and 3 sleep timers | 10 futures cancelled; 3 sleep callbacks fire; `close()` at drain |
| E-11 | 10 001st timer | `RGE-TIMING-0060`; first 10 000 unaffected |
| E-12 | `call_at` from a worker thread | `RGE-INTERNAL-0064` |
| E-13 | virtual: main awaits an `asyncio.Event` nobody sets | `RGE-TIMING-0061` with the blocked task names |
| E-14 | virtual: `while True: await clock.sleep(0)` | `RGE-TIMING-0062` (per-instant limit) |
| E-15 | virtual: real socket registered (e.g. a lab server started by mistake) | `RGE-INTERNAL-0063` at the next advance |
| E-16 | virtual: third-party `await asyncio.sleep(3600)` | completes at virtual `+3600 s`; ordering per INV-12 |
| E-17 | real: loop fires 5 ms early relative to `perf_counter` | guard re-arms; no early dispatch |
| E-18 | `VirtualRuntime.run` called twice | `RGE-INTERNAL-0064` |
| E-19 | `AsyncioScheduler` given a `VirtualClock` | `RGE-INTERNAL-0065` |
| E-20 | lateness model returns a negative number | `RGE-INTERNAL-0066` at dispatch |

## 22. Unit and integration test requirements

| ID | Condition | Expected observation |
|---|---|---|
| TST-RG-P03-006-01 | Property (Hypothesis): random sequences of push/cancel on `TimerQueue`; compare pop order with a sorted reference of `(due, seq)` | identical order; ties FIFO; cancelled never popped (INV-3/5) |
| TST-RG-P03-006-02 | Worked example WE1 (A, B, C, D, E; past-due E) in the virtual scheduler | order `C@3, A@5, E@5, B@5, D@5`; lateness E = 1 s, others 0 |
| TST-RG-P03-006-03 | Virtual exactness: 1 000 random integer due times (incl. very large and 1 ns apart); record `started_ns` | `started_ns == due` for every timer (no float error); order by `(due, seq)` |
| TST-RG-P03-006-04 | Worked example WE4 lateness injection (`120 ms`, and a model returning 0) and its propagation into an `Observation` via a stub runner | `lateness_ns` exactly 120 000 000 / 0; `scheduling_lateness_ns` equals it (RG-P02-006 TST-16) |
| TST-RG-P03-006-05 | Worked example WE2: 24 h of 1 Hz probes + revocation at 3 600 s | 86 400 results; final mono/wall values exactly as stated; all lateness 0; run completes within the unit budget (≤ 5 s) |
| TST-RG-P03-006-06 | `drain` (virtual): sleepers of 1 s, 1 h, 24 h; chained timers; second concurrent `drain` | returns after the last timer; time advanced to the last due; INV-10; `drain` called while a due timer exists never returns early |
| TST-RG-P03-006-07 | Deadlock and runaway: unset `Event`; zero-delay self-rescheduler; span limit | `RGE-TIMING-0061` (names listed), `RGE-TIMING-0062` (limit named) |
| TST-RG-P03-006-08 | Strict I/O: register a `socketpair` end in the virtual loop; run an executor-backed call with the guard installed | `RGE-INTERNAL-0063`; with `virtual_strict_io=false` the run proceeds (lab manifest flag) |
| TST-RG-P03-006-09 | Third-party timers: `asyncio.sleep(10)`, `loop.call_later(5, f)` mixed with scheduler timers at identical instants | all on the virtual timeline; scheduler consequences precede loop timers at one instant (INV-12); identical across 100 repetitions |
| TST-RG-P03-006-10 | Cancellation matrix: `TimerHandle.cancel` (before/after fire/in own callback), `run_at` future cancel (before start, during run, after done), scope cancel with pending `run_at` + sleepers + sink | per §10.5 and E-6…E-10; no timer or task left behind (`pending() == ()`, no pending tasks) |
| TST-RG-P03-006-11 | Capacity: 10 000 timers accepted, 10 001st `RGE-TIMING-0060`; cancel 6 000 ⇒ capacity regained; compaction triggers (heap length shrinks) | as stated (INV-4) |
| TST-RG-P03-006-12 | Real scheduler with a fake clock/loop pair (loop clock coarse by 15.625 ms, firing early by ≤ one tick when unbiased): bias on vs off; clock-source drift of 50 ppm | with bias: no early dispatch, `early_wakeups ≤ 1` per timer, no busy loop (wake count ≤ 3 per timer); without bias the test shows the early-fire/re-arm churn (documents the need) |
| TST-RG-P03-006-13 | Real scheduler functional on `SystemClock`: 200 timers at random 0–200 ms with ties; record `started ≥ due` and order | INV-1/2/3 hold (property: never early) |
| TST-RG-P03-006-14 | Error isolation: callback raising, `run_at` coroutine raising `RgError` and `ValueError`; real vs virtual | real: scheduler continues, futures carry `RgError`/`RGE-INTERNAL-0002`; virtual: `drain()` raises the first error with count |
| TST-RG-P03-006-15 | Clock-jump injection WE5 with `FaultPlan` of §8.4 and a 1 Hz probe stub + `WallStepDetector` | timer starts identical to a no-fault run (INV-8); one `wall_step(+2 s)` anomaly; wall stamps shifted from t = 3 600 s |
| TST-RG-P03-006-16 | Determinism: run the same virtual program twice in one process, in two processes, on Python 3.11/3.12/3.13/3.14 and Linux/Windows/macOS (golden event log) | byte-identical `(name, intended, started)` logs (INV-7) |
| TST-RG-P03-006-17 | BM-SCHED-1: 50 concurrent probe timers at 20 Hz for 5 min on the reference environment (real clock, in-process echo server) | records lateness p50/p95/p99/max; asserts NFR-PERF-001 thresholds (p95 ≤ 25 ms, p99 ≤ 100 ms) — a miss fails the benchmark gate and triggers rationale review |
| TST-RG-P03-006-18 | Windows runner: log `Clock.loop_granularity_ns`; repeat BM-SCHED-1 | lateness ≤ granularity + NFR-PERF-001 budget; falsifies/confirms A-3 |
| TST-RG-P03-006-19 | Composition: `VirtualRuntime.run` with a RunScope, main raising, nested `spawn`; second `run`; `SystemRuntime.open` with virtual config; misuse (wrong thread, no loop, rebind, use after close) | codes `RGE-INTERNAL-0064/0065`; `RunScope` semantics intact (INV-1 of RG-P03-005) |
| TST-RG-P03-006-20 | Lint: fixtures proving `.b` is allowed only in `asyncio_scheduler.py`, no `create_task`, no `time.*` in `rg_core.scheduler` | rglint/ruff clean on the package; violations in a deliberately bad fixture are reported |
| TST-RG-P03-006-21 | Integration (lab virtual time): engine-style schedule (dense probes then backoff, settle sleep, state-machine timeouts armed as timers) with the mock IdP; compare classification with the real-time lab run (ADR-0014 equivalence) | identical normalised evidence and classification (RG-P09-005 consumes the dataset) |

## 23. Mocking and test fixtures

Doubles: `VirtualRuntime` itself (primary), `FakeLoopClock` (coarse-tick loop time + early-fire emulation for TST-12), `InlineExecutorSet` (RG-P03-005 testing helpers; runs `run_blocking` callables inline), `StubProbeRunner` (records `ScheduledResult`s). Fixtures: `fixtures/scheduler/we1_order.json`, `we2_24h.json`, `fault_plan_we5.json` (§8.4), `golden_event_log.jsonl` (TST-16), `lateness_models.py`. pytest plugin `rg_core.testing.pytest_virtual` provides the `virtual_runtime` fixture (sync tests call `runtime.run(main)`); async tests must not mix the pytest event loop with the virtual loop.

## 24. Objective acceptance criteria

- **AC-RG-P03-006-01** Timers dispatch in strictly ascending `(due_mono_ns, submission_seq)` order in both implementations, FIFO on ties, and never before their due instant (verified by TST-RG-P03-006-01, TST-RG-P03-006-02, TST-RG-P03-006-13).
- **AC-RG-P03-006-02** In virtual time every timer starts at exactly its due instant (plus an injected lateness model value), a 24-hour experiment completes without wall-clock waiting, and third-party `asyncio.sleep` shares the virtual timeline (verified by TST-RG-P03-006-03, TST-RG-P03-006-04, TST-RG-P03-006-05, TST-RG-P03-006-09).
- **AC-RG-P03-006-03** `drain` runs a virtual experiment to quiescence, and deadlocks, runaways and real I/O during virtual advance are detected with the specified codes (verified by TST-RG-P03-006-06, TST-RG-P03-006-07, TST-RG-P03-006-08).
- **AC-RG-P03-006-04** Cancellation of handles, futures and scopes behaves as specified and leaves no timer or task behind (verified by TST-RG-P03-006-10).
- **AC-RG-P03-006-05** The timer count is bounded; the 10 001st timer is rejected with `RGE-TIMING-0060` and cancelled timers free capacity (verified by TST-RG-P03-006-11).
- **AC-RG-P03-006-06** The real scheduler tolerates coarse and drifting loop clocks without early dispatch or busy waiting, isolates callback failures, and meets the NFR-PERF-001 lateness thresholds on the reference environments (verified by TST-RG-P03-006-12, TST-RG-P03-006-14, TST-RG-P03-006-17, TST-RG-P03-006-18).
- **AC-RG-P03-006-07** Injected wall jumps and rates never change timer order or lateness and are visible to the wall-step detector (verified by TST-RG-P03-006-15).
- **AC-RG-P03-006-08** Virtual runs are deterministic across processes, Python versions and operating systems, and equivalent to real-time lab runs in classification (verified by TST-RG-P03-006-16, TST-RG-P03-006-21).
- **AC-RG-P03-006-09** Composition helpers refuse mismatched clock kinds and misuse, and the package passes the lint rules with only the documented allow-list entry (verified by TST-RG-P03-006-19, TST-RG-P03-006-20).

## 25. Research sources and engineering rationale

Sources: INTERFACE-CONTRACTS §3 (`Clock`, `Scheduler`); SYSTEM-ARCHITECTURE §5 (timing discipline, determinism tie-break); ADR-0004, ADR-0006, ADR-0014; REPO-ASSESSMENT §2 (SimPy cannot drive real sockets); TECHNICAL-FEASIBILITY §2/§3 (own scheduler; R-003, R-016); RG-P03-005 §7.4–7.7, §12.7, §20 (RunScope, executors, lint, loop-timer granularity note); PRD NFR-PERF-001/002/003, FR-LAB-001/004; RG-P02-001 (virtual clock, calibration). External prior art (evidence tag **S**: read from search-result excerpts this session, not evaluated by installation): aiotools `VirtualClock` (patches the *current* loop so sleeps return instantly; README states tight coupling with asyncio internals), async-solipsism (event loop with fake time and mock sockets; known issue aio-libs/aiohttp #10149: a handler firing exactly on time is treated as early and resubmitted forever when time only advances while something sleeps). **V-lab (author prototype, CPython 3.11.16/3.12/3.13 on Linux, this session):** a selector-hook design (this spec §12.5) advanced a 24-hour virtual timeline in well under a millisecond, executed scheduler timers and a third-party `asyncio.sleep` in one deterministic order, and exposed the pitfall that time must not advance in the same `select` call that dispatches timers (corrected in §12.5).

- **DEC-1 Virtual-time loop = `asyncio.SelectorEventLoop` subclass with an injected `VirtualSelector` and overridden `time()`.** Chosen: the engine, adapters and lab code run **unchanged** on the same asyncio primitives (`TaskGroup`, `Queue`, `Lock`, `gather`, `RunScope`); no private loop attribute is patched; time advances only when the loop is provably idle (the selector is invoked with no ready handle; it uses the `selectors.BaseSelector` interface that `SelectorEventLoop` accepts, assumption A-1); scheduler timers use exact integer ns. Rejected alternatives: **(B) purpose-built cooperative runner** — would not run `asyncio`-based code (TaskGroup, Queue, Event), forcing an RG-specific concurrency library and diverging the lab from production (violates ADR-0014's "same engine" intent); **(C) SimPy** (ADR-0006/0014, REPO-ASSESSMENT §2: a generator-based discrete-event simulator; cannot host asyncio coroutines or in-process ASGI transports; its real-time environment couples to wall time) — re-evaluated for *pure* simulation in RG-P09-001, not for the engine; **(D) time-patching (`freezegun`, `time-machine`)** — process-global monkey-patching, unsafe with worker threads, does not control `perf_counter` consumers consistently, contradicts "no hidden global state"; **(E) third-party virtual-time loops (aiotools, async-solipsism)** — add runtime dependencies to a pydantic-only package (ADR-0003), patch loop internals or ship mock sockets we do not need, and (async-solipsism) expose the exact-time re-queue hazard; kept as prior art. Verification: TST-03/05/07/09/16.
- **DEC-2 Scheduler timers are *not* loop timers in virtual mode** (dispatched from the selector at idleness) but are loop timers in real mode. Chosen: exactness and the `(due, seq)` order are independent of the loop's float clock and early-fire tolerance; the same `TimerQueue` serves both modes so ordering semantics cannot diverge. Rejected: one loop-timer-based implementation for both (inherits asyncio's heap tie behaviour and the early-fire hazard in virtual time). Verification: TST-01/03.
- **DEC-3 Strict total order by `(due, seq)`** with unique `seq`: removes dependence on `heapq` tie handling and implements the SYSTEM-ARCHITECTURE §5 rule literally. Verification: TST-01/02.
- **DEC-4 Never-early guard + loop-granularity bias** (real mode): the guard makes correctness independent of loop-clock quality; the bias prevents guard churn on 15.6 ms-tick loops. Rejected: relying on `loop.call_at` precision (RG-P03-005 §20 forbids), spinning with `sleep(0)` (burns CPU at 50 timers/s on Windows). Verification: TST-12/17/18.
- **DEC-5 Lateness recorded, never corrected**: a late timer is dispatched late and says so (`ScheduledResult.lateness_ns`, histogram, observation field); the scheduler never "catches up" by skipping or compressing intervals (honest spacing is what the exposure arithmetic needs). Verification: TST-04/13.
- **DEC-6 Bounded count with a synchronous failure** (`RGE-TIMING-0060`) rather than queueing: producers (probe concurrency, RG-P05-014) own backpressure; hidden queues would distort schedules. Verification: TST-11.
- **DEC-7 After scope cancellation sync callbacks still fire, new coroutines do not** — prevents sinks from hanging on dropped sleep timers while stopping probes promptly. Verification: TST-10.
- **DEC-8 Virtual runtime is single-use and refuses real I/O by default** — a lab run's timeline is never reused, and nondeterminism from real sockets/threads is detected instead of tolerated (`virtual_strict_io`). Verification: TST-08/19.

## 26. Remaining uncertainties or assumptions

| # | Assumption | Evidence tag | Falsifying test |
|---|---|---|---|
| A-1 | `asyncio.SelectorEventLoop(selector)` accepts a custom `selectors.BaseSelector`, and `BaseEventLoop._run_once` passes `timeout=None` when nothing is scheduled/ready and `0` when work is ready (implementation behaviour, not a documented API) on CPython 3.11–3.14 | V-lab on 3.11.16/3.12/3.13 (Linux); 3.14 and Windows/macOS unverified (U) | TST-RG-P03-006-16 on the full CI matrix; failure ⇒ `RGE-INTERNAL-0067` self-test at `VirtualRuntime.create` and fallback to real-time lab mode |
| A-2 | `asyncio.Runner(loop_factory=…)` runs `main` on our loop without touching global policy (3.11+) | V-lab (3.11–3.13); docs | TST-19 |
| A-3 | On Windows with CPython < 3.13 the asyncio loop clock granularity is ≈ 15.6 ms (NFR-PERF-002 tag U) | U | TST-RG-P03-006-18 (`Clock.loop_granularity_ns` logged; lateness measured) |
| A-4 | A real selector's wake-up pair is the only registered fd of an idle virtual loop (so `len(get_map()) > 1` identifies real I/O) | V-lab (Linux); platform differences U | TST-RG-P03-006-08 on all platforms |
| A-5 | Third-party libraries used in the lab (mock IdP/service via in-process transports) perform no real I/O and no thread offload when composed with inline executors | design | TST-08 guard; RG-P09-002/-003 conformance |
| A-6 | **CCR-5 (to RG-P03-005):** (a) §23 helper `VirtualClock.advance(ns)` does not exist — tests must use `await clock.sleep(ns)` under `VirtualScheduler` or `VirtualClockDriver.advance_to`; (b) RG-LINT-001 `.b` allow-list gains `src/rg_core/scheduler/asyncio_scheduler.py` | — | review of RG-P03-005 after the coordinator's sweep; TST-20 |
| A-7 | aiotools/async-solipsism behaviours quoted in §25 are accurate as of the excerpts read | S | none required (prior art only; no dependency) |
| A-8 | 10 000 timers (default) exceed any realistic concurrent schedule (200 probes × a few timers) | proposal | BM-SCHED-3; configurable |
| A-9 | `ScheduledResult.finished_ns` (additive) does not conflict with the frozen `.value/.intended_ns/.started_ns` contract | design | contract test in RG-P05-014 |

## 27. Maintainability, portability, and future extension requirements

- **Versioning:** the port signatures are frozen (INTERFACE-CONTRACTS §3); additions are optional members. `SchedulerConfig` fields are additive; `FaultPlan` is a lab input schema (`1.0`) extended by new `kind` discriminators (RG-P09-004 adds event/response faults in its own models, using `call_at` ordering).
- **Extension points:** `LatenessModel`; `add_quiescence_guard`; additional `TaskRole`s via RG-P03-005; alternative implementations (e.g. a distributed coordinator's scheduler) implement the same `Scheduler` and must pass the scheduler conformance kit (`rg_core.testing.scheduler_conformance`: TST-01/02/10/11 parametrised over implementations).
- **Reuse:** `TimerQueue` + `VirtualEventLoop` form a small, dependency-free *deterministic asyncio runtime* reusable by any asyncio project that needs virtual time without patching globals (candidate for separate packaging only if reuse is demonstrated, RG-P14-001).
- **Portability:** adding a platform requires only passing TST-08/16/18 there; no platform branches exist in the code, only configuration of the loop granularity bias.
- **Deprecation:** none yet; if CPython changes `_run_once`'s selector protocol, the self-test (`RGE-INTERNAL-0067`) fails closed and the lab falls back to real-time mode (ADR-0014) while the virtual loop is adapted.
