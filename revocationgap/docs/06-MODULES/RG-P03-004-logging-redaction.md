---
id: RG-P03-004
title: "Logging, tracing and redaction"
phase: "03"
package: core
module_ids: [MOD-CORE-LOGGING_REDACTION]
status: DRAFT
depends_on: [RG-P03-002]
requirements: [FR-SEC-006, FR-SEC-005, FR-OPS-005, FR-CLI-003, FR-SEC-010, FR-SEC-014, FR-EVD-006, NFR-PERF-005, NFR-PLAT-002, NFR-REL-002, NFR-MNT-002]
interfaces_defined: [IF-CORE-LOG]
interfaces_used: [IF-CORE-CLOCK, IF-CORE-SERIAL, IF-CORE-ERR]
schemas_defined: [SCH-LOGREC]
schemathesis_touchpoints: []
---

# RG-P03-004 — Logging, tracing and redaction

> Scope: `rg_core.logging` (redactor, detectors, canary registry, claim allow-list, terminal sanitiser, JSON/text formatters, correlation context, record factory, redacting handlers, event/metric naming) and the app-side sink wiring `revocationgap.logsetup` (console, rotating file) specified here. `rg_core.logging` itself performs **no I/O**: handlers wrap stdlib handlers that the composition root constructs.

## 1. Module identifier and name

| Item | Value |
|---|---|
| Element | RG-P03-004 — Logging, tracing and redaction |
| Module id | `MOD-CORE-LOGGING_REDACTION` |
| Packages | `rg_core.logging` (`redactor.py`, `detectors.py`, `canary.py`, `claims.py`, `terminal.py`, `formatter.py`, `handlers.py`, `context.py`, `factory.py`, `events.py`, `config.py`); app adapter `revocationgap.logsetup` (`configure_logging`, console/file sink construction) |
| Interface owned | `IF-CORE-LOG` (`Redactor`, `Redacted`, `StructuredLogger`, `RedactingHandler`, `sanitize_for_terminal`, `bind_context`) |
| Schema owned | **new** `SCH-LOGREC` (JSON log record) |
| Consumers | everything that logs; RG-P03-008 (store gate), RG-P08-011 (report gate), RG-P10-001 (CLI), RG-P10-004 (GUI/API), RG-P11-001 (canary registration at secret resolution), RG-P03-003 (`[logging]` section model) |

## 2. Phase and requirement references

| Requirement | Realised by |
|---|---|
| FR-SEC-006 | one `Redactor` used at the log, store, report, GUI/API, CLI and exception boundaries (§7.1, §10.1); detection of tokens, cookies, passwords, authorization headers, client secrets and their encodings; claim allow-list |
| FR-SEC-005 | canary registry fed by `SecretResolver` at resolution time; no secret in logs, process arguments or crash output (global hooks §10.7) |
| FR-OPS-005 | stdlib logging + structured JSON, correlation ids, levels, rotating file sink, mandatory redaction, body logging off by default |
| FR-CLI-003 | `sanitize_for_terminal` (TM-11) |
| FR-SEC-010 | terminal context of output escaping (HTML/Markdown/XML escaping belong to RG-P08-011/RG-P10-004) |
| FR-SEC-014 | redaction cannot be disabled by configuration; bodies not logged by default |
| FR-EVD-006 | redaction at the persistence boundary: `redact_body`, `redact_headers`, `contains_canary` |
| NFR-PERF-005 | CPU budget with redaction enabled (§17) |
| NFR-PLAT-002 | UTF-8, LF newlines, Windows console encoding rules |
| NFR-REL-002 | deterministic log lines under the virtual clock (timestamps from `Clock`) |
| NFR-MNT-002 | typed API (mypy strict) |

Threats and validity: **TM-07** (credential/evidence leakage — primary), **TM-11** (terminal escape/markup injection — primary), TM-08 (store disclosure: store receives only redacted data), TM-12 (the gate is a prerequisite for report escaping), TM-14 (control characters/CRLF in log fields cannot forge lines), TM-27 (audit/log tamper: log records carry `seq`; the audit log is separate), TM-34 (bounded log volume), **SC-07** (canary test design §22), R-013 (secret leakage risk). Workflows: all.

## 3. Purpose and user/security value

A pentesting tool that handles IdP admin credentials and live bearer tokens will be run in CI logs, shared screen sessions and bug-bounty evidence bundles. One missed token in a log line is a reportable defect in the tool itself. This module therefore makes redaction a **single, central, non-optional gate** with three independent layers (record factory, handler wrapper, formatter scrub), detects secrets *by value* (registered canaries in all their encodings) as well as *by shape* (JWT, `Bearer`, cookies, key/value pairs), and gives the CLI a sanitiser so that target-controlled strings cannot move the cursor, retitle the terminal or spoof links.

## 4. Explicit responsibilities

- **RESP-1** Implement `Redactor` with text/value/header/URL/body/exception entry points, deterministic markers, a thread-safe runtime canary registry and an allow-list for JWT claims.
- **RESP-2** Define the detector catalogue (`DET-01…DET-10`), the encoded-form catalogue (`ENC-1…ENC-9`) and the redaction marker grammar.
- **RESP-3** Implement the header, URL/query/fragment and body (JSON, form, text, opaque) redaction rules of §9.
- **RESP-4** Redact exception messages, `__notes__`, cause chains and tracebacks without ever capturing locals or source lines.
- **RESP-5** Provide a structured JSON formatter and a text formatter (`SCH-LOGREC`), timestamps from the injected `Clock`.
- **RESP-6** Provide correlation context (`experiment_id`, `probe_id`, `attempt_id`) via `contextvars`, propagated through tasks and `run_blocking`.
- **RESP-7** Make it **impossible to attach a handler without redaction**: record factory, `RgLogger.addHandler` guard, `RedactingHandler` wrapper, startup/`doctor` guard check.
- **RESP-8** Install global hooks so uncaught exceptions, thread exceptions, unraisable errors, warnings and asyncio exception handlers go through the gate.
- **RESP-9** Define log levels, sinks (console on stderr, rotating JSONL file) and the `LoggingConfig` model (`[logging]` section).
- **RESP-10** Define event and metric naming conventions and the catalogue of names emitted by platform modules.
- **RESP-11** Provide `sanitize_for_terminal` and `escape_markup` (TM-11).
- **RESP-12** Define the SC-07 canary/fuzz test design and its oracle.

## 5. Out-of-scope responsibilities

| Excluded | Owner |
|---|---|
| `Secret`, `SecretHandle`, fingerprint function, shape primitives | RG-P03-002 (this module reuses `fingerprint_of` and `find_secret_shape`) |
| Resolving secrets from env/keyring/file and calling `register_canary` at resolution | RG-P11-001 |
| What is stored when, evidence hash chain, raw (unredacted) encrypted capture and reveal auditing | RG-P03-008 / RG-P08-001 / RG-P11-003 |
| HTML/Markdown/XML/CSV escaping in reports and GUI | RG-P08-011 / RG-P10-004 / RG-P10-006 |
| CLI rendering, `rich` usage, exit codes | RG-P10-001 |
| Audit log (hash-chained, separate file) | RG-P11-002 / RG-P03-008 |
| Event-bus metric transport | RG-P03-007 (this spec names metrics and event kinds only) |
| Config parsing/layering | RG-P03-003 |
| File permission helper (0600/ACL) used when creating log files | RG-P03-008 (`ensure_private`) |
| Token decoding/claim semantics | RG-P04-003 / RG-P02-003 (use `Redactor.filter_claims`) |

## 6. Dependencies and prerequisites

* Specs: RG-P03-002 (`Secret`, `fingerprint_of`, `find_secret_shape`, `Model`, `Label`, `ShortText`, `canonical_json`), RG-P03-005 (`RgError`, `ErrorRecord`; interface-only use, `rg_core.errors.core` is a stdlib-only leaf), `Clock` signature (DATA-MODEL §2.2).
* Standard library only: `logging`, `contextvars`, `re`, `unicodedata`, `base64`, `urllib.parse`, `html`, `hashlib`, `json`, `traceback`, `threading`, `sys`, `warnings`. No third-party dependency; `rich` is **not** imported (CLI concern; compatibility test uses `rich` as a dev dependency).
* Python ≥ 3.11 (atomic groups/possessive quantifiers in `re` are used to bound regex backtracking; A-2).
* Environment: none at import time. `revocationgap.logsetup` needs the workspace path and the file-permission helper of RG-P03-008.

## 7. External and internal interfaces

### 7.1 Redactor (`rg_core.logging.redactor`) — IF-CORE-LOG

