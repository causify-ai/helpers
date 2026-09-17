# Download Tools
- Scripts to download, convert, and summarize content (web pages, academic papers,
  Hacker News submissions, podcast transcripts) to Markdown, plus a pipeline for
  managing a Google Sheets-based link database

## Structure of the Dir
- `test/`
  - Unit tests for the download and gsheet-processing scripts

## Description of Files
| File                                   | Description                                                                  | Cluster             |
| -------------------------------------- | ---------------------------------------------------------------------------- | ------------------- |
| `bookmark_utils.py`                    | Shared helpers for downloading/uploading Google Sheets data and CSV files    | Shared Utilities    |
| `download_academic_paper_to_md.py`     | Download an academic paper (arXiv/DOI/PDF), convert to Markdown, summarize   | Content Downloaders |
| `download_hn_article_to_md.py`         | Download a Hacker News submission (comments and article), convert, summarize | Content Downloaders |
| `download_html_to_md.py`               | Download a generic web page and convert it to Markdown, summarize            | Content Downloaders |
| `download_link_articles.py`            | Download/summarize article content and HN comments for rows from a Gsheet or a local CSV | Gsheet Pipelines    |
| `download_to_md.py`                    | Detect input type and dispatch to the matching `download_*_to_md.py` script  | Content Downloaders |
| `download_utils.py`                    | Shared helpers for fetching article titles and summarizing text via an LLM   | Shared Utilities    |
| `podcast_dl.py`                        | Download and format a podcast transcript from various sources                | Podcast Tools       |
| `podcast_dl_example.sh`                | Example invocations of `podcast_dl.py` for each supported source type        | Podcast Tools       |
| `pre_process_bookmarks.py`             | Pipeline to extract HN article URLs and classify articles by topic/cluster, for a Gsheet or a local CSV | Gsheet Pipelines    |
| `process_bookmarks.py`                 | Download, summarize, and archive HN bookmarks from a CSV to a destination    | Bookmark Pipeline   |
| `process_one_off_gsheet_links.py`      | One-off pipeline to rename topic tags in the Gsheet (data migration)         | Gsheet Pipelines    |
| `update_bookmarks_from_raindrop.py`    | Sync new bookmarks from `Raindrop.io` into the Gsheet or a local CSV         | Gsheet Pipelines    |

## Link Gsheet Schema
- E.g.,
  ```bash
  > export LINKS_GSHEET="<your-google-sheets-url>"

  > export LINKS_GSHEET=https://docs.google.com/spreadsheets/d/1i6Z7v2TzPdftR9BQ5Ia6jrrNWvVy-pUCxZAt4A59l8M/edit?gid=2008094999#gid=2008094999
  ```

- The master Google Sheets document contains the following columns:
  - `Title`: Article title
    - _Example_: "Rust is not a good C replacement"
  - `Url`: Source URL
    - Can be: direct article URL, paper link, or Hacker News submission URL
    - _Example_:
      https://drewdevault.com/2019/03/25/Rust-is-not-a-good-C-replacement.html,
      https://news.ycombinator.com/item?id=40212490
  - `Timestamp`: Date and time when added
    - Format: YYYY-MM-DD HH:MM:SS
    - _Example_: 2024-04-30 22:23:54
  - `Article_url`: URL of the actual article (extracted from HN submission if
    applicable)
    - _Example_:
      https://medium.com/airbnb-engineering/chronon-airbnbs-ml-feature-platform-is-now-open-source-d9c4dba859e8
  - `Article_title`: Title of the actual article (extracted from HN submission if
    applicable)
    - Typically same as `Title` for HN submissions
  - `Article_tag`: Categorized topic/tag for the article
    - _Example_: "Automated Theorem Proving", "AI Infrastructure", "Python Ecosystem"
  - `Article_cluster`: High-level cluster grouping topics
    - _Example_: "AI", "Data/Infra", "Dev tools", "Finance", "Math", "Business",
      "CyberSec", "SwEng"
  - `Interesting`: Relevance rating (1 to 5)
  - `Notes`: Additional notes and comments

