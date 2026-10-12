# RevocationGap — Interface Contracts (frozen index and port signatures)

**Status:** frozen contract v1.0 (RG-P03-001). Every `IF-*` below has exactly one owning element which writes the full contract (error behaviour, threading, test doubles, examples). The **signatures in §3 are normative** for parallel authoring: owners may add optional parameters/methods and refine exceptions, but may not rename, remove or change the meaning of anything shown without a [`CONTRACT-CHANGELOG.md`](CONTRACT-CHANGELOG.md) entry. Types (`TimeInstant`, `Observation`, …) are defined in [`DATA-MODEL.md`](DATA-MODEL.md). All I/O methods are `async` unless marked *sync*; blocking implementations run on the executors described in SYSTEM-ARCHITECTURE §5. All methods raise only `RgError` subclasses (DATA-MODEL §6).

## 1. Interface index

| IF id | Name | Defined in | Owner element | Real implementations | Test doubles |
|---|---|---|---|---|---|
| IF-CORE-CLOCK | `Clock` | `rg_core.ports.time` | RG-P02-001 | `SystemClock` | `VirtualClock` |
| IF-CORE-SCHEDULER | `Scheduler` | `rg_core.ports.time` | RG-P03-006 | `AsyncioScheduler` | `VirtualScheduler` |
| IF-CORE-EVENTBUS | `EventBus` | `rg_core.ports.events` | RG-P03-007 | `InProcessEventBus` | sync bus |
| IF-CORE-SERIAL | `SchemaRegistry`, `IdFactory`, canonical JSON | `rg_core.serial` | RG-P03-002 | rg_core | — |
| IF-CORE-LOG | `Redactor`, structured logger | `rg_core.logging` | RG-P03-004 | rg_core | recording |
| IF-CORE-ERR | `RgError` hierarchy | `rg_core.errors` | RG-P03-005 | rg_core | — |
| IF-CORE-STORE | `ExperimentStore`, `EvidenceStore`, `AuditLog` | `rg_core.ports.store` | RG-P03-008 | SQLite/blob (app) | in-memory |
| IF-CORE-SECRETS | `SecretResolver` | `rg_core.ports.secrets` | RG-P11-001 | env/keyring/file (app) | in-memory |
| IF-CORE-PLUGIN | `PluginRegistry`, `PluginManifest` | `rg_core.ports.plugins` | RG-P03-009 | app loader | static registry |
| IF-CFG-LOADER | config loading/validation | `revocationgap.config` | RG-P03-003 | app | — |
| IF-EXP-MACHINE | `ExperimentMachine` (pure transition function) | `rg_core.experiment` | RG-P02-007 | rg_core | — |
| IF-ENG-ENGINE | `ExperimentEngine` | `revocationgap.engine` | RG-P03-010 | app | — |
| IF-ENG-SERVICE | `ApplicationService` | `revocationgap.service` | RG-P03-010 | app | fake |
| IF-IDP-ADAPTER | `IdentityProviderAdapter` (composite) | `rg_core.ports.idp` | RG-P04-001 | rg_idp adapters | mock IdP adapter (rg_lab) |
| IF-IDP-CAPS | `ProviderCapabilities` | `rg_core.ports.idp` | RG-P04-001 | — | — |
| IF-IDP-ACQUIRE | `CredentialAcquirer` | `rg_core.ports.idp` | RG-P04-002 | rg_idp | rg_lab |
| IF-IDP-ORACLE | `TokenOracle` | `rg_core.ports.idp` | RG-P04-004 | rg_idp | rg_lab |
| IF-IDP-ADMIN | `AdminControl` | `rg_core.ports.idp` | RG-P04-006 | rg_idp | rg_lab |
| IF-IDP-EVENTS | `EventSource` | `rg_core.ports.idp` | RG-P04-011 | rg_idp.ssf, provider logs | rg_lab |
| IF-REV-ACTION | `RevocationAction` | `rg_core.ports.revocation` | RG-P06-001 | rg_idp, app (manual) | scripted |
| IF-REV-ANCHOR | `AnchorRecorder` | `rg_core.revocation` | RG-P06-009 | rg_core | — |
| IF-PROBE-HTTP | `HttpTransport` | `rg_probe.transport` | RG-P05-004 | `RawHttpTransport`, `StHttpTransport` | `InProcessAppTransport` |
| IF-PROBE-WS | `WebSocketSession` | `rg_probe.websocket` | RG-P05-011 | websockets adapter | scripted server |
| IF-PROBE-ASSERT | `Assertion` | `rg_core.ports.assertions` | RG-P05-006 | built-ins + plugins | — |
| IF-PROBE-SCHEDULE | `ProbeSchedule` strategies | `rg_probe.schedule` | RG-P05-008 | rg_probe | fixed |
| IF-PROBE-LIMIT | `RateLimiter`, retry policy | `rg_probe.limits` | RG-P05-009 | rg_probe | null |
| IF-PROBE-RUNNER | `ProbeRunner` | `rg_probe.runner` | RG-P05-014 | rg_probe | — |
| IF-PROBE-TEMPLATE | `RequestTemplate` rendering | `rg_core.spec.template` / `rg_probe.template` | RG-P05-002 | rg_probe | — |
| IF-ST-CATALOG | `OperationCatalog` | `rg_stbridge` | RG-P05-005 | rg_stbridge | fixture catalog |
| IF-ST-GEN | baseline/scenario generation | `rg_stbridge.generate` | RG-P07-005 | rg_stbridge | — |
| IF-SCN-LOADER | `ScenarioLoader` | `rg_core.scenario` | RG-P07-001 | rg_core | — |
| IF-ANA-ALIGN | `ClockAligner` | `rg_core.analysis.align` | RG-P08-002 | rg_core | — |
| IF-ANA-CORRELATE | `EventCorrelator` | `rg_core.analysis.correlate` | RG-P08-003 | rg_core | — |
| IF-ANA-WINDOW | `ExposureCalculator` | `rg_core.analysis.window` | RG-P08-004 | rg_core | — |
| IF-ANA-CONFIDENCE | `ConfidenceScorer` | `rg_core.analysis.confidence` | RG-P08-005 | rg_core | — |
| IF-ANA-CLASSIFY | `OutcomeClassifier` | `rg_core.analysis.classify` | RG-P02-009 (rules), RG-P08-006 (findings) | rg_core | — |
| IF-ANA-BASELINE | `BaselineProvider` | `rg_core.ports.baselines` | RG-P08-008 | built-in + plugins | — |
| IF-ANA-HISTORY | `HistoryComparator` | `revocationgap.history` | RG-P08-009 | app | — |
| IF-RPT-RENDERER | `ReportRenderer` | `rg_core.ports.report` | RG-P08-011 | HTML/MD/JSON/SARIF/JUnit (app) | golden |
| IF-LAB-IDP / IF-LAB-SERVICE / IF-LAB-FAULT / IF-LAB-FIXTURE | lab control APIs | `rg_lab` | RG-P09-002 / 003 / 004 / 005 | rg_lab | — |
| IF-UI-CLI | CLI command contract | `revocationgap.cli` | RG-P10-001 | app | — |
| IF-UI-WEB | GUI internal web API | `revocationgap.gui` | RG-P10-004 | app | — |
| IF-API-AUTOMATION | automation HTTP API | `revocationgap.api` | RG-P10-007 | app | — |
| IF-SEC-SCOPE | `ScopeEnforcer` | `rg_core.scope` | RG-P11-002 | rg_core | permissive-for-tests (lab only) |

