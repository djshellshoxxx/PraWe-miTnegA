# ADR-0010 — Outcome taxonomy and policy profiles

* **Status:** Accepted · **Owner:** RG-P03-001 (detail: RG-P02-005, RG-P02-009, RG-P08-006)
* **Context.** The master prompt requires six continued-access outcome classes; STANDARDS-REFERENCE shows the same behaviour (JWT accepted until `exp` after logout) is conformant to OAuth/OIDC but violates ASVS V7.4.1/V7.4.2 for application session tokens (RF-10).
* **Decision.** `OutcomeClass ∈ {enforced, expected, documented_delay, risky_config, vulnerable, needs_verification, inconclusive}` (`enforced` = no continued access beyond tolerance; the other six are the master-prompt classes). Every classification is computed **relative to a `PolicyProfile`** (`protocol` default, `vendor_doc`, `asvs_5_l1|l2|l3`, `nist_aal2|aal3`, `operator`) and records it; a finding's class may legitimately differ between profiles and reports show the matrix.
* **Consequences.** Classifier inputs: expectation set (per credential type × event × validation mode), measured window, evidence strength. `vulnerable` requires an expectation that is MUST-level in the selected profile, high-confidence evidence and a passed independent-validation step.
* **Verification.** Golden classification tables (P02-009 tests), mutation tests of rule boundaries.