```python
class Boundary(str, Enum): log="log"; store="store"; report="report"; gui="gui"; cli="cli"; export="export"; exception="exception"
class SecretKind(str, Enum): password="password"; token="token"; cookie="cookie"; client_secret="client_secret"; api_key="api_key"; private_key="private_key"; other="other"

class RedactionPolicy(Model):                     # immutable; built from LoggingConfig.redaction + built-ins (additive only)
    extra_sensitive_keys: tuple[Label, ...] = ()
    extra_claim_allowlist: tuple[Label, ...] = ()
    min_canary_length: int = 8                    # 4..64
    max_text_bytes: int = 1_048_576               # 4 KiB..16 MiB
    encoded_depth: int = 2                        # 0..3 (DET-09)

class RedactionReport(Model):                     # counts only; never any matched text
    counts: dict[Label, Count]                    # rule id → hits (DET-xx, ENC-canary, KEY, HDR, URL)
    canary_hits: Count; changed: bool; truncated: bool

@dataclass(frozen=True) class Redacted(Generic[T]):   # constructible only by Redactor (private token); typed boundary currency
    value: T; report: RedactionReport; boundary: Boundary

class CanaryHandle(NamedTuple): id: str; label: str; forms: int; degraded: bool        # degraded = some encodings skipped (secret too short)

class Redactor:                                   # thread-safe; all methods sync, pure w.r.t. inputs; never raise
    def __init__(self, policy: RedactionPolicy = RedactionPolicy()) -> None
    def register_canary(self, secret: Secret, *, label: str, kind: SecretKind) -> CanaryHandle      # label = handle string or test label; ≤ 256 canaries
    def unregister_canary(self, handle: CanaryHandle) -> None
    def clear_canaries(self) -> None                                                                 # tests only (guarded by a flag set at construction)
    def redact_text(self, text: str, *, boundary: Boundary = Boundary.log) -> str
    def redact_value(self, value: JsonValue, *, boundary: Boundary = Boundary.log) -> Redacted[JsonValue]
    def redact_headers(self, headers: Mapping[str, str | Sequence[str]]) -> Redacted[dict[str, list[str]]]
    def redact_url(self, url: str) -> str
    def redact_body(self, body: bytes, *, media_type: str | None, max_bytes: int = 65_536) -> Redacted[RedactedBody]
    def redact_exception(self, exc: BaseException, *, include_traceback: bool = True) -> Redacted[str]
    def filter_claims(self, claims: Mapping[str, JsonValue]) -> dict[str, JsonValue]               # allow-list; unknown claims dropped
    def contains_canary(self, data: str | bytes) -> bool                                            # registered canaries (all forms) only; used as a post-write assertion by store/report/GUI
    def stats(self) -> Mapping[str, int]                                                           # canary count, forms, lifetime hits per rule

class RedactedBody(Model): kind: Literal["text","json","form","opaque"]; text: Annotated[str, Field(max_length=65_536)] | None; size: Count; sha256_redacted: Sha256Digest | None; truncated: bool; hits: Count
```

Contract: no method raises. On an internal failure (detector exception, pathological input) the method fails **closed**: `redact_text` returns `"${RG:redaction_failed}"`, `redact_value` replaces the offending leaf, and an event `redaction.failed{rule}` is logged (code `RGE-INTERNAL-0042` in the event, not raised). `Redactor.__repr__` shows only counts; `__reduce__` raises (canary forms are secret-equivalent). `RedactedBody.text` is bounded by `max_bytes`; `sha256_redacted` is the SHA-256 of the **redacted** text; the module never emits a hash of unredacted content (§15).

### 7.2 Structured logger and context (`rg_core.logging.context`, `handlers`)

```python
def get_logger(component: str) -> StructuredLogger         # component: Label, e.g. "rg.probe.runner"; returns RgLogger-backed adapter
class StructuredLogger:
    def event(self, level: int, name: str, /, **fields: object) -> None      # name per §10.7; fields flat, redacted by the gate
    def debug/info/warning/error/critical(self, msg: str, *args: object, **fields: object) -> None
    def exception(self, msg: str, exc: BaseException | None = None, **fields: object) -> None   # attaches ErrorRecord/traceback (redacted)
    def isEnabledFor(self, level: int) -> bool

@contextmanager def bind_context(*, experiment_id: str | None = KEEP, probe_id: str | None = KEEP, attempt_id: str | None = KEEP) -> Iterator[None]
def current_context() -> LogContext                         # NamedTuple(experiment_id, probe_id, attempt_id)

class RgLogger(logging.Logger):                             # addHandler(h) raises InternalError RGE-INTERNAL-0040 unless isinstance(h, RedactingHandler)
class RedactingHandler(logging.Handler):
    def __init__(self, inner: logging.Handler, *, redactor: Redactor, formatter: "RgFormatter", level: int = logging.NOTSET) -> None
    # emit(): format → final scrub → inner.handle(copy with msg=line, args=(), exc_info=None, exc_text=None)
def install_record_factory(redactor: Redactor, clock: Clock) -> Callable[[], None]       # returns uninstall(); idempotent; wraps the previous factory
def install_global_hooks(redactor: Redactor, logger: StructuredLogger) -> Callable[[], None]   # sys.excepthook, threading.excepthook, sys.unraisablehook, warnings capture, asyncio exception handler (set per loop by engine)
def assert_logging_safe(*, root: logging.Logger = logging.getLogger()) -> None            # walks root, rg tree and Logger.manager.loggerDict; raises RGE-INTERNAL-0040
```

### 7.3 Formatters and sinks

```python
class RgFormatter(logging.Formatter):  # abstract
class JsonFormatter(RgFormatter): ...     # one canonical JSON object per line (SCH-LOGREC), "\n" terminator, no ANSI
class TextFormatter(RgFormatter): ...     # "HH:MM:SS.mmm LEVEL component [exp=… probe=… att=…] event msg k=v …", always passed through sanitize_for_terminal

# revocationgap.logsetup (app)
def configure_logging(cfg: LoggingConfig, *, redactor: Redactor, clock: Clock, workspace: Path | None, holds_workspace_lock: bool,
                      stderr: TextIO = sys.stderr) -> LoggingHandle        # builds sinks, installs factory + hooks; raises StoreError RGE-STORE-0040 only when file.required=true
class LoggingHandle: def shutdown(self) -> None; def flush(self) -> None; stats: Mapping[str, int]
```

### 7.4 Terminal sanitiser (`rg_core.logging.terminal`) — TM-11

```python
def sanitize_for_terminal(text: str, *, max_len: int | None = None, allow_newlines: bool = False) -> str      # pure, O(n), idempotent
def escape_markup(text: str) -> str          # same semantics as rich.markup.escape (verified against rich by TST-…-20)
```

### 7.5 Error codes (block 0040–0059)

| Code | Name | Category | Raised/used when |
|---|---|---|---|
| `RGE-INTERNAL-0040` | UNREDACTED_HANDLER | INTERNAL | attaching a non-redacting handler to an `rg` logger, or `assert_logging_safe` finds one |
| `RGE-INTERNAL-0041` | CANARY_LIMIT_EXCEEDED | INTERNAL | more than 256 registered canaries (raised by `register_canary`; the only raising method) |
| `RGE-INTERNAL-0042` | REDACTION_FAILED | INTERNAL | recorded in the `redaction.failed` event (never raised) |
| `RGE-CONFIG-0040` | LOGGING_CONFIG_INVALID | CONFIG | `[logging]` validation failure (`details.field`, `details.reason`) |
| `RGE-STORE-0040` | LOG_FILE_UNWRITABLE | STORE | file sink cannot be opened and `file.required=true` (otherwise a warning event and console-only fallback) |

## 8. Data structures and schemas

### 8.1 `SCH-LOGREC` — one JSON log line (`schema_version "1.0"`; `LogRecordV1(Document)` with `SCHEMA_ID="log_record"`)

| Field | Type | Constraint | Description |
|---|---|---|---|
| `schema_version` | `SchemaVersion` | `"1.0"` | |
| `seq` | `Int64` | per-handler, strictly increasing | detects dropped/reordered lines |
| `ts` | `str` | RFC 3339 UTC, microseconds, `Z` | derived by integer arithmetic from `wall_ns` |
| `wall_ns` | `Int64` | decimal string | `Clock.wall_ns()` at record creation |
| `mono_ns` | `Int64` | decimal string | `Clock.mono_ns()` at record creation |
| `clock_id` | `Label` | `"system"` or `"virtual:<run>"` | |
| `level` | `Literal["DEBUG","INFO","WARNING","ERROR","CRITICAL"]` | | |
| `logger` | `Label` | ≤ 64 | component |
| `event` | `str` | grammar §10.7, ≤ 64 | `log.message` for plain messages |
| `msg` | `str` | ≤ 2048 code points, redacted, control characters escaped by JSON | |
| `fields` | `dict[Label→JsonScalar \| tuple]` | ≤ 32 keys, values ≤ 512 | structured fields, redacted |
| `experiment_id` / `probe_id` / `attempt_id` | `ExpId \| None` / `PrbId \| None` / `AttId \| None` | | correlation (omitted when None) |
| `thread` | `Label` | ≤ 64 | `rg-probe_3`, `MainThread` |
| `error` | `ErrorRecord \| None` | SCH-ERROR | present when an `RgError` is attached |
| `exc` | `str \| None` | ≤ 8192, redacted, no source lines, no locals | traceback text |
| `redactions` | `Count` | | number of replacements in this record |

Example (complete):

```json
{"attempt_id":"att_01M4QPJTKV04HMASW9NF6YY094","clock_id":"system","event":"probe.sent","experiment_id":"exp_01M4QPJTKV04HMASW9NF6YY093","fields":{"credential":"${RG:secret:env:RG_ALICE_TOKEN:fp:3f9a1c0d2b7e}","status":200,"url":"https://api.lab.invalid/v1/items?access_token=${RG:redacted:access_token}"},"level":"INFO","logger":"rg.probe.runner","mono_ns":"184467440737","msg":"probe sent","probe_id":"prb_01M4QPJTKV04HMASW9NF6YY095","redactions":2,"schema_version":"1.0","seq":"42","thread":"rg-probe_3","ts":"2026-10-12T09:20:00.123456Z","wall_ns":"1791796800123456789"}
```

### 8.2 Redaction marker grammar

`${RG:<body>[:fp:<12 hex>]}` where `<body>` is one of: (a) the **handle** of a registered canary exactly as the frozen architecture text prescribes (`secret:env:RG_ALICE_TOKEN`; characters outside `[A-Za-z0-9._:/@\\-]` replaced by `_`; test canaries use `canary:<n>`); (b) `detected:<detector>` with `<detector>` ∈ {`jwt`, `bearer`, `basic`, `cookie`, `key_value`, `pem`, `url_userinfo`, `high_entropy`, `encoded`, `vendor`}; (c) `redacted:<key>` (sensitive key/header/parameter name); (d) `redaction_failed`; (e) `truncated`. Regex: `\$\{RG:[A-Za-z0-9._:/@\\-]{1,200}\}`. A fingerprint suffix is present only for kinds `token`, `cookie`, `client_secret`, `api_key`, JWT and bearer detections; **never** for `password`, `private_key`, `basic`, `url_userinfo`, `high_entropy`, `other` (DEC-6). Markers are never re-processed (idempotence: detectors skip marker spans).

### 8.3 Policy tables

