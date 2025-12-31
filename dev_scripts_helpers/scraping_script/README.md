# scraping_script

This directory contains tools for web scraping operations.

## Structure of the Dir

This directory contains only scripts and notebooks with no subdirectories.

## Description of Files

- `extract_hn_article.py`
  - Extracts article title and URL from Hacker News discussion pages
- `SorrTask396_scraping_script.ipynb`
  - Exploratory notebook for developing scraping script functionality

## Description of Executables

### `extract_hn_article.py`

#### What It Does

- Extracts the submission title and original article URL from Hacker News discussion pages
- Supports single URL processing or batch CSV processing
- Issues warnings for non-Hacker News URLs and handles request failures gracefully

#### Examples

- Extract info from a single Hacker News URL:
  ```bash
  > ./extract_hn_article.py --hn_url "https://news.ycombinator.com/item?id=45619537"
  ```

- Process a CSV file with Hacker News URLs:
  ```bash
  > ./extract_hn_article.py --input_file hn_links.csv --output_file results.csv
  ```

- Process with verbose logging:
  ```bash
  > ./extract_hn_article.py --hn_url "https://news.ycombinator.com/item?id=45619537" -v DEBUG
  ```

- Batch process CSV where the input file has a 'url' column:
  ```bash
  > ./extract_hn_article.py --input_file input.csv --output_file output.csv
  ```
