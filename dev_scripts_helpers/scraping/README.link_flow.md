# Hacker News Links Processor

## Overview

This directory contains scripts for managing, processing, and enriching links
(from Hacker News and other sources) stored in Google Sheets.

The workflow involves downloading links from various sources (Google Sheets,
Raindrop.io), enriching them with article metadata and AI-generated tags, and
syncing the processed data back to Google Sheets.

## Link Gsheet Schema

- E.g., 
  ```
  export LINKS_GSHEET="<your-google-sheets-url>"
  # E.g.,
  export LINKS_GSHEET=https://docs.google.com/spreadsheets/d/1i6Z7v2TzPdftR9BQ5Ia6jrrNWvVy-pUCxZAt4A59l8M/edit?gid=1324796321#gid=1324796321
  ```

- The master Google Sheets document contains the following columns:
  - `Title`: Article title
    - Example: "Rust is not a good C replacement"
  - `Url`: Source URL
    - Can be: direct article URL, paper link, or Hacker News submission URL
    - Examples:
      https://drewdevault.com/2019/03/25/Rust-is-not-a-good-C-replacement.html,
      https://news.ycombinator.com/item?id=40212490
  - `Timestamp`: Date and time when added
    - Format: YYYY-MM-DD HH:MM:SS
    - Example: 2024-04-30 22:23:54
  - `Article_url`: URL of the actual article (extracted from HN submission if applicable)
    - Example:
      https://medium.com/airbnb-engineering/chronon-airbnbs-ml-feature-platform-is-now-open-source-d9c4dba859e8
  - `Article_title`: Title of the actual article (extracted from HN submission if applicable)
    - Typically same as `Title` for HN submissions
  - `Article_tag`: Categorized topic/tag for the article
    - Example: "Automated Theorem Proving", "AI Infrastructure", "Python Ecosystem"
  - `Article_cluster`: High-level cluster grouping topics
    - Example: "AI", "Data/Infra", "Dev tools", "Finance", "Math", "Business",
      "CyberSec", "SwEng"
  - `Interesting`: Relevance rating (1 to 5)
  - `Notes`: Additional notes and comments

## Description of Files

### `update_link_gsheet_from_raindrop.py`

#### What It Does

- Synchronizes bookmarks from Raindrop.io with a Google Sheets document

- Implements a four-action pipeline:
  1. **download_link_gsheet**: Downloads current data from Google Sheets to CSV
  2. **download_raindrop_data**: Fetches new bookmarks from Raindrop.io API (only
     items created after the latest timestamp in the gsheet)
  3. **combine**: Transforms and combines Raindrop data into gsheet schema
  4. **upload_link_gsheet**: Uploads combined data back to Google Sheets in a new
     timestamped tab

- Features:
  - Incremental sync: only fetches new bookmarks by comparing timestamps
  - Field mapping: converts Raindrop fields to gsheet columns
  - Timestamp normalization: converts ISO 8601 format to YYYY-MM-DD HH:MM:SS
  - Title cleanup: strips "| HackerNews" suffix from Raindrop titles
  - Prepends new data: Raindrop bookmarks appear at the top of the gsheet
  - Automatic pagination: handles Raindrop API pagination to fetch all bookmarks
  - Fault tolerance: graceful handling of malformed timestamps

#### Example Usage

- Sync all new bookmarks from Raindrop to Google Sheets:
  ```bash
  > update_link_gsheet_from_raindrop.py \
      --url "$LINKS_GSHEET" \
      --all
  ```

- Run individual actions:
  ```bash
  # Just download from Google Sheets
  > update_link_gsheet_from_raindrop.py \
      --url "$LINKS_GSHEET" \
      --action download_link_gsheet

  # Just fetch from Raindrop (requires RAINDROP_API_TOKEN env var)
  > update_link_gsheet_from_raindrop.py \
      --action download_raindrop_data

  # Combine data without uploading
  > update_link_gsheet_from_raindrop.py \
      --action combine
  ```

- Requirements:
  - `RAINDROP_API_TOKEN` environment variable must be set to authenticate with
    Raindrop API
  - Google Sheets URL with data

### `process_link_gsheet.py`

#### What It Does

- A comprehensive pipeline for enriching and processing Hacker News articles from
  a Google Sheets document
