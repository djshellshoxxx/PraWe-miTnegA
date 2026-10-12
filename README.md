# PraWe-miTnegA

**Open-source temporal security fuzzing and forensic analysis for AI-agent workflows.**

PraWe-miTnegA aims to find security failures that emerge because agent operations occur at the wrong time, in the wrong order, or under authority that is no longer valid. Its flagship engine, **ChronoFuzz**, will systematically vary timing, event order, retries, callback delivery, expirations, and relevant state changes. **AuthorityDecay**, its first security test pack, focuses on the lifetime of authorizations, approvals, and delegated work.

The project is early-stage. No production-agent vulnerability detection or integration is implemented yet.

## The problem

An AI agent may check approval, queue work, and later execute an action after that approval has expired or been revoked. A document may pass through memory summaries before another agent uses it. Multiple agents may see different states, timers, or tool definitions. Short prompt-injection tests often fail to model these interactions.

PraWe-miTnegA will provide controlled synthetic environments, security policy assertions, reusable scenario definitions, timestamped traces, test-case minimization, and eventually cross-system timeline branching. A finding must be backed by an observable, reproducible policy violation, not merely an LLM judge's suspicion.

## Framework strategy

**Use SimPy 4.x as a dependency, not a fork.** Its discrete-event simulation and virtual clock supply the initial event scheduler. Keep all AI-security domain models and mutation logic in this repository.

Optional future integrations:

- [LangGraph](https://github.com/langchain-ai/langgraph): agent state and checkpoint adapters.
- [Temporal Python SDK](https://github.com/temporalio/sdk-python): adapters for Temporal workflow testing and its existing time-skipping test environment.
- [AgentLAB](https://github.com/TanqiuJiang/AgentLAB): benchmark and campaign interoperability, not a mandatory runtime dependency.
- [Hypothesis](https://github.com/HypothesisWorks/hypothesis): potential stateful fuzz-input generation and minimization.

See [foundation and upstream decision](docs/FOUNDATION.md).

## Development phases

1. **Foundation:** SimPy scheduling, a synthetic authorization scenario, deterministic findings, tests and a CLI.
2. **Contracts:** typed event/state/policy/adapter specifications, serialization and replay manifests.
3. **ChronoFuzz:** scheduling and time mutation, invariant checking, coverage and regression fixtures.
4. **AuthorityDecay:** approval expiry, revocation, queued work and callback timing.
5. **Integrations:** LangGraph, Temporal, AgentLAB, MCP and external tool adapters.
6. **Analysis:** causal graphs, timeline branches, trace minimization and reporting.
7. **Product:** visual timeline, scenario editor, CI, distributed execution and broader temporal test packs.

## Prototype scope

The first executable fixture models approval at planning time and checks whether an operation remains authorized at execution time. A deliberately faulty caching mode demonstrates a failed invariant. This is a **synthetic regression demonstration**, not an exploit against a real deployed agent.

Install with `python -m pip install -e '.[dev]'`, run `python -m pytest`, and execute `prawe` when dependencies are available.

## Engineering principles

Use modular interfaces, secure synthetic test environments, observable outcomes, reproducible seeds, explicit limits on virtualized dependencies, and redaction of captured secrets. Time advancement does **not** accelerate external model inference or remote APIs automatically.

License selection is pending. Review all upstream licenses before vendoring or redistribution.
