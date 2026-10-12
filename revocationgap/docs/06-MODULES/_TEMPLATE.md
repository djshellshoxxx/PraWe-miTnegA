---
id: RG-PNN-NNN                 # must equal the work-element id in docs/work-elements.yaml
title: "Element title"
phase: "NN"
package: core|idp|probe|stbridge|lab|app   # owning distribution (see 04-ARCHITECTURE/SYSTEM-ARCHITECTURE.md §4)
module_ids: [MOD-CORE-EXAMPLE]            # stable module identifiers introduced/owned by this element
status: DRAFT
depends_on: []                            # must equal registry deps exactly
requirements: [FR-AREA-001]               # IDs defined in 03-PRODUCT/PRODUCT-REQUIREMENTS.md
interfaces_defined: [IF-EXAMPLE]          # IF-* contracts this element owns (indexed in INTERFACE-CONTRACTS.md)
interfaces_used: []
schemas_defined: [SCH-EXAMPLE]            # SCH-* data schemas this element owns (indexed in DATA-MODEL.md)
schemathesis_touchpoints: []              # verified upstream symbols relied upon, e.g. "schemathesis.Case.call"; [] if none
---

# RG-PNN-NNN — Element title

> Writing rules: every section 1–27 below is mandatory (write "Not applicable — <reason>" only when truly inapplicable;
> never leave it vague). Use language-neutral signatures + Python-typed examples. Every tested behaviour gets a
> `TST-<ID>-NN` test; every acceptance criterion `AC-<ID>-NN` cites at least one TST. Define things once; link to other specs.

## 1. Module identifier and name
## 2. Phase and requirement references
## 3. Purpose and user/security value
## 4. Explicit responsibilities
## 5. Out-of-scope responsibilities
## 6. Dependencies and prerequisites
## 7. External and internal interfaces
## 8. Data structures and schemas
## 9. Inputs, outputs, and validation rules
## 10. Detailed execution behavior
## 11. State transitions and invariants
## 12. Core algorithms and pseudocode
## 13. Internal functions, methods, or service operations
## 14. Error handling and failure recovery
## 15. Security requirements and trust boundaries
## 16. Concurrency, asynchronous behavior, and resource ownership
## 17. Performance and resource requirements
## 18. Configuration and defaults
## 19. Logging, observability, and evidence requirements
## 20. Platform compatibility
## 21. Edge cases and invalid inputs
## 22. Unit and integration test requirements
## 23. Mocking and test fixture requirements
## 24. Objective acceptance criteria
## 25. Research sources and engineering rationale
## 26. Remaining uncertainties or assumptions
## 27. Maintainability, portability, and future extension requirements
