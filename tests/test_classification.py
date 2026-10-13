"""Tests for conservative synthetic authorization outcome classification."""
import pytest
from prawemintega.classification import classify_evidence, classify_campaign
from prawemintega.campaign import CampaignConfig, run_campaign
from prawemintega.evidence import build_evidence
from prawemintega.revocation import RevocationScenario, run_revocation_scenario


def scenario(revocation, execution, cached=False):
    return build_evidence(run_revocation_scenario(RevocationScenario(revocation, execution, cached_authorization=cached)))


def test_denied_action_after_revocation_is_enforced():
    assert classify_evidence(scenario(5, 6))["outcome"] == "enforced"


def test_allowed_action_before_revocation_is_not_applicable():
    assert classify_evidence(scenario(5, 4))["outcome"] == "not_applicable"


def test_cached_authorization_after_revocation_is_confirmed_fixture_violation():
    result = classify_evidence(scenario(5, 6, True))
    assert result["outcome"] == "synthetic_violation"
    assert result["verified"] is True


def test_boundary_at_revocation_is_enforced():
    assert classify_evidence(scenario(5, 5))["outcome"] == "enforced"


def test_invalid_evidence_is_inconclusive():
    record = scenario(5, 6, True)
    record["events"].clear()
    assert classify_evidence(record) == {"outcome": "inconclusive", "verified": False}


def test_campaign_classification_counts():
    record = run_campaign(CampaignConfig(5, (-1, 0, 1), cached_authorization=True))
    result = classify_campaign(record)
    assert result["verified"] is True
    assert result["counts"] == {"not_applicable": 1, "synthetic_violation": 2}


def test_tampered_campaign_is_inconclusive():
    record = run_campaign(CampaignConfig(5, (0, 1)))
    record["summary"]["cases"] = 99
    assert classify_campaign(record) == {"verified": False, "outcome": "inconclusive"}


def test_campaign_clean_case_classification():
    record = run_campaign(CampaignConfig(5, (-1, 0, 1)))
    assert classify_campaign(record)["counts"] == {"enforced": 2, "not_applicable": 1}
