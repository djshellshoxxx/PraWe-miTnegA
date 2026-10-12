from prawemintega.core import run_authorization_scenario, fuzz_authorization_expiry


def test_allows_action_before_expiry():
    result = run_authorization_scenario(expiry=10, execution=5)
    assert result.violation is False
    assert result.action_allowed is True


def test_rejects_execution_at_expiry():
    result = run_authorization_scenario(expiry=10, execution=10)
    assert result.violation is False
    assert result.action_allowed is False


def test_detects_stale_authorization_at_execution():
    result = run_authorization_scenario(expiry=10, execution=11, buggy_cached_authorization=True)
    assert result.violation is True
    assert result.action_allowed is True


def test_fuzzer_finds_expiry_boundary():
    findings = fuzz_authorization_expiry(expiry=10, offsets=(-2, -1, 0, 1, 2), buggy_cached_authorization=True)
    assert [f.execution for f in findings] == [10, 11, 12]
    assert all(f.violation for f in findings)


def test_event_log_has_ordered_virtual_timestamps():
    result = run_authorization_scenario(expiry=10, execution=11)
    times = [event["time"] for event in result.events]
    assert times == sorted(times)
