# ADR-0002 — Python 3.11+ as implementation language and runtime floor

* **Status:** Accepted · **Owner:** RG-P03-001
* **Context.** Schemathesis (Python ≥3.10), Authlib, Hypothesis, security-research audience. `websockets` 17 requires ≥3.11 (providers-b); Python 3.10 reaches end-of-life in Oct 2026 (exact date U → RG-P13-001).
* **Alternatives.** Go/Rust (fast, single binary; cannot use Schemathesis — violates mandate); TypeScript (no equivalent foundation); Python 3.10 floor (EOL, loses `TaskGroup`, `tomllib`, `ExceptionGroup`).
* **Decision.** Python **≥3.11**, CI matrix 3.11–3.14 on Linux + Windows (+ macOS best effort). Type-checked (mypy strict on `rg_core`), `from __future__ import annotations` avoided where pydantic needs runtime types.
* **Consequences.** Process-level parallelism is future work (Phase 14); thread offload for blocking I/O. Distribution as wheels + PyInstaller one-folder.
* **Verification.** CI matrix; RG-P12-005.
