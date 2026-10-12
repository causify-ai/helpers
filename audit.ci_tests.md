Given the output of pytest_multi_build.py --target . and the last run of master
on the CI
Figure out which are the tests that are runned locally but not in the CI and vice
versa and why

## Plan

Confirmed with user:
- CI scope = `Fast tests` + `Slow tests` + `Superslow tests` workflows only
- "Last run of master" = latest `push`-triggered run per workflow
- OK to compare local branch `gp` (commit `d35ceb9f`) as-is against
  `origin/master` (commit `f67eb2d1`), calling out branch differences if
  relevant
- Reuse already-generated local artifacts instead of re-running:
  - `dev_scripts_helpers/testing/pytest_multi_build.py.log`
  - `tmp.pytest_multi_build/apple.txt`
  - `tmp.pytest_multi_build/dev_container.txt`
  - `tmp.pytest_multi_build/docker.txt`

- [x] Confirm scope of "CI tests"
- [x] Confirm which "last run of master" to use per workflow
- [x] Confirm reuse of already-generated local artifacts
- [x] Flag branch mismatch (confirmed acceptable)
- [x] Extract the set of test node IDs collected/executed locally from each
      of the 3 build logs (apple / dev_container / docker)
- [x] Download CI logs for the chosen "last run of master" of each workflow
      and extract the set of test node IDs actually executed
- [x] Diff the sets: tests run locally but not in CI, and tests run in CI but
      not locally
- [x] Classify each difference by root cause (pytest marker filtering
      fast/slow/superslow, environment-conditional skips via `hserver`,
      machine-specific tests, e.g. `_gp_mac1`, docker engine differences
      apple/dev_container/docker vs CI's single docker image, missing
      AWS/S3/local-only resources, branch content differences, etc.)
- [x] Write up findings

## Result

### Done
- Compared the 3 local `pytest_multi_build.py --target .` build logs
  (`apple`, `dev_container`, `docker`) against the CI's last push-triggered
  `Fast tests` + `Slow tests` runs on master, plus the latest `Superslow
  tests` schedule run (it never runs on push, see below)
- Found `apple` and `docker` builds collect the exact same 4442 tests (they
  differ only in pass/fail outcome, not in which tests run); `dev_container`
  collects a different, smaller set (4215) because it runs inside the same
  Docker image CI uses
- Diffed `dev_container` (closest local analog to CI's execution
  environment) against the union of CI's Fast+Slow+Superslow node IDs
  (4160 tests): only 65 line differences out of ~4200 tests (~98.5% overlap)
- Root-caused every difference found; see summary below

### Not done
- Did not re-run `pytest_multi_build.py` fresh (reused today's existing
  artifacts, per user confirmation)
- Did not check out `origin/master` locally to eliminate the 1-commit branch
  drift (per user confirmation); the `test_htable.py` and the
  `test_pytest_multi_build.py` differences below are a direct consequence
  of that drift, not an environment/CI difference
- Did not investigate why CI's 3 jobs' "selected" counts sum to 4160 while
  each independently reports "collected 4162 items" (a 2-test discrepancy);
  judged immaterial to the root-cause analysis requested

## Summary

Local `dev_container` (the local build that runs inside the same Docker
image CI uses) and CI's `Fast tests` + `Slow tests` + `Superslow tests`
(last push run on `master`, except `Superslow tests` which only ever runs
on a daily schedule/`workflow_dispatch` — never on push) agree almost
perfectly: 4160 tests in the CI union vs 4215 tests locally, a difference
of only 65 test IDs out of ~4200 (~98.5% overlap). Every difference has a
concrete, code-level cause; none of it is unexplained drift:

1. **CI explicitly opts out of one whole file (49 tests).**
   `dev_scripts_helpers/documentation/test/test_notes_to_pdf.py` skips
   itself entirely when `hserver.is_inside_ci()` is true (lines 22-26):
   building the Docker images it exercises takes too long for CI. Runs
   locally (`apple`, `dev_container`, `docker`), never in CI.

2. **A marker-stacking gap causes 2 tests to be invisible to CI on every
   job.** CI splits tests into three *mutually exclusive* `-m` marker
   expressions: `not slow and not superslow` (Fast), `slow and not
   superslow` (Slow), `not slow and superslow` (Superslow). A test tagged
   with **both** `@pytest.mark.slow` and `@pytest.mark.superslow` (one via
   class decorator, one via method decorator) matches none of the three
   expressions and is deselected everywhere — it never runs in CI, on any
   job, regardless of how long it is allowed to run. This looks like a
   genuine gap in the fast/slow/superslow partitioning, worth flagging to
   the team.

