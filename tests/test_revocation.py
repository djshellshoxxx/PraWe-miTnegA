"""Regression tests for synthetic revocation and delayed authorization checks."""

import math

import pytest

from prawemintega.revocation import (
    RevocationScenario,
    fuzz_revocation_schedule,
    run_revocation_scenario,
)


def test_action_before_revocation_is_permitted():
    result = run_revocation_scenario(
        RevocationScenario(revocation_at=10, execution_at=5)
    )
    assert result.action_allowed
    assert not result.violation
    assert [event.kind for event in result.events] == [
        "approval_granted", "action_allowed", "approval_revoked"
    ]


def test_action_at_revocation_is_denied():
    result = run_revocation_scenario(
        RevocationScenario(revocation_at=10, execution_at=10)
    )
    assert not result.action_allowed
    assert not result.violation
    assert [event.kind for event in result.events] == [
        "approval_granted", "approval_revoked", "action_denied"
    ]


def test_cached_approval_violation_after_revocation():
    result = run_revocation_scenario(
        RevocationScenario(revocation_at=5, execution_at=8, cached_authorization=True)
    )
    assert result.action_allowed
    assert result.violation
    assert result.events[-1].kind == "action_allowed"
    assert result.events[-1].time == 8.0


def test_revocation_at_zero_takes_effect_before_action():
    result = run_revocation_scenario(
        RevocationScenario(revocation_at=0, execution_at=0)
    )
    assert not result.action_allowed
    assert not result.violation


def test_expiration_is_independent_of_revocation():
    result = run_revocation_scenario(
        RevocationScenario(revocation_at=20, execution_at=10, expiry_at=10)
    )
    assert not result.action_allowed
    assert not result.violation


def test_cached_approval_cannot_bypass_expiry_without_violation():
    result = run_revocation_scenario(
        RevocationScenario(revocation_at=20, execution_at=10, expiry_at=10, cached_authorization=True)
    )
    assert result.action_allowed
    assert result.violation


def test_fuzzer_is_deterministic_and_returns_verified_findings_only():
    scenario = RevocationScenario(revocation_at=10, execution_at=0, cached_authorization=True)
    a = fuzz_revocation_schedule(scenario, offsets=(-2, 0, 2))
    b = fuzz_revocation_schedule(scenario, offsets=(2, -2, 0))
    assert a == b
    assert [finding.scenario.execution_at for finding in a] == [10.0, 12.0]
    assert all(finding.violation for finding in a)


def test_compliant_fuzzer_has_no_findings():
    scenario = RevocationScenario(revocation_at=10, execution_at=0)
    assert fuzz_revocation_schedule(scenario, offsets=(-1, 0, 1)) == []


@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf, -1])
def test_invalid_revocation_time_is_rejected(invalid):
    with pytest.raises(ValueError):
        run_revocation_scenario(RevocationScenario(revocation_at=invalid, execution_at=2))


@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf, -1])
def test_invalid_execution_time_is_rejected(invalid):
    with pytest.raises(ValueError):
        run_revocation_scenario(RevocationScenario(revocation_at=2, execution_at=invalid))


def test_invalid_mutation_offset_is_rejected():
    with pytest.raises(ValueError):
        fuzz_revocation_schedule(RevocationScenario(revocation_at=5, execution_at=0), offsets=(math.nan,))


def test_invalid_expiry_is_rejected():
    with pytest.raises(ValueError):
        run_revocation_scenario(RevocationScenario(revocation_at=5, execution_at=6, expiry_at=math.inf))