## Description of Executables

### `download_to_md.py`

#### What It Does
- Detects the type of `--input` and dispatches to the matching converter:
  - **hn**: HN submission URL (`news.ycombinator.com/item?id=...`) ->
    `download_hn_article_to_md.py`
  - **academic_paper**: arXiv URL, DOI (URL or bare), or generic `.pdf` URL ->
    `download_academic_paper_to_md.py`
  - **html**: anything else (generic web page) -> `download_html_to_md.py`
- `--output` is only forwarded to the dispatched script when specified; otherwise the
  dispatched script derives its own output name

#### Examples
- Download a generic web page (auto-detected as html):
  ```bash
  > download_to_md.py --input "https://example.com/article"
  ```

- Download an arXiv paper (auto-detected as academic_paper):
  ```bash
  > download_to_md.py --input "https://arxiv.org/abs/1706.03762"
  ```

- Download an HN submission with an explicit output base name:
  ```bash
  > download_to_md.py \
      --input "https://news.ycombinator.com/item?id=40212490" \
      --output ./links/my_article
  ```

### `download_academic_paper_to_md.py`

#### What It Does
- Downloads academic papers from arXiv, DOI, or a generic PDF URL
- Saves the paper with a standardized base name, e.g.,
  `2016.Ribeiro_et_al.Why_Should_I_Trust_You...`, shared across the `.pdf`, `.md`,
  and `.summary.md` outputs
- Converts the PDF to Markdown and summarizes it

#### Examples
- Download from an arXiv URL (runs download, convert, summarize by default):
  ```bash
  > download_academic_paper_to_md.py --input "https://arxiv.org/abs/1706.03762"
  ```

- Download from a DOI URL or bare DOI:
  ```bash
  > download_academic_paper_to_md.py --input "10.1038/nature12373"
  ```

- Save under a custom directory when `--output` is not passed:
  ```bash
  > PAPERS_DIR=./my_papers download_academic_paper_to_md.py \
      --input "https://arxiv.org/abs/1706.03762"
  ```

- Only download and convert, skip summarization:
  ```bash
  > download_academic_paper_to_md.py \
      --input "10.1038/nature12373" \
      --skip_action summarize
  ```

- Show what would be done without downloading, converting, or summarizing:
  ```bash
  > download_academic_paper_to_md.py --input "10.1038/nature12373" --dry_run
  ```

### `download_hn_article_to_md.py`

#### What It Does
- Downloads a Hacker News link: both the comments and the article it points to
- Converts and summarizes both
- Output filenames share a base name (the sanitized submission title, unless
  `--output` is given)

#### Examples
- Download, convert, and summarize an HN submission:
  ```bash
  > download_hn_article_to_md.py \
      --input "https://news.ycombinator.com/item?id=40212490"
  ```

- Only download the article and comments, skip summarization:
  ```bash
  > download_hn_article_to_md.py \
      --input "https://news.ycombinator.com/item?id=40212490" \
      --action download_hn_url \
      --action download_article_url
  ```

- Overwrite existing output files:
  ```bash
  > download_hn_article_to_md.py \
      --input "https://news.ycombinator.com/item?id=40212490" \
      --no_incremental
  ```

### `download_html_to_md.py`

#### What It Does
- Downloads an HTML page (or reads a local HTML file) and converts it to Markdown
  using one of several converters: `auto` (BeautifulSoup, falling back to
  readability), `pandoc`, `bs`, or `readability`
- Summarizes the converted content

#### Examples
- Download a page and convert with the default `auto` converter:
  ```bash
  > download_html_to_md.py --input https://example.com --output output.md
  ```

- Convert with a specific converter:
  ```bash
  > download_html_to_md.py \
      --input https://example.com \
      --output output.md \
      --converter pandoc
  ```

