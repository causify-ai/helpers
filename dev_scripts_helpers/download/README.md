# Download Tools

- Scripts to download, convert, and summarize content (web pages, academic
  papers, Hacker News submissions, podcast transcripts) to Markdown, plus a
  pipeline for managing a Google Sheets-based link database.

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
| `download_link_articles.py`            | Download/summarize article content and HN comments for rows in a Gsheet      | Gsheet Pipelines    |
| `download_to_md.py`                    | Detect input type and dispatch to the matching `download_*_to_md.py` script  | Content Downloaders |
| `download_utils.py`                    | Shared helpers for fetching article titles and summarizing text via an LLM   | Shared Utilities    |
| `podcast_dl.py`                        | Download and format a podcast transcript from various sources                | Podcast Tools       |
| `podcast_dl_example.sh`                | Example invocations of `podcast_dl.py` for each supported source type        | Podcast Tools       |
| `process_gsheet_links.py`              | Pipeline to extract HN article URLs and classify articles by topic/cluster   | Gsheet Pipelines    |
| `process_one_off_gsheet_links.py`      | One-off pipeline to rename topic tags in the Gsheet (data migration)         | Gsheet Pipelines    |
| `update_gsheet_links_from_raindrop.py` | Sync new bookmarks from `Raindrop.io` into the Gsheet                        | Gsheet Pipelines    |

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
  - `Article_url`: URL of the actual article (extracted from HN submission if applicable)
    - _Example_:
      https://medium.com/airbnb-engineering/chronon-airbnbs-ml-feature-platform-is-now-open-source-d9c4dba859e8
  - `Article_title`: Title of the actual article (extracted from HN submission if applicable)
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
- `--output` is only forwarded to the dispatched script when specified;
  otherwise the dispatched script derives its own output name

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
  `2016.Ribeiro_et_al.Why_Should_I_Trust_You...`, shared across the `.pdf`,
  `.md`, and `.summary.md` outputs
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

- Downloads a Hacker News link: both the comments and the article it points
  to
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

- Downloads an HTML page (or reads a local HTML file) and converts it to
  Markdown using one of several converters: `auto` (BeautifulSoup, falling
  back to readability), `pandoc`, `bs`, or `readability`
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
- Each step writes a numbered file to `<OUTPUT>.md.tmp/`, and the final
  result is copied to `<OUTPUT>.md`

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

### `update_gsheet_links_from_raindrop.py`

#### What It Does

- Synchronizes bookmarks from `Raindrop.io` with a Google Sheets document
- Implements a four-action pipeline:
  - **download_gsheet_links**: Downloads current data from Google Sheets to
    CSV
  - **download_raindrop_data**: Fetches new bookmarks from the `Raindrop.io`
    API (only items created after the latest timestamp in the gsheet)
  - **combine_data**: Transforms and combines `Raindrop.io` data into the
    gsheet schema
  - **upload_gsheet_links**: Uploads combined data back to Google Sheets in a
    new timestamped tab
- Requires the `RAINDROP_API_TOKEN` environment variable

#### Examples

- Sync all new bookmarks from `Raindrop.io` to Google Sheets:
  ```bash
  > update_gsheet_links_from_raindrop.py \
      --url "$LINKS_GSHEET" \
      --all_actions
  ```

- Just download from Google Sheets:
  ```bash
  > update_gsheet_links_from_raindrop.py \
      --url "$LINKS_GSHEET" \
      --clear_actions \
      --action download_gsheet_links
  ```

- Just fetch from `Raindrop.io` (requires `RAINDROP_API_TOKEN`):
  ```bash
  > update_gsheet_links_from_raindrop.py \
      --url "$LINKS_GSHEET" \
      --clear_actions \
      --action download_raindrop_data
  ```

- Combine data without uploading:
  ```bash
  > update_gsheet_links_from_raindrop.py \
      --url "$LINKS_GSHEET" \
      --clear_actions \
      --action download_gsheet_links \
      --action download_raindrop_data \
      --action combine_data
  ```

### `process_gsheet_links.py`

#### What It Does

- Pipeline for enriching Hacker News articles from a Google Sheets document:
  - **download_link_gsheet**: Downloads data from Google Sheets to CSV
  - **update_article_url**: Extracts article URLs from HN links via the HN
    API
  - **update_article_tag**: Classifies articles by topic using an LLM
  - **update_article_cluster**: Maps topics to higher-level cluster
    categories
  - **upload_link_gsheet**: Uploads the processed CSV back to Google Sheets
- Only processes rows with empty target columns (incremental, resumable)

#### Examples

- Run the complete pipeline on a Google Sheets document:
  ```bash
  > process_gsheet_links.py --url "$LINKS_GSHEET" --all_actions
  ```

- Just download data from Google Sheets:
  ```bash
  > process_gsheet_links.py --url "$LINKS_GSHEET" --action download_link_gsheet
  ```

- Extract article URLs only:
  ```bash
  > process_gsheet_links.py --url "$LINKS_GSHEET" --action update_article_url
  ```

- Tag articles using a specific LLM model:
  ```bash
  > process_gsheet_links.py \
      --url "$LINKS_GSHEET" \
      --action update_article_tag \
      --model gpt-4o-mini
  ```

### `download_link_articles.py`

#### What It Does

- Downloads article content and HN comments from links stored in Google
  Sheets (or a single URL via `--input`, bypassing Google Sheets)
- Saves downloaded content to text files with bash-safe filenames derived
  from the `Title` column
- Actions: **download_hn_url**, **download_article_url**,
  **summarize_hn_url**, **summarize_article_url**

#### Examples

- Download all (HN comments and article) for the first row of the Gsheet:
  ```bash
  > download_link_articles.py --url "$LINKS_GSHEET" --row_idx 1 --all_actions
  ```

- Download HN comments for rows 0-10 where `Url` is not empty:
  ```bash
  > download_link_articles.py \
      --url "$LINKS_GSHEET" \
      --row_idx "0:10" \
      --action download_hn_url
  ```

- Download a single article URL directly, bypassing Google Sheets:
  ```bash
  > download_link_articles.py \
      --input "https://news.ycombinator.com/item?id=40212490" \
      --all_actions
  ```

- Summarize articles for all rows:
  ```bash
  > download_link_articles.py --url "$LINKS_GSHEET" --action summarize_article_url
  ```

### `process_one_off_gsheet_links.py`

#### What It Does

- One-off migration pipeline that renames old topic tags to their simplified
  names in the Gsheet
- Steps: download from Google Sheets, replace tags in the local CSV, upload
  the result back

#### Examples

- Run the complete tag-renaming pipeline:
  ```bash
  > process_one_off_gsheet_links.py --url "$LINKS_GSHEET"
  ```

## Description of Workflows

### Full Link-Processing Workflow

- **Purpose**: Ingest new bookmarks, classify them, and archive their content
  and summaries

- **Steps**:
  1. Download links from `Raindrop.io` and merge with the existing gsheet:
     ```bash
     > update_gsheet_links_from_raindrop.py --url "$LINKS_GSHEET" --all_actions
     ```
  2. Extract article URLs and classify by topic/cluster:
     ```bash
     > process_gsheet_links.py --url "$LINKS_GSHEET" --all_actions
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
