---
id: RG-P03-005
title: "Async model, error taxonomy and cancellation"
phase: "03"
package: core
module_ids: [MOD-CORE-ASYNC_ERRORS_CANCELLATION]
status: DRAFT
depends_on: [RG-P03-002]
requirements: [FR-OPS-006, FR-PRB-017, FR-EXP-007, FR-CLI-002, FR-SEC-005, FR-SEC-009, NFR-REL-002, NFR-REL-003, NFR-REL-004, NFR-PERF-001, NFR-PERF-003, NFR-PLAT-001, NFR-MNT-001, NFR-MNT-002, NFR-TEST-003]
interfaces_defined: [IF-CORE-ERR, IF-CORE-AIO]
interfaces_used: [IF-CORE-CLOCK, IF-CORE-SERIAL]
schemas_defined: [SCH-ERROR]
schemathesis_touchpoints: []
---

# RG-P03-005 — Async model, error taxonomy and cancellation

> Scope: `rg_core.errors` (hierarchy, codes, records, group collapse), `rg_core.aio` (run scope, deadlines, executors, queues, abort controller, loop-lag monitor), dev tool `tools/rglint.py` + ruff configuration (RG-LINT-001/-002/-003). Pure Python; the only I/O-capable pieces are the executors (threads) and the signal handler, both created by the composition root, not at import time.

## 1. Module identifier and name

| Item | Value |
|---|---|
| Element | RG-P03-005 — Async model, error taxonomy and cancellation |
| Module id | `MOD-CORE-ASYNC_ERRORS_CANCELLATION` |
| Packages | `rg_core.errors` (`core.py` — `RgError` classes, stdlib-only leaf; `codes.py`, `registry.py`, `record.py` — `ErrorRecord`, depends on `rg_core.model.base`), `rg_core.aio` (`scope.py`, `deadline.py`, `executors.py`, `queues.py`, `abort.py`, `lag.py`, `commit.py`); dev tools `tools/rglint.py`, `[tool.ruff]` fragment in `pyproject.toml` |
| Interfaces owned | `IF-CORE-ERR` (the `RgError` hierarchy, `ErrorCode`, `ErrorRegistry`, `ErrorRecord`, `collapse_group`, `exit_kind_of`); **new** `IF-CORE-AIO` (`RunScope`, `Deadline`, `ExecutorSet`/`run_blocking`, `BoundedQueue`, `AbortController`, `shield_commit`, `run_cleanup`) |
| Schemas owned | **new** `SCH-ERROR` (`ErrorRecord`, `CauseRecord`) |
| Consumers | every module (errors); RG-P03-006 scheduler, RG-P03-007 event bus, RG-P03-008 store (executor `store`, commit shielding), RG-P03-010 engine (scopes, cleanup, abort), RG-P05-009/-014 (retry, probe concurrency), RG-P06-001 (shielded admin calls), RG-P04-* (executor `idp`) |

## 2. Phase and requirement references

| Requirement | How realised here |
|---|---|
| FR-OPS-006 | `Deadline` gives every operation a timeout on the injected clock; `RunScope.cancel` + `CancelBudget.probe_stop` (default 1 s) stop probing; cleanup runs after abort. |
| FR-PRB-017 | `ExecutorSet` bounded `probe` executor; cooperative cancellation; no threads left after `ExecutorSet.aclose`. |
| FR-EXP-007 | `run_cleanup` / `shield_commit` guarantee that CLEANING_UP runs after ABORTED/FAILED paths and that a second signal cannot silently skip the restoration ledger. |
| FR-CLI-002 | `ExitKind` + `exit_kind_of(error)` supplies the category→exit-kind hook; integer codes belong to RG-P10-001. |
| FR-SEC-005 | `RgError.details` and `ErrorRecord` are secret-safe by construction (§9 rules E1–E6). |
| FR-SEC-009 | Bounded queues with explicit overflow policies; typed `QueueFull`/`ExecutorSaturated` errors. |
| NFR-REL-002 | Deterministic structured concurrency under a virtual clock (no wall waits; fixed spawn order). |
| NFR-REL-003 | Every queue and retry-adjacent wait is bounded; evidence-bearing queues use `block` only. |
| NFR-REL-004 | Scope/executor teardown rules; no leaked tasks or threads after `RunScope`/`ExecutorSet` close. |
| NFR-PERF-001, NFR-PERF-003 | Executor sizing (default 64 `probe` workers), queueing-delay measurement (`BlockingResult`), `LoopLagMonitor`. |
| NFR-PLAT-001 | ProactorEventLoop/Windows signal rules; CI matrix 3.11–3.14. |
| NFR-MNT-001, NFR-MNT-002 | `rg_core` stays I/O-free at import; typed API (mypy strict); lint rules enforce the dependency on `Clock`. |
| NFR-TEST-003 | RG-LINT-001 forbids wall-clock waits, so unit tests run without sleeping. |

Threats: **TM-34** (RG-side exhaustion: bounded queues/executors, quota abort), **TM-10** (bounded per-probe memory via queue/executor limits), **TM-28** (durations from the monotonic clock only; lint), **TM-07** (error details cannot carry secrets), **TM-29** (the `idp` executor limit caps concurrent admin calls). Validity items: **TV-15/TV-16-style** timing integrity — `BlockingResult` exposes submission→start queueing delay so lateness is never hidden. Workflows: WF-01 (run), WF-11 (abort/cleanup).

## 3. Purpose and user/security value

Three cross-cutting guarantees: (1) every failure is one `RgError` with a stable, documented code, so CLI exit codes, GUI messages, evidence records and tests agree; (2) concurrency is structured — every task has an owner scope, abort propagates within a stated budget, and cleanup/restoration of synthetic identities always runs (SC-13); (3) nothing can block the event loop or bypass the injected clock unnoticed, because lint rules make those mistakes build failures. The measurement value is direct: the exposure width `W` includes scheduling and queueing lateness (DATA-MODEL §4), so bounded executors with measured queueing delay keep the uncertainty honest.

## 4. Explicit responsibilities

- **RESP-1** Define `ErrorCategory` (13 values of DATA-MODEL §6), `RgError` and one subclass per category with the frozen constructor `RgError(category, code, message, retryable, details, cause)`.
- **RESP-2** Define the error-code format, the `ErrorCode`/`ErrorRegistry` mechanism and the **reserved code-block table** (§8.3) other elements allocate from.
- **RESP-3** Define the generic codes of block 0001–0019 (§7.3).
- **RESP-4** Define `ErrorRecord` (`SCH-ERROR`) and `RgError.to_record` for evidence/log serialisation, with cause chaining and details sanitisation.
- **RESP-5** Define exception-group handling: `collapse_group`, severity order, cancellation filtering.
- **RESP-6** Define `RunScope` (structured concurrency on `asyncio.TaskGroup`), task roles, supervised/sink tasks, cancel reasons and `CancelBudget`.
- **RESP-7** Define the cancellation protocol: soft/hard abort, shielding rules, `shield_commit`, `CommitLedger`, `run_cleanup`, `await_uncancellable`.
- **RESP-8** Define `Deadline` and `cancel_and_wait` on the injected `Clock`.
- **RESP-9** Define `ExecutorSet` with the three bounded executors (`probe`, `idp`, `store`), sizing, saturation behaviour, `run_blocking` (context propagation, serial keys, timing bracket).
- **RESP-10** Define `BoundedQueue` with overflow policies `block`, `drop_oldest`, `fail` and the backpressure rules table.
- **RESP-11** Define `AbortController` (SIGINT/SIGTERM/SIGBREAK handling, press counting) and `LoopLagMonitor`.
- **RESP-12** Specify lint rules RG-LINT-001, RG-LINT-002, RG-LINT-003 as executable checks with fixtures.
- **RESP-13** Define `ExitKind` and `exit_kind_of`.

## 5. Out-of-scope responsibilities

| Excluded | Owner |
|---|---|
| `Clock`/`TimeInstant` semantics, `SystemClock`, `VirtualClock` | RG-P02-001 |
| `Scheduler`, timer wheel, intended-vs-actual lateness records | RG-P03-006 (uses `Deadline` helpers, not the reverse) |
| `EventBus` queues' subscriber policy (uses `BoundedQueue`) | RG-P03-007 |
| SQLite connection ownership inside the `store` thread, WAL/commit semantics | RG-P03-008 |
| Experiment state machine and the decision *when* to enter CLEANING_UP | RG-P02-007 / RG-P03-010 (this spec supplies the mechanism) |
| Restoration ledger content and idempotent restoration actions | RG-P06-010 |
| Retry/backoff/jitter policy and rate limiting | RG-P05-009 |
| Probe-level concurrency limits and per-probe cancellation details | RG-P05-014 (consumes `ExecutorSet`) |
| CLI exit-code integers, banner, interactive confirmations | RG-P10-001 |
| Log formatting/redaction (uses `ErrorRecord`) | RG-P03-004 |
| Configuration file parsing of `[engine.*]` sections | RG-P03-003 (this spec supplies the section models, §18) |
| Allocation of per-area codes | each element, within its block (§8.3) |

## 6. Dependencies and prerequisites