- It performs five sequential actions:
  1. **download**: Downloads data from Google Sheets to CSV
  2. **update_article_url**: Extracts article URLs from HN links using the HN API
  3. **update_article_tag**: Classifies articles using LLM into predefined topics
  4. **update_article_cluster**: Maps topics to higher-level cluster categories
  5. **upload**: Uploads processed CSV back to Google Sheets with results

- Features:
  - Incremental processing with progress bars using tqdm
  - Fault tolerance: only processes rows with empty target columns, skips already-processed rows
  - Caching for HN API calls to avoid redundant lookups
  - LLM batch processing with configurable batch sizes
  - Automatic output file updates after each batch during tagging
  - Creates timestamped tabs in Google Sheets for each run

#### Example Usage

- Run the complete pipeline on a Google Sheets document:
  ```bash
  > process_link_gsheet.py \
      --url "$LINKS_GSHEET" \
      --all
  ```

- Run specific actions:
  ```bash
  # Just download data from Google Sheets
  > process_link_gsheet.py \
      --url "$LINKS_GSHEET" \
      --action download

  # Extract article URLs only
  > process_link_gsheet.py \
      --url "$LINKS_GSHEET" \
      --action update_article_url

  # Tag articles using LLM with custom model
  > process_link_gsheet.py \
      --url "$LINKS_GSHEET" \
      --action update_article_tag \
      --model gpt-4
  ```

### `download_link_articles.py`

#### What It Does

- Downloads article content and HN comments from links stored in Google Sheets
- Saves downloaded content to text files with bash-safe filenames derived from
  the Title column
- Supports filtering by column indices and column-based selection criteria

- Implements two actions:
  1. **download_url**: Downloads HN comments from HackerNews submission URLs
  2. **download_article_url**: Downloads article content from article URLs

- Features:
  - Incremental processing with progress bars using tqdm
  - Recursive HN comment fetching with depth limiting
  - Article content extraction using BeautifulSoup
  - Browser User-Agent header to avoid 403 Forbidden errors
  - Bash-safe filename generation from article titles
  - Column indexing with range support (e.g., "0:10" for rows 0-9)
  - Optional filtering by non-empty cells in a specified column
  - JSON caching for HN API calls to avoid redundant requests

#### Example Usage

- Download HN comments for rows 0-10 where Url column is not empty:
  ```bash
  > download_link_articles.py \
      --url "$LINKS_GSHEET" \
      --column_idx "0:10" \
      --select_column "Url" \
      --action download_url
  ```

- Download all (both HN comments and articles):
  ```bash
  > download_link_articles.py \
      --url "$LINKS_GSHEET" \
      --select_column "Article_url" \
      --all
  ```

- Download article content from Article_url column:
  ```bash
  > download_link_articles.py \
      --url "$LINKS_GSHEET" \
      --select_column "Article_url" \
      --action download_article_url
  ```

- Download from rows 0-5, skip downloading articles:
  ```bash
  > download_link_articles.py \
      --url "$LINKS_GSHEET" \
      --column_idx "0:5" \
      --select_column "Url" \
      --skip_action download_article_url
  ```

#### Output Files

- **HN Comments**: Filename format `TITLE.hn_comments.txt`
  - Contains recursively fetched comments with nested replies
  - Includes comment metadata: author, score, timestamp
  - Depth-limited to avoid excessive API calls

- **Article Content**: Filename format `TITLE.text.txt`
  - Contains extracted article text from <p> tags
  - Falls back to raw HTML if extraction fails
  - Uses browser User-Agent to avoid access restrictions

## Complete Workflow Example

A typical workflow for enriching links from multiple sources:

1. Download links from Raindrop.io and merge with existing gsheet:
   ```bash
   > update_link_gsheet_from_raindrop.py --url <sheet_url> --all
   ```

2. Process HN articles to extract URLs and classify by topic:
   ```bash
   > process_link_gsheet.py --url <sheet_url> --all
   ```

3. Download HN comments for selected articles:
   ```bash
   > download_link_articles.py \
       --url <sheet_url> \
       --select_column "Url" \
       --action download_url
   ```

4. Review the results in the new timestamped tabs created in Google Sheets and
   examine downloaded files in the local directory
