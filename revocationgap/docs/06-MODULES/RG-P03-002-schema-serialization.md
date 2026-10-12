---
id: RG-P03-002
title: "Shared schema and serialization framework"
phase: "03"
package: core
module_ids: [MOD-CORE-SCHEMA_SERIALIZATION]
status: DRAFT
depends_on: [RG-P03-001]
requirements: [FR-EXP-001, FR-EVD-002, FR-EVD-003, FR-EVD-004, FR-EVD-007, FR-OPS-003, FR-SEC-005, FR-SEC-009, FR-RPT-008, FR-EXT-004, NFR-REL-002, NFR-MNT-002, NFR-MNT-003, NFR-MNT-005, NFR-TEST-004]
interfaces_defined: [IF-CORE-SERIAL]
interfaces_used: [IF-CORE-CLOCK, IF-CORE-ERR]
schemas_defined: [SCH-SERIAL]
schemathesis_touchpoints: []
---

# RG-P03-002 — Shared schema and serialization framework

> Scope: `rg_core.model.base`, `rg_core.model.enums`, `rg_core.serial` (canonical JSON, digests, schema registry, JSON Schema export, `IdFactory`, `Secret`/`SecretHandle`, shape detectors). Pure Python + pydantic v2; **no I/O** (NFR-MNT-001): file writing of `schemas/` is done by the dev tool `tools/rgschemas.py` that wraps these functions.

## 1. Module identifier and name

| Item | Value |
|---|---|
| Element | RG-P03-002 — Shared schema and serialization framework |
| Module id | `MOD-CORE-SCHEMA_SERIALIZATION` |
| Python packages | `rg_core.model.base` (base classes, scalar types), `rg_core.model.enums` (frozen enums of DATA-MODEL §3), `rg_core.serial` (`canonical`, `digest`, `registry`, `jsonschema`, `ids`, `secret`, `shapes`, `limits`) |
| Distribution | `revocationgap-core` (depends on `pydantic` only; pin `pydantic>=2.14,<2.15`, quarterly bump per ADR-0007) |
| Interfaces owned | `IF-CORE-SERIAL` (this spec defines `SchemaRegistry`, `IdFactory`, `canonical_json`/`digest` functions, `Secret`, `SecretHandle`, `Model`/`Document` conventions) |
| Schemas owned | `SCH-SERIAL` (registry manifest `schemas/index.json`, exported JSON Schema file layout, id grammar, `ValidationIssue`) |
| Consumers | every spec that defines a persisted/exported model (SCH-*), RG-P03-003 (config digest, handle syntax, shape detectors), RG-P03-004 (shape detectors, `Secret`), RG-P03-008 (canonical bytes, digests), RG-P08-001 (hash-chain primitive), RG-P11-001 (`SecretResolver` returns `Secret`) |

## 2. Phase and requirement references

Phase 03 (architecture/platform). Requirements realised or verified here:

| Requirement | How this module realises it |
|---|---|
| FR-EXP-001 | `digest(spec_json, domain="rg.spec.v1")` over canonical JSON gives the **spec digest** recorded in the run manifest; secret-freeness is enforced by `Secret` non-serialisability and the model-conformance rules (§9). |
| FR-EVD-002 | Persisted derived records are written as canonical bytes, so recomputation reproduces them byte-for-byte (INV-3, TST-RG-P03-002-02). |
| FR-EVD-003 | `Provenance` mixin carries exactly one `derivation` per record and `produced_by`. |
| FR-EVD-004 / FR-EVD-007 | `chain_digest()` and `digest()` are the primitives for the evidence hash chain and manifest digest; their algorithm is frozen here (RG-P08-001 owns the chain semantics). |
| FR-OPS-003, NFR-MNT-005 | `schema_version` semantics, migration hooks, newer-major refusal, schema compatibility classifier. |
| FR-SEC-005 | `Secret` and `SecretHandle`: no repr/str/format/pickle/serialise; inline-secret shape detectors for configuration rejection. |
| FR-SEC-009 | Bounds rule: every string, array, map and integer in an exported schema is bounded; strict JSON parsing limits (size, depth). |
| FR-RPT-008, NFR-REL-002 | Deterministic bytes: canonical JSON, sorted sets, id determinism under virtual clock. |
| FR-EXT-004 | `rg_core` stays importable with pydantic as the only third-party dependency. |
| NFR-MNT-002, NFR-MNT-003 | Typed API under mypy `--strict`; JSON Schemas generated and golden-tested. |
| NFR-TEST-004 | Test ids `TST-RG-P03-002-NN` cited by ACs in §24. |

Threat/validity items: **TM-07** (typed secret that cannot be serialised, logged or formatted), **TM-14** (no pickle/unsafe loaders; strict JSON parser; control characters stripped), **TM-15** (untrusted record parsing with limits), **TM-26** (digest primitives), **TM-34** (bounded sizes), **TV-20** (versioned manifests), **SC-05** (determinism), **SC-07** (Secret hygiene, together with RG-P03-004). Workflows touched: all (every WF reads/writes models).

## 3. Purpose and user/security value

Every other element defines models; this element makes them behave identically. It supplies (a) one base class with strict, frozen, `extra="forbid"` semantics and secret-safe validation errors, (b) one canonical byte representation so that digests, evidence chains and reports are reproducible across platforms, Python versions and hash seeds, (c) one place that decides what versions mean and how old documents are migrated, (d) one id generator that is deterministic under the virtual clock, and (e) the `Secret` type that makes credential leakage a type error rather than a review finding.

Security value: pydantic's default `ValidationError` text includes the offending input value; with a token in a mistyped field this would leak it into logs. The base class disables that (`hide_input_in_errors=True`) and every conversion to `RgError` drops inputs. `Secret` has no path to a string, a pickle or a JSON document except the audited `reveal()` call.

## 4. Explicit responsibilities

- **RESP-1** Provide `Model` (frozen, strict, forbid-extra, input-hiding) and `Document(Model)` (adds `schema_version`), plus `Provenance` mixin (`derivation`, `produced_by`).
- **RESP-2** Provide scalar/constraint types: `Int64`, `SafeInt`, `Count`, `SortedSet[T]`, text tiers (`Label`, `Slug`, `ShortText`, `LongText`), typed entity ids (`ExpId`, …), `ExtKind[E]`, `SecretHandle`, `Sha256Digest`.
- **RESP-3** Implement the canonical JSON encoder (`canonical_json`, `canonical_bytes`), strict JSON parser (`parse_json`), domain-separated `digest()` and `chain_digest()`.
- **RESP-4** Implement `SchemaRegistry`: document registry, polymorphic record families (discriminated by `kind`), version checks, migration chain, conformance checks at registration, freeze.
- **RESP-5** Implement JSON Schema export (`export_schemas`) with deterministic output, the `schemas/` layout, the golden-file check and the compatibility classifier used to decide minor vs major bumps.
- **RESP-6** Implement `IdFactory(clock, rng)` (ULID, monotonic within a millisecond) and id parse/validate helpers with the frozen prefixes of DATA-MODEL §2.1.
- **RESP-7** Implement `Secret` (+ `fingerprint_of`) and `SecretHandle` grammar/parsing; guarantee non-serialisability.
- **RESP-8** Implement `rg_core.serial.shapes`: pure detectors for inline-credential shapes (JWT, `Bearer`/`Basic` values, PEM private keys, URL userinfo, high-entropy values under secret-named keys) used by RG-P03-003 (config rejection) and reused by RG-P03-004.
- **RESP-9** Implement `rg_core.model.enums` verbatim from DATA-MODEL §3 and keep it in sync by a doc-sync test.
- **RESP-10** Define the module's error codes (§7.9) and map pydantic validation errors to `RgError` without input values.

## 5. Out-of-scope responsibilities

| Excluded item | Owner |
|---|---|
| Field-level schemas of domain entities (`TimeInstant`, `Credential`, `Observation`, …) | the SCH-* owners in DATA-MODEL §8 (RG-P02-001 … RG-P11-002) |
| `RgError` class, error-code registry and `ErrorCode` allocation rules | RG-P03-005 (this spec only *uses* its blocks 0020–0039) |
| Redaction rules beyond shape detection; log formatting | RG-P03-004 |
| Reading `secret:` handles, keyring/env/file resolvers, `SecretResolver` | RG-P11-001 (must call `fingerprint_of` from this spec) |
| Configuration files, layering, unknown-key policy | RG-P03-003 |
| SQLite/blob persistence, evidence chain semantics, atomic file writes of schema files | RG-P03-008 / RG-P08-001; `tools/rgschemas.py` writes `schemas/` (dev tool) |
| Workspace backup and applying migrations to a store | RG-P11-006 (this spec only defines the pure per-document migration hook) |
| Hypothesis strategies (they import `hypothesis`, forbidden inside packages) | `tests/support/strategies.py` of each owner; shared primitives in RG-P12-002 |

## 6. Dependencies and prerequisites

