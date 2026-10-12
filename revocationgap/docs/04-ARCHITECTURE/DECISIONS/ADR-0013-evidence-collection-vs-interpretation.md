# ADR-0013 — Evidence collection and interpretation are separate, one-way

* **Status:** Accepted · **Owner:** RG-P03-001 (detail: RG-P08-001…011)
* **Decision.** Probes, adapters and orchestration write **only** immutable, append-only `EvidenceItem`s and `Observation`s (facts with provenance). Analysis (clock alignment, correlation, exposure window, classification) consumes evidence and produces **derived records** labelled by `derivation` (`observed` | `calculated` | `assumed` | `hypothesis`), each referencing its inputs and the algorithm version; derived records can be recomputed from evidence at any time with a newer algorithm (historical re-analysis). Reports must label every statement with its derivation class.
* **Alternatives.** Analysis embedded in probes (loses re-analysis, mixes facts with judgements).
* **Verification.** Re-analysis determinism test: recompute from stored evidence == stored derived records (P12-002).