- Skip the summarization step:
  ```bash
  > download_html_to_md.py \
      --input https://example.com \
      --output output.md \
      --skip_action summarize
  ```

### `podcast_dl.py`

#### What It Does
- Downloads and formats a podcast transcript from `lexfridman`, `dwarkesh`,
  `podcasttranscript_ai`, or `podscripts_co`
- Default behavior runs `download`, `format`, and `lint` in sequence
- Each step writes a numbered file to `<OUTPUT>.md.tmp/`, and the final result is
  copied to `<OUTPUT>.md`

#### Examples
- Default: download, format, and lint a Lex Fridman episode:
  ```bash
  > podcast_dl.py \
      --type lexfridman \
      --title lars-brownworth \
      --output ./podcasts/lars-brownworth.md
  ```

- Download only:
  ```bash
  > podcast_dl.py \
      -a download \
      --type lexfridman \
      --title lars-brownworth \
      --output ./podcasts/lars-brownworth.md
  ```

- Download and format (skip linting):
  ```bash
  > podcast_dl.py \
      -a download -a format \
      --type dwarkesh \
      --title andrej-karpathy \
      --output ./podcasts/andrej-karpathy.md
  ```

- Run the example script covering all source types:
  ```bash
  > ./podcast_dl_example.sh
  ```

### `update_bookmarks_from_raindrop.py`

#### What It Does
- Synchronizes new bookmarks from `Raindrop.io` into either a live Google
  Sheet or a local CSV file, selected via the required `--target
  {gsheet,local_csv}` (no default)
- Requires the `RAINDROP_API_TOKEN` environment variable
- **`--target gsheet`**: a four-action pipeline
  - **download_gsheet_links**: Downloads current data from Google Sheets to CSV
  - **download_raindrop_data**: Fetches new bookmarks from the `Raindrop.io` API
    (only items created after the latest timestamp in the gsheet)
  - **combine_data**: Transforms and combines `Raindrop.io` data into the gsheet
    schema, writing a new combined tmp CSV
  - **upload_gsheet_links**: Uploads combined data back to Google Sheets in a new
    timestamped tab
- **`--target local_csv`** (requires `--local_csv <path>`): only
  `download_raindrop_data` and `combine_data` apply (no gsheet
  download/upload: `download_gsheet_links`/`upload_gsheet_links`); the
  latest-`Timestamp` cutoff is read directly from `--local_csv`, and `combine_data`
  prepends newly-fetched rows into that same file in place, leaving every existing
  row (`Done` included) untouched

#### Examples
- Sync all new bookmarks from `Raindrop.io` to Google Sheets:
  ```bash
  > update_bookmarks_from_raindrop.py \
      --target gsheet \
      --url "$LINKS_GSHEET" \
      --all_actions
  ```

- Just download from Google Sheets:
  ```bash
  > update_bookmarks_from_raindrop.py \
      --target gsheet \
      --url "$LINKS_GSHEET" \
      --clear_actions \
      --action download_gsheet_links
  ```

- Just fetch from `Raindrop.io` (requires `RAINDROP_API_TOKEN`):
  ```bash
  > update_bookmarks_from_raindrop.py \
      --target gsheet \
      --url "$LINKS_GSHEET" \
      --clear_actions \
      --action download_raindrop_data
  ```

- Combine data without uploading:
  ```bash
  > update_bookmarks_from_raindrop.py \
      --target gsheet \
      --url "$LINKS_GSHEET" \
      --clear_actions \
      --action download_gsheet_links \
      --action download_raindrop_data \
      --action combine_data
  ```

- Sync new bookmarks directly into a local CSV instead of a Google Sheet:
  ```bash
  > update_bookmarks_from_raindrop.py \
      --target local_csv \
      --local_csv /Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv \
      --action download_raindrop_data --action combine_data
  ```