* Specs: RG-P03-001 frozen contracts (DATA-MODEL §1, §2.1, §2.4, §3; INTERFACE-CONTRACTS `Clock`, `SecretResolver`). `IF-CORE-ERR` (RG-P03-005) supplies `RgError`; the dependency is by interface only (registry says RG-P03-002 depends on RG-P03-001); `rg_core.errors.core` (the `RgError` classes, stdlib-only) is a leaf module imported by `rg_core.model.base` and `rg_core.serial`, while `rg_core.errors.record` (which needs `Model`) is imported only by consumers, so there is no import cycle.
* Libraries: `pydantic` 2.14.x (MIT) with `pydantic-core` wheels on Windows/Linux/macOS; stdlib `unicodedata`, `hashlib`, `hmac`, `threading`, `re`, `json`, `decimal`, `base64`, `secrets`. Dev/test only: `hypothesis`, `pytest` (never imported by packages; SC-08).
* Python: 3.11–3.14 (ADR-0002). `from __future__ import annotations` is **not** used in modules that define pydantic models.
* Environment: none (no filesystem, no network, no clock reads except through the injected `Clock`).

## 7. External and internal interfaces

### 7.1 Base classes and scalar types (`rg_core.model.base`)

```python
class Model(BaseModel):
    model_config = ConfigDict(
        frozen=True, extra="forbid", strict=True, allow_inf_nan=False,
        hide_input_in_errors=True, validate_default=True, use_enum_values=False,
        populate_by_name=False, arbitrary_types_allowed=False, revalidate_instances="never")

class Document(Model):                       # every persisted/exported top-level record
    SCHEMA_ID: ClassVar[str]                 # snake_case, e.g. "experiment_spec"
    SCHEMA_VERSION: ClassVar[tuple[int, int]]  # (major, minor) this code writes and reads up to
    schema_version: SchemaVersion            # str, pattern ^(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})$

class ProducedBy(Model):  component: Label; version: ShortText
class Provenance(Model):  derivation: Derivation; produced_by: ProducedBy      # mixin (multiple inheritance with Document)

Int64      = Annotated[int, _Int64]       # python mode: int; JSON mode: decimal string ^-?[0-9]+$, |v|<=2**63-1
SafeInt    = Annotated[int, Field(ge=-(2**53-1), le=2**53-1)]
Count      = Annotated[int, Field(ge=0, le=2**53-1)]
SortedSet  = Annotated[frozenset[T], _SortedSerializer]       # JSON array sorted by canonical order
Label      = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$", max_length=64)]
Slug       = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,63}$", max_length=64)]
ShortText  = Text(max_length=256, multiline=False)        # factory returns Annotated[str, ...]
LongText   = Text(max_length=4096, multiline=True)
Sha256Digest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$", max_length=71)]
ExtKind[E] = Union[E, ExtensionKind]; ExtensionKind = Annotated[str, Field(pattern=r"^x\.[a-z0-9][a-z0-9-]{0,30}\.[a-z][a-z0-9_]{0,62}$", max_length=100)]
```

Typed entity ids: `ExpId, ScnId, PrvId, TgtId, IdnId, CrdId, AttId, ObsId, EvdId, FndId, DrvId, RevId, PrbId, TlnId, RptId, AudId` = `Annotated[str, Field(pattern=r"^<prefix>_[0-7][0-9A-HJKMNP-TV-Z]{25}$", max_length=30)]` for the prefixes of DATA-MODEL §2.1. The first ULID character is limited to `0–7` because 26 Crockford characters carry 130 bits and a ULID has 128.

### 7.2 Canonical JSON and digests (`rg_core.serial.canonical`)

```python
JsonValue = None | bool | int | float | str | Sequence["JsonValue"] | Mapping[str, "JsonValue"]

def canonical_json(value: JsonValue) -> str: ...                    # sync, pure; raises RgError RGE-INTERNAL-0021
def canonical_bytes(value: JsonValue) -> bytes: ...                 # canonical_json(value).encode("utf-8")
def to_json_value(doc: Model) -> dict[str, JsonValue]: ...          # doc.model_dump(mode="json", exclude_none=True, by_alias=False)
def dump_document(doc: Model) -> bytes: ...                         # canonical_bytes(to_json_value(doc)); the ONLY persisted form
def parse_json(data: bytes | str, *, limits: ParseLimits = DEFAULT_LIMITS) -> JsonValue: ...   # strict; raises RGE-STORE-0025/0026
def digest(value: JsonValue | bytes, *, domain: DigestDomain) -> Sha256Digest: ...
def chain_digest(prev: Sha256Digest | None, record: JsonValue, *, domain: Literal["rg.chain.v1"] = "rg.chain.v1") -> Sha256Digest: ...
def fingerprint_of(material: bytes) -> str: ...                     # "fp:" + sha256(material).hexdigest()[:12]
DigestDomain = Literal["rg.spec.v1", "rg.chain.v1", "rg.report.v1", "rg.config.v1", "rg.scope.v1"]
class ParseLimits(NamedTuple): max_bytes: int; max_depth: int; max_items: int   # DEFAULT_LIMITS = (16 MiB, 64, 1_000_000)
```

All functions are synchronous, pure, thread-safe, idempotent. `digest` of a `JsonValue` hashes `domain.encode() + b"\n" + canonical_bytes(value)`; of `bytes` hashes `domain.encode() + b"\n" + data` (used by evidence blobs only when a domain-separated digest is wanted; **content-addressed blob keys are the plain `sha256(data)` hex** owned by RG-P03-008 and are not produced by `digest`). `chain_digest(prev, record)` = `sha256(b"rg.chain.v1\n" + (prev or "sha256:" + "0"*64).encode() + b"\n" + canonical_bytes(record))`.

### 7.3 Schema registry (`rg_core.serial.registry`)

```python
class Migration(NamedTuple):
    schema_id: str; from_major: int; to_major: int       # to_major == from_major + 1
    fn: Callable[[dict[str, Any]], dict[str, Any]]       # pure, deterministic, no I/O, no clock; receives a deep copy

class SchemaRegistry:                                    # explicit object, no module-level singleton
    def register_document(self, model: type[Document]) -> None
    def declare_family(self, family: str, *, discriminator: str = "kind") -> None
    def register_record(self, family: str, kind: str, model: type[Document]) -> None   # kind: snake_case or "x.<vendor>.<name>"
    def add_migration(self, m: Migration) -> None
    def freeze(self) -> None                             # after freeze every register_*/add_* raises RGE-INTERNAL-0024
    def load_document(self, schema_id: str, raw: Mapping[str, Any]) -> Document
    def load_record(self, family: str, raw: Mapping[str, Any]) -> Document
    def loads_document(self, schema_id: str, data: bytes | str, *, limits: ParseLimits = DEFAULT_LIMITS) -> Document
    def loads_record(self, family: str, data: bytes | str, *, limits: ParseLimits = DEFAULT_LIMITS) -> Document
    def check_document(self, schema_id: str, raw: Mapping[str, Any]) -> ValidationReport   # non-raising, for config/UX
    def json_schemas(self) -> Mapping[tuple[str, str], dict[str, Any]]    # (schema_id, "major.minor") → JSON Schema
    def schema_ids(self) -> Sequence[str]
class ValidationIssue(Model): loc: Annotated[tuple[str | int, ...], Field(max_length=32)]; type: Label; message: ShortText   # never contains the input value
class ValidationReport(Model): ok: bool; issues: Annotated[tuple[ValidationIssue, ...], Field(max_length=200)]
```

Raised: `RGE-STORE-0020…0026`, `RGE-INTERNAL-0024` (§7.9). Concurrency: registration is single-threaded at composition; after `freeze()` the registry is read-only and safe for concurrent use from any thread. Idempotency: `register_*` of the identical class twice is a no-op; a different class for the same key raises `RGE-INTERNAL-0024`.

### 7.4 IdFactory (`rg_core.serial.ids`)

```python
IdPrefix = Literal["exp","scn","prv","tgt","idn","crd","att","obs","evd","fnd","drv","rev","prb","tln","rpt","aud"]
class RandomSource(Protocol): def randbits(self, k: int) -> int: ...        # secrets.SystemRandom().randbits in production; random.Random(seed) or scripted in tests
class ParsedId(NamedTuple): prefix: IdPrefix; ulid: str; timestamp_ms: int
class IdFactory:                                          # part of IF-CORE-SERIAL
    def __init__(self, clock: Clock, rng: RandomSource) -> None
    def new(self, prefix: IdPrefix) -> str                # "<prefix>_<ULID>"; sync; thread-safe (internal lock); raises RGE-INTERNAL-0022/0023
    def new_ulid(self) -> str
    @staticmethod
    def parse(value: str) -> ParsedId                     # raises RGE-CONFIG-0022
```

### 7.5 Secrets (`rg_core.serial.secret`)

```python
class Secret:                                             # final; __slots__ = ("_v",); class attribute __secret__ = True (marker honoured by RgError.details sanitising, RG-P03-005 rule E2)
    def __init__(self, value: str | bytes) -> None        # empty value allowed only for bytes b"" (placeholder), see §9
    def reveal(self) -> str                               # UTF-8 decode of bytes; the audited exit
    def reveal_bytes(self) -> bytes
    def fingerprint(self) -> str                          # fingerprint_of(reveal_bytes())
    def wipe(self) -> None                                # zero the internal bytearray; later reveal() raises RGE-INTERNAL-0020
    # __repr__/__str__/__format__ → "<Secret>"; __eq__ constant-time vs Secret only; __hash__ = None
    # __reduce__/__reduce_ex__/__getstate__/__setstate__/__bytes__/__iter__/__len__ → raise SecretMisuseError (RGE-INTERNAL-0020)
    # __copy__ / __deepcopy__ → return self (immutable)

@dataclass(frozen=True) class SecretHandleRef: resolver: str; name: str
SecretHandle = Annotated[str, Field(pattern=r"^secret:[a-z][a-z0-9_-]{0,31}:[^\x00-\x1f\x7f]{1,512}$", max_length=552)]
def parse_secret_handle(value: str) -> SecretHandleRef        # raises RGE-CONFIG-0020 (message never echoes the value)
```

