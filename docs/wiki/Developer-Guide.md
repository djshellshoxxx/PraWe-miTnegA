# Developer Guide

```sh
python -m pip install -e '.[dev]'
python -m pytest              # 73 tests pass on this snapshot
```

Console commands (from `pyproject.toml`): `prawe`, `prawe-revocation`, `prawe-campaign`, `prawe-verify`.
The only runtime dependency is SimPy 4.x (`simpy>=4.1,<5`). Python 3.10 or newer.
CI: `.github/workflows/test.yml`.
