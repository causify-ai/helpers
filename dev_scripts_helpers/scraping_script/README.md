# scraping_script

This directory contains tools for extracting data from Hacker News using the official API.

## Structure of the Dir

This directory contains only scripts and notebooks with no subdirectories.

## Description of Files

- `extract_hn_article.py`
  - Extracts article title and URL from Hacker News submissions using the Firebase API
- `SorrTask396_scraping_script.ipynb`
  - Exploratory notebook for developing HN data extraction functionality

## Description of Executables

### `extract_hn_article.py`

#### What It Does

- Extracts submission title and original article URL from Hacker News items using the official HN Firebase API
- Uses the programmatic API (https://hacker-news.firebaseio.com/v0/) instead of web scraping for reliability
- Supports single URL processing or batch CSV processing with automatic column insertion
- Displays progress bar when processing multiple URLs in CSV mode for better visibility
- Handles non-HN URLs gracefully with warnings and empty result columns

#### Examples

- Extract info from a single Hacker News URL:
  ```bash
  > ./extract_hn_article.py --hn_url "https://news.ycombinator.com/item?id=45148180"
  ```

- Process a CSV file with Hacker News URLs in a 'url' column:
  ```bash
  > ./extract_hn_article.py --input_file hn_links.csv --output_file results.csv
  ```

- Enable debug logging to see API calls:
  ```bash
  > ./extract_hn_article.py --hn_url "https://news.ycombinator.com/item?id=45148180" -v DEBUG
  ```

- Batch process with automatic column insertion after the 'url' column:
  ```bash
  > ./extract_hn_article.py --input_file input.csv --output_file output.csv
  ```
  The output CSV will have two new columns inserted after 'url': Article_title and Article_url