pydantic integration: `Secret` fields are declared `Annotated[Secret, SecretField]` with `exclude=True`; a `Secret` in a *non-excluded* field makes `model_dump*` raise (converted by `to_json_value` to `SecretMisuseError`); JSON-Schema generation for such a field emits `{"x-rg-secret": true}`; the registry refuses to register a `Document` having a non-excluded `Secret` field (RGE-INTERNAL-0024).

### 7.6 Shape detectors (`rg_core.serial.shapes`)

```python
class SecretShape(Enum): JWT; BEARER_VALUE; BASIC_VALUE; PEM_PRIVATE_KEY; URL_USERINFO; KEYED_HIGH_ENTROPY
def find_secret_shape(text: str, *, key: str | None = None) -> SecretShape | None     # pure, O(len), never returns the matched text
SECRET_KEY_NAME = re.compile(r"(?i)(pass(word|wd)?|secret|token|api[_-]?key|credential|private[_-]?key|authorization|cookie|session[_-]?id)")
```

### 7.7 JSON Schema export (`rg_core.serial.jsonschema`)

```python
def export_schemas(registry: SchemaRegistry, *, extra: Mapping[tuple[str, str], dict[str, Any]] | None = None) -> Mapping[str, bytes]   # relpath → file bytes (LF, UTF-8, trailing newline); `extra` carries schemas produced by other registries, e.g. RG-P03-003's `config_document`
def check_golden(registry: SchemaRegistry, committed: Mapping[str, bytes]) -> GoldenReport   # missing / extra / changed files with unified diffs
def classify_change(old: dict[str, Any], new: dict[str, Any]) -> Literal["identical","additive","breaking"]
```

CLI wrapper (dev tool, outside packages): `python tools/rgschemas.py --check | --write`.

### 7.8 Enums (`rg_core.model.enums`)

`ClockKind, OutcomeClass, PolicyProfile, ProbeOutcome, ProbeCategory, ProbeKind, ControlKind, CredentialType, CredentialFormat, SenderBinding, ValidationMode, RevocationKind, AckState, ActionClass, Derivation, ConfidenceLevel, ExperimentState` — all `str, Enum`, values exactly those of DATA-MODEL §3. `RevocationKind` fields in models are typed `ExtKind[RevocationKind]`.

### 7.9 Error codes (block 0020–0039; see RG-P03-005 §8 for the registry rule)

| Code | Name | Retryable | Raised when |
|---|---|---|---|
| `RGE-STORE-0020` | SCHEMA_VALIDATION_FAILED | no | persisted/imported document fails model validation (`details.issues` = ≤200 `ValidationIssue`, no inputs) |
| `RGE-STORE-0021` | SCHEMA_UNKNOWN_KIND | no | `load_record` finds a discriminator value or family that is not registered |
| `RGE-STORE-0022` | SCHEMA_VERSION_UNSUPPORTED | no | document major > supported major, or same major with minor > supported minor, or malformed version |
| `RGE-STORE-0023` | SCHEMA_MIGRATION_MISSING | no | document major < supported major and no migration chain exists |
| `RGE-STORE-0024` | SCHEMA_MIGRATION_FAILED | no | hook raised, mutated its input, or produced a document that fails validation |
| `RGE-STORE-0025` | DOCUMENT_LIMIT_EXCEEDED | no | bytes/depth/item limit of `ParseLimits` exceeded |
| `RGE-STORE-0026` | JSON_INVALID | no | syntax error, duplicate key, `NaN`/`Infinity` constant, BOM, lone surrogate, non-object root where an object is required |
| `RGE-INTERNAL-0020` | SECRET_MISUSE | no | `Secret` repr-escape attempts: pickle, serialisation, iteration, `bytes()`, reveal after wipe |
| `RGE-INTERNAL-0021` | CANONICAL_UNREPRESENTABLE | no | value cannot be canonicalised (§12.1 rules R1–R7) |
| `RGE-INTERNAL-0022` | ID_PREFIX_UNKNOWN | no | `IdFactory.new` with a prefix outside the frozen table |
| `RGE-INTERNAL-0023` | ID_COUNTER_OVERFLOW | no | 2⁸⁰ ids requested within one millisecond |
| `RGE-INTERNAL-0024` | SCHEMA_REGISTRATION_CONFLICT | no | duplicate key, registration after freeze, or conformance rule C1–C9 violated |
| `RGE-CONFIG-0020` | SECRET_HANDLE_INVALID | no | handle does not match the grammar |
| `RGE-CONFIG-0022` | ID_INVALID | no | id string fails the grammar of §7.1 |

## 8. Data structures and schemas

### 8.1 `schemas/` layout and `index.json` (SCH-SERIAL)

```
schemas/
  index.json                                   # manifest, canonical JSON, sorted by schema_id then version
  <schema_id>/<major>.<minor>.schema.json      # JSON Schema 2020-12, serialization mode, one file per supported version
  _families/<family>.schema.json               # oneOf over registered kinds (discriminator "kind")
```

| Field of `index.json` | Type | Constraint | Description |
|---|---|---|---|
| `schema_version` | `SchemaVersion` | `"1.0"` | version of the index format |
| `generator` | object | `{"pydantic": "2.14.1", "rg_core": "<version>"}` | tool versions that produced the files (informational; excluded from golden diff) |
| `documents[]` | array ≤ 2000 | sorted | one entry per `(schema_id, version)` |
| `documents[].schema_id` | `Slug` | unique with version | e.g. `experiment_spec` |
| `documents[].version` | `SchemaVersion` | — | e.g. `"1.0"` |
| `documents[].path` | `ShortText` | relative, `/` separators | file path |
| `documents[].sha256` | `Sha256Digest` | plain sha256 of the file bytes | tamper/diff aid |
| `documents[].model` | `ShortText` | dotted import path | e.g. `rg_core.model.experiment.ExperimentSpec` |
| `families[]` | array | — | `{family, discriminator, kinds[]: {kind, schema_id}}` |

Example (complete; the `sha256` value is illustrative):

```json
{"documents":[{"model":"rg_core.model.example.ExampleDoc","path":"example_doc/1.0.schema.json","schema_id":"example_doc","sha256":"sha256:0b8e1f3a5d6c7e9f0a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f6071","version":"1.0"}],"families":[{"discriminator":"kind","family":"timeline_entry","kinds":[{"kind":"state_transition","schema_id":"timeline_state_transition"}]}],"generator":{"pydantic":"2.14.1","rg_core":"0.1.0"},"schema_version":"1.0"}
```

Each exported file has `$schema = https://json-schema.org/draft/2020-12/schema`, `$id = urn:rg:schema:<schema_id>:<major>.<minor>`, `title` = class name, `additionalProperties: false` on every object, and extension keywords `x-rg-format: "int64"` (Int64), `x-rg-secret` (excluded Secret fields; never present in registered documents), `x-rg-unbounded: "<justification>"` (only for fields the owner explicitly exempts, §9 rule C7).

### 8.2 Id grammar

`<prefix>_<ULID>`, ULID = 26 Crockford base32 characters from `0123456789ABCDEFGHJKMNPQRSTVWXYZ`, first character `0–7`, upper-case only. Total length 30. Parsing is case-sensitive (lower-case ids are rejected, not normalised).

### 8.3 Version grammar

`schema_version = "<major>.<minor>"`, both decimal without leading zeros (except `0`), each ≤ 9999. `SCHEMA_VERSION=(1,2)` means the code writes `"1.2"` and reads `1.0…1.2` of major 1 and migrates majors `< 1`.

### 8.4 Text policies

| Type | Max (Unicode code points) | Newlines | Notes |
|---|---|---|---|
| `Label` | 64 | no | ASCII pattern; identifiers/names |
| `Slug` | 64 | no | lower-case ASCII pattern |
| `ShortText` | 256 | no | free text; cleaned per §10.4 |
| `LongText` | 4096 | `\n` only | free text; CRLF/CR normalised to `\n` |
| `Text(max_length=N, multiline=…)` | N ≤ 65 536 | per flag | factory for other bounds; N > 4096 requires a justification comment checked in review |

## 9. Inputs, outputs, and validation rules

Conformance rules checked by `register_document`/`register_record` (violation → `RGE-INTERNAL-0024`, `details.rule = "C<n>"`, `details.field`):

| Rule | Check |
|---|---|
| C1 | model derives from `Document` and `SCHEMA_ID`, `SCHEMA_VERSION` are set; `schema_id` matches `^[a-z][a-z0-9_]{0,63}$` |
| C2 | `schema_version` field present and not overridden with a different type |
| C3 | every `set`/`frozenset` annotation is `SortedSet`; every `float` is finite (inherited config) |
| C4 | no bare `int` annotation: each integer is `Int64`, `SafeInt` or `Count` (or carries explicit `ge`/`le` within ±(2⁵³−1)) |
| C5 | no `datetime`, `date`, `time`, `timedelta`, `Decimal`, `bytes`, `Path`, `Any`, `object` annotations (time is `TimeInstant`/`Int64` ns; paths are `ShortText`; bytes are digests/refs) |
| C6 | no non-excluded `Secret` field |
| C7 | exported serialization schema: every `type: string` without `enum`/`const` has `maxLength`; every `type: array` has `maxItems`; every `type: object` with `additionalProperties` other than `false` has `maxProperties`; every `type: integer` has `minimum` and `maximum`; exemption only via `x-rg-unbounded` |
| C8 | discriminated unions use field name `kind` with `Literal[...]` values matching `^[a-z][a-z0-9_]{0,62}$` or an `x.<vendor>.<name>` extension kind registered in the family |
| C9 | every `RevocationKind`-typed field is `ExtKind[RevocationKind]`; every other open vocabulary uses `ExtKind[<Enum>]` (never bare `str`) |

