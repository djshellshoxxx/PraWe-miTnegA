"""Command-line runner for deterministic synthetic revocation evidence."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .evidence import evidence_json
from .revocation import RevocationScenario, run_revocation_scenario


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a synthetic authorization revocation experiment")
    parser.add_argument("--revocation", required=True, type=float, help="Virtual revocation time")
    parser.add_argument("--execution", required=True, type=float, help="Virtual action time")
    parser.add_argument("--expiry", type=float, help="Optional authorization expiration time")
    parser.add_argument("--cached-authorization", action="store_true", help="Run intentionally defective synthetic fixture")
    parser.add_argument("--output", type=Path, help="Write the evidence JSON to this path")
    args = parser.parse_args(argv)
    try:
        scenario = RevocationScenario(
            revocation_at=args.revocation,
            execution_at=args.execution,
            expiry_at=args.expiry,
            cached_authorization=args.cached_authorization,
        )
        data = evidence_json(run_revocation_scenario(scenario))
    except (ValueError, OverflowError) as exc:
        parser.error(str(exc))
    if args.output is None:
        sys.stdout.write(data)
    else:
        # Refuse silent replacement of existing evidence.
        try:
            with args.output.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(data)
        except OSError as exc:
            parser.error(f"unable to write evidence: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