### `pre_process_bookmarks.py`

#### What It Does
- Pipeline for enriching Hacker News articles, applied the same way to a
  Google Sheets document or a local CSV, selected via the required `--target
  {gsheet,local_csv}` (no default)
- **`--target gsheet`**: a five-action pipeline
  - **download_link_gsheet**: Downloads data from Google Sheets to CSV
  - **update_article_url**: Extracts article URLs from HN links via the HN API
  - **update_article_tag**: Classifies articles by topic using an LLM
  - **update_article_cluster**: Maps topics to higher-level cluster categories
  - **upload_link_gsheet**: Uploads the processed CSV back to Google Sheets
- **`--target local_csv`** (requires `--local_csv <path>`): only
  `update_article_url`, `update_article_tag`, and `update_article_cluster`
  apply (no gsheet download/upload); rows are read directly from
  `--local_csv`, and the final clustered result is written back into that
  same file in place
- Only processes rows with empty target columns (incremental, resumable)

#### Examples
- Run the complete pipeline on a Google Sheets document:
  ```bash
  > pre_process_bookmarks.py --target gsheet --url "$LINKS_GSHEET" --all_actions
  ```

- Just download data from Google Sheets:
  ```bash
  > pre_process_bookmarks.py \
      --target gsheet --url "$LINKS_GSHEET" \
      --action download_link_gsheet
  ```

- Extract article URLs only:
  ```bash
  > pre_process_bookmarks.py \
      --target gsheet --url "$LINKS_GSHEET" \
      --action update_article_url
  ```

- Tag articles using a specific LLM model:
  ```bash
  > pre_process_bookmarks.py \
      --target gsheet --url "$LINKS_GSHEET" \
      --action update_article_tag \
      --model gpt-4o-mini
  ```

- Run the same enrichment pipeline directly against a local CSV instead of a
  Google Sheet, updating it in place:
  ```bash
  > pre_process_bookmarks.py \
      --target local_csv --local_csv bookmarks.csv \
      --all_actions
  ```

### `download_link_articles.py`

#### What It Does
- Downloads article content and HN comments; `--input` is the primary,
  gsheet-free way to run it, accepting either a single HN submission/article
  URL (bypassing Google Sheets, type auto-detected) or a path to a local
  bookmarks CSV (batch mode, all its rows); `--url` remains available for a
  live Google Sheets document
- Saves downloaded content to text files with bash-safe filenames derived from the
  `Title` column
- Actions: **download_hn_url**, **download_article_url**, **summarize_hn_url**,
  **summarize_article_url**

#### Examples
- Download a single HN submission directly, bypassing Google Sheets:
  ```bash
  > download_link_articles.py \
      --input "https://news.ycombinator.com/item?id=40212490" \
      --all_actions
  ```

- Download and summarize all rows from a local bookmarks CSV:
  ```bash
  > download_link_articles.py --input bookmarks.csv --all_actions
  ```

- Download HN comments for rows 0-10 of a local bookmarks CSV where `Hn_url`
  is not empty:
  ```bash
  > download_link_articles.py \
      --input bookmarks.csv \
      --row_idx "0:10" \
      --action download_hn_url
  ```

- Download all (HN comments and article) for the first row of a Gsheet:
  ```bash
  > download_link_articles.py --url "$LINKS_GSHEET" --row_idx 1 --all_actions
  ```

- Summarize articles for all rows of a Gsheet:
  ```bash
  > download_link_articles.py --url "$LINKS_GSHEET" --action summarize_article_url
  ```

### `process_bookmarks.py`

#### What It Does
- Processes unprocessed rows (no `Done` flag) from a local bookmarks CSV (columns:
  `Title`, `Article_url`, `Hn_url`, `Timestamp`, `Article_tag`, `Article_cluster`,
  `Done`), up to `--limit` rows
