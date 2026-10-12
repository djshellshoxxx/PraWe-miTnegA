"""Tests for versioned, deterministic, secret-free revocation evidence."""
import json
from dataclasses import replace

import pytest

from prawemintega.evidence import (
    build_evidence, evidence_json, verify_evidence,
)
from prawemintega.revocation import RevocationScenario, run_revocation_scenario


def test_evidence_reproducible_and_round_trips():
    result = run_revocation_scenario(RevocationScenario(revocation_at=5, execution_at=6, cached_authorization=True))
    a = build_evidence(result)
    b = build_evidence(result)
    assert a == b
    assert a["schema_version"] == 1
    assert a["finding"]["violation"] is True
    assert verify_evidence(a)
    assert json.loads(evidence_json(result)) == a


def test_evidence_order_and_boundary_trace():
    result = run_revocation_scenario(RevocationScenario(revocation_at=3, execution_at=3))
    evidence = build_evidence(result)
    assert [e["kind"] for e in evidence["events"]] == [
        "approval_granted", "approval_revoked", "action_denied"
    ]
    assert [e["sequence"] for e in evidence["events"]] == [0, 1, 2]
    assert verify_evidence(evidence)


def test_evidence_detects_modified_event():
    data = build_evidence(run_revocation_scenario(RevocationScenario(revocation_at=1, execution_at=2)))
    data["events"][-1]["kind"] = "action_allowed"
    assert not verify_evidence(data)


def test_evidence_detects_modified_policy_outcome():
    data = build_evidence(run_revocation_scenario(RevocationScenario(revocation_at=1, execution_at=2)))
    data["finding"]["violation"] = True
    assert not verify_evidence(data)


def test_evidence_rejects_unsupported_schema_version():
    data = build_evidence(run_revocation_scenario(RevocationScenario(revocation_at=1, execution_at=2)))
    data["schema_version"] = 999
    assert not verify_evidence(data)


def test_evidence_refuses_noncanonical_types():
    data = build_evidence(run_revocation_scenario(RevocationScenario(revocation_at=1, execution_at=2)))
    data["events"][0]["time"] = float("nan")
    assert not verify_evidence(data)
