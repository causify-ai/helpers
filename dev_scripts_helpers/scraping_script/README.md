# scraping_script

This directory contains tools for extracting data from Hacker News using the official API.

## Structure of the Dir

This directory contains only scripts and notebooks with no subdirectories.

## Description of Files

- `extract_hn_article.py`
  - Extracts article title and URL from Hacker News submissions and optionally classifies them using LLM
- `SorrTask396_scraping_script.ipynb`
  - Exploratory notebook for developing HN data extraction functionality

## Description of Executables

### `extract_hn_article.py`

#### What It Does

- Extracts submission title and original article URL from Hacker News items using the official HN Firebase API
- Uses the programmatic API (https://hacker-news.firebaseio.com/v0/) instead of web scraping for reliability
- Processes CSV files with HN URLs and adds Article_title and Article_url columns
- Optionally classifies articles into categories using LLM with configurable batch processing
- Displays progress bar when processing URLs for better visibility
- Handles non-HN URLs gracefully with warnings and empty result columns

#### Examples

- Process a CSV file with Hacker News URLs in a 'url' column:
  ```bash
  > ./extract_hn_article.py --input_file input.csv --output_file output.csv
  ```
  The output CSV will have two new columns inserted after 'url': Article_title and Article_url

- Enable debug logging to see API calls:
  ```bash
  > ./extract_hn_article.py --input_file input.csv --output_file output.csv -v DEBUG
  ```

- Process CSV and classify articles using LLM:
  ```bash
  > ./extract_hn_article.py --input_file input.csv --output_file output.csv --tag_articles
  ```
  Adds Article_tag column with LLM-generated category tags

- Process with custom batch size for LLM tagging:
  ```bash
  > ./extract_hn_article.py --input_file input.csv --output_file output.csv --tag_articles --batch_size 5
  ```
  Processes 5 titles per LLM batch call instead of the default 10

- Use a specific LLM model for tagging:
  ```bash
  > ./extract_hn_article.py --input_file input.csv --output_file output.csv --tag_articles --model gpt-4
  ```
  Uses gpt-4 model for article classification
