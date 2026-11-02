# `summarize_md.py`

- Summarizes a markdown file section by section with an LLM
- Input: a markdown file and a header level (`--md_level`) that sets the size of each
  section
- Output: a markdown file with the same header structure, where the text of each
  section is replaced by its summary
- Used to compress a book chapter, a paper, or lecture notes to a fraction of their
  size (default 10%)

## Examples

- Summarize every level-1 chapter to 10% of its size (writes `book.summary.md`):

  ```bash
  > summarize_md.py -i book.md
  ```

- Summarize every level-2 section to at most 500 words, replacing the old output:

  ```bash
  > summarize_md.py \
      -i book.md \
      -o book.short.md \
      --md_level 2 \
      --max_words 500 \
      --overwrite
  ```

- Summarize only the level-2 sections from "Chapter 1" to "Chapter 2":

  ```bash
  > summarize_md.py \
      -i book.md \
      --md_level 2 \
      --select "Chapter 1:Chapter 2"
  ```

- Keep every header and bullet, shorten each bullet to 30% of its words, and write
  terse text:

  ```bash
  > summarize_md.py \
      -i book.md \
      --md_level 1 \
      --pct_words 0.3 \
      --keep_bullets \
      --caveman
  ```

- Check the result on the first section only, with a different model:

  ```bash
  > summarize_md.py \
      -i book.md \
      --md_level 1 \
      --dry_run \
      --model "openrouter/anthropic/claude-haiku-4.5"
  ```

## Configuration & Inputs

### Command-line Arguments

| Argument                                                                         | Type       | Default                                 | Description                                                                                   |
| :------------------------------------------------------------------------------- | :--------- | :-------------------------------------- | :-------------------------------------------------------------------------------------------- |
| `-i`, `--input`                                                                  | str        | required                                | Input markdown file (`-` for stdin is not supported: the file must exist)                     |
| `-o`, `--output`                                                                 | str        | `<input>.summary.md`                    | Output file; if equal to the input, the default name is used                                  |
| `--md_level`                                                                     | int        | 1                                       | Header level to summarize (1=H1, 2=H2, ...); 0 or -1 summarizes the whole file as one section |
| `--select`                                                                       | str        | `""` (all headers)                      | Range of headers as `START:END` (title prefix, header, or line number); see `--help`          |
| `--model`                                                                        | str        | `openrouter/deepseek/deepseek-v4-flash` | LLM model name, as `hllm_cli.DEFAULT_MODEL`                                                   |
| `--max_words`                                                                    | int        | 0 (not set)                             | Max words of the summary of each section; wins over `--pct_words`                             |
| `--pct_words`                                                                    | float      | 0.1                                     | Target size of each summary as fraction of the section words; 0 = no limit                    |
| `--keep_bullets`                                                                 | flag       | false                                   | Keep every header and bullet, shorten only the text of each bullet                            |
| `--caveman`                                                                      | flag       | false                                   | Write terse text: drop articles, filler, and hedging                                          |
| `--dry_run`                                                                      | flag       | false                                   | Summarize the first section only, print it, and stop                                          |
| `--test`                                                                         | flag       | false                                   | Write the SHA1 digest of each section instead of calling the LLM                              |
| `--overwrite`                                                                    | flag       | false                                   | Delete the output file if it exists; otherwise the script fails                               |
| `--action`, `--skip_action`, `--only_action`, `--all_actions`, `--clear_actions` | str / flag | actions `summarize`, `lint`             | Select the actions to run (see `helpers.hselect_action`)                                      |
| `-v`                                                                             | str        | `INFO`                                  | Log level: `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`                           |
| `--no_report_command_line`                                                       | flag       | false                                   | Do not print the command line                                                                 |
- `--max_words` and `--pct_words` are mutually exclusive
- `--input_files` and `--from_file` are accepted by the parser but ignored: the
  script processes one file at a time
- Valid actions
  - `summarize`: split the file, summarize each section, write the output
  - `lint`: format the output file with `lint_text.py`; skipped with `--test`

### Environment Variables

- `OPENROUTER_KEY`: API key for the default OpenRouter model, read by the
  `llm-openrouter` plugin (not needed with `--test`)

### Dependencies

- The `uv run` header of the script installs: `llm`, `llm-openrouter`, `tokencost`,
  `markdown-it-py`, `tqdm`
- The style rules file `text.rules.md` must be in the Git tree, since the script adds
  it to the system prompt

