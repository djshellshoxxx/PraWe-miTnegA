# Foundation decision: SimPy with optional adapters

## Decision

Use SimPy 4.x as a Python dependency for the initial deterministic event scheduler. Do not fork SimPy or AgentLAB. Keep the domain model, security invariants, scenarios, traces, and attack mutations owned by PraWe-miTnegA. Add LangGraph, Temporal, and AgentLAB as optional adapters after validating pinned versions, licenses, and integration tests.

## Why

SimPy provides mature discrete-event scheduling and an explicit virtual-time clock without an LLM provider or workflow server. Temporal already time-skips Temporal workflows; LangGraph already checkpoints LangGraph agents. Do not reimplement those capabilities inside their native runtimes.

## Prototype limitation

The first executable example tests an instrumented **synthetic approval workflow**, not arbitrary deployed AI agents. The intentionally faulty cached-approval mode is a demonstration fixture, not a discovered vulnerability. SimPy does not accelerate external APIs or model inference. Approval validity is checked at the **execution** boundary.

## Roadmap

1. SimPy scheduler, authorization fixture, deterministic findings, CLI and tests.
2. Versioned Clock, Event, Scenario, PolicyOracle, SnapshotAdapter and AgentAdapter interfaces.
3. Schedule mutation: expiry, reordering, retries, skew, cancellation and reproducibility.
4. Optional LangGraph, Temporal, AgentLAB adapters with compatibility and license reviews.
5. MemoryEpoch and MCPChronicle security test packs, minimization, trace UI and CI.

## Upstream links

- SimPy: https://github.com/simpx/simpy
- Hypothesis: https://github.com/HypothesisWorks/hypothesis
- LangGraph: https://github.com/langchain-ai/langgraph
- Temporal Python SDK: https://github.com/temporalio/sdk-python
- AgentLAB: https://github.com/TanqiuJiang/AgentLAB

No upstream source code has been copied into this repository. Review licenses and all transitive dependencies before vendoring.
