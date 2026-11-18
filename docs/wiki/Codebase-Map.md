# Codebase Map

Descriptions below come from each module's docstring.

| I want to... | Look in |
|---|---|
| Synthetic authorisation-lifetime scenarios on a SimPy virtual clock (CLI `prawe`) | `src/prawemintega/core.py` |
| Bounded, reproducible synthetic temporal mutation campaigns | `src/prawemintega/campaign.py`, `campaign_cli.py` |
| Deterministic synthetic authorisation revocation scenarios | `src/prawemintega/revocation.py`, `revocation_cli.py` |
| Conservative outcome labels (these never assert a real-world vulnerability) | `src/prawemintega/classification.py` |
| Versioned evidence manifests with SHA-256 digests (detects accidental change, not forgery) | `src/prawemintega/evidence.py` |
| Inspect and verify stored synthetic evidence without touching external targets | `src/prawemintega/verify_cli.py` |
| Tests (8 files, 73 tests) | `tests/` |
| Foundation decision | `docs/FOUNDATION.md` |
| Packaging and console entry points | `pyproject.toml` |
