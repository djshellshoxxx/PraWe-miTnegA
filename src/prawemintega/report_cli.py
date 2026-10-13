"""Offline report generation from replay-verifiable synthetic evidence.

No real identity-provider vulnerability conclusion is made by this tool.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .classification import classify_campaign, classify_evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify synthetic revocation evidence")
    parser.add_argument("file", type=Path, help="Evidence JSON file")
    parser.add_argument("--max-bytes", type=int, default=10 * 1024 * 1024)
    args = parser.parse_args(argv)
    if not 1 <= args.max_bytes <= 100 * 1024 * 1024:
        parser.error("max-bytes must be between 1 and 104857600")
    try:
        with args.file.open("rb") as stream:
            raw = stream.read(args.max_bytes + 1)
        if len(raw) > args.max_bytes:
            parser.error("evidence exceeds max-bytes limit")
    except OSError as exc:
        parser.error(f"cannot read evidence: {exc}")
    try:
        record = json.loads(raw)
        if isinstance(record, dict) and record.get("engine") == "synthetic-revocation-campaign-v1":
            report = classify_campaign(record)
            if not report["verified"]:
                report["outcome"] = "inconclusive"
        else:
            report = classify_evidence(record)
    except (ValueError, TypeError, RecursionError, UnicodeError):
        report = {"verified": False, "outcome": "inconclusive"}
    report["scope"] = "synthetic_only"
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return 0 if report["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
