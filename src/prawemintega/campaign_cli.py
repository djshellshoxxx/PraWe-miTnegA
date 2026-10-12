"""CLI for bounded deterministic synthetic revocation campaigns."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .campaign import CampaignConfig, campaign_json, run_campaign


def _offsets(value: str) -> tuple[float, ...]:
    try:
        if not value.strip():
            raise ValueError("offsets must not be empty")
        return tuple(float(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid offsets: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run bounded synthetic authorization timing mutations")
    parser.add_argument("--revocation", type=float, required=True, help="Virtual revocation time")
    parser.add_argument("--offsets", type=_offsets, required=True, help="Comma-separated execution offsets")
    parser.add_argument("--expiry", type=float, help="Optional authorization expiry")
    parser.add_argument("--cached-authorization", action="store_true", help="Use intentionally defective synthetic fixture")
    parser.add_argument("--max-cases", type=int, default=1000, help="Maximum distinct test executions")
    parser.add_argument("--output", type=Path, help="New JSON output file (must not exist)")
    args = parser.parse_args(argv)
    try:
        record = run_campaign(CampaignConfig(
            revocation_at=args.revocation,
            offsets=args.offsets,
            expiry_at=args.expiry,
            cached_authorization=args.cached_authorization,
            max_cases=args.max_cases,
        ))
        data = campaign_json(record)
    except (TypeError, ValueError, OverflowError) as exc:
        parser.error(str(exc))
    if args.output is None:
        sys.stdout.write(data)
    else:
        try:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(data)
        except OSError as exc:
            parser.error(f"unable to write campaign evidence: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
