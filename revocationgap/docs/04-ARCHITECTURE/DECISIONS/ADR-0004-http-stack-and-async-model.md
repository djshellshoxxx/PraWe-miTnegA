# ADR-0004 — One synchronous HTTP stack (`requests`/urllib3) + asyncio orchestration with bounded thread offload

* **Status:** Accepted · **Owner:** RG-P03-001 (detail: RG-P03-005, RG-P05-004/005)
* **Context.** Schemathesis' transport is `requests`; Authlib 1.8's httpx integration now requires `httpx2` (providers-b); WebSocket needs asyncio. Evidence must be comparable across IdP calls and target probes (same TLS, cookie, pooling semantics).
* **Alternatives.** (a) httpx/httpx2 everywhere (async-native; second stack beside ST; HTTP/2; unstable naming churn); (b) aiohttp; (c) **requests everywhere + `asyncio.to_thread`/bounded `ThreadPoolExecutor`, asyncio only for WebSocket and servers**.
* **Decision.** (c). The engine is an asyncio application; every blocking call (ST `Case.call`, Authlib/requests calls, SQLite) runs in a dedicated bounded executor per concern (`probe`, `idp`, `store`) so one slow target cannot starve scheduling. Timestamps are taken **inside the worker thread** immediately around the blocking call and also at submission (to measure queueing lateness).
* **Consequences.** No HTTP/2 or HTTP/3 probing in v1 (documented limitation); thread scaling limits (target ≤ 200 concurrent probes/process, to be validated RG-P12-004). A second implementation behind the same ports (httpx) remains possible.
* **Verification.** ISO-9/ISO-10; scheduling-lateness benchmark (P12-004).