Runtime validation rules for inputs (numbered; each names its code):

| Rule | Input | Rule text | Code |
|---|---|---|---|
| V1 | JSON text | UTF-8, no BOM, no duplicate keys, no `NaN`/`Infinity`/`-Infinity`, no lone surrogates | RGE-STORE-0026 |
| V2 | JSON text | `len(bytes) ≤ max_bytes`, nesting ≤ `max_depth`, total containers+scalars ≤ `max_items` (defaults 16 MiB / 64 / 1 000 000; callers may tighten, never loosen above 64 MiB) | RGE-STORE-0025 |
| V3 | raw document | `schema_version` present, grammar §8.3 | RGE-STORE-0022 |
| V4 | raw document | `(major, minor) ≤ SCHEMA_VERSION` after migration | RGE-STORE-0022 |
| V5 | raw document | model validation passes (strict, extra forbid) | RGE-STORE-0020 |
| V6 | record | discriminator present and registered | RGE-STORE-0021 |
| V7 | canonicalisation | rules R1–R7 of §12.1 | RGE-INTERNAL-0021 |
| V8 | id string | grammar §8.2 and prefix ∈ frozen table | RGE-CONFIG-0022 |
| V9 | handle string | grammar of `SecretHandle` | RGE-CONFIG-0020 |
| V10 | `IdFactory.new(prefix)` | prefix ∈ frozen table | RGE-INTERNAL-0022 |

Outputs: `dump_document` returns canonical UTF-8 bytes; `export_schemas` returns file bytes; every raised error is an `RgError` (never a bare `ValidationError`, `ValueError`, `TypeError`, `pickle.PicklingError`).

## 10. Detailed execution behavior

### 10.1 Writing a document (clock: none)
1. Caller constructs a `Document` (validated, frozen). 2. `dump_document(doc)`: `to_json_value` → `model_dump(mode="json", exclude_none=True)`; pydantic serialisers emit `Int64` as decimal strings, `SortedSet` as sorted arrays, enums as values. A `PydanticSerializationError` caused by a `Secret` is converted to `SecretMisuseError`. 3. `canonical_bytes` (§12.1). 4. Caller persists the bytes (store, bundle) or hashes them (`digest`). No clock is read.

### 10.2 Reading a document
1. `loads_document(schema_id, data)`: `parse_json` with limits (V1, V2). 2. Root must be an object with `schema_version` (V3). 3. If `major < SCHEMA_VERSION.major`: apply migrations `major → major+1 …` (each on a deep copy; the output is re-checked for a valid version string ≥ `"{to_major}.0"`), else if `major > …` raise 0022. 4. If `minor > SCHEMA_VERSION.minor` raise 0022 (RevocationGap refuses data written by a newer minor because `extra="forbid"`; the message names both versions). 5. Validate with `model_validate_json(canonical_bytes(raw))` — not `model_validate(raw)` — so that the JSON-mode branch of `Int64` (decimal strings only) applies to data that came from JSON. 6. Failures → `RgError(STORE, 0020)` carrying issues without inputs.

### 10.3 Polymorphic records
`declare_family("timeline_entry")` then `register_record("timeline_entry", "state_transition", StateTransitionEntry)`. `load_record(family, raw)`: read `raw["kind"]` (must be `str`), look up the registered model, continue as §10.2. The exported `_families/<family>.schema.json` is `oneOf` of member schemas with `discriminator: {propertyName: "kind"}`. Plugin-provided kinds must be `x.<vendor>.<name>`; core kinds must not use the `x.` prefix.

### 10.4 Text cleaning (applies to `ShortText`, `LongText`, `Text`)
Order: (1) require `str` (strict) → (2) NFC → (3) remove `Cc` characters (single-line: all including `\t \n`; multiline: all except `\n`, after `\r\n`/`\r` → `\n`), remove U+2028/U+2029 (single-line), remove bidi controls U+200E, U+200F, U+061C, U+202A–U+202E, U+2066–U+2069 and U+FEFF → (4) reject lone surrogates → (5) length check on the cleaned value (over-length is **rejected**, never truncated; producers that must keep prefixes call `clip_text(value, max_length)` which appends `…[+N]` where N is the removed code-point count and still fits `max_length`). Zero-width joiner/non-joiner are kept (needed by several scripts); terminal exposure is handled by RG-P03-004's sanitiser.

### 10.5 Schema export and golden check
`export_schemas`: for every registered `(schema_id, version)` generate `model_json_schema(mode="serialization", schema_generator=RgJsonSchema)`; `RgJsonSchema` overrides: `Int64` → `{"type":"string","pattern":"^-?[0-9]+$","maxLength":20,"x-rg-format":"int64"}`; drops `title` of fields (keeps class title); sets `$schema`, `$id`; sorts keys; verifies rule C7; renders with `json.dumps(sort_keys=True, indent=2, ensure_ascii=False)` + `"\n"`. `check_golden` compares with committed bytes after normalising `\r\n` → `\n` **only to report** a `line_endings` hint (the comparison itself is byte-exact; `.gitattributes` marks `schemas/** text eol=lf`).

### 10.6 Id generation (clock: injected `Clock.wall_ns()`, one read per ULID)
See §12.3. Ids are issued by the composition root's single `IdFactory`; the factory is passed explicitly (no module-level state).

## 11. State transitions and invariants

`SchemaRegistry` lifecycle: `OPEN → FROZEN` (one-way).

| From | Event | To | Effect |
|---|---|---|---|
| OPEN | `register_*`, `add_migration` | OPEN | conformance checks run immediately |
| OPEN | `freeze()` | FROZEN | verifies that every `Migration` chain is contiguous from major 1 to `SCHEMA_VERSION.major` for each document; computes schemas |
| FROZEN | any `register_*` | FROZEN | raises `RGE-INTERNAL-0024` |
| FROZEN | `load_*`, `json_schemas` | FROZEN | allowed |

`IdFactory` internal state `(last_ms, last_rand)`: `(−1, 0)` → after each call `last_ms' = max(last_ms, now_ms)`; see INV-6.

Invariants:
- **INV-1** `canonical_bytes(parse_json(canonical_bytes(x))) == canonical_bytes(x)` for every representable `x` (idempotence).
- **INV-2** `canonical_bytes(x)` is independent of dict insertion order, `PYTHONHASHSEED`, platform, locale and Python version 3.11–3.14.
- **INV-3** For every registered document `d`: `loads_document(id, dump_document(d)) == d` and `dump_document(loads_document(id, b)) == b` when `b = dump_document(d)`.
- **INV-4** `dump_document` output never contains a `Secret` material substring and never contains a `null` value (None fields are omitted).
- **INV-5** Within one `IdFactory`, the sequence of ULIDs is strictly increasing in lexicographic order, regardless of wall-clock regressions.
- **INV-6** `timestamp_ms(new_ulid()) = max(previous timestamp_ms, floor(clock.wall_ns()/10⁶))`.
- **INV-7** No `ValidationError.input`/input value appears in any `RgError.message`, `RgError.details` or `ValidationIssue` produced by this module.
- **INV-8** `Secret` has no code path to `str`, `bytes`, pickle, JSON, `repr` or `%`/`format` except `reveal*()`.
- **INV-9** A registered document type is immutable: attribute assignment raises; `model_copy(update=…)` is forbidden by convention and flagged by `tests/lint` (new records reference predecessors).
- **INV-10** `export_schemas` is a pure function of the registry: two calls produce identical bytes; three runs with different `PYTHONHASHSEED` produce identical bytes.

## 12. Core algorithms and pseudocode

### 12.1 Canonical JSON (RFC 8785 style with RevocationGap restrictions)

Rules: **R1** `None→null`, `bool→true/false`. **R2** `int` allowed only if `|n| ≤ 2⁵³−1`, rendered base-10 without sign for zero/plus; larger magnitudes must already be strings (Int64) → else `RGE-INTERNAL-0021`. **R3** `float` must be finite; rendered by the ES6 `Number.toString` algorithm (§12.2); `-0.0 → 0`. **R4** `str` is NFC-normalised, must encode to UTF-8 (no lone surrogates), serialised with JSON escapes `\" \\ \b \f \n \r \t` and `\u00XX` (lower-case hex) for other code points < U+0020; everything else (including `/`, U+007F, U+2028, non-ASCII) is emitted literally. **R5** mapping keys must be `str`; keys are NFC-normalised first; two keys equal after NFC → error; keys sorted by the byte order of their UTF-16BE encoding (RFC 8785 §3.2.3), which differs from code-point order for supplementary characters. **R6** sequences keep order; tuples are sequences; `set` is rejected (models use `SortedSet`). **R7** no whitespace; separators `,` and `:`.