3. **Branch drift (`gp` is 1 commit ahead of `origin/master`).** The CI
   run being compared against tested `origin/master` @ `f67eb2d1`; the
   local run was on branch `gp` @ `d35ceb9f`. Two files differ between the
   branches:
   - `helpers/test/test_htable.py`: `gp` adds a new test class
     (`Test_compute_column_widths`, 5 tests) on top of the file that
     already exists on `master`.
   - `dev_scripts_helpers/testing/test/test_pytest_multi_build.py`: `gp`
     renamed/restructured `Test_cleanup_old_files` (2 tests on `master`)
     into an extra `Test_run_build::test4` (1 test on `gp`).
   Neither is an environment or CI-selection difference — re-running CI on
   branch `gp` itself would make these match.

Separately (outside the 65-test diff above, but still part of "runs
locally" via `pytest_multi_build.py`): the `apple`/`docker` builds run
*outside* the dev container, on gp's Mac host venv, and additionally
collect 9 files that `dev_container`/CI don't (`test_cc_lib.py`,
`test_cc_script.py`, `test_llm_cli.py`, `test_hllm.py`,
`test_hllm_decorator.py`, `test_cc_lint.py`, and 3 more) because those
files start with `pytest.importorskip("claude_agent_sdk"/"llm"/"openai")`
and those packages are only installed in the host venv, not in the Docker
image. The inverse also happens: `test_hasyncio.py`, `test_haws.py`, and
`test_hlogging.py` skip on the host venv
(`if not hserver.is_inside_docker(): pytest.skip(...)`) but run fine in
`dev_container` and in CI.

## Problematic Tests

### Only in CI-skip-by-design (49 tests, run locally, skipped in CI)
All of `dev_scripts_helpers/documentation/test/test_notes_to_pdf.py`:
`Test_notes_to_pdf1` (test1-4), `Test_notes_to_pdf_filters` (test1-5),
`Test_notes_to_pdf_output_types` (test1-3), `Test_notes_to_pdf_toc_options`
(test1-4), `Test_notes_to_pdf_actions` (test1-3),
`Test_notes_to_pdf_script_generation` (test1-2),
`Test_notes_to_pdf_errors` (test1-2), `Test_notes_to_pdf_edge_cases`
(test1-4), `Test_notes_to_pdf_pandoc_ast` (test1-3),
`Test_notes_to_pdf_latex_options` (test1-2),
`Test_notes_to_pdf_typst_abbrevs::test1`,
`Test_notes_to_pdf_latex_colors` (test1-6),
`Test_notes_to_pdf_color_abbrevs_in_math` (test1-2),
`Test_notes_to_pdf_tilde_in_code::test1`,
`Test_notes_to_pdf_latex_cancel` (test1-4), `Test_small_font_code_typst::test1`,
`Test_notes_to_pdf_lectures_template` (test1-2).

### Marker-stacking bug (2 tests, run locally, never selected by any CI job)
- `dev_scripts_helpers/documentation/test/test_render_images.py::Test_render_image_code1::test1`
- `dev_scripts_helpers/documentation/test/test_render_images.py::Test_render_image_code1::test4`
- Cause: class carries `@pytest.mark.superslow`, these 2 methods
  additionally carry `@pytest.mark.slow` → excluded from all 3 CI marker
  expressions simultaneously.

### Branch drift, `gp` vs `master` (run locally only, will exist in CI once merged)
- `helpers/test/test_htable.py::Test_compute_column_widths::test1..test5`
  (5 tests, new class added on `gp`)
- `dev_scripts_helpers/testing/test/test_pytest_multi_build.py::Test_run_build::test4`
  (1 test, from restructuring on `gp`)

### Branch drift, `master` vs `gp` (run in CI only, removed/renamed on `gp`)
- `dev_scripts_helpers/testing/test/test_pytest_multi_build.py::Test_cleanup_old_files::test1`
- `dev_scripts_helpers/testing/test/test_pytest_multi_build.py::Test_cleanup_old_files::test2`

### Host-venv-only (apple/docker builds; need packages not in the Docker image)
`dev_scripts_helpers/ai/test/test_cc_lib.py`,
`dev_scripts_helpers/ai/test/test_cc_script.py`,
`dev_scripts_helpers/documentation/test/test_count_words.py`,
`dev_scripts_helpers/documentation/test/test_generate_images.py`,
`dev_scripts_helpers/download/test/test_download_to_md.py`,
`dev_scripts_helpers/llms/test/test_llm_cli.py`,
`helpers/test/test_hllm.py`, `helpers/test/test_hllm_decorator.py`,
`linters2/test/test_cc_lint.py`
(`pytest.importorskip("claude_agent_sdk" / "llm" / "openai")`).

### Docker-only (dev_container/CI; need `hserver.is_inside_docker()`)
`helpers/test/test_hasyncio.py`, `helpers/test/test_haws.py`,
`helpers/test/test_hlogging.py`
(`if not hserver.is_inside_docker(): pytest.skip(...)`).
