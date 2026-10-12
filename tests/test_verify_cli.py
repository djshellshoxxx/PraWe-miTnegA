"""End-to-end verification of stored synthetic campaign evidence."""
import json
import subprocess
import sys

from prawemintega.campaign import CampaignConfig, run_campaign
from prawemintega.evidence import build_evidence
from prawemintega.revocation import RevocationScenario, run_revocation_scenario


def invoke(*args):
    return subprocess.run(
        [sys.executable, "-m", "prawemintega.verify_cli", *args],
        text=True, capture_output=True,
    )


def test_verify_campaign_file(tmp_path):
    path = tmp_path / "campaign.json"
    path.write_text(json.dumps(run_campaign(CampaignConfig(5, (-1, 0, 1)))), encoding="utf-8")
    result = invoke(str(path))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["valid"] is True
    assert json.loads(result.stdout)["kind"] == "campaign"


def test_verify_single_scenario_file(tmp_path):
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(build_evidence(run_revocation_scenario(RevocationScenario(5, 7)))), encoding="utf-8")
    result = invoke(str(path))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["kind"] == "scenario"


def test_verify_rejects_tampered_campaign(tmp_path):
    path = tmp_path / "campaign.json"
    record = run_campaign(CampaignConfig(5, (0, 1)))
    record["summary"]["violations"] = 999
    path.write_text(json.dumps(record), encoding="utf-8")
    result = invoke(str(path))
    assert result.returncode == 1
    assert json.loads(result.stdout)["valid"] is False


def test_verify_rejects_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{broken", encoding="utf-8")
    result = invoke(str(path))
    assert result.returncode == 1
    assert json.loads(result.stdout)["valid"] is False


def test_verify_missing_file_is_error(tmp_path):
    result = invoke(str(tmp_path / "missing.json"))
    assert result.returncode == 2


def test_verify_rejects_oversized_input(tmp_path):
    path = tmp_path / "large.json"
    path.write_bytes(b" " * 1048577)
    result = invoke(str(path), "--max-bytes", "1048576")
    assert result.returncode == 2
