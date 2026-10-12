"""Bounded, reproducible synthetic temporal mutation campaigns.

This module operates only on in-memory SimPy test fixtures. Records contain
complete per-case evidence and are replay-verifiable; hashes are not signatures.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Iterable, Any

from .evidence import build_evidence, verify_evidence
from .revocation import RevocationScenario, run_revocation_scenario


@dataclass(frozen=True)
class CampaignConfig:
    revocation_at: float
    offsets: Iterable[float]
    cached_authorization: bool = False
    expiry_at: float | None = None
    max_cases: int = 1000


def _serialize(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_serialize(payload).encode("utf-8")).hexdigest()


def run_campaign(config: CampaignConfig) -> dict[str, Any]:
    """Execute no more than max_cases distinct, non-negative candidate times."""
    if type(config.max_cases) is not int or not 1 <= config.max_cases <= 10000:
        raise ValueError("max_cases must be an integer limit between 1 and 10000")
    if type(config.revocation_at) not in (int, float) or not math.isfinite(config.revocation_at) or config.revocation_at < 0:
        raise ValueError("revocation_at must be finite and non-negative")
    candidates: set[float] = set()
    for offset in config.offsets:
        if type(offset) not in (float, int) or not math.isfinite(offset):
            raise ValueError("offset must be a finite number")
        execution = config.revocation_at + offset
        if not math.isfinite(execution):
            raise ValueError("computed execution must be finite")
        if execution >= 0:
            candidates.add(float(execution))
        if len(candidates) > config.max_cases:
            raise ValueError("campaign case limit exceeded")
    cases = [
        build_evidence(run_revocation_scenario(RevocationScenario(
            revocation_at=config.revocation_at,
            execution_at=execution,
            expiry_at=config.expiry_at,
            cached_authorization=config.cached_authorization,
        )))
        for execution in sorted(candidates)
    ]
    payload: dict[str, Any] = {
        "schema_version": 1,
        "engine": "synthetic-revocation-campaign-v1",
        "cases": cases,
        "summary": {
            "cases": len(cases),
            "violations": sum(1 for case in cases if case["finding"]["violation"]),
        },
    }
    payload["sha256"] = _hash(payload)
    return payload


def verify_campaign(record: dict[str, Any]) -> bool:
    """Check integrity, case ordering, and exact deterministic replay."""
    try:
        if type(record) is not dict or record.get("schema_version") != 1:
            return False
        if record.get("engine") != "synthetic-revocation-campaign-v1":
            return False
        cases = record["cases"]
        if type(cases) is not list or len(cases) > 10000:
            return False
        if any(not verify_evidence(case) for case in cases):
            return False
        times = [case["scenario"]["execution_at"] for case in cases]
        if times != sorted(set(times)):
            return False
        expected = {
            "cases": len(cases),
            "violations": sum(1 for case in cases if case["finding"]["violation"]),
        }
        if record["summary"] != expected:
            return False
        payload = {k: v for k, v in record.items() if k != "sha256"}
        return len(record) == 5 and record.get("sha256") == _hash(payload)
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        return False


def campaign_json(record: dict[str, Any]) -> str:
    if not verify_campaign(record):
        raise ValueError("cannot serialize invalid campaign evidence")
    return _serialize(record) + "\n"
