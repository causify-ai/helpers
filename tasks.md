### [ ] Sync Raindrop bookmarks to Obsidian with a short summary

* Affected repo: helpers

* Problem
- Automatically keep the Obsidian vault
  (`/Users/saggese/Library/Mobile Documents/iCloud~md~obsidian/Documents/GP/`)
  updated with a short summary (article + HN comments) for each Hacker News
  bookmark saved in Raindrop.
- Design constraint: no new scripts. The 2 existing scripts
  (`update_gsheet_links_from_raindrop.py`, to be renamed
  `update_bookmarks_from_raindrop.py`; `process_bookmarks.py`) each gain a
  second, independently-selectable mode instead:
  - `update_bookmarks_from_raindrop.py`: sync new Raindrop bookmarks into a
    live **Google Sheet** (existing) or directly into a **local CSV** (new)
  - `process_bookmarks.py`: copy merged summaries to **Google Drive**
    (existing default) or to **Obsidian** (new); either destination can be run
    at any time, independently of the other, against the same CSV
  - Both modes/destinations of each script share their core logic; only the
    small input/output-path logic differs
- Source of truth for bookmarks is the local CSV
  `/Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv`
  (1779 rows today; only 45 marked `Done`); this data file keeps its current
  name even after the script rename (it's user data, not code). Scripts live
  in `helpers_root/dev_scripts_helpers/download/`. See that dir's
  `README.md`, section "Modular Raindrop Sync and Multi-Destination Bookmark
  Workflow", for the full target design this breaks down.

* Solution

- [x] PR1: Rename `update_gsheet_links_from_raindrop.py` ->
  `update_bookmarks_from_raindrop.py`
  - Once the script can sync into a local CSV as well as a Google Sheet
    (PR2), "gsheet_links" in the name is no longer accurate; do this rename
    first so PR2 lands on the final name
  - Use the `git.move` skill (renames a file and updates references) rather
    than a plain `mv`, to catch call sites automatically
  - Update in the renamed file itself:
    - The module docstring's `Import as: import ... as <alias>` line and the
      alias used at call sites
    - The `GSHEET_CSV_FILE` / `RAINDROP_CSV_FILE` / `COMBINED_CSV_FILE`
      temp-file-prefix string literal (currently
      `"update_gsheet_links_from_raindrop"`, passed to
      `dshdbout.get_tmp_file_path()` in 6 places) -> `"update_bookmarks_from_raindrop"`,
      so generated tmp file names match the new script name (see
      `.claude/skills/coding.rules.md` under "Temporary Files")
    - The gsheet tab-name prefix built in `_upload_to_gsheet()`
      (`"update_gsheet_links_from_raindrop." + <date>"`) -> the new prefix
    - All usage examples in the module docstring
  - Rename `test/test_update_gsheet_links_from_raindrop.py` ->
    `test/test_update_bookmarks_from_raindrop.py`; update its imports, alias,
    and docstrings referencing the old module name
  - Update `README.md`: the "Description of Files" table row and the
    `### update_gsheet_links_from_raindrop.py` executable section header/body
  - Do **not** rename the data file
    `update_gsheet_links_from_raindrop.combined_data.csv` in
    `notes1/bookmarks/` -- it is user data and keeps its existing name

  ## Result
  - Done:
    - `git mv` for the script and its test file (history preserved)
    - Updated, in one pass, every occurrence of the old module name/alias
      (`dsglfr` -> `dsbfr`) in both files: docstring `Import as`/usage
      examples, the 8 temp-file-prefix string literals, the gsheet
      tab-name prefix
    - `README.md`: "Description of Files" table row and the
      `### update_bookmarks_from_raindrop.py` section (header + all 4
      example commands)
    - Verified: module imports, all 17 renamed unit tests pass, pyflakes
      clean, `git status` shows clean `R`enames (not delete+add)
  - Not done (intentionally out of PR1 scope, per task spec):
    - 3 other old-name mentions in `README.md` (the "Full Link-Processing
      Workflow" step 1 command, the "CSV-Based Bookmark Processing
      Workflow" intro, and the historical "is renamed to" sentence in the
      already-written "planned" section) -- PR1's README scope was
      explicitly limited to the table row + dedicated section; these are
      folded in by PR7
    - Data file `update_gsheet_links_from_raindrop.combined_data.csv` name
      -- left untouched by design (user data, not code)

- [x] PR2: Modularize `update_bookmarks_from_raindrop.py`'s sync target
  - Add `--target {gsheet,local_csv}` (default: `gsheet`, preserves today's
    behavior and CLI unchanged for that mode)
  - Refactor `_get_latest_timestamp_from_file()`, `_download_raindrop_data()`,
    and `_combine_raindrop_with_gsheet_links()` to take explicit base-CSV-path
    / output-CSV-path parameters instead of the hardcoded gsheet tmp-file
    paths, so both targets share the same core Raindrop-fetch/field-mapping
    logic
  - `--target local_csv` requires `--local_csv <path>`; only
    `download_raindrop_data` and `combine_data` are valid actions for it
    (reject `download_gsheet_links` / `upload_gsheet_links` with a clear
    error); the latest-`Timestamp` cutoff is read directly from
    `--local_csv`, and `combine_data` prepends newly-fetched rows into that
    same file in place, leaving every existing row (`Done` included)
    untouched
  - `--target gsheet` behavior and output paths are unchanged
  - Add/update unit tests per `.claude/skills/testing.rules.md` for both
    targets, including the in-place-merge behavior for `local_csv`

  ## Result
  - Done:
    - `--target {gsheet,local_csv}` (default `gsheet`) and `--local_csv
      <path>` CLI args
    - `_get_latest_timestamp_from_file()`, `_download_raindrop_data()`,
      `_combine_raindrop_with_gsheet_links()` refactored to take explicit
      `base_csv`/`output_csv` params instead of hardcoded gsheet tmp paths;
      `raindrop_csv` stays an internal tmp file shared by both targets
    - `local_csv` target: only `download_raindrop_data`/`combine_data` are
      valid (enforced by passing a separate `_LOCAL_CSV_ACTIONS` list to
      `hselacti.select_actions()`, which rejects other actions with a clear
      `AssertionError`); `combine_data` prepends into `--local_csv` in
      place (`output_csv == base_csv`), verified to leave existing rows
      (`Done` included) untouched, both at the unit level and via a real
      CLI smoke test
    - `_get_action_output_file()` made target-aware so `combine_data`'s
      incremental-skip check is disabled for `local_csv` (it would
      otherwise always skip, since `--local_csv` already exists)
    - `gsheet` target: verified byte-for-byte behavior-preserving (all
      pre-existing tests pass unchanged; new `--target`/`--local_csv` args
      default to today's behavior)
    - Tests: 7 new/updated cases (in-place-merge, target-aware
      `_get_action_output_file`) + 3 new end-to-end CLI tests (missing
      `--local_csv`, rejected gsheet-only action, full local_csv round
      trip); 82/82 tests pass in the dir, pyflakes clean
  - Not done: none (full PR2 scope covered)

- [x] PR3: Skip non-HN rows in `process_bookmarks.py`
  - A row whose `Hn_url` is not a real HN item URL
    (`news.ycombinator.com/item?id=...`, e.g. a plain article link
    `Raindrop.io` put in that column) can never be processed by this script.
    Set `Done = "skipped"` on it immediately (no download), so it stops
    occupying `--limit` slots on every future run. Handling plain-article
    bookmarks is explicitly out of scope (396 of the current 1734 unprocessed
    rows are like this)
  - Add unit tests for the skip case

  ## Result
  - Done:
    - The invalid-`Hn_url` check already existed in `_process_row()` but
      only logged a warning and returned without marking the row, so it
      re-occupied a `--limit` slot every run; fixed to set
      `row["Done"] = "skipped"` (outside `--dry_run`)
    - `_process_row()`'s return type changed from `Tuple[bool, ...]` to a
      status string (`"processed"`/`"skipped"`/`"dry_run"`/`"failed"`),
      needed to decouple "persist the CSV" from "count as processed" in
      `_main()`'s loop -- a skipped row must persist immediately even when
      it's the only row selected this run
    - `--dry_run` invariant preserved: the skip is detected and reported in
      dry-run mode too (useful for PR4's future dry-run reporting) but
      `Done` is left unmutated and the CSV is never written
    - `_main()`'s final log line now reports `skipped` count alongside
      `processed`
    - New `test_process_bookmarks.py` (this script had no test file yet):
      4 unit tests on `_process_row()` (non-HN URL, empty URL, valid URL
      not skipped, dry_run doesn't mutate) + 2 end-to-end tests (skip
      persists to disk after one run; a previously-skipped row is not
      re-selected on a later run)
    - Verified via real CLI run (not just pytest): `--dry_run` leaves the
      CSV untouched; a real run with `--limit 1` marks only the skip
      candidate `Done=skipped` and leaves the real HN row (not yet reached)
      untouched
    - 88/88 tests pass in the dir, pyflakes clean
  - Not done: handling plain-article bookmarks (explicitly out of scope
    per the task)

- [x] PR4: Modularize `process_bookmarks.py`'s destination
  - Replace `--gdrive_dir` / `--no_save_to_google_drive` with:
    - `--dest_type {gdrive,obsidian,none}` (default: `gdrive`, preserves
      today's default path/behavior), each mapping to a built-in default
      path (`_DEFAULT_GDRIVE_DIR`, new `_DEFAULT_OBSIDIAN_DIR` =
      `/Users/saggese/Library/Mobile Documents/iCloud~md~obsidian/Documents/GP/`)
    - `--dest_dir <path>` (optional): overrides the built-in path for the
      selected `--dest_type`
  - Decouple "row processed" (`Done=yes`: download+summarize+merge done,
    merged file cached under `--output_dir`) from "row copied to a given
    destination". Add a reconciliation pass that, for the currently selected
    destination, copies the cached merged file for every `Done=yes` row
    whose file is missing there -- no re-download, no re-summarize, no LLM
    cost
  - The reconciliation pass runs over **all** `Done=yes` rows every
    invocation, not bounded by `--limit` (which only bounds how many new,
    not-yet-`Done` rows get downloaded this run); `--limit 0` runs
    reconciliation only
  - `--dry_run` reports, without downloading, writing, or mutating the CSV:
    rows to be newly processed this run, rows to be marked `skipped`, and
    rows to be copied/repaired into the selected destination
  - Add/update unit tests for: `--dest_type` selection, `--dest_dir`
    override, and the reconciliation/repair pass (including the
    `Done=yes`-but-missing-from-destination case and `--limit 0`)

  ## Result
  - Done:
    - `--dest_type {gdrive,obsidian,none}` (default `gdrive`) + `--dest_dir`
      override replace `--gdrive_dir`/`--no_save_to_google_drive`;
      `_resolve_dest_dir()` maps type -> built-in default path (new
      `_DEFAULT_OBSIDIAN_DIR`), or `None` for `none`
    - `_process_row()` made destination-agnostic: it now only
      downloads/summarizes/merges/caches under `--output_dir` and sets
      `Done`; the gdrive-copy call was removed entirely
    - New `_reconcile_destination()` + `_find_cached_merged_summary()`:
      for the selected destination, copies every `Done=yes` row's cached
      merged file that's missing there -- no re-download, no
      re-summarize. Runs over **all** `Done=yes` rows every invocation
      (not `--limit`-bounded); `_main()` calls it unconditionally after
      the row-processing loop, so `--limit 0` naturally runs
      reconciliation only
    - `_find_cached_merged_summary()` had to explicitly exclude the 2
      per-item summary files (`*.2.article_url.summary.md`/
      `*.4.hn_url.summary.md`), which also end in `.summary.md` and would
      otherwise be misidentified as the merged file by a naive glob
    - `--dry_run` extended to cover the full contract: reports rows to be
      newly processed (`num_would_process`, tracked via the existing
      per-row `status`) and rows to be copied/repaired
      (`_reconcile_destination(..., dry_run=True)`), without creating any
      dir, writing the CSV, or copying any file -- verified via unit
      tests and 2 real CLI runs (dry_run left the CSV, output dir, and
      obsidian dir fully untouched; the follow-up real run then performed
      exactly the reported reconciliation)
    - Tests: 13 new unit tests (`_resolve_dest_dir` x4,
      `_find_cached_merged_summary` x2, `_reconcile_destination` x5) + 2
      new end-to-end tests (`--limit 0` reconciliation-only backfill,
      `--dest_type none` requires no `--dest_dir`); 2 existing end-to-end
      tests updated for the `--gdrive_dir` -> `--dest_dir` rename
    - Verified real Google Drive and Obsidian dirs untouched by the test
      suite (checked file mtimes before/after); 100/100 tests pass in the
      dir, pyflakes clean
  - Not done: none (full PR4 scope covered)
  - Noted, not touched (pre-existing, unrelated to this task):
    `dev_scripts_helpers/download/test/test_bookmark_utils.py` has
    uncommitted local changes that predate this session (last touched by
    commit `c665cc9d`, not by any PR1-PR4 work here) -- flagged to the
    user rather than folded into this diff

- [ ] PR5: Add a manual `Score` placeholder to the merged-summary template
  - In `_build_info_section()`, add an empty `Score: ` line right after
    `Article_cluster` in the `# Info` section of every newly generated
    `<base>.summary.md` file
  - This is a placeholder for the user to fill in by hand while reading in
    Obsidian (matches the existing manual convention already present in
    13/40 current notes, e.g. `Score: 2/5`); it is not LLM-computed and must
    not be populated automatically

- [ ] PR6: Increase bullet/comment counts in the summarization prompts
  - `download_utils.ARTICLE_SUMMARY_PROMPT`: raise "7-10 bullet points and
    fewer than about 250 words" to "12-15 bullet points and fewer than about
    400 words"; fix the stale comment above it that still says "5 bullet
    points"
  - `download_hn_article_to_md._HN_COMMENTS_PROMPT`: raise "summarize the
    5-10 most interesting comments" to "summarize the 10-15 most interesting
    comments"

- [ ] PR7: Update `README.md`
  - Document `update_bookmarks_from_raindrop.py`'s new `--target`
    modes (`gsheet`, `local_csv`) in its own "What It Does"/"Examples"
    sections
  - Document `process_bookmarks.py`'s new `--dest_type` / `--dest_dir`, the
    skip-non-HN logic, and the reconciliation/repair pass semantics
    (including `--limit 0`) in its own "What It Does"/"Examples" sections
  - Update the bullet/comment count numbers in the prompt descriptions
  - Address the existing `TODO(ai_gp)` in the README ("CSV-Based Bookmark
    Processing Workflow" section is too detailed): trim it down and move the
    step-by-step detail into `process_bookmarks.py`'s own docstring/comments
  - Fold the "Modular Raindrop Sync and Multi-Destination Bookmark Workflow"
    section (currently marked planned) into the regular workflow list once
    implemented, with one example per target/destination combination
