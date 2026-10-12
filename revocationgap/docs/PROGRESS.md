# RevocationGap — Progress Tracker

_Persistent project memory. Update on every commit. A resumed session must first reconcile this file against `git log` and `python tools/specgate.py check`._

## Resume protocol

1. `git fetch && git log --oneline -20 -- revocationgap/` and compare with "Most recent verified commit" below.
2. `cd revocationgap && pip install -r tools/requirements.txt && python tools/specgate.py check` — fix any gate errors for elements marked COMPLETE/DRAFT before continuing.
3. `python tools/specgate.py order` — first non-COMPLETE element whose dependencies are COMPLETE is next, unless "Next exact action" says otherwise.

## Current state

| Field | Value |
|---|---|
| Current phase | 00 research integration (W1) |
| Current work element | Awaiting research agents: RG-P00-003 (standards, 2nd pass), P00-004, P00-005 |
| Branch | `claude/revocationgap-spec` |
| Most recent verified commit | _(none yet)_ |
| Push status | not yet attempted |
| Blockers | none |

## Next exact action

Write `02-RESEARCH/REPO-ASSESSMENT.md`, `02-RESEARCH/SCHEMATHESIS-INTEGRATION.md`, then foundation architecture documents; collect research-agent drafts from `/workspace/rg-scratch/{competitive,standards,providers-a,providers-b}/`.

## Status summary (generated)

<!-- BEGIN:STATUS -->
| Status | Count |
|---|---|
| TODO | 112 |
| IN_PROGRESS | 0 |
| DRAFT | 0 |
| COMPLETE | 2 |
| BLOCKED | 0 |

| Phase | Complete / Total |
|---|---|
| 00 Repository Discovery and Technical Research | 2 / 6 |
| 01 Product Requirements and Threat Modeling | 0 / 4 |
| 02 Temporal Authorization Model | 0 / 9 |
| 03 Core System Architecture | 0 / 11 |
| 04 Authentication and Identity Adapters | 0 / 11 |
| 05 Probe and Offensive Test Engine | 0 / 14 |
| 06 Revocation Orchestration | 0 / 10 |
| 07 Attack Scenario Library | 0 / 5 |
| 08 Evidence, Correlation, and Finding Analysis | 0 / 11 |
| 09 Test Laboratory and Simulation Framework | 0 / 6 |
| 10 CLI, GUI, and User Experience | 0 / 7 |
| 11 Security and Operational Engineering | 0 / 7 |
| 12 Testing, QA, and Verification | 0 / 6 |
| 13 Build, Packaging, Distribution, and Documentation | 0 / 4 |
| 14 Future Expansion and Product Strategy | 0 / 1 |
| 15 Independent Specification Audit | 0 / 2 |

Next 8 eligible elements in dependency order: RG-P00-003, RG-P00-004, RG-P00-005, RG-P00-006, RG-P01-001, RG-P01-002, RG-P01-003, RG-P01-004
<!-- END:STATUS -->

## Architectural decisions

See `04-ARCHITECTURE/DECISIONS/` (index in `SYSTEM-ARCHITECTURE.md` §12).

## Known specification defects

None recorded yet. Defects found during review are listed in `SPECIFICATION-AUDIT.md` with severity.

## Pending research questions

See `OPEN-QUESTIONS.md`.
