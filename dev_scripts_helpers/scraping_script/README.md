# scraping_script

This directory contains tools for extracting data from Hacker News using the official API.

## Structure of the Dir

- `test/`
  - Unit tests and test outcomes for HN article extraction

## Description of Files

- `extract_hn_article.py`
  - Extracts article title and URL from Hacker News submissions and optionally classifies them using LLM
- `SorrTask396_scraping_script.ipynb`
  - Exploratory notebook for developing HN data extraction functionality

## Description of Executables

### `extract_hn_article.py`

#### What It Does

- Extracts submission title and original article URL from Hacker News items using the official HN Firebase API (https://hacker-news.firebaseio.com/v0/)
- Processes CSV files with HN URLs in batches and adds Article_title and Article_url columns
- Updates output CSV file incrementally after each batch for fault tolerance during URL extraction
- Optionally classifies articles into predefined categories using LLM with configurable batch processing
- Updates output CSV file incrementally after each batch during LLM tagging for fault tolerance
- Displays progress bars for both URL extraction and LLM tagging workloads
- Handles non-HN URLs gracefully with warnings and empty result columns
- Uses caching to avoid redundant API calls for previously processed URLs

#### Examples

- Process a CSV file with Hacker News URLs in a 'url' column:
  ```bash
  > ./extract_hn_article.py --input_file input.csv --output_file output.csv
  ```
  The output CSV will have two new columns inserted after 'url': Article_title and Article_url. URLs are processed in batches of 10 (default) with the output file updated after each batch.

- Process with custom batch size for URL extraction:
  ```bash
  > ./extract_hn_article.py --input_file input.csv --output_file output.csv --url_batch_size 5
  ```
  Processes 5 URLs per batch instead of the default 10. Useful for more frequent checkpoints with large files.

- Enable debug logging to see API calls and batch processing:
  ```bash
  > ./extract_hn_article.py --input_file input.csv --output_file output.csv -v DEBUG
  ```

- Process CSV and classify articles using LLM:
  ```bash
  > ./extract_hn_article.py --input_file input.csv --output_file output.csv --tag_articles
  ```
  Adds Article_tag column with LLM-generated category tags from predefined list. The output file is updated after each batch, allowing recovery from interruptions.

- Process with custom batch sizes for both URL extraction and LLM tagging:
  ```bash
  > ./extract_hn_article.py --input_file input.csv --output_file output.csv --url_batch_size 20 --tag_articles --batch_size 5
  ```
  Processes 20 URLs per batch during extraction and 5 titles per LLM batch call during tagging.

- Use a specific LLM model for tagging:
  ```bash
  > ./extract_hn_article.py --input_file input.csv --output_file output.csv --tag_articles --model gpt-4
  ```
  Uses gpt-4 model for article classification instead of the default model.
