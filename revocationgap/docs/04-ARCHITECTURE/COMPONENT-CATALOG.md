# Component Catalog

Every module has a stable id `MOD-<PACKAGE>-<SLUG>`, exactly one owning work element and one specification in `docs/06-MODULES/`. The table is generated from `docs/work-elements.yaml` (`python tools/specgate.py render`); responsibilities, interfaces and tests are in each module's spec (sections 4, 7, 22). Package meanings: `core`=`rg_core`, `idp`=`rg_idp`, `probe`=`rg_probe`, `stbridge`=`rg_stbridge` (the only Schemathesis importer), `lab`=`rg_lab`, `app`=`revocationgap` (engine, store, config, report renderers, CLI, GUI, API). See `SYSTEM-ARCHITECTURE.md` §3.

<!-- BEGIN:CATALOG -->
| Module id | Element | Package | Responsibility (element title) | Depends on | Spec | Status |
|---|---|---|---|---|---|---|
| MOD-CORE-TIME_AND_CLOCK_MODEL | RG-P02-001 | core | Time and clock model | P01-004, P03-001 | `06-MODULES/RG-P02-001-time-and-clock-model.md` | TODO |
| MOD-CORE-IDENTITY_PERMISSION_STATE | RG-P02-002 | core | Identity and permission state model | P02-001 | `06-MODULES/RG-P02-002-identity-permission-state.md` | TODO |
| MOD-CORE-CREDENTIAL_LIFECYCLE | RG-P02-003 | core | Credential, session and token lifecycle model | P02-002 | `06-MODULES/RG-P02-003-credential-lifecycle.md` | TODO |
| MOD-CORE-REVOCATION_EVENT_MODEL | RG-P02-004 | core | Revocation event model and event ordering | P02-003 | `06-MODULES/RG-P02-004-revocation-event-model.md` | TODO |
| MOD-CORE-EXPECTED_ENFORCEMENT_MODEL | RG-P02-005 | core | Expected enforcement model | P02-004 | `06-MODULES/RG-P02-005-expected-enforcement-model.md` | TODO |
| MOD-CORE-OBSERVATION_CONFIDENCE_MODEL | RG-P02-006 | core | Observation and confidence model | P02-004 | `06-MODULES/RG-P02-006-observation-confidence-model.md` | TODO |
| MOD-CORE-EXPERIMENT_STATE_MACHINE | RG-P02-007 | core | Experiment state machine and transitions | P02-005, P02-006 | `06-MODULES/RG-P02-007-experiment-state-machine.md` | TODO |
| MOD-CORE-TIMELINE_REPRESENTATION | RG-P02-008 | core | Timeline representation | P02-006 | `06-MODULES/RG-P02-008-timeline-representation.md` | TODO |
| MOD-CORE-OUTCOME_CLASSIFICATION | RG-P02-009 | core | Outcome classification rules | P02-005, P02-006, P02-007 | `06-MODULES/RG-P02-009-outcome-classification.md` | TODO |
| MOD-CORE-SCHEMA_SERIALIZATION | RG-P03-002 | core | Shared schema and serialization framework | P03-001 | `06-MODULES/RG-P03-002-schema-serialization.md` | TODO |
| MOD-APP-CONFIGURATION | RG-P03-003 | app | Configuration subsystem | P03-002 | `06-MODULES/RG-P03-003-configuration.md` | TODO |
| MOD-CORE-LOGGING_REDACTION | RG-P03-004 | core | Logging, tracing and redaction | P03-002 | `06-MODULES/RG-P03-004-logging-redaction.md` | TODO |
| MOD-CORE-ASYNC_ERRORS_CANCELLATION | RG-P03-005 | core | Async model, error taxonomy and cancellation | P03-002 | `06-MODULES/RG-P03-005-async-errors-cancellation.md` | TODO |
| MOD-CORE-SCHEDULER | RG-P03-006 | core | Scheduler abstraction and clock injection | P02-001, P03-005 | `06-MODULES/RG-P03-006-scheduler.md` | TODO |
| MOD-CORE-EVENT_BUS | RG-P03-007 | core | Event bus | P03-005 | `06-MODULES/RG-P03-007-event-bus.md` | TODO |
| MOD-APP-PERSISTENCE_STORE | RG-P03-008 | app | Persistence layer and evidence store | P03-002, P02-006 | `06-MODULES/RG-P03-008-persistence-store.md` | TODO |
| MOD-CORE-PLUGIN_ARCHITECTURE | RG-P03-009 | core | Plugin architecture | P03-002, P03-005 | `06-MODULES/RG-P03-009-plugin-architecture.md` | TODO |
| MOD-APP-EXPERIMENT_ENGINE | RG-P03-010 | app | Experiment orchestration engine and composition root | P02-007, P03-003, P03-006, P03-007, P03-008, P03-009 | `06-MODULES/RG-P03-010-experiment-engine.md` | TODO |
| MOD-APP-CROSS_PLATFORM_DEPLOYMENT | RG-P03-011 | app | Cross-platform deployment model | P03-001 | `06-MODULES/RG-P03-011-cross-platform-deployment.md` | TODO |
| MOD-IDP-IDP_ADAPTER_FRAMEWORK | RG-P04-001 | idp | Identity adapter framework and capability model | P02-004, P03-005, P03-009 | `06-MODULES/RG-P04-001-idp-adapter-framework.md` | TODO |
| MOD-IDP-OIDC_CLIENT | RG-P04-002 | idp | Generic OAuth/OIDC client (Authlib) | P04-001 | `06-MODULES/RG-P04-002-oidc-client.md` | TODO |
| MOD-IDP-TOKEN_JWT_ANALYSIS | RG-P04-003 | idp | Token handling and JWT analysis | P04-002, P02-003 | `06-MODULES/RG-P04-003-token-jwt-analysis.md` | TODO |
| MOD-IDP-INTROSPECTION_REVOCATION_LOGOUT | RG-P04-004 | idp | Introspection, revocation and logout endpoint clients | P04-002 | `06-MODULES/RG-P04-004-introspection-revocation-logout.md` | TODO |
| MOD-IDP-SESSION_COOKIE_ADAPTER | RG-P04-005 | idp | Session-cookie and application-session adapter | P04-001, P02-003 | `06-MODULES/RG-P04-005-session-cookie-adapter.md` | TODO |
| MOD-IDP-GENERIC_PROVIDER_ADAPTER | RG-P04-006 | idp | Generic standards-based test-service adapter | P04-003, P04-004 | `06-MODULES/RG-P04-006-generic-provider-adapter.md` | TODO |
| MOD-IDP-KEYCLOAK_ADAPTER | RG-P04-007 | idp | Keycloak adapter | P04-006, P00-005 | `06-MODULES/RG-P04-007-keycloak-adapter.md` | TODO |
| MOD-IDP-ENTRA_ADAPTER | RG-P04-008 | idp | Microsoft Entra ID adapter | P04-006, P00-005 | `06-MODULES/RG-P04-008-entra-adapter.md` | TODO |
| MOD-IDP-OKTA_ADAPTER | RG-P04-009 | idp | Okta adapter | P04-006, P00-005 | `06-MODULES/RG-P04-009-okta-adapter.md` | TODO |
| MOD-IDP-AUTH0_ADAPTER | RG-P04-010 | idp | Auth0 adapter | P04-006, P00-005 | `06-MODULES/RG-P04-010-auth0-adapter.md` | TODO |
| MOD-IDP-SSF_CAEP | RG-P04-011 | idp | SSF/CAEP event ingestion and transmission | P04-001, P03-007 | `06-MODULES/RG-P04-011-ssf-caep.md` | TODO |
| MOD-PROBE-PROBE_MODEL | RG-P05-001 | probe | Probe model and configuration | P02-006, P03-002 | `06-MODULES/RG-P05-001-probe-model.md` | TODO |
| MOD-PROBE-REQUEST_TEMPLATES | RG-P05-002 | probe | Request templates and variable substitution | P05-001 | `06-MODULES/RG-P05-002-request-templates.md` | TODO |
| MOD-PROBE-CREDENTIAL_INJECTION | RG-P05-003 | probe | Credential and session injection | P05-002, P02-003 | `06-MODULES/RG-P05-003-credential-injection.md` | TODO |
| MOD-PROBE-HTTP_TRANSPORT | RG-P05-004 | probe | Raw HTTP transport | P05-003, P02-001 | `06-MODULES/RG-P05-004-http-transport.md` | TODO |
| MOD-STBRIDGE-SCHEMATHESIS_BRIDGE | RG-P05-005 | stbridge | Schemathesis bridge: operation catalog and probe derivation | P05-004, P00-002 | `06-MODULES/RG-P05-005-schemathesis-bridge.md` | TODO |
| MOD-PROBE-RESPONSE_ASSERTIONS | RG-P05-006 | probe | Response assertion engine | P05-001 | `06-MODULES/RG-P05-006-response-assertions.md` | TODO |
| MOD-PROBE-BASELINE_CONTROLS | RG-P05-007 | probe | Baseline and negative-control validation | P05-006, P05-004 | `06-MODULES/RG-P05-007-baseline-controls.md` | TODO |
| MOD-PROBE-PROBE_SCHEDULING | RG-P05-008 | probe | Probe scheduling (post-revocation schedules) | P03-006, P05-007, P02-006 | `06-MODULES/RG-P05-008-probe-scheduling.md` | TODO |
| MOD-PROBE-RATE_LIMIT_RETRY | RG-P05-009 | probe | Rate limiting, retry and backoff | P05-004, P03-005 | `06-MODULES/RG-P05-009-rate-limit-retry.md` | TODO |
| MOD-PROBE-RESULT_NORMALIZATION | RG-P05-010 | probe | Result normalization | P05-006, P05-004, P02-006 | `06-MODULES/RG-P05-010-result-normalization.md` | TODO |
| MOD-PROBE-WEBSOCKET_PROBE | RG-P05-011 | probe | WebSocket persistence probe | P05-010, P05-003 | `06-MODULES/RG-P05-011-websocket-probe.md` | TODO |
| MOD-STBRIDGE-GRAPHQL_PROBES | RG-P05-012 | stbridge | GraphQL probes | P05-005, P05-011 | `06-MODULES/RG-P05-012-graphql-probes.md` | TODO |
| MOD-PROBE-REPLAY_REPRODUCIBILITY | RG-P05-013 | probe | Replay and reproducibility | P05-010, P03-008 | `06-MODULES/RG-P05-013-replay-reproducibility.md` | TODO |
| MOD-PROBE-PROBE_CONCURRENCY | RG-P05-014 | probe | Probe concurrency, failure recovery and cancellation | P05-008, P05-009, P05-010 | `06-MODULES/RG-P05-014-probe-concurrency.md` | TODO |
| MOD-CORE-REVOCATION_ACTION_FRAMEWORK | RG-P06-001 | core | Revocation action framework | P04-001, P02-004, P03-005 | `06-MODULES/RG-P06-001-revocation-action-framework.md` | TODO |
| MOD-APP-MANUAL_REVOCATION | RG-P06-002 | app | Manual revocation acknowledgment | P06-001 | `06-MODULES/RG-P06-002-manual-revocation.md` | TODO |
| MOD-IDP-ACCOUNT_ENTITLEMENT_ACTIONS | RG-P06-003 | idp | Account and entitlement removal actions (disable, delete, role, group) | P06-001, P04-006 | `06-MODULES/RG-P06-003-account-entitlement-actions.md` | TODO |
| MOD-IDP-SESSION_TOKEN_ACTIONS | RG-P06-004 | idp | Session termination and token revocation actions | P06-001, P04-004 | `06-MODULES/RG-P06-004-session-token-actions.md` | TODO |
| MOD-IDP-CREDENTIAL_RESET_ACTIONS | RG-P06-005 | idp | Password and credential reset actions | P06-001 | `06-MODULES/RG-P06-005-credential-reset-actions.md` | TODO |
| MOD-IDP-CONDITIONAL_ACCESS_DEVICE | RG-P06-006 | idp | Conditional Access and device compliance changes | P06-001, P04-008 | `06-MODULES/RG-P06-006-conditional-access-device.md` | TODO |
| MOD-IDP-SERVICE_IDENTITY_REVOCATION | RG-P06-007 | idp | Service identity (workload) revocation | P06-003 | `06-MODULES/RG-P06-007-service-identity-revocation.md` | TODO |
| MOD-IDP-EVENT_DRIVEN_REVOCATION | RG-P06-008 | idp | Event-driven and externally observed revocation | P06-001, P04-011 | `06-MODULES/RG-P06-008-event-driven-revocation.md` | TODO |
| MOD-CORE-REVOCATION_ANCHORING | RG-P06-009 | core | Revocation correlation and acknowledgment anchoring | P06-001, P02-004, P02-001 | `06-MODULES/RG-P06-009-revocation-anchoring.md` | TODO |
| MOD-CORE-RESTORATION_CLEANUP | RG-P06-010 | core | Restoration, cleanup and reactivation | P06-003, P06-004 | `06-MODULES/RG-P06-010-restoration-cleanup.md` | TODO |
| MOD-CORE-SCENARIO_DSL | RG-P07-001 | core | Scenario definition schema (declarative DSL) | P05-001, P06-001, P02-005 | `06-MODULES/RG-P07-001-scenario-dsl.md` | TODO |
| MOD-CORE-SCENARIO_CATALOG_A | RG-P07-002 | core | Scenario catalog A: credential and session lifecycle | P07-001, P06-004, P06-003 | `06-MODULES/RG-P07-002-scenario-catalog-a.md` | TODO |
| MOD-CORE-SCENARIO_CATALOG_B | RG-P07-003 | core | Scenario catalog B: authorization propagation and cross-service enforcement | P07-001, P06-003, P05-011 | `06-MODULES/RG-P07-003-scenario-catalog-b.md` | TODO |
| MOD-CORE-SCENARIO_CATALOG_C | RG-P07-004 | core | Scenario catalog C: events, ordering and reactivation | P07-001, P06-008, P06-010 | `06-MODULES/RG-P07-004-scenario-catalog-c.md` | TODO |
| MOD-STBRIDGE-SCENARIO_GENERATION | RG-P07-005 | stbridge | Automated temporal scenario generation | P07-002, P07-003, P07-004, P05-005 | `06-MODULES/RG-P07-005-scenario-generation.md` | TODO |
| MOD-CORE-EVIDENCE_COLLECTION | RG-P08-001 | core | Evidence collection and bundle format | P03-008, P05-010, P06-009 | `06-MODULES/RG-P08-001-evidence-collection.md` | TODO |
| MOD-CORE-CLOCK_ALIGNMENT | RG-P08-002 | core | Clock alignment and timestamp provenance | P02-001, P08-001 | `06-MODULES/RG-P08-002-clock-alignment.md` | TODO |
| MOD-CORE-EVENT_CORRELATION | RG-P08-003 | core | Event correlation engine | P08-002, P06-009 | `06-MODULES/RG-P08-003-event-correlation.md` | TODO |
| MOD-CORE-EXPOSURE_WINDOW | RG-P08-004 | core | Exposure window computation | P08-003, P02-006 | `06-MODULES/RG-P08-004-exposure-window.md` | TODO |
| MOD-CORE-CONFIDENCE_SCORING | RG-P08-005 | core | Confidence scoring | P08-004 | `06-MODULES/RG-P08-005-confidence-scoring.md` | TODO |
| MOD-CORE-FINDING_CLASSIFICATION | RG-P08-006 | core | Finding classification and false-positive reduction | P08-005, P02-009 | `06-MODULES/RG-P08-006-finding-classification.md` | TODO |
| MOD-CORE-DEDUP_REPRODUCIBILITY | RG-P08-007 | core | Duplicate detection and reproducibility scoring | P08-006, P05-013 | `06-MODULES/RG-P08-007-dedup-reproducibility.md` | TODO |
| MOD-CORE-ENFORCEMENT_BASELINES | RG-P08-008 | core | Provider enforcement baselines | P02-005, P08-006 | `06-MODULES/RG-P08-008-enforcement-baselines.md` | TODO |
| MOD-APP-HISTORICAL_REGRESSION | RG-P08-009 | app | Historical comparison and regression analysis | P08-007, P03-008 | `06-MODULES/RG-P08-009-historical-regression.md` | TODO |
| MOD-CORE-RISK_IMPACT_SCORING | RG-P08-010 | core | Risk and impact scoring | P08-006 | `06-MODULES/RG-P08-010-risk-impact-scoring.md` | TODO |
| MOD-APP-REPORTING | RG-P08-011 | app | Report data contracts and report generation | P08-006, P08-009, P08-010, P02-008 | `06-MODULES/RG-P08-011-reporting.md` | TODO |
| MOD-LAB-LAB_ARCHITECTURE | RG-P09-001 | lab | Lab architecture and deterministic virtual-time simulation | P03-006, P02-007 | `06-MODULES/RG-P09-001-lab-architecture.md` | TODO |
| MOD-LAB-MOCK_IDP | RG-P09-002 | lab | Mock identity provider | P09-001, P04-006 | `06-MODULES/RG-P09-002-mock-idp.md` | TODO |
| MOD-LAB-MOCK_SERVICES | RG-P09-003 | lab | Mock protected services and enforcement profiles | P09-002 | `06-MODULES/RG-P09-003-mock-services.md` | TODO |
| MOD-LAB-FAULT_INJECTION | RG-P09-004 | lab | Fault and clock injection | P09-003, P02-001 | `06-MODULES/RG-P09-004-fault-injection.md` | TODO |
| MOD-LAB-FIXTURES_DATASETS | RG-P09-005 | lab | Fixtures, expected datasets and fixture versioning | P09-004, P07-004 | `06-MODULES/RG-P09-005-fixtures-datasets.md` | TODO |
| MOD-LAB-KEYCLOAK_LAB | RG-P09-006 | lab | Keycloak integration laboratory | P04-007, P09-003 | `06-MODULES/RG-P09-006-keycloak-lab.md` | TODO |
| MOD-APP-CLI_CONTRACT | RG-P10-001 | app | CLI command contract | P03-010, P08-011, P07-001 | `06-MODULES/RG-P10-001-cli-contract.md` | TODO |
| MOD-APP-WORKSPACE_UX | RG-P10-002 | app | Project workspace and configuration UX | P10-001, P03-003 | `06-MODULES/RG-P10-002-workspace-ux.md` | TODO |
| MOD-APP-RUN_UX | RG-P10-003 | app | Experiment run UX: dry run and live timeline | P10-002, P08-011 | `06-MODULES/RG-P10-003-run-ux.md` | TODO |
| MOD-APP-GUI_ARCHITECTURE | RG-P10-004 | app | Local GUI architecture and internal web API | P10-001, P03-007 | `06-MODULES/RG-P10-004-gui-architecture.md` | TODO |
| MOD-APP-GUI_SCREENS | RG-P10-005 | app | GUI screens and interactions | P10-004, P10-003 | `06-MODULES/RG-P10-005-gui-screens.md` | TODO |
| MOD-APP-FINDINGS_UX | RG-P10-006 | app | Findings review, comparison and export UX | P10-005, P08-009 | `06-MODULES/RG-P10-006-findings-ux.md` | TODO |
| MOD-APP-AUTOMATION_API | RG-P10-007 | app | Automation API | P10-004 | `06-MODULES/RG-P10-007-automation-api.md` | TODO |
| MOD-APP-SECRETS_REDACTION | RG-P11-001 | app | Secret storage, credential lifecycle and redaction | P03-004, P03-008 | `06-MODULES/RG-P11-001-secrets-redaction.md` | TODO |
| MOD-APP-SCOPE_ENFORCEMENT | RG-P11-002 | app | Scope enforcement and authorization controls | P03-003, P06-001 | `06-MODULES/RG-P11-002-scope-enforcement.md` | TODO |
| MOD-APP-EVIDENCE_ENCRYPTION | RG-P11-003 | app | Encrypted evidence storage | P11-001, P08-001 | `06-MODULES/RG-P11-003-evidence-encryption.md` | TODO |
| MOD-CORE-PLUGIN_TRUST | RG-P11-004 | core | Plugin trust boundaries | P03-009, P11-002 | `06-MODULES/RG-P11-004-plugin-trust.md` | TODO |
| MOD-APP-RUN_RECOVERY | RG-P11-005 | app | Interrupted-run recovery | P03-010, P06-010 | `06-MODULES/RG-P11-005-run-recovery.md` | TODO |
| MOD-APP-DIAGNOSTICS_MIGRATIONS | RG-P11-006 | app | Diagnostics, updates, migrations and offline operation | P03-008, P03-011 | `06-MODULES/RG-P11-006-diagnostics-migrations.md` | TODO |
| MOD-APP-SUPPLY_CHAIN | RG-P11-007 | app | Dependency and supply-chain security | P03-011 | `06-MODULES/RG-P11-007-supply-chain.md` | TODO |
<!-- END:CATALOG -->
