# Architecture Summary

From `docs/FOUNDATION.md` and the README.

- **SimPy as a dependency, not a fork.** SimPy's discrete-event simulation and virtual clock provide the scheduler. The security models and mutation logic stay in this repository.
- **Optional adapters later.** LangGraph (agent state and checkpoints) and the Temporal SDK are possible future adapters.
- **Findings must be reproducible.** A finding needs an observable, reproducible policy violation, not an LLM judge's opinion (README).
- **Synthetic environments.** Test environments are synthetic; time advancement does not accelerate real systems (README, "Engineering principles").
- **Roadmap.** Foundation, contracts, ChronoFuzz, AuthorityDecay, integrations, analysis, product (README "Development phases").
