# ADR-0012 — Reproducibility by serialised experiment spec + request snapshots, not by regeneration

* **Status:** Accepted · **Owner:** RG-P03-001 (detail: RG-P05-013)
* **Context.** Hypothesis-based regeneration depends on library versions and randomness; a revocation experiment must be repeatable across versions/configs/providers (differentiator D-6).
* **Decision.** A run stores (1) the fully-resolved `ExperimentSpec` (secrets as handles), (2) pinned request snapshots per probe (method, URL template + parameters, non-credential headers, body hash/blob), (3) seeds for any generation step, (4) tool and dependency versions (including `schemathesis.__version__`). Replay re-executes (2) against the same or a different target; regeneration from a seed is a separate, lab-oriented mode.
* **Alternatives.** Regenerate from seeds only (fragile across upstream versions); record/replay of network traffic (VCR) as the primary mechanism (replays *responses*, which would replay the exact vulnerability being measured — useful only for analysis regression, kept as lab fixture format).
* **Consequences.** Snapshots must be secret-free (ISO-4); credentials are re-resolved at replay time from handles.
* **Verification.** Replay determinism tests in the lab (P05-013, P09-005).
