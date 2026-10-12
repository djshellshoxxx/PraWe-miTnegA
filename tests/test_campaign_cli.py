"""Command-line campaign regression tests."""
import json
import subprocess
import sys


def run(*args):
    return subprocess.run([sys.executable, "-m", "prawemintega.campaign_cli", *args], text=True, capture_output=True)


def test_campaign_cli_emits_verified_results():
    p = run("--revocation", "5", "--offsets=-1,0,1", "--cached-authorization")
    assert p.returncode == 0, p.stderr
    record = json.loads(p.stdout)
    from prawemintega.campaign import verify_campaign
    assert verify_campaign(record)
    assert record["summary"] == {"cases": 3, "violations": 2}


def test_campaign_cli_can_write_file(tmp_path):
    path = tmp_path / "results.json"
    p = run("--revocation", "5", "--offsets=0,1", "--output", str(path))
    assert p.returncode == 0, p.stderr
    assert not p.stdout
    from prawemintega.campaign import verify_campaign
    assert verify_campaign(json.loads(path.read_text()))


def test_campaign_cli_refuses_existing_output(tmp_path):
    path = tmp_path / "results.json"
    path.write_text("original")
    p = run("--revocation", "5", "--offsets=0", "--output", str(path))
    assert p.returncode != 0
    assert path.read_text() == "original"


def test_campaign_cli_rejects_nonfinite_and_empty_offsets():
    for offsets in ("nan", "inf", ""):
        p = run("--revocation", "5", "--offsets=" + offsets)
        assert p.returncode != 0
        assert not p.stdout


def test_campaign_cli_rejects_excessive_mutations():
    p = run("--revocation", "5", "--offsets=0,1,2,3", "--max-cases", "2")
    assert p.returncode != 0
