# Bounds and robustness

Anyone can publish a dataset, and the library will be pointed at anything. It has no cost to
bound (it calls no model) and no secret to protect (only the caller's Hub token, which it never
sees). What it must do is refuse hostile or broken input with a named error, never a crash and
never a silently wrong number. This document lists the bounds, when each arrives, and what is
measured.

## 1. Bounds, in the order they arrive

| Bound | Mechanism | Milestone |
|---|---|---|
| Only `meta/` is downloaded | `snapshot_download` with allow-patterns; a dataset's videos and frame data are never fetched by the level-0 inspection | 0 |
| Unsupported versions refused | `codebase_version` outside `v3.0` raises `UnsupportedFormatError` before anything else is read | 0 |
| Consistency, not trust | Declared totals are checked against the episode table; a mismatch is a failed check, not an accepted claim | 0 |
| Terminal output is inert | `to_text` replaces control characters in every string that comes from the dataset and caps column widths, so a task text or a dataset name cannot drive the terminal | 0 |
| Metadata size cap | A `meta/` directory or episode table beyond a configurable size is refused with an error naming the size | 1 |
| Selective, capped downloads | The numeric audit fetches the `data/` chunks an episode needs and caps episodes per audit and bytes per file | 1 |
| Malformed parquet | A truncated or malformed file becomes a `Check` that failed with the parse error in `detail`, and the audit continues on the rest | 1 |
| Video caps | Episodes decoded per audit and frames per episode are bounded; decoding errors are per-episode failures | 2 |

## 2. Hostile inputs the library expects

| Input | Effect today | Effect after the bound |
|---|---|---|
| A dataset with a million-row episode table | Downloaded and parsed | Refused by size before parsing |
| A task text that reads like instructions | Quoted in the report as data; the library has no model to instruct | Unchanged; a judge or an assistant downstream treats it as data too, but that is their document |
| A task text carrying terminal escape sequences | Replaced by `?` in the terminal rendering; quoted verbatim in Markdown and JSON, which are written to files and tools, not to a terminal | Unchanged |
| Declared `total_frames` that does not match the data | `frame_total_matches` fails | Unchanged |
| A truncated parquet file | An exception surfaces | A named failed check, audit continues |
| A local path with `meta/` but no `info.json` | `FileNotFoundError` | An `UnsupportedFormatError` saying what is missing |

## 3. What is measured

- **Latency** per stage: download, parse, inspect, render; recorded in `JOURNAL.md` and the
  README table when it changes.
- **Dependency footprint**: packages in the lock file, none of them a cloud or agent SDK.
- **Determinism**: the test suite asserts identical reports on identical inputs.
- **Nothing about cost**: the library has none beyond bandwidth. The cost of a model that a
  caller supplies for the visual audit is the caller's to measure; the library gives it the
  frame counts to do so.