## Output & Side Effects

### Files Created

- Output file: `<input>.summary.md` (or `<input>.summary` if the input does not end
  with `.md`), or the path given by `--output`
  - The file is emptied at the start and then appended section by section, so a
    failed run leaves the sections done so far
  - Each section starts with its header line, followed by its summary
  - Parent headers (level lower than `--md_level`) are written once, before their
    first child, together with the summary of their intro text
- With `--select`, only the sections in the range are written
- The input file is never modified

### Exit Codes

- `0`: Success
- Non-zero: Failure, e.g., the input file is missing, no header exists at
  `--md_level`, `--select` matches no header, or the output file exists without
  `--overwrite`

### Logging

- Prints to stdout:
  - Statistics of the input: word count, estimated read time (250 words per minute),
    header level, compression target
  - The list of headers to summarize
  - Statistics of the output: word count, read time, compression rate
- Shows a `tqdm` progress bar with the running LLM cost
- Logs the total LLM cost at `INFO` level
- Logs a warning if the LLM returns more words than the limit: the summary is not
  truncated
- Changes the log level with `-v`

## Software Architecture

### Data Flow

1. **Input**: `_main()` parses the arguments and reads the markdown file
2. **Parsing**: `markdown-it-py` builds the token list, and
   `_extract_headers_from_ast()` turns it into `(level, title, line_number)` tuples
3. **Selection**: `_get_target_headers()` keeps the headers at `--md_level`, cut to
   the `--select` range
4. **Section extraction**: for each target header, `_extract_section()` returns the
   lines up to the next header of the same or higher level, including all nested
   content
5. **Prompt**: `_get_system_prompt()` builds the system prompt from `text.rules.md`
   plus the optional `--keep_bullets` and `--caveman` rules, and
   `_get_length_constraint()` adds the length rule to it
6. **Summary**: `_summarize_text()` calls the LLM, or computes a SHA1 digest with
   `--test`
7. **Output**: `_process_headers_for_summarization()` appends the header and the
   summary to the output file
8. **Lint**: the `lint` action formats the output file

### Key Functions

- `_main(parser: argparse.ArgumentParser) -> None`
  - Parses the arguments, selects the actions, and runs `summarize` and `lint` in
    order
- `_run_summarize_action(args, in_file_name, out_file_name) -> str`
  - Orchestrates parse, selection, prompt building, summarization, and statistics;
    returns the output file path
- `_get_target_headers(all_headers, *, md_level, md_start, md_end) -> List[Tuple[int, str, int]]`
  - Filters headers by level and range; returns one synthetic header
    `Entire Document` if `md_level <= 0`
- `_extract_section(header, all_headers, lines, *, md_level) -> str`
  - Returns the text of one section, without trailing empty lines
- `_remove_section_header(section_text: str) -> str`
  - Removes the header line before the LLM call, since the script writes it itself
- `_get_max_words_out(text, *, max_words, pct_words) -> int`
  - Computes the word limit of a summary: `max_words` first, then `pct_words` of the
    words of the section
- `_get_length_constraint(max_words_out, num_words_in) -> str`
  - Builds the length rule written in the prompt
- `_summarize_text(text, system_prompt, model, *, test_mode, max_words, pct_words) -> Tuple[str, float]`
  - Returns the summary and its cost; skips the LLM for empty text
- `_process_headers_for_summarization(...) -> Tuple[float, int]`
  - Loops over the target headers, writes the output file, and returns the total cost
    and the summary word count
- `_prepare_output_file(in_file_name, out_file_name, overwrite) -> str`
  - Resolves the output name and handles an existing file

### Design Patterns

- **Prompt-only limits**: `--max_words` and `--pct_words` are written in the LLM
  prompt. The script never truncates the input or the summary, and only warns when
  the LLM exceeds the limit
- **Incremental output**: the file grows section by section, so progress survives a
  failure
- **Action pipeline**: `summarize` and `lint` use `helpers.hselect_action`, so a user
  can run only one
  - `--only_action lint` formats the file in `--output`, or the input file in place
    if `--output` is not set
- **Deterministic test mode**: `--test` replaces the LLM with a SHA1 digest, which
  lets the unit tests in
  `dev_scripts_helpers/documentation/test/test_summarize_md.py` run without network
  or cost
- **Cost**: one LLM call per section (plus one per intro text), so the cost grows
  linearly with the number of target headers