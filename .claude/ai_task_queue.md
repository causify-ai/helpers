# Ready

# Backlog

### [ ] Add GitHub Actions CI to umd_classes

- Goal
  - `umd_classes` repo has no CI. `helpers_root` docs describe the linter/gitleaks
    workflow pattern used elsewhere in the org, but no `.github/workflows/` exist
    in this repo, so lint/test regressions are not caught automatically.

- Solution

- [ ] PR1: Add fast-tests workflow
- Add `.github/workflows/fast_tests.yml` that runs `pytest_log` (or
  `invoke run_fast_tests`) on push/PR, scoped to the dirs that already pass
  locally: `class_scripts`, `class_project`, `book_springer`,
  `class_cs_refreshers` (see TODO.md "[.] Make the unit tests pass in
  umd_classes" for which dirs are green)
- Reference existing patterns:
  `helpers_root/docs/build_system/all.linter_gh_workflow.explanation.md`
  `helpers_root/docs/tools/all.invoke_workflows.how_to_guide.md`

- [ ] PR2: Add linter + gitleaks workflow
- Add `.github/workflows/linter.yml` running `linters2/lint.py`
- Add `.github/workflows/gitleaks.yml` per
  `helpers_root/docs/tools/git/all.gitleaks.reference.md`
- Add a yamllint pre-commit hook (`repo: https://github.com/adrienverge/yamllint`)

- Examples
- `gh run list --workflow fast_tests.yml --limit 1` should show a run for
  `umd_classes1` after PR1 merges

### [ ] Merge count_lecture_* scripts

- Goal
  - `count_lecture_commentary_pages.py` (counts pages in book PDFs) and
    `count_lecture_pages.py` (counts pages in lecture PDFs) are near-duplicates;
    only the input file glob differs.

- [ ] PR1: Merge into one script with a mode flag
- Diff the two scripts to confirm only the input-file selection differs
- Merge into a single `count_lecture_pages.py` with a `--input_type
  {lecture,commentary}` (or `--glob`) option, or auto-detect from `--input_dir`
- Update callers (grep repo for both script names) and any docs/READMEs that
  reference the old name
- Delete the now-redundant script

- Examples
- `count_lecture_pages.py --input_type commentary --dir book_springer/...`
  replicates old `count_lecture_commentary_pages.py` output

### [ ] HelpersTask1342: Standardize executable CLI interfaces

- Goal
  - Executables across the repo use inconsistent flags for the same concept
    (input file, file list), making scripts harder to chain and remember.
  - Source: notes1/TODO.md ("HelpersTask1342_Fix_script_interfaces")

- Solution

- [ ] PR1: Audit and document the standard interface
- Grep all executables (`dev_scripts_helpers/`, `linters2/`, repo-root scripts)
  for their argparse flags
- Document the standard: `-i`/`--input` for a single input file, `--files` for
  a list of files, consistent with `helpers_root` conventions
- List every script that deviates

- [ ] PR2: Fix deviating scripts
- Update the deviating scripts (and their unit tests / call sites) to the
  standard interface, in small batches per PR to keep review tractable

- Examples
- `some_script.py -i file.md` and `some_script.py --files "a.py b.py"` work
  the same way across all listed scripts

### [ ] Rename lecture slide source files to .smd with L-prefix naming

- Goal
  - Lecture slide sources live as `.txt` under `lectures_source/` but are
    markdown-flavored slide files; naming is inconsistent
    (`Lesson01.1-AI_and_Machine_Learning.txt`).
  - Target: extension `.smd` (slide markdown), name pattern
    `L01.1-AI_and_machine_learning.smd` (`Lesson` -> `L`, keep `XY.Z` numbering,
    words lowercase-with-underscores as in the example).

- Solution

- [ ] PR1: Rename script
- Write a script (or extend `coding.rename` skill flow) that renames all
  `lectures_source/*.txt` files to the new `L<XY>.<Z>-<name>.smd` pattern
- Update every reference to the old filenames (slide-gen scripts, `gen_slides.py`,
  `notes_to_pdf.py`, test fixtures, docs) via `git.move`/`git.update_references`
  conventions
- Run affected unit tests (`msml610/test`, `data605/test`) to confirm nothing
  broke

- [ ] PR2: Port frontmatter
- Port each file's frontmatter to the style expected by the Latex/Typst
  pipeline (see `notes_to_pdf.py` frontmatter handling)

- Examples
  - `msml610/lectures_source/Lesson01.1-Intro.txt` ->
    `msml610/lectures_source/L01.1-intro.smd`

### [ ] Deduplicate docker_jupyter.sh via symlinks

- Goal
  - Multiple per-project `docker_jupyter.sh` files are byte-identical copies of
    `class_project/project_template/docker_jupyter.sh`, drifting out of sync
    when the template is updated.

- Solution

- [ ] PR1: Find and replace with symlinks
- Script: find every `docker_jupyter.sh` in the repo whose content matches
  `class_project/project_template/docker_jupyter.sh` byte-for-byte
- Replace each match with a relative symlink to the template file
- Skip (report, don't touch) any file that differs, for manual review

- Examples
- `ls -l research/some_project/docker_jupyter.sh` shows it as a symlink to
  `../../class_project/project_template/docker_jupyter.sh`

## msml610

### Create Book Chapter for L04*

- Run msml610/prompt.slides_and_book_flow.md

## gen_book_chapters.py

### [ ] Add cc loop in gen_book_chapters
- Instead of using an LLM use cc agent
  - Iterate until it compiles
  - run_typst.py --input msml610/book/Lesson01.4-Brief_History_of_AI.typ --output msml610/book/Lesson01.4-Brief_History_of_AI.pdf --action render_images --skip_action open_pdf

- Keep the LLM chat open so that we don't have to send the same instructions over and
  over (only for the library version)
- Also we can use this to keep track of the old text and make the transitions
  smoother

## git_create_issue_and_branch.py

###

git_create_issue_and_branch.py --no_submodules should be default

# Done
