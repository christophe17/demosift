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
                      (Lambda tool    (Claude vision   outliers        (dataset card,
                      on parquet,     on sampled       (embeddings,    via Identity +
                      via Gateway)    frames; Nova     clusters,       Hub OAuth)
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
| Code Interpreter | Running code the agent writes for a free-form question on a finished report ("plot joint 3 in episode 12"); never the fixed audits, which are Lambdas (D16) | later, with the conversation on a report |
| Memory | Conversational context for the conversation on a finished report ("why did episode 7 fail?"), across turns and sessions. Not audit history and not thresholds: those are queryable records and live in the public instance's table | 2 |
| Policy | Cedar rules on the Gateway: the write tool is callable only on the signed-in user's own datasets, and only after the consent step. This is the structural answer to an injection arriving through a task text or a dataset card (`docs/05-cost-and-security.md` §4) | 1 |
| Evaluations | Judging the narrative against the deterministic inspection; the gold-set metrics | 3 |

**Browser is not used**: the Hub has a complete API, so driving a browser would be tool
exposure, not a need. A service with no work to do is not wired in.

**Decided (D16, 2026-09-25): the fixed audits are Lambdas, Code Interpreter is for improvised
code only.** The numeric and visual audits are our own code: deterministic, tested, unchanging.
Deterministic code has nothing to do in a sandbox for improvised execution; it runs as
functions behind the Gateway, deployed by the public instance. Code Interpreter earns its
place only where the agent writes code that was not planned, the free-form question on a
finished report, which arrives with that conversation.

## 4. Execution units

One library, several thin entrypoints. "Multi-agent" does not mean multi-container: the
Strands graph of the orchestrator, the audit agents and the writer lives in one process, and
AgentCore isolates each user session in its own micro-VM and scales to zero between two.
What must not live in that process is heavy work: from milestone 2 an audit downloads
gigabytes of video, decodes frames and calls a vision model per episode, and doing that inside
the agent's session ties batch compute to the process that converses.

| Entrypoint | Does | Runs where | Deployed by |
|---|---|---|---|
| CLI | Everything, locally, without AWS | The user's laptop | Nobody, `pip install` |
| Runtime container (§5) | The agent: orchestrate, call tools, narrate. Thin; it does not crunch | AgentCore Runtime | The public instance (`demosift-web`) |
| Audit functions | The numeric audit, the visual audit of one episode: pure functions of this library | Lambda, exposed to the agent through Gateway and fed by the instance's queue | The public instance, as thin handlers over these functions (D16) |

demosift ships the library, the image and the functions; the public instance decides how many
deployables there are and wires them.

## 5. The container contract

What the public instance, or anyone else, relies on when running the image. Verified by
running it locally (`JOURNAL.md`, 2026-09-21).

| Item | Value |
|---|---|
| Image | Built by `services/runtime/Dockerfile`, `linux/arm64`, Python 3.12, non-root user (uid 10001), no persistent state |
| Listens | `0.0.0.0:8080` |
| `GET /ping` | Health: `{"status": "Healthy", ...}` |
| `POST /invocations` | JSON in, JSON out, the request and response of §2: `dataset_id` and `mode` in; `passed`, `inspection`, `markdown`, `latency_seconds`, and in `agent` mode `narrative`, `usage`, `model_id` out |
| Environment | `DEMOSIFT_MODEL_ID` (default `eu.anthropic.claude-sonnet-5`), `DEMOSIFT_REGION` (default `eu-central-1`), `DEMOSIFT_LOG_LEVEL`, `DEMOSIFT_HF_CACHE_DIR` (writable), `HF_TOKEN` optional for private datasets |
| Needs at runtime | Network egress to `huggingface.co`; in `agent` mode, `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` on the configured model or inference profile; nothing else. `inspect` mode calls no model and needs no AWS permission |
| Logs | Structured lines on stdout; never a token, never a user's data |

Anything the image needs that is not in this table is a bug in this table.

## 6. Data flow and storage

- **Inputs** stay on the Hub. Only `meta/` is downloaded at milestone 0; milestone 1
  downloads the `data/` chunks needed for the numeric audit; milestone 2 downloads video
  files episode by episode and extracts sampled frames.
- **Outputs** are the report (returned to the caller, later written into the dataset card)
  and, from milestone 3, the labels produced by the visual audit, stored as a versioned
  table because they become the training set of the cost cascade.
- **Nothing personal** is stored: a dataset id, a report, timings and token counts.
