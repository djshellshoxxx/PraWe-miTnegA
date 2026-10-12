"""Versioned evidence manifests for synthetic authorization experiments.

The SHA-256 digest detects accidental changes, not malicious forgery: no
signature or trusted timestamp is provided. Verification also replays the
synthetic scenario and compares the complete deterministic evidence payload.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict
from typing import Any

from .revocation import RevocationResult, RevocationScenario, run_revocation_scenario


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ensure_ascii=True,
    ).encode("utf-8")


def _digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def build_evidence(result: RevocationResult) -> dict[str, Any]:
    """Produce a deterministic, JSON-compatible, synthetic test record."""
    # Replay to ensure callers cannot package an internally inconsistent result.
    expected = run_revocation_scenario(result.scenario)
    if result != expected:
        raise ValueError("result does not match the replayed synthetic scenario")
    payload: dict[str, Any] = {
        "schema_version": 1,
        "engine": "synthetic-revocation-v1",
        "scenario": asdict(result.scenario),
        "finding": {
            "action_allowed": result.action_allowed,
            "violation": result.violation,
        },
        "events": [
            {"sequence": i, "time": event.time, "kind": event.kind}
            for i, event in enumerate(result.events)
        ],
    }
    payload["sha256"] = _digest(payload)
    return payload


def verify_evidence(record: dict[str, Any]) -> bool:
    """Validate digest and independently replay the exact synthetic timeline.

    This validates a self-contained synthetic fixture only, not authenticity
    or policy compliance of an external identity provider.
    """
    try:
        if not isinstance(record, dict) or record.get("schema_version") != 1:
            return False
        if type(record["schema_version"]) is not int:
            return False
        if not isinstance(record.get("sha256"), str):
            return False
        without_digest = {k: v for k, v in record.items() if k != "sha256"}
        if record["sha256"] != _digest(without_digest):
            return False
        scenario_input = record["scenario"]
        if not isinstance(scenario_input, dict):
            return False
        expected = build_evidence(
            run_revocation_scenario(RevocationScenario(**scenario_input))
        )
        return record == expected
    except (TypeError, ValueError, KeyError, OverflowError, AttributeError, RecursionError):
        return False


def evidence_json(result: RevocationResult) -> str:
    """Canonical UTF-8-compatible JSON suitable for CI artifacts."""
    return _canonical(build_evidence(result)).decode("utf-8") + "\n"
