# ADR-0011 — Safe-by-default execution with mandatory scope document and action classes

* **Status:** Accepted · **Owner:** RG-P03-001 (detail: RG-P11-002)
* **Decision.** No network action occurs without a validated **scope document** (hosts/tenants/identities/permitted action classes, rate and time limits, SaaS clearance acknowledgement). Action classes: `observe` (read-only probes, introspection), `authenticate` (token acquisition for declared test identities), `mutate_identity` (disable/role/group/session/password on declared test identities only), `mutate_policy` (conditional access/device compliance/realm-level), each separately enabled. `mutate_*` additionally require `--confirm` tokens or interactive confirmation, produce a restoration plan, and write to an append-only audit log. Dry-run executes the full validation and prints the exact planned requests without sending them.
* **Alternatives.** Trust the operator (rejected: R-006/R-022), config-only flags without audit (rejected).
* **Verification.** Property tests: for every generated plan, any request to a host outside scope is rejected before I/O (P12-006).
