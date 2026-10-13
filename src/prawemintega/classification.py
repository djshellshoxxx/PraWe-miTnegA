"""Conservative outcome labels for replay-verified synthetic authorization data.

These labels never assert a vulnerability in an actual identity provider or agent.
Real-world verdicts need independently sourced policy expectations and observations.
"""
from __future__ import annotations

from typing import Any

from .campaign import verify_campaign
from .evidence import verify_evidence


def classify_evidence(record: dict[str, Any]) -> dict[str, Any]:
    """Classify one synthetic run after validating its evidence and replay."""
    if not verify_evidence(record):
        return {"outcome": "inconclusive", "verified": False}
    scenario = record["scenario"]
    finding = record["finding"]
    execution = scenario["execution_at"]
    invalid_at_execution = (
        execution >= scenario["revocation_at"]
        or (scenario["expiry_at"] is not None and execution >= scenario["expiry_at"])
    )
    if not invalid_at_execution:
        outcome = "not_applicable"
    elif finding["violation"]:
        outcome = "synthetic_violation"
    else:
        outcome = "enforced"
    return {"outcome": outcome, "verified": True}


def classify_campaign(record: dict[str, Any]) -> dict[str, Any]:
    """Aggregate only verified campaign cases, without unsupported risk claims."""
    if not verify_campaign(record):
        return {"verified": False, "outcome": "inconclusive"}
    counts: dict[str, int] = {}
    for case in record["cases"]:
        outcome = classify_evidence(case)["outcome"]
        counts[outcome] = counts.get(outcome, 0) + 1
    return {"verified": True, "counts": dict(sorted(counts.items()))}
