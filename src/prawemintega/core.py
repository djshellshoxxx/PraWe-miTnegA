"""Synthetic authorization-lifetime scenarios on a SimPy virtual clock.

A deliberately defective cached-approval policy is included strictly as a test fixture.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Iterable

import simpy


@dataclass(frozen=True)
class ScenarioResult:
    expiry: float
    execution: float
    action_allowed: bool
    violation: bool
    events: tuple[dict[str, Any], ...]


def run_authorization_scenario(
    *, expiry: float, execution: float, buggy_cached_authorization: bool = False
) -> ScenarioResult:
    """Execute a synthetic approval scenario; expiry is exclusive.

    Authorization is checked at execution time by the correct policy. The
    defective mode deliberately reuses approval obtained at virtual time zero.
    """
    if not math.isfinite(expiry) or not math.isfinite(execution):
        raise ValueError("expiry and execution must be finite")
    if expiry <= 0 or execution < 0:
        raise ValueError("expiry must be positive and execution must be non-negative")

    env = simpy.Environment()
    events: list[dict[str, Any]] = [{"time": 0.0, "event": "approval_granted"}]
    outcome: dict[str, bool] = {}

    def operation():
        yield env.timeout(execution)
        allowed = bool(buggy_cached_authorization or env.now < expiry)
        outcome["allowed"] = allowed
        events.append({"time": float(env.now), "event": "action_allowed" if allowed else "action_denied"})

    env.process(operation())
    env.run()
    allowed = outcome["allowed"]
    return ScenarioResult(
        expiry=float(expiry),
        execution=float(execution),
        action_allowed=allowed,
        violation=bool(allowed and execution >= expiry),
        events=tuple(events),
    )


def fuzz_authorization_expiry(
    *, expiry: float, offsets: Iterable[float] = (-1, 0, 1), buggy_cached_authorization: bool = False
) -> list[ScenarioResult]:
    """Boundary-focused schedule mutation returning only verified violations."""
    if not math.isfinite(expiry):
        raise ValueError("expiry must be finite")
    if expiry <= 0:
        raise ValueError("expiry must be positive")
    candidates = set()
    for offset in offsets:
        if not math.isfinite(offset):
            raise ValueError("offsets must be finite")
        execution = expiry + offset
        if not math.isfinite(execution):
            raise ValueError("computed execution must be finite")
        if execution >= 0:
            candidates.add(float(execution))
    candidates = sorted(candidates)
    return [r for when in candidates if (r := run_authorization_scenario(
        expiry=expiry, execution=when, buggy_cached_authorization=buggy_cached_authorization
    )).violation]


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic temporal authorization fuzzer")
    parser.add_argument("--expiry", type=float, default=10)
    parser.add_argument("--buggy-fixture", action="store_true", help="enable intentionally vulnerable synthetic policy")
    args = parser.parse_args()
    findings = fuzz_authorization_expiry(expiry=args.expiry, buggy_cached_authorization=args.buggy_fixture)
    print(json.dumps({"finding_count": len(findings), "findings": [asdict(r) for r in findings]}, indent=2))


if __name__ == "__main__":
    main()
