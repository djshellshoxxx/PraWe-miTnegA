# ADR-0005 — SQLite (WAL) + content-addressed blob files as the run store

* **Status:** Accepted · **Owner:** RG-P03-001 (detail: RG-P03-008)
* **Context.** Single-user local tool; Windows+Linux; crash consistency for interrupted runs; portable evidence bundles; optional encryption.
* **Alternatives.** Plain JSONL files (no queries, weak atomicity); DuckDB (analytics-strong, less crash-safe single-writer semantics, heavier); Postgres (server dependency); **SQLite WAL + blobs**.
* **Decision.** One SQLite database per workspace (metadata, timeline, findings, run index) and a content-addressed blob directory (`sha256` filenames) for raw evidence; append-only event log table per experiment with monotonic sequence numbers; migrations by numbered SQL scripts; export = zip of DB subset + blobs + manifest with hashes.
* **Consequences.** Single writer per workspace (engine holds a lock file; documented); WAL on network filesystems unsupported (diagnostic warning RG-P11-006).
* **Verification.** Crash-injection tests (P12-002/P11-005): kill -9 at every state transition leaves a recoverable run.
