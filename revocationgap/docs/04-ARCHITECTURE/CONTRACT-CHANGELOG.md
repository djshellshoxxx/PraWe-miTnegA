# Contract Changelog

Changes to frozen contracts (`SYSTEM-ARCHITECTURE.md`, `DATA-MODEL.md`, `INTERFACE-CONTRACTS.md`, ADRs). Process: INTERFACE-CONTRACTS §5.

| Date | Contract | Change | Rationale | Dependants swept |
|---|---|---|---|---|
| 2026-10-12 | all | v1.0 baseline authored (RG-P03-001 draft) | initial freeze | — |
| 2026-10-12 | INTERFACE-CONTRACTS §2.5 | `RGE-PROVIDER-UNSUPPORTED` → `RGE-PROVIDER-0001` (alias resolved on read only) | DATA-MODEL §6 code format | RG-P03-005 |
| 2026-10-12 | SYSTEM-ARCHITECTURE §9 | metric names dotted: `probe.latency`, `scheduler.lateness`, `queue.depth` | RG-P03-004 §10.7 grammar | RG-P03-004, P03-007 |
| 2026-10-12 | DATA-MODEL §2.4 | fingerprints only for high-entropy classes | RG-P03-004 DEC-6 | RG-P03-004, P11-001 |
| 2026-10-12 | INTERFACE-CONTRACTS §1, DATA-MODEL §8 | added IF-CORE-AIO, IF-CFG-REGISTRY, SCH-ERROR, SCH-LOGREC | new owned ids | — |
| 2026-10-12 | CCR-A…J (review REVIEW-P03-002-005) | A: config primitives in `rg_core.model.config`; B: all secrets registered as canaries; C: nullable/`None` rules; D: shielded `commit_grace` for durable/state-changing ops; E: ADR-0007 `Secret` raises on serialisation; F: `uses` edges P03-002↔P03-005 (errors.core stdlib leaf), P03-003→P03-004/005, P03-004/005→P02-001 recorded; G: `Scheduler.call_at` stays, RG-LINT-001.b narrowed to loop receivers; H: `fs` executor added (4 executors); I: composition-root thread pools/signal handlers/logging hooks allowed in rg_core; J: `details.residual_state` + exit kind | defects D-004, D-002, D-008, D-005, D-054, D-070, D-014, D-033, D-047, D-009 | P03-002…005 |
| 2026-10-12 | Core-temporal CCR-1…6 | 1: happy-path state order `DRAFT→VALIDATED→BASELINING→ARMED→REVOKING→OBSERVING→ANALYZING→CLEANING_UP→COMPLETE|INCONCLUSIVE` (USER-WORKFLOWS §3, TM-06 updated); 3: `ExperimentStore.transition(..., trigger, runtime_patch, records)` atomic; 2,4,5 forwarded to RG-P03-002/005 owner; 6 (`ses` prefix) declined — sessions are value entities keyed `ses:<12 hex fp>` per RG-P02-003; added IF-CORE-CLOCKGUARD/AUTHSTATE/CREDGRAPH/EVENTORDER/OBSERVATION/TIMELINE, IF-ANA-EXPECT | P02-001…009, P03-006 authors | P02-007, USER-WORKFLOWS, THREAT-MODEL |
| 2026-10-12 | **Normative adoption** | RG-P03-005 §8.3 error-code block table (0001–0019 P03-005; 0020–0039 P03-002; 0040–0059 P03-004; 0060–0069 scheduler; 0070–0079 event bus; 0100–0999 P02-00k own k·100; 1000–1199 config; 1200–1399 store; 1400/1500/1600 plugins/engine/deployment; 1700–2799 P04; 2800–4199 P05; 4200–5199 P06; 5200–5699 P07; 5700–6799 P08; 6800–7399 P09; 7400–8099 P10; 8100–8799 P11; 8800–9899 reserved; 9900–9999 test-only) and P03-002 model-conformance rules C1–C9 (no bare `int` — use `Count`/`SafeInt`/`Int64`; explicit bounds on every str/list/map; `SortedSet`; no datetime/Path/bytes/Decimal in models; `Secret` fields `exclude=True`; `ExtKind` for extensible vocabularies) | enforced by registry | all spec authors |

