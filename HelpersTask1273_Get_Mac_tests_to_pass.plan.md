# Fix macOS Test Failures — Root Cause Analysis

Date: 2026-06-08
Total failures: 41
Docker image: 623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp:dev
Host architecture: aarch64 (ARM64 / Apple Silicon)

---

## Category 1: Missing `uv` tool in Docker container (rc=127)

**Size: ~18 tests (~44% of all failures)**

The scripts `convert_pdf_to_md.py`, `lint_txt.py`, and `summarize_md.py` all
invoke `uv` via `/usr/bin/env: 'uv'`, but `uv` is not installed in the base
Docker image `623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp:dev`.

**Error signature (identical across all affected tests):**

```
/usr/bin/env: 'uv': No such file or directory
rc='127'
```

### Affected tests

| Test file | Test(s) | Script that fails |
|---|---|---|
| `test_convert_pdf_to_md.py` | `Test_convert_pdf_to_md::test1` | `convert_pdf_to_md.py` |
| `test_lint_txt.py` | `Test_lint_txt_py1::test4` | `lint_txt.py --use_dockerized_prettier` |
| `test_piper_markdown_reader.py` | `Test__extract_markdown_section::test1,2,4,5,6,7` (6 tests) | `lint_txt.py` (called by `piper_markdown_reader.py`) |
| `test_summarize_md.py` | `Test_summarize_md_py1::test1-4` (4 tests) | `summarize_md.py` |
| `test_summarize_md.py` | `Test_summarize_md_py2::test1-4` (4 tests) | `summarize_md.py` |
| `test_summarize_md.py` | `Test_summarize_md_py3::test1-3` (3 tests) | `summarize_md.py` |

**Fix:** Install `uv` in the Docker image, OR remove the dependency on `uv` in
these scripts (e.g., use the system Python directly).

---

## Category 2: Golden file drift — environment variables mismatch

**Size: 10 tests**

### 2a. Docker compose file env vars (`Test_generate_compose_file*`)

**Affected tests:**
`Test_generate_compose_file1::test1,2,3,4`,
`Test_generate_compose_file2::test1,2,3,4`

The generated docker-compose YAML now contains 3 extra env vars that the golden
file does not expect:

```
< QUANDL_API_KEY=$QUANDL_API_KEY
< ARTIFICIAL_ANALYSIS_API_KEY=$ARTIFICIAL_ANALYSIS_API_KEY
< OPENROUTER_API_KEY=$OPENROUTER_API_KEY
```

Additionally, `Test_generate_compose_file1::test4` and
`Test_generate_compose_file2::test1-4` have different volume mount paths and
working directory paths in the linter section (e.g., `../../../:/app` vs
`../../:/app`, `/data/dummy/src/...` vs `/app:/src`).

**Fix:** Regenerate golden files for these tests by running with
`--update_outcome`.

### 2b. Notes-to-pdf script env vars (`Test_notes_to_pdf1`)

**Affected tests:** `Test_notes_to_pdf1::test2,3`

The docker run commands in the generated bash script pass different env vars
than the golden file expects. The golden file has `AM_GDRIVE_PATH`,
`AM_TELEGRAM_TOKEN`, etc. while the actual output has
`ARTIFICIAL_ANALYSIS_API_KEY`, `OPENROUTER_API_KEY`, `QUANDL_API_KEY`.

**Fix:** Regenerate golden files.

---

## Category 3: Architecture-dependent golden file (aarch64 vs x86_64)

**Size: 1 test**

**Test:** `Test_build_png_container1::test2` (`test_lib_png.py`)

The test checks the `convert` tool version string from ImageMagick. The golden
file expects:

```
Version: ImageMagick 7.1.2-19 Q16-HDRI x86_64 ...
```

But the container runs on an ARM64 host (Apple Silicon), producing:

```
Version: ImageMagick 7.1.2-19 Q16-HDRI aarch64 ...
```

