"""Report command regression tests for replay-verified synthetic evidence."""
import json
import subprocess
import sys

from prawemintega.campaign import CampaignConfig, run_campaign
from prawemintega.evidence import build_evidence
from prawemintega.revocation import RevocationScenario, run_revocation_scenario


def invoke(path):
    return subprocess.run([sys.executable, "-m", "prawemintega.report_cli", str(path)], text=True, capture_output=True)


def test_report_classifies_valid_campaign(tmp_path):
    path = tmp_path / "campaign.json"
    path.write_text(json.dumps(run_campaign(CampaignConfig(5, (-1, 0, 1), cached_authorization=True))))
    result = invoke(path)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["verified"] is True
    assert report["scope"] == "synthetic_only"
    assert report["counts"] == {"not_applicable": 1, "synthetic_violation": 2}


def test_report_classifies_single_evidence(tmp_path):
    path = tmp_path / "scenario.json"
    record = build_evidence(run_revocation_scenario(RevocationScenario(5, 6)))
    path.write_text(json.dumps(record))
    result = invoke(path)
    assert result.returncode == 0
    assert json.loads(result.stdout)["outcome"] == "enforced"


def test_report_rejects_modified_evidence(tmp_path):
    path = tmp_path / "scenario.json"
    record = build_evidence(run_revocation_scenario(RevocationScenario(5, 6)))
    record["finding"]["violation"] = True
    path.write_text(json.dumps(record))
    result = invoke(path)
    assert result.returncode == 1
    assert json.loads(result.stdout)["outcome"] == "inconclusive"


def test_report_rejects_missing_file(tmp_path):
    result = invoke(tmp_path / "missing.json")
    assert result.returncode == 2


def test_report_rejects_oversized_file(tmp_path):
    path = tmp_path / "large.json"
    path.write_bytes(b" " * (10 * 1024 * 1024 + 1))
    result = invoke(path)
    assert result.returncode == 2
