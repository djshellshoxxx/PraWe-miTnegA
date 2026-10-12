# ADR-0007 — pydantic v2 frozen models as the shared contract and schema source

* **Status:** Accepted · **Owner:** RG-P03-001 (detail: RG-P03-002)
* **Alternatives.** dataclasses (+hand validation, no JSON Schema), attrs/cattrs, msgspec (fast, smaller ecosystem for JSON Schema/discriminated unions), **pydantic v2**.
* **Decision.** `rg_core` models are `pydantic.BaseModel` with `frozen=True`, `extra="forbid"`, discriminated unions on `kind`, explicit `schema_version` on persisted/exported documents, JSON Schema exported to `schemas/` and verified in CI against golden files. Secrets use a `Secret` wrapper that **raises on serialisation and is excluded from dumps**; documents refer to secrets only by `SecretHandle` fields (CCR-E).
* **Consequences.** pydantic-core wheels (Rust) required on all platforms (available for Windows/Linux/macOS); upgrade policy: minor pins, quarterly bump.
* **Verification.** Schema-golden test; round-trip property tests.
