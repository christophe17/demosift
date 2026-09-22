# The LeRobot dataset format, as observed

This is the learning guide behind `demosift.format` and `demosift.inspection`. Everything
here was read from real datasets on the Hugging Face Hub on 2026-09-21
(`lerobot/svla_so101_pickplace`, `lerobot/svla_so100_pickplace`,
`lerobot/aloha_sim_insertion_human`, all `codebase_version: v3.0`), not from memory. The
metadata of the first is recorded under `tests/fixtures/svla_so101_pickplace/meta/`.

## 1. Vocabulary

- **Dataset**: a set of recorded *episodes* of a robot doing a task, plus the schema that
  says what was recorded.
- **Episode**: one continuous recording, from the start of an attempt to its end — for
  example one pick-and-place, about ten seconds.
- **Frame**: one time step inside an episode. At 30 fps an episode of 303 frames lasts
  10.1 seconds. Every frame carries the robot's *state* (where its joints are), the *action*
  (where they were commanded to go), a timestamp, and one image per camera.
- **Feature**: one named column of the recording, with a data type and a shape.
  `observation.state` and `action` are vectors of joint values; `observation.images.<camera>`
  are video streams.
- **Task**: the natural-language instruction the episode fulfils ("pink lego brick into the
  transparent box"). A dataset can hold several tasks; each episode lists the ones it covers.

## 2. Layout on disk

```
meta/
  info.json                              dataset-level description and the feature schema
  stats.json                             per-feature min/max/mean/std/count over the whole dataset
  tasks.parquet                          task text (the index) → task_index
  episodes/chunk-000/file-000.parquet    one row per episode (see §4)
data/
  chunk-000/file-000.parquet             one row per frame, several episodes per file (see §5)
videos/
  observation.images.up/chunk-000/file-000.mp4     several episodes concatenated per file
  observation.images.side/chunk-000/file-000.mp4
```

Files are grouped in *chunks* of `chunks_size` (1000) files; small datasets have a single
chunk and a single file per directory. The path templates are declared in `info.json`
(`data_path`, `video_path`), which is why the reader never hard-codes them.

## 3. `meta/info.json`

Observed keys and their values on `lerobot/svla_so101_pickplace`:

| Key | Value | Meaning |
|---|---|---|
| `codebase_version` | `"v3.0"` | The format version; the reader refuses anything else |
| `robot_type` | `"so100_follower"` | Free text set by the recording software |
| `total_episodes` / `total_frames` / `total_tasks` | 50 / 11939 / 1 | Declared totals, checked against the episode table |
| `fps` | 30 | Frames per second of every stream |
| `chunks_size` | 1000 | Files per chunk directory |
| `data_path`, `video_path` | templates | Where frame data and videos live |
| `data_files_size_in_mb`, `video_files_size_in_mb` | 100, 500 | Target file sizes when writing; `aloha_sim_insertion_human` has a single `files_size_in_mb` instead, so these are optional |
| `splits` | `{"train": "0:50"}` | Episode ranges per split |
| `features` | map | The schema, below |

Each feature has `dtype`, `shape`, optional `names`, and for videos an `info` block:

```json
"action": {"dtype": "float32", "shape": [6],
           "names": ["shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos",
                     "wrist_flex.pos", "wrist_roll.pos", "gripper.pos"]}
"observation.images.up": {"dtype": "video", "shape": [480, 640, 3],
           "names": ["height", "width", "channels"],
           "info": {"video.height": 480, "video.width": 640, "video.codec": "av1",
                    "video.pix_fmt": "yuv420p", "video.fps": 30, "video.channels": 3,
                    "has_audio": false}}
```

`names` is not always a list of strings — some datasets nest it (`{"motors": [...]}`) and the
ALOHA dataset omits it for its 14-dimensional state — so `Feature.flat_names` returns the
names only when they are a plain list.

## 4. The episode table (`meta/episodes/…parquet`)

One row per episode, 62 columns on the SO-101 dataset. The columns that matter:

| Column | Example | Used for |
|---|---|---|
| `episode_index` | 0 | Identity; must run 0..N-1 |
| `length` | 303 | Frames in the episode; sums to `total_frames` |
| `tasks` | `["pink lego brick into the transparent box"]` | Every episode must carry at least one task known to `tasks.parquet` |
| `data/chunk_index`, `data/file_index` | 0, 0 | Which data file holds the episode's frames |
| `dataset_from_index`, `dataset_to_index` | 0, 303 | The episode's frame range in the global index |
| `videos/<camera>/chunk_index`, `.../file_index` | 0, 0 | Which video file holds the episode |
| `videos/<camera>/from_timestamp`, `.../to_timestamp` | 0.0, 10.1 | Where the episode sits inside that video file, in seconds |
| `stats/<feature>/{min,max,mean,std,count}` | arrays | Per-episode statistics of every feature |

The per-episode `stats/…` columns are what milestone 1 starts from for action-range checks
without downloading the frame data.

## 5. The frame table (`data/…parquet`)

One row per frame; 11939 rows and 7 columns on the SO-101 dataset:
`action` (float32[6]), `observation.state` (float32[6]), `timestamp` (float32, seconds from
the episode start: 0.0, 0.0333, 0.0667…), `frame_index` (position in the episode),
`episode_index`, `index` (global position), `task_index`. Images are not in this table; they
are decoded from the video files using the per-episode `from_timestamp`.

Milestone 1 reads this table for timestamp regularity (gaps or duplicates against `1/fps`),
frozen frames (state and action unchanged over many steps), action and state ranges against
the declared limits, and jerk.

## 6. What each level-0 check verifies, and what a failure means

| Check | Verifies | A failure usually means |
|---|---|---|
| `frame_total_matches` | Σ `length` = `total_frames` | An interrupted upload or a hand-edited `info.json`; training loaders may index out of range |
| `episode_count_matches` | rows = `total_episodes` | Same causes; episodes silently missing |
| `episode_indices_contiguous` | indices are 0..N-1 | Episodes deleted without re-indexing; splits and loaders assume contiguity |
| `fps_positive` | `fps` > 0 | A corrupted schema; every duration becomes meaningless |
| `no_empty_episode` | every `length` > 0 | A recording stopped before its first frame |
| `every_episode_has_known_task` | task texts exist in `tasks.parquet` | Task annotations lost or mistyped; language-conditioned policies train on garbage labels |
| `video_span_matches_length[camera]` | (`to` − `from`) × fps ≈ `length` within one frame | Video and frame data out of sync for that camera — the most damaging fault for vision policies, and invisible without this check |

Length outliers are reported as hints, not failures: a very short episode may be a failed
attempt that should be removed, or a legitimately quick success. Only a human, or the visual
audit of milestone 2, can tell.

## 7. Why robust statistics for the outliers

The mean and the standard deviation are pulled by the very outliers one is looking for: one
5000-frame episode among fifty 300-frame ones inflates the standard deviation enough to hide
itself. The median and the median absolute deviation (MAD) are not moved by a few extreme
values. The score used is `(length − median) / (1.4826 × MAD)`, where 1.4826 rescales the MAD
to a standard deviation for normally distributed data, so a threshold of 3.5 reads like
"3.5 sigmas". When the MAD is zero (all episodes the same length, as in the ALOHA simulation
dataset) no outlier is reported rather than dividing by zero.
