<!-- toc -->

- [Check Links Script](#check-links-script)
  * [Goal](#goal)
  * [Usage Examples](#usage-examples)
    + [Basic Usage](#basic-usage)
    + [Verbose Output](#verbose-output)
  * [Architecture](#architecture)
    + [Core Components](#core-components)
    + [Output Format](#output-format)

<!-- tocstop -->

# Check Links Script

## Goal

The `check_links.py` script validates the reachability of URLs found in text
files, particularly Markdown files. It extracts various URL formats from the
input file, attempts to reach each URL via HTTP/HTTPS requests, and reports
which links are broken or unreachable.

## Usage Examples

### Basic Usage

Check links in a Markdown file:

```bash
> check_links.py --in_file README.md
```

### Verbose Output

Check links with debug-level logging:

```bash
> check_links.py --in_file docs.txt -v DEBUG
```

## Architecture

### Core Components

1. **URL Extraction (`_extract_urls_from_text`)**
   - Uses regex patterns to find URLs in multiple formats:
     - Markdown links: `[text](https://example.com)`
     - Standalone URLs: `https://example.com`
   - Returns deduplicated list of URLs

2. **URL Validation (`_check_url_reachable`)**
   - Makes HTTP/HTTPS requests with 10-second timeout
   - Uses custom User-Agent to avoid blocking
   - Returns `True` for HTTP status codes < 400
   - Handles various exceptions gracefully

3. **File Processing (`_check_links_in_file`)**
   - Reads input file using `helpers.hio`
   - Extracts and validates all URLs
   - Categorizes URLs as reachable or broken
   - Provides progress logging

### Output Format

The script provides:

- Real-time status for each URL (✓ for reachable, ✗ for broken)
- Summary statistics (total, reachable, broken counts)
- List of all broken URLs for easy fixing
