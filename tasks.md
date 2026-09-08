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

- [ ] PR1: Rename `update_gsheet_links_from_raindrop.py` ->
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

- [ ] PR2: Modularize `update_bookmarks_from_raindrop.py`'s sync target
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

- [ ] PR3: Skip non-HN rows in `process_bookmarks.py`
  - A row whose `Hn_url` is not a real HN item URL
    (`news.ycombinator.com/item?id=...`, e.g. a plain article link
    `Raindrop.io` put in that column) can never be processed by this script.
    Set `Done = "skipped"` on it immediately (no download), so it stops
    occupying `--limit` slots on every future run. Handling plain-article
    bookmarks is explicitly out of scope (396 of the current 1734 unprocessed
    rows are like this)
  - Add unit tests for the skip case

- [ ] PR4: Modularize `process_bookmarks.py`'s destination
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
