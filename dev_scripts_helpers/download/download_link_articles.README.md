# Overview

- Downloads article content and Hacker News comments from links stored in Google
  Sheets
- Supports actions:
  - fetching HN comments
  - downloading article content
  - summarizing both using Claude (via `llm_cli.py`)
- Output files are stored locally with sanitized titles from the spreadsheet.
- Designed to work with Google Sheets as a data source, the official HN API for
  comments, web scraping for article extraction, and optional LLM-based
  summarization