## 2. Contract rules that apply to every interface

1. **Cancellation:** every `async` method honours `asyncio.CancelledError` promptly (≤ the method's documented cancel budget, default 1 s) and leaves no half-applied state it cannot report (state-changing admin calls report `unknown outcome` rather than swallow cancellation).
2. **Time:** implementations receive a `Clock` at construction and never read system time directly. Methods that perform network I/O return the `TimeInstant` pair bracketing the wire interaction in their result objects (`started_at`, `finished_at`).
3. **Secrets:** results are secret-free except explicit `CredentialMaterial` return types, which are `Secret`-wrapped and non-serialisable.
4. **Idempotency:** methods with side effects document idempotency; `RevocationAction.execute` is **not** idempotent but `plan`/`verify`/`restore` are.
5. **Errors:** a method never returns "success" for a partially failed operation; capability gaps raise `RgError(category=PROVIDER, code=RGE-PROVIDER-UNSUPPORTED)` with the `capability` name — callers must consult `capabilities()` first.
6. **Thread-safety:** stated per interface; default = *safe for concurrent calls from multiple tasks of one event loop*, not safe across threads.

## 3. Normative signatures (Python Protocol form)

```python
# ---- rg_core.ports.time -------------------------------------------------------------------------
class Clock(Protocol):                                   # IF-CORE-CLOCK  (sync reads; thread-safe)
    kind: ClockKind
    def wall_ns(self) -> int: ...
    def mono_ns(self) -> int: ...
    def now(self) -> TimeInstant: ...                    # paired read: mono, wall, mono → read_cost_ns; one call per instant
    async def sleep(self, ns: int) -> None: ...          # monotonic; virtual clocks advance the virtual timeline
    async def sleep_until(self, mono_ns: int) -> None: ...

class TimerHandle(Protocol):
    def cancel(self) -> None: ...
    @property
    def due_mono_ns(self) -> int: ...

class Scheduler(Protocol):                               # IF-CORE-SCHEDULER
    clock: Clock
    def call_at(self, due_mono_ns: int, callback: Callable[[], Awaitable[None] | None], *, name: str) -> TimerHandle: ...
    def run_at(self, due_mono_ns: int, coro_factory: Callable[[], Awaitable[T]], *, name: str) -> "asyncio.Future[ScheduledResult[T]]": ...
    # ScheduledResult carries .value, .intended_ns, .started_ns (→ scheduling lateness)
    async def drain(self) -> None: ...                   # virtual: run to quiescence; system: wait for outstanding timers

# ---- rg_core.ports.events -----------------------------------------------------------------------
class Event(Model): seq: int; at: TimeInstant; experiment_id: str | None; kind: str; payload: Mapping[str, Any]
class EventBus(Protocol):                                # IF-CORE-EVENTBUS
    async def publish(self, event: Event) -> None: ...                       # never drops events flagged critical=True
    def subscribe(self, kinds: Collection[str] | Literal["*"], *, name: str, queue_size: int = 1024,
                  overflow: Literal["block", "drop_oldest", "fail"] = "drop_oldest") -> "Subscription": ...
class Subscription(Protocol):
    def __aiter__(self) -> AsyncIterator[Event]: ...
    async def close(self) -> None: ...
    dropped: int                                         # count of events dropped under drop_oldest

# ---- rg_core.ports.store ------------------------------------------------------------------------
class ExperimentStore(Protocol):                         # IF-CORE-STORE (single writer per workspace)
    async def create_experiment(self, exp: Experiment) -> None: ...
    async def append_timeline(self, exp_id: str, entry: TimelineEntry) -> None: ...         # durable before return
    async def append_observation(self, exp_id: str, obs: Observation) -> None: ...
    async def append_event(self, exp_id: str, ev: RevocationEvent) -> None: ...
    async def put_derived(self, exp_id: str, rec: DerivedRecord) -> None: ...                # replaces same (algorithm, key) version
    async def transition(self, exp_id: str, frm: ExperimentState, to: ExperimentState, at: TimeInstant) -> None: ...   # CAS on state
    async def load(self, exp_id: str) -> ExperimentSnapshot: ...
    def query(self, q: ExperimentQuery) -> AsyncIterator[ExperimentSummary]: ...
class EvidenceStore(Protocol):
    async def put(self, data: bytes | AsyncIterator[bytes], meta: EvidenceMeta) -> EvidenceRef: ...   # content-addressed; dedup by sha256
    async def get(self, ref: EvidenceRef, *, unredact: bool = False) -> bytes: ...
class AuditLog(Protocol):
    async def append(self, rec: AuditRecord) -> None: ...                                    # hash-chained; fsync policy configurable

# ---- rg_core.ports.secrets ----------------------------------------------------------------------
class SecretResolver(Protocol):                          # IF-CORE-SECRETS
    async def resolve(self, handle: SecretHandle) -> Secret: ...
    def fingerprint(self, secret: Secret) -> str: ...    # sync

# ---- rg_core.ports.idp --------------------------------------------------------------------------
class ProviderCapabilities(Model):                       # IF-IDP-CAPS (declarative; every flag has evidence ref)
    adapter_id: str; provider_version: str | None
    can_acquire: set[AcquisitionFlow]                    # password, auth_code_pkce_scripted, client_credentials, device, session_cookie_form, token_exchange
    token_oracle: set[OracleOp]                          # introspect, userinfo, refresh_check, prompt_none_check, revoke_endpoint
    admin_ops: set[RevocationKind]                       # kinds the adapter can *cause*
    event_sources: set[EventSourceKind]                  # admin_event_log, system_log, ssf_push, ssf_poll, audit_api
    cae_capable: bool                                    # Entra continuous access evaluation client declaration
    supports: Mapping[str, SupportLevel]                 # fine-grained flags: "access_token_revocation", "refresh_rotation", "backchannel_logout"…
    limits: ProviderLimits                               # rate limits, consistency notes, ToS/clearance requirement flags
    evidence: Mapping[str, str]                          # capability → research doc anchor

class CredentialAcquirer(Protocol):                      # IF-IDP-ACQUIRE
    async def acquire(self, identity: Identity, flow: AcquisitionFlow, *, params: Mapping[str, Any] = ...) -> AcquisitionResult: ...
class AcquisitionResult(Model): credentials: list[CredentialMaterial]; started_at: TimeInstant; finished_at: TimeInstant; session_ref: str | None
class CredentialMaterial(Model): credential: Credential; secret: Secret   # `secret` excluded from serialisation (model_config exclude)

class TokenOracle(Protocol):                             # IF-IDP-ORACLE — independent oracles used alongside resource probes
    async def introspect(self, cred: CredentialMaterial) -> OracleResult: ...
    async def userinfo(self, cred: CredentialMaterial) -> OracleResult: ...
    async def try_refresh(self, refresh: CredentialMaterial, *, rotate_ok: bool = False) -> OracleResult: ...   # may consume RT; documented
    async def session_liveness(self, session_ref: str) -> OracleResult: ...                                  # prompt=none or provider API
class OracleResult(Model): op: OracleOp; verdict: Literal["active","inactive","error","unsupported"]; raw_ref: EvidenceRef | None; started_at: TimeInstant; finished_at: TimeInstant; signals: Mapping[str, Any]

class AdminControl(Protocol):                            # IF-IDP-ADMIN — only reachable through RevocationAction + ScopeEnforcer
    async def apply(self, change: AdminChange, *, dry_run: bool = False) -> AdminResult: ...
    async def read_state(self, identity: Identity) -> AuthorizationState: ...
class AdminResult(Model): ack_state: AckState; requested_at: TimeInstant; acknowledged_at: TimeInstant | None; claimed_effective_at: RemoteInstant | None; provider_ref: str | None; raw_ref: EvidenceRef | None

class EventSource(Protocol):                             # IF-IDP-EVENTS
    def stream(self, *, since: TimeInstant | None = None) -> AsyncIterator[ExternalEvent]: ...
    async def close(self) -> None: ...

class IdentityProviderAdapter(Protocol):                 # IF-IDP-ADAPTER (composite; components may raise UNSUPPORTED)
    descriptor: AdapterDescriptor
    async def capabilities(self) -> ProviderCapabilities: ...        # may probe discovery documents; cached per run
    acquirer: CredentialAcquirer; oracle: TokenOracle; admin: AdminControl; events: EventSource | None
    async def aclose(self) -> None: ...

# ---- rg_core.ports.revocation -------------------------------------------------------------------
class RevocationAction(Protocol):                        # IF-REV-ACTION
    descriptor: ActionDescriptor                         # kind, action_class (ActionClass), prerequisites, side_effects, restorable: bool, required_admin_permissions
    async def plan(self, ctx: ActionContext) -> ActionPlan: ...             # pure/readonly; used by dry-run & scope check
    async def execute(self, plan: ActionPlan, ctx: ActionContext) -> RevocationEvent: ...   # records requested_at/acknowledged_at; non-idempotent
    async def verify(self, event: RevocationEvent, ctx: ActionContext) -> VerificationResult: ...   # independent confirmation via read_state/oracle
    async def restore(self, event: RevocationEvent, ctx: ActionContext) -> RestorationResult: ...   # idempotent; always attempted in CLEANING_UP

# ---- rg_core.ports.assertions -------------------------------------------------------------------
class Assertion(Protocol):                               # IF-PROBE-ASSERT (sync, pure, no I/O, deterministic)
    id: str; params_schema: type[Model]
    def evaluate(self, exchange: NormalizedExchange, params: Model, ctx: AssertionContext) -> AssertionResult: ...
class AssertionResult(Model): assertion_id: str; passed: bool; role: Literal["positive_access","denial_signal","guard"]; detail: str; observed: Mapping[str, Any]

# ---- rg_probe.transport / websocket ------------------------------------------------------------
class PreparedProbeRequest(Model):                       # built by rg_probe.template / rg_stbridge; secret-free
    method: str; url: str; headers: Mapping[str, str]; body: bytes | EvidenceRef | None; content_type: str | None
    operation_ref: OperationRef | None; snapshot_ref: EvidenceRef; correlation_id: str
class CallPolicy(Model): timeout_connect_s: float; timeout_read_s: float; allow_redirects: Literal[False] = False; verify_tls: bool|str; fresh_connection: bool; max_body_bytes: int
class HttpTransport(Protocol):                           # IF-PROBE-HTTP
    kind: Literal["raw","schemathesis","inproc"]
    async def send(self, request: PreparedProbeRequest, auth: RequestAuth, policy: CallPolicy, *, identity_key: str) -> HttpExchange: ...
    async def aclose(self) -> None: ...
class RequestAuth(Model): headers: Mapping[str, Secret|str]; cookies: Mapping[str, Secret|str]    # per-call, never stored
class HttpExchange(Model):                               # raw-ish record; normalised form in SCH-EXCHANGE
    t_send_start: TimeInstant; t_recv_end: TimeInstant; status: int | None; response_headers: Mapping[str, list[str]]
    body_ref: EvidenceRef | None; body_truncated: bool; server_date: RemoteInstant | None; connection_reused: bool | None
    http_version: str | None; error: TransportErrorInfo | None; transport_kind: str

class WebSocketSession(Protocol):                        # IF-PROBE-WS
    async def connect(self, spec: WsConnectSpec, auth: RequestAuth, clock: Clock) -> WsConnectResult: ...
    async def ping_or_message(self, probe: WsLivenessSpec) -> WsLivenessResult: ...
    def close_events(self) -> AsyncIterator[WsCloseEvent]: ...        # server-initiated close with code/reason + TimeInstant
    async def aclose(self) -> None: ...

# ---- rg_probe.runner ----------------------------------------------------------------------------
class ProbeRunner(Protocol):                             # IF-PROBE-RUNNER
    async def run_phase(self, plan: ProbePlan, *, phase: Literal["control","baseline","observe"], sink: ObservationSink,
                        stop: StopRule | None) -> PhaseSummary: ...
class ObservationSink(Protocol):
    async def emit(self, obs: Observation) -> None: ...

# ---- rg_stbridge --------------------------------------------------------------------------------
class OperationCatalog(Protocol):                        # IF-ST-CATALOG  (full contract in SCHEMATHESIS-INTEGRATION §5.3 + RG-P05-005)
    @classmethod
    def load(cls, source: SchemaSource, *, timeout_s: float = 15.0) -> "OperationCatalog": ...   # sync; run in executor
    def operations(self) -> Sequence[OperationRef]: ...
    def describe(self, ref: OperationRef) -> OperationDescription: ...
    def protected(self) -> Sequence[OperationRef]: ...
    def derive_template(self, ref: OperationRef, *, values: Mapping[str, Any] | None = None,
                        generation: Literal["examples","generated","explicit"] = "examples", seed: int | None = None) -> RequestTemplate: ...

# ---- rg_core.analysis ---------------------------------------------------------------------------
class ClockAligner(Protocol):    def estimate(self, domain: ClockDomain, samples: Sequence[RemoteInstant]) -> ClockOffset: ...                                         # sync, pure
class EventCorrelator(Protocol): def correlate(self, ev: RevocationEvent, evidence: EvidenceIndex) -> CorrelationResult: ...                                           # sync, pure
class ExposureCalculator(Protocol): def compute(self, event: RevocationEvent, observations: Sequence[Observation], params: WindowParams) -> ExposureWindow: ...     # sync, pure
class ConfidenceScorer(Protocol): def score(self, window: ExposureWindow, ctx: ConfidenceContext) -> Confidence: ...                                                  # sync, pure
class OutcomeClassifier(Protocol): def classify(self, window: ExposureWindow, expectations: ExpectationSet, confidence: Confidence, profile: PolicyProfile, ctx: ClassifyContext) -> Classification: ...   # sync, pure, deterministic
class BaselineProvider(Protocol): def expectations(self, provider: ProviderRef, target: Target, profile: PolicyProfile) -> ExpectationSet: ...                          # sync

# ---- rg_core.ports.report -----------------------------------------------------------------------
class ReportRenderer(Protocol):                          # IF-RPT-RENDERER
    format_id: str; media_type: str; file_extension: str
    def render(self, report: ReportModel, options: RenderOptions) -> RenderedReport: ...    # sync, pure; MUST NOT reach network; MUST escape all untrusted strings

# ---- rg_core.scope ------------------------------------------------------------------------------
class ScopeEnforcer(Protocol):                           # IF-SEC-SCOPE (sync, pure over a loaded Scope)
    def authorize(self, req: ScopeRequest) -> ScopeDecision: ...      # req: action_class, host/tenant/identity, rate; raises RgError(SCOPE) via .require(...)
    def require(self, req: ScopeRequest) -> None: ...

# ---- revocationgap.engine -----------------------------------------------------------------------
class ExperimentEngine(Protocol):                        # IF-ENG-ENGINE
    async def run(self, spec: ExperimentSpec, ctx: RunContext, *, manual_ack: ManualAckChannel | None = None) -> ExperimentResult: ...
    async def abort(self, exp_id: str, reason: str) -> None: ...
    async def resume(self, exp_id: str, ctx: RunContext) -> ExperimentResult: ...       # interrupted-run recovery (RG-P11-005)
    def events(self, exp_id: str) -> Subscription: ...
```

## 4. Dependency/call-direction summary (for cycle checking by `specgate`/audit)

`rg_core` ports are *implemented* by outer packages and *called* by the engine. Calls never go from `rg_core` into `rg_idp`/`rg_probe`/app. `rg_probe` never calls `rg_idp`; credentials arrive as `RequestAuth` built by the engine from `CredentialMaterial`. `rg_idp` never calls `rg_probe`. `rg_stbridge` calls `rg_probe` only through `IF-PROBE-HTTP` helpers (implementing it) and `rg_core` models. Revocation actions call `AdminControl` + `ScopeEnforcer` (injected) and record to `AnchorRecorder`; they never call probes.

## 5. Contract change process

1. Propose in the element's spec section 26 ("uncertainties") *or* as a PR touching this file; 2. add a row to `CONTRACT-CHANGELOG.md` (date, interface, change, rationale, dependants swept); 3. update every dependant spec in the same commit; 4. `specgate check` must pass.
