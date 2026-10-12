"""End-to-end CLI tests for synthetic authorization experiments."""
import json
import subprocess
import sys


def invoke(*args):
    return subprocess.run([sys.executable, "-m", "prawemintega.revocation_cli", *args], capture_output=True, text=True)


def test_cli_produces_verifiable_evidence():
    result = invoke("--revocation", "5", "--execution", "6", "--cached-authorization")
    assert result.returncode == 0, result.stderr
    record = json.loads(result.stdout)
    assert record["finding"]["violation"] is True
    from prawemintega.evidence import verify_evidence
    assert verify_evidence(record)


def test_cli_returns_clean_policy_result():
    result = invoke("--revocation", "5", "--execution", "6")
    assert result.returncode == 0
    assert json.loads(result.stdout)["finding"]["violation"] is False


def test_cli_rejects_nonfinite_times():
    result = invoke("--revocation", "nan", "--execution", "6")
    assert result.returncode != 0
    assert not result.stdout
    assert "finite" in result.stderr


def test_cli_never_writes_file_on_invalid_input(tmp_path):
    target = tmp_path / "evidence.json"
    result = invoke("--revocation", "inf", "--execution", "2", "--output", str(target))
    assert result.returncode != 0
    assert not target.exists()


def test_cli_can_write_evidence_file(tmp_path):
    target = tmp_path / "evidence.json"
    result = invoke("--revocation", "4", "--execution", "5", "--output", str(target))
    assert result.returncode == 0
    assert not result.stdout
    from prawemintega.evidence import verify_evidence
    assert verify_evidence(json.loads(target.read_text(encoding="utf-8")))