**Built-in sensitive key names** (case-insensitive, matched on the whole key after normalising `-`→`_`): `password, passwd, pwd, secret, client_secret, api_key, apikey, access_token, refresh_token, id_token, id_token_hint, token, assertion, code_verifier, private_key, credential, credentials, authorization, cookie, set_cookie, session, session_id, sessionid, sid_cookie, signature, sig, otp, pin`, plus any key matching `SECRET_KEY_NAME` of RG-P03-002. The OAuth `code` parameter is sensitive only in URL query/fragment and form bodies, not in JSON keys.

**Built-in sensitive headers:** `Authorization, Proxy-Authorization, Cookie, Set-Cookie, X-API-Key, Api-Key, X-Auth-Token, X-CSRF-Token, X-XSRF-Token, X-Amz-Security-Token, X-Goog-Api-Key, Ocp-Apim-Subscription-Key, DPoP`, plus any header name matching `(?i)(token|secret|key|password|auth|session|cookie|credential|signature)` except the pass-through list `Content-Type, Content-Length, Content-Encoding, Date, Server, Cache-Control, Age, Vary, ETag, Via, X-Cache, Retry-After, WWW-Authenticate`.

**Sensitive URL parameters:** `access_token, refresh_token, id_token, id_token_hint, token, code, client_secret, assertion, password, api_key, apikey, key, sig, signature, X-Amz-Signature, X-Amz-Security-Token, client_assertion, request` (the OIDC request object).

**Default claim allow-list (`filter_claims`):** `iss, aud, exp, iat, nbf, auth_time, jti, azp, client_id, scope, scp, roles, sid, acr, amr, typ, ver, tid, cnf, sub`. Everything else (e.g. `email`, `name`, `preferred_username`, `upn`, custom claims) is dropped; `extra_claim_allowlist` may add names but a name matching a sensitive key is rejected (`RGE-CONFIG-0040`). `sub` is retained because identities are synthetic (SCR-05) and it is the correlation key; operators handling real identities can remove it via `redaction.drop_sub=true`.

## 9. Inputs, outputs, and validation rules

**Detector catalogue** (applied by `redact_text` to every non-marker, non-protected span; each rule bounded by `max_text_bytes`; patterns use possessive quantifiers):

| Rule | Detects | Replacement | Guards |
|---|---|---|---|
| DET-01 | JWT/JWS (3 dot-separated base64url parts, third may be empty) and JWE (5 parts); first part must base64url-decode to a JSON object | `${RG:detected:jwt:fp:…}` | header must parse; parts ≥ 4 chars |
| DET-02 | authentication scheme + credential: `Bearer`, `Basic`, `Digest`, `Negotiate`, `NTLM`, `DPoP`, `MAC`, `AWS4-HMAC-SHA256`, `SSWS` (Okta API tokens; OKTA.md row A30 is tagged V\*/3P, so it is used only to widen detector coverage — a false positive costs nothing) followed by ≥ 8 non-space characters | scheme kept, credential → `${RG:detected:bearer:fp:…}` (`basic` without fp) | |
| DET-03 | cookie text `Cookie:`/`Set-Cookie:` lines and `name=value` pairs after those names | names kept; values → `${RG:detected:cookie:fp:…}`; attributes `Path, Domain, Expires, Max-Age, SameSite, Secure, HttpOnly, Partitioned` kept | |
| DET-04 | `key=value`, `key: value`, `"key":"value"`, `'key': 'value'` where key ∈ sensitive keys | value → `${RG:redacted:<key>}` (fp only for token-like keys) | empty/`null`/`true`/`false` values untouched |
| DET-05 | PEM private-key blocks (`PRIVATE KEY`, `ENCRYPTED PRIVATE KEY`, `OPENSSH PRIVATE KEY`, `PGP PRIVATE KEY BLOCK`) incl. body | `${RG:detected:pem}` | certificates are not redacted |
| DET-06 | URL userinfo `scheme://user:pass@host` | userinfo → `${RG:detected:url_userinfo}` | |
| DET-07 | sensitive URL query/fragment parameter values in any `http(s)/ws(s)` URL or relative `?…` string | value → `${RG:redacted:<param>}` | parameter names per §8.3 |
| DET-08 | high-entropy value after a keyword (`token`, `secret`, `password`, `key`, `bearer`, `credential`) followed by `:`/`=`/`is`: ≥ 16 chars of `[A-Za-z0-9+/=_.~-]`, Shannon entropy ≥ 3.5 bits/char | `${RG:detected:high_entropy}` | **protected spans** are skipped: RG ids (`exp_…`), `sha256:<hex>`, `fp:<hex>`, UUIDs, ISO-8601 timestamps |
| DET-09 | encoded secrets: words (maximal runs of `[A-Za-z0-9._~%+/=:-]`, ≥ 16 chars) whose percent-decoded and/or base64/base64url-decoded views (depth ≤ `encoded_depth`, decoded size ≤ 8 KiB, valid UTF-8) trigger DET-01, DET-02, DET-04, DET-05 | whole word → `${RG:detected:encoded}` | |
| DET-10 | caller-registered vendor patterns (`RedactionPolicy` extension, none by default) | `${RG:detected:vendor}` | extension API is internal (RG-P12 plugins in future) |

**Canary matching (`ENC-n`)**: see §12.2. A registered secret is replaced by `${RG:secret:<label>[:fp:…]}` wherever any of its forms occurs, *before* detectors run.

**Header rules** (`redact_headers`; names case-insensitive; multi-valued lists processed element-wise):
- H1 `Authorization`/`Proxy-Authorization`: scheme kept, credential replaced (DET-02 semantics).
- H2 `Cookie`: each `name=value` → name kept, value → `${RG:detected:cookie:fp:…}`; `Set-Cookie`: same, attributes kept (DET-03).
- H3 other sensitive headers (§8.3): whole value → `${RG:redacted:<header-lower>[:fp]}`.
- H4 `Location`, `Referer`, `Origin`, `Content-Location`: `redact_url`.
- H5 all remaining values: `redact_text` (so a token smuggled into `X-Debug` is caught by DET-01/02/04/09 and canaries).
- H6 `WWW-Authenticate` keeps `error`, `error_description`, `scope`, `realm`, `resource_metadata` parameters (needed by assertions, RFC 6750 §3) and passes through `redact_text`.

**URL rules** (`redact_url`): U1 parse with `urllib.parse.urlsplit` (failure → `redact_text` on the whole string); U2 userinfo removed (DET-06); U3 each query and fragment parameter in the sensitive list → value replaced, name kept, order kept; fragments that look like query strings (`#access_token=…`) are processed the same; U4 the path is passed through `redact_text` (secrets embedded in paths, e.g. `/reset/<token>`: DET-01/DET-09 and canaries); U5 scheme/host/port untouched.

**Body rules** (`redact_body`): B1 media type `application/json` or `+json` or sniffed JSON → parse with RG-P03-002 limits; keys in §8.3 → marker (value type irrelevant); all string leaves → `redact_text`; output canonical JSON; invalid JSON → treated as text. B2 `application/x-www-form-urlencoded` → parse pairs, sensitive names → marker (also `code`), other values → `redact_text`; re-encoded. B3 `text/*`, `application/xml`, `+xml`, `application/javascript` → `redact_text` (XML/SAML `<saml:Assertion>`/`<ds:SignatureValue>` content between tags whose local name contains `Assertion`, `Signature`, `Credential`, `Password`, `Token` → marker, B3a). B4 anything else, or invalid UTF-8 → kind `opaque`: `text=None`, only `size`; additionally the raw bytes are scanned for canary byte forms; a hit leaves the same descriptor (nothing else is kept). B5 input longer than `max_bytes` is cut **before** redaction at a UTF-8 boundary, `truncated=True`, and a `${RG:truncated}` marker is appended so a secret split by the cut cannot survive as a prefix (the cut tail is dropped, not stored).

**Exception rules** (`redact_exception`): X1 text = `<qualified type>: <redact_text(str(exc))>`; if `str(exc)` raises → `<unprintable>`. X2 `RgError`: `<code>: <message>` plus `details` as `k=v` with values redacted. X3 `__notes__` redacted. X4 cause/context chain up to depth 10, `ExceptionGroup` members up to 16 each, cycle-safe. X5 traceback frames: `File "<last 3 path components>", line N, in <func>` — **no source lines, no locals, no argument values**; absolute paths are shortened so OS user names in home directories do not leak. X6 total ≤ 8192 chars, clipped with `${RG:truncated}`.

**Context rules:** C1 `bind_context` validates `experiment_id`/`probe_id`/`attempt_id` against the id grammar of RG-P03-002; an invalid value is bound as `"<invalid>"` and logged once as `log.context_invalid` (binding never raises). C2 context is restored on exit even on exceptions.

**Handler rules:** L1 only `RedactingHandler` instances may be attached to `rg.*` loggers and to the root logger by `configure_logging`; L2 `assert_logging_safe` runs at `configure_logging` end, at `rg doctor`, and at the start of every experiment; L3 no configuration key can turn redaction off.

## 10. Detailed execution behavior

### 10.1 One log call, end to end (clock: injected `Clock`, read once per record)
1. `log.event(INFO, "probe.sent", url=u, status=200)` → `RgLogger._log`. 2. `isEnabledFor` check (cheap exit). 3. **Layer 1 — record factory** (`install_record_factory`): creates the `LogRecord`, then sets `rg_wall_ns/rg_mono_ns/rg_clock_id` from `Clock.now()` (one read), overrides `created`/`msecs` from them, pre-renders `getMessage()` (applying `%` args safely: a formatting error yields `<format error>`), replaces `msg` by `redact_text(rendered)`, sets `args=()`, converts `exc_info` into redacted text stored in `exc_text` and sets `exc_info=None`. 4. `rg_fields` (the structured fields from `extra`) are redacted by `RgLogger.makeRecord` (extras are attached *after* the factory runs, so the logger class handles them). 5. Handlers: `RedactingHandler.emit` → `JsonFormatter.format` (canonical JSON of §8.1, `error` from an attached `RgError` via `to_record(scrub=redactor.redact_text)`) → **Layer 3 — final scrub** `redact_text(line)` (JSON-escaped output could re-introduce forms; idempotent) → inner stdlib handler writes. 6. Failures inside handlers are swallowed by `Handler.handleError` override: first failure prints one line `log sink error (<sink>)` to stderr **without** the exception text, subsequent failures are counted.