```
def canon(v):
  if v is None: return "null"
  if v is True: return "true"; if v is False: return "false"          # test bool before int
  if isinstance(v, int): require abs(v) <= 2**53-1 else raise 0021;  return str(v)
  if isinstance(v, float): require isfinite(v) else raise 0021;  return es6(v)
  if isinstance(v, str): s = NFC(v); s.encode("utf-8") (raise 0021 on surrogate); return json_escape(s)
  if isinstance(v, (list, tuple)): return "[" + ",".join(canon(x) for x in v) + "]"
  if isinstance(v, Mapping):
      d = {}
      for k, x in v.items():
          require isinstance(k, str) else raise 0021
          nk = NFC(k); require nk not in d else raise 0021; d[nk] = x
      keys = sorted(d, key=lambda k: k.encode("utf-16-be"))
      return "{" + ",".join(json_escape(k) + ":" + canon(d[k]) for k in keys) + "}"
  raise 0021
```

Worked example (test vector **V1**). Input (Python): `{"b":1, "a":[True, None, "\u00e9", "e\u0301"], "\U00010000":1, "\ue000":2, "n":0.5}`. Steps: both strings in `a` become U+00E9 after NFC; keys sorted by UTF-16BE bytes: `a` (0061) < `b` (0062) < `n` (006E) < U+10000 (D800 DC00) < U+E000 (E000) — code-point order would put U+E000 before U+10000, so this case distinguishes RFC 8785 order from naive `sorted()`. Canonical text: `{"a":[true,null,"é","é"],"b":1,"n":0.5,"𐀀":1,"":2}` (the last key is U+E000, private use). UTF-8 bytes SHA-256 = `9f51223aabe7c29af4f17a737ce9c366a08d474152d8929af9933b81c4a89157`; `digest(V1, domain="rg.spec.v1")` = `sha256:944adab9f5019c33e81f054ea97bd64e440222426c07ce450c50850141d7b029`.

### 12.2 ES6 float formatting

```
def es6(x):                        # x finite
  if x == 0: return "0"
  sign = "-" if x < 0 else ""; d = Decimal(repr(abs(x)))     # repr = shortest round-trip digits
  digits = strip_trailing_zeros(d.digits); k = len(digits)
  n = len(d.digits) + d.exponent                              # value = 0.<digits> × 10^n
  if k <= n <= 21:   s = digits + "0"*(n-k)
  elif 0 < n <= 21:  s = digits[:n] + "." + digits[n:]
  elif -6 < n <= 0:  s = "0." + "0"*(-n) + digits
  else:              e = n-1; s = digits[0] + ("." + digits[1:] if k > 1 else "") + "e" + ("+" if e>=0 else "-") + str(abs(e))
  return sign + s
```

| Input | Output | Why |
|---|---|---|
| `1.0` | `1` | integral float prints without fraction |
| `100.0` | `100` | — |
| `0.1` | `0.1` | — |
| `1e16` | `10000000000000000` | Python `repr` would give `1e+16`; ES6 keeps decimal up to 10²¹ |
| `1e21` | `1e+21` | n = 22 > 21 → exponent form |
| `1.5e-7` | `1.5e-7` | n = −6 → exponent form (Python gives `1.5e-07`) |
| `1e-6` | `0.000001` | n = −5 |
| `5e-324` | `5e-324` | smallest subnormal |
| `-0.0` | `0` | sign of zero dropped |
| `12345678.9` | `12345678.9` | — |

### 12.3 ULID generation

```
ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
def new_ulid(self):
  with self._lock:
    ms = self._clock.wall_ns() // 1_000_000
    require 0 <= ms < 2**48
    if ms > self._last_ms:  self._last_ms = ms;  self._last_rand = self._rng.randbits(80)
    else:                   self._last_rand += 1;  require self._last_rand < 2**80 else raise 0023   # ms <= last_ms: same ms or clock stepped back
    n = (self._last_ms << 80) | self._last_rand
  return encode_base32_26(n)          # big-endian 5-bit groups, 26 characters, first char 0-7
```

The RNG is consulted only when the millisecond advances; same-millisecond calls increment. Deterministic replay therefore needs the same call sequence, which the virtual lab guarantees (ADR-0014).

Worked example (scripted RNG returning `0x0123456789ABCDEF0123`, then `0xFFFFFFFFFFFFFFFFFFFF`; virtual `wall_ns = 1791796800123456789` → ms `1791796800123`):

| Call | `wall_ns` | Action | Result ULID |
|---|---|---|---|
| 1 | 1791796800123456789 | new ms → draw #1 | `01M4QPJTKV04HMASW9NF6YY093` |
| 2 | 1791796800123456789 | same ms → +1 | `01M4QPJTKV04HMASW9NF6YY094` |
| 3 | 1791796800124456789 | ms advanced → draw #2 | `01M4QPJTKWZZZZZZZZZZZZZZZZ` |
| 4 | 1791796800124456789 | same ms → +1 overflows 2⁸⁰ | raises `RGE-INTERNAL-0023` |

A wall-clock step back by 5 ms between calls 1 and 2 would still yield `…YY094` with the same timestamp prefix (INV-5/6).

### 12.4 Encoded forms of a secret
`Secret` deliberately offers no `encodings()` method (it would hand out derived material). The canary-registry algorithm that computes base64/URL/hex forms is specified in RG-P03-004 §12.2 and calls `reveal_bytes()` only inside the redactor.

### 12.5 Schema compatibility classifier
`classify_change(old, new)` walks both schemas: **breaking** if any property is removed, any `required` entry is added, any `type` changes, `enum` loses a member, a bound tightens (`maxLength`/`maxItems`/`maximum` decreases, `minimum` increases), `pattern` changes, `additionalProperties` changes, a `const` changes, or a `oneOf` member is removed; **additive** if only optional properties/enum members/`oneOf` members are added or bounds loosen; otherwise **identical**. CI rule: additive ⇒ minor bump required; breaking ⇒ major bump plus a registered `Migration`; identical with a changed `SCHEMA_VERSION` ⇒ error. Example: old `{"properties":{"a":{"type":"string","maxLength":64}},"required":["a"]}` → new adds optional `b` ⇒ `additive`; new sets `maxLength: 32` ⇒ `breaking`.

## 13. Internal functions, methods, or service operations

| Function | Signature | Purpose |
|---|---|---|
| `_es6_float` | `(x: float) -> str` | §12.2 |
| `_json_escape` | `(s: str) -> str` | R4 escapes |
| `_clean_text` | `(s: str, *, multiline: bool) -> str` | §10.4 steps 2–4 |
| `clip_text` | `(s: str, max_length: int) -> str` | public helper for producers (truncation with `…[+N]`) |
| `_encode_ulid` | `(n: int) -> str` | 130-bit big-endian base32 |
| `_walk_schema` | `(schema: dict) -> Iterator[tuple[str, dict]]` | rule C7 traversal and classifier |
| `_issues_from_validation_error` | `(e: ValidationError) -> tuple[ValidationIssue, ...]` | uses `e.errors(include_input=False, include_url=False, include_context=False)`; truncates to 200; `message` is the pydantic `msg` cleaned to `ShortText` |
| `_apply_migrations` | `(raw: dict, schema_id: str, target_major: int) -> dict` | deep-copies, applies chain, verifies each step |
| `_check_conformance` | `(model: type[Document]) -> None` | rules C1–C9 |
| `SecretField` | `Annotated` marker | `core_schema.is_instance_schema(Secret)` with a serializer that raises, JSON-Schema override `{"x-rg-secret": true}` |
| `_Int64`, `_SortedSerializer` | pydantic schema hooks | `json_or_python_schema`; sorted list serialiser (sort key = canonical text of each element) |

## 14. Error handling and failure recovery

| Failure | Detection | Handling | Recovery | Code |
|---|---|---|---|---|
| Malformed JSON / duplicate key | `parse_json` (object_pairs_hook rejects duplicates; `parse_constant` rejects NaN) | raise, nothing partially returned | caller reports corrupted/untrusted record | RGE-STORE-0026 |
| Oversized/deep document | byte count before parse; depth counter in hook | raise before allocation of full structure where possible | caller refuses import (TM-15) | RGE-STORE-0025 |
| Validation failure | `ValidationError` | convert, strip inputs | none (data bug); store layer marks record corrupt | RGE-STORE-0020 |
| Unknown kind | missing registry entry | raise | plugin not loaded → caller reports plugin id from kind prefix | RGE-STORE-0021 |
| Newer version | version compare | raise with both versions | upgrade RevocationGap | RGE-STORE-0022 |
| Missing/failed migration | chain gap / exception / validation | raise; input untouched | restore workspace backup (RG-P11-006) | RGE-STORE-0023/0024 |
| Secret serialisation attempt | `PydanticSerializationError` / `__reduce__` | raise `SecretMisuseError`; never include value | fix the caller (bug); no data written | RGE-INTERNAL-0020 |
| Non-canonicalisable value | R1–R7 | raise; names the JSON path | fix producer (e.g. int > 2⁵³ must be `Int64`) | RGE-INTERNAL-0021 |
| Registration conflict | conformance checks | raise at composition → process start fails | fix model definition | RGE-INTERNAL-0024 |
| Clock regression | `ms <= last_ms` | continue with increment (not an error) | — | — |
| ID overflow | counter ≥ 2⁸⁰ | raise | wait one millisecond is *not* offered (would read the clock); caller retries after the clock advances | RGE-INTERNAL-0023 |

Partial-failure semantics: all operations are all-or-nothing and side-effect-free; `export_schemas` returns either the complete file map or raises (no partial map).

## 15. Security requirements and trust boundaries

