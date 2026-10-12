# PraWe-miTnegA

**Temporal red teaming, stateful attack simulation, and time-travel debugging for autonomous AI agents.**

> Project status: Research and specification planning. No implemented features are claimed.

## Introduction

PraWe-miTnegA is a proposed open-source platform for evaluating security failures that emerge during the long-term operation of AI agents. Most prompt-injection tests examine an individual input or a short exchange. Autonomous agents can operate for days, weeks, or months, carry information between sessions, call external tools, execute scheduled tasks, and delegate work to other agents. An instruction originating from a low-trust source can be saved, summarized, retrieved later, and eventually influence a privileged decision.

PraWe-miTnegA aims to make these delayed, state-dependent failures observable, reproducible, and testable without waiting for real-world time to pass.

The goal is a controllable testing environment in which a researcher can simulate a changing organization, advance a virtual clock, inspect an agent's state, introduce adversarial conditions, create alternative timeline branches, and determine whether an actual security policy was violated.

**Virtual time is not a promise to accelerate every external system.** Time can only be controlled where the application, adapter, or simulated dependency supports it. Real model calls, external APIs, and independent providers may still operate according to wall-clock time.

## Why this project exists

A security issue may require many individually ordinary events to happen before it becomes visible:

1. An agent encounters untrusted material during a legitimate task.
2. Content from that material enters persistent memory or a summary.
3. Subsequent sessions retrieve or transform the content.
4. A scheduled job, permission change, or agent handoff changes the context.
5. The agent attempts an action that violates the current authorization policy.

PraWe-miTnegA is intended to capture and analyze this complete sequence, not merely classify the initial input as suspicious.

## Intended capabilities

### Primary platform features

- **Virtual time and event scheduling:** advance controlled simulation clocks; trigger scheduled tasks, expirations, and environment events.
- **Long-horizon campaign execution:** describe multi-session test scenarios with delayed triggers, stateful tool interactions, and conditional events.
- **Agent state inspection:** trace short- and long-term memory, task state, relevant configurations, and provenance where supported by adapters.
- **Snapshots and timeline branching:** restore supported state to checkpoints and compare baseline, attacked, and mitigated runs.
- **Synthetic environment simulation:** model messages, documents, identities, approvals, permissions, tool responses, and recurring workflows.
- **Trust-boundary assertions:** detect verifiable unauthorized actions, incorrect use of revoked permissions, and other explicitly specified policy violations.
- **Evidence and causality analysis:** record timestamped events and dependencies; distinguish observed correlation from causally supported findings.
- **Reproduction and regression tests:** package cases with seeds, artifacts, dependencies, and expected outcomes.
- **Interactive timeline analysis:** inspect agent activity, memory changes, security findings, and diverging test branches.
- **Attack variation:** explore controlled variations in timing, exposure, ordering, and environment state while respecting test budgets.

### Supporting features

Planned supporting capabilities include a CLI, REST API, Python SDK, pluggable agent and memory adapters, MCP integration, prebuilt scenarios, machine-readable reports, CI integration, token and execution budgets, safe trace redaction, and local-model support.

### Possible later capabilities

Possible later releases may include automated campaign planning, cross-agent permission-path analysis, distributed scenario workers, enterprise digital twins using synthetic or sanitized data, behavioral-drift metrics, model-upgrade comparisons, and incident reconstruction.

These are proposed directions, not committed release dates.

## Example use case

A synthetic IT-support agent reads an untrusted support document on virtual day 1. On day 6, its summary is persisted to memory. On day 19, another workflow retrieves that memory. On day 37, the organization's simulated permissions change. On day 60, an automated action attempts to use an approval that is no longer valid.

PraWe-miTnegA should show how the relevant data traveled, identify the policy boundary, capture the attempted action, and let the tester branch from an earlier checkpoint to verify a potential fix.

## Proposed architecture

The platform is intended to consist of loosely coupled modules:

1. **Simulation core:** virtual clock, deterministic event queue, scenario runner, and explicit event/state contracts.
2. **State subsystem:** snapshots, persistence adapters, memory provenance, and supported restoration mechanisms.
3. **Environment adapters:** synthetic services, agent frameworks, MCP, external tool contracts, and model-provider gateways.
4. **Security test engines:** long-horizon scenarios, stateful mutation, trust-boundary policies, and outcome verification.
5. **Evidence and analysis:** traces, branch comparisons, event graphs, replay manifests, and regression artifacts.
6. **User interfaces:** CLI and API first, followed by a visual timeline and scenario editor.

