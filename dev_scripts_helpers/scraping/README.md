# Hacker News Links Processor

## HN Gsheet
- The list of links is stored in a Gsheet
	- E.g., https://docs.google.com/spreadsheets/d/1i6Z7v2TzPdftR9BQ5Ia6jrrNWvVy-pUCxZAt4A59l8M

- The schema
	- `Title`
		- "Rust is not a good C replacement"
	- `Url`
		- https://drewdevault.com/2019/03/25/Rust-is-not-a-good-C-replacement.html
		- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4752797
		- https://news.ycombinator.com/item?id=40212490
	- `Timestamp`
		- 2024-04-30 22:23:54
	- `Article_url`
		- If it's a HN link
		- https://medium.com/airbnb-engineering/chronon-airbnbs-ml-feature-platform-is-now-open-source-d9c4dba859e8
	- `Article_title`
		- If it's a HN link
		- Typically the same as `Title`
	- `Article_tag`
		- "Automated Theorem Proving"
	- `Article_cluster`
		- "AI"
	- `Interesting`
		-  (1 to 5)
	- `Notes`

from_gsheet.py --url https://docs.google.com/spreadsheets/d/1i6Z7v2TzPdftR9BQ5Ia6jrrNWvVy-pUCxZAt4A59l8M/edit?gid=1509921826#gid=1509921826 --tabname "All" --output_file file.csv

## Update Gsheet from Pocket / Raindrop

### Manual Download

- Go to http://raindrop.io, https://app.raindrop.io/my/0
- Export CSV / Get backup

- The schema is like
	- `id`
		- "1655820619"
	- `title`
		- "ripgrep is faster than {grep, ag, git grep, ucg, pt, sift} | hacker news"
	- `note`
	- `excerpt`
	- `url`
		- https://news.ycombinator.com/item?id=47499245`
	- `tags`
	- `created`
		- 2026-03-24t10:13:48.297z
	- `cover`
		- https://rdl.ink/render/https%3A%2F%2Fnews.ycombinator.com%2Fitem%3Fid%3D47499245
	- `highlights`
	- `favorite`
		- FALSE

### Download through API

```
> update_hn_gsheet_from_raindrop.py
```

### Update HN Gsheet

- Extract data
	- title
	- url
	- created
- Read the

## Complete Gsheet

- Point to a Gsheet with tabs
- Complete the missing cells
- Save a new Gsheet

Step 2\) If title is for an HN article, extract the article title and URL

Extract HN articles
dev\_scripts\_helpers/scraping\_script/extract\_hn\_article.py \--input\_file /Users/saggese/Downloads/Pocket\\ links\\ \-\\ All\\ \\(1\\).csv \--output\_file txt.csv

Step 3\) Decorate with tag1, tag2
The possible topics are [All\_links](https://docs.google.com/spreadsheets/d/1i6Z7v2TzPdftR9BQ5Ia6jrrNWvVy-pUCxZAt4A59l8M/edit?gid=1509921826#gid=1509921826)

Step 4\)

| title | url | Timestamp | Article\_url | Article\_tag |
| :---- | :---- | :---- | :---- | :---- |
| Writing a good Claude.md | Hacker News | https://news.ycombinator.com/item?id=46098838 | 2025-12-01T03:14:33.954Z | https://www.humanlayer.dev/blog/writing-a-good-claude-md | Prompt Engineering |

Step 5\) Download

dev\_scripts\_helpers/google/to\_gsheet.py \--input\_file out.csv \--url https://docs.google.com/spreadsheets/d/1UZiJlRqUhNiFEFhdmLzVkxQ1kll7hQhQE-rnzNuIz5c/edit?gid=209574908\#gid=209574908 \--tabname Sheet7

Step 6\) Read notes/papers.pocket.txt


## Description of Files

- `extract_hn_article.py`
  - Extracts article title and URL from Hacker News submissions and optionally classifies them using LLM

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
