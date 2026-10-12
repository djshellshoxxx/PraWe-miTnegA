# ADR-0006 — Dual-clock instants with explicit uncertainty; injectable Clock/Scheduler; own virtual-time implementation

* **Status:** Accepted · **Owner:** RG-P03-001 (detail: RG-P02-001, RG-P03-006)
* **Context.** The product's claim is a *bounded interval*. Wall clocks jump (NTP, VM pause); server `Date` has 1 s resolution; Keycloak `start-dev` omits `Date` (V-lab).
* **Alternatives.** Single wall-clock timestamps (simple; wrong under adjustments); monotonic only (no cross-system correlation); SimPy environment (sibling project) for simulation — cannot drive real sockets; **`TimeInstant` = (wall_ns, mono_ns, clock_id, uncertainty_ns) from an injectable `Clock`**.
* **Decision.** All durations between local events are computed from `mono_ns`; wall time is used only for display, cross-system correlation and provider-log joins, always with an uncertainty. Remote times are a distinct type (`RemoteInstant`) with `resolution_ns` and a `ClockDomain`; conversion to local time requires a `ClockOffset` estimate carrying its own uncertainty (RG-P08-002). Production code never calls `time.time()`/`time.monotonic()`/`asyncio.sleep` directly (lint-enforced); a virtual-time `Clock` + loop drives the lab deterministically.
* **Consequences.** Slight verbosity; makes determinism and fault injection (skew, jumps) first-class.
* **Verification.** Lint rule RG-LINT-001; clock-skew property tests (P12-002).
