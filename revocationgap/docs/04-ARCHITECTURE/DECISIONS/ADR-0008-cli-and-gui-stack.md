# ADR-0008 — `click` CLI; local FastAPI + Jinja2 + htmx + SSE GUI; shared application service layer

* **Status:** Accepted · **Owner:** RG-P03-001 (detail: RG-P10-001/004)
* **Alternatives.** Typer (thin layer on click), argparse; SPA (React/Vite) + REST, Textual TUI, Electron.
* **Decision.** `click` (already transitive via ST) + `rich` for output; GUI served only on `127.0.0.1` (random token in URL/cookie, Host/Origin checks, CSRF tokens), server-rendered templates with htmx and Server-Sent Events for the live timeline — no Node toolchain, so packaging stays pure Python. CLI, GUI and automation API are thin adapters over one `ApplicationService` (RG-P03-010) so behaviour cannot diverge.
* **Consequences.** Less rich client interactivity than an SPA; chart rendering via server-side SVG/Plotly-free inline SVG (RG-P08-011).
* **Verification.** Contract tests of ApplicationService; GUI end-to-end with Playwright (P12-005).
