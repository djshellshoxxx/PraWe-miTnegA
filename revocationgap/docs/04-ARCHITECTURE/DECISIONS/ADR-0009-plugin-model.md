# ADR-0009 — Entry-point plugins with capability declaration; in-process, trusted-by-installation

* **Status:** Accepted · **Owner:** RG-P03-001 (detail: RG-P03-009, RG-P11-004)
* **Alternatives.** Sandboxed subprocess plugins (strong isolation, heavy IPC), WASM, config-only extension; **Python entry points (`importlib.metadata`)**.
* **Decision.** Groups: `revocationgap.idp_adapters`, `.transports`, `.revocation_actions`, `.assertions`, `.report_renderers`, `.scenario_packs`, `.baselines`. Each plugin exposes a `PluginManifest` (id, version, api_version, capabilities, required permissions such as `network`, `secrets:read`). Loading requires the plugin id on an operator allow-list; unknown plugins are listed but not loaded. Plugins run **in-process with full trust** (documented honestly: installation = trust); no claim of sandboxing. API versioning by `api_version` major.
* **Verification.** Plugin conformance tests (P12-003), allow-list tests (P11-004).
