---
id: RG-P03-003
title: "Configuration subsystem"
phase: "03"
package: app
module_ids: [MOD-APP-CONFIGURATION]
status: DRAFT
depends_on: [RG-P03-002]
requirements: [FR-CLI-006, FR-OPS-007, FR-SEC-005, FR-SEC-001, FR-SEC-008, FR-SEC-009, FR-SEC-012, FR-SEC-014, FR-EVD-007, NFR-PLAT-002, NFR-REL-002, NFR-MNT-002]
interfaces_defined: [IF-CFG-LOADER, IF-CFG-REGISTRY]
interfaces_used: [IF-CORE-SERIAL, IF-CORE-ERR, IF-CORE-LOG, IF-CORE-AIO, IF-CORE-CLOCK]
schemas_defined: [SCH-CONFIG]
schemathesis_touchpoints: []
---

# RG-P03-003 — Configuration subsystem

> Scope: package `revocationgap.config` — parse (TOML syntax), layer (defaults < preset < workspace file < environment < CLI), validate (types, ranges, unknown keys, cross-field, cross-section, scope-aware), report (effective configuration with per-field provenance), reload (atomic), and the **section registry** through which every other element contributes its own validated sub-model. The scope document (`scope.toml`) is a separate document owned by RG-P11-002; this spec defines only how its path and digest are handled and where the "no network action without a validated scope" gate hooks in.

## 1. Module identifier and name

| Item | Value |
|---|---|
| Element | RG-P03-003 — Configuration subsystem |
| Module id | `MOD-APP-CONFIGURATION` |
| Package | `revocationgap.config`: `parse.py` (TOML + key index), `layers.py`, `envmap.py`, `clilayer.py`, `registry.py`, `models.py` (root + `[workspace]`), `normalize.py` (path/URL/duration/size), `validate.py`, `report.py`, `service.py` (reload), `scopehook.py`, `profiles.py`, `template.py` |
| Interfaces owned | `IF-CFG-LOADER` (`ConfigLoader`, `ConfigService`, `EffectiveConfig`, `ConfigIssue`); **new** `IF-CFG-REGISTRY` (`ConfigSectionRegistry`, `ConfigSection`, validator hooks) |
| Schemas owned | `SCH-CONFIG` (`config_document` = JSON Schema of `revocationgap.toml`; `effective_config_report`) |
| Consumers | RG-P03-010 (composition root), RG-P10-001/-002 (CLI, `rg config show/validate`, `rg init`), RG-P10-004 (GUI reload), RG-P11-002 (scope hooks, URL normaliser), every element registering a section |

## 2. Phase and requirement references

| Requirement | Realised by |
|---|---|
| FR-CLI-006 | layered precedence, provenance report (`rg config show`), unknown keys rejected (§10, §12.1) |
| FR-OPS-007 | parse stage separate from validation stage; all errors reported together with paths, stable codes and suggestions (§9, §10.4) |
| FR-SEC-005 | inline secrets rejected; only `secret:` handle syntax accepted (rules K12/K13) |
| FR-SEC-001 | scope path/digest handling and the validated-scope gate hook points (§10.7); no scope-free mode |
| FR-SEC-008 | `probe.verify_tls=false` is accepted only as a recorded *relaxation* and is scope-checked (S4) |
| FR-SEC-009 | `[limits]` section (body, header, document, queue, quota limits) with ranges |
| FR-SEC-012 | `[plugins].allow` allow-list section skeleton and duplicate/format validation |
| FR-SEC-014 | safe defaults catalogue; every deviation from a safety default is listed in `relaxations` |
| FR-EVD-007 | `config_digest` (canonical, workspace-relative) for the run manifest; effective configuration snapshot |
| NFR-PLAT-002 | path, URL, line-ending, encoding and long-path rules (§20) |
| NFR-REL-002 | deterministic merge/digest; no environment reads outside the loader |
| NFR-MNT-002 | typed API |

Threats: **TM-14** (safe parser only — `tomllib`; no YAML, pickle, `eval`, variable interpolation; CR/LF and control characters rejected in strings that become headers/identifiers), **TM-07** (no secrets in files, env values or flags), **TM-02** (operator configuration is the only source of base URLs; schema-provided URLs are not configuration), **TM-06** (scope digest pin), **TM-17/TM-21** (GUI and receiver binds default to loopback; relaxation needs explicit fields), **TM-22** (plugin allow-list shape), **TM-29/TM-34/TM-10** (limits). Workflows: WF-02 (validation/dry run), WF-12 (plugins), all CLI flows.

## 3. Purpose and user/security value

Configuration is the second place (after probes) where a mistake changes what the tool does to a real tenant. This subsystem makes mistakes *visible and attributable*: every effective value has a layer and a source line, unknown or misspelled keys fail instead of silently falling back to defaults, secrets cannot be pasted into files that end up in git, relaxations of safe defaults are enumerated for the audit log, and a run records the exact configuration digest it used. Splitting parse from validate keeps syntax errors (which have line/column) distinct from semantic errors (which have field paths and codes), and lets `rg config validate` run in CI without network access or scope knowledge.

## 4. Explicit responsibilities

- **RESP-1** Locate and read `revocationgap.toml` (and the optional explicit `--config`), enforce size/encoding limits, parse with `tomllib`, convert parse failures into `ConfigIssue`s with line/column.
- **RESP-2** Implement layered precedence `defaults < preset < file < file-profile < env < cli`, deep-merge tables, replace lists, and record a `FieldProvenance` for every leaf.
- **RESP-3** Map environment variables (`RG_<SECTION>_<FIELD>`, keyed-table form `RG_<SECTION>__<KEY>__<FIELD>`) and CLI overrides (dotted paths) onto the schema; reject unknown names.
- **RESP-4** Validate with pydantic section models (frozen, `extra="forbid"`), cross-field validators, cross-section validators and scope-aware validators; collect all issues.
- **RESP-5** Define the section registry (`IF-CFG-REGISTRY`) and the catalogue of the **whole product's configuration surface** (§8), fully for `[workspace]` and as owned skeletons for the other sections.
- **RESP-6** Normalise values: durations, byte sizes, paths (Windows/POSIX), URLs; reject ambiguous forms.
- **RESP-7** Reject inline secrets and enforce handle syntax (`SecretHandle` of RG-P03-002; shape detectors).
- **RESP-8** Produce the effective-configuration report with provenance and relaxations (`rg config show`) in text, JSON and TOML renderings, and the portable `config_digest`.
- **RESP-9** Provide atomic reload semantics (`ConfigService`) with reload classes and an atomic file writer for generated configuration.
- **RESP-10** Provide scope-document handling: path resolution, digest computation, pin check, `ScopeHook` protocol and the gate hook points.
- **RESP-11** Define the issue/error format (codes, paths, suggestions, sources) and the exit-kind hook.
- **RESP-12** Define built-in profiles/presets and the profile overlay mechanism.

## 5. Out-of-scope responsibilities

| Excluded | Owner |
|---|---|
| Contents and validation of `scope.toml`; `ScopeEnforcer`; the validated-scope object | RG-P11-002 (this spec specifies the hook, not the document) |
| Field definitions for non-`[workspace]` sections beyond the skeletons of §8 | probe → RG-P05-001; schedule → RG-P05-008; store → RG-P03-008; evidence → RG-P08-001/RG-P11-003; plugins → RG-P03-009; engine → RG-P03-010; providers → RG-P04-001/-007…-010; targets → RG-P05-001; policy → RG-P02-009/RG-P08-008; gui → RG-P10-004; cli → RG-P10-001; report → RG-P08-011; lab → RG-P09-001 |
| `[logging]` fields and `[engine.cancel]`/`[engine.executors]`/`[engine.loop_lag]` fields | RG-P03-004 / RG-P03-005 (summarised in §8) |
| Resolving `secret:` handles | RG-P11-001 |
| CLI flag parsing (click), command-specific flags, exit-code integers, `rg init` UX | RG-P10-001 / RG-P10-002 |
| Workspace creation, lock, `.rg` layout, file permission helper | RG-P03-008 / RG-P11-006 |
| Config-file migrations between schema majors | RG-P11-006 (uses `Migration` of RG-P03-002) |
| Editing existing configuration files programmatically (`rg config set`) | not provided in v1 (comment preservation cannot be guaranteed with `tomllib`) |

## 6. Dependencies and prerequisites

* Specs: RG-P03-002 (`Model`, `Document`, `Int64`, `Label`, `SecretHandle`, `Sha256Digest`, `canonical_json`, `digest`, shape detectors, `SchemaRegistry` for `SCH-CONFIG`). Interface-only use of `IF-CORE-ERR`, `IF-CORE-LOG` (`Redactor`, `sanitize_for_terminal` for display), `IF-CORE-AIO` (`ExecutorSet`, `shield_commit` in the atomic writer) and `IF-CORE-CLOCK`.
* Stdlib: `tomllib` (3.11+), `pathlib`, `os`, `ipaddress`, `urllib.parse`, `difflib`, `hashlib`, `re`, `unicodedata`; `codecs` for IDNA. Third-party: `pydantic` (via rg_core). `platformdirs` is **not** used by this module (workspace discovery is by walking up from the CWD, §10.1); RG-P10-002 may use it for the *user-level* template directory.
* Environment: read via `LoadRequest.env` (explicit mapping); `LoadRequest.from_process()` is the only code that touches `os.environ`/`Path.cwd()`.

## 7. External and internal interfaces

### 7.1 Loader and service (`IF-CFG-LOADER`)

```python
@dataclass(frozen=True)
class LoadRequest:
    cwd: Path
    workspace_dir: Path | None = None              # --workspace; None → discover (§10.1)
    config_file: Path | None = None                # --config; overrides discovery of revocationgap.toml
    profile: str | None = None                     # --profile
    env: Mapping[str, str] = field(default_factory=dict)
    cli_overrides: Mapping[str, CliValue] = field(default_factory=dict)   # dotted path → value; produced by the CLI flag table (§8.6)
    platform: Literal["linux", "windows", "macos"] = ...
    @classmethod
    def from_process(cls, *, workspace_dir=None, config_file=None, profile=None, cli_overrides=None) -> "LoadRequest": ...   # reads os.environ, Path.cwd(), sys.platform

class ConfigLoader:                                # sync; blocking file reads (call via run_blocking("store", …) from async code); thread-safe (stateless)
    def __init__(self, registry: ConfigSectionRegistry) -> None
    def parse(self, req: LoadRequest) -> ParsedConfig                                 # stage 1: syntax only (RESP-1); never raises for user errors
    def validate(self, parsed: ParsedConfig, *, scope_hook: ScopeHook | None = None) -> LoadResult   # stage 2: RESP-2…RESP-8
    def load(self, req: LoadRequest, *, scope_hook: ScopeHook | None = None) -> LoadResult          # parse + validate

class LoadResult(NamedTuple):
    config: EffectiveConfig | None                 # None if any error-severity issue
    issues: tuple[ConfigIssue, ...]                # errors and warnings, sorted (§10.4)
    @property ok(self) -> bool
    def require(self) -> "EffectiveConfig"        # raises ConfigLoadError (RgError, category CONFIG, code RGE-CONFIG-1020 family) carrying all issues

class EffectiveConfig(Model):                      # frozen; the validated product-wide configuration
    schema_version: Literal["1.0"]
    sections: Mapping[str, Model]                  # "workspace" → WorkspaceConfig, … (typed attribute access via properties generated per registered section)
    provenance: ProvenanceMap                      # excluded from digest
    relaxations: tuple[Relaxation, ...]
    workspace_root: str; files: tuple[ConfigFileRef, ...]; profile: str | None
    scope: ScopeReference
    @property config_digest(self) -> Sha256Digest   # digest(portable JSON of sections, "rg.config.v1")
    def report(self) -> "EffectiveConfigReport"

class ConfigService:                               # long-lived holder for GUI/API servers; CLI uses ConfigLoader directly
    def __init__(self, loader: ConfigLoader, req_factory: Callable[[], LoadRequest], *, scope_hook: ScopeHook | None) -> None
    @property current(self) -> EffectiveConfig     # atomic read; callers hold the returned object for the duration of an operation
    async def reload(self, executors: ExecutorSet) -> "ReloadReport"       # §10.8
    def subscribe_live(self, path_prefix: str, cb: Callable[[str, object], None]) -> None
    def require_validated_scope(self) -> "ValidatedScopeRef"                # raises ScopeError RGE-SCOPE-1100
async def write_config_atomic(path: Path, data: bytes, *, executors: ExecutorSet, clock: Clock) -> None   # §10.9
```