### 10.2 Canary registration
`SecretResolver.resolve` (RG-P11-001) calls `redactor.register_canary(secret, label=str(handle), kind=…)`. The redactor builds the form set (§12.2), merges it into a new immutable snapshot (copy-on-write; readers are lock-free), and logs `redaction.canary_registered{label, forms, degraded}` — never the forms. Registration happens before the secret is returned to the caller, so no code path can hold an unregistered resolved secret.

### 10.3 Gate call sites (who calls what)

| Boundary | Caller | Calls | Post-condition check |
|---|---|---|---|
| log | record factory / handlers | `redact_text`, `redact_value` | final scrub |
| store | RG-P03-008 persistence | `redact_body`, `redact_headers`, `redact_value` before any write | `contains_canary(bytes) is False` asserted before commit; violation aborts the write (`RGE-STORE-…` in P03-008 block) |
| report | RG-P08-011 | `redact_text` on every target-derived string; `redact_value` on embedded JSON | `contains_canary(rendered)` on each artefact |
| gui/api | RG-P10-004 | `redact_value` on JSON responses; `redact_text` on rendered fragments | response middleware calls `contains_canary` |
| cli | RG-P10-001 | `redact_text` then `sanitize_for_terminal` for every target-derived or exception string | — |
| exception | engine/global hooks | `redact_exception` | — |
| export | RG-P08-001 bundles | same as store | `contains_canary` over every file |