* **Trust boundary:** every `loads_*` input is untrusted (store contents after tampering, imported bundles — TM-15, config-embedded documents, plugin records). Parsing is strict (V1/V2), schema-validated, never `pickle`/`eval`/YAML.
* **TM-07 / SC-07:** `Secret` — fixed placeholder for `repr/str/format`, no pickling (`__reduce_ex__` raises), no hashing, no iteration, no length, constant-time equality, `wipe()`; `Model` hides inputs in validation errors; `to_json_value` fails closed on a `Secret` in an included field; registry rejects such models (C6). Fingerprints (`fp:`+12 hex of SHA-256) are the only derived value that may be stored; for **low-entropy secrets** (passwords) a 48-bit truncated hash is dictionary-attackable — RG-P03-004 therefore omits fingerprints for password-class secrets in redaction markers (DEC-5, A-6).
* **TM-14:** text cleaning removes control and bidi characters at the model boundary; strict mode prevents implicit coercions (`"1"` → `1`); no template or expression evaluation anywhere.
* **TM-26:** `chain_digest` domain separation (`rg.chain.v1`) prevents a spec digest from being replayed as a chain link; digests over canonical bytes remove representation ambiguity (key order, Unicode forms).
* **TM-34:** bounded parse limits and schema bounds (C7) cap memory per record.
* **Residual:** a Python `str` obtained from `reveal()` is immutable and cannot be wiped; `Secret` stores bytes in a `bytearray` that `wipe()` zeroes, but copies made by callers are out of reach (A-7).

## 16. Concurrency, asynchronous behavior, and resource ownership

All APIs are synchronous and CPU-bound; none blocks on I/O. `IdFactory` is thread-safe (one `threading.Lock` held for the duration of one id computation, ≪ 10 µs) because ids are minted from loop tasks and worker threads (e.g. `probe` executor creating `att_` ids). `SchemaRegistry` is mutated only during composition on one thread; after `freeze()` it is immutable. `Secret` instances are immutable except `wipe()`, which is idempotent and takes the instance lock. Large documents (> 1 MiB canonicalisation) should be processed in the `store` executor to keep loop latency under the scheduling budget (NFR-PERF-001); the functions themselves do not offload. No resources are owned beyond memory.

## 17. Performance and resource requirements

Proposals (validated by benchmarks; not measured facts):

| Budget | Value | Rationale | Test |
|---|---|---|---|
| `canonical_bytes` throughput | ≥ 20 MB/s on the reference CI runner for typical record mixes (strings/ints/nested maps) | observation records average ≤ 2 KiB (NFR-PERF-007) → ≥ 10 000 records/s ≫ 50 probes/s | TST-RG-P03-002-27 |
| `IdFactory.new` | ≤ 5 µs mean, ≤ 50 µs p99 single-threaded | ids minted on every attempt | TST-RG-P03-002-16 |
| `loads_document` of a 2 KiB observation | ≤ 200 µs mean | store read path | TST-RG-P03-002-27 |
| `export_schemas` for ≤ 150 documents | ≤ 10 s | CI step | TST-RG-P03-002-13 |
| Memory of registry | ≤ 50 MiB for 150 documents (pydantic core schemas) | startup budget NFR-PERF-009 | TST-RG-P03-002-27 |
| `import rg_core.serial` | ≤ 150 ms warm | `rg --version` ≤ 0.5 s | TST-RG-P03-002-27 |

## 18. Configuration and defaults

This module has no user-facing configuration (library defaults only; no environment reads). Parameters are constructor/function arguments:

| Parameter | Type | Default | Range | Failure behaviour |
|---|---|---|---|---|
| `ParseLimits.max_bytes` | int | 16 MiB | 1 KiB – 64 MiB | larger value → `ValueError` converted to `RGE-INTERNAL-0024` at composition |
| `ParseLimits.max_depth` | int | 64 | 4 – 128 | idem |
| `ParseLimits.max_items` | int | 1 000 000 | 100 – 10 000 000 | idem |
| `SCHEMA_VERSION` | `(int,int)` | per document | major ≥ 1 | invalid → registration error |
| `pydantic` pin | — | `>=2.14,<2.15` | — | enforced by the lock file (RG-P11-007) |

Env/CLI names: none (config of dependants lives in RG-P03-003: `RG_LIMITS_MAX_DOCUMENT_BYTES` maps to `ParseLimits.max_bytes` for imports).

## 19. Logging, observability, evidence requirements

This module does not log (pure; avoids recursion with the redaction gate). Observability hooks: `SchemaRegistry.stats()` returns counts (documents, families, kinds, migrations) for `rg doctor`; failures carry structured `details` (`schema_id`, `family`, `kind`, `found_version`, `supported_version`, `rule`, `field`, `issues` — never input values). Evidence: the generator versions (`pydantic`, `rg_core`) are included in `schemas/index.json`; the run manifest (RG-P08-001) records `schema_versions: {schema_id: "major.minor"}` obtained from `SchemaRegistry.versions()` (FR-EVD-007). Derived-record rule: every `Provenance`-bearing record states exactly one `derivation` (FR-EVD-003).

## 20. Platform compatibility

* **Line endings/encodings:** all canonical bytes and schema files are UTF-8, LF; repository `.gitattributes`: `schemas/** text eol=lf`, `**/*.golden.json text eol=lf` so Windows checkouts with `core.autocrlf=true` do not break golden tests; `check_golden` reports a `line_endings` hint when only CRLF differs.
* **Locale independence:** no `str.lower()/upper()` on untrusted text for comparisons except ASCII-only patterns; `sorted` is never used on text for output without the UTF-16 key.
* **Float formatting:** relies on `repr(float)` shortest round-trip (CPython on all platforms; A-3).
* **Integers:** Python arbitrary precision; the 2⁵³/2⁶³ rules do not depend on platform word size.
* **Hash seed:** `PYTHONHASHSEED` randomisation is neutralised by sorting (INV-2, TST-RG-P03-002-26).
* **Windows/macOS:** pydantic-core binary wheels exist for both (ADR-0007); no path handling here (paths are strings in models).

## 21. Edge cases and invalid inputs

| # | Input | Expected behaviour |
|---|---|---|
| E1 | `canonical_json({"a": 2**53})` | `RGE-INTERNAL-0021` (details.path `$.a`, reason `int_out_of_safe_range`) |
| E2 | `canonical_json(float("nan"))`, `inf`, `-inf` | `RGE-INTERNAL-0021` |
| E3 | key `"é"` and key `"e\u0301"` in one mapping | `RGE-INTERNAL-0021` (`duplicate_key_after_nfc`) |
| E4 | string containing `"\ud800"` | `RGE-INTERNAL-0021` (`lone_surrogate`) |
| E5 | JSON text with BOM `\ufeff{...}` | `RGE-STORE-0026` |
| E6 | `{"a":1,"a":2}` | `RGE-STORE-0026` (duplicate key, even if values equal) |
| E7 | JSON number for an `Int64` field (`{"t": 12}`) | `RGE-STORE-0020` (issue type `string_type`) |
| E8 | `"t":"9223372036854775808"` | `RGE-STORE-0020` (range) |
| E9 | `"t":"0012"` | accepted → value 12; re-serialises as `"12"` (canonicalisation normalises) |
| E10 | `schema_version "1.3"` read by code `(1,2)` | `RGE-STORE-0022` |
| E11 | `schema_version "2.0"` with no migration `1→2` registered, reader `(2,0)`, document `"1.4"` | `RGE-STORE-0023` |
| E12 | `kind: "x.acme.probe"` in a family without that registration | `RGE-STORE-0021` |
| E13 | `ShortText` of exactly 256 code points (after cleaning) | accepted; 257 → `RGE-STORE-0020` |
| E14 | `ShortText` input `"ab\u202ecd"` | stored as `"abcd"` |
| E15 | ULID first character `8` | id grammar rejects (`RGE-CONFIG-0022`) |
| E16 | `IdFactory.new("xyz")` | `RGE-INTERNAL-0022` |
| E17 | `Secret("")` | allowed only as bytes `b""` placeholder: `reveal()` returns `""`; `fingerprint()` of empty material is allowed but resolvers must not produce empty secrets (RG-P11-001) |
| E18 | `copy.deepcopy(secret)`; `pickle.dumps(secret)`; `json.dumps(secret)`; `str(secret)` | `deepcopy` returns the same object; `pickle.dumps` raises `RGE-INTERNAL-0020`; `json.dumps` raises the stdlib `TypeError` (no hook is installed; its text names only the type `Secret`); `str` returns `<Secret>`. Callers persist documents only through `dump_document`, which converts to `RGE-INTERNAL-0020` |
| E19 | float field value `1` in JSON | accepted (`1` → `1.0`); canonical output `1` (type information is not preserved by design; schemas say `number`) |
| E20 | model with a `set[str]` field | `RGE-INTERNAL-0024` rule C3 at registration |

## 22. Unit and integration test requirements

Test ids are stable; tests live under `tests/unit/core/serial/` unless noted. "Property" tests use Hypothesis (test-only dependency).