- For each row:
  1. Calls `download_hn_article_to_md.py` to download and summarize the submission
     (article + HN comments) under `--output_dir`
  2. Merges the article summary and HN comments summary into a single
     `<date>.hn_<item_id>.<title>.summary.md` file, with an `# Info` section
     (`Title`, `Article`, `HN`, `Timestamp`, `Article_tag`, `Article_cluster`, an
     empty manual `Score: ` placeholder) followed by `# Article Summary` (12-15
     bullet points) and `# HN Comments Summary` (10-15 comments) sections
  3. Sets `Done=yes` on the row and saves the CSV in place, so an interrupted run
     can resume
  - A row whose `Hn_url` isn't a real HN item URL (e.g., a plain article link
    `Raindrop.io` put in that column) is set to `Done=skipped` immediately
    instead, with no download, so it stops occupying `--limit` slots on every
    future run
- Always reads and writes a local CSV directly, unlike `pre_process_bookmarks.py`
  and `download_link_articles.py`, for which a local CSV is one of two supported
  data sources (selected via `--target`/`--input`, alongside a live Google Sheet)
- **Destination reconciliation**: separately from row processing, every invocation
  copies the cached merged summary for every `Done=yes` row that's missing from the
  selected destination (`--dest_type {gdrive,obsidian,none}`, default `gdrive`;
  `--dest_dir <path>` overrides the built-in path) -- no re-download, no
  re-summarize. This runs over *all* `Done=yes` rows, not bounded by `--limit`
  (`--limit 0` runs reconciliation only), and is what makes destinations
  independent: switching `--dest_type` later backfills the new one for free
  - Every invocation also always backs up merged summaries into a fixed,
    git-tracked dir, independent of `--dest_type` (a version-controlled copy,
    separate from the user-selectable viewing destination)
- `--dry_run` reports, without downloading, writing, or mutating the CSV: rows to be
  newly processed, rows to be marked `skipped`, and rows to be copied/repaired into
  the selected destination

#### Examples
- Process up to 10 unprocessed rows (default), copying to Google Drive:
  ```bash
  > process_bookmarks.py \
      -i /Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv \
      --limit 10
  ```

- Preview what would be done without downloading or writing anything:
  ```bash
  > process_bookmarks.py --input bookmarks.csv --dry_run
  ```

- Reprocess rows even if already marked `Done`, overwriting existing local output
  files:
  ```bash
  > process_bookmarks.py --input bookmarks.csv --no_incremental
  ```

- Copy merged summaries to the Obsidian vault instead of Google Drive:
  ```bash
  > process_bookmarks.py --input bookmarks.csv --dest_type obsidian
  ```

- Keep the merged summaries local (under `--output_dir`) only:
  ```bash
  > process_bookmarks.py \
      --input bookmarks.csv \
      -o ./tmp.hn_downloads \
      --dest_type none
  ```

- Backfill a destination for rows already processed, without downloading anything
  new:
  ```bash
  > process_bookmarks.py --input bookmarks.csv --dest_type obsidian --limit 0
  ```

### `process_one_off_gsheet_links.py`

#### What It Does
- One-off migration pipeline that renames old topic tags to their simplified names in
  the Gsheet
- Steps: download from Google Sheets, replace tags in the local CSV, upload the
  result back

#### Examples
- Run the complete tag-renaming pipeline:
  ```bash
  > process_one_off_gsheet_links.py --url "$LINKS_GSHEET"
  ```

## Description of Workflows

### Full Link-Processing Workflow
- **Purpose**: Ingest new bookmarks, classify them, and archive their content and
  summaries

