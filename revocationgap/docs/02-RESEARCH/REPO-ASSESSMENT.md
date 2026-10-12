# Repository Discovery and Existing-Work Assessment (RG-P00-001)

_Assessed 2026-10-12 against `djshellshoxxx/PraWe-miTnegA` @ `33d6958` (default branch `main`)._

## 1. What exists

| Item | Finding |
|---|---|
| Repository | `djshellshoxxx/PraWe-miTnegA`, public-access via workspace credentials; one branch (`main`), **no tags, no releases, no open or closed pull requests, no issues** (GitHub API: PR list empty, issue #1 404). |
| History | 8 commits, 2026-10: introduction + phased roadmap, scope refinement (ChronoFuzz/AuthorityDecay), SimPy foundation (pyproject, `src/prawemintega/core.py`, test file, `docs/FOUNDATION.md`), CI workflow. |
| Product | **PraWe-miTnegA — "temporal security fuzzing and forensic analysis for AI-agent workflows"** (engine *ChronoFuzz*, test pack *AuthorityDecay*). Early-stage; explicitly "no production-agent vulnerability detection or integration is implemented yet". |
| Code | One module (`core.py`, ≈75 LOC): a synthetic approval-expiry scenario on a **SimPy 4.x** virtual clock, boundary fuzzer and CLI `prawe`. 5 pytest tests. Python ≥3.10. License undecided. |
| CI | `.github/workflows/test.yml`: pytest on Python 3.10/3.12/3.13 (ubuntu). |
| Specs | `docs/FOUNDATION.md` (SimPy decision). No RevocationGap material. |
| RevocationGap | **Not present.** No repository named `RevocationGap` exists under the account (GitHub search: 0 results). |

## 2. Relationship to RevocationGap

The two projects share a *theme* (authority that is valid when granted but invalid by the time it is exercised; boundary-focused temporal testing; deterministic virtual-clock fixtures) but differ in target and method:

| Aspect | PraWe-miTnegA (existing) | RevocationGap (this package) |
|---|---|---|
| Target | AI-agent workflows (planning vs execution time) | Real identity providers, APIs, sessions, tokens |
| Method | Schedule mutation on a simulated clock | Controlled experiments on live/lab systems measuring real continued access |
| Foundation | SimPy 4.x | Schemathesis (version-pinned) + Authlib |
| Outcome | Invariant violation in a synthetic model | Bounded exposure intervals with uncertainty and classification |

**Reuse decision.** No code is shared. RevocationGap does **not** depend on PraWe-miTnegA or SimPy: the RevocationGap laboratory must drive *real asyncio I/O* (HTTP servers, WebSockets) and needs an injectable `Clock`/`Scheduler` that also exists in production; a SimPy `Environment` cannot drive real sockets (see ADR-0006 in `04-ARCHITECTURE/DECISIONS/`, to be authored in RG-P03-001; SimPy is re-evaluated for the *pure-simulation* lab mode in RG-P09-001). The AuthorityDecay idea of boundary-offset mutation around an expiry instant is acknowledged as prior inspiration for RevocationGap's "boundary-focused probe schedule" (RG-P05-008).

## 3. Preservation and placement

* Existing files are untouched; all RevocationGap content is added under `revocationgap/` (roadmap §2, OQ-001).
* The existing CI workflow runs `pytest` at repo root only; RevocationGap's own CI is specified in RG-P13-002 and would be added as a separate workflow scoped to `revocationgap/**`, leaving the existing workflow unchanged.
* The existing README's license statement ("License selection is pending") means the repository has **no license file**. RevocationGap's license decision (candidate: Apache-2.0, compatible with Schemathesis MIT, Authlib BSD-3, Authlib/Hypothesis MPL-2.0 as a dependency not vendored) is recorded in RG-P01-001/RG-P13-003 and is not applied to files outside `revocationgap/`.

## 4. Environment constraints discovered

* Git push is permitted only to branches named `claude/*`; work is on `claude/revocationgap-spec` (push verified 2026-10-12).
* Network access to PyPI, GitHub and public docs is available; no IdP tenants (Entra/Okta/Auth0) or Docker daemon are assumed available to the specification agents. Provider behaviour is therefore established from vendor documentation, and every statement not exercised against a live system is labelled documented-not-observed.