- **TST-RG-P03-002-01** Canonical vector V1 (§12.1): bytes equal the literal text; SHA-256 `9f51…9157`; domain digest `sha256:944a…b029`.
- **TST-RG-P03-002-02** Property: for random JSON values `x` (nested, unicode incl. surrogate-pair characters, floats finite, ints within ±2⁵³): `canonical_bytes(parse_json(canonical_bytes(x))) == canonical_bytes(x)`; also `dump_document(loads_document(id, b)) == b` for generated documents of every registered model.
- **TST-RG-P03-002-03** Key ordering/NFC: UTF-16 order example (`U+10000` < `U+E000`); permuting insertion order of 200 random keys yields identical bytes; NFC collision raises `RGE-INTERNAL-0021`.
- **TST-RG-P03-002-04** Float table of §12.2 (all rows) plus 10 000 random doubles: `float(es6(x)) == x` (round trip) and output contains no `e-0`/`e+0` zero-padded exponent.
- **TST-RG-P03-002-05** Rejections R1–R7: E1–E4 and non-str key, `set`, `bytes`, `Decimal` values each raise `RGE-INTERNAL-0021` with `details.path`.
- **TST-RG-P03-002-06** `Int64`: python mode accepts int within range; JSON mode requires string `^-?[0-9]+$`; `model_dump(mode="json")` emits string; E7–E9; schema contains `x-rg-format: int64` and `pattern`.
- **TST-RG-P03-002-07** `Model` base: assignment raises; `extra` forbidden; strict (`"1"` for int rejected); `ValidationError` conversion: a model validated with input `"CANARY-9f3a"` in a wrong-typed field yields an `RgError` whose `message`, `details` and `repr` do not contain `CANARY-9f3a` (INV-7).
- **TST-RG-P03-002-08** Round-trip property over **every** registered model (fixture list from the registry; strategies from `tests/support/strategies.py`): `loads(dump(m)) == m`. Fails the build if a registered model has no strategy.
- **TST-RG-P03-002-09** Conformance C1–C9: one failing model per rule is rejected with the right `details.rule`; a conforming model passes; `freeze()` then register → `RGE-INTERNAL-0024`.
- **TST-RG-P03-002-10** Polymorphic families: discriminator routing, unknown kind E12, extension kind accepted only after registration, `_families` schema `oneOf` correct.
- **TST-RG-P03-002-11** Version semantics: reader `(1,2)` accepts `"1.0"`, `"1.2"`, rejects `"1.3"` and `"2.0"` (0022), malformed `"1.02"`, `"1"` (0022).
- **TST-RG-P03-002-12** Migration chain on fixtures `tests/migrations/<schema_id>/<from>_to_<to>/{in,out}.json`: `1→2→3` applied in order; input dict unchanged (deep-copy proof via `copy.deepcopy` comparison); gap → 0023; hook raising or returning an invalid doc → 0024; migrated output equals golden.
- **TST-RG-P03-002-13** Schema export/golden: `export_schemas` equals committed `schemas/**` byte-for-byte (CI job `schemas-check`); run under `PYTHONHASHSEED` ∈ {0, 1, 4242} identical; mutating a model without `--write` fails with a unified diff; every file satisfies C7.
- **TST-RG-P03-002-14** `classify_change`: ≥ 8 pairs (add optional → additive; remove property → breaking; tighten maxLength → breaking; loosen → additive; add required → breaking; enum add → additive; enum remove → breaking; identical → identical).
- **TST-RG-P03-002-15** IdFactory vectors (§12.3 table) with a scripted RNG and a settable fake `Clock`; backwards clock step; overflow raises 0023; `parse()` round-trips; lexicographic order equals issue order for 100 000 ids across 5 ms boundaries.
- **TST-RG-P03-002-16** IdFactory concurrency/determinism/perf: 8 threads × 5 000 ids are unique, each thread's subsequence increasing; two runs with `VirtualClock` + `random.Random(7)` + the same call sequence produce identical id lists; mean ≤ 5 µs (benchmark marker).
- **TST-RG-P03-002-17** `Secret` behaviours: `repr`, `str`, `format(s)`, `f"{s}"`, `"%s" % s`, `"{}".format(s)` all equal `<Secret>`; `pickle.dumps` (all protocols), `copy.copy` (returns same object), `bytes(s)`, `list(s)`, `len(s)`, `hash(s)` raise or are undefined as specified; `s == Secret(same)` true, `s == "x"` false; `traceback.TracebackException(..., capture_locals=True)` output with a `Secret` local contains no material.
- **TST-RG-P03-002-18** `Secret` and pydantic: excluded field omitted from `model_dump/json`; non-excluded field → `SecretMisuseError`; registering a model with a non-excluded `Secret` → C6; `json.dumps(secret)` raises `TypeError` whose text lacks the material; `wipe()` then `reveal()` → 0020.
- **TST-RG-P03-002-19** `SecretHandle` grammar table (≥ 12 rows: `secret:env:RG_X`, `secret:keyring:rg/alice`, `secret:file:./s/a.txt`, `secret:file:C:\s\a.txt`, uppercase resolver, missing name, control character, 513-char name, whitespace-only name, plain token `eyJhbGciOi…`, `Bearer abc`, empty); invalid ones raise 0020 with a message lacking the input.
- **TST-RG-P03-002-20** Text types: NFC, control and bidi removal (E14), CRLF normalisation in `LongText`, 256/257 boundary (E13), `clip_text` output length ≤ max and ends with `…[+N]` with correct N, surrogate rejection, property: cleaned text is a fixed point of cleaning.
- **TST-RG-P03-002-21** `ExtKind`: accepts base values and `x.acme.my_kind`; rejects `x.Acme.k`, `x.acme.`, `x..k`, `X.acme.k`, `x.acme.k.extra`, 101-char values, core kinds spelled with `x.` prefix in a family; JSON Schema is `anyOf[enum, pattern]`.
- **TST-RG-P03-002-22** `fingerprint_of(b"hunter2") == "fp:f52fbd32b2b3"`; `Secret("hunter2").fingerprint()` equal; fingerprint never equals prefix of material.
- **TST-RG-P03-002-23** `parse_json`: BOM, duplicate keys, `NaN`, depth 65, 16 MiB + 1 bytes, 1 000 001 items, lone-surrogate escape `"\ud800"`, valid supplementary pair `"\ud83d\ude00"`; each maps to the documented code; accepted inputs return identical structures to `json.loads`.
- **TST-RG-P03-002-24** Doc-sync: every enum in `rg_core.model.enums` equals the corresponding class in the fenced code block of `docs/04-ARCHITECTURE/DATA-MODEL.md` §3 (names and values; parsed with `ast`); prefix table of §2.1 equals `IdPrefix` literal values.
- **TST-RG-P03-002-25** Shape detectors: positive corpus (JWT, `Bearer eyJ…`, `Basic dXNlcjpwYXNz`, PEM header, `https://u:p@h/`, `password = "Zx9…"` with key `client_secret`) and negative corpus (ids `exp_01M4…`, `sha256:` digests, UUIDs, base64 of a 12-byte nonce under key `nonce`, prose) — 0 false negatives, 0 false positives; no function return value contains matched text.
- **TST-RG-P03-002-26** Determinism: canonical bytes of the same registered documents computed in subprocesses with different `PYTHONHASHSEED`, locale (`C`, `tr_TR.UTF-8`) and Python versions available in CI (3.11–3.14) are identical.
- **TST-RG-P03-002-27** Benchmarks (marker `bench`): budgets of §17.
- **TST-RG-P03-002-28** Windows line endings: with `core.autocrlf=true` checkout simulation (CRLF copy of `schemas/`), `check_golden` fails with a `line_endings` hint, and the `.gitattributes` rule is asserted present.

## 23. Mocking and test fixture requirements

* `rg_core.testing.FakeClock` (settable `wall_ns`) and `VirtualClock` (RG-P02-001) for `IdFactory`; `ScriptedRandom(values)` implementing `RandomSource` (in `rg_core.testing`, no hypothesis).
* `tests/support/strategies.py`: primitives (`json_values`, `int64s`, `labels`, `short_texts`, `ext_kinds`, `ulids(prefix)`), plus per-owner `register_strategy(model, strategy)`; a registry-completeness test fails when a registered model lacks a strategy.
* Fixture datasets: `tests/data/canonical/vectors.json` (V1 + ≥ 30 vectors incl. ES6 float table), `tests/data/handles.json`, `tests/migrations/**`, `tests/data/shapes/{positive,negative}.txt`, golden `schemas/**` (the repository directory itself).
* No network, no filesystem except fixtures read by tests; temp dirs only for the `tools/rgschemas.py` integration test.

## 24. Objective acceptance criteria