### 7.2 Registry (`IF-CFG-REGISTRY`)

```python
class ReloadClass(str, Enum): live="live"; next_run="next_run"; restart="restart"
class ConfigSection(Model):                        # base of every section model (frozen, extra=forbid, strict)
    ...
def meta(*, reload: ReloadClass = ReloadClass.next_run, safety_default: bool = False, secret_handle: bool = False, doc: str = "") -> FieldMeta     # used inside Annotated[...] on every field

class SectionSpec(NamedTuple):
    name: str                         # "probe", "engine.executors", "providers"
    model: type[ConfigSection]
    owner: str                        # element id
    keyed: bool = False               # True for providers/targets/plugins.config: table of named entries
    discriminator: str | None = None  # for keyed sections with variants: field name selecting the variant model (e.g. "adapter")
class ConfigSectionRegistry:                       # explicit object built by the composition root; no import-time registration
    def register_section(self, spec: SectionSpec) -> None
    def register_variant(self, section: str, tag: str, model: type[ConfigSection], *, owner: str) -> None     # e.g. ("providers", "idp.keycloak", KeycloakProviderConfig)
    def add_cross_validator(self, name: str, fn: CrossValidator, *, owner: str) -> None
    def add_scope_validator(self, name: str, fn: ScopeAwareValidator, *, owner: str) -> None
    def add_preset(self, profile: str, overrides: Mapping[str, object], *, owner: str) -> None
    def freeze(self) -> None
    def build_root_model(self) -> type[Model]
    def env_table(self) -> Mapping[str, str]       # ENV_NAME → dotted path (fixed schema only)
    def describe(self) -> Sequence[FieldDescriptor]   # generates §8 catalogue + `rg config schema`; used by the doc-sync test
    def export_json_schema(self) -> dict[str, Any]  # `config_document` input-form schema (§8.1); consumed by tools/rgschemas.py via export_schemas(extra=…)
CrossValidator = Callable[[EffectiveConfigDraft], Sequence[ConfigIssue]]                 # pure, sync
ScopeAwareValidator = Callable[[EffectiveConfigDraft, ScopeView], Sequence[ConfigIssue]]  # pure, sync; ScopeView is a Protocol of RG-P11-002
```

Plugins register sections and variants through RG-P03-009 **before** `freeze()`; a plugin's section lives at `[plugins.config.<plugin_id>]` and is validated by the model its manifest declares.

### 7.3 Issues and errors

```python
class IssueSource(Model): layer: Literal["default","preset","file","file_profile","env","cli"]; file: ShortText | None; line: Count | None; column: Count | None
                          approximate: bool = False; env_var: Label | None = None; flag: Label | None = None
class ConfigIssue(Model): code: str; severity: Literal["error","warning"]; path: ShortText; message: ShortText; suggestion: ShortText | None
                          source: IssueSource | None; details: dict[Label, DetailValue]
class ConfigLoadError(ConfigError): issues: tuple[ConfigIssue, ...]      # RgError; exit_kind → config_error; scope issues keep category SCOPE
def render_issues(issues: Sequence[ConfigIssue], *, fmt: Literal["text","json"], color: bool = False) -> str
```

### 7.4 Scope hook (`scopehook.py`)

```python
class ScopeView(Protocol): ...                     # defined by RG-P11-002 (host/tenant/identity/action/rate queries)
class ScopeValidation(Model): ok: bool; digest: Sha256Digest | None; issues: tuple[ConfigIssue, ...]
class ValidatedScope:                              # opaque token; constructible only by RG-P11-002's validator (private constructor token)
    digest: Sha256Digest; view: ScopeView
class ScopeHook(Protocol):                         # implemented by RG-P11-002; sync
    def validate(self, path: Path, raw: bytes, parsed: Mapping[str, object], *, now: TimeInstant) -> tuple[ScopeValidation, "ValidatedScope | None"]
class ScopeReference(Model): path: ShortText; digest: Sha256Digest | None; pinned_digest: Sha256Digest | None; status: Literal["unchecked","missing","invalid","valid"]
def scope_file_digest(parsed: Mapping[str, object]) -> Sha256Digest        # digest(toml_to_json_value(parsed), "rg.scope.v1")
```

### 7.5 Error codes (block 1000–1199; owner RG-P03-003)

| Code | Name | Cat | Meaning |
|---|---|---|---|
| `RGE-CONFIG-1001` | TOML_SYNTAX | CONFIG | invalid TOML (line/column, `approximate` when only "end of document" is known) |
| `RGE-CONFIG-1002` | CONFIG_FILE_NOT_FOUND | CONFIG | explicit `--config`/`RG_CONFIG` path missing (a missing *discovered* file is not an error) |
| `RGE-CONFIG-1003` | CONFIG_FILE_UNREADABLE | CONFIG | permission error, directory, device |
| `RGE-CONFIG-1004` | CONFIG_ENCODING_OR_SIZE | CONFIG | not UTF-8, NUL byte, or > 1 MiB |
| `RGE-CONFIG-1005` | SCHEMA_VERSION_MISSING | CONFIG | warning: assumed `"1.0"` |
| `RGE-CONFIG-1006` | SCHEMA_VERSION_UNSUPPORTED | CONFIG | newer major/minor than this build |
| `RGE-CONFIG-1007` | TOML_LOCAL_DATETIME | CONFIG | local date/time without offset (ambiguous) |
| `RGE-CONFIG-1020` | VALUE_INVALID | CONFIG | wrong type or failed validator (`details.type`) |
| `RGE-CONFIG-1021` | UNKNOWN_KEY | CONFIG | key/section not in the schema (with suggestion) |
| `RGE-CONFIG-1022` | REQUIRED_MISSING | CONFIG | required field absent |
| `RGE-CONFIG-1023` | OUT_OF_RANGE | CONFIG | numeric/duration/size outside range |
| `RGE-CONFIG-1024` | ENUM_INVALID | CONFIG | not an allowed value |
| `RGE-CONFIG-1025` | DURATION_INVALID | CONFIG | duration grammar |
| `RGE-CONFIG-1026` | BYTESIZE_INVALID | CONFIG | size grammar |
| `RGE-CONFIG-1027` | PATH_INVALID | CONFIG | NUL, `~`, reserved Windows name, trailing dot/space, escapes workspace, UNC where local FS required |
| `RGE-CONFIG-1028` | URL_INVALID | CONFIG | scheme, userinfo, fragment/query, ambiguous numeric host, control characters |
| `RGE-CONFIG-1029` | SECRET_HANDLE_INVALID | CONFIG | field requires `secret:<resolver>:<name>` |
| `RGE-CONFIG-1030` | INLINE_SECRET | CONFIG | secret-shaped value in a configuration source (never echoed) |
| `RGE-CONFIG-1032` | VARIANT_UNKNOWN | CONFIG | keyed-section discriminator names an unregistered variant |
| `RGE-CONFIG-1033` | CROSS_FIELD | CONFIG | rule X* violated (`details.rule`) |
| `RGE-CONFIG-1034` | CROSS_SECTION | CONFIG | dangling reference or incompatible sections |
| `RGE-CONFIG-1035` | SAFETY_RELAXED | CONFIG | warning: a safety default was relaxed (`details.path`) |
| `RGE-CONFIG-1036` | DEPRECATED_KEY | CONFIG | warning |
| `RGE-CONFIG-1037` | PROFILE_UNKNOWN | CONFIG | profile name not found in presets or file |
| `RGE-CONFIG-1060` | ENV_UNKNOWN_VARIABLE | CONFIG | `RG_<KNOWN-SECTION>_…` variable matching no field |
| `RGE-CONFIG-1061` | ENV_EMPTY_IGNORED | CONFIG | warning |
| `RGE-CONFIG-1062` | KEY_AMBIGUOUS | CONFIG | two keyed-table keys equal after normalisation (`kc-lab` / `kc_lab`) |
| `RGE-CONFIG-1063` | ENV_CANNOT_CREATE_ENTRY | CONFIG | env override addresses a keyed entry not defined in an earlier layer |
| `RGE-CONFIG-1064` | CLI_OVERRIDE_INVALID | CONFIG | unknown or non-overridable path |
| `RGE-CONFIG-1104` | SCOPE_AWARE_VIOLATION | CONFIG | scope-aware rule S* violated (`details.rule`) |
| `RGE-CONFIG-1120` | RELOAD_REJECTED | CONFIG | new configuration invalid; previous retained |
| `RGE-SCOPE-1100` | SCOPE_NOT_VALIDATED | SCOPE | a network-capable operation was requested without a validated scope |
| `RGE-SCOPE-1101` | SCOPE_FILE_MISSING | SCOPE | scope file not found at the configured path |
| `RGE-SCOPE-1102` | SCOPE_DIGEST_MISMATCH | SCOPE | `workspace.scope_digest` pin differs from the file's digest |
| `RGE-SCOPE-1103` | SCOPE_CHANGED | SCOPE | scope digest changed since validation (re-verification, TM-06) |
| `RGE-STORE-1141` | CONFIG_WRITE_FAILED | STORE | atomic writer failed after retries |
| `RGE-CONFIG-1140` | CONFIG_EXISTS | CONFIG | generated config would overwrite an existing file |

## 8. Data structures and schemas

### 8.1 Root document (`config_document` 1.0)

A `revocationgap.toml` is a TOML document whose top-level keys are `schema_version`, the sections below, and the optional `[profile.<name>]` overlay tables. Complete example:

```toml
schema_version = "1.0"

[workspace]
name = "acme-staging"
profile = "ci"
scope_digest = "sha256:0b8e1f3a5d6c7e9f0a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f6071"

[probe]
concurrency = 32
verify_tls = true

[schedule]
dense_interval = "1s"
horizon = "15m"

[providers.kc-lab]
adapter = "idp.keycloak"
issuer = "http://127.0.0.1:8080/realms/rg-lab"
admin_credential = "secret:env:RG_KC_ADMIN_PASSWORD"

[targets.demo-api]
kind = "http_api"
base_url = "http://127.0.0.1:9000"
provider = "kc-lab"
validation_mode = "introspection"

[profile.ci.cli]
non_interactive = true
output = "json"
```

The JSON Schema `config_document` (`schemas/config_document/1.0.schema.json`, built-in sections only) describes the **input** form for editors and CI linters: it is generated in *validation* mode by `ConfigSectionRegistry.export_json_schema()` with string-pattern overrides for `Duration`, `ByteSize`, `PathValue`, `UrlValue` (so `"30s"` is valid and `30` is not), it is golden-tested like every other schema (RG-P03-002 §10.5), and it is not part of the serialization-mode export of `SchemaRegistry` because section models are not persisted `Document`s.

### 8.2 Value types (shared by all sections)

