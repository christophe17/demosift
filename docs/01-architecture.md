# Architecture

What the library is, what it is not, and how a deployment uses it. The guiding rule is
`CLAUDE.md` §4.1: no model and no network beyond the Hub, so that every number is reproducible
from code.

## 1. What it is and is not

```
   demosift (this repository, public)              a deployment (elsewhere)
 ┌──────────────────────────────────────┐        ┌──────────────────────────────────────┐
 │ format reader ─▶ inspection ─▶ report │        │ pip install demosift==x.y.z          │
 │        ▲                              │        │   ├─ a queue and workers running the │
 │   Hub access (meta/ only)             │  ───▶  │   │  audit on request                │
 │   CLI over the same functions         │        │   ├─ an assistant whose tools are    │
 │   command-line image                  │        │   │  these functions                 │
 └──────────────────────────────────────┘        │   └─ a front end, sign-in, storage    │
                                                  └──────────────────────────────────────┘
```

The library is the whole audit. A deployment adds the things that exist only because there
are users to serve: a way to ask for an audit, a place to keep it, someone to explain it. None
of that changes a single number, which is why none of it is here.

## 2. Modules

| Module | Responsibility | Depends on |
|---|---|---|
| `demosift.format` | Parse `meta/` of a v3.0 dataset into typed objects; refuse other versions | pandas, pyarrow, pydantic |
| `demosift.hub` | Download only `meta/` (`snapshot_download` with patterns); accept a local directory | huggingface_hub |
| `demosift.inspection` | Facts (cameras, tasks, lengths) and consistency checks; robust outliers on length | format |
| `demosift.report` | Markdown card, plain text for a terminal, JSON | inspection, click |
| `demosift.config` | The two environment variables the library reads: cache directory, log level | |
| `demosift.cli` | `inspect` with `--format` (text, markdown, json), over the same functions | click, everything above |

## 3. The public surface

`demosift/__init__.py` re-exports what a caller needs, so that nothing deeper is imported:

| Name | What it is |
|---|---|
| `resolve_source(spec, cache_dir=None) -> Path` | A local root for a Hub id or an existing directory |
| `fetch_meta(dataset_id, revision=None, cache_dir=None, token=None) -> Path` | The download alone |
| `load_meta(root) -> DatasetMeta` | Parsed `meta/` |
| `inspect_root(root, dataset_id=None) -> Inspection`, `inspect_meta(meta, dataset_id)` | The level-0 inspection |
| `Inspection`, `Check`, `DatasetMeta`, `UnsupportedFormatError` | The types a caller stores, branches on, or catches |
| `to_markdown(inspection) -> str`, `to_text(inspection, *, width=100, color=False) -> str`, `to_json(inspection) -> str` | Renderings: a dataset card or a file, a terminal, a tool |
| `__version__` | |

`Inspection` is a Pydantic model; `model_dump(mode="json")` is the storable form. This surface
is a contract (`CLAUDE.md` §4.8): additions are minor versions, removals are major ones.

## 4. Where the library goes next

Each milestone adds functions to the same surface, in the same spirit: deterministic where the
problem is deterministic, and where a model's judgement is needed, an interface plus a
calibration, never a model client.

| Milestone | Added to the library | Model involved? |
|---|---|---|
| 1 | Frame-level numeric audit on the `data/` parquet files: timestamp regularity, frozen frames, action and state ranges, jerk; selective download of the chunks an episode needs | No |
| 2 | Visual audit: frame sampling per episode, the rubric, parsing of a judge's structured answer, and the calibration of that judge against the gold set. The judge itself is a `VisionJudge` protocol the caller implements (a callable from image bytes and rubric to a structured verdict); the library ships a fixture judge for tests, never a real one | Through the caller |
| 3 | Gold-set tooling: annotation format, precision and recall with Wilson intervals, Cohen's kappa per criterion | No |
| 4 | Trajectory features, clustering of behaviour modes, ranked outliers, workspace coverage map | No |
| 5 | The cascade: cheap classifier on embeddings, calibration, conformal thresholds on a false-alarm budget | Through the caller |

The `VisionJudge` protocol is defined when milestone 2 opens, not before: an interface with
no implementation behind it is speculation.

## 5. How a deployment uses it

- **Install a released version, pinned**: `pip install demosift==x.y.z` (or the git tag until
  PyPI exists). A deployment never builds from a checkout, so the number a user sees was
  produced by a tagged, tested release.
- **Call the functions from wherever the work runs**: a serverless function importing
  `inspect_root` is the whole numeric audit; an assistant's tool wrapping the same call is the
  whole of what the assistant may state about a dataset.
- **Store `Inspection.model_dump(mode="json")`** and render with `to_markdown` when a person
  reads it.
- **Bring your own model** for the visual audit, behind the protocol of §4, and publish its
  calibration before publishing its verdicts.

The hosted instance at `demosift.io` does exactly this; its architecture is its own document
in its own repository.

## 6. Data flow

Only `meta/` is downloaded today, into the Hub cache (`DEMOSIFT_HF_CACHE_DIR`, or
`huggingface_hub`'s default). Milestone 1 downloads the `data/` chunks an audit needs and no
more; milestone 2 downloads video per episode and decodes sampled frames. Nothing is written
anywhere but that cache. Nothing personal is ever read: a dataset id, its public files, and
for private ones the token the caller already holds.
