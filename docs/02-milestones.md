# Milestones

Each milestone ships something usable on its own, so a pause between two costs nothing.
Work happens on one milestone at a time (`CLAUDE.md` §4.5); ideas outside it become issues.

| # | Milestone | Content | Status |
|---|---|---|---|
| 0 | **Foundation** | Terraform (budget, ECR, AgentCore Runtime), the level-0 inspection as CLI and as an agent, authentication and per-user quota in front of the Runtime, observability, a first invocation measured; the faithfulness test of the agent's narrative | in progress |
| 1 | **Numeric audit** | Frame-level checks on the parquet data: timestamp gaps, frozen frames, action and state ranges, jerk; run through Code Interpreter; Hub API as Gateway tools; the report written into the dataset card with the user's consent; security replayed on poisoned datasets before write-back goes live; first users | planned |
| 2 | **Visual audit v0** | Uniformly sampled frames per episode sent to a vision model with a fixed rubric (occlusion, lighting, missing object, failed demonstration); everything through the strong model at this scale to produce labels; cost measured per frame; every published metric from N runs with intervals | planned |
| 3 | **Gold set** | About two hundred episodes annotated by hand; the visual audit calibrated against them (precision, recall, Cohen's kappa per criterion); gold-set replay before any prompt or model change; Evaluations wired | planned |
| 4 | **Modes, outliers, coverage** | Trajectory features, clustering of behaviour modes, ranked outliers, workspace coverage map with gaps | later |
| 5 | **Cascade and thresholds** | Cheap classifier on embeddings, calibration, conformal thresholds on a false-alarm budget, the cost-versus-quality curve | later |
| 6 | **Curation impact** | Train an imitation policy on raw versus curated data and measure the difference | later |

## How the audit proves itself

An audit tool that is not itself measured is an opinion. These are the measurements the tool
needs to be trusted, each introduced at the milestone where it first matters.

1. **Faithfulness of the narrative (milestone 0).** The agent's text is checked against the
   inspection JSON it was given: every number, camera key and task text in the narrative must
   appear in the JSON, the inspection tool must have been called, and no other tool exists.
   A narrative that fails is discarded and the deterministic Markdown is returned instead.
2. **No conclusion from a single run (milestone 2).** Model outputs are not reproducible. Any
   metric published about them — agreement, precision, cost per frame — comes from N runs
   (N = 3 in CI, N = 10 for published numbers) with a 95 % bootstrap interval, and a comparison
   between two prompts or models is reported as "not significant" when the intervals overlap.
3. **Calibration of the visual audit (milestone 3).** The vision model's verdicts are compared
   with the hand-annotated gold set: precision and recall with Wilson intervals, and Cohen's
   kappa per criterion. The rubric asks for the justification before the verdict, frame order
   is permuted where frames are compared, and the model that judges narratives is not the
   model that wrote them. A criterion with kappa below 0.6 is published as *indicative*, never
   as a verdict, until its rubric improves.
4. **Replay before change (milestone 3).** Before any change of prompt, rubric or model, the
   new version is run on the gold set and the metrics of item 3 are compared with the current
   version; the go/no-go and the numbers go into `JOURNAL.md`.
5. **Security is measured, not asserted (milestone 1).** See `docs/05-cost-and-security.md` §4.

## Definition of done of the first pass (milestones 0–3)

| Someone checks | The pass delivers |
|---|---|
| It runs, without asking the author | A public URL, sign-in with Hugging Face OAuth, a dataset id in, a report out |
| It is visible in the ecosystem | The report is written into the dataset card with a link back to the tool |
| It is measured | The README table: datasets audited, episodes processed, latency and cost per audit, precision and recall of the visual audit on the gold set with intervals |
| It is serious engineering | Terraform, CI, tests, Observability traces one can consult, a one-page architecture, a decisions log |
| It is safe to expose | Per-user quota, Bedrock budget cap with alarm, secrets out of the code, Apache-2.0 |
| Someone else uses it | Audits launched by strangers, issues opened |

## Excluded from the first pass

No clustering or coverage map, no model cascade, no calibration, no policy training. These
are milestones 4–6 and they build on the labels the first pass produces.
