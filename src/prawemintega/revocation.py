"""Deterministic, synthetic authorization revocation scenarios.

This module uses a virtual SimPy clock and has no external network or IdP side effects.
A deliberately stale cached-authorization mode is a regression fixture, not a real exploit.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Iterable

import simpy


@dataclass(frozen=True)
class RevocationScenario:
    revocation_at: float
    execution_at: float
    expiry_at: float | None = None
    cached_authorization: bool = False


@dataclass(frozen=True)
class TimelineEvent:
    time: float
    kind: str


@dataclass(frozen=True)
class RevocationResult:
    scenario: RevocationScenario
    action_allowed: bool
    violation: bool
    events: tuple[TimelineEvent, ...]


def _validate_time(name: str, value: float, *, positive: bool = False) -> None:
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    if value < 0 or (positive and value == 0):
        raise ValueError(f"{name} must be non-negative" if not positive else f"{name} must be positive")


def run_revocation_scenario(scenario: RevocationScenario) -> RevocationResult:
    """Run one approval, one revocation, and one execution in virtual time.

    The authority is granted at t=0. A revocation at time T takes effect
    before an execution scheduled at T. An expiry at T is exclusive.
    The policy oracle independently checks actual validity at execution.
    """
    _validate_time("revocation_at", scenario.revocation_at)
    _validate_time("execution_at", scenario.execution_at)
    if scenario.expiry_at is not None:
        _validate_time("expiry_at", scenario.expiry_at, positive=True)

    env = simpy.Environment()
    events: list[TimelineEvent] = [TimelineEvent(0.0, "approval_granted")]
    revoked = False
    outcome: dict[str, bool] = {}

    def revoke():
        nonlocal revoked
        yield env.timeout(scenario.revocation_at)
        revoked = True
        events.append(TimelineEvent(float(env.now), "approval_revoked"))

    def execute():
        yield env.timeout(scenario.execution_at)
        actual_valid = not revoked and (
            scenario.expiry_at is None or env.now < scenario.expiry_at
        )
        allowed = bool(scenario.cached_authorization or actual_valid)
        outcome["allowed"] = allowed
        outcome["violation"] = bool(allowed and not actual_valid)
        events.append(TimelineEvent(float(env.now), "action_allowed" if allowed else "action_denied"))

    # Creating the revocation process first guarantees that equal-time
    # revocation/execution events resolve with revocation precedence.
    env.process(revoke())
    env.process(execute())
    env.run()
    return RevocationResult(
        scenario=scenario,
        action_allowed=outcome["allowed"],
        violation=outcome["violation"],
        events=tuple(events),
    )


def fuzz_revocation_schedule(
    scenario: RevocationScenario,
    *,
    offsets: Iterable[float] = (-1, 0, 1),
) -> list[RevocationResult]:
    """Find reproducible post-revocation authorization violations.

    Offsets are relative to the revocation time. Invalid candidate times
    are rejected before they can reach the virtual scheduler.
    """
    _validate_time("revocation_at", scenario.revocation_at)
    _validate_time("execution_at", scenario.execution_at)
    if scenario.expiry_at is not None:
        _validate_time("expiry_at", scenario.expiry_at, positive=True)
    candidates: set[float] = set()
    for offset in offsets:
        if not isinstance(offset, (int, float)) or not math.isfinite(offset):
            raise ValueError("offset must be finite")
        when = scenario.revocation_at + offset
        if not math.isfinite(when):
            raise ValueError("candidate execution time must be finite")
        if when >= 0:
            candidates.add(float(when))
    findings = [
        run_revocation_scenario(replace(scenario, execution_at=when))
        for when in sorted(candidates)
    ]
    return [result for result in findings if result.violation]