- **Steps**:
  1. Download links from `Raindrop.io` and merge with the existing gsheet:
     ```bash
     > update_bookmarks_from_raindrop.py --target gsheet --url "$LINKS_GSHEET" --all_actions
     ```
  2. Extract article URLs and classify by topic/cluster:
     ```bash
     > pre_process_bookmarks.py --target gsheet --url "$LINKS_GSHEET" --all_actions
     ```
  3. Download HN comments and article content:
     ```bash
     > download_link_articles.py --url "$LINKS_GSHEET" --all_actions
     ```
  4. Summarize articles and HN comments using an LLM:
     ```bash
     > download_link_articles.py --url "$LINKS_GSHEET" --action summarize_article_url
     > download_link_articles.py --url "$LINKS_GSHEET" --action summarize_hn_url
     ```
  5. Review the results in the new timestamped tabs in Google Sheets and the
     downloaded files (articles, comments, summaries) in the local directory

### CSV-Based Bookmark Processing Workflow

- **Purpose**: run the same enrichment, download, and summarization stages as
  the Gsheet-based workflow above, but tracked in a local CSV (e.g., the
  `combined_data.csv` produced by `update_bookmarks_from_raindrop.py`'s
  `combine_data` action) instead of a live Google Sheet
- **Steps**:
  1. Extract article URLs and classify by topic/cluster, updating the CSV in
     place:
     ```bash
     > pre_process_bookmarks.py \
         --target local_csv --local_csv bookmarks.csv \
         --all_actions
     ```
  2. Download HN comments and article content, and summarize them using an
     LLM:
     ```bash
     > download_link_articles.py --input bookmarks.csv --all_actions
     ```
  3. Merge the downloaded summaries into per-item files and mark rows `Done`:
     ```bash
     > process_bookmarks.py -i bookmarks.csv --limit 3
     ```
- See `process_bookmarks.py`'s own module docstring for the full row-processing,
  skip, and destination-reconciliation flow, and `download_hn_article_to_md.py`'s
  docstring for the per-item output filename convention (`<base>.1.article_url.md`,
  `<base>.2.article_url.summary.md`, etc.)
- **Notes**:
  - Rerunning `process_bookmarks.py` later only processes the next unprocessed rows
    (`Done` still unset), since the CSV is updated in place after each row
  - Use `--dry_run` first to see which rows would be picked up without downloading or
    writing anything
  - Use `--no_incremental` to force re-download and re-summarize rows already marked
    `Done`

