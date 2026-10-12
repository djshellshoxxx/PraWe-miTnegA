# ADR-0001 — Schemathesis as pinned upstream foundation behind an adapter

* **Status:** Accepted (2026-10-12) · **Owner:** RG-P00-002 / RG-P03-001 · **Supersedes:** —
* **Context.** System-prompt mandate: build on Schemathesis, no fork. Research (SCHEMATHESIS-INTEGRATION.md) verified 4.30.1: strong schema/operation/request machinery, **no** temporal concept, no WebSocket, no timestamps on `Response`, hazardous auth re-try/caching defaults, ≈weekly releases.
* **Alternatives.** (A) Fork and extend Schemathesis — rejected: merge burden against ≈40 releases/16 weeks. (B) Drive Schemathesis' engine/CLI (`st run`) and add checks — rejected: engine API undocumented, time axis impossible, hypothesis-driven re-sends. (C) Schemathesis as a library behind a bridge using only the documented Python API — **selected**. (D) Ignore Schemathesis — rejected by mandate and loses operation/security-scheme discovery.
* **Decision.** `schemathesis` is a version-pinned dependency (`>=4.30.1,<4.31`; exact in lock) imported **only** by `rg_stbridge`. RG owns time, state, probes, assertions, evidence. A required `RawHttpTransport` fallback implements the same port (CR-9) so upstream is an accelerator, not a single point of failure.
* **Consequences.** Thin bridge (≈1.5–2 kLOC planned); weekly compat canary; import-linter + isolation tests ISO-1…ISO-11; any upstream change request goes upstream, not into a fork.
* **Verification.** RG-P12-006 (ISO suite, API-surface test, import boundary), RM-ST-1…6.