| Type | TOML form | Parsed to | Rules |
|---|---|---|---|
| `Duration` | string `"<n><unit>…"`, units `ns us ms s m h d`, decimal allowed, concatenation allowed (`"1h30m"`); **bare numbers rejected** (`RGE-CONFIG-1025`, suggestion "write \"30s\"") | `int` nanoseconds (`Int64`; displayed as exact units) | no sub-nanosecond results; range per field |
| `ByteSize` | integer (bytes) or string `"<n>[.<n>]<B|KiB|MiB|GiB>"`; `KB/MB/GB` rejected with suggestion (IEC units only) | `int` bytes | range per field |
| `PathValue` | string | normalised absolute path **string** in OS-native form (internal `\\?\` form for Windows long paths); typed accessors return `pathlib.Path`; serialised workspace-relative with `/` when inside the workspace, else absolute with `/` | §12.5 |
| `UrlValue` | string | normalised URL string | §12.4 |
| `SecretHandle` | string `secret:<resolver>:<name>` | validated string (never resolved here) | rules K12/K13 |
| `Label`, `Slug`, `ShortText` | string | per RG-P03-002 | |
| `Enum` | string | exact lower-case value | `RGE-CONFIG-1024` lists allowed values |
| `Bool` | TOML bool; env `true/false/1/0` (case-insensitive) | bool | |
| `Int`, `Float` | TOML number | bounded `SafeInt`/finite float | no TOML floats for integer fields |
| `list[T]` | TOML array; env comma-separated | tuple | replaced, never appended, across layers |

### 8.3 Provenance and report structures

| Structure | Fields |
|---|---|
| `FieldProvenance` | `path`, `layer` ∈ {default, preset, file, file_profile, env, cli}, `file`, `line`, `column`, `approximate`, `env_var`, `flag` |
| `Relaxation` | `path`, `value` (display), `default` (display), `rule` (why it is a safety default) |
| `ConfigFileRef` | `path`, `sha256` (plain hash of file bytes), `size` |
| `EffectiveConfigReport` (`SCH-CONFIG`, document `effective_config_report` 1.0) | `schema_version`, `config_digest`, `profile`, `workspace_root`, `files[]`, `env_used[]` (names only), `entries[]` (`path`, `value`, `type`, `layer`, `source`, `default`, `relaxed`, `reload`), `relaxations[]`, `scope: ScopeReference`, `issues[]` |

Example fragment of a text rendering (`rg config show --provenance`):

```
workspace.data_dir       = ".rg"        [default]
probe.concurrency        = 32           [file revocationgap.toml:7]
probe.verify_tls         = false        [env RG_PROBE_VERIFY_TLS]   ! safety default relaxed
schedule.horizon         = "15m"        [file revocationgap.toml:12]
cli.output               = "json"       [file revocationgap.toml:24 (profile ci)]
engine.seed              = 1234         [cli --seed]
scope: scope.toml  status=unchecked  pinned=sha256:0b8e…6071
config_digest: sha256:7c1f…a90e
```

### 8.4 Section catalogue (whole product)

Ownership key: **full** = this element defines every field; **skeleton** = names, types and *proposed* defaults/ranges are listed so cross-validators and docs can be written now; the owning element finalises values in its own spec and any change is a CONTRACT-CHANGELOG entry once that owner's spec is COMPLETE. Env var = `RG_` + dotted path with `.`→`_`, upper-case; keyed sections use the double-underscore form (§12.2).

| Section | Owner (status) | Registered by | Keyed | Purpose |
|---|---|---|---|---|
| `[workspace]` | RG-P03-003 (**full**, §8.5) | `revocationgap.config.models` | no | workspace identity, data/scope/scenario/report locations, active profile, scope pin |
| `[engine]` (+ `engine.cancel`, `engine.executors.{probe,idp,store}`, `engine.loop_lag`) | RG-P03-010 (skeleton, §8.6); sub-sections RG-P03-005 (**full there**, summarised) | engine; `rg_core.aio` | no | clock kind, seed, settle, cancel budgets, executor sizing |
| `[probe]` | RG-P05-001 (skeleton, §8.7) | `rg_probe` | no | probe concurrency, timeouts, TLS, identification |
| `[schedule]` | RG-P05-008 (skeleton, §8.8) | `rg_probe.schedule` | no | post-revocation schedule defaults, horizon, confirmation tail |
| `[limits]` | cross-cutting; each field owned by the element named in §8.9 (skeleton) | each owner | no | resource limits on untrusted input and run size |
| `[store]` | RG-P03-008 (skeleton, §8.10) | store | no | SQLite durability/locking |
| `[evidence]` | RG-P08-001 / RG-P11-003 (skeleton, §8.11) | evidence, encryption | no | capture, encryption, retention |
| `[logging]` (+ `logging.console`, `logging.file`, `logging.redaction`) | RG-P03-004 (**full there**, summarised) | `rg_core.logging` | no | levels, sinks, redaction policy |
| `[gui]` | RG-P10-004 (skeleton, §8.12) | gui | no | local GUI/API bind, token, origins |
| `[plugins]` (+ `plugins.config.<id>`) | RG-P03-009 (skeleton, §8.13) | plugin loader | `config` keyed | allow-list and per-plugin config |
| `[providers.<name>]` | RG-P04-001 (common, skeleton) + adapters RG-P04-007…-010 (variants) | adapters | **keyed**, discriminator `adapter` | IdP instances |
| `[targets.<name>]` | RG-P05-001 / RG-P11-002 (skeleton, §8.14) | probe/scope | **keyed** | services under test |
| `[policy]` | RG-P02-009 / RG-P08-008 (skeleton, §8.15) | classification | no | policy profiles and tolerances |
| `[cli]` | RG-P10-001 (skeleton, §8.16) | cli | no | non-interactive, output format, colour |
| `[report]` | RG-P08-011 (skeleton) | report | no | formats and options |
| `[lab]` | RG-P09-001 (skeleton) | lab | no | lab mode and assets |

### 8.5 `[workspace]` — **full** (owner RG-P03-003)

| Field | Type | Default | Range / rule | Env | Reload | Notes |
|---|---|---|---|---|---|---|
| `name` | `Label` | basename of workspace directory (sanitised) | `^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$` | `RG_WORKSPACE_NAME` | next_run | shown in reports |
| `profile` | `Label \| None` | `None` | name of a preset or `[profile.<name>]` | `RG_PROFILE` (the one non-derived env name; no `RG_WORKSPACE_PROFILE` exists) | restart | resolution order: CLI `--profile` > env `RG_PROFILE` > this field; read from the file's base tables only |
| `data_dir` | `PathValue` | `.rg` | inside workspace unless `allow_external_data_dir`; not UNC | `RG_WORKSPACE_DATA_DIR` | restart | holds store, blobs, audit log, logs, lock |
| `allow_external_data_dir` | bool | `false` | safety default (relaxation when true) | `RG_WORKSPACE_ALLOW_EXTERNAL_DATA_DIR` | restart | |
| `scope_file` | `PathValue` | `scope.toml` | must be a regular file at validation time (`missing` otherwise) | `RG_WORKSPACE_SCOPE_FILE` | next_run | the document is RG-P11-002's |
| `scope_digest` | `Sha256Digest \| None` | `None` | `sha256:<64 hex>` | `RG_WORKSPACE_SCOPE_DIGEST` | next_run | pin (TM-06); mismatch → `RGE-SCOPE-1102` |
| `scenarios_dir` | `PathValue` | `scenarios` | no UNC restriction | `RG_WORKSPACE_SCENARIOS_DIR` | next_run | |
| `reports_dir` | `PathValue` | `reports` | | `RG_WORKSPACE_REPORTS_DIR` | next_run | |

Global (non-section) inputs: `RG_CONFIG` (path of the config file; same as `--config`), `RG_PROFILE` (also the env name of `workspace.profile`), `RG_WORKSPACE` (workspace directory; same as `--workspace`). They are never persisted in the effective document.

### 8.6 `[engine]` (owner RG-P03-010; skeleton) and sub-sections

| Field | Type | Default | Range | Env | Owner of final value |
|---|---|---|---|---|---|
| `engine.clock` | enum `system`/`virtual` | `system` | `virtual` only with `lab.mode=virtual` (X1) | `RG_ENGINE_CLOCK` | RG-P03-010 |
| `engine.seed` | `Int64 \| None` | `None` (random per run, recorded in manifest) | 0 … 2⁶³−1 | `RG_ENGINE_SEED` | RG-P03-010 |
| `engine.settle` | `Duration \| None` | `None` (adapter default) | 0s–10m | `RG_ENGINE_SETTLE` | RG-P03-010 / adapters (≥ 1 s floor where required, FR-EXP-005) |
| `engine.cancel.{probe_stop,drain,cleanup,commit_grace}` | `Duration` | `1s`, `5s`, `120s`, `5s` | see RG-P03-005 §18 | `RG_ENGINE_CANCEL_<NAME>` | RG-P03-005 |
| `engine.executors.{probe,idp,store}.{max_workers,queue_capacity,saturation_timeout}` | int, int, `Duration` | probe 64/256/`2s`; idp 8/64/`30s`; store 1/1024/`none` | see RG-P03-005 §18 | `RG_ENGINE_EXECUTORS_<NAME>_<FIELD>` | RG-P03-005 |
| `engine.loop_lag.{interval,warn}` | `Duration` | `100ms`, `100ms` | 10ms–10s / 1ms–10s | `RG_ENGINE_LOOP_LAG_<FIELD>` | RG-P03-005 |

### 8.7 `[probe]` (owner RG-P05-001; skeleton, proposed values)

| Field | Type | Default | Range | Env | Notes |
|---|---|---|---|---|---|
| `concurrency` | int | 20 | 1 … `min(limits.max_concurrent_probes, engine.executors.probe.max_workers)` (X2) | `RG_PROBE_CONCURRENCY` | FR-PRB-017 default 20 |
| `connect_timeout` | `Duration` | `5s` | 100ms–5m | `RG_PROBE_CONNECT_TIMEOUT` | |
| `read_timeout` | `Duration` | `15s` | 100ms–10m | `RG_PROBE_READ_TIMEOUT` | |
| `total_timeout` | `Duration` | `30s` | 100ms–1h; ≥ both above (X3) | `RG_PROBE_TOTAL_TIMEOUT` | |
| `verify_tls` | bool | `true` | safety default; `false` ⇒ relaxation + scope rule S4 | `RG_PROBE_VERIFY_TLS` | FR-SEC-008 |
| `ca_bundle` | `PathValue \| None` | `None` | file must exist at run time | `RG_PROBE_CA_BUNDLE` | |
| `fresh_connection` | bool | `false` | | `RG_PROBE_FRESH_CONNECTION` | CallPolicy |
| `user_agent_suffix` | `ShortText` | `""` | no control characters (TM-14) | `RG_PROBE_USER_AGENT_SUFFIX` | tool identification RU-05 is always sent |

No field controls redirect following: redirects are never followed (TM-01), so there is nothing to configure.

### 8.8 `[schedule]` (owner RG-P05-008; skeleton)

| Field | Type | Default | Range | Env |
|---|---|---|---|---|
| `dense_interval` | `Duration` | `1s` | 100ms–5m (≤ `max_interval`, X4) | `RG_SCHEDULE_DENSE_INTERVAL` |
| `backoff_factor` | float | 2.0 | 1.0–10.0 | `RG_SCHEDULE_BACKOFF_FACTOR` |
| `max_interval` | `Duration` | `30s` | ≥ `dense_interval` | `RG_SCHEDULE_MAX_INTERVAL` |
| `horizon` | `Duration` | `10m` | 10s–24h; ≥ `confirm_n × dense_interval` (X4) | `RG_SCHEDULE_HORIZON` |
| `confirm_n` | int | 3 (`N_confirm`, DATA-MODEL §4) | 1–50 | `RG_SCHEDULE_CONFIRM_N` |
| `confirm_span` | `Duration \| None` | `None` (= max(3 × probe interval, 10 s), `T_confirm`) | 1s–1h | `RG_SCHEDULE_CONFIRM_SPAN` |

### 8.9 `[limits]` (cross-cutting; skeleton; proposals pending RG-P12-004 benchmarks per OQ-TM-04)

| Field | Type | Default | Range | Env | Owner |
|---|---|---|---|---|---|
| `max_concurrent_probes` | int | 50 | 1–512 | `RG_LIMITS_MAX_CONCURRENT_PROBES` | RG-P05-014 |
| `max_body_read_bytes` | `ByteSize` | `1MiB` | 1KiB–64MiB | `RG_LIMITS_MAX_BODY_READ_BYTES` | RG-P05-004 (TM-10) |
| `max_body_capture_bytes` | `ByteSize` | `64KiB` | 0–16MiB | `RG_LIMITS_MAX_BODY_CAPTURE_BYTES` | RG-P08-001 (NFR-PERF-007) |
| `max_header_bytes` / `max_header_count` | `ByteSize` / int | `32KiB` / 100 | 1KiB–1MiB / 10–1000 | `RG_LIMITS_MAX_HEADER_BYTES`, `RG_LIMITS_MAX_HEADER_COUNT` | RG-P05-004 |
| `max_decompression_ratio` | int | 20 | 1–1000 | `RG_LIMITS_MAX_DECOMPRESSION_RATIO` | RG-P05-004 |
| `max_api_description_bytes` / `max_api_description_depth` | `ByteSize` / int | `8MiB` / 64 | 1KiB–64MiB / 4–128 | `RG_LIMITS_MAX_API_DESCRIPTION_BYTES`, `…_DEPTH` | RG-P05-005 (TM-04) |
| `max_event_payload_bytes` | `ByteSize` | `256KiB` | 1KiB–16MiB | `RG_LIMITS_MAX_EVENT_PAYLOAD_BYTES` | RG-P04-011 |
| `max_document_bytes` | `ByteSize` | `16MiB` | 1KiB–64MiB | `RG_LIMITS_MAX_DOCUMENT_BYTES` | RG-P03-002 `ParseLimits.max_bytes` for imports |
| `queue_depth_default` | int | 1024 | 16–1 000 000 | `RG_LIMITS_QUEUE_DEPTH_DEFAULT` | RG-P03-007 |
| `evidence_quota_bytes` | `ByteSize` | `512MiB` | 1MiB–1TiB | `RG_LIMITS_EVIDENCE_QUOTA_BYTES` | RG-P03-008 (TM-34) |
| `max_experiment_duration` | `Duration` | `24h` | 1m–30d | `RG_LIMITS_MAX_EXPERIMENT_DURATION` | RG-P03-010 |

### 8.10–8.16 Remaining skeletons (proposed; owners finalise)

| Section / field | Type | Default | Range / rule | Env |
|---|---|---|---|---|
| `store.batch_commit_interval` | `Duration` | `250ms` | 10ms–250ms (NFR-REL-001) | `RG_STORE_BATCH_COMMIT_INTERVAL` |
| `store.busy_timeout` | `Duration` | `5s` | 0s–60s | `RG_STORE_BUSY_TIMEOUT` |
| `store.lock_wait` | `Duration` | `0s` | 0s–10m (FR-EXP-010) | `RG_STORE_LOCK_WAIT` |
| `evidence.capture_bodies` | bool | `true` | | `RG_EVIDENCE_CAPTURE_BODIES` |
| `evidence.raw_capture` | bool | `false` | safety default; requires encryption (X10) and a scope flag | `RG_EVIDENCE_RAW_CAPTURE` |
| `evidence.encryption` | enum `off`/`aes256gcm` | `off` | `aes256gcm` requires `key_source` (X9) | `RG_EVIDENCE_ENCRYPTION` |
| `evidence.key_source` | `SecretHandle \| None` | `None` | handle only | `RG_EVIDENCE_KEY_SOURCE` |
| `evidence.retention_days` | int \| None | `None` | 1–36500 | `RG_EVIDENCE_RETENTION_DAYS` |
| `gui.bind` | string host | `127.0.0.1` | non-loopback requires `allow_non_loopback` + TLS (X7, TM-17) | `RG_GUI_BIND` |
| `gui.port` | int | `0` (ephemeral, printed at start) | 0 or 1024–65535 (NFR-PLAT-003) | `RG_GUI_PORT` |
| `gui.allow_non_loopback` | bool | `false` | safety default | `RG_GUI_ALLOW_NON_LOOPBACK` |
| `gui.tls_cert` / `gui.tls_key` | `PathValue \| None` | `None` | both or neither | `RG_GUI_TLS_CERT`, `RG_GUI_TLS_KEY` |
| `gui.token_ttl` | `Duration` | `8h` | 1m–7d | `RG_GUI_TOKEN_TTL` |
| `gui.sse_queue_size` | int | 256 | 16–65536 | `RG_GUI_SSE_QUEUE_SIZE` |
| `plugins.allow` | list of `{name: Label, version: ShortText, digest: Sha256Digest}` | `[]` | unique names (X13); never auto-discovered (TM-22) | not env-settable (structured) |
| `plugins.config.<id>` | variant table | — | model from plugin manifest | `RG_PLUGINS__CONFIG__<ID>__<FIELD>` |
| `providers.<name>.adapter` | `Slug` (discriminator) | required | registered variant (`RGE-CONFIG-1032`) | `RG_PROVIDERS__<NAME>__ADAPTER` |
| `providers.<name>.issuer` | `UrlValue` | required | | `RG_PROVIDERS__<NAME>__ISSUER` |
| `providers.<name>.tenant` | `ShortText \| None` | `None` | realm/tenant id read back at preflight (TM-05) | `…__TENANT` |
| `providers.<name>.admin_credential` | `SecretHandle \| None` | `None` | handle only | `…__ADMIN_CREDENTIAL` |
| `providers.<name>.timeout` | `Duration` | `30s` | 1s–10m | `…__TIMEOUT` |
| `targets.<name>.kind` | enum `http_api`/`graphql`/`websocket` | required | | `RG_TARGETS__<NAME>__KIND` |
| `targets.<name>.base_url` | `UrlValue` | required | scheme per kind (X6); no userinfo/query/fragment | `…__BASE_URL` |
| `targets.<name>.provider` | `Label \| None` | `None` | must name a `providers` entry (X5) | `…__PROVIDER` |
| `targets.<name>.validation_mode` | `ValidationMode` | `unknown` | enum of DATA-MODEL §3 | `…__VALIDATION_MODE` |
| `targets.<name>.description_source` | `PathValue \| UrlValue \| None` | `None` | OpenAPI/GraphQL document; fetched only through the scope-enforcing transport (TM-04) | `…__DESCRIPTION_SOURCE` |
| `policy.profiles` | list[`PolicyProfile`] | `["protocol"]` | ≥ 1 | `RG_POLICY_PROFILES` |
| `cli.non_interactive` | bool | `false` | | `RG_CLI_NON_INTERACTIVE` |
| `cli.output` | enum `text`/`json` | `text` | | `RG_CLI_OUTPUT` |
| `cli.color` | enum `auto`/`always`/`never` | `auto` | | `RG_CLI_COLOR` |
| `report.formats` | list[enum] | `["html","json"]` | ⊂ {html, markdown, json, sarif, junit} | `RG_REPORT_FORMATS` |
| `lab.mode` | enum `off`/`virtual`/`real` | `off` | | `RG_LAB_MODE` |

`[logging]`: `level=INFO`, `console.level=WARNING`, `console.format=text`, `file.enabled=true`, `file.path=<data_dir>/logs/rg.log`, `file.level=INFO`, `file.max_bytes=5MiB`, `file.backup_count=5`, `file.required=false`, `log_bodies=false`, `body_log_bytes=1KiB`, `redaction.{extra_sensitive_keys,extra_claim_allowlist,drop_sub,min_canary_length,max_text_bytes}` — full table with ranges in RG-P03-004 §18; there is no key that disables redaction.

### 8.17 Built-in presets (layer `preset`)

| Profile | Overrides | Intended use |
|---|---|---|
| `default` | none | interactive |
| `ci` | `cli.non_interactive=true`, `cli.output="json"`, `logging.console.format="json"`, `cli.color="never"` | pipelines (FR-CLI-007) |
| `lab` | `lab.mode="virtual"`, `engine.clock="virtual"`, `gui.port=0` | virtual-time laboratory |

Presets never touch safety-default fields. A `[profile.<name>]` table in the file overlays the same shape and wins over the file's base tables; it can also define new profile names.

## 9. Inputs, outputs, and validation rules

Parse stage (no schema knowledge): **P1** size ≤ 1 MiB (`RGE-CONFIG-1004`); **P2** valid UTF-8 without NUL; a single leading BOM is stripped and reported as a warning with code `RGE-CONFIG-1004` (`details.reason="bom_stripped"`); **P3** `tomllib` syntax (`RGE-CONFIG-1001`); **P4** no local (naive) date/time values (`RGE-CONFIG-1007`; offset datetimes are converted to UTC strings); **P5** `schema_version` present (warning `RGE-CONFIG-1005` if absent), grammar valid, `(major, minor) ≤ (1, 0)` (`RGE-CONFIG-1006`); **P6** top-level values other than `schema_version` are tables.

Validation stage:

| Rule | Check | Code |
|---|---|---|
| K1 | every key (any depth) exists in the registered model of its table; unknown → error with nearest-name suggestion | 1021 |
| K2 | keyed-section entry names match `^[a-z0-9][a-z0-9_-]{0,31}$`; two names equal after `-`→`_` normalisation are rejected | 1020 / 1062 |
| K3 | keyed-section discriminator names a registered variant | 1032 |
| K4 | required fields present | 1022 |
| K5 | types strict (no `"1"`→1 coercion; TOML float for an int field rejected) | 1020 |
| K6 | numeric/duration/size range per field | 1023 |
| K7 | enum membership (suggestion lists values) | 1024 |
| K8 | `Duration` grammar §8.2 | 1025 |
| K9 | `ByteSize` grammar §8.2 | 1026 |
| K10 | path rules §12.5 | 1027 |
| K11 | URL rules §12.4 | 1028 |
| K12 | fields declared `secret_handle` match the `SecretHandle` grammar | 1029 |
| K13 | **no string value in any layer (file, env, CLI) may have an inline-secret shape** (`find_secret_shape` of RG-P03-002: JWT, `Bearer`/`Basic` value, PEM private key, URL userinfo) and no field whose key matches `SECRET_KEY_NAME` may hold a non-handle value; the message names the path only, never the value | 1030 |
| K14 | strings that become headers, identifiers or log fields contain no CR/LF/control characters (TM-14) | 1020 |
| X1 | `engine.clock="virtual"` ⇒ `lab.mode="virtual"` | 1033 |
| X2 | `probe.concurrency ≤ limits.max_concurrent_probes` and `≤ engine.executors.probe.max_workers` | 1033 |
| X3 | `connect_timeout ≤ total_timeout` and `read_timeout ≤ total_timeout` | 1033 |
| X4 | `dense_interval ≤ max_interval`; `horizon ≥ confirm_n × dense_interval`; `confirm_span ≤ horizon` | 1033 |
| X5 | `targets.*.provider` ∈ `providers` keys | 1034 |
| X6 | `kind ∈ {http_api, graphql}` ⇒ scheme `http`/`https`; `kind="websocket"` ⇒ `ws`/`wss` | 1033 |
| X7 | non-loopback `gui.bind` ⇒ `allow_non_loopback=true` and both TLS paths set | 1033 |
| X8 | `logging.log_bodies=true` ⇒ `logging.level="DEBUG"` | 1033 |
| X9 | `evidence.encryption≠"off"` ⇒ `evidence.key_source` set | 1033 |
| X10 | `evidence.raw_capture=true` ⇒ `evidence.encryption≠"off"` | 1033 |
| X11 | any field marked `safety_default` whose value differs from its default is appended to `relaxations` and yields a warning | 1035 |
| X13 | `plugins.allow` names unique | 1033 |
| X14 | `engine.executors.store.max_workers == 1`, and `saturation_timeout="none"` only for `store` | 1033 |
| S1 | scope-aware: every `targets.*.base_url` origin is listed in the validated scope | 1104 |
| S2 | `probe.concurrency` and `limits.max_concurrent_probes` ≤ the scope's concurrency limit | 1104 |
| S3 | `schedule.horizon` and `limits.max_experiment_duration` ≤ the scope's maximum duration | 1104 |
| S4 | `probe.verify_tls=false` requires a per-host TLS-off entry in the scope | 1104 |
| S5 | `providers.*.tenant` ∈ scope tenants when the provider's adapter can mutate | 1104 |

Outputs: `LoadResult`, `EffectiveConfig`, `EffectiveConfigReport`, `ReloadReport`. `LoadResult.config is None` whenever an error-severity issue exists. Scope-aware rules S* run only when a `ScopeHook` was supplied and the scope validated; without it the result is *valid but not runnable* (`scope.status="unchecked"`), and `require_validated_scope()` raises `RGE-SCOPE-1100`.

## 10. Detailed execution behavior

### 10.1 Discovery (`parse`)
1. Determine workspace root: `workspace_dir` if given; else walk up from `cwd` (max 32 levels) to the first directory containing `revocationgap.toml`; none found → workspace root = `cwd` and no file layer (defaults only; `rg init` creates the file). 2. Config file path: `config_file` (must exist, else `RGE-CONFIG-1002`) else `<root>/revocationgap.toml` (absent is fine). 3. Read bytes once (≤ 1 MiB), compute `sha256`, strip one BOM, decode UTF-8, parse with `tomllib.loads`. 4. Build the key index (§12.6) for line numbers. 5. Convert TOML datetimes (P4). Output `ParsedConfig(files, tables, key_index, issues)`.
Timing/clock: none; file `mtime` is never used for semantics.

### 10.2 Layer assembly (`validate`, steps 1–3)
1. `defaults`: values from model defaults (not materialised as a dict; used as the base of the merge). 2. `preset`: `registry.presets[profile]` (profile resolution: CLI > `RG_PROFILE` > `workspace.profile` of the file base; unknown profile → `RGE-CONFIG-1037` unless a `[profile.<name>]` table exists). 3. `file`: file tables except `profile`. 4. `file_profile`: `[profile.<active>]` overlay. 5. `env`: `RG_*` variables mapped through `env_table()` (§12.2); keyed-entry variables processed in a second pass once `adapter`/`kind` values from earlier layers are known. 6. `cli`: `cli_overrides` dotted paths. Each step merges onto the accumulator (§12.1) and records provenance for every leaf it sets.

### 10.3 Validation (steps 4–8)
4. Unknown-key scan on the merged tree (K1–K3) *before* model construction so suggestions have sibling lists. 5. Normalisation of typed strings (durations, sizes, paths, URLs) and inline-secret scan (K13) over **every** string leaf of every layer, so that a secret in a lower layer overridden by a higher one is still reported. 6. Construct section models (pydantic, strict, `extra=forbid`); convert `ValidationError`s to issues (`include_input=False`) mapped to codes 1020–1029 by error type. 7. Cross-field rules X1–X14 and registered cross validators on the `EffectiveConfigDraft` (all sections constructed; sections that failed are absent and dependent rules are skipped with no cascading errors). 8. Relaxation detection (X11). If a `ScopeHook` was supplied: read the scope file (if missing → `RGE-SCOPE-1101` error only when the caller asked for runnable validation), compute digest, check the pin (`RGE-SCOPE-1102`), call the hook, run S1–S5.

### 10.4 Reporting
Issues are de-duplicated by `(code, path, source)` and sorted by severity (errors first), layer order, file, line, path. `render_issues(fmt="text")` line format:
`<file>:<line>:<col>: error RGE-CONFIG-1021 [probe.concurency] unknown key (did you mean 'concurrency'?)` — for env: `env RG_PROBE_CONCURENCY: …`; for CLI: `flag --concurency: …`. Approximate positions are suffixed `~`. `fmt="json"` emits `{"issues":[ConfigIssue…]}` in canonical JSON. All issues of all layers are reported together (FR-OPS-007); a syntax error in the file stops *validation of the file layer only* — env and CLI layers are still validated so the operator sees every problem once.

### 10.5 Effective configuration and digest
After validation: `EffectiveConfig.sections` built; `config_digest = digest(portable_json(sections), "rg.config.v1")` where `portable_json` = `to_json_value` of each section (Int64 durations/sizes as strings; paths workspace-relative with `/`; no provenance, no env/CLI source data, no absolute workspace root). Identical effective values on different machines (same relative layout) therefore give the same digest (NFR-REL-002).

### 10.6 `rg config show` / `validate`
`validate` = `load` without scope hook, exit kind `config_error` on errors, warnings printed. `show` = `load` + report; formats `text` (table, provenance with `--provenance`), `json` (`EffectiveConfigReport`), `toml` (effective values, comment-free, loadable again: round-trip property). Values pass `redact_text` then `sanitize_for_terminal` before printing (defence in depth; values cannot be secrets after K13).

### 10.7 Scope handling and the "no network action without a validated scope" gate
Hook points (all required, specified for their owners):
- **H1 (config)** `EffectiveConfig.scope` carries path, digest, pin and status; `ConfigService.require_validated_scope()` returns a `ValidatedScopeRef` or raises `RGE-SCOPE-1100`/`1101`/`1102`.
- **H2 (composition root, RG-P03-010)** `compose(config, plugins)` accepts a `ValidatedScope` argument; the factories for `HttpTransport`, `WebSocketSession`, `IdentityProviderAdapter`, `EventSource` take that object as a constructor parameter, so a network-capable port cannot be built without it (type-level gate); the lab constructs a generated loopback scope through the same validator (FR-SEC-001: no scope-free mode).
- **H3 (engine, RG-P03-010/RG-P02-007)** DRAFT→VALIDATED checks `scope.status="valid"` and pins `scope.digest` at ARMED; before every mutating action RG-P11-002 re-verifies the digest (`RGE-SCOPE-1103`, TM-06). `scope_file_digest` is the function used for both.
- **H4 (dry run)** performs validation and rendering without any socket; it still requires a valid scope.
- **H5** `rg config validate` and `rg doctor` never contact the network and do not require a scope.
The scope file is read by the loader only to compute its digest and to give the hook the raw bytes; its schema is not interpreted here.

### 10.8 Reload
`ConfigService.reload(executors)`: (1) build a `LoadRequest` from the factory, run `loader.load` via `run_blocking("store", …)`; (2) if errors → keep `current`, return `ReloadReport(applied=False, issues)` and emit `config.reload_rejected` (`RGE-CONFIG-1120`); (3) else diff `current` vs new by leaf path and classify by the field's `ReloadClass`; (4) atomically replace `current` (single reference assignment under a lock; readers never see a mixture); (5) invoke `live` subscribers (`subscribe_live`) in registration order, isolating exceptions; (6) `next_run` and `restart` changes are listed in `ReloadReport` (`pending_next_run`, `pending_restart`) and are **not** applied to running components. A running experiment always uses the immutable `EffectiveConfig` captured in its `RunContext` (config snapshot digest recorded in the manifest); reload cannot alter it. Only GUI/API server processes call `reload`; the CLI loads once per command. No file watching: reload is explicit.

### 10.9 Atomic writer (`rg init`, templates)
`write_config_atomic(path, data)`: refuse if `path` exists unless the caller passed `overwrite=True` (`RGE-CONFIG-1140`); create temp file `<dir>/.revocationgap.toml.<8 random hex>.tmp` (`O_CREAT|O_EXCL`), write bytes with LF newlines, `flush` + `os.fsync`; `os.replace(tmp, path)`; on POSIX fsync the directory; on `PermissionError` (Windows antivirus/indexer holding the target) retry up to 5 times waiting 50, 100, 200, 400, 800 ms via `Clock.sleep`; remove the temp file on failure; failure → `RGE-STORE-1141`. All file calls run on the `store` executor and are shielded from cancellation (`shield_commit`).

## 11. State transitions and invariants

`ConfigService.current` changes only by whole-object replacement: `V0 → V1 → …` on successful reloads; a rejected reload leaves `Vn`.

`ConfigSectionRegistry`: `OPEN → FROZEN` (as RG-P03-002's registry).

Invariants:
- **INV-1** For any field, the effective value is the value from the highest-precedence layer (`cli > env > file_profile > file > preset > default`) that defines it, and `provenance[path].layer` names that layer (property-tested).
- **INV-2** Lists are replaced, never concatenated, across layers.
- **INV-3** `EffectiveConfig` is immutable; `config_digest` is a pure function of effective values (independent of provenance, absolute paths outside the workspace aside).
- **INV-4** No secret value (anything accepted as a `SecretHandle` aside) is present in any layer or in any report/issue/log produced by this module; issue messages never include input values.
- **INV-5** The loader never reads `os.environ`, the clock or the network; given identical `LoadRequest` and file bytes it returns identical results.
- **INV-6** Unknown keys never fall back silently: a key absent from the schema yields an error in every layer.
- **INV-7** Env variable names for the fixed schema are unique (`env_table` is injective) and every scalar or list-of-scalars fixed leaf has exactly one name (`workspace.profile` ↔ `RG_PROFILE` is the only non-derived name; list-of-tables fields such as `plugins.allow` have none).
- **INV-8** After a rejected reload, `current` is the object returned before the call.
- **INV-9** `rg config show --format toml` output loads back to an `EffectiveConfig` with the same `config_digest`.
- **INV-10** Every field marked `safety_default` that differs from its default appears in `relaxations`.

## 12. Core algorithms and pseudocode

### 12.1 Merge with provenance
```
def merge(acc, layer_name, tree, source_of):        # acc: dict path→(value, FieldProvenance); tree: nested dict from the layer
    for path, value in flatten(tree):                # flatten stops at lists and at values (leaf = scalar or list)
        acc[path] = (value, FieldProvenance(layer=layer_name, **source_of(path)))
    return acc
```
Worked example (field `probe.concurrency`): default 20; file `32` (line 7); env `RG_PROBE_CONCURRENCY=16`; CLI `--concurrency 8` → merge order gives 20 → 32 → 16 → 8; effective `8`, provenance `cli --concurrency`; if the CLI flag is absent the value is `16` from `env RG_PROBE_CONCURRENCY`. With a profile `ci` overlay setting `32`→`24` the file-level values are `32` (file) then `24` (file_profile): the overlay wins over the base file but loses to env. Lists: file `report.formats=["html","json"]`, env `RG_REPORT_FORMATS=sarif` → effective `["sarif"]`.

### 12.2 Env name derivation
Fixed schema: `ENV = "RG_" + "_".join(segment.upper() for segment in path.split("."))`. Examples: `probe.verify_tls → RG_PROBE_VERIFY_TLS`; `engine.executors.probe.max_workers → RG_ENGINE_EXECUTORS_PROBE_MAX_WORKERS`; `logging.file.max_bytes → RG_LOGGING_FILE_MAX_BYTES`. `registry.freeze()` fails (`InternalError RGE-INTERNAL-0001`, `invariant=env_name_collision`) if two paths map to one name (e.g. a field `store.lock_wait` and a sub-section `store.lock` with field `wait`).
Keyed sections: `ENV = "RG_" + SECTION + "__" + KEY + "__" + FIELD_PATH`, with `KEY` = entry name upper-cased, `-`→`_`; matching to existing entries ignores case and `-`/`_`; an ambiguity raises `RGE-CONFIG-1062`; a variable for a non-existent entry raises `RGE-CONFIG-1063`. Example: `RG_PROVIDERS__KC_LAB__ISSUER` sets `providers.kc-lab.issuer`.
Variables to consider: exact names from `env_table()`, keyed names, and `RG_CONFIG`, `RG_PROFILE`, `RG_WORKSPACE`. A variable that starts with one of the section prefixes `RG_WORKSPACE_`, `RG_ENGINE_`, `RG_PROBE_`, `RG_SCHEDULE_`, `RG_LIMITS_`, `RG_STORE_`, `RG_EVIDENCE_`, `RG_LOGGING_`, `RG_GUI_`, `RG_PLUGINS_`, `RG_PROVIDERS_`, `RG_TARGETS_`, `RG_POLICY_`, `RG_CLI_`, `RG_REPORT_`, `RG_LAB_` but matches nothing → `RGE-CONFIG-1060` (typo detection; suggestion from `difflib`). Other `RG_*` names (e.g. `RG_ALICE_PASSWORD`, `RG_TOKEN_ALICE`) are secret-source variables referenced by handles and are ignored by the loader. **Rule for secret env names:** they must not start with a section prefix (checked by `SecretHandle` validation of `secret:env:<NAME>` — a name with a section prefix is rejected, `RGE-CONFIG-1029`).
Empty values are ignored with warning `RGE-CONFIG-1061`. Parsing of env text: bool (`true|false|1|0`, case-insensitive), int, float, enum, `Duration`, `ByteSize`, lists comma-separated (elements may not contain commas), everything else string.

### 12.3 Duration and size parsing
```
DURATION = ^(?:\d+(?:\.\d+)?(?:ns|us|ms|s|m|h|d))+$           # units: ns=1, us=1e3, ms=1e6, s=1e9, m=6e10, h=3.6e12, d=8.64e13 ns
ns = sum(Decimal(n) * UNIT[u] for n, u in parts); require ns == ns.to_integral_value() else 1025
```
| Input | Result |
|---|---|
| `"30s"` | 30 000 000 000 |
| `"250ms"` | 250 000 000 |
| `"1h30m"` | 5 400 000 000 000 |
| `"1.5s"` | 1 500 000 000 |
| `"0.5ns"` | error 1025 (sub-nanosecond) |
| `30` (bare number) | error 1025: "write \"30s\"" |
| `"1m30s"` | 90 000 000 000 |
Sizes: `SIZE = ^(\d+(?:\.\d+)?)\s?(B|KiB|MiB|GiB)$` → bytes (`KiB=1024`); `"64KiB"=65 536`, `"1.5MiB"=1 572 864`, `"5MB"` → error 1026 with suggestion "use MiB (1 MiB = 1 048 576 bytes)"; integer TOML value = bytes.

### 12.4 URL normalisation (`normalize_url`, shared with RG-P11-002 for scope matching)
```
def normalize_url(s, *, allowed_schemes, allow_query=False):
    reject if any char < 0x21 or == 0x7f or in "\\ " ; u = urlsplit(s)
    scheme = u.scheme.lower() in allowed_schemes else 1028
    reject u.username/u.password (userinfo)                      # TM-07
    reject fragment; reject query unless allow_query
    host = u.hostname: IPv6 → ipaddress.ip_address(h).compressed in brackets; IPv4 must be dotted-quad of 4 decimal octets (no leading zeros, no int/hex/octal forms) else 1028; names → IDNA/punycode lower-case; strip trailing dot
    port = u.port; drop if default for scheme (80/443/80/443); 1..65535
    path = remove_dot_segments(percent_normalise(u.path)); strip one trailing "/" unless path == "/"; empty path → ""
    return f"{scheme}://{host}[:{port}]{path}"
```
Examples: `HTTPS://API.Example.COM:443/v1/../items/` → `https://api.example.com/items`; `http://[0:0:0:0:0:0:0:1]:80` → `http://[::1]`; `https://bücher.example/` → `https://xn--bcher-kva.example`; `http://2130706433/` → error 1028 (numeric host form); `https://user:pw@host/` → error 1028 (userinfo; message does not echo it); `https://host/a%2fb` → path kept `a%2Fb` (hex upper-cased, no decoding of reserved characters).

### 12.5 Path normalisation (`normalize_path`)
```
def normalize_path(p, *, base, root, local_fs_required, portable=True):
    reject NUL; reject leading "~" (no home expansion; suggest an absolute path); reject "${" and "%VAR%" patterns (no interpolation, TM-14)
    segs = split on both "/" and "\\" if the source is a TOML literal for Windows; reject any segment that (case-insensitively, with or without extension) is CON PRN AUX NUL COM1-9 LPT1-9, or ends with "." or " "    # portable rule applies on every OS
    q = os.path.normpath(join(base, p)); absolute
    if root and not allow_external and not within(q, root): reject                       # containment uses normcase + NFC + realpath(strict=False)
    if local_fs_required and is_unc(q): reject                                           # SQLite WAL needs a local FS
    if windows and len(q) >= 240: internal form = "\\\\?\\" + q    (display strips the prefix)
    return q
```
`base` = workspace root for the file layer and presets; `cwd` for env and CLI. Containment on Windows and macOS compares `normcase`d, NFC-normalised, case-folded strings (both file systems are case-insensitive by default); on Linux case-sensitive. Serialisation to the portable JSON form: inside the workspace → relative with `/` (`./.rg` printed as `.rg`), else absolute with `/`.

### 12.6 Best-effort key index (line/column provenance)
`tomllib` returns no positions. The index scans lines: skip blank/comment lines; track multi-line strings (`"""`/`'''` toggles) and bracket depth of multi-line arrays/inline tables; `[a.b]` / `[[a.b]]` set the current table path (dotted parts split respecting quotes); `key = …` and dotted `a.b = …` register `path → (line, column of key start)`; a duplicate path in the same table is remembered as a `DuplicateKeyHint`. Lookup for a path falls back to the nearest enclosing table header line (`approximate=true`). Inline-table members get the line of the key that opens the table (approximate). Syntax errors: `tomllib` on CPython 3.11–3.13 reports `(at line L, column C)` in the message for most errors but only `(at end of document)` for some (e.g. duplicate keys: *Cannot overwrite a value*); the loader extracts `L, C` by regex, or uses `lineno/colno` attributes when present (3.14), and for "end of document" uses the line of the first `DuplicateKeyHint` if the message is *Cannot overwrite a value*, else the last line with `approximate=true` (author-verified message formats, A-1).

### 12.7 Suggestions
`suggest(name, candidates)` = first of `difflib.get_close_matches(name, candidates, n=1, cutoff=0.6)`; examples: `concurency` among `probe` fields → `concurrency`; `verify_tsl` → `verify_tls`. Enum errors list values; range errors state `allowed <min>..<max>`; handle errors: `use secret:env:NAME, secret:keyring:service/name or secret:file:PATH`; inline secret: `store the value in an environment variable and set this field to "secret:env:NAME"` (the offending value is never echoed).

### 12.8 Relaxation detection
`relaxations = [Relaxation(path, display(value), display(default), rule) for each leaf whose FieldMeta.safety_default and value != default]`; initial safety-default fields: `probe.verify_tls`, `workspace.allow_external_data_dir`, `gui.allow_non_loopback`, `gui.bind` (non-loopback), `evidence.raw_capture`, `evidence.encryption` (`off` is the default, not a relaxation), `logging.log_bodies`, `limits.*` raised above their defaults by more than ×4. The list is part of the report and is written to the audit log at arming (RG-P11-002).

## 13. Internal functions, methods, or service operations

| Function | Signature | Purpose |
|---|---|---|
| `read_config_bytes` | `(path, limit) -> bytes` | P1–P2 |
| `parse_toml` | `(text) -> tuple[dict, list[ConfigIssue]]` | wraps `tomllib`, §12.6 error extraction |
| `toml_to_json_value` | `(obj) -> JsonValue` | datetimes → UTC strings; rejects naive; used for scope digest |
| `build_key_index` | `(text) -> KeyIndex` | §12.6 |
| `flatten` / `unflatten` | `(tree) -> dict[path, value]` | merge helpers |
| `env_to_tree` | `(env, table, tree_so_far) -> tuple[dict, list[ConfigIssue]]` | §12.2 |
| `cli_to_tree` | `(overrides, registry) -> tuple[dict, list[ConfigIssue]]` | validates paths/types |
| `scan_inline_secrets` | `(layer_trees) -> list[ConfigIssue]` | K13 |
| `parse_duration` / `parse_size` | `(s) -> int` | §12.3 |
| `normalize_url` / `normalize_path` | see §12.4/12.5 | |
| `issues_from_validation_error` | `(e, layer_index) -> list[ConfigIssue]` | maps pydantic error types to codes |
| `detect_relaxations` | `(sections) -> tuple[Relaxation, ...]` | §12.8 |
| `portable_json` | `(sections, root) -> dict` | §10.5 |
| `classify_reload` | `(old, new) -> ReloadReport` | §10.8 |
| `ConfigService._swap` | `(new)` | lock + assignment |

## 14. Error handling and failure recovery

| Failure | Detection | Handling | Recovery | Code |
|---|---|---|---|---|
| File missing (explicit) | stat | issue; continue with env/CLI layers | fix path | 1002 |
| File unreadable/binary | read/decode | issue | fix permissions | 1003/1004 |
| TOML syntax | `tomllib` | issue with line/col; file layer skipped | fix file | 1001 |
| Unknown key | K1 | issue + suggestion; model not built for that table | fix spelling | 1021 |
| Inline secret | K13 | issue (path only), value never stored in the issue | use handle | 1030 |
| Invalid value | pydantic/normalisers | issue(s) | correct | 1020–1029 |
| Cross-field/section violation | X*, validators | issue | correct | 1033/1034 |
| Scope missing/mismatch | hook | `RGE-SCOPE-*` issue (error only when runnable validation requested) | provide/refresh scope; update pin | 1101/1102 |
| Reload with invalid file | validation | previous config retained; issues reported | fix file; reload again | 1120 |
| Atomic write fails | `PermissionError`/`OSError` after 5 retries | temp removed; error | close other readers | `RGE-STORE-1141` |
| Validator raises an exception | try/except around each registered validator | issue `RGE-INTERNAL-0001` (`invariant=validator_exception`, validator name) — validation continues | fix validator | — |
| Registry misuse (duplicate section, env collision) | `freeze` | startup failure | fix composition | `RGE-INTERNAL-0001` |

Partial-failure semantics: `load` never returns a configuration when any error exists; warnings alone do not block. All issues from all layers are returned in one result.

## 15. Security requirements and trust boundaries

* **Untrusted inputs:** the config file (may come from a repository checkout), environment (CI), CLI flags; all are parsed with `tomllib` only, size-limited (1 MiB), strict types, no interpolation, no includes, no `~`/env expansion (TM-14).
* **TM-07 / FR-SEC-005:** K12/K13: only handle syntax is accepted for credentials; shape detection runs on *every* string of *every* layer; issues never echo values; process arguments carry no secret because no CLI path accepts a secret value (K13 applies to CLI too, and paths whose key matches `SECRET_KEY_NAME` accept handles only); `rg config show` prints handles, never resolved material.
* **TM-02:** base URLs for probing come only from `targets.*.base_url` (operator configuration) and must lie within the scope (S1); schema `servers` are not configuration.
* **TM-06:** `workspace.scope_digest` pin; `scope_file_digest` is canonical (formatting/comment-insensitive) so whitespace edits don't break the pin but semantic edits do.
* **TM-17/TM-21:** `gui.bind` default loopback; non-loopback needs explicit fields and TLS; receiver binds are configured in the scope (SCR-12), not here.
* **TM-22:** `plugins.allow` entries carry digests; unknown plugin config sections are rejected (K1).
* **FR-SEC-014:** relaxations are enumerated and audited; presets cannot relax.
* **Redirects:** no config field exists to enable redirects.
* **Residual:** an operator can still put a secret in a free-text field in a shape the detector does not recognise (e.g. a short password in `description`); K13 is a safety net, not a guarantee; typed fields (`SecretHandle`) remain the primary control.

## 16. Concurrency, asynchronous behavior, and resource ownership

`ConfigLoader` is stateless, synchronous and thread-safe; it is invoked via `run_blocking("store", …)` from async code (small blocking reads) or directly by the sync CLI bootstrap. `ConfigService` is loop-confined except `current` (atomic reference read from any thread) and `subscribe_live` callbacks (invoked on the loop). The reload lock is a `threading.Lock` held only for the reference swap (≪ 1 ms). The atomic writer runs on the `store` executor with the commit shielded. No background tasks, no file watchers, no handles kept open between calls.

## 17. Performance and resource requirements

Proposals (benchmarks validate):

| Budget | Value | Test |
|---|---|---|
| `load` of a 50-key file with all sections registered | ≤ 50 ms warm (excluding import time) | TST-RG-P03-003-24 |
| `load` of a 1 MiB file (limit) | ≤ 500 ms | TST-RG-P03-003-24 |
| `rg config validate` start to finish (CLI) | ≤ 1 s with `rg run --help` budget of NFR-PERF-009 untouched (config import must not import Schemathesis/hypothesis/pytest) | TST-RG-P03-003-24 |
| Memory | ≤ 20 MiB for registry + models | TST-RG-P03-003-24 |
| Key index | linear in lines; ≤ 20 ms for 10 000 lines | TST-RG-P03-003-24 |

## 18. Configuration and defaults

This module's own configuration surface is the catalogue of §8 (the subsystem *is* the configuration). Parameters of the subsystem itself (not user-overridable): `MAX_CONFIG_BYTES = 1 MiB`, `MAX_DISCOVERY_DEPTH = 32`, `ATOMIC_WRITE_RETRIES = 5` with backoff 50 ms × 2ⁿ, `MAX_ISSUES = 500` (further issues are summarised as `… and N more`). Global inputs: `RG_CONFIG`, `RG_PROFILE`, `RG_WORKSPACE`; precedence of the config *file location*: `--config` > `RG_CONFIG` > `<workspace>/revocationgap.toml`. Failure behaviour per rule in §9.

### 18.1 CLI flag table for global flags (owned here; command-specific flags belong to RG-P10-001)

| Flag | Maps to | Notes |
|---|---|---|
| `--workspace/-w PATH` | `LoadRequest.workspace_dir` | not a config key |
| `--config PATH` | `LoadRequest.config_file` | |
| `--profile NAME` | `workspace.profile` (layer cli) | |
| `-v` / `-vv` / `-q` | `logging.console.level` = `INFO` / `DEBUG` / `ERROR` | |
| `--log-format {text,json}` | `logging.console.format` | |
| `--non-interactive` | `cli.non_interactive=true` | FR-CLI-007 |
| `--json` | `cli.output="json"` | |
| `--no-color` | `cli.color="never"` | |
| `--clock {system,virtual}` | `engine.clock` | X1 applies |
| `--seed N` | `engine.seed` | |
Any other `cli_overrides` key must be a valid dotted path in the registry or `RGE-CONFIG-1064`.

## 19. Logging, observability, evidence requirements

Events (logger `rg.config`): `config.loaded{files, profile, digest, warnings}` (INFO), `config.relaxed{path}` (WARNING per relaxation), `config.reload_applied{live, pending_next_run, pending_restart}` (INFO), `config.reload_rejected{errors}` (WARNING), `config.env_ignored{count}` (DEBUG). Issue messages and paths are safe by construction; values are logged only as display strings of validated fields and never for fields with `secret_handle` metadata beyond the handle. Evidence: the run manifest (RG-P08-001) records `config_digest`, `config_files[] (path, sha256)`, `profile`, `relaxations[]`, `scope_digest`, and the list of env var *names* consulted (never values). The effective-config snapshot (`EffectiveConfigReport` without provenance noise) is stored as a derived evidence item at run start (FR-EVD-007).

## 20. Platform compatibility

| Topic | Rule |
|---|---|
| Encoding | UTF-8 only; a UTF-8 BOM (Windows Notepad) is stripped with a warning; other encodings → 1004 |
| Line endings | CRLF and LF accepted (tomllib); generated files use LF; the atomic writer opens in binary mode |
| Paths (Windows) | accepts `C:\x\y`, `C:/x/y`, UNC; TOML literal strings (`'C:\data'`) recommended — a basic string with unescaped backslash is a TOML syntax error and the issue suggests literal strings; drive-letter case-insensitive; reserved device names and trailing dot/space rejected on all platforms (portable workspaces); long paths: internal `\\?\` prefix at ≥ 240 characters, `rg doctor` reports `LongPathsEnabled` |
| Paths (macOS) | NFD file names (HFS+/APFS normalisation differences) compared after NFC+casefold |
| Case sensitivity | containment checks follow the platform's file-system default; config keys and enum values are case-sensitive; env var names upper-case only (Windows env is case-insensitive and reports upper-case names; on POSIX a lower-case `rg_probe_concurrency` is ignored with a `config.env_ignored` debug count) |
| Network FS | `workspace.data_dir` on UNC rejected (1027); on mounted network filesystems detection is `rg doctor`'s (NFR-PLAT-002) |
| Environment | CI systems may pass empty variables: ignored with warning (1061) |
| Python | `tomllib` error message formats differ slightly across 3.11–3.14 (3.14 adds position attributes) → §12.6 handles both |
| Permissions | the loader only reads; the generated file is created with default permissions (config holds no secrets) |

## 21. Edge cases and invalid inputs

| # | Case | Expected behaviour |
|---|---|---|
| E-1 | `[probe]` contains `concurency = 5` | 1021 with suggestion `concurrency`; position `file:<line>`; other errors still reported |
| E-2 | `probe.concurrency = "20"` | 1020 (strict type), no coercion |
| E-3 | `timeout = 30` for a `Duration` | 1025 "write "30s"" |
| E-4 | `RG_PROBE_VERIFY_TLS=false` | accepted; relaxation listed; S4 checked when scope available; warning 1035 |
| E-5 | `RG_PROBE_CONCURENCY=5` | 1060 with suggestion |
| E-6 | `admin_credential = "hunter2"` | 1029 (not a handle) and 1030 not raised for it (not secret-shaped) — message never echoes `hunter2` |
| E-7 | `admin_credential = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2ln"` | 1030 INLINE_SECRET (path only) |
| E-8 | `base_url = "https://user:pw@host/"` | 1028; value not echoed |
| E-9 | TOML with BOM and CRLF | parsed; warning for BOM |
| E-10 | duplicate keys in a table | 1001 with the second occurrence line (hint) |
| E-11 | `[workspace] data_dir = "../outside"` | 1027 unless `allow_external_data_dir=true` (then relaxation) |
| E-12 | `data_dir = "CON"` or `"logs."` | 1027 |
| E-13 | `[providers.kc-lab]` and `[providers.kc_lab]` | 1062 |
| E-14 | `[providers.x] adapter = "idp.unknown"` | 1032 listing registered variants |
| E-15 | `--profile nope` with no such preset or `[profile.nope]` | 1037 |
| E-16 | env sets `RG_PROVIDERS__NEW__ISSUER` for an entry that exists in no layer | 1063 |
| E-17 | file layer has a syntax error, env sets an invalid value | both reported (1001 and 1020 with `env_var`) |
| E-18 | `engine.executors.store.max_workers = 2` | 1033 (X14) |
| E-19 | `gui.bind = "0.0.0.0"` without `allow_non_loopback` | 1033 (X7) |
| E-20 | `scope_digest` pin differs from the file | `RGE-SCOPE-1102` on runnable validation; plain `validate` warns |
| E-21 | reload while file is half-written | syntax error → 1120, previous config retained |
| E-22 | 600 errors | first 500 shown + summary line |
| E-23 | TOML local time `t = 07:32:00` | 1007 |
| E-24 | Windows path `'C:\Users\a\ws'` in TOML literal string | accepted; normalised to `C:\Users\a\ws`; serialised `C:/Users/a/ws` |

## 22. Unit and integration test requirements

- **TST-RG-P03-003-01** Parse stage: valid file; syntax-error corpus (≥ 12 files: unterminated string, bad table header, duplicate key, bad escape, trailing comma in inline table, BOM+CRLF, 1 MiB+1 bytes, NUL byte, non-UTF-8) → codes 1001/1004 with expected line/column; "end of document" cases flagged `approximate` and the duplicate-key hint line used; runs on every CI Python.
- **TST-RG-P03-003-02** Key index fixtures: tables, dotted keys, array of tables, multi-line strings/arrays, inline tables, quoted keys; exact `(line, col)` for simple keys, `approximate=True` fallback otherwise.
- **TST-RG-P03-003-03** Precedence property (Hypothesis): random subsets of the six layers assign random valid values to random fields; the effective value equals the highest layer's value, `provenance.layer` matches, lists replaced (INV-1, INV-2); worked example of §12.1 as a fixed case.
- **TST-RG-P03-003-04** Env mapping: `env_table()` injective and complete for all registered fixed fields (INV-7); examples of §12.2; keyed form; lower-case POSIX variables ignored; section-prefix typo → 1060 with suggestion; non-prefixed `RG_ALICE_PASSWORD` ignored; empty value ignored with warning; secret env names starting with a section prefix rejected in handles.
- **TST-RG-P03-003-05** Unknown keys: random extra key at every depth of the fixture file is reported with code 1021 and, when within edit distance, the nearest-name suggestion; unknown section; unknown variant (1032).
- **TST-RG-P03-003-06** Strict typing and ranges: table-driven rows for every rule K4–K9 with the expected code and *no* coercion (`"20"`, `20.0`, `true` for int); boundaries (min, max, min−1, max+1) for ≥ 10 numeric fields.
- **TST-RG-P03-003-07** Duration/size: table of §12.3; property: `parse(format(n)) == n` for random ns up to 10¹⁵ and sizes up to 10¹²; `KB`/`MB` rejected with suggestion; bare numbers rejected for durations.
- **TST-RG-P03-003-08** URL normalisation: examples of §12.4; idempotence property (`normalize(normalize(u)) == normalize(u)`); rejection corpus (userinfo, spaces, backslash, `http://2130706433`, `http://0x7f.1`, `http://017700000001`, `http://[::1`, fragment, query where disallowed, `javascript:`); message never contains the input.
- **TST-RG-P03-003-09** Path normalisation: POSIX and Windows corpora (`..` escape, `~`, `${HOME}`, `%APPDATA%`, `CON.txt`, trailing dot, UNC for `data_dir`, mixed separators, ≥ 240-char path gets `\\?\` internally, case-insensitive containment on Windows/macOS, NFD vs NFC) — Windows rows run only on the Windows CI leg, POSIX rows everywhere.
- **TST-RG-P03-003-10** Inline-secret rejection: 200 generated secret-shaped strings (JWT, `Bearer x`, `Basic …`, PEM, URL userinfo) injected into random string fields in each layer (file, env, CLI) → 1030 with the path, never the value; a secret overridden by a higher layer is still reported; grep of all issues/logs/report for the injected canaries = 0 (SC-07 hook, uses RG-P03-004 oracle).
- **TST-RG-P03-003-11** Handle syntax: fields typed `SecretHandle` accept the three standard resolvers and reject plain strings with 1029; `secret:env:RG_PROBE_X` (section prefix) rejected.
- **TST-RG-P03-003-12** Cross-field and cross-section rules X1–X14: one failing fixture per rule plus one passing; errors from independent rules reported together; a failing section suppresses only dependent rules.
- **TST-RG-P03-003-13** Section registry: registration of owner sections/variants/validators; duplicate section name, duplicate variant tag, env-name collision, registration after `freeze` → `RGE-INTERNAL-0001`; plugin section at `[plugins.config.<id>]` validated by its model; variant discriminator error 1032.
- **TST-RG-P03-003-14** Profiles/presets: `ci` and `lab` presets; `[profile.ci]` overlay order (file base < overlay < env < CLI); unknown profile 1037; presets cannot relax safety defaults (asserted over all preset definitions).
- **TST-RG-P03-003-15** Effective-config report: golden text and JSON renderings for a fixture (layers from every source); provenance lines/flags/env names; relaxations; `scope` block; values never contain a canary; `--format toml` round trip with equal `config_digest` (INV-9).
- **TST-RG-P03-003-16** Digest portability: the same fixture loaded from two different absolute roots (and on Windows vs Linux CI) yields the same `config_digest`; changing a value changes it; provenance changes do not (INV-3).
- **TST-RG-P03-003-17** Error report format: text and JSON golden for a mixed-error fixture; ordering (errors before warnings, layer order, file/line); de-duplication; 500-issue cap with summary; env/flag source formats; exit kind of `ConfigLoadError` is `config_error`, of scope issues `scope_refusal`.
- **TST-RG-P03-003-18** Scope handling: digest of a scope file is stable under comment/whitespace/key-order edits and changes on value edits (canonical); datetime handling (offset → UTC string, naive → 1007); pin mismatch → `RGE-SCOPE-1102`; missing file → 1101; fake `ScopeHook` drives S1–S5 (1104 with `details.rule`); no hook → `status="unchecked"` and `require_validated_scope` → `RGE-SCOPE-1100`.
- **TST-RG-P03-003-19** Gate hooks H2–H4 contract test (with a fake composition root): constructing `HttpTransport`/adapter factories without a `ValidatedScope` is a type error and a runtime `RGE-SCOPE-1100`; dry run performs no socket calls (socket monkeypatch fails the test).
- **TST-RG-P03-003-20** Reload: valid reload swaps atomically (a reader thread hammering `current` never sees a mixed object — consistency check across 2 correlated fields); invalid reload keeps previous (INV-8) and returns issues; reload classes partition changes into live/next_run/restart; `live` subscribers invoked once, exceptions isolated; running-experiment snapshot unaffected.
- **TST-RG-P03-003-21** Atomic writer: refuses overwrite (1140); crash injection between temp write and replace leaves either the old or the new file (never partial); Windows `PermissionError` retry path simulated (marker `windows`); temp file removed on failure; LF newlines.
- **TST-RG-P03-003-22** Relaxations: each safety-default field changed → listed; defaults → empty; `limits` raised > ×4 listed; the list equals the audit payload format of RG-P11-002 fixture.
- **TST-RG-P03-003-23** Catalogue doc-sync: the exported `config_document` schema equals the committed golden file and rejects `timeout = 30` but accepts `"30s"`; `registry.describe()` equals the tables of §8.5–§8.17 of this spec for `[workspace]` (full) and for every skeleton field name/type/default/env var once the owner section is registered; env names unique; every `safety_default` field is documented.
- **TST-RG-P03-003-24** Benchmarks (marker `bench`) for the budgets of §17, plus an import test asserting `import revocationgap.config` does not import `schemathesis`, `hypothesis`, `pytest` or `rich`.
- **TST-RG-P03-003-25** Determinism/purity: `load` with identical `LoadRequest` and file bytes returns equal results across 100 runs; the loader does not read `os.environ`/clock/network (monkeypatched to raise).
- **TST-RG-P03-003-26** CLI layer: global flag table of §18.1 maps to the paths; unknown dotted path → 1064; a flag attempting to set a secret-named path to a non-handle → 1029/1030; `-v` precedence over env.

## 23. Mocking and test fixture requirements

* `FakeFs` (in-memory files, injectable `PermissionError`, crash points) behind `ConfigLoader(fs=…)`; real-FS tests use `tmp_path`.
* Fake `ScopeHook`/`ScopeView` (permissive and restrictive variants) and `ValidatedScope` factory test helper (`rg_core.testing`).
* Fixture trees `tests/data/config/{valid,syntax,unknown,typing,secrets,windows,profiles,scope}/`; golden outputs `*.golden.txt`/`*.golden.json` (LF).
* Section fixtures: minimal fake owner sections registering into a test registry (to test the extension mechanism without the real owners).
* `FakeClock`; `ExecutorSet` test instance for the writer and reload.
* Hypothesis strategies (test-only) for layered trees over a synthetic registry.

## 24. Objective acceptance criteria

- **AC-RG-P03-003-01** Parse errors carry line/column (or an explicit `approximate` flag) across Python 3.11–3.14, and syntax stages never mask validation of other layers (verified by TST-RG-P03-003-01, TST-RG-P03-003-02, TST-RG-P03-003-17).
- **AC-RG-P03-003-02** Effective values follow `default < preset < file < file-profile < env < cli`, lists replace, and each leaf's provenance names the winning layer and source (verified by TST-RG-P03-003-03, TST-RG-P03-003-14, TST-RG-P03-003-26).
- **AC-RG-P03-003-03** Env variable names are derived mechanically, unique, typo-checked and never read outside the loader (verified by TST-RG-P03-003-04, TST-RG-P03-003-25).
- **AC-RG-P03-003-04** Every unknown key, section, variant or env/flag name is an error with a stable code and, when close, a suggestion (verified by TST-RG-P03-003-04, TST-RG-P03-003-05, TST-RG-P03-003-13).
- **AC-RG-P03-003-05** Types are strict, ranges enforced, and durations, sizes, paths and URLs follow the stated grammars and normalisation (verified by TST-RG-P03-003-06, TST-RG-P03-003-07, TST-RG-P03-003-08, TST-RG-P03-003-09).
- **AC-RG-P03-003-06** Inline secrets in any layer are rejected without being echoed, and only `secret:` handles are accepted for credentials (verified by TST-RG-P03-003-10, TST-RG-P03-003-11).
- **AC-RG-P03-003-07** Cross-field, cross-section and scope-aware rules report all violations together with their rule ids (verified by TST-RG-P03-003-12, TST-RG-P03-003-18).
- **AC-RG-P03-003-08** Other elements can register sections, keyed variants, validators and presets before freeze, and registry misuse is rejected (verified by TST-RG-P03-003-13, TST-RG-P03-003-23).
- **AC-RG-P03-003-09** The effective-configuration report with provenance and relaxations is available in text, JSON and TOML, the TOML form round-trips, and the configuration digest is portable across machines (verified by TST-RG-P03-003-15, TST-RG-P03-003-16, TST-RG-P03-003-22).
- **AC-RG-P03-003-10** The scope file is a separate document whose digest pin and hook points enforce "no network action without a validated scope" and dry run opens no sockets (verified by TST-RG-P03-003-18, TST-RG-P03-003-19).
- **AC-RG-P03-003-11** Reload is atomic, never applies a partially valid configuration, classifies changes by reload class and leaves running experiments untouched (verified by TST-RG-P03-003-20).
- **AC-RG-P03-003-12** Generated configuration files are written atomically with Windows retry behaviour (verified by TST-RG-P03-003-21).
- **AC-RG-P03-003-13** Error reports follow the documented text/JSON formats and map to exit kinds (verified by TST-RG-P03-003-17).
- **AC-RG-P03-003-14** The catalogue in this spec matches the registered models and the performance/import budgets hold (verified by TST-RG-P03-003-23, TST-RG-P03-003-24).

## 25. Research sources and engineering rationale

Sources: SYSTEM-ARCHITECTURE §6.3 (composition root, config only reads env), §7 (workspace layout), §9 (layered precedence, unknown keys error); PRD FR-CLI-006, FR-OPS-007, FR-SEC-001/-005/-008/-009/-012/-014, FR-EVD-007, FR-EXP-005/-010, FR-PRB-017, NFR-PLAT-002/-003, NFR-PERF-007, NFR-REL-001; USER-WORKFLOWS SCR-01…SCR-12 (scope document contents — scope is *not* configuration), WF-02; THREAT-MODEL TM-02, TM-04, TM-05, TM-06, TM-07, TM-14, TM-17, TM-21, TM-22, OQ-TM-04 (limits defaults pending benchmarks); DATA-MODEL §2.4 (handles), §3 (`ValidationMode`, `PolicyProfile`), §4 (`N_confirm`, `T_confirm`); ADR-0011 (scope), ADR-0012 (reproducibility: spec/config digests); TECHNICAL-FEASIBILITY §2 (`platformdirs` listed for app, `tomllib`). `tomllib` message/position behaviour on 3.11–3.13 was checked by the author (sandbox CPython 3.11.16/3.12.3/3.13.15); 3.14 attributes are an assumption (A-1).

Decisions:

- **DEC-1 TOML via `tomllib` only; no YAML, no includes, no interpolation.** Rejected: YAML (aliases, implicit typing, TM-04/TM-14 class of issues), JSON (no comments), INI. Verification: TST-…-01, -09.
- **DEC-2 Six layers with `file_profile` and `preset` as explicit layers.** Gives profiles a defined place without changing the four-layer contract of FR-CLI-006 for users; provenance names the finer layer. Rejected: profile as a separate file (extra discovery rules). Verification: TST-…-03, -14.
- **DEC-3 Lists replace, tables merge.** Rejected: append semantics (cannot remove an inherited element). Verification: TST-…-03.
- **DEC-4 Durations require units; bare numbers rejected.** Removes the `_s`/`_ms` suffix ambiguity (frozen `CallPolicy` keeps `_s` internally; the composition root converts). Rejected: bare seconds (mistakes by ×1000). Verification: TST-…-07.
- **DEC-5 Sizes IEC only.** `64KB` ambiguity (1000 vs 1024) removed. Verification: TST-…-07.
- **DEC-6 Env mapping derived from the schema; keyed entries via `__`; env may not create entries.** Rejected: free-form env (cannot validate), creating entries from env (unreviewable config in CI). Verification: TST-…-04.
- **DEC-7 Strict typing, no coercion.** Prevents `"false"` strings becoming truthy and `"20"` silently accepted. Verification: TST-…-06.
- **DEC-8 Inline-secret scan over all layers including overridden values.** A secret committed in the file is a leak even if env overrides it. Verification: TST-…-10.
- **DEC-9 Best-effort line provenance via a small key index** rather than a position-preserving parser dependency (`tomlkit`/`rtoml`): zero extra dependency, accurate for ordinary files, flagged `approximate` otherwise. Rejected: `tomlkit` (dependency, slower, preserves formatting but still no per-value positions API we can rely on). Verification: TST-…-02.
- **DEC-10 Portable digest with workspace-relative paths.** Run manifests compare across machines. Rejected: absolute paths in the digest (never equal). Verification: TST-…-16.
- **DEC-11 Whole-object atomic reload with reload classes; no file watching; running experiments pinned.** Rejected: field-wise hot patching (tearing, un-auditable), inotify/ReadDirectoryChanges (platform divergence). Verification: TST-…-20.
- **DEC-12 Scope is a separate document; config holds only path and pin.** Keeps authorisation reviewable independently of tuning (ADR-0011). A typed `ValidatedScope` token in port factories makes the gate structural. Verification: TST-…-18, -19.
- **DEC-13 Section registry with explicit registration** (no import side effects, same rationale as RG-P03-002 DEC-8) and skeleton ownership table so parallel authors do not collide. Verification: TST-…-13, -23.
- **DEC-14 No `rg config set`.** Rejected for v1 (comment/format preservation). Template generation only. Verification: review.

## 26. Remaining uncertainties or assumptions

| # | Assumption | Falsifying test |
|---|---|---|
| A-1 | `tomllib` reports `(at line L, column C)` for most syntax errors and `(at end of document)` for some (e.g. duplicate keys) on CPython 3.11–3.13 (author sandbox); Python 3.14 exposes position attributes (not verified here) | TST-…-01 on the 3.14 leg |
| A-2 | Proposed defaults in the skeleton sections (§8.6–§8.16) are acceptable starting points; owners may change them in their specs | doc-sync test TST-…-23 fails until the owner spec and catalogue agree |
| A-3 | `limits.*` defaults are placeholders until RG-P12-004 benchmarks (OQ-TM-04) | benchmark results; no figure is asserted as measured |
| A-4 | IDNA 2003 codec (`str.encode("idna")`) suffices for normalising operator-typed hostnames; IDNA 2008 differences are out of scope | URL corpus with deviation characters (`ß`, final sigma) → documented behaviour; revisit if the `idna` package is adopted |
| A-5 | Windows `os.replace` over an existing file is atomic for same-volume paths | TST-…-21 Windows leg |
| A-6 | `difflib.get_close_matches(cutoff=0.6)` gives useful suggestions for the catalogue's key names | suggestion corpus in TST-…-05 (precision check) |
| A-7 | The K13 shape detector (RG-P03-002) has acceptable false-positive rate on legitimate configuration strings (URLs, paths, descriptions) | positive/negative corpora TST-…-10 and the shipped example files |
| A-8 | Operators rarely need more than 500 simultaneous issues; the cap hides no distinct rule | TST-…-17 |
| A-9 | RG-P11-002 can supply `ScopeHook`/`ValidatedScope` with the signatures of §7.4 | contract review when RG-P11-002 is authored; CCR if changed |
| A-10 | Walking up to find `revocationgap.toml` does not surprise users in nested repositories | UX review RG-P10-002 |

## 27. Maintainability, portability, and future extension requirements

* **Extension points:** `ConfigSectionRegistry.register_section/register_variant/add_*_validator/add_preset` (the only way to add configuration); `ReloadClass` and `safety_default` metadata on fields; keyed sections for providers/targets/plugins.
* **Adding a field:** add it to the owner's model with `meta(...)`; the catalogue test (TST-…-23) forces the §8 table to be updated; additive changes are minor schema versions of `config_document` (RG-P03-002 rules); renames are deprecations: keep the old key one minor release as `DEPRECATED_KEY` (1036) mapped to the new path.
* **Versioning:** `schema_version` in the file; migrations (`Migration` hooks of RG-P03-002) run before validation for older majors (RG-P11-006 applies them with backup); newer majors are refused (1006).
* **Reuse:** the loader core (layering, provenance, env mapping, normalisers, suggestions) has no RevocationGap-specific code outside the registered sections and could back other tools; `normalize_url`/`normalize_path` are shared with RG-P11-002 so scope matching and configuration agree byte-for-byte.
* **Future:** `rg config set` with format-preserving edits (needs a position-preserving TOML writer); remote/managed configuration sources (would add a layer between file and env, still validated by the same registry); per-experiment overlay files. None changes the section contracts.
* **Documentation generation:** `registry.describe()` generates the user-facing configuration reference and `config_document` JSON Schema (usable by editors via Taplo); the golden schema covers built-in sections only (plugin sections are added at runtime).