- **AC-RG-P03-002-01** Canonical JSON matches RFC 8785 ordering/number rules plus the stated restrictions and reproduces vector V1 exactly (verified by TST-RG-P03-002-01, TST-RG-P03-002-03, TST-RG-P03-002-04).
- **AC-RG-P03-002-02** Canonicalisation is idempotent and independent of insertion order, hash seed, locale and Python version 3.11–3.14 (verified by TST-RG-P03-002-02, TST-RG-P03-002-26).
- **AC-RG-P03-002-03** Every unrepresentable value (NaN/Inf, int > 2⁵³−1, non-str key, set, NFC key collision, lone surrogate) raises `RGE-INTERNAL-0021` and never produces partial output (verified by TST-RG-P03-002-05).
- **AC-RG-P03-002-04** All 64-bit nanosecond integers appear as decimal strings in JSON and are rejected as JSON numbers (verified by TST-RG-P03-002-06).
- **AC-RG-P03-002-05** Base `Model` is frozen, strict, extra-forbidding and no `RgError` or issue produced from validation contains the offending input (verified by TST-RG-P03-002-07).
- **AC-RG-P03-002-06** Every registered model round-trips byte-identically and satisfies conformance rules C1–C9 (verified by TST-RG-P03-002-08, TST-RG-P03-002-09).
- **AC-RG-P03-002-07** Version handling accepts older minors of the same major, refuses newer minors/majors, and applies pure, ordered migrations with documented failure codes (verified by TST-RG-P03-002-11, TST-RG-P03-002-12).
- **AC-RG-P03-002-08** Exported JSON Schemas under `schemas/` equal the committed golden files byte-for-byte on 3 hash seeds and satisfy the bounds rule C7; schema changes are classified additive/breaking by `classify_change` (verified by TST-RG-P03-002-13, TST-RG-P03-002-14, TST-RG-P03-002-28).
- **AC-RG-P03-002-09** Polymorphic record families route by `kind`, reject unknown kinds and accept extension kinds only when registered (verified by TST-RG-P03-002-10, TST-RG-P03-002-21).
- **AC-RG-P03-002-10** `IdFactory` yields strictly increasing ULIDs under same-millisecond bursts and clock regressions, identical sequences under the virtual clock with a seeded RNG, and unique ids across 8 threads (verified by TST-RG-P03-002-15, TST-RG-P03-002-16).
- **AC-RG-P03-002-11** `Secret` never exposes its value via repr/str/format/pickle/copy/serialisation, and a model cannot be registered or dumped with a non-excluded `Secret` (verified by TST-RG-P03-002-17, TST-RG-P03-002-18, TST-RG-P03-002-22).
- **AC-RG-P03-002-12** `SecretHandle` accepts exactly the documented grammar and rejects inline credentials without echoing them (verified by TST-RG-P03-002-19, TST-RG-P03-002-25).
- **AC-RG-P03-002-13** Free-text types clean (NFC, control, bidi) and reject over-length input at the documented boundaries (verified by TST-RG-P03-002-20).
- **AC-RG-P03-002-14** Strict JSON parsing enforces the size/depth/item limits and rejects duplicate keys, BOM and non-finite constants (verified by TST-RG-P03-002-23).
- **AC-RG-P03-002-15** Enum and id-prefix catalogues equal DATA-MODEL §3 and §2.1 (verified by TST-RG-P03-002-24).
- **AC-RG-P03-002-16** Performance proposals of §17 hold on the reference CI runner (verified by TST-RG-P03-002-27).

## 25. Research sources and engineering rationale

Sources: ADR-0007 (pydantic frozen models, schema golden, round-trip property tests); DATA-MODEL §1 (int64 rule, free-text rule), §2.1 (ids), §2.4 (secrets), §9 invariant 7 (canary); TECHNICAL-FEASIBILITY §2 data-contracts row, §3 R-013 (secret leakage), R-018 (evidence volume); THREAT-MODEL TM-07, TM-14, TM-15, TM-26, TM-34; PRD FR-SEC-005/-009, FR-EVD-004. RFC 8785 (JSON Canonicalization Scheme) is used as a design reference only; its text was **not** fetched in this session, so conformance claims are limited to the rules written in §12.1 (A-1).

Decisions:

- **DEC-1 pydantic v2 frozen models with `strict=True`.** Rejected: dataclasses + hand validation (no JSON Schema), msgspec (smaller ecosystem for schema/discriminators), attrs/cattrs. Why: ADR-0007. Verification: TST-…-07, -08, -13.
- **DEC-2 Canonical JSON = RFC 8785 rules + restrictions (ints ≤ 2⁵³−1, NFC, no NaN).** Rejected: `json.dumps(sort_keys=True)` (code-point key order, Python float format differs from every other implementation, no NFC), CBOR/deterministic CBOR (not human-inspectable, extra dependency), hashing pydantic `model_dump_json` (not stable across versions). Why: digests must be recomputable by a non-Python verifier (bundle verification). Verification: TST-…-01, -03, -04, -26.
- **DEC-3 Persisted form is canonical bytes, `exclude_none=True`.** Rejected: pretty JSON on disk (formatting drift breaks byte-for-byte FR-EVD-002), including nulls (adding an optional field in a minor version would change old digests). Consequence: new optional fields in minor versions MUST default to `None`; `None` and "absent" are the same state. Verification: TST-…-02, -11.
- **DEC-4 Int64 as strings only in JSON mode** via `json_or_python_schema`. Rejected: accept JSON numbers (silent precision loss in JavaScript consumers, GUI). Verification: TST-…-06.
- **DEC-5 Own `Secret`, not `pydantic.SecretStr`.** SecretStr prints `**********`, exposes `get_secret_value`, and serialises to the mask silently (a masked-but-present value is easy to mistake for safe data and survives in persisted docs); ours raises. Rejected also: keeping secrets as `str` with redaction only. Verification: TST-…-17, -18. Fingerprints of passwords are not emitted in redaction markers (see RG-P03-004 DEC-6).
- **DEC-6 Export JSON Schema in serialization mode** (what is written to disk) with explicit `Int64` override. Rejected: validation mode (accepts both int and str shapes pydantic internal unions expose; excluded secret fields would appear). Verification: TST-…-13.
- **DEC-7 Bounds rule C7 enforced on exported schemas** rather than by convention: converts FR-SEC-009 into a build failure. Cost: owners must annotate bounds on every list/str/int. Verification: TST-…-09, -13.
- **DEC-8 Explicit registry object, `freeze()`, no import-time registration** (no hidden global state; plugin kinds register before freeze). Verification: TST-…-09, -10.
- **DEC-9 Own ULID implementation** (≈ 40 lines) instead of `python-ulid`/UUIDv7 libraries: needs injected `Clock`/RNG, monotonic increment under regressions, no new dependency. Rejected: UUIDv7 (36-char ids and no Crockford prefix compatibility with frozen DATA-MODEL §2.1). Verification: TST-…-15, -16.
- **DEC-10 Domain-separated digests** (`rg.spec.v1`, `rg.chain.v1`, …) so an artefact valid in one context cannot be replayed in another. Verification: TST-…-01.
- **DEC-11 Hypothesis strategies stay in `tests/support`** to honour SC-08 (no `hypothesis` import in packages). Verification: import-linter contract.
- **DEC-12 Forward compatibility is refused (newer minor → error).** Rejected: ignore-unknown mode (silently drops evidence fields). Verification: TST-…-11.

## 26. Remaining uncertainties or assumptions

| # | Assumption | Falsifying test |
|---|---|---|
| A-1 | The restricted RFC 8785 rules in §12.1 produce the same bytes as a conforming JCS implementation for all values within R2–R4 (RFC text not fetched this session) | cross-check TST-…-26 against an independent implementation (e.g. a JCS library in the bundle-verifier test) on the 30+ vectors; any mismatch reopens DEC-2 |
| A-2 | pydantic 2.14.1 behaviours used here (author sandbox check on CPython 3.12.3, 2026-10-12, not a research-register row): `json_or_python_schema` selects the JSON branch for `model_validate_json`; `hide_input_in_errors=True` removes inputs from error text; serialization-mode schema omits `exclude=True` fields; `allow_inf_nan=False` rejects `NaN`/`1e999`; strict float accepts JSON `1` | TST-…-06, -07, -13 on every pydantic bump |
| A-3 | `repr(float)` is the shortest round-trip representation on all supported platforms/versions | TST-…-04 (10 000 random doubles) on Windows + Linux CI |
| A-4 | `str.encode("utf-16-be")` ordering equals RFC 8785 key ordering for all valid strings | TST-…-03 |
| A-5 | `frozenset` JSON-mode serialisation order is not stable, hence `SortedSet` is required | TST-…-26 with differing hash seeds on a model using plain `frozenset[str]` (must differ) vs `SortedSet` (must not) |
| A-6 | A 12-hex-digit fingerprint is acceptable for high-entropy credentials but offline-attackable for low-entropy passwords | review decision recorded in RG-P03-004 DEC-6; test TST-RG-P03-004-17 asserts password-class markers carry no fingerprint |
| A-7 | `bytearray` zeroing is best effort; interpreter copies may persist | accepted residual; documented, no test can falsify |
| A-8 | Registry freeze/conformance cost fits startup (≤ 150 documents) | TST-…-27 |
| A-9 | Plugin authors can express their kinds as `x.<vendor>.<name>` without needing nested unions | contract kit review in RG-P12-003 |

## 27. Maintainability, portability, and future extension requirements

* **Extension points:** `SchemaRegistry.register_record` for plugin kinds (via RG-P03-009 before freeze); `Migration` hooks; `DigestDomain` additions require a CONTRACT-CHANGELOG entry (domains are part of the evidence format); new scalar types are added to `rg_core.model.base` only with a conformance rule.
* **Versioning/deprecation (NFR-MNT-005):** a field is deprecated by documenting it in the schema `description` for one minor release and removed only in the next major with a `Migration`; `index.json` records every version still readable.
* **Reuse outside RevocationGap:** `rg_core.serial.canonical` (canonical JSON/digests), `ids`, `secret` have no RG-specific imports other than `Clock` (a one-method protocol) and can be vendored.
* **Upgrade procedure for pydantic:** bump in a PR; CI runs `schemas-check`, round-trip and determinism tests; any golden diff must be classified by `classify_change` and approved.
* **Documented limits:** no support for non-string map keys, `Decimal`, `datetime`, floats in id/digest-critical fields; adding any of them requires amending rules R1–R7 (and thus DEC-2) with a new digest domain version.