* Specs: RG-P03-002 (`Model`, `Document` conventions, `Secret`, `Label`, `ShortText`, `canonical` helpers); `IF-CORE-CLOCK` from RG-P02-001 by signature only (DATA-MODEL §2.2, INTERFACE-CONTRACTS §3; no dependency on that spec's file).
* Python ≥ 3.11 (`asyncio.TaskGroup`, `except*`, `ExceptionGroup`, `Task.cancelling/uncancel`); CI 3.11–3.14. Standard library only (`asyncio`, `concurrent.futures`, `contextvars`, `threading`, `signal`, `queue` not used).
* Environment: a running asyncio loop for `aio` (one per experiment run, owned by the engine); the main thread for `AbortController.install`.
* Tooling: `ruff` (pinned in `pyproject.toml`; rule families `TID251`, `ASYNC`), `ast` (stdlib) for `tools/rglint.py`.

## 7. External and internal interfaces

### 7.1 Error hierarchy (`rg_core.errors`) — IF-CORE-ERR

```python
class ErrorCategory(str, Enum):      # values are the upper-case tokens used in codes
    CONFIG="CONFIG"; SCOPE="SCOPE"; AUTH="AUTH"; PROVIDER="PROVIDER"; TRANSPORT="TRANSPORT"; TARGET="TARGET"
    ASSERTION="ASSERTION"; TIMING="TIMING"; STORE="STORE"; PLUGIN="PLUGIN"; UPSTREAM_COMPAT="UPSTREAM_COMPAT"
    CANCELLED="CANCELLED"; INTERNAL="INTERNAL"

class ErrorCode(NamedTuple):
    code: str                  # "RGE-<CAT>-<NNNN>", regex ^RGE-(CONFIG|SCOPE|AUTH|PROVIDER|TRANSPORT|TARGET|ASSERTION|TIMING|STORE|PLUGIN|UPSTREAM_COMPAT|CANCELLED|INTERNAL)-[0-9]{4}$
    name: str                  # SYMBOLIC_NAME, ^[A-Z][A-Z0-9_]{2,47}$
    category: ErrorCategory
    owner: str                 # element id, e.g. "RG-P03-005"
    retryable: bool            # default for new instances
    summary: str               # ≤ 120 chars, constant text

class RgError(Exception):                                  # sync, picklable, thread-safe to construct and read
    def __init__(self, category: ErrorCategory, code: str | ErrorCode, message: str,
                 retryable: bool = False, details: Mapping[str, object] | None = None,
                 cause: BaseException | None = None) -> None: ...
    category: ErrorCategory; code: str; message: str; retryable: bool
    details: Mapping[str, DetailValue]         # read-only mapping (MappingProxyType), sanitised (§9 E1–E6)
    cause: BaseException | None                # also set as __cause__
    @property exit_kind(self) -> ExitKind
    def to_record(self, *, scrub: Callable[[str], str] | None = None, occurred_at: TimeInstant | None = None,
                  produced_by: ProducedBy | None = None) -> ErrorRecord: ...
    def with_details(self, *, cause: BaseException | None = KEEP, **extra: object) -> "RgError": ...   # returns a NEW instance of the same class (errors are not mutated); `KEEP` sentinel = keep current cause
    def __str__(self) -> str: ...     # "<code>: <message>"  — never includes details or cause text
    def __repr__(self) -> str: ...    # "RgError(code='…', category='…', retryable=…, details_keys=[…])"

class ConfigError(RgError); ScopeError(RgError); AuthError(RgError); ProviderError(RgError); TransportError(RgError)
class TargetError(RgError); AssertionEvalError(RgError); TimingError(RgError); StoreError(RgError); PluginError(RgError)
class UpstreamCompatError(RgError); CancelledByRg(RgError); InternalError(RgError)
class QueueFull(TimingError)       # RGE-TIMING-0003
class QueueClosed(CancelledByRg)   # RGE-CANCELLED-0005
# subclass constructor: Cls(code, message, *, retryable=None, details=None, cause=None); category fixed by class; retryable=None → ErrorCode default

DetailValue = None | bool | int | float | str | tuple[None | bool | int | float | str, ...]     # flat: no nested mappings

def wrap_unexpected(exc: Exception, *, where: str) -> RgError: ...          # → InternalError RGE-INTERNAL-0002, details {where, exc_type}; never wraps BaseException-only types
def collapse_group(group: BaseExceptionGroup, *, where: str) -> RgError | asyncio.CancelledError: ...
def leaf_exceptions(group: BaseExceptionGroup) -> list[BaseException]: ...
def walk_causes(exc: BaseException, *, max_depth: int = 5) -> Iterator[BaseException]: ...   # cause, then __cause__, then (if suppress_context False) __context__; cycle-safe
class ExitKind(str, Enum): ok; findings; inconclusive; config_error; scope_refusal; internal_error; operator_abort; failure
def exit_kind_of(exc: BaseException | None) -> ExitKind: ...
```

Behaviour: constructing an `RgError` never raises (invalid details are repaired, §9). `retryable` semantic: **the same operation may succeed if retried unchanged**; the retry *policy* (count, backoff) is RG-P05-009. Errors are immutable after construction (attributes are read-only properties).

### 7.2 Registry (`rg_core.errors.registry`)

```python
class ErrorRegistry:                                       # explicit object built at composition; no import-time mutation
    @classmethod
    def build(cls, declared: Iterable[ErrorCode]) -> "ErrorRegistry"      # validates uniqueness, format, block ownership (§8.3); raises InternalError RGE-INTERNAL-0006
    def lookup(self, code: str) -> ErrorCode                               # KeyError → InternalError RGE-INTERNAL-0006
    def by_owner(self, owner: str) -> Sequence[ErrorCode]
    def resolve_alias(self, text: str) -> str                              # "RGE-PROVIDER-UNSUPPORTED" → "RGE-PROVIDER-0001"; only used when *reading* text
    def as_markdown(self) -> str                                           # generated catalogue (docs/08-SECURITY or docs/11-API error catalogue)
```
Each package exposes `ERROR_CODES: tuple[ErrorCode, ...]` in its `codes.py` (module constants; no registration side effects). `rg_core.errors.all_declared()` imports the known packages explicitly (`rg_core.*`, then app packages if installed) and `ErrorRegistry.build` checks them. Code strings used in source must come from these constants (rule RG-LINT-003.c, §7.8).

### 7.3 Generic codes (block 0001–0019, owner RG-P03-005)

| Code | Name | Category | Retryable | Meaning / raised by |
|---|---|---|---|---|
| `RGE-INTERNAL-0001` | INVARIANT_VIOLATION | INTERNAL | no | a documented `INV-n` of any module failed (`details.invariant`) |
| `RGE-INTERNAL-0002` | UNEXPECTED_EXCEPTION | INTERNAL | no | `wrap_unexpected` of a foreign exception (`details.where`, `details.exc_type`) |
| `RGE-INTERNAL-0003` | ASYNC_ENVIRONMENT_UNSUPPORTED | INTERNAL | no | Python < 3.11; eager task factory installed; running without a loop; free-threaded build |
| `RGE-INTERNAL-0004` | SCOPE_MISUSE | INTERNAL | no | `spawn` after scope exit/on a closed scope; scope entered twice; `cancel` from a foreign loop |
| `RGE-INTERNAL-0005` | EXECUTOR_MISUSE | INTERNAL | no | `run_blocking` from a non-loop thread; unknown executor; `serial_key` too long; call after `aclose` |
| `RGE-INTERNAL-0006` | ERROR_CODE_UNDECLARED | INTERNAL | no | registry build failure or lookup of an undeclared code |
| `RGE-TIMING-0001` | DEADLINE_EXCEEDED | TIMING | no | `Deadline.run` expiry; details `what`, `budget_ns` |
| `RGE-TIMING-0002` | EXECUTOR_SATURATED | TIMING | no | executor slot not obtained within `saturation_timeout`; details `executor`, `waited_ns` |
| `RGE-TIMING-0003` | QUEUE_FULL | TIMING | no | `fail` policy or `put_nowait` on a full `block` queue; details `queue`, `capacity` |
| `RGE-CANCELLED-0001` | CANCELLED | CANCELLED | n/a | cancellation recorded as a result (not raised inside tasks); details `reason` ∈ `CancelReason` |
| `RGE-CANCELLED-0002` | OUTCOME_UNKNOWN | CANCELLED | n/a | a shielded state-changing call did not finish within `commit_grace`; details `what` |
| `RGE-CANCELLED-0003` | CLEANUP_BUDGET_EXCEEDED | CANCELLED | n/a | `run_cleanup` budget ended with the cleanup task unfinished |
| `RGE-CANCELLED-0004` | HARD_ABORT | CANCELLED | n/a | second abort press: cleanup waits abandoned |
| `RGE-CANCELLED-0005` | QUEUE_CLOSED | CANCELLED | n/a | `get` on a closed, drained queue; `put` on a closed queue |
| `RGE-PROVIDER-0001` | UNSUPPORTED | PROVIDER | no | capability gap (`details.capability`); the symbolic spelling `RGE-PROVIDER-UNSUPPORTED` of INTERFACE-CONTRACTS §2.5 is an alias of this code (CCR-1) |

In-task rule: inside a running task, cancellation is always the native `asyncio.CancelledError` (never converted), so INTERFACE-CONTRACTS §2 rule 1 holds. `CancelledByRg` objects appear only as *results* (`RunResult.cancelled`, cleanup outcomes, ledger entries, evidence records).

### 7.4 Run scope and cancellation (`rg_core.aio`) — IF-CORE-AIO

```python
class CancelReason(str, Enum): operator="operator"; signal="signal"; fatal_child_error="fatal_child_error"; quota="quota"; rate_limit_stop="rate_limit_stop"; shutdown="shutdown"
class TaskRole(str, Enum): probe="probe"; scheduler="scheduler"; worker="worker"; observer="observer"; sink="sink"; cleanup="cleanup"
class CancelBudget(Model): probe_stop_ns: Int64 = 1_000_000_000; drain_ns: Int64 = 5_000_000_000; cleanup_ns: Int64 = 120_000_000_000; commit_grace_ns: Int64 = 5_000_000_000

class CancelToken:                                         # readable from sync code and threads
    @property cancelled(self) -> bool; reason(self) -> CancelReason | None; hard(self) -> bool
    def raise_if_cancelled(self) -> None                   # raises asyncio.CancelledError (sync helpers inside tasks)

class RunScope:                                            # async context manager; one per run (and nestable)
    def __init__(self, name: str, clock: Clock, *, budget: CancelBudget = CancelBudget(), parent: "RunScope | None" = None,
                 collapse: bool = True, ledger: "CommitLedger | None" = None) -> None
    async def __aenter__(self) -> "RunScope"
    async def __aexit__(self, et, ev, tb) -> bool
    def spawn(self, coro: Coroutine[Any, Any, T], *, name: str, role: TaskRole = TaskRole.worker,
              critical: bool = True) -> "asyncio.Task[T]"
    def spawn_sink(self, coro: Coroutine[Any, Any, T], *, name: str) -> "asyncio.Task[T]"     # drained, not cancelled, on soft abort
    def on_drain(self, callback: Callable[[], None]) -> None  # sync callbacks run (in registration order) when front tasks have ended (e.g. queue.close)
    def cancel(self, reason: CancelReason) -> None            # idempotent, thread-safe via call_soon_threadsafe; first reason wins
    def hard_abort(self) -> None                              # idempotent
    token: CancelToken; ledger: CommitLedger; failures: Sequence[RgError]   # supervised-task failures recorded, not raised
    stuck: Sequence[str]                                      # names of tasks that ignored cancellation beyond budget

async def cancel_and_wait(task: "asyncio.Task[Any]", *, clock: Clock, budget_ns: int) -> bool   # True if finished within budget
async def await_uncancellable(task: "asyncio.Task[T]", *, clock: Clock, budget_ns: int, token: CancelToken | None = None,
                              reraise: bool = True) -> "AwaitOutcome[T]"
async def shield_commit(coro: Awaitable[T], *, what: str, clock: Clock, grace_ns: int, ledger: "CommitLedger") -> T
async def run_cleanup(factory: Callable[[], Awaitable[T]], *, clock: Clock, budget_ns: int, token: CancelToken) -> "CleanupOutcome[T]"
class CommitRecord(Model): what: Label; status: Literal["completed","unknown","failed"]; started: TimeInstant; finished: TimeInstant | None; error_code: str | None
class CommitLedger: def records(self) -> Sequence[CommitRecord]; def unknown(self) -> Sequence[CommitRecord]
```

### 7.5 Deadlines (`rg_core.aio.deadline`)

```python
class Deadline:
    @classmethod
    def after(cls, clock: Clock, duration_ns: int) -> "Deadline"           # duration_ns in [1, 10**15]
    def remaining_ns(self) -> int                                           # max(0, due - clock.mono_ns())
    def expired(self) -> bool
    def child(self, max_ns: int | None = None) -> "Deadline"               # min(self, now + max_ns)
    @property due_mono_ns(self) -> int; clock_id(self) -> str
    async def run(self, awaitable: Awaitable[T], *, what: str) -> T         # raises TimingError RGE-TIMING-0001; cancels the awaitable (budget 1 s)
```
Cancellation: cancelling the caller cancels the awaitable and the internal sleeper, then re-raises `CancelledError`.

### 7.6 Executors (`rg_core.aio.executors`)

```python
ExecutorName = Literal["probe", "idp", "store"]
class ExecutorSpec(Model): max_workers: Count; queue_capacity: Count; saturation_timeout_ns: Int64 | None   # None = wait indefinitely (allowed for "store" only)
class BlockingResult(NamedTuple, Generic[T]): value: T; submitted: TimeInstant; started: TimeInstant; finished: TimeInstant
class ExecutorStats(Model): running: Count; queued: Count; waiting: Count; completed: Count; rejected: Count; max_queue_delay_ns: Int64
class ExecutorSet:                                         # one per run context
    def __init__(self, specs: Mapping[ExecutorName, ExecutorSpec], clock: Clock) -> None
    async def run_blocking(self, name: ExecutorName, fn: Callable[..., T], *args: Any, label: str,
                           serial_key: str | None = None, deadline: Deadline | None = None, shield: bool = False) -> BlockingResult[T]
    def stats(self) -> Mapping[ExecutorName, ExecutorStats]
    async def aclose(self, *, budget_ns: int = 5_000_000_000) -> Sequence[str]      # returns labels of calls still running (abandoned)
```
`fn` must carry its own finite I/O timeout (`deadline.remaining_ns()` converted by the caller); `run_blocking` rejects `deadline=None` for executors `probe` and `idp` only when `ExecutorSet(strict=True)` (default in production, off in unit tests of pure helpers).

### 7.7 Queues, abort, lag (`rg_core.aio.queues`, `abort`, `lag`)

```python
OverflowPolicy = Literal["block", "drop_oldest", "fail"]
class PutResult(str, Enum): accepted="accepted"; dropped_oldest="dropped_oldest"; dropped_self="dropped_self"
class QueueStats(Model): depth: Count; capacity: Count; high_water: Count; dropped: Count; blocked_total_ns: Int64; closed: bool
class BoundedQueue(Generic[T]):                            # loop-confined; put_threadsafe for other threads
    def __init__(self, name: str, capacity: int, policy: OverflowPolicy, *, clock: Clock) -> None        # capacity in [1, 1_000_000]
    async def put(self, item: T, *, critical: bool = False) -> PutResult
    def put_nowait(self, item: T, *, critical: bool = False) -> PutResult
    def put_threadsafe(self, loop: asyncio.AbstractEventLoop, item: T, *, critical: bool = False) -> "concurrent.futures.Future[PutResult]"
    async def get(self) -> T                                # raises CancelledByRg RGE-CANCELLED-0005 when closed and empty
    def get_nowait(self) -> T
    def close(self) -> None                                  # no more puts; getters drain, then see QueueClosed
    def stats(self) -> QueueStats

class AbortController:
    def __init__(self, loop: asyncio.AbstractEventLoop, *, on_soft: Callable[[CancelReason], None], on_hard: Callable[[], None],
                 on_force: Callable[[], NoReturn]) -> None
    def install(self) -> None          # main thread only; else RGE-INTERNAL-0005
    def uninstall(self) -> None        # restores previous handlers; idempotent
    @property presses(self) -> int

class LoopLagMonitor:                  # optional; one task per run
    def __init__(self, clock: Clock, *, interval_ns: int = 100_000_000, warn_ns: int = 100_000_000, emit: Callable[[int], None]) -> None
    async def run(self) -> None        # sleeps interval (Clock.sleep); lag = (actual wake − intended) in ns; emit(lag) ; cancelled with its scope
```

### 7.8 Lint tools

`ruff check` (rule families `TID251`, `ASYNC`) and `python tools/rglint.py [--root <dir>] [--select RG-LINT-001,RG-LINT-002,RG-LINT-003] <paths…>`; output lines `path:line:col: RG-LINT-00X[.sub] message`; exit status 1 if any finding. Details and fixtures in §12.7 and §22.

## 8. Data structures and schemas

### 8.1 `ErrorRecord` (SCH-ERROR, `schema_version "1.0"`; `ErrorRecord(Document)` with `SCHEMA_ID="error_record"`, `CauseRecord(Model)`)

| Field | Type | Constraint | Default | Description |
|---|---|---|---|---|
| `schema_version` | `SchemaVersion` | `"1.0"` | `"1.0"` | |
| `category` | `ErrorCategory` | — | — | |
| `code` | `str` | `^RGE-[A-Z_]+-[0-9]{4}$`, ≤ 40 | — | |
| `name` | `str \| None` | `^[A-Z][A-Z0-9_]{2,47}$` | None | symbolic name if declared |
| `message` | `ShortText` | single line, ≤ 256 after cleaning (longer messages are clipped with `…[+N]`) | — | constant text, no untrusted interpolation |
| `retryable` | `bool` | — | — | |
| `details` | `dict[Label→DetailValue]` | ≤ 32 keys; str values ≤ 512; tuples ≤ 32 items | `{}` | flat, sanitised |
| `cause_chain` | `tuple[CauseRecord, …]` | ≤ 5 | `()` | nearest cause first |
| `exit_kind` | `ExitKind` | — | — | |
| `occurred_at` | `TimeInstant \| None` | SCH-TIME | None | stamped by the catcher from its `Clock`; errors never read clocks |
| `derivation` | `Derivation` | `observed` | `observed` | |
| `produced_by` | `ProducedBy \| None` | — | None | |

`CauseRecord`: `type` (`ShortText`, qualified class name), `code` (`str | None`, present when the cause is an `RgError`), `message` (`ShortText | None`; present only when the caller supplied `scrub`, never otherwise).

Example (complete):

```json
{"category":"TIMING","cause_chain":[{"code":null,"message":null,"type":"asyncio.exceptions.CancelledError"}],"code":"RGE-TIMING-0001","derivation":"observed","details":{"budget_ns":"5000000000","what":"idp.token_exchange"},"exit_kind":"failure","message":"Deadline exceeded","name":"DEADLINE_EXCEEDED","occurred_at":{"clock_id":"system","mono_ns":"184467440737","read_cost_ns":"800","wall_ns":"1791796800123456789"},"retryable":false,"schema_version":"1.0"}
```

(`budget_ns` appears as a string because `details` integers beyond 2⁵³−1 are Int64-encoded; integers within the safe range stay numbers — `to_record` converts any int with |v| > 2⁵³−1 to its decimal string.)

### 8.2 Configuration models (consumed by RG-P03-003)

`ExecutorsConfig(Model)`: `probe: ExecutorSpecConfig`, `idp: ExecutorSpecConfig`, `store: ExecutorSpecConfig`; `CancelConfig(Model)`: `probe_stop`, `drain`, `cleanup`, `commit_grace` as `Duration`; `LoopLagConfig`: `interval`, `warn`. Field tables in §18.

### 8.3 Reserved error-code blocks (normative; the registry enforces it)

A block is the `NNNN` range of a code, **independent of category**: an element that owns block `0200–0299` may mint `RGE-STORE-0205` and `RGE-CONFIG-0210`. Uniqueness is per `(category, NNNN)`.

| Range | Owner |
|---|---|
| 0001–0019 | RG-P03-005 (this spec; §7.3) — all categories |
| 0020–0039 | RG-P03-002 serialization (see its §7.9) |
| 0040–0059 | RG-P03-004 logging/redaction |
| 0060–0069 / 0070–0079 | RG-P03-006 scheduler / RG-P03-007 event bus |
| 0080–0099 | reserved platform (unallocated) |
| 0100–0999 | RG-P02-001 … RG-P02-009: element `RG-P02-00k` owns `k·100 … k·100+99` |
| 1000–1199 | RG-P03-003 configuration (200 codes) |
| 1200–1399 | RG-P03-008 persistence store (200 codes) |
| 1400–1499 / 1500–1599 / 1600–1699 | RG-P03-009 plugins / RG-P03-010 engine / RG-P03-011 deployment |
| 1700–2799 | RG-P04-001 … RG-P04-011: `RG-P04-0kk` owns `1700+100·(kk−1)` + 99 |
| 2800–4199 | RG-P05-001 … RG-P05-014: base `2800+100·(kk−1)` |
| 4200–5199 | RG-P06-001 … RG-P06-010: base `4200+100·(kk−1)` |
| 5200–5699 | RG-P07-001 … RG-P07-005: base `5200+100·(kk−1)` |
| 5700–6799 | RG-P08-001 … RG-P08-011: base `5700+100·(kk−1)` |
| 6800–7399 | RG-P09-001 … RG-P09-006: base `6800+100·(kk−1)` |
| 7400–8099 | RG-P10-001 … RG-P10-007: base `7400+100·(kk−1)` |
| 8100–8799 | RG-P11-001 … RG-P11-007: base `8100+100·(kk−1)` |
| 8800–9899 | reserved (new elements request a block by CONTRACT CHANGE REQUEST) |
| 9900–9999 | test-only codes (`rg_core.testing`); never emitted by production code |

Example: RG-P05-004 (HTTP transport, kk=4) owns 3100–3199, e.g. `RGE-TRANSPORT-3101`; RG-P11-002 (scope, kk=2) owns 8200–8299, e.g. `RGE-SCOPE-8201`.

## 9. Inputs, outputs, and validation rules

`RgError` construction/serialisation rules (never raise; repairs are counted in `details["repaired"]` as a tuple of rule ids):

| Rule | Input | Repair/behaviour |
|---|---|---|
| E1 | `details` key not matching `^[a-z][a-z0-9_]{0,47}$` | renamed `invalid_key_<n>`; `repaired` gets `E1` |
| E2 | `details` value that is a `Secret` or any object whose class sets `__secret__ = True` | replaced by `"<secret>"` |
| E3 | `str` value > 512 code points | clipped with `…[+N]` |
| E4 | `bytes` | `"<bytes:N>"`; `Path`/`PurePath` → `os.fspath` string; `Enum` → `.value`; `int` beyond ±(2⁵³−1) → decimal string; `float` non-finite → `"<nan>"`/`"<inf>"` |
| E5 | `Mapping`/`list`/`set`/object | mapping/list/set → flat tuple of ≤ 32 scalars or `"<mapping:N>"`; other objects → `"<unserialisable:TypeName>"` |
| E6 | more than 32 keys | first 32 in sorted key order kept; `repaired` gets `E6` |
| E7 | `message` containing control characters or newlines | replaced by single spaces; clipped to 512 (record clips to 256) |
| E8 | `code` not matching the format | `InternalError RGE-INTERNAL-0006` is returned **instead** (the original code is moved to `details.bad_code`) |
| E9 | `category` differs from the code's category token | same as E8 |

Run-scope rules (violations raise `InternalError`): **S1** `RunScope` is entered once, on a running loop, from a task (`RGE-INTERNAL-0004`); **S2** `spawn` only while ACTIVE or CANCELLING (`RGE-INTERNAL-0004`); **S3** `loop.get_task_factory()` must be `None` (eager tasks reorder start; `RGE-INTERNAL-0003`); **S4** Python ≥ 3.11 and GIL build (`RGE-INTERNAL-0003`).

Executor rules: **X1** `name ∈ {probe, idp, store}` (`RGE-INTERNAL-0005`); **X2** called on the loop thread; **X3** `serial_key` ≤ 128 chars; **X4** `store` spec has `max_workers == 1`; **X5** `saturation_timeout_ns=None` only for `store` (violation → config error `RGE-CONFIG-1033` raised by RG-P03-003 rule X14; `ExecutorSet.__init__` re-checks with `RGE-INTERNAL-0005`).

Queue rules: **Q1** capacity ∈ [1, 1 000 000]; **Q2** `critical` items are never dropped by `drop_oldest`; **Q3** `put` after `close` raises `QueueClosed` (0005).

Deadline rules: **D1** `duration_ns ∈ [1, 10¹⁵]` (≈ 11.5 days); **D2** a `Deadline` is bound to one `clock_id`; using it with another clock raises `RGE-INTERNAL-0001` (`invariant=deadline_clock_mismatch`).

Outputs: only `RgError` subclasses cross module boundaries; `ErrorRecord` is the serialised form.

## 10. Detailed execution behavior

### 10.1 Raising and serialising errors
1. Raise site builds `ConfigError(CODE_X, "constant message", details={...}, cause=exc)`. 2. The constructor sanitises details (§9), sets `__cause__`, computes nothing time-dependent. 3. The catching layer that owns a `Clock` calls `err.to_record(scrub=redactor.redact_text, occurred_at=clock.now())`. 4. The record is stored as evidence/timeline note or logged; the Redactor (RG-P03-004) still runs at the boundary (defence in depth). `to_record` without `scrub` omits cause messages.

### 10.2 Run scope lifecycle (clock: injected, read only for budgets)
1. `async with RunScope("run", clock, budget=…) as scope:` checks S1–S4, creates an internal `asyncio.TaskGroup` (front group). 2. `spawn(role!=sink)` creates the task through the group (`tg.create_task`) after wrapping it: `critical=True` → exceptions propagate to the group (siblings cancelled, group raises `ExceptionGroup`); `critical=False` → the wrapper catches `Exception`, records `RgError` in `scope.failures`, returns `None`. 3. `spawn_sink` creates the task with `loop.create_task` inside `aio` (the only module allowed to, RG-LINT-003.b) and tracks it outside the group. 4. `cancel(reason)`: first call sets the token (`reason`, `cancelled=True`), cancels every **front** task (`probe`, `scheduler`, `worker`, `observer`) and the host task's pending waits are the caller's duty (`token`); sinks are untouched. 5. Front group exit: `__aexit__` awaits the group; native `CancelledError` children are ignored by the group; the first non-cancel exception cancels siblings. 6. After the front group ended: run `on_drain` callbacks (e.g. `queue.close()`), then `await_uncancellable(sinks, budget=drain_ns)`; sinks still pending after the budget are cancelled and listed in `scope.stuck`; on hard abort sinks are cancelled immediately. 7. Exit result: if the front group raised → `collapse_group` → raise the resulting `RgError` (with `__cause__` = the group) when `collapse=True`, else re-raise the group; if the host was cancelled → `CancelledError` propagates after step 6.

### 10.3 Abort protocol (soft → hard → force)
`AbortController` signal handler (main thread) increments `presses` and uses `loop.call_soon_threadsafe`: press 1 → `on_soft(CancelReason.signal)` (engine: `scope.cancel`, state machine → ABORTED then CLEANING_UP); press 2 → `on_hard()` (`scope.hard_abort()`: `CancelToken.hard=True`; cleanup waits end; residual items are left in the durable restoration ledger for `rg resume`); press 3 → `on_force()` (default supplied by the app: flush stderr, `os._exit(<operator_abort exit code>)`).
Budgets after press 1 at instant `t0`: front tasks must end by `t0 + probe_stop` (1 s); tasks still alive are recorded in `scope.stuck` and **abandoned** (their threads finish by their own I/O timeouts); then drain (≤ 5 s); then cleanup (§10.5) with `cleanup` budget (120 s).

### 10.4 Shielded commits
`shield_commit(coro, what=…, grace_ns, ledger)`: wraps `coro` in an inner task; awaits `asyncio.shield(inner)`. If the awaiting task is cancelled, it keeps waiting for `inner` up to `grace_ns` (clock race) and then **always re-raises `CancelledError`**. Ledger entry: `completed` (inner finished in time, result discarded to the caller but stored via `ledger` `error_code=None`), `failed` (inner raised: recorded with its code), or `unknown` (grace expired → `RGE-CANCELLED-0002`). The engine's cleanup consults `ledger.unknown()` and treats those operations as *possibly applied* (restores conservatively).
Shielding rules (what is shielded):

| Operation | Shielded | Reason |
|---|---|---|
| `ExperimentStore.transition/append_timeline/append_observation/append_event` | yes (`store` executor + `shield_commit`) | durable-before-act (NFR-REL-001); a half-written transition is worse than a late abort |
| `AuditLog.append` for mutating actions | yes, and failure is fatal for the action | TM-27 (fail closed) |
| `RevocationAction.execute/restore`, `AdminControl.apply` | yes | INTERFACE-CONTRACTS §2 rule 1 (report *unknown outcome* instead of swallowing) |
| CLEANING_UP phase | yes (`run_cleanup`, separate task) | restoration must outlive the abort |
| probes, oracle reads, scheduler timers, bus delivery, rendering | no | safe to discard |

### 10.5 Cleanup after abort
`run_cleanup(factory, clock, budget_ns, token)`: creates `cleanup = loop.create_task(factory(), name="cleanup")` (separate task, role `cleanup`); `await_uncancellable(cleanup, budget, token)`; returns `CleanupOutcome(status ∈ {completed, budget_exceeded, hard_aborted, failed}, value | error)`. Absorbed cancellations are counted; after the wait, if any cancellation was absorbed and `reraise=True`, `CancelledError` is re-raised so the host still ends as cancelled. `budget_exceeded` → `RGE-CANCELLED-0003`; `hard_aborted` → `RGE-CANCELLED-0004`; both are recorded in the run manifest and reported as residual state (FR-EXP-007).

### 10.6 `run_blocking`
1. Check X1–X3 and that `ExecutorSet` is open. 2. `submitted = clock.now()`. 3. Acquire a *slot* from the executor's `asyncio.Semaphore(max_workers + queue_capacity)`: `saturation_timeout_ns` governs the wait (race with `clock.sleep`); expiry → `TimingError RGE-TIMING-0002`, `rejected += 1`. 4. If `serial_key`: await the key's FIFO lock. 5. `ctx = contextvars.copy_context()`; submit `_timed(ctx, fn, args)` to the `ThreadPoolExecutor`; inside the worker thread: `started = clock.now()`; `value = ctx.run(fn, *args)`; `finished = clock.now()`. 6. Await the wrapped future. If the awaiting task is cancelled: with `shield=False` the future is cancelled if still queued, otherwise the thread continues and its result is discarded; slot and key lock are released **only when the thread finishes** (done-callback via `call_soon_threadsafe`). With `shield=True` the call is wrapped by `shield_commit` semantics. 7. Return `BlockingResult(value, submitted, started, finished)`; queueing delay = `started.mono_ns − submitted.mono_ns`, recorded into `ExecutorStats.max_queue_delay_ns` and emitted as metric `executor.queue_delay`.

### 10.7 Queues
`put` per policy (§12.4). `close()` wakes all waiters; blocked putters get `QueueClosed`; getters drain remaining items then raise `QueueClosed`. `blocked_total_ns` accumulates clock time spent blocked in `put` (backpressure measure).

## 11. State transitions and invariants

`RunScope`: `NEW → ACTIVE → CANCELLING → DRAINING → CLOSED` (CANCELLING skipped without abort; ACTIVE → DRAINING when all front tasks end normally).

| From | Event | To |
|---|---|---|
| NEW | `__aenter__` | ACTIVE |
| ACTIVE | `cancel(reason)` | CANCELLING |
| ACTIVE/CANCELLING | front group finished | DRAINING |
| DRAINING | sinks finished or drain budget/`hard_abort` | CLOSED |
| CLOSED | any `spawn` | error `RGE-INTERNAL-0004` |

`AbortController`: `IDLE → SOFT → HARD → FORCED` on presses 1/2/3.

Invariants:
- **INV-1** Every task created by `aio` has exactly one owner scope; after `RunScope.__aexit__` returns, none of its tasks is pending except those in `scope.stuck` (and those are cancelled).
- **INV-2** `RgError` instances are immutable and `str(err)` contains neither `details` nor cause text.
- **INV-3** `to_record(...)` never contains a `Secret` material substring when `details` were built from `Secret`s (E2) and never contains cause messages unless `scrub` is supplied.
- **INV-4** `Deadline.remaining_ns()` is non-increasing for a fixed clock and equals `max(0, due − mono_ns)`.
- **INV-5** `slots_in_use ≤ max_workers + queue_capacity` at all times; `running ≤ max_workers`.
- **INV-6** In `drop_oldest` queues a `critical` item is never dropped; `depth ≤ capacity` except while a `critical` put is blocked (depth stays ≤ capacity; the putter waits).
- **INV-7** `shield_commit` never returns normally after the caller was cancelled (always re-raises `CancelledError`).
- **INV-8** The ledger contains exactly one record per `shield_commit` call.
- **INV-9** With a virtual clock no `aio` function performs a wall-clock wait (no `time.sleep`, `loop.call_later`, `asyncio.sleep`, `asyncio.timeout`).
- **INV-10** The first `CancelReason` set on a token is never overwritten.
- **INV-11** `ErrorRegistry` has no two entries with equal `(category, NNNN)`, and every entry's `NNNN` lies in its owner's block.

## 12. Core algorithms and pseudocode

### 12.1 `collapse_group` (exception groups from `TaskGroup`)
```
SEVERITY = [INTERNAL, SCOPE, STORE, UPSTREAM_COMPAT, PLUGIN, CONFIG, AUTH, PROVIDER, TARGET, ASSERTION, TRANSPORT, TIMING, CANCELLED]   # index = rank
def collapse_group(group, where):
    leaves = leaf_exceptions(group)                       # depth-first, completion order
    real = [e for e in leaves if not isinstance(e, asyncio.CancelledError)]
    if not real: return asyncio.CancelledError()          # every leaf was a cancellation
    errs = [e if isinstance(e, RgError) else wrap_unexpected(e, where=where) for e in real]   # KeyboardInterrupt/SystemExit are re-raised, never wrapped
    primary = min(errs, key=lambda e: (SEVERITY.index(e.category), errs.index(e)))             # best rank, then first to fail
    others = [e for e in errs if e is not primary]
    return primary.with_details(suppressed_count=len(others),
                                suppressed=tuple(e.code for e in others[:16]), cause=group)
```
Worked example: group leaves in completion order = `[TransportError RGE-TRANSPORT-3101, StoreError RGE-STORE-1201, CancelledError, ValueError]` → real = 3 → `ValueError` wrapped as `RGE-INTERNAL-0002`; ranks: INTERNAL 0, STORE 2, TRANSPORT 10 → primary = the wrapped `ValueError` (`RGE-INTERNAL-0002`), `suppressed_count=2`, `suppressed=("RGE-STORE-1201","RGE-TRANSPORT-3101")`. If only `[TransportError, StoreError]` → primary `RGE-STORE-1201`.

### 12.2 `Deadline.run`
```
async def run(self, awaitable, *, what):
    work = ensure_future(awaitable); sleeper = ensure_future(clock.sleep_until(self.due))
    try:
        done, _ = await asyncio.wait({work, sleeper}, return_when=FIRST_COMPLETED)
        if work in done: return work.result()                     # propagates work's exception
        await cancel_and_wait(work, clock=clock, budget_ns=1_000_000_000)
        raise TimingError(DEADLINE_EXCEEDED, "Deadline exceeded", details={"what": what, "budget_ns": self.budget_ns})
    finally:
        for t in (work, sleeper): if not t.done(): t.cancel()
        # then await sleeper's cancellation to avoid "Task was destroyed but it is pending"
```
Numeric example (mono ns): `now=5_000_000_000`, `Deadline.after(clock, 2_000_000_000)` → `due=7_000_000_000`. At `now=6_800_000_000` `child(500_000_000)` → `min(7_000_000_000, 6_800_000_000+500_000_000)=7_000_000_000`, `remaining=200_000_000`; at `now=6_900_000_000` a child with `max_ns=50_000_000` → `due=6_950_000_000`.

### 12.3 `await_uncancellable`
```
async def await_uncancellable(task, *, clock, budget_ns, token=None, reraise=True):
    budget = ensure_future(clock.sleep(budget_ns)); hard = ensure_future(token.wait_hard()) if token else None
    absorbed = 0; status = "completed"
    try:
        while True:
            try: await asyncio.wait({task, budget} | ({hard} if hard else set()), return_when=FIRST_COMPLETED)
            except asyncio.CancelledError: absorbed += 1; continue       # asyncio.wait does not cancel `task`
            if task.done(): break
            status = "hard_aborted" if (hard and hard.done()) else "budget_exceeded"; break
    finally: cancel(budget, hard)
    if absorbed and reraise: raise asyncio.CancelledError()
    return AwaitOutcome(status, absorbed, task if task.done() else None)
```
(Author-verified prototype on CPython 3.11 and 3.13: a cleanup task completes although the host is cancelled twice; hard abort and budget expiry end the wait with the cleanup task still pending — A-2.)

### 12.4 `BoundedQueue.put`
```
def _try_put(item, critical):                       # returns PutResult or None (= must wait)
    if len(q) < capacity: q.append((item, critical)); return accepted
    if policy == "fail": raise QueueFull(TIMING-0003)
    if policy == "drop_oldest":
        i = index of oldest entry with critical == False
        if i is not None: del q[i]; q.append((item, critical)); dropped += 1; return dropped_oldest
        if not critical: dropped += 1; return dropped_self            # queue full of critical items: the new non-critical item is discarded
        return None                                                    # critical put into an all-critical full queue: wait
    return None                                                        # policy == "block": wait
async def put(item, critical=False):
    while True:
        r = _try_put(item, critical)
        if r is not None: wake_getter(); return r
        t0 = clock.mono_ns(); await not_full.wait(); blocked_total += clock.mono_ns() - t0      # not_full is an asyncio.Event re-armed by get()
```
Worked example, capacity 3, policy `drop_oldest` (items `(name, critical)`): put `a`(n), `b`(c), `c`(n) → `[a,b,c]`; put `d`(n) → drops `a` → `[b,c,d]`, `dropped=1`; put `e`(c) → drops `c` → `[b,d,e]`; put `f`(c) → drops `d` → `[b,e,f]`; put `g`(c) → no non-critical entry → waits; put `h`(n) → `dropped_self`; after one `get()` removes `b` the waiting `g` is accepted → `[e,f,g]`, `dropped=3`.

### 12.5 Executor slot accounting
Slots = `max_workers + queue_capacity`. Example probe defaults (64 workers, 256 queue → 320 slots): 400 concurrent `run_blocking` calls → 64 running, 256 queued in the pool, 80 waiting on the semaphore; each waiter gives up after `saturation_timeout` (2 s) with `RGE-TIMING-0002` (the probe runner records `not_sent` reason `executor_saturated`, RG-P05-014); when workers finish, waiters are admitted FIFO.

### 12.6 `AbortController` handler
```
def _handler(signum, frame):                       # main thread, between bytecodes
    self.presses += 1; n = self.presses
    loop.call_soon_threadsafe({1: lambda: on_soft(CancelReason.signal), 2: on_hard}.get(n, on_force))   # n>=3 → force
```
Installed signals: POSIX `SIGINT`, `SIGTERM`; Windows `SIGINT` (Ctrl+C) and `SIGBREAK` (Ctrl+Break). `loop.add_signal_handler` is never used (unsupported on Windows loops).

### 12.7 Lint rules (checks, scope, fixtures)

**Scope (production paths):** `src/rg_core/**`, `src/rg_probe/**`, `src/rg_idp/**`, `src/rg_stbridge/**`, `src/revocationgap/{engine,service,store,config}/**`. Excluded: `tests/**`, `src/rg_lab/**` (virtual-time driver owns real timers), `src/revocationgap/{cli,gui,api}/**` for RG-LINT-001 only. The single allow-listed time reader is `src/rg_core/time/system_clock.py` (`per-file-ignores`); any other suppression is `# noqa: TID251 -- RG-LINT-001: <reason ≥ 10 chars>` and CI prints the count (budget 0 outside `system_clock.py`).

**RG-LINT-001 — no direct time/sleep.** Implemented by ruff `TID251` banned-api (matches qualified names through import aliases; author-verified with ruff 0.17.0, A-4) plus rglint sub-rule `.b`:

```toml
[tool.ruff.lint]
select = ["TID251", "ASYNC"]
[tool.ruff.lint.flake8-tidy-imports.banned-api]
# each msg starts with "RG-LINT-001: use the injected Clock/Scheduler"
"time.time" = {msg="RG-LINT-001"}  "time.time_ns" "time.monotonic" "time.monotonic_ns" "time.perf_counter" "time.perf_counter_ns"
"time.sleep" "time.localtime" "time.gmtime" "datetime.datetime.now" "datetime.datetime.utcnow" "datetime.datetime.today" "datetime.date.today"
"asyncio.sleep" "asyncio.wait_for" "asyncio.timeout" "asyncio.timeout_at" "threading.Timer" "uuid.uuid1"      # same entry shape
```
rglint `.b`: any call to an attribute named `call_later` or `call_at` (loop timers).
Fixture `tests/lint/fixtures/lint001/bad_time.py` (lines as comments) and expected ruff output (author-run):

| File:line | Expected |
|---|---|
| `bad_time.py:6` | `TID251 time.monotonic` (alias import `from time import monotonic as mono`; the later call `mono()` on line 12 is **not** separately reported) |
| `:10` `time.time()` | `TID251 time.time` |
| `:11` `t.perf_counter_ns()` (alias `import time as t`) | `TID251 time.perf_counter_ns` |
| `:13` `datetime.datetime.utcnow()` | `TID251 datetime.datetime.utcnow` |
| `:14` `dt.now()` (`from datetime import datetime as dt`) | `TID251 datetime.datetime.now` |
| `:19` `await asyncio.sleep(1)` | `TID251 asyncio.sleep` |
| `:20` `asyncio.wait_for(...)` | `TID251 asyncio.wait_for` |
| `:21` `async with asyncio.timeout(1)` | `TID251 asyncio.timeout` |

and `tests/lint/fixtures/lint001/bad_loop_timer.py`: `loop.call_later(1, f)` on line 6 → `RG-LINT-001.b`. Clean fixture `ok_clock.py` (uses `clock.now()`, `await clock.sleep(n)`) → 0 findings.

**RG-LINT-002 — no blocking calls on the event loop.** Inside an `async def` body (excluding nested `def`/`lambda`, which are the intended offload targets), flag: ruff `ASYNC210` (blocking HTTP via `requests`/`httpx`), `ASYNC220/221/222` (processes), `ASYNC230`/`ASYNC240` (`open`, blocking pathlib), `ASYNC250` (`input`), `ASYNC251` (`time.sleep`) — all author-verified to fire (A-4) — plus rglint sub-rules:

| Sub-rule | Pattern (AST) | Why |
|---|---|---|
| `.a` | call on module `sqlite3`, or `execute/executemany/executescript/commit/cursor/close` on a name assigned from `sqlite3.connect(...)` | store I/O belongs on the `store` executor |
| `.b` | `x.submit(...).result()`; `.join()` on a name containing `thread`; `.acquire()` with no args | blocks the loop thread |
| `.c` | `get/post/put/delete/patch/head/options/request/send` on a name assigned from `requests.Session(...)`/`requests.session()` | Session methods are not covered by ASYNC210 |
| `.d` | any call to `.call(...)` or `.call_and_validate(...)` | Schemathesis `Case.call` is blocking (ADR-0004) |
| `.e` | `hashlib.pbkdf2_hmac`, `hashlib.scrypt` | CPU-bound KDF |
| `.f` | `socket.create_connection/getaddrinfo/gethostbyname`; `connect/recv/send/sendall/accept/recvfrom` on a name assigned from `socket.socket(...)` | blocking DNS/sockets |
| `.g` | `read_text/read_bytes/write_text/write_bytes`; `os.fsync/os.replace/os.makedirs`, `shutil.copy/copyfile/rmtree` | blocking file system |
| `.h` | `input()` | blocking console |
| `.i` | `asyncio.run(...)`, `.run_until_complete(...)` | nested event loop |

Pragma for a justified exception: `# rg-lint: allow(RG-LINT-002.d) -- <reason ≥ 10 chars>` on the same line; a pragma without a reason is itself reported as `RG-LINT-000`. Fixture `tests/lint/fixtures/lint002/bad_blocking.py` with expected rglint findings (author-run prototype):

| Line | Code | Statement |
|---|---|---|
| 12, 13 | `.a` | `sqlite3.connect(...)`, `conn.execute(...)` |
| 15 | `.c` | `s.get(...)` where `s = requests.Session()` |
| 17, 18 | `.f` | `sock.connect(...)`, `socket.getaddrinfo(...)` |
| 19 | `.d` | `case.call()` |
| 20 | `.g` | `Path("a").read_text()` (ruff also reports `ASYNC240`) |
| 21 | `.e` | `hashlib.pbkdf2_hmac(...)` |
| 22, 23, 24 | `.b` | `pool.submit(print).result()`, `worker_thread.join()`, `lock.acquire()` |
| 25 | `.i` | `asyncio.run(...)` |
| 26 | `.h` | `input()` (ruff also reports `ASYNC250`) |
| 28–30 (nested `def offloaded`) | none | sync function offload target |
| 32 | none | pragma with reason on the line |

**RG-LINT-003 — portable and structured asyncio.** rglint-only. `.a` forbids `add_signal_handler`, `add_reader`, `add_writer` (NotImplemented on Windows loops), `asyncio.get_event_loop_policy/set_event_loop_policy`, `asyncio.Windows*EventLoopPolicy`, `asyncio.get_event_loop` (policy APIs are deprecated on newer Pythons; A-5). `.b` forbids `asyncio.create_task`, `asyncio.ensure_future`, `<loop>.create_task` outside `src/rg_core/aio/**` (all tasks go through `RunScope.spawn`); `tg.create_task` inside `aio` is allowed. `.c` forbids string literals matching `RGE-[A-Z_]+-\d{4}` outside `codes.py` modules and tests (codes must be the declared constants). Fixture `bad_asyncio_misc.py`: line 5 `.a` (`loop.add_signal_handler`), 6 `RG-LINT-001.b`, 7 `.a` (`set_event_loop_policy`), 8 `.b` (`asyncio.create_task`).

CI jobs: `ruff check src` and `python tools/rglint.py src` both required; fixtures run by `tests/lint/test_rules.py` (TST-RG-P03-005-18/-19/-20).

## 13. Internal functions, methods, or service operations

| Function | Signature | Purpose |
|---|---|---|
| `_sanitise_details` | `(raw: Mapping[str, object] \| None) -> tuple[Mapping[str, DetailValue], tuple[str, ...]]` | rules E1–E6 |
| `_clean_message` | `(s: str) -> str` | rule E7 |
| `_rank` | `(c: ErrorCategory) -> int` | severity index |
| `_wrap_task` | `(coro, *, scope, critical, name) -> Coroutine` | supervised wrapper |
| `_timed` | `(ctx, fn, args, clock) -> tuple[T, TimeInstant, TimeInstant]` | worker-side bracket |
| `_Slot` | async context manager | acquire/release executor slots with saturation timeout |
| `_KeyLocks` | class | FIFO per-key locks, released from worker done-callback |
| `_QueueCore` | class | deque + events used by `BoundedQueue` |
| `_check_environment` | `() -> None` | S3, S4 |
| `rglint._Visitor` | `ast.NodeVisitor` | rules of §12.7 with scope tracking (`async_depth`, `sync_in_async`, name-assignment tables) |

## 14. Error handling and failure recovery

| Failure | Detection | Handling | Recovery | Code |
|---|---|---|---|---|
| Child task raises (critical) | `TaskGroup` | siblings cancelled; group collapsed | engine → FAILED, cleanup | the child's code (primary) |
| Supervised child raises | wrapper | recorded in `scope.failures`; run continues | engine decides per role | child's code |
| Task ignores cancel beyond `probe_stop` | `cancel_and_wait` budget | abandoned; listed in `scope.stuck`; warning `runscope.task_stuck` | thread finishes by own timeout | — (metric `runscope.stuck_tasks`) |
| Executor saturated | slot wait > timeout | `TimingError` | probe → `not_sent`; admin call → caller error | RGE-TIMING-0002 |
| Blocking call hangs | `Deadline.run` around `run_blocking` | caller unblocked; thread abandoned, slot held until it ends | per-call I/O timeout reclaims the slot | RGE-TIMING-0001 |
| Cancelled during state-changing call | `shield_commit` grace expiry | ledger `unknown` | cleanup restores conservatively | RGE-CANCELLED-0002 |
| Cleanup overruns budget | `await_uncancellable` | outcome `budget_exceeded`; run ends with residuals reported | `rg resume` finishes restoration | RGE-CANCELLED-0003 |
| Second Ctrl+C | `AbortController` | cleanup wait abandoned | durable restoration ledger | RGE-CANCELLED-0004 |
| Queue full | policy | per policy (block/drop/fail) | backpressure | RGE-TIMING-0003 (fail only) |
| Queue closed | `close()` | getters drain then error | normal shutdown | RGE-CANCELLED-0005 |
| Undeclared code at runtime | `ErrorRegistry` (debug/test builds) | returns InternalError | fix declaration | RGE-INTERNAL-0006 |
| Eager task factory / old Python | S3/S4 | refuse to start run | fix environment | RGE-INTERNAL-0003 |
| Signal on non-main thread install | `install` | raise | call from main thread | RGE-INTERNAL-0005 |

Partial-failure semantics: `ExecutorSet.aclose` returns the labels of calls still running; it never hides them. `RunScope.__aexit__` always completes sink draining before raising the collapsed error.

## 15. Security requirements and trust boundaries

* **TM-07 / FR-SEC-005:** exceptions are the most common secret leak (URLs with tokens inside `requests` exceptions, `repr` of headers). Mitigations here: `RgError.__str__`/`__repr__` omit details and causes; details are flat and sanitised (E2–E5); `to_record` omits non-RG cause messages unless a scrubber is passed; raw foreign exceptions are wrapped (`wrap_unexpected` keeps only the type name). RG-P03-004 redacts tracebacks and never captures locals.
* **TM-34 / FR-SEC-009:** all queues and executors bounded; defaults in §18; `fail`/`block` policies explicit; evidence-bearing queues cannot be configured to drop (config validator rejects `drop_oldest` for `store`/observation sinks).
* **TM-10:** per-probe memory bound = executor slot count × per-probe cap (RG-P05-004).
* **TM-28:** `Deadline` reads only the monotonic clock of the injected `Clock`; RG-LINT-001 removes direct time sources.
* **TM-29:** `idp` executor (8 workers) bounds concurrent admin/oracle calls regardless of probe concurrency; `serial_key` per tenant/identity prevents concurrent admin mutations on one identity.
* **TM-27:** audit append is shielded and fail-closed (see §10.4).
* **Trust boundary:** signal handlers run in the main thread and only touch counters and `call_soon_threadsafe` (async-signal-safe subset of Python); no I/O in handlers.
* **Pickle:** `RgError` pickles by `(class, code, message, retryable, details-as-dict)` without causes, because process boundaries (future workers, RG-P14-001) must not carry foreign exception objects.

## 16. Concurrency, asynchronous behavior, and resource ownership

* **Loop ownership:** one event loop per experiment run in the main thread of the CLI/GUI process (GUI server hosts additional servers natively on the same loop); `aio` objects are **loop-confined** except where stated thread-safe: `CancelToken` (read), `RunScope.cancel`, `BoundedQueue.put_threadsafe`, `ExecutorSet.stats`, `IdFactory`-like pure helpers.
* **Threads:** `ThreadPoolExecutor` per executor name, `thread_name_prefix="rg-<name>"`; `store` has exactly one thread (SQLite connection identity is that thread; RG-P03-008 opens and closes its connection by submitting jobs to the `store` executor); `probe`/`idp` threads are interchangeable — `serial_key` gives per-key mutual exclusion and FIFO order, **not** thread identity (A-7).
* **Context propagation:** `contextvars.copy_context()` at submission; correlation ids (`experiment_id`, `probe_id`, `attempt_id`, RG-P03-004) therefore appear in worker-thread logs. `asyncio.to_thread` is not used directly (RG-LINT-003 does not ban it, but it bypasses bounded slots; code review rule).
* **Locks:** no `threading.Lock` is held across an `await`; `IdFactory`-style locks guard ≤ 10 µs sections only.
* **Ownership/teardown order (engine contract):** (1) `RunScope` exit (tasks, sinks) → (2) cleanup → (3) `ExecutorSet.aclose` (`probe`, `idp`, then `store` last so final commits flush) → (4) event loop close. `ExecutorSet.aclose` calls `shutdown(wait=False, cancel_futures=True)` after the budget and reports abandoned labels; interpreter exit still joins non-daemon pool threads, bounded by each call's I/O timeout.
* **Backpressure rules (normative table):**

| Queue | Policy | Rationale |
|---|---|---|
| observation/evidence sink → store writer | `block` | evidence never dropped (NFR-REL-003); probes slow and lateness is recorded |
| store writer submission (executor `store`) | wait indefinitely | durability |
| probe submission (executor `probe`) | wait ≤ 2 s then `not_sent(executor_saturated)` | keeps lateness bounded and honest |
| event-bus subscriber (default) | `drop_oldest`, `critical` protected | UI/metrics may lose non-critical events; `dropped` counter exposed (RG-P03-007) |
| GUI SSE client | `drop_oldest` | slow browser must not stall the run |
| inbound event receiver (CAEP/back-channel) | `fail` → HTTP 503 | TM-20/TM-21 floods |
| log handler queue (if any) | `drop_oldest` for DEBUG/INFO, `block` never | logging must not stall measurements; WARNING+ marked critical |

## 17. Performance and resource requirements

Proposals with validating tests (not measured facts):

| Budget | Value | Rationale | Test |
|---|---|---|---|
| Abort → all front tasks ended | ≤ 1 s (default `probe_stop`), typically ≪ 100 ms | FR-OPS-006 | TST-RG-P03-005-10 |
| `run_blocking` overhead (no-op `fn`) | p95 ≤ 200 µs added latency, p99 ≤ 1 ms on Linux; Windows p95 ≤ 1 ms | NFR-PERF-001 budget is 25 ms p95 for everything | TST-RG-P03-005-22 |
| `BoundedQueue` put+get | ≤ 10 µs mean | event rates ≤ 10⁴/s | TST-RG-P03-005-22 |
| `RgError` construct + `to_record` | ≤ 20 µs mean | error paths under fault injection | TST-RG-P03-005-22 |
| Loop lag under 50 concurrent in-flight probes | p99 ≤ 25 ms (Linux), reported on Windows | NFR-PERF-001 | TST-RG-P03-005-23 |
| Threads | ≤ 64 + 8 + 1 = 73 default (+512 max probe) | NFR-PERF-003: 200 in-flight needs `probe.max_workers ≥ 200` | TST-RG-P03-005-24 |
| Memory per queued call | ≤ 2 KiB bookkeeping | NFR-PERF-006 | TST-RG-P03-005-24 |

## 18. Configuration and defaults

Sections registered into the RG-P03-003 registry as sub-sections of `[engine]` (owner RG-P03-005). Env var = `RG_` + path joined by `_`, upper-case.

| Key | Type | Default | Range | Env | Reload class | Failure behaviour |
|---|---|---|---|---|---|---|
| `engine.cancel.probe_stop` | Duration | `1s` | 100ms–30s | `RG_ENGINE_CANCEL_PROBE_STOP` | next_run | `RGE-CONFIG-1023` (out of range) |
| `engine.cancel.drain` | Duration | `5s` | 0s–5m | `RG_ENGINE_CANCEL_DRAIN` | next_run | idem |
| `engine.cancel.cleanup` | Duration | `120s` | 1s–1h | `RG_ENGINE_CANCEL_CLEANUP` | next_run | idem |
| `engine.cancel.commit_grace` | Duration | `5s` | 100ms–60s | `RG_ENGINE_CANCEL_COMMIT_GRACE` | next_run | idem |
| `engine.executors.probe.max_workers` | int | 64 | 1–512 | `RG_ENGINE_EXECUTORS_PROBE_MAX_WORKERS` | restart | idem; cross-check `limits.max_concurrent_probes ≤ max_workers` |
| `engine.executors.probe.queue_capacity` | int | 256 | 0–4096 | `RG_ENGINE_EXECUTORS_PROBE_QUEUE_CAPACITY` | restart | idem |
| `engine.executors.probe.saturation_timeout` | Duration | `2s` | 0s–5m | `RG_ENGINE_EXECUTORS_PROBE_SATURATION_TIMEOUT` | restart | `0s` = fail immediately |
| `engine.executors.idp.max_workers` | int | 8 | 1–64 | `RG_ENGINE_EXECUTORS_IDP_MAX_WORKERS` | restart | idem |
| `engine.executors.idp.queue_capacity` | int | 64 | 0–1024 | `RG_ENGINE_EXECUTORS_IDP_QUEUE_CAPACITY` | restart | idem |
| `engine.executors.idp.saturation_timeout` | Duration | `30s` | 0s–5m | `RG_ENGINE_EXECUTORS_IDP_SATURATION_TIMEOUT` | restart | idem |
| `engine.executors.store.max_workers` | int | 1 | exactly 1 | `RG_ENGINE_EXECUTORS_STORE_MAX_WORKERS` | restart | other values rejected |
| `engine.executors.store.queue_capacity` | int | 1024 | 16–65536 | `RG_ENGINE_EXECUTORS_STORE_QUEUE_CAPACITY` | restart | idem |
| `engine.executors.store.saturation_timeout` | Duration \| `"none"` | `"none"` (wait indefinitely) | `"none"` or 1s–1h | `RG_ENGINE_EXECUTORS_STORE_SATURATION_TIMEOUT` | restart | only `store` may use `"none"` |
| `engine.loop_lag.interval` | Duration | `100ms` | 10ms–10s | `RG_ENGINE_LOOP_LAG_INTERVAL` | live | idem |
| `engine.loop_lag.warn` | Duration | `100ms` | 1ms–10s | `RG_ENGINE_LOOP_LAG_WARN` | live | idem |

Precedence/provenance rules are RG-P03-003's. Library defaults equal the table (`CancelBudget`, `ExecutorSpec` factories).

## 19. Logging, observability, evidence requirements

Events (logger `rg.aio`, correlation ids bound by the caller): `runscope.opened{name}`, `runscope.cancel_requested{name,reason}`, `runscope.front_ended{name,elapsed_ns}`, `runscope.drained{name,elapsed_ns,stuck}`, `runscope.task_stuck{task}`, `executor.saturated{executor,waited_ns}`, `executor.slow_call{label,duration_ns}` (≥ 5 s), `queue.overflow{queue,policy,dropped}`, `abort.press{n}`, `commit.unknown{what}`, `cleanup.outcome{status}`. Metrics (names per RG-P03-004 §10.7 conventions; architecture's informal `scheduling_lateness`/`queue_depth` are aliases): `executor.queue_depth{executor}`, `executor.queue_delay{executor}` (ns), `executor.running{executor}`, `queue.depth{queue}`, `queue.dropped.count{queue}`, `queue.blocked_time{queue}`, `loop.lag` (ns), `runscope.stuck_tasks`. Evidence: `ErrorRecord` items (kind `error_record`) for every failed operation that affects a result; run manifest gets `abort: {presses, reason, cleanup_status}`, `commit_ledger` summary (counts and any `unknown` entries) and `executors` effective sizes. Redaction: all log fields pass the Redactor; `details` never contains free-form untrusted text (E3 caps) but is redacted regardless.

## 20. Platform compatibility

| Topic | Linux/macOS | Windows |
|---|---|---|
| Event loop | default selector loop | default **ProactorEventLoop** (Python ≥ 3.8): no `add_signal_handler`, no `add_reader/add_writer` → RG-LINT-003.a; never call `set_event_loop_policy` (deprecated APIs avoided; CI `-W error::DeprecationWarning` on 3.14) |
| Abort signals | `SIGINT`, `SIGTERM` via `signal.signal` + `call_soon_threadsafe` | `SIGINT` (Ctrl+C), `SIGBREAK` (Ctrl+Break); `SIGTERM` from `os.kill`/Task Manager is `TerminateProcess` and cannot be caught; console-close events are not caught (v1 limitation → recovery via `rg resume`) |
| Loop wake on signal | self-pipe via `call_soon_threadsafe` | same; relies on the Proactor loop's wake-up (A-3) |
| Timer granularity | `time.monotonic` ns-resolution | asyncio timers use `time.monotonic` whose resolution on Windows for Python < 3.13 is reported ≈ 15.6 ms (NFR-PERF-002, tag U) → loop timers can be late by one tick; RG-P03-006 must not rely on `loop.call_at` precision; `LoopLagMonitor` quantifies it; benchmark TST-RG-P03-005-23 runs on Windows |
| Threads | `ThreadPoolExecutor`, stack 8 MiB virtual (RSS small) | default 1 MiB stacks; 73 threads fine |
| Paths/encodings | n/a | n/a (no file I/O here) |
| Python 3.11–3.14 | `TaskGroup`, `except*`, `uncancel` behave identically on 3.11–3.13 in the author's checks; 3.14 verified by CI (A-1) | same |

## 21. Edge cases and invalid inputs

| # | Case | Expected behaviour |
|---|---|---|
| E-1 | `RgError(CONFIG, "RGE-STORE-0001", …)` (category/code mismatch) | returns `InternalError RGE-INTERNAL-0006` with `details.bad_code`; does not raise |
| E-2 | `details={"Token": Secret("x"), "a b": 1}` | keys repaired (`invalid_key_1`, `invalid_key_2`), `repaired=("E1",)`; value `"<secret>"` |
| E-3 | details with a nested dict | replaced by `"<mapping:N>"` |
| E-4 | `collapse_group` of only `CancelledError` leaves | returns `CancelledError` (re-raised by caller) |
| E-5 | group containing `KeyboardInterrupt` | `KeyboardInterrupt` is re-raised, not wrapped |
| E-6 | `spawn` after scope closed | `RGE-INTERNAL-0004` |
| E-7 | Task catches `CancelledError` and continues | after `probe_stop` listed in `scope.stuck`, abandoned; run proceeds; conformance kit fails such a task in tests |
| E-8 | `cancel()` called twice with different reasons | first reason retained (INV-10) |
| E-9 | `Deadline.after(clock, 0)` | `ValueError`-class misuse → `RGE-INTERNAL-0001` (`invariant=deadline_duration`) |
| E-10 | `run_blocking` whose `fn` raises `RgError` | exception propagates unchanged; slot released |
| E-11 | `run_blocking` whose `fn` raises a foreign exception | wrapped by `wrap_unexpected(where=label)` |
| E-12 | queue capacity 0 or 1_000_001 | `RGE-INTERNAL-0001` (`invariant=queue_capacity`) |
| E-13 | `put` on closed queue / `get` on closed empty queue | `RGE-CANCELLED-0005` |
| E-14 | `AbortController.install` called off the main thread | `RGE-INTERNAL-0005` |
| E-15 | three SIGINTs within one loop iteration | each increments; actions 1,2,3 are scheduled in order |
| E-16 | `serial_key` task cancelled while running | key lock stays held until the thread ends (no concurrent mutation) |
| E-17 | virtual clock: `Deadline.run` where work completes at the same virtual instant as the deadline | work wins (result delivered); tie rule: `work in done` is checked first |
| E-18 | executor `store` configured `max_workers=2` | config error; `ExecutorSet` re-check raises `RGE-INTERNAL-0005` |

## 22. Unit and integration test requirements

- **TST-RG-P03-005-01** Error construction: all 13 subclasses fix their category; code format regex; E8/E9 repair; `str/repr` contain neither details values nor cause text; pickle round-trip keeps `(code, message, retryable, details)` and drops cause.
- **TST-RG-P03-005-02** Details sanitisation E1–E6 table (secret, bytes, Path, Enum, big int, NaN, nested mapping, 33 keys, 600-char string); property: for random nested inputs the sanitised `details` always satisfies the flat-type schema and never contains a registered canary string.
- **TST-RG-P03-005-03** `to_record`: example of §8.1; cause chain depth cap 5 with a cycle; foreign cause message omitted without `scrub`, present and passed through `scrub` with it; `occurred_at` passthrough; JSON round-trip via RG-P03-002 `dump_document`; schema golden for `SCH-ERROR`.
- **TST-RG-P03-005-04** `ErrorRegistry.build`: rejects duplicate `(category, NNNN)`, out-of-block code, bad format; accepts all declared codes of installed packages; alias `RGE-PROVIDER-UNSUPPORTED` resolves to `RGE-PROVIDER-0001`; AST scan of `src/**` finds no code literal outside `codes.py` (RG-LINT-003.c).
- **TST-RG-P03-005-05** `collapse_group` vectors: §12.1 worked example (primary `RGE-INTERNAL-0002`, suppressed list), only-cancel group, nested groups flattened in completion order, `KeyboardInterrupt` re-raise, tie on severity picks the first failure.
- **TST-RG-P03-005-06** `exit_kind_of`: CONFIG→`config_error`, SCOPE→`scope_refusal`, INTERNAL→`internal_error`, CANCELLED with reason `operator`/`signal`/`hard` → `operator_abort`, CANCELLED with `quota` → `failure`, TRANSPORT → `failure`, `None` → `ok`.
- **TST-RG-P03-005-07** RunScope structured concurrency under `VirtualClock`: critical child failure cancels siblings and raises the collapsed error with `__cause__` group; supervised failure recorded in `scope.failures` and run continues; no pending tasks after exit (`asyncio.all_tasks()` snapshot) — repeated on every CI Python (3.11–3.14).
- **TST-RG-P03-005-08** Scope misuse S1–S4: double enter, spawn after close, eager task factory installed (3.12+ only), call outside a task → documented codes.
- **TST-RG-P03-005-09** Cancel reason semantics: first reason wins (INV-10); `cancel` from another thread via `call_soon_threadsafe`; `CancelToken` readable from a worker thread; `raise_if_cancelled` raises native `CancelledError`.
- **TST-RG-P03-005-10** Abort budget: 50 probe-role tasks blocked in `await clock.sleep(10 s)` plus 5 tasks inside `run_blocking` (threads sleeping 300 ms on a `threading.Event`): after `cancel(operator)` all awaiting tasks end within `probe_stop`; threads finish within their timeout; `scope.stuck` is empty; a deliberately non-cooperative task (swallows `CancelledError`) ends in `scope.stuck` after `probe_stop` (virtual time).
- **TST-RG-P03-005-11** Sink draining: store-writer sink task keeps consuming a `block` queue after soft abort until `on_drain` closes it; every item enqueued before cancel is persisted (counted); drain budget exceeded → sink cancelled and listed; `hard_abort` cancels immediately.
- **TST-RG-P03-005-12** `shield_commit`: cancel during a 100 ms commit with grace 5 s → commit completes, ledger `completed`, `CancelledError` re-raised (INV-7); commit longer than grace → `unknown`, `RGE-CANCELLED-0002` in ledger; commit raising → `failed`; one ledger record per call (INV-8).
- **TST-RG-P03-005-13** `run_cleanup`/`await_uncancellable`: cleanup completes though the host is cancelled twice (vector of §12.3); hard token ends the wait with `hard_aborted`; budget expiry yields `budget_exceeded`; host still ends cancelled when a cancellation was absorbed; cleanup runs after an abort injected in each experiment state of a fake state machine (kill-injection style, virtual time).
- **TST-RG-P03-005-14** `Deadline`: arithmetic example of §12.2; `run` returns work result; expiry raises `RGE-TIMING-0001` and cancels the work within budget; tie rule E-17; cancelling the caller cancels both internal tasks (no "Task was destroyed" warnings with `-X dev`); uses no wall waits (monkeypatch `time.sleep`/`asyncio.sleep` to fail).
- **TST-RG-P03-005-15** `ExecutorSet` sizing and saturation: probe spec (2 workers, 2 queue, timeout 1 s virtual): 6 concurrent calls → 2 running, 2 queued, 2 waiting; the 2 waiting get `RGE-TIMING-0002` after 1 s; INV-5 sampled at every step; stats counters.
- **TST-RG-P03-005-16** `run_blocking` semantics: context vars (`experiment_id`) visible in the worker; `started/finished` stamped inside the worker (thread id recorded) and `started ≥ submitted`; `serial_key` ordering and mutual exclusion under cancellation (E-16); `store` executor always runs on one thread id; foreign exception wrapped (E-11).
- **TST-RG-P03-005-17** `BoundedQueue`: worked example of §12.4 step by step; `block` backpressure with `blocked_total_ns` > 0 under virtual time; `fail` raises `RGE-TIMING-0003`; `put_threadsafe` from 4 threads; `close` semantics; property: model-based test (Hypothesis stateful) against a reference list implementation for random put/get/close sequences, asserting INV-6.
- **TST-RG-P03-005-18** RG-LINT-001 fixtures: ruff output on `bad_time.py` equals the table of §12.7 line for line; `bad_loop_timer.py` → `RG-LINT-001.b`; `ok_clock.py` → 0; `system_clock.py` allow-listed; suppression count outside it = 0.
- **TST-RG-P03-005-19** RG-LINT-002 fixtures: rglint (+ ruff ASYNC) findings on `bad_blocking.py` equal the table; nested `def` and pragma-with-reason produce none; pragma without reason → `RG-LINT-000`; `ok_offload.py` (uses `await ex.run_blocking(...)`) → 0.
- **TST-RG-P03-005-20** RG-LINT-003 fixtures: `bad_asyncio_misc.py` findings; `asyncio.create_task` allowed inside `rg_core/aio/` fixture path only; `.c` code-literal rule on a fixture file.
- **TST-RG-P03-005-21** `AbortController` on POSIX: send `SIGINT` thrice to a subprocess running a fake engine → soft, hard, force callbacks in order; handlers restored on `uninstall`; non-main-thread install rejected.
- **TST-RG-P03-005-22** Micro-benchmarks (marker `bench`): `run_blocking` no-op, queue put/get, error construction/`to_record` against §17 budgets.
- **TST-RG-P03-005-23** `LoopLagMonitor` + 50 concurrent `run_blocking` calls of 50 ms I/O-simulating sleeps under the real clock on Linux and Windows: p99 lag recorded and compared with 25 ms (Windows result reported; failure on Windows is a recorded finding, not a silent pass).
- **TST-RG-P03-005-24** Resource bounds: 10 000 queued submissions against `probe` (64+256) never exceed 320 slots; thread count ≤ 73 + test threads; leak test: 100 consecutive `RunScope`+`ExecutorSet` cycles end with the same `threading.active_count()` and `len(asyncio.all_tasks())` (NFR-REL-004).
- **TST-RG-P03-005-25** Windows-only integration: spawn the fake engine with `CREATE_NEW_PROCESS_GROUP`, send `CTRL_BREAK_EVENT` once → soft abort within 1 s and cleanup completes; twice → hard; marker `windows`. (Real Ctrl+C in a console is a documented manual check, A-3.)
- **TST-RG-P03-005-26** Cancellation conformance kit self-test: `rg_core.testing.cancel_kit.assert_cancels(factory, clock, budget)` passes a cooperative coroutine and fails a swallowing one; the kit is reused by every port's contract tests (INTERFACE-CONTRACTS §2 rule 1).

## 23. Mocking and test fixture requirements

* `VirtualClock`/`FakeClock` (RG-P02-001) with `advance(ns)` driving `sleep`/`sleep_until`; a `step()` helper (RG-P03-006) is not required — `aio` tests await real asyncio primitives while the clock advances in a driver task (`advance_until_quiescent`).
* `rg_core.testing.cancel_kit`: `assert_cancels`, `NonCooperativeTask`, `SlowCommit(duration)`, `ThreadGate` (a `threading.Event` wrapper to hold worker threads deterministically), `FakeSignalSender`.
* Fixture trees: `tests/lint/fixtures/{lint001,lint002,lint003}/` as listed in §12.7; `tests/data/errors/codes_ok.py`, `codes_dup.py`, `codes_out_of_block.py`.
* Hypothesis (test-only) for TST-02, -17; strategies in `tests/support/strategies.py`.
* No real sockets; no sleeps except in TST-22/-23/-25 (marked `slow`, excluded from the 5-minute virtual-time suite, NFR-TEST-003).

## 24. Objective acceptance criteria

- **AC-RG-P03-005-01** Every `RgError` has a category-fixed subclass, a code matching `RGE-<CAT>-<NNNN>`, immutable state, and `str/repr` free of details and cause text (verified by TST-RG-P03-005-01).
- **AC-RG-P03-005-02** Error details are flat, bounded and never carry `Secret` material or canary strings; construction never raises (verified by TST-RG-P03-005-02, TST-RG-P03-005-03).
- **AC-RG-P03-005-03** The error-code registry enforces uniqueness per `(category, NNNN)` and per-element blocks, and no code literal exists outside declared constants (verified by TST-RG-P03-005-04).
- **AC-RG-P03-005-04** Exception groups collapse deterministically by the documented severity order, keep cancellation distinct, and never wrap `KeyboardInterrupt` (verified by TST-RG-P03-005-05, TST-RG-P03-005-06).
- **AC-RG-P03-005-05** `RunScope` leaves no pending tasks after exit on Python 3.11–3.14, records supervised failures and rejects misuse with the documented codes (verified by TST-RG-P03-005-07, TST-RG-P03-005-08, TST-RG-P03-005-24).
- **AC-RG-P03-005-06** After an abort request all cooperative front tasks end within the configured `probe_stop` (default 1 s) and non-cooperative tasks are reported, not silently awaited (verified by TST-RG-P03-005-09, TST-RG-P03-005-10, TST-RG-P03-005-26).
- **AC-RG-P03-005-07** Evidence sinks drain every item enqueued before abort within the drain budget (verified by TST-RG-P03-005-11).
- **AC-RG-P03-005-08** Cleanup completes after abort in every injected state, survives repeated cancellation, and a second press abandons only the wait (verified by TST-RG-P03-005-13, TST-RG-P03-005-21, TST-RG-P03-005-25).
- **AC-RG-P03-005-09** Shielded commits always re-raise cancellation, record exactly one ledger entry each, and mark unconfirmed outcomes `unknown` with `RGE-CANCELLED-0002` (verified by TST-RG-P03-005-12).
- **AC-RG-P03-005-10** `Deadline` arithmetic and expiry use only the injected clock and cancel the guarded work (verified by TST-RG-P03-005-14).
- **AC-RG-P03-005-11** The three executors never exceed their slot bounds, report saturation with `RGE-TIMING-0002`, propagate context variables and expose the submission→start queueing delay (verified by TST-RG-P03-005-15, TST-RG-P03-005-16, TST-RG-P03-005-24).
- **AC-RG-P03-005-12** Bounded queues honour block/drop_oldest/fail semantics, never drop critical items and match the reference model (verified by TST-RG-P03-005-17).
- **AC-RG-P03-005-13** The lint rules RG-LINT-001/-002/-003 reproduce the expected findings on the fixtures and produce zero findings on clean fixtures (verified by TST-RG-P03-005-18, TST-RG-P03-005-19, TST-RG-P03-005-20).
- **AC-RG-P03-005-14** Performance proposals of §17 are measured and reported on Linux and Windows (verified by TST-RG-P03-005-22, TST-RG-P03-005-23).

## 25. Research sources and engineering rationale

Sources: ADR-0004 (executors, timestamps inside the worker), ADR-0006 (Clock injection, lint rule), ADR-0002 (3.11 floor: `TaskGroup`, `ExceptionGroup`), SYSTEM-ARCHITECTURE §5 (runtime model, backpressure), §9 (cross-cutting), DATA-MODEL §6 (error categories), INTERFACE-CONTRACTS §2 (cancellation rule, errors rule 5), PRD FR-OPS-006, FR-PRB-017, NFR-PERF-001/-002/-003, NFR-REL-003/-004, TECHNICAL-FEASIBILITY R-016 (thread offload jitter), THREAT-MODEL TM-07, TM-27, TM-28, TM-29, TM-34. Python/ruff behaviours were checked by the author in a sandbox (CPython 3.11.16, 3.12.3, 3.13.15; ruff 0.17.0) and are carried as assumptions A-1…A-7.

Decisions:

- **DEC-1 One `RgError` with per-category subclasses and numeric codes.** Rejected: one exception class per code (hundreds of classes), string-only error ids (no ownership/ranges). Verification: TST-…-01, -04.
- **DEC-2 Code blocks independent of category, per owning element.** Rejected: per-category sequential allocation (merge conflicts between parallel authors), semantic numbering (churn). Verification: TST-…-04.
- **DEC-3 Errors never raise from their constructor and sanitise details by construction.** Rejected: raising on bad details (hides the original failure), free-form dict details (secret leakage, TM-07). Verification: TST-…-02.
- **DEC-4 Native `CancelledError` inside tasks; `CancelledByRg` only as a recorded result.** Rejected: converting cancellation to `RgError` (breaks `TaskGroup` semantics and INTERFACE-CONTRACTS §2 rule 1). Verification: TST-…-07, -09.
- **DEC-5 `RunScope` = TaskGroup (front) + separately tracked sinks.** A single TaskGroup would cancel the store writer together with probes on abort and lose evidence; sinks are therefore drained, not cancelled. Rejected: plain `gather` (no structured errors), one TaskGroup per role (nested cancellation order hard to reason about). Verification: TST-…-11.
- **DEC-6 Cleanup in a separate task awaited by `await_uncancellable`.** Rejected: `try/finally` in the host (second Ctrl+C cancels the cleanup), `asyncio.shield` alone (no budget, no hard abort). Verification: TST-…-13.
- **DEC-7 Three-stage abort (soft/hard/force) on signal counts.** Rejected: single-stage (operator cannot interrupt a stuck cleanup), `loop.add_signal_handler` (not available on Windows loops). Verification: TST-…-21, -25.
- **DEC-8 Executors: `probe` 64/256, `idp` 8/64, `store` 1/1024.** Rationale: NFR-PERF-003 needs ≥ 50 in-flight probes for MVP (64 workers) with 200 reachable by config; `idp` small because provider rate limits dominate (TM-29); `store` single writer (SQLite WAL, ADR-0005) and single thread for connection identity. Rejected: one shared pool (a slow target starves persistence — ADR-0004), `asyncio.to_thread` default pool (unbounded queue, no saturation signal). Verification: TST-…-15, -16, -24.
- **DEC-9 Serial keys give exclusion + FIFO, not thread affinity**, except the single-thread `store`. Rejected: per-key dedicated threads (thread explosion), `threading.local` sessions (hidden state). Verification: TST-…-16.
- **DEC-10 `Deadline` races the work against `clock.sleep_until`** instead of `asyncio.timeout`, so deadlines advance with the virtual clock and RG-LINT-001 can ban loop-time APIs. Rejected: `asyncio.timeout` (loop time, not injected clock). Verification: TST-…-14.
- **DEC-11 Lint = ruff `TID251`/`ASYNC` + a small AST script.** Rejected: a custom ruff plugin (ruff has no plugin API), flake8 plugin (extra toolchain), runtime monkey-patching of `time` (fragile, hidden global state). Limits: name-based heuristics (A-6). Verification: TST-…-18…-20.
- **DEC-12 Bounded queues with only three policies** (`block`, `drop_oldest`, `fail`), identical to the frozen EventBus signature; `drop_oldest_noncritical` of the architecture text is expressed as `drop_oldest` + `critical` flag. Verification: TST-…-17.
- **DEC-13 `ExitKind` lives here, integers in RG-P10-001**, so that every library can classify errors without importing the CLI. Verification: TST-…-06.

## 26. Remaining uncertainties or assumptions

| # | Assumption | Falsifying test |
|---|---|---|
| A-1 | `TaskGroup`, `except*`, `Task.uncancel`, shield and cancel semantics behave as used here on CPython 3.11–3.14 (author sandbox: 3.11.16, 3.12.3, 3.13.15 identical; 3.14 not available in the sandbox) | TST-…-07, -13 on the 3.14 CI leg |
| A-2 | The `await_uncancellable` pattern keeps a cleanup task running through repeated host cancellation and ends on hard token/budget (author prototype on 3.11 and 3.13) | TST-…-13 |
| A-3 | On Windows the Proactor loop wakes for a Python-level `SIGINT`/`SIGBREAK` handler that calls `call_soon_threadsafe` (not verified on Windows in this session) | TST-…-25 (automated via `CTRL_BREAK_EVENT`) and the manual Ctrl+C check |
| A-4 | ruff `TID251` resolves qualified names through import aliases and `ASYNC210/220/221/230/240/250/251` fire on the fixture patterns (author-run with ruff 0.17.0; rule set may change between ruff releases) | TST-…-18, -19 on every ruff bump (ruff version is pinned) |
| A-5 | asyncio event-loop policy APIs are deprecated/removed on newer Pythons, so avoiding them is forward compatible (not verified for 3.14 in this session) | CI leg 3.14 with `-W error::DeprecationWarning` |
| A-6 | Name-based AST heuristics (RG-LINT-002.a/.c/.f) have no false negatives on the codebase's coding conventions and acceptable false positives | seeded-bug corpus in TST-…-19; review of pragma count |
| A-7 | No RevocationGap blocking dependency requires thread identity on `probe`/`idp` threads (e.g. `requests.Session` is used under `serial_key`, Authlib sessions per identity) | contract kit of RG-P04-002/-P05-004 (they must state thread-safety) |
| A-8 | `ProactorEventLoop` timer granularity on Windows < 3.13 is ≈ 15.6 ms (NFR-PERF-002 tag U) | TST-…-23 on Windows |
| A-9 | Non-daemon pool threads blocked in I/O delay interpreter exit by at most the call's I/O timeout | TST-…-24 (process-exit timing under abort) |
| A-10 | Free-threaded CPython builds are out of scope (`RGE-INTERNAL-0003`) | CI matrix excludes them |

## 27. Maintainability, portability, and future extension requirements

* **Extension points:** new categories are not allowed without a CONTRACT-CHANGELOG entry (DATA-MODEL §6 is frozen); new codes are added by owners inside their block; new `TaskRole`s extend `RunScope` front/sink classification via a table (front roles: probe, scheduler, worker, observer; back role: sink).
* **Future workers (RG-P14-001):** `RgError` pickling contract and `ErrorRecord` are process-boundary safe; executors map to separate processes by swapping `ExecutorSet` implementation behind the same `run_blocking` signature.
* **Python upgrades:** each new CPython release is added to the CI matrix on release; `-W error::DeprecationWarning` on the newest leg; asyncio behaviours listed in §20 are re-verified by the tests named in A-1.
* **Lint maintenance:** banned-API list lives in `pyproject.toml`; every addition needs a fixture row in §12.7 and a test; rglint sub-rules are append-only (ids never reused).
* **Reuse:** `rg_core.aio` and `rg_core.errors` depend only on `Clock` and `rg_core.model.base`; they can be lifted into other asyncio tools that need structured cancellation with durable cleanup.
* **Deprecation:** removing a code is never allowed (codes are permanent identifiers); retired codes stay in the registry with `retired=True` and a pointer to the replacement.
