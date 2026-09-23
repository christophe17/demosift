# Architecture

What exists at milestone 0, and the target the later milestones grow into. The guiding rule
is in `CLAUDE.md` §4.1: the core is deterministic and the models narrate, classify or judge
on top of it — never the other way round.

## 1. Today (milestone 0)

```
                 laptop                                   AgentCore Runtime (linux/arm64 container)
┌───────────────────────────────┐        ┌──────────────────────────────────────────────────────┐
│ demosift inspect <id>         │        │ POST /invocations {"dataset_id", "mode"}             │
│   resolve_source ─▶ Hub meta/ │        │   handle(payload)                                    │
│   load_meta ─▶ inspect_meta   │        │     inspect_dataset_impl ─▶ Inspection ─▶ Markdown   │
│   to_markdown / to_json       │        │     mode=agent: Strands Agent on Bedrock             │
└───────────────────────────────┘        │        └─ tool inspect_dataset (same code path)      │
                                         │   GET /ping                                          │
                                         └──────────────────────────────────────────────────────┘
```

| Component | Module | Responsibility |
|---|---|---|
| Format reader | `demosift.format` | Parse `meta/` of a v3.0 dataset into typed objects; refuse other versions |
| Hub access | `demosift.hub` | Download only `meta/` (`snapshot_download` with patterns); accept a local directory |
| Inspection | `demosift.inspection` | Facts (cameras, tasks, lengths) and consistency checks; robust outliers on length |
| Report | `demosift.report` | Markdown card and JSON |
| Agent | `demosift.agent` | Strands agent with one tool; system prompt forbids inventing numbers |
| Runtime | `demosift.runtime` | AgentCore Runtime entrypoint; `inspect` mode without any model call |
| CLI | `demosift.cli` | `inspect`, `agent`, `serve` |

**Why a model-free mode exists.** Every request that can be answered without a model is
answered without one: it is free, instant and reproducible, and it gives the deterministic
baseline that the agent's narrative is compared against in tests. The `agent` mode exists to
exercise the Bedrock path end to end and to measure its cost and latency (see the numbers
table in `README.md`).

## 2. Request flow through AgentCore Runtime

1. A client calls the Runtime's invocation endpoint with a JSON payload, authenticated by IAM
   SigV4: the CLI with the operator's credentials, and the public instance's worker with its
   own role (`demosift-web`, D12). The Runtime never sees an end user's token; end-user
   sign-in, quotas and history are the public instance's job, not this repository's. AgentCore
   starts or resumes a session.
2. The SDK routes the payload to `invoke()`, which delegates to `handle()` — a pure function
   so the tests call it without an HTTP server.
3. `handle()` downloads `meta/` from the Hub (cached in the container's Hub cache), builds the
   `Inspection`, renders it, and in `agent` mode asks the Strands agent to narrate it. The
   agent's only tool re-runs the same inspection; nothing else is reachable.
4. The response carries the inspection JSON, the Markdown, the narrative, token usage and
   the latency, so every number a later document quotes is in the response itself.

## 3. Target layout (milestones 1–5)

```
                         ┌──────────────── orchestrator agent (Runtime) ────────────────┐
                         │ reads meta, plans the audit, fans out per episode, aggregates │
                         └───┬───────────────┬───────────────┬───────────────┬──────────┘
                             ▼               ▼               ▼               ▼
                      numeric audit    visual audit    coverage &      report writer
                      (Code           (Claude vision   outliers        (dataset card,
                      Interpreter     on sampled       (embeddings,    via Identity +
                      on parquet)     frames; Nova     clusters,       Hub OAuth)
                                      first in the     gaps map)
                                      cascade)
                             │               │               │               │
                             └──────── Gateway: Hub API as MCP tools; Memory: past audits ─┘
```

| AgentCore service | Used for | From milestone |
|---|---|---|
| Runtime | Hosting the agents; sessions; scaling to zero | 0 |
| Observability | Traces of every tool call and model call; the latency and token numbers | 0 |
| Gateway | The Hugging Face Hub API (list files, read/write dataset cards) exposed as MCP tools with one credential | 1 |
| Identity | Vaulting a user's outbound Hugging Face grant so the agent can read their private datasets and write their dataset card as them; end-user sign-in itself happens in the public instance (`demosift-web`, its D3) | 1 |
| Code Interpreter | Running the numeric audit on parquet files in a sandbox instead of inside the agent container | 1 |
| Memory | Conversational context for the conversation on a finished report ("why did episode 7 fail?"), across turns and sessions. Not audit history and not thresholds: those are queryable records and live in the public instance's table | 2 |
| Policy | Cedar rules on the Gateway: the write tool is callable only on the signed-in user's own datasets, and only after the consent step. This is the structural answer to an injection arriving through a task text or a dataset card (`docs/05-cost-and-security.md` §4) | 1 |
| Evaluations | Judging the narrative against the deterministic inspection; the gold-set metrics | 3 |

**Browser is not used**: the Hub has a complete API, so driving a browser would be tool
exposure, not a need. A service with no work to do is not wired in.

**Open question on Code Interpreter (decide when milestone 1 opens).** The numeric audit is
our own code: deterministic, tested, unchanging. Its natural home is a Lambda behind the
Gateway, not a sandbox. Code Interpreter earns its place when the agent writes code that was
not planned, which is the free-form user question ("show me the distribution of joint 3 in
episode 12"). Milestone 1 decides on real usage: a Lambda for the fixed audit, Code
Interpreter for ad-hoc analysis, or both.

## 4. Data flow and storage

- **Inputs** stay on the Hub. Only `meta/` is downloaded at milestone 0; milestone 1
  downloads the `data/` chunks needed for the numeric audit; milestone 2 downloads video
  files episode by episode and extracts sampled frames.
- **Outputs** are the report (returned to the caller, later written into the dataset card)
  and, from milestone 3, the labels produced by the visual audit, stored as a versioned
  table because they become the training set of the cost cascade.
- **Nothing personal** is stored: a dataset id, a report, timings and token counts.
