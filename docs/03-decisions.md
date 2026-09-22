# Decisions

Short records, newest last. A decision is changed by a new entry, not by editing an old one.

| # | Date | Decision | Why |
|---|---|---|---|
| D1 | 2026-09-21 | Name the project **demosift** | "Demos" is the community's word for demonstrations, "sift" is sorting good from bad; free on PyPI, one homonymous repository on GitHub |
| D2 | 2026-09-21 | Python 3.12, `uv`, a single `src/` package | One package is enough until a second deployable exists; `uv` gives a lock file and fast CI |
| D3 | 2026-09-21 | Region `eu-central-1`; default model `eu.anthropic.claude-sonnet-5` through the EU cross-region profile | AgentCore and the EU inference profiles were verified available there on 2026-09-18 for the author's previous project; EU data residency for a European author |
| D4 | 2026-09-21 | Read LeRobot codebase **v3.0 only**; refuse other versions with an explicit error | The Hub's current format; supporting v2.1 doubles the reader for datasets that are being migrated anyway. Revisit when a user asks |
| D5 | 2026-09-21 | Deterministic core, models narrate | A report whose numbers come from a model cannot be trusted or tested; the inspection is code, the model writes prose over it |
| D6 | 2026-09-21 | Apache-2.0 | The licence of LeRobot and of most of the ecosystem; permissive, with a patent grant |
| D7 | 2026-09-21 | Download only `meta/` at milestone 0 | Metadata weighs kilobytes, data and videos weigh gigabytes; frame-level audits will download selectively |
| D8 | 2026-09-21 | Strands Agents as the agent framework, the `bedrock_agentcore` SDK for the Runtime contract | Both are AWS's first-party choices for AgentCore; the author already knows them |
| D9 | 2026-09-21 | GitHub organization **undecided**; the repository starts under the author's personal account | No organization exists yet; moving a repository later keeps its history and redirects |
| D10 | 2026-09-21 | Terraform layout inherited from `cgp-ai`: `modules/` and `envs/<env>/<layer>/`, one state per layer, partial backend | Known to the author; scales to staging and prod without restructuring |
| D11 | 2026-09-21 | A model-free `inspect` mode in the Runtime | Free and instant answers whenever no model is needed; the deterministic baseline for testing the narrative |