**Root cause:** The golden file hardcodes the CPU architecture, making it
non-portable across x86_64 and ARM64 platforms.

**Fix:** Either (a) regenerate the golden file on the ARM64 host, or (b) make
the test architecture-agnostic by filtering out the architecture string before
comparison.

---

## Category 4: Golden file drift — linting output format changed

**Size: 5 tests**

**Affected tests:** `Test_lint_txt2::test3,6,8,9`,
`Test_lint_txt_py1::test1`

The `lint_txt.py` script produces different output than what the golden files
contain. Key differences include:

- **Table of contents:** The `<!-- toc -->` / `<!-- tocstop -->` sections are
  empty in actual output but the golden files expect TOC entries to be
  generated there.
- **Header formatting:** `# Header` is being stripped to `Header` in the
  actual output (or vice versa depending on the test).
- **Punctuation:** Backticks around literals like `` `%` `` and `` `tuple` ``
  are missing in actual output.
- **Capitalization:** E.g., `Python Formatting` vs `Python formatting`.

**Root cause:** The `lint_txt.py` behavior changed (possibly due to updated
dependencies like `prettier` or markdown parsers) but golden files were not
regenerated.

**Fix:** Investigate the linter behavior change first, then regenerate golden
files if the new behavior is correct.

---

## Category 5: Submodule guard in docker build/release tests

**Size: 3 tests**

**Affected tests:**
`Test_docker_build_prod_image1::test_candidate_user_tag1`,
`Test_docker_build_prod_image1::test_single_arch_prod_image1`,
`Test_docker_release_prod_image1::test_aws_ecr1`

All three fail with:

```
* Failed assertion *
cond=False
The build should be run from a super repo, not a submodule.
```

**Root cause:** The helpers repo is mounted as a nested module inside the
Docker container (`CSFY_USE_HELPERS_AS_NESTED_MODULE=1`). These docker
build/release tests correctly guard against being run from a submodule. The
code under test detects the current context as a submodule of the repo at
`/app` and refuses to proceed.

**Status: not a bug — the tests are working as designed.** These tests require
being run from a super-repo context, not from the helpers submodule in
isolation.

---

## Category 6: Test file outside standard `test/` directory

**Size: 2 tests**

**Affected tests:**
`TestLibTasksRunTests1::test_find_test_class1`,
`TestLibTasksRunTests1::test_find_test_files2`

Both fail with:

```
'book_proposals' == 'test'
Test file '/app/book_proposals/test_reorganize_books.py' needs to be under a `test` dir
```

**Root cause:** The test discovery logic found the file
`.../book_proposals/test_reorganize_books.py` and asserts that its parent
directory should be named `test`. However this file is under `book_proposals/`
— it uses a `test_` prefix but lives in a non-standard directory.

**Fix:** Move `test_reorganize_books.py` to a `test/` directory under
`book_proposals/`, or update the file to follow the standard naming convention
(e.g., `reorganize_books_test.py`).

---

## Bonus issue (non-fatal diagnostic)

During container startup:

```
find: '/app/helpers_root/dev_scripts_helpers/documentation/mkdocs': No such file or directory
```

This is not a test failure but indicates a stale reference in the container's
PATH setup script — the directory `mkdocs` inside `documentation/` no longer
exists but something still tries to add it to the PATH.

---

## Summary

| # | Root Cause | Tests | Severity | Suggested Fix |
|---|---|---|---|---|
| 1 | `uv` not installed in Docker image | ~18 | **High** | Install `uv` in Dockerfile or remove dependency |
| 2 | Golden file drift (env vars) | 10 | Medium | Regen golden files via `--update_outcome` |
| 3 | Architecture hardcoded in golden file | 1 | Low | Filter out arch or regen golden |
| 4 | Linter output format drifted | 5 | Medium | Investigate + regen golden files |
| 5 | Submodule guard in docker tests | 3 | Info | Working as designed |
| 6 | Test file outside `test/` dir | 2 | Low | Move file or rename |