Plugins should have versioned contracts and test fixtures. External dependencies must not dictate the project's domain model or prevent support for other agent frameworks.

### Open-source foundations to evaluate

| Project | Proposed use | Decision |
| --- | --- | --- |
| [SimPy](https://simpy.readthedocs.io/) | Discrete-event simulation and controllable logical time | Preferred initial foundation; validate integration |
| [Temporal Python SDK](https://github.com/temporalio/sdk-python) | Time-skipping tests for Temporal workflows | Optional adapter; do not require Temporal for core operation |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Agent checkpoints, state history, and branch replay | First-class adapter candidate |
| [AgentLAB](https://github.com/TanqiuJiang/AgentLAB) | Long-horizon adversarial scenarios and benchmark methodology | Research/reference and potential scenario integration |
| [OpenART](https://github.com/AI45Lab/OpenART) | Evolving, stateful agent test environments | Research/reference and potential environment integration |
| [Microsoft PyRIT](https://github.com/microsoft/PyRIT) | Attack orchestration and evaluation | Optional security-testing integration |
| [LangGraph Testing](https://github.com/Autonoma-Tools/langgraph-testing) | Checkpoint and test architecture examples | Implementation reference |
| [ServiceNow AgentLab](https://github.com/ServiceNow/AgentLab) | Large-scale reproducible agent experiments | Future integration candidate |

**Dependency policy:** All potential upstream integrations must be assessed for licensing, maintained versions, security, supported environments, architectural fit, and reproducibility before adoption. No external code has yet been incorporated.

## Proposed development phases

- **Phase 0 — Research and project foundation:** establish purpose, survey open-source foundations, define high-level architecture and constraints.
- **Phase 1 — Specification metaprompts:** create prompts for research, developer-ready functional specifications, architecture, data contracts, threat models, and verification plans.
- **Phase 2 — Specification package:** produce complete, versioned specifications; review interfaces, security assumptions, and testability before implementation.
- **Phase 3 — Simulation MVP:** build the virtual clock, event scheduler, one example agent, synthetic environment, state capture, policy checks, and CLI.
- **Phase 4 — Security testing:** introduce long-horizon campaigns, memory provenance, state snapshots and branching, mutation, and reliable reproduction.
- **Phase 5 — User-facing application:** add the timeline UI, scenario editor, reports, additional adapters, and CI integration.
- **Phase 6 — Quality and release:** verify features against specifications, audit code and dependencies, fix bugs, benchmark performance, and publish tested packages.
- **Phase 7 — Advanced research:** investigate distributed runs, automated exploration, enterprise simulations, and incident forensics.

Every phase should have documented acceptance criteria and automated tests. Progress should be recorded in version-controlled planning documents.

## Design principles

- **Evidence before assertions:** measure real tool effects or explicit simulated policy outcomes rather than treating model-generated judgments as proof.
- **Determinism where possible:** make event ordering, fixtures, randomness, and state transitions reproducible; clearly identify stochastic model behavior.
- **Modularity:** keep reusable components independently testable, documented, and portable.
- **Safe-by-default tests:** prefer isolated services, synthetic identities, mock credentials, and controlled target environments.
- **Cost-conscious execution:** include token, runtime, concurrency, and storage budgets.
- **Honest simulation boundaries:** report what was virtualized, what was mocked, and what depended on live systems.
- **Extensibility:** use stable contracts and adapters instead of embedding a specific AI framework into the core.
- **Maintainability:** provide tests, typed interfaces, migration guidance, and meaningful comments explaining non-obvious decisions.

## Current status and next steps

The repository is at the introduction and research stage. No architecture, upstream dependency, test strategy, or feature list is finalized.

**Next planned step:** author metaprompts that generate a comprehensive, developer-ready specification package, including a dependency decision record, module boundaries, full functional and nonfunctional requirements, event/state schemas, testing strategy, phased implementation plan, and explicit completion criteria.

## Related projects and background

- [SimPy](https://simpy.readthedocs.io/)
- [Temporal Python SDK](https://github.com/temporalio/sdk-python)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [AgentLAB](https://github.com/TanqiuJiang/AgentLAB)
- [OpenART](https://github.com/AI45Lab/OpenART)
- [Microsoft PyRIT](https://github.com/microsoft/PyRIT)

## License

A project license has not yet been selected. Before accepting external contributions or redistributing incorporated code, select an explicit repository license and review the licenses and attribution requirements of all dependencies.
