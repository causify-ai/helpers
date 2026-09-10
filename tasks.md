### [ ] Unify gsheet / local-CSV bookmark pre-processing flow

* Affected repo: helpers

* Solution

- Rename `process_gsheet_links.py` -> `pre_process_bookmarks.py`
  - Update its module docstring, `Import as:` line, the README's file table and
    "Description of Executables" section, all workflow sections, and its test
    file `test/test_process_gsheet_links.py` -> `test/test_pre_process_bookmarks.py`
  - Update every other in-repo reference to the old name (e.g., `grep -r
    process_gsheet_links`)

- `pre_process_bookmarks.py` should be applicable to both gsheet and local_csv
  in the same way
  - Add a `--target {gsheet,local_csv}` argument (required, no default),
    mirroring the existing `--target` on `update_bookmarks_from_raindrop.py`
    (do NOT call it `--dest_type`: that name is already used by
    `process_bookmarks.py` for an unrelated concept -- output destination
    `gdrive`/`obsidian`/`none` -- and reusing it here would make the same flag
    name mean two different things in two scripts that run back-to-back in
    the same pipeline)
  - `--target gsheet`: unchanged behavior. `--url` is required, still falling
    back to the `$LINKS_GSHEET` env var if not passed (keep
    `resolve_gsheet_url()`'s existing fallback; do not remove it).
    `download_link_gsheet` and `upload_link_gsheet` stay in the action list
  - `--target local_csv` (requires `--local_csv <path>`): `download_link_gsheet`
    and `upload_link_gsheet` drop out of the action list (no gsheet
    download/upload). `update_article_url`/`update_article_tag`/
    `update_article_cluster` run against that file: the given `--local_csv`
    is used directly in place of the gsheet-downloaded CSV as input to the
    first stage, and the final clustered result is written back into that
    same `--local_csv` file in place (overwriting it), instead of uploading
    to a gsheet tab
  - No default `--target`: it must always be passed explicitly, for both
    values

- Extend `download_link_articles.py`'s `--input` to accept either:
  - a single URL (existing behavior, unchanged: builds one synthetic row,
    `--row_idx` ignored), or
  - a path to a local bookmarks CSV (new: batch mode, loading all rows the
    same way the `--url`/gsheet path does today, including honoring
    `--row_idx` to select a subset -- lift today's "ignored with --input"
    restriction for this case)
  - Detect which case applies by checking whether the value is an existing
    local file path vs. a URL
  - This makes `--input` (gsheet-free) the primary/default way to run this
    script, in line with moving away from gsheet-centric usage; `--url`
    remains supported but is no longer the primary documented path

- In the README's "CSV-Based Bookmark Processing Workflow" section, document
  that the local-CSV pipeline goes through the same enrichment stages as the
  gsheet pipeline, before `process_bookmarks.py` runs:
  1. `pre_process_bookmarks.py --target local_csv --local_csv <path>
     --all_actions` (extract article URLs, tag, cluster -- written back into
     `<path>` in place)
  2. `download_link_articles.py --input <path> --all_actions` (download and
     summarize article/HN content)
  3. `process_bookmarks.py -i <path> ...` (merge summaries, mark `Done`,
     reconcile destination)

- Update `dev_scripts_helpers/download/README.md`:
  - Rewrite the `process_gsheet_links.py` section as `pre_process_bookmarks.py`,
    documenting `--target {gsheet,local_csv}` and `--local_csv`
  - Update the `download_link_articles.py` section and the "Full
    Link-Processing Workflow" section for the new `--target`/`--input`
    behavior above
  - Remove references to the past/previous interface and to how the current
    behavior came to be (no mention of PRs or prior iterations) -- the README
    should only describe how things work right now
