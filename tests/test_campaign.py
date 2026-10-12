"""Regression tests for finite, deterministic synthetic mutation campaigns."""
import math

import pytest

from prawemintega.campaign import CampaignConfig, run_campaign, campaign_json, verify_campaign


def test_campaign_reproduces_violations_at_revocation_boundary():
    config = CampaignConfig(revocation_at=10, offsets=(-2, 0, 2), cached_authorization=True)
    record = run_campaign(config)
    assert record["summary"] == {"cases": 3, "violations": 2}
    assert [case["scenario"]["execution_at"] for case in record["cases"]] == [8.0, 10.0, 12.0]
    assert verify_campaign(record)


def test_campaign_is_order_independent_and_reproducible():
    first = run_campaign(CampaignConfig(revocation_at=8, offsets=(2, -1, 2, 0)))
    second = run_campaign(CampaignConfig(revocation_at=8, offsets=(-1, 0, 2)))
    assert first == second
    assert campaign_json(first) == campaign_json(second)
    assert verify_campaign(first)


def test_campaign_verification_rejects_changed_result():
    record = run_campaign(CampaignConfig(revocation_at=3, offsets=(0, 1), cached_authorization=True))
    record["summary"]["violations"] = 0
    assert not verify_campaign(record)


def test_campaign_limit_blocks_excessive_executions():
    with pytest.raises(ValueError, match="limit"):
        run_campaign(CampaignConfig(revocation_at=3, offsets=range(100), max_cases=5))


def test_campaign_rejects_bool_or_nonfinite_offsets():
    for offset in (True, math.nan, math.inf):
        with pytest.raises(ValueError):
            run_campaign(CampaignConfig(revocation_at=3, offsets=(offset,)))


def test_campaign_zero_and_negative_candidate_handling():
    record = run_campaign(CampaignConfig(revocation_at=0, offsets=(-1, 0, 1), cached_authorization=True))
    assert [case["scenario"]["execution_at"] for case in record["cases"]] == [0.0, 1.0]
    assert record["summary"] == {"cases": 2, "violations": 2}


def test_campaign_limits_raw_mutation_inputs_even_if_all_duplicate():
    from itertools import repeat
    with pytest.raises(ValueError, match="input limit"):
        run_campaign(CampaignConfig(revocation_at=3, offsets=repeat(0), max_cases=5))


def test_campaign_rejects_invalid_expiry_with_no_cases():
    with pytest.raises(ValueError):
        run_campaign(CampaignConfig(revocation_at=3, offsets=(), expiry_at=math.inf))


def test_campaign_rejects_boolean_revocation_time():
    with pytest.raises(ValueError):
        run_campaign(CampaignConfig(revocation_at=True, offsets=(0,)))