### Modular Raindrop Sync and Multi-Destination Bookmark Workflow
- 3 scripts (`update_bookmarks_from_raindrop.py`, `pre_process_bookmarks.py`,
  `process_bookmarks.py`) each have a second, independently-selectable mode,
  instead of separate scripts:
  - `update_bookmarks_from_raindrop.py`: a `--target` selects whether new
    `Raindrop.io` bookmarks are synced into a live **Google Sheet** or
    directly into a **local CSV** file
  - `pre_process_bookmarks.py`: a `--target` selects whether URL extraction,
    tagging, and clustering apply to a live **Google Sheet** or a **local
    CSV** file, updated in place
  - `process_bookmarks.py`: a `--dest_type` selects whether merged summaries
    are copied to **Google Drive**, the **Obsidian** vault, or kept local
    only; any of the 3 scripts can be run at any time, independently of the
    others, and a fixed git-tracked dir is always backed up into as well (see
    `process_bookmarks.py`'s docstring)
  - All 3 scripts share their core logic (Raindrop fetching/field-mapping;
    URL extraction/tagging/clustering; download+summarize+merge) across
    modes/destinations; only the small input/output-path logic differs per
    mode

- **`update_bookmarks_from_raindrop.py --target {gsheet,local_csv}`**
  (required, no default):
  - `--target gsheet`: 4 actions (`download_gsheet_links`,
    `download_raindrop_data`, `combine_data`, `upload_gsheet_links`);
    latest-timestamp cutoff comes from a Google Sheet download,
    `combine_data` writes a new tmp combined CSV for the upload step
    ```bash
    > update_bookmarks_from_raindrop.py \
        --target gsheet --url "$LINKS_GSHEET" --all_actions
    ```
  - `--target local_csv`: only `download_raindrop_data` and `combine_data`
    apply (no gsheet download/upload); requires `--local_csv <path>`;
    latest-timestamp cutoff is read directly from that file, and
    `combine_data` prepends newly-fetched Raindrop rows into that same file
    in place, leaving every existing row (`Done` included) untouched
    ```bash
    > update_bookmarks_from_raindrop.py \
        --target local_csv \
        --local_csv /Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv \
        --action download_raindrop_data --action combine_data
    ```

- **`pre_process_bookmarks.py --target {gsheet,local_csv}`**
  (required, no default):
  - `--target gsheet`: 5 actions (`download_link_gsheet`, `update_article_url`,
    `update_article_tag`, `update_article_cluster`, `upload_link_gsheet`)
    ```bash
    > pre_process_bookmarks.py --target gsheet --url "$LINKS_GSHEET" --all_actions
    ```
  - `--target local_csv`: only `update_article_url`, `update_article_tag`, and
    `update_article_cluster` apply (no gsheet download/upload); requires
    `--local_csv <path>`; rows are read directly from that file, and the
    final clustered result is written back into it in place
    ```bash
    > pre_process_bookmarks.py \
        --target local_csv --local_csv bookmarks.csv \
        --all_actions
    ```

- **`process_bookmarks.py --dest_type {gdrive,obsidian,none}`**
  (default: `gdrive`) with optional `--dest_dir <path>` to override the
  built-in path for the selected type:
  - Row processing (`--limit`-bounded): a row with `Done` empty is
    downloaded, summarized, merged into `<base>.summary.md` under
    `--output_dir`, and marked `Done=yes` -- this step is destination-agnostic
  - A row whose `Hn_url` isn't a real HN item URL (e.g., a plain article link
    `Raindrop.io` put in that column) is marked `Done=skipped` immediately, no
    download, so it stops occupying `--limit` slots on every future run
    (handling plain-article bookmarks is out of scope)
  - Destination reconciliation (runs every invocation over **all**
    `Done=yes` rows, not `--limit`-bounded): for the selected `--dest_type`/
    `--dest_dir`, any `Done=yes` row whose `<base>.summary.md` is missing from
    that destination gets copied there from the local `--output_dir` cache --
    no re-download, no re-summarize, no LLM cost. This is what makes
    destinations independent: running once with `--dest_type gdrive` and
    later with `--dest_type obsidian` backfills Obsidian for free from files
    already processed. A fixed git-tracked dir is always reconciled into as
    well, regardless of `--dest_type`
    ```bash
    # Process the next 10 unprocessed rows and copy them to Google Drive
    > process_bookmarks.py -i CSV --dest_type gdrive --limit 10

    # Process the next 10 unprocessed rows and copy them to Obsidian instead
    > process_bookmarks.py -i CSV --dest_type obsidian --limit 10

    # Keep merged summaries local only (still backed up to the git dir)
    > process_bookmarks.py -i CSV --dest_type none --limit 10

    # Reconcile Obsidian only (no new downloads) for rows already Done
    > process_bookmarks.py -i CSV --dest_type obsidian --limit 0
    ```
  - `--dry_run` reports, without downloading, writing, or mutating the CSV:
    rows to be newly processed this run, rows to be marked `skipped`, and rows
    to be copied/repaired into the selected destination
  - Each new `<base>.summary.md`'s `# Info` section includes an empty `Score: `
    line, for you to fill in by hand while reading (matches the manual rating
    convention already used in the Obsidian vault, e.g. `Score: 2/5`); it is
    never LLM-computed
  - Article summaries: 12-15 bullet points; HN comments summaries: 10-15
    comments

- **Notes**:
  - Same incremental/resume behavior as the CSV-Based Bookmark Processing
    Workflow above: rerun any time, only the outstanding batch is processed
  - `--dest_type gdrive` and `--dest_type obsidian` can both be run against the
    same CSV over time; neither is a replacement for the other
