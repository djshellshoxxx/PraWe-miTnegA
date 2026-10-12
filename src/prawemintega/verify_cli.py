"""Inspect and verify stored synthetic evidence without executing external targets."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .campaign import verify_campaign
from .evidence import verify_evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify synthetic revocation evidence")
    parser.add_argument("file", type=Path, help="JSON evidence file")
    parser.add_argument("--max-bytes", type=int, default=10485760,
                        help="Maximum input size, default 10 MiB")
    args = parser.parse_args(argv)
    if not 1 <= args.max_bytes <= 104857600:
        parser.error("--max-bytes must be between 1 and 104857600")
    try:
        with args.file.open("rb") as stream:
            raw = stream.read(args.max_bytes + 1)
        if len(raw) > args.max_bytes:
            parser.error("evidence exceeds max-bytes limit")
    except OSError as exc:
        parser.error(f"cannot read evidence: {exc}")
    try:
        record = json.loads(raw)
        kind = "campaign" if isinstance(record, dict) and record.get("engine") == "synthetic-revocation-campaign-v1" else "scenario"
        valid = verify_campaign(record) if kind == "campaign" else verify_evidence(record)
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError, TypeError):
        kind = "unknown"
        valid = False
    print(json.dumps({"kind": kind, "valid": bool(valid)}, sort_keys=True))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
