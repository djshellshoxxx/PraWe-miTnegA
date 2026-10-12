# ADR-0014 — Laboratory has two execution modes: virtual-time in-process and real-time over sockets

* **Status:** Accepted · **Owner:** RG-P03-001 (detail: RG-P09-001)
* **Decision.** (1) **Virtual-time mode:** mock IdP and mock services are in-process ASGI/WSGI apps invoked through ST's in-process transport (or direct calls via the `HttpTransport` port) under a virtual `Clock`/`Scheduler`; a 24-hour token lifetime scenario runs in milliseconds and is fully deterministic. (2) **Real-time mode:** the same mock apps served on localhost sockets (and Keycloak in a container) for end-to-end realism, real clocks. Every lab-mode run is labelled in evidence (`transport.kind`, `clock.kind`) and reports never mix virtual-time results with live-target conclusions.
* **Alternatives.** Real-time only (slow, non-deterministic); virtual-time only (misses socket/TLS/pool effects).
* **Verification.** Same scenario passes in both modes with equal classification (P09-005).
