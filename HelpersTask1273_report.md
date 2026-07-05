# HelpersTask1273 Fix Plan

**Focus:** Fix the new temp-file regression in build1 (40 failures, vs 15 in prior run).

## Phase 1: Temp File Writes (X category, 20 tests) — QUICK WIN

### Fix 1.1: `dev_scripts_helpers/dockerize/lib_prettier.py:340–341`

**Current code:**
```python
tmp_file_name = "tmp.prettier_on_str." + file_type
hio.to_file(tmp_file_name, txt)
```

**Fix:** Use `self.get_scratch_space()`:
```python
# ... in prettier_on_str():
scratch_dir = self.get_scratch_space()
tmp_file_name = os.path.join(scratch_dir, f"tmp.prettier_on_str.{file_type}")
hio.to_file(tmp_file_name, txt)
# Then use tmp_file_name as before
```

**Tests affected:** 5 tests in test_lint_txt.py, 5 tests in test_hmarkdown_formatting.py

---

### Fix 1.2: `helpers/hlatex.py:29–30`

**Current code:**
```python
in_file_name = "./tmp.run_pandoc_in.md"
hio.to_file(in_file_name, txt)
```

**Fix:** Use `self.get_scratch_space()`:
```python
# ... in convert_pandoc_md_to_latex():
scratch_dir = self.get_scratch_space()
in_file_name = os.path.join(scratch_dir, "tmp.run_pandoc_in.md")
hio.to_file(in_file_name, txt)
# Update out_file_name similarly
out_file_name = in_file_name.replace(".md", ".tex")
```

**Tests affected:** 4 tests in test_transform_notes.py

---

### Fix 1.3: `helpers/test/test_hunit_test.py` — Check for relative-path writes

These tests are meta-tests that deliberately check the test framework's diff output. They may be writing to relative paths. **Need inspection:**

- `TestCheckString1::test_check_string_not_equal1`
- `TestCheckString1::test_check_string_not_equal3`
- `TestCheckDataFrame1::test_check_df_not_equal1..4`

**Tests affected:** 5 tests

---

## Phase 2: Graphviz Output Path (Y category, 13 tests) — MEDIUM

Graphviz (`dot`) fails to write PDFs. Error: `Could not open "output.pdf" for writing`.

**Suspected locations:**
- `import_check/test/test_show_imports.py` — where graphviz is called
- Graphviz Python library backend configuration

**Need to inspect:**
1. Where is the output path constructed in `test_show_imports.py`?
2. Is it a relative path? Should be absolute or use temp dir.
3. Check if the test's working directory or output directory is accessible.

**Tests affected:** 13 tests in test_show_imports.py (all except test1, test10)

---

## Phase 3: Docker Mount / Permission Issues (Z category, 3 tests) — LOWER PRIORITY

These involve nested docker containers (latex, png, llm_transform). Failures are:
- pdflatex can't write `input.log`
- graphviz can't write in nested container
- llm_transform nested docker failure

**Root cause:** Likely user ID mapping, mount permissions, or working directory in nested container.

**Need to investigate:**
1. `dev_scripts_helpers/dockerize/lib_latex.py:292` — docker-cmd invocation
2. Mount configuration in docker-compose or hdocker.py
3. User ID mapping for nested containers (`--user $(id -u):$(id -g)`)

**Tests affected:** 3 tests

---

## Phase 4: Mount-Info Code Bug (E category, 2 tests) — DEFERRED (Known Issue)

This was identified in the prior report and is a real code bug (not a regression). Lower priority, high effort.

**Tests affected:** 2 tests in hdocker/hserver (also appears in build2/3)

---

## Execution Order

1. **Fix 1.1 + 1.2 + 1.3** — 30 min, fixes 14 tests immediately.
2. **Investigate Y** — 15 min, likely 1-line fix if it's a relative path.
3. **Re-run build1** — verify X and Y fixes drop build1 from 40 → ~10 failures.
4. **Tackle Z if time permits** — 1–2 hours, medium effort.
5. **Defer E** — documented, tracked for later.

---

## Testing Commands

```bash
# Build1 only (focus on in-container fixes)
manage_cache.py --action clear_all
(export CSFY_DOCKER_ENGINE="docker"; i docker_cmd --stage=local -v 1.6.0 --cmd "pytest . -k 'test_lint_txt or test_transform_notes or test_hmarkdown_formatting or test_show_imports'") 2>&1 | tee build1_verify.txt

# Full build1 re-run after fixes
manage_cache.py --action clear_all
(export CSFY_DOCKER_ENGINE="docker"; i docker_cmd --stage=local -v 1.6.0 --cmd "pytest .") 2>&1 | tee build1_rerun.txt
```

---

## Notes

- All fixes are **localized** (no ripple effects expected) — two module methods and one test file.
- Once X and Y are fixed, build1 should drop from 40 → ~10 failures (only Z, E, B, K remain).
- Fixes are **container-agnostic** — using `tempfile` works on any platform/OS.
- No changes to test expectations or goldens needed (just temp file paths).