### 10.4 Terminal sanitiser (TM-11)
Single pass over code points: (1) `\n` kept only when `allow_newlines`; (2) every other C0 control (U+0000–U+001F incl. `\t`, `\r`, `\b`, ESC), DEL, C1 (U+0080–U+009F incl. U+009B CSI, U+009D OSC, U+0085 NEL), line/paragraph separators U+2028/2029, bidirectional controls (U+061C, U+200E, U+200F, U+202A–U+202E, U+2066–U+2069), zero-width and joiner-class format characters used for spoofing (U+200B–U+200D, U+2060–U+2064, U+FEFF), tag characters (U+E0000–U+E007F) and unpaired surrogates are replaced by visible escapes `\xNN` (≤ U+00FF), `\uNNNN`, or `\UNNNNNNNN`; (3) all other characters pass unchanged; (4) if `max_len` is set the result is clipped to `max_len` code points with a trailing `…[+N]` (N = removed count). Because the ESC byte is escaped, a sequence like `ESC ] 8 ; ; http://evil ESC \ text ESC ] 8 ; ;` (OSC 8 hyperlink) is rendered as the harmless text `\x1b]8;;http://evil\x1b\text\x1b]8;;`. The function is idempotent (it adds only printable characters and never touches an existing backslash). `escape_markup` doubles nothing but prefixes `\` to every `[` that starts a tag-like token (`[a-z#/@…]`) exactly as `rich.markup.escape` does, so that bracket sequences in untrusted text cannot be interpreted as styles. **Author check:** `rich` 15.x passes raw ESC characters inside a `rich.text.Text` and inside `markup=False` strings through to the terminal (A-4), so the sanitiser is mandatory even when the CLI never uses markup.

### 10.5 Level semantics
`DEBUG` internals and (only with `log_bodies=true`) redacted, clipped bodies; `INFO` lifecycle (experiment states, probes sent, anchors); `WARNING` recoverable anomalies (clock anomaly, dropped non-critical events, rotation failure, canary degraded); `ERROR` an operation failed (an `RgError` is attached); `CRITICAL` safety stops (scope violation, invariant breach, audit append failure). No custom levels.

### 10.6 Sinks (app, `configure_logging`)
Console: handler on `sys.stderr` (stdout is reserved for command output and `--json`), level `console.level` (default `WARNING`), formatter text or JSON; output encoded with the stream encoding and `errors="backslashreplace"`. File: `RotatingFileHandler` subclass at `<data_dir>/logs/rg.log` created through the permission helper (0600 / owner-only ACL), `encoding="utf-8"`, `newline="\n"`, `delay=True`, `maxBytes`/`backupCount` from config; JSON formatter; attached **only when the process holds the workspace lock** (`holds_workspace_lock=True`: run/resume/lab/GUI server), so rotation never races across processes; read-only commands log to console only. A rotation `PermissionError` (Windows: file held open by another process) skips the rotation, appends to the current file and emits one `log.rotation_failed` warning.

### 10.7 Event and metric naming conventions

**Events** (log `event`, bus event `kind`): `<domain>.<noun>[.<verb>]` — 2 to 4 dot-separated segments, each `[a-z][a-z0-9_]*`, ≤ 64 chars total; past-tense verbs for facts (`probe.sent`, `experiment.state_changed`), no free text, no ids in the name. Domains: `experiment, probe, scheduler, executor, queue, runscope, abort, commit, cleanup, store, evidence, audit, config, plugin, provider, idp, target, authz, redaction, log, clock, lab`. (`runscope` = task scopes of RG-P03-005; `authz` = authorization scope of RG-P11-002.)

**Metrics:** `<domain>.<measure>` (2–3 segments), SI-style implicit units declared in the catalogue (durations in ns, sizes in bytes, counts unitless), never unit suffixes in the name; counters end in `.count`; gauges and histograms do not. Bus kind for a sample: `metric.<name>` (RG-P03-007 owns transport).

| Metric | Unit/type | Source | Architecture alias |
|---|---|---|---|
| `probe.latency` | ns, histogram | `t_recv_end − t_send_start` per attempt | `probe_latency` |
| `scheduler.lateness` | ns, histogram | `actual − intended` dispatch | `scheduling_lateness` |
| `queue.depth` | gauge | `BoundedQueue.stats` | `queue_depth` |
| `queue.dropped.count` | counter | drop_oldest drops | — |
| `executor.queue_delay` | ns, histogram | RG-P03-005 | — |
| `executor.running` / `executor.queue_depth` | gauge | RG-P03-005 | — |
| `loop.lag` | ns, histogram | `LoopLagMonitor` | — |
| `redaction.hits.count` | counter by rule | `Redactor.stats` | — |
| `store.commit_latency` | ns, histogram | RG-P03-008 | — |
| `evidence.bytes` | bytes, counter | RG-P03-008 | — |

The names `probe_latency`, `scheduling_lateness`, `queue_depth` used informally in SYSTEM-ARCHITECTURE §9 are aliases of the dotted names above (CCR-2).

### 10.8 Global hooks
`install_global_hooks`: `sys.excepthook` and `threading.excepthook` → `logger.critical("uncaught exception", exc)` then the original default behaviour is **not** invoked (it would print an unredacted traceback); `sys.unraisablehook` likewise; `logging.captureWarnings(True)` routes `warnings` to the `py.warnings` logger (which propagates to redacting root handlers); the engine sets `loop.set_exception_handler(handler)` per loop that logs `context["message"]` and the redacted exception. `faulthandler` is left enabled for fatal signals (it prints frames only, no values; A-6).

## 11. State transitions and invariants

`Redactor` canary registry: snapshot `Sₙ → Sₙ₊₁` on `register`/`unregister` (immutable snapshots, atomic reference swap under a lock; readers never lock). Logging setup: `UNCONFIGURED → CONFIGURED → SHUT_DOWN`; a second `configure_logging` call with identical arguments is a no-op, with different arguments it raises `RGE-INTERNAL-0040` (`details.reason="reconfigure"`, E-13).

| From | Event | To | Effect |
|---|---|---|---|
| UNCONFIGURED | `configure_logging` | CONFIGURED | factory, hooks, sinks installed; `assert_logging_safe` passes |
| CONFIGURED | `shutdown` | SHUT_DOWN | flush, uninstall factory/hooks, close sinks |
| any | `addHandler(non-redacting)` on `rg.*` | unchanged | raises `RGE-INTERNAL-0040` |

Invariants:
- **INV-1** For every registered canary and every output of every `Redactor` method and every sink: no form of ENC-1…ENC-9 occurs (SC-07; TST-…-09/-10).
- **INV-2** `redact_text(redact_text(x)) == redact_text(x)` (idempotence).
- **INV-3** `redact_text` and all other methods never raise and terminate in time linear in the (bounded) input size.
- **INV-4** Any substring of the output matching the marker grammar is either produced by the redactor or was already in the input; the redactor never emits a fingerprint for password-class secrets.
- **INV-5** Every handler reachable from an `rg.*` logger or the root logger configured by `configure_logging` is a `RedactingHandler` (`assert_logging_safe`).
- **INV-6** `sanitize_for_terminal(x)` contains no character in classes C0 (except permitted `\n`), DEL, C1, bidi controls, zero-width controls, surrogates, tag characters; and is idempotent.
- **INV-7** A log record is formatted from exactly one `Clock.now()` reading; two records created at the same virtual instant get strictly increasing `seq` per handler.
- **INV-8** Redaction does not change the *set of structured field names* of a record (only values), except for key renaming of invalid keys (RG-P03-005 E1).
- **INV-9** `RedactedBody.sha256_redacted` is a function of redacted text only; no function of this module returns a digest of unredacted input.

## 12. Core algorithms and pseudocode

### 12.1 `redact_text`
```
def redact_text(text, boundary):
    if len(text.encode()) > policy.max_text_bytes: text = text[:policy.max_text_bytes_chars] + "${RG:truncated}"      # cut first (B5 semantics)
    segs = split_on_markers(text)                               # marker spans are protected, never rewritten
    out = []
    for seg in segs:
        if seg.is_marker: out.append(seg.text); continue
        s = replace_canaries(seg.text)                          # §12.2, runs first: exact value knowledge beats heuristics
        s = DET_05(s); s = DET_06(s); s = DET_01(s); s = DET_02(s); s = DET_03(s); s = DET_04(s); s = DET_07(s)
        s = DET_08(s, protected=protected_spans(s)); s = DET_09(s, depth=policy.encoded_depth)
        out.append(s)
    return "".join(out)
# each DET_n wraps its own try/except: on exception → return "${RG:redaction_failed}" for the whole text and count RGE-INTERNAL-0042
```
Worked example. Registered canary `S = "hunter2-Secret!"` (kind `password`, label `secret:env:RG_ALICE_PASSWORD`). Input: `POST /login password=hunter2-Secret! Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhbGljZSJ9.c2ln&x=1 token=abc`. Steps: canary replaced → `password=${RG:secret:env:RG_ALICE_PASSWORD}` (no fp, password class); DET-01 sees the JWT (header `{"alg":"HS256"}` decodes to JSON) → `${RG:detected:jwt:fp:<12 hex>}`; DET-02 finds `Bearer` followed by a marker → untouched (protected); DET-04 `token=abc` → value `abc` is not empty → `token=${RG:redacted:token}`. Output: `POST /login password=${RG:secret:env:RG_ALICE_PASSWORD} Authorization: Bearer ${RG:detected:jwt:fp:…}&x=1 token=${RG:redacted:token}`.

### 12.2 Canary forms (`register_canary`)
Let `b = secret.reveal_bytes()`, `s = b.decode("utf-8")` (if decoding fails only byte forms are generated). Forms (set semantics; each form must be ≥ `min_canary_length` characters, else it is skipped and the handle is `degraded`):

| Id | Form | Notes |
|---|---|---|
| ENC-1 | `s`, plus NFC and NFD variants when they differ | raw |
| ENC-2 | base64 (standard alphabet) trimmed for 3 alignments | below |
| ENC-3 | base64url trimmed for 3 alignments | below |
| ENC-4 | percent-encoding: `quote(s, safe="")`, `quote_plus(s)`, `quote(s, safe="!'()*")` (JS `encodeURIComponent`), `quote(s, safe="/")`, each with upper- and lower-case hex digits | |
| ENC-5 | double percent-encoding of `quote(s, safe="")` | |
| ENC-6 | hex of UTF-8 bytes, lower and upper case | |
| ENC-7 | JSON string body: `json.dumps(s)[1:-1]` with `ensure_ascii` true and false | quotes, backslashes, `\uXXXX` |
| ENC-8 | HTML/XML escaped: `html.escape(s, quote=True)` | reports/GUI |
| ENC-9 | Python `repr(s)[1:-1]` | dict/list reprs in logs and tracebacks |

Base64 alignment algorithm (an embedded secret's encoding depends on its byte offset `o = position mod 3`): for `o ∈ {0,1,2}`: `e = b64(b"\x00"*o + b).rstrip("=")`; drop the first `{0:0, 1:2, 2:3}[o]` characters (they mix filler and secret bits) and, when `(o + len(b)) mod 3 ≠ 0`, drop the last character (it mixes secret bits with following bytes); the remainder is a form. Verified by the author: 20 000 random secrets (6–39 bytes) embedded with random 0–8 byte prefixes and suffixes were always matched by at least one of the 3 forms, standard and URL-safe alphabet (A-1). Worked example: `b = b"hunter2-secret"` (14 bytes) → forms `aHVudGVyMi1zZWNyZX` (o=0), `h1bnRlcjItc2VjcmV0` (o=1), `odW50ZXIyLXNlY3Jld` (o=2). A secret of 5 bytes yields forms shorter than 8 characters → skipped, `degraded=True` (raw and percent forms still apply).

Matching: build `index: dict[str, list[Form]]` keyed by the first 4 characters of each form (forms are ≥ 8 long); scan `text` at each position, look up `text[i:i+4]`, verify candidates longest-first, replace non-overlapping matches left to right. Secrets shorter than 8 characters are matched on raw form only, with non-alphanumeric boundaries (`(?<![A-Za-z0-9])…(?![A-Za-z0-9])`) to limit false positives, and are `degraded`. Complexity `O(n · (1 + candidates per prefix))`.

### 12.3 JWT detector (DET-01) and fingerprint
```
def det01(s):
    for m in JWT_CANDIDATE.finditer(s):          # (?>[A-Za-z0-9_-]{4,}\.){2,4}[A-Za-z0-9_-]*  anchored at word start
        parts = m.group(0).split(".")
        if len(parts) not in (3, 5): continue
        hdr = b64url_decode_json(parts[0])       # must be a JSON object, else skip
        if not isinstance(hdr, dict): continue
        yield m.span(), f"${{RG:detected:jwt:{fingerprint_of(m.group(0).encode())}}}"
```
(`fingerprint_of` returns `fp:<12 hex>`; marker `…:jwt:fp:3f9a1c0d2b7e}`.)

### 12.4 Sanitiser table (worked)

| Input (repr) | Output |
|---|---|
| `"ok"` | `ok` |
| `"\x1b[2J\x1b[H"` | `\x1b[2J\x1b[H` |
| `"\x1b]0;pwned\x07"` | `\x1b]0;pwned\x07` |
| `"a\rb"` | `a\rb` |
| `"txt\u202egpj.exe"` | `txt\u202egpj.exe` |
| `"zero\u200bwidth"` | `zero\u200bwidth` |
| `"\x9b31m"` | `\x9b31m` |
| `"line1\nline2"`, `allow_newlines=False` | `line1\nline2` (visible backslash-n) |
| `"line1\nline2"`, `allow_newlines=True` | unchanged (real newline) |
| `"x" * 300`, `max_len=100` | first 100 chars ending `…[+N]` such that total length = 100 |

### 12.5 Level/size accounting
`fields` values are clipped to 512 code points (`…[+N]`), `msg` to 2048; the record is dropped to `msg="record too large"` with `fields` removed if the final line exceeds 16 KiB (counted in `log.sink_stats`).

## 13. Internal functions, methods, or service operations

| Function | Signature | Purpose |
|---|---|---|
| `_split_on_markers` | `(s: str) -> list[Seg]` | protects existing markers |
| `_protected_spans` | `(s: str) -> list[tuple[int,int]]` | ids, digests, UUIDs, timestamps for DET-08 |
| `_entropy_bits_per_char` | `(s: str) -> float` | Shannon entropy |
| `_b64url_decode_json` | `(p: str) -> object \| None` | JWT header check |
| `_forms_for` | `(b: bytes, s: str \| None, min_len: int) -> tuple[list[Form], bool]` | ENC catalogue |
| `_Snapshot` | immutable class | `index`, `forms`, `canaries` (labels only) |
| `_mark` | `(kind, label, fp: str \| None) -> str` | marker builder with label sanitising |
| `_redact_json` | `(o: JsonValue, path) -> JsonValue` | key-based and leaf redaction |
| `_redact_form` | `(s: str) -> str` | form bodies |
| `_redact_xml_text` | `(s: str) -> str` | B3a |
| `_format_exception` | `(exc, depth) -> str` | X1–X6 |
| `_ts_from_ns` | `(wall_ns: int) -> str` | integer-only RFC 3339 formatting |
| `_RecordFactory` | callable class | layer 1 |
| `_guard_add_handler` | `(logger, h)` | L1 |
| `_safe_str` | `(o) -> str` | `str()` that never raises |

## 14. Error handling and failure recovery

| Failure | Detection | Handling | Recovery | Code |
|---|---|---|---|---|
| Detector exception/ReDoS guard (> 50 ms per call via input-size bound) | try/except in each rule; input cap | whole text → `${RG:redaction_failed}`; counter | none needed; bug filed from event | RGE-INTERNAL-0042 (event) |
| Non-redacting handler attached | `addHandler` guard / `assert_logging_safe` | raise at attach/startup | fix configuration | RGE-INTERNAL-0040 |
| > 256 canaries | registration | raise | resolver unregisters unused handles | RGE-INTERNAL-0041 |
| Log file cannot be opened | `configure_logging` | `required=false`: warning + console-only; `true`: raise | fix permissions/path | RGE-STORE-0040 |
| Sink write error | `handleError` override | one stderr line, counter | rotation/disk fix | — |
| Rotation PermissionError (Windows) | `doRollover` wrapper | continue appending; one warning | close other readers | — |
| Format error in `%` args | factory | `<format error>` message | — | — |
| Invalid correlation id | `bind_context` | bound as `<invalid>` | — | — |
| Clock read failure | factory | fall back to previous record's stamps + `clock_fault=true` field | — | — |

Partial failure: a record is either fully redacted or replaced; never emitted partially.

## 15. Security requirements and trust boundaries

* **Untrusted inputs:** every string handed to the redactor may be target-controlled (headers, bodies, error texts, identity names). The redactor treats inputs as data only; it never evaluates, decodes beyond depth 2, or follows references.
* **TM-07:** (1) typed `Secret` (RG-P03-002) prevents accidental formatting; (2) canary registry catches *known* secrets in any encoding even where shape detectors would not (e.g. a short password); (3) shape detectors catch *unknown* tokens; (4) three layers (factory, handler, formatter) so that bypassing one — a foreign handler on the root logger, `extra=` fields, JSON re-encoding — does not leak; (5) global hooks cover crash output; (6) `assert_logging_safe` detects foreign handlers; (7) fingerprints omitted for password-class secrets.
* **TM-11 / FR-CLI-003:** sanitiser as specified; console sink always sanitises; JSON log files escape control characters by encoding (a `tail -f` of a JSONL file cannot inject escapes).
* **TM-14:** log fields cannot forge lines: JSON encoding of newlines in `msg`; the text formatter runs the sanitiser with `allow_newlines=False`.
* **TM-08:** `RedactedBody.sha256_redacted` only; no unredacted hash (a hash of a body containing a low-entropy password enables offline guessing).
* **Residual risks:** (a) secrets split across separate log lines or fields; (b) secrets that were never registered and have no recognisable shape (e.g. an opaque 12-character admin password in free text without a keyword) — mitigated by `SecretHandle`-only configuration (they are always resolved through `SecretResolver`, hence registered); (c) base64 forms of *derived* values (hash of the secret) are not secrets; (d) a plugin that logs via `print()` bypasses the logger — hooks cover `sys.excepthook`, not `sys.stdout`; plugins are fully trusted code (TM-22).
* **Access to forms:** the canary snapshot is secret-equivalent: never logged, never pickled, excluded from `repr`, not exposed by `stats()`.

## 16. Concurrency, asynchronous behavior, and resource ownership

* `Redactor`: thread-safe; the canary snapshot is swapped atomically under a `threading.Lock` held only during registration (≤ a few ms); reads are lock-free. Hit counters use per-thread local counters merged on `stats()`.
* `RedactingHandler.emit` runs in the calling thread (stdlib handlers lock per handler with `Handler.lock`); the inner handler's I/O therefore blocks the caller for the duration of one write. File and console writes are local and short; there is no queue/listener thread by default (a `QueueHandler` variant is deferred: its queue would be lossy or blocking, both unacceptable on the measurement path; A-5). Consequence: logging in the event loop thread performs synchronous local file writes (≤ 100 µs typical); RG-LINT-002 does not flag logging calls. Large bodies must never be logged at INFO.
* Correlation context uses `contextvars`: task creation copies the context; `ExecutorSet.run_blocking` (RG-P03-005) copies it into worker threads; threads created by third-party code do not inherit it (their records carry no ids).
* `seq` counters are per handler under the handler lock.
* Ownership: `LoggingHandle` owns sinks and the installed factory/hooks; `shutdown()` flushes and closes in reverse order and restores the previous record factory and hooks.

## 17. Performance and resource requirements

Proposals (validated by benchmarks, not measured facts):

| Budget | Value | Rationale | Test |
|---|---|---|---|
| `redact_text`, 256-byte typical log text, ≤ 16 canaries (≈ 600 forms) | mean ≤ 50 µs, p99 ≤ 200 µs | 50 probes/s × ~5 lines ≪ 15 % of a core (NFR-PERF-005) | TST-RG-P03-004-24 |
| `redact_text`, 4 KiB | p99 ≤ 2 ms | header/URL dumps | TST-RG-P03-004-24 |
| `redact_body`, 64 KiB JSON | p95 ≤ 10 ms | default capture cap (NFR-PERF-007) | TST-RG-P03-004-24 |
| `register_canary` (1 secret, ≈ 40 forms) | ≤ 5 ms; 256 canaries ≤ 1 s total | resolution happens at run start | TST-RG-P03-004-24 |
| JSON log line formatting | ≤ 30 µs mean | | TST-RG-P03-004-24 |
| Memory of 256 canaries | ≤ 5 MiB | | TST-RG-P03-004-24 |
| Adversarial input (1 MiB of `eyJ.`-like or `=`-runs) | ≤ 100 ms (bounded by `max_text_bytes` and possessive quantifiers) | ReDoS resistance | TST-RG-P03-004-22 |
| Sanitiser | ≥ 50 MB/s for ASCII | | TST-RG-P03-004-24 |
| Log volume | file sink default 5 MiB × 5 files | TM-34 | TST-RG-P03-004-19 |

## 18. Configuration and defaults

`[logging]` section model `LoggingConfig` (registered in the RG-P03-003 section registry, owner RG-P03-004). Env var `RG_LOGGING_<PATH>` (path joined by `_`).

| Key | Type | Default | Range / values | Env | Reload | Failure behaviour |
|---|---|---|---|---|---|---|
| `logging.level` | enum | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL | `RG_LOGGING_LEVEL` | live | `RGE-CONFIG-0040` |
| `logging.console.level` | enum | `WARNING` | same | `RG_LOGGING_CONSOLE_LEVEL` | live | idem |
| `logging.console.format` | enum | `text` | `text`, `json` | `RG_LOGGING_CONSOLE_FORMAT` | next_run | idem |
| `logging.file.enabled` | bool | `true` | | `RG_LOGGING_FILE_ENABLED` | next_run | |
| `logging.file.path` | Path | `<data_dir>/logs/rg.log` | inside workspace unless absolute and writable | `RG_LOGGING_FILE_PATH` | restart | `RGE-CONFIG-0040` (path rules of RG-P03-003) |
| `logging.file.level` | enum | `INFO` | | `RG_LOGGING_FILE_LEVEL` | live | |
| `logging.file.max_bytes` | ByteSize | `5MiB` | 64KiB–1GiB | `RG_LOGGING_FILE_MAX_BYTES` | restart | |
| `logging.file.backup_count` | int | 5 | 0–50 | `RG_LOGGING_FILE_BACKUP_COUNT` | restart | |
| `logging.file.required` | bool | `false` | | `RG_LOGGING_FILE_REQUIRED` | restart | `true` → `RGE-STORE-0040` on open failure |
| `logging.log_bodies` | bool | `false` | requires `level=DEBUG` | `RG_LOGGING_LOG_BODIES` | next_run | `true` with level above DEBUG → `RGE-CONFIG-0040`; counted as a safety relaxation (audited, FR-SEC-014) |
| `logging.body_log_bytes` | ByteSize | `1KiB` | 0–16KiB | `RG_LOGGING_BODY_LOG_BYTES` | next_run | |
| `logging.redaction.extra_sensitive_keys` | list[Label] | `[]` | ≤ 64 entries; additive only | `RG_LOGGING_REDACTION_EXTRA_SENSITIVE_KEYS` (comma-separated) | next_run | |
| `logging.redaction.extra_claim_allowlist` | list[Label] | `[]` | ≤ 64; may not match a sensitive key | `RG_LOGGING_REDACTION_EXTRA_CLAIM_ALLOWLIST` | next_run | `RGE-CONFIG-0040` |
| `logging.redaction.drop_sub` | bool | `false` | | `RG_LOGGING_REDACTION_DROP_SUB` | next_run | |
| `logging.redaction.min_canary_length` | int | 8 | 4–64 | `RG_LOGGING_REDACTION_MIN_CANARY_LENGTH` | restart | lowering below 8 marks all short canaries `degraded` |
| `logging.redaction.max_text_bytes` | ByteSize | `1MiB` | 4KiB–16MiB | `RG_LOGGING_REDACTION_MAX_TEXT_BYTES` | restart | |

There is deliberately **no** `logging.redaction.enabled` key (L3, FR-SEC-014).

## 19. Logging, observability, evidence requirements

Events emitted by this module (logger `rg.logging`): `redaction.canary_registered{label,kind,forms,degraded}` (INFO), `redaction.failed{rule}` (ERROR), `redaction.hit_summary{counts}` (DEBUG, periodic), `log.sink_error{sink}` (WARNING, once per sink), `log.rotation_failed{path_basename}` (WARNING), `log.sink_unavailable{sink}` (WARNING), `log.guard_violation{logger}` (CRITICAL), `log.context_invalid{field}` (WARNING). Metrics: `redaction.hits.count{rule}`, `log.records.count{level}`, `log.dropped.count`. Evidence: `RedactionReport` (counts only) attached to every redacted evidence item's metadata by RG-P03-008; run manifest records `redactor: {policy_digest, canary_count, degraded_count}` (`policy_digest` = `digest(policy, "rg.config.v1")`). Reports include a "redaction applied" statement and the counts, never samples.

## 20. Platform compatibility

* **Encoding/newlines:** file sink UTF-8 with LF on all platforms (the sink overrides `_open` to pass `newline="\n"`; stdlib would translate to CRLF on Windows). Console output uses the stream's encoding with `backslashreplace`, so a cp1252 console never raises `UnicodeEncodeError`.
* **Windows:** log rotation can fail with `PermissionError` when another process holds the file; handled (§10.6). Long paths: the sink receives an already-normalised path (RG-P03-003 adds the `\\?\` prefix when the path exceeds the legacy limit). File creation permissions via the owner-only ACL helper (RG-P03-008).
* **POSIX:** files created `0600` through `os.open(…, 0o600)`; umask irrelevant.
* **Terminals:** sanitiser independent of terminal type; ANSI colour is never emitted by the logging layer (the CLI may colour its own output after sanitising).
* **Clock:** timestamps from `Clock`; with `VirtualClock` log files are deterministic (golden-file tests).
* **Python 3.11–3.14:** `logging` record-factory and `LoggerAdapter` APIs unchanged; `logging.getLevelNamesMapping` (3.11+) used for level validation.

## 21. Edge cases and invalid inputs

| # | Case | Expected behaviour |
|---|---|---|
| E-1 | secret appears across two `%s` args (`"%s%s", a, b`) | factory renders first → canary matched in the combined text |
| E-2 | secret in `extra={"rg_fields": {...}}` or logger `**fields` | redacted by `RgLogger.makeRecord` (fields) and again by the handler |
| E-3 | secret inside an exception message of a `requests`-like exception (URL with `?access_token=…`) | DET-07/canary in `redact_exception`; global excepthook output redacted |
| E-4 | base64 of `user:password` in `Authorization: Basic …` | DET-02 replaces the credential; canary base64 alignments also match |
| E-5 | URL-encoded password in a form body (`password=p%40ss`) | B2 → marker by key; canary ENC-4 covers any other location |
| E-6 | secret `"a"` (1 char) registered | `degraded=True`, raw-with-boundaries only; warning event; recommended minimum 8 |
| E-7 | huge input (50 MiB) | cut to `max_text_bytes` first; `${RG:truncated}` appended |
| E-8 | invalid UTF-8 bytes in body | kind `opaque`; canary byte-scan only |
| E-9 | text already containing markers | untouched (INV-2) |
| E-10 | log message contains `\n` forged line `{"level":"INFO"…}` | JSON-escaped within `msg`; text formatter shows `\n` visibly |
| E-11 | foreign library attaches a `StreamHandler` to the root logger after `configure_logging` | factory still redacts records; `assert_logging_safe` (startup of next experiment/doctor) reports `RGE-INTERNAL-0040` |
| E-12 | `bind_context(experiment_id="'; DROP")` | bound as `<invalid>`; no exception |
| E-13 | `configure_logging` called twice with different config | second call raises `RGE-INTERNAL-0040` (`reason=reconfigure`); identical config is a no-op |
| E-14 | ISO timestamps, `exp_…` ids, `sha256:<64 hex>`, UUIDs in text | unchanged (protected spans) |
| E-15 | JWT whose header is not JSON (`aaa.bbb.ccc`) | not treated as JWT; DET-08/09 may still apply if keyword context exists |
| E-16 | cookie `lang=en` in `Cookie` header | value replaced anyway unless listed in the cookie allow-list (default empty) |
| E-17 | claims containing `email` | dropped by `filter_claims` |
| E-18 | exception whose `__str__` raises | `<unprintable>` |
| E-19 | record with `exc_info` of `RgError` carrying `details` secret strings | `ErrorRecord` built with `scrub`; details values pass the redactor |

## 22. Unit and integration test requirements

- **TST-RG-P03-004-01** Canary forms catalogue: for 12 representative secrets (ASCII, specials `p@ss w0rd/+=é"'<>&`, CJK, emoji with ZWJ, NFC/NFD pair, 8-char minimum, 64-char, JWT-shaped, PEM-ish, random bytes as latin-1) each ENC-1…ENC-9 form is generated and `redact_text` removes it when it appears alone, with prefix/suffix noise, and inside JSON strings.
- **TST-RG-P03-004-02** Base64 alignment: vector `hunter2-secret` → the 3 forms of §12.2; property over 20 000 random secrets/prefixes/suffixes (standard and URL-safe, padded and unpadded) — always matched; a deliberately wrong alignment table fails the test (mutation check).
- **TST-RG-P03-004-03** Detector catalogue DET-01…DET-09 positive corpus (≥ 6 samples each, including JWE, `SSWS` token, `Basic`, PEM `OPENSSH PRIVATE KEY`, URL userinfo, fragment `#access_token=`, double-encoded JWT) and negative corpus (RG ids, digests, UUIDs, timestamps, `fp:` values, markers, prose, JSON without sensitive keys): every positive redacted, every negative unchanged.
- **TST-RG-P03-004-04** Worked example of §12.1: exact output string equality (with a fixed fingerprint function).
- **TST-RG-P03-004-05** Marker policy: password-class canaries and `Basic` detections never carry `fp:`; token/JWT/cookie do; markers match the grammar regex; idempotence `redact(redact(x)) == redact(x)` property over generated texts (INV-2).
- **TST-RG-P03-004-06** Header rules H1–H6 table-driven (≥ 20 header cases incl. multi-valued `Set-Cookie`, `WWW-Authenticate: Bearer error="invalid_token"` kept, `Location` with token in query, custom `X-Debug` smuggling a JWT).
- **TST-RG-P03-004-07** URL rules U1–U5 (userinfo, query, fragment, path token, IPv6 host, malformed URL fallback) and DET-07 on relative query strings.
- **TST-RG-P03-004-08** Body rules B1–B5: JSON with nested sensitive keys, form body, XML/SAML assertion, binary opaque with canary bytes, cut-point splitting a secret across `max_bytes` (no prefix of the secret survives), `sha256_redacted` equals SHA-256 of the returned text and no API returns a hash of the input (INV-9).
- **TST-RG-P03-004-09** SC-07 canary fuzz, log path: Hypothesis builds 200 canaries × carriers C1–C14 (message, `%s` args, f-string, `extra`, exception chain, `raise from`, traceback, repr of dict, JSON/form bodies, URL, headers, nested dict, bytes, `RgError.details`) × encodings (all ENC forms generated by an **independent test-side encoder** plus a decoding oracle that base64-decodes every long word of the output at 3 alignments and looks for canary bytes); all configured sinks capture output (in-memory console handler, JSON file handler on a temp dir, foreign root handler); assertion: 0 occurrences of any canary or form in any sink.
- **TST-RG-P03-004-10** SC-07 canary fuzz, gate path: the same generator against `redact_value`, `redact_headers`, `redact_body`, `redact_exception`, `filter_claims` outputs and `contains_canary` (must be `False` on outputs and `True` on raw inputs).
- **TST-RG-P03-004-11** Layer independence: with the record factory uninstalled the handler layer alone passes TST-09; with the handler layer bypassed (inner handler attached to a foreign logger) the factory layer alone redacts message and exception text; with both bypassed the formatter scrub alone redacts the formatted line (three mutation runs, each must still pass for its own layer).
- **TST-RG-P03-004-12** Handler guard: `RgLogger.addHandler(logging.StreamHandler())` raises `RGE-INTERNAL-0040`; attaching a `RedactingHandler` works; `assert_logging_safe` flags a foreign root handler and a handler hidden on a child logger from `Logger.manager.loggerDict`; `configure_logging` twice (E-13).
- **TST-RG-P03-004-13** Exception redaction X1–X6: URL-with-token exception message, `RgError` with details, `__notes__`, 12-deep cause chain, `ExceptionGroup` of 20 members, exception with raising `__str__`, absolute-path shortening, no source lines or locals even when a local variable holds a canary.
- **TST-RG-P03-004-14** Global hooks: raising in the main thread (subprocess), in a worker thread, in `__del__` (unraisable), a `warnings.warn` with a canary, an asyncio task exception with canary → captured stderr/log contain 0 canaries and one redacted record each; default `sys.excepthook` output not emitted.
- **TST-RG-P03-004-15** Formatter: `SCH-LOGREC` golden lines under `VirtualClock` (byte-equal), integer-only timestamp formatting (`ts` for `wall_ns=1791796800123456789` is `2026-10-12T09:20:00.123456Z`), per-handler `seq` strictly increasing under 8 threads, records > 16 KiB replaced.
- **TST-RG-P03-004-16** Correlation context: ids propagate into child tasks, into `run_blocking` worker threads (RG-P03-005 fixture) and reset on exit; invalid id bound as `<invalid>` (E-12); JSON lines carry the three ids.
- **TST-RG-P03-004-17** Fingerprint policy: `fingerprint_of(b"hunter2") == "fp:f52fbd32b2b3"` appears for a `token`-kind canary and never for `password`-kind (DEC-6 test); two tokens never share a marker.
- **TST-RG-P03-004-18** Claim allow-list: `filter_claims` keeps exactly the defaults; `extra_claim_allowlist` additive; sensitive-name extension rejected (`RGE-CONFIG-0040`); `drop_sub=true` removes `sub`; unknown/PII claims dropped.
- **TST-RG-P03-004-19** Sinks (`logsetup`, temp workspace): rotation at `max_bytes` produces `rg.log.1…N` and never more than `backup_count` files; files `0600` on POSIX; LF newlines on Windows; console uses stderr only; read-only command mode (no workspace lock) attaches no file sink; `file.required=true` with unwritable path → `RGE-STORE-0040`, `false` → warning + console only; Windows `PermissionError` rotation simulated by holding the file open (marker `windows`).
- **TST-RG-P03-004-20** Terminal sanitiser: table of §12.4; property: output has no forbidden class (INV-6) and is idempotent; ANSI/OSC/OSC 8/bidi/zero-width/C1 corpus (≥ 60 samples, including the TM-11 examples); `escape_markup` equals `rich.markup.escape` on 500 generated strings (test skipped when `rich` is not installed in the app test env); a rendered `rich.Console` capture of sanitised corpus contains no ESC byte.
- **TST-RG-P03-004-21** Event/metric naming: AST scan of `src/**` finds every `event(...)` literal matching the grammar of §10.7 and registered in `rg_core.logging.events`; metric names match the catalogue.
- **TST-RG-P03-004-22** ReDoS/adversarial: 1 MiB inputs (`eyJ` repeated, `=` runs, nested brackets, 10⁵ `%` sequences, very long base64-like words) complete ≤ 100 ms each and never raise.
- **TST-RG-P03-004-23** Registry limits: 257th canary → `RGE-INTERNAL-0041`; `unregister` frees a slot; concurrent registration from 8 threads while 8 threads redact (no exception, no missed redaction after registration returns).
- **TST-RG-P03-004-24** Benchmarks (marker `bench`) for every row of §17.
- **TST-RG-P03-004-25** Config model: all `[logging]` rows validated (defaults, ranges, `log_bodies` requires DEBUG, no `redaction.enabled` key → unknown-key error from RG-P03-003), reload classes declared.

## 23. Mocking and test fixture requirements

* `rg_core.testing.RecordingHandler` (captures formatted lines and the `LogRecord`s), `CanarySet` generator (`make_canaries(n, seed)` returns secrets with metadata), independent encoder/decoder oracle in `tests/support/canary_oracle.py` (must not import production encoders), `FakeClock`/`VirtualClock`.
* Corpora under `tests/data/redaction/`: `positive/*.txt`, `negative/*.txt`, `terminal_injection.txt` (TM-11 samples), `headers.json`, `bodies/*`.
* Subprocess harness `tests/support/crash_runner.py` for global hooks and signal-time behaviour.
* Process-level SC-07 sweep fixture (shared with RG-P11-001): lab workspace + canary secrets → search `.rg/**`, SQLite WAL, logs, reports, stdout/stderr for all forms (this spec supplies the oracle; RG-P11-001 owns the end-to-end test).
* Hypothesis (test-only); `rich` (dev dependency of the app test suite only).

## 24. Objective acceptance criteria

- **AC-RG-P03-004-01** For every registered canary, none of its raw, base64/base64url (3 alignments), percent-encoded (single, double, plus/lower-hex variants), hex, JSON-escaped, HTML-escaped or `repr`-escaped forms appears in any log sink output, `Redacted` result or exception text, over ≥ 10 000 fuzzed carriers (verified by TST-RG-P03-004-01, TST-RG-P03-004-02, TST-RG-P03-004-09, TST-RG-P03-004-10).
- **AC-RG-P03-004-02** Unregistered secrets of recognised shape (JWT/JWE, Bearer/Basic/SSWS credentials, cookies, sensitive key/value pairs, PEM private keys, URL userinfo, sensitive query/fragment parameters, encoded variants) are replaced, while RG ids, digests, UUIDs and timestamps are untouched (verified by TST-RG-P03-004-03, TST-RG-P03-004-04, TST-RG-P03-004-06, TST-RG-P03-004-07).
- **AC-RG-P03-004-03** Redaction is idempotent, never raises, and bounded in time on adversarial 1 MiB inputs (verified by TST-RG-P03-004-05, TST-RG-P03-004-22).
- **AC-RG-P03-004-04** Body redaction never stores or returns a hash of unredacted content and no prefix of a secret split by the size cut survives (verified by TST-RG-P03-004-08).
- **AC-RG-P03-004-05** Redaction holds if any one of the three layers is bypassed, and attaching a non-redacting handler to an `rg` logger or leaving one on the root logger is detected (verified by TST-RG-P03-004-11, TST-RG-P03-004-12).
- **AC-RG-P03-004-06** Exception messages, notes, chains and tracebacks are redacted without source lines or locals, and uncaught exceptions, thread exceptions, unraisables, warnings and asyncio errors reach logs only through the gate (verified by TST-RG-P03-004-13, TST-RG-P03-004-14).
- **AC-RG-P03-004-07** Log lines conform to `SCH-LOGREC`, are deterministic under the virtual clock and carry correlation ids across tasks and worker threads (verified by TST-RG-P03-004-15, TST-RG-P03-004-16).
- **AC-RG-P03-004-08** Fingerprints appear only for high-entropy credential classes and never for passwords (verified by TST-RG-P03-004-17).
- **AC-RG-P03-004-09** JWT claims are filtered through the documented allow-list with additive-only extension (verified by TST-RG-P03-004-18).
- **AC-RG-P03-004-10** Console and rotating-file sinks behave as specified on Linux and Windows (stderr only, 0600/owner-only files, LF newlines, bounded rotation, lock-holder-only file sink) (verified by TST-RG-P03-004-19, TST-RG-P03-004-25).
- **AC-RG-P03-004-11** The terminal sanitiser leaves no control, escape, bidi or zero-width character in output, is idempotent, and `escape_markup` matches `rich.markup.escape` (verified by TST-RG-P03-004-20).
- **AC-RG-P03-004-12** All emitted event and metric names follow the naming grammar and catalogue (verified by TST-RG-P03-004-21).
- **AC-RG-P03-004-13** The canary registry enforces its limit and is safe under concurrent registration and redaction (verified by TST-RG-P03-004-23).
- **AC-RG-P03-004-14** The performance proposals of §17 are met on the reference runner or reported with the measured deviation (verified by TST-RG-P03-004-24).

## 25. Research sources and engineering rationale

Sources: SYSTEM-ARCHITECTURE §6.2 (redaction gate, marker format `${RG:<handle>:<fingerprint>}`), §9 (logging cross-cutting), DATA-MODEL §2.4 (fingerprint = `sha256(material)[:12]`), §9 invariant 7 (canary test); PRD FR-SEC-005/-006/-014, FR-OPS-005, FR-CLI-003, FR-EVD-006; THREAT-MODEL TM-07, TM-08, TM-11, TM-14; Charter SC-07; TECHNICAL-FEASIBILITY §2 (CLI: click + rich), R-013; providers research: OKTA §A30 (SSWS scheme), AUTH0 revoke endpoint parameters (`token`, `client_secret` in request bodies), AUTHLIB-AND-LIBS (client auth methods → `client_assertion`, `client_secret` appear on the wire). Interpretation of `rich` behaviour is an author sandbox check (A-4). RFC 6750 §3 (`WWW-Authenticate` parameters retained) is cited via STANDARDS-REFERENCE SV-009.

Decisions:

- **DEC-1 Single central `Redactor` with three layers** (record factory, handler wrapper, formatter scrub) instead of a logging filter only. A `logging.Filter` on handlers is bypassed by any foreign handler and by `extra`/formatter paths; the factory makes redaction independent of handler topology. Rejected: filter-only; wrapping `sys.stdout`/`sys.stderr` (hides, but does not protect files and stores). Verification: TST-…-11, -12.
- **DEC-2 Value-based canaries first, shape detectors second.** Exact knowledge of runtime secrets in all encodings is more reliable than heuristics; heuristics catch unregistered tokens. Rejected: shape-only (misses short passwords), canary-only (misses tokens received from IdPs that RG never resolved from a handle). Verification: TST-…-01, -03.
- **DEC-3 Three base64 alignments with trimmed boundary characters** rather than encoding the secret with fixed padding only. Verification: TST-…-02 (property + mutation check).
- **DEC-4 First-4-character prefix index instead of a regex alternation or Aho–Corasick.** Python `re` alternations degrade linearly with branch count; a prefix index is simple, dependency-free and meets the proposed budget; Aho–Corasick remains the documented fallback if TST-…-24 fails. Verification: TST-…-24.
- **DEC-5 Redaction output is markers, not asterisks**: markers are greppable, carry kind/label for debugging, are idempotent, and let tests distinguish "redacted" from "absent". Rejected: `***` (loses provenance), deleting values (changes structure). Verification: TST-…-05.
- **DEC-6 No fingerprint for password-class secrets** (and for private keys, Basic credentials, userinfo, unknown high-entropy text). A 48-bit truncated SHA-256 of a low-entropy password can be confirmed offline by dictionary search; for generated tokens (≥ 128 bits) it cannot. The frozen fingerprint format is unchanged for the classes where it is safe; the frozen text "truncation prevents recovery" is accurate only for high-entropy material (CCR-3). Verification: TST-…-17.
- **DEC-7 No hash of unredacted bodies** (`sha256_redacted` only). Rejected: `original_sha256` for dedupe (offline guess oracle for form bodies containing passwords). Cost: RG-P03-008 deduplicates on redacted content only. Verification: TST-…-08.
- **DEC-8 Synchronous handlers, no listener thread.** A `QueueHandler`/`QueueListener` pair needs an unbounded or lossy queue (TM-34 vs evidence): lossy logging could drop the very line that explains an incident; unbounded violates NFR-PERF-006. File writes are local and short. Rejected for v1; revisit if TST-RG-P03-005-23 shows loop-lag regressions from logging. Verification: TST-…-24.
- **DEC-9 Sanitiser escapes instead of deleting** control characters (TM-11 asks for visible escapes), is idempotent, and is a separate mandatory step from `rich` markup handling. Verification: TST-…-20.
- **DEC-10 File sink only in the workspace-lock holder.** Avoids multi-process rotation races without cross-process locks. Rejected: file locking around rotation (Windows semantics differ). Verification: TST-…-19.
- **DEC-11 No config key disables redaction.** Rejected: `--no-redact` flag (the only legitimate raw capture is the encrypted, audited path of RG-P11-003 which is a separate mechanism). Verification: TST-…-25.
- **DEC-12 Exceptions rendered without source lines or locals.** Rejected: `traceback.format_exception(capture_locals=True)` (prints `repr` of locals, may include tokens). Verification: TST-…-13.

## 26. Remaining uncertainties or assumptions

| # | Assumption | Falsifying test |
|---|---|---|
| A-1 | The 3-alignment trimmed base64 forms cover every embedding of a secret in standard and URL-safe base64 (author prototype: 20 000 random embeddings, 0 misses) | TST-…-02 |
| A-2 | Python 3.11+ `re` supports possessive quantifiers/atomic groups, bounding backtracking; detectors stay within the 100 ms adversarial budget | TST-…-22 on 3.11–3.14 |
| A-3 | Heuristic thresholds (entropy ≥ 3.5 bits/char, ≥ 16 chars, keyword proximity) give an acceptable false-positive rate on RG's own log/evidence vocabulary | negative corpus TST-…-03 plus measured FP rate on lab run logs (≤ 1 per 10 000 lines, proposal) |
| A-4 | `rich` (15.x in the author sandbox) does not strip ESC/OSC sequences from `Text` or from `markup=False` strings; `rich.markup.escape` semantics as in §10.4 (author check, not a research-register row) | TST-…-20 (re-run on every `rich` bump) |
| A-5 | Local synchronous log writes cost ≤ 100 µs and do not violate the 25 ms p95 lateness budget at 50 probes/s | TST-RG-P03-005-23 with logging enabled |
| A-6 | `faulthandler` output contains no values (frames only) | crash-runner test in TST-…-14 (SIGSEGV simulation via `faulthandler._sigsegv` on Linux) |
| A-7 | `Secret.reveal_bytes()` inside the redactor is acceptable: forms live in memory for the process lifetime | accepted residual (memory scraping is out of the threat model, RU-12) |
| A-8 | Operators never need `sub` redacted by default because identities are synthetic (SCR-05) | `drop_sub` provided; review in RG-P11-002 |
| A-9 | Windows console `PermissionError` on rotation is the only rotation hazard (antivirus scanners/other readers) | TST-…-19 Windows leg |
| A-10 | No plugin writes secrets via `print()`; plugins are trusted code (TM-22) | documented residual |

## 27. Maintainability, portability, and future extension requirements

* **Extension points:** `RedactionPolicy` additive keys/claims; `DET-10` vendor patterns (internal API now, plugin API after RG-P11-004); new `SecretKind`s need a fingerprint-class decision recorded in §8.2; new boundaries extend `Boundary` (enum values are logged in `RedactionReport`).
* **Detector maintenance:** each detector has a positive and negative corpus file; adding a detector requires entries in both and a benchmark row; detector ids are never reused.
* **Versioning:** `SCH-LOGREC` follows RG-P03-002 rules (additive minor); marker grammar is part of the evidence format (changes need a CONTRACT-CHANGELOG entry).
* **Upgrade hazards:** `rich`, `logging` internals (`LogRecord` attributes), Python regex engine changes — covered by tests named in §26.
* **Reuse:** `Redactor`, detectors and sanitiser have no RevocationGap imports beyond `Secret`/`fingerprint_of` and can be used by any security tool; the logging wrappers depend only on stdlib `logging`.
* **Future:** out-of-process log shipping (OTLP) must send `SCH-LOGREC` lines that already passed the gate; a listener-thread variant must keep the invariants INV-1/INV-5 (redact before enqueue).
