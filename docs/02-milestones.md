# Milestones

Each milestone ships something usable on its own, as a release of the library. Work happens on
one milestone at a time (`CLAUDE.md` §4.4); ideas outside it become issues.

| # | Milestone | Content | Status |
|---|---|---|---|
| 0 | **Foundation** | The level-0 inspection as a library and a CLI, the command-line image, CI, the release workflow (wheel, GitHub release, image); the public surface documented; the learning guide | `v0.2.0` ready to tag |
| 1 | **Numeric audit** | Frame-level checks on the parquet data: timestamp gaps, frozen frames, action and state ranges, jerk; selective download; every reader bounded against hostile input | planned |
| 2 | **Visual audit** | Frame sampling per episode, the rubric, parsing of a judge's structured verdict, the `VisionJudge` protocol and a fixture judge; the calibration tooling that turns a judge's output into verdicts only once measured | planned |
| 3 | **Gold set tooling** | Annotation format for about two hundred hand-labelled episodes; precision and recall with Wilson intervals; Cohen's kappa per criterion; replay of a judge against the gold set | planned |
| 4 | **Modes, outliers, coverage** | Trajectory features, clustering of behaviour modes, ranked outliers, workspace coverage map with gaps | later |
| 5 | **Cascade and thresholds** | Cheap classifier on embeddings, calibration, conformal thresholds on a false-alarm budget, the cost-versus-quality curve | later |
| 6 | **Curation impact** | Train an imitation policy on raw versus curated data and measure the difference | later |

## How the audit proves itself

An audit tool that is not itself measured is an opinion. These are the measurements the tool
needs to be trusted, each introduced at the milestone where it first matters.

1. **Determinism (milestone 0).** The same dataset revision produces the same report, byte
   for byte; the tests assert it on recorded fixtures and on deliberate corruptions of them.
2. **Hostile input is bounded (milestone 1).** Every reader has a size bound and an explicit
   error; a malformed or oversized file becomes a named failure, never a crash or a silently
   wrong number (`docs/05`).
3. **No conclusion from a single run (milestone 2).** A model's verdicts are not reproducible.
   Any metric published about a judge, agreement, precision, cost per frame, comes from N runs
   (N = 3 in CI, N = 10 for published numbers) with a 95 % bootstrap interval; two judges or
   rubrics whose intervals overlap are reported as "not significant".
4. **Calibration before verdicts (milestone 3).** A judge's output is compared with the
   hand-annotated gold set: precision and recall with Wilson intervals, Cohen's kappa per
   criterion. A criterion with kappa below 0.6 is published as *indicative*, never as a
   verdict, until its rubric improves.
5. **Replay before change (milestone 3).** Before any change of rubric, sampling or judge, the
   new version is run on the gold set and compared with the current one; the go/no-go and the
   numbers go into `JOURNAL.md`.

## Definition of done of the first pass (milestones 0–3)

| Someone checks | The pass delivers |
|---|---|
| It is installable and honest | `pip install demosift`, one command, a report that says what it cannot see |
| It is measured | The README table: latencies, dependency count, test coverage; from milestone 2, the judge's precision and recall on the gold set with intervals |
| It is serious engineering | CI, tests on real recorded data, a one-page architecture, a decisions log, a versioned public surface |
| It is safe to point at anything | Bounded downloads, explicit errors on hostile input, no credential but the caller's Hub token |
| Someone else uses it | Installs from the release, issues opened, the hosted instance runs it |

## Excluded from the first pass

No clustering or coverage map, no cascade, no policy training. These are milestones 4–6 and
build on the labels the first pass produces. And, permanently: no model client, no agent, no
server, no deployment.
