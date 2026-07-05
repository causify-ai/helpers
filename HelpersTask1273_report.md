# Failing tests report (from `run.sh`)

Generated from `build1.txt`, `build2.txt`, `build3.txt` produced by `run.sh`
(`HelpersTask1273_Get_Mac_tests_to_pass` branch).

## Run summary

| Build | Command | Result |
|---|---|---|
| `build1.txt` | `CSFY_DOCKER_ENGINE=docker; i docker_cmd --stage=local -v 1.6.0 --cmd "pytest ."` | **Aborted before any test ran.** `docker pull causify/helpers:local-saggese-1.6.0` → `manifest unknown`. Image tag not published; not a test failure. |
| `build2.txt` | `CSFY_DOCKER_ENGINE=docker; pytest_log .` (pytest run natively on the Mac host, `docker` engine used for any dockerized sub-processes) | 85 failed, 3199 passed, 231 skipped, 525s |
| `build3.txt` | `CSFY_DOCKER_ENGINE=apple; pytest_log .` (same, but `apple` container engine) | 85 failed, 3194 passed, 236 skipped, 436s |

`build2` and `build3` fail the **same 84 tests**, plus one engine-specific test each
(see category F). `build3` also has 5 additional `SKIPPED` (not failed) tests, all
explicitly marked `"Fails with Apple container engine, see HelpersTask1273"` in
`dockerize/test/test_lib_pandoc.py`, `test_lib_png.py`, `test_lib_prettier.py` (x3) —
these are pre-existing skip markers added by this task, not fixes.

## Root-cause categories

### A — Golden file hardcodes a container path (`/app/...`), actual run is native on host
Tests run natively on the Mac (not inside the `causify/helpers` container), so real
paths are `/Users/.../helpers_root/...` instead of the container's `/app/helpers_root/...`
that the `check_string` golden files were captured against.

- `helpers/test/test_hdocker.py::Test_convert_to_docker_path1::test1`
- `helpers/test/test_hdocker.py::Test_convert_to_docker_path1::test2`
- `linters/test/test_amp_check_md_toc_headers.py::Test_verify_toc_postion::test1`
- `linters/test/test_amp_dev_scripts.py::Test_linter_py1::test_linter1`
- `linters/test/test_amp_dev_scripts.py::Test_linter_py1::test_linter2`
- `linters/test/test_amp_dev_scripts.py::Test_linter_py1::test_linter_txt1`
- `linters/test/test_amp_dev_scripts.py::Test_linter_py1::test_linter_txt2`
- `linters/test/test_amp_dev_scripts.py::Test_linter_py1::test_DevToolsTask408`

Fails in: **build2, build3**.

### B — Module dotted-name depends on the parent-directory name at import time
Golden files hardcode a module qualname (e.g. `helpers.test.test_hobject._Object1`).
Depending on where the repo checkout sits (`/app/helpers_root` in the container vs
`/Users/saggese/src/csfy1/helpers_root` on this host), pytest's import-mode picks up an
extra ancestor directory (`app` or `csfy1`) as a namespace-package prefix, so the actual
qualname becomes `csfy1.helpers...` or `.app.linters...` instead of the golden's plain
`helpers...`/`linters...`. Root cause is checkout-path-dependent, not a real code bug —
but it means these goldens can never match on an arbitrary host checkout path.

- `helpers/test/test_hobject.py::Test_obj_to_str1::test1..6` (6)
- `helpers/test/test_hobject.py::Test_obj_to_str2::test1..6` (6)
- `helpers/test/test_hobject.py::Test_PrintableMixin_to_config_str::test1`, `test2` (2)
- `helpers/test/test_hintrospection.py::Test_is_pickleable1::test_method3`
- `helpers/test/test_hintrospection.py::Test_get_name_from_function1::test1`
- `helpers/test/test_hintrospection.py::Test_get_function_from_string1::test1`
- `helpers/test/test_hunit_test_mock.py::Test_Mock_Class_with_context_manager1::test1`
- `helpers/test/test_hdbg.py::Test_dassert_issubclass1::test_man_fail1`, `test_man_fail2` (2)
- `linters/test/test_amp_normalize_import.py::TestEndToEndShortImports::test_normalize_imports`
- `linters2/test/test_normalize_import.py::TestEndToEndShortImports::test_normalize_imports`

Fails in: **build2, build3**.

### C — Host is missing the `pydeps` CLI tool
`pydeps` is installed in the Docker image but not on the bare Mac host `PATH`
(`/bin/bash: pydeps: command not found`, rc=127).

- `import_check/test/test_detect_import_cycles.py::Test_detect_import_cycles::test1..13` (13)
- `import_check/test/test_show_imports.py::Test_show_imports::test1..14` (14)

Fails in: **build2, build3**. Fix: install `pydeps` in the host venv, or route these
through a container.

### D — Host tool versions differ from the container image (docformatter/autoflake/isort)
Output text differs because the host's installed formatter/linter version (or the tool
is simply missing) doesn't match the version pinned in the Docker image.

- `linters/test/test_amp_doc_formatter.py::Test_docformatter::test1`
- `linters/test/test_amp_doc_formatter.py::Test_docformatter::test2`
- `linters/test/test_amp_doc_formatter.py::Test_docformatter::test3`
- `linters/test/test_amp_doc_formatter.py::Test_docformatter::test5`
- `linters/test/test_amp_doc_formatter.py::Test_docformatter::test7` — host: `docformatter: command not found`
- `linters/test/test_amp_autoflake.py::TestAutoflake::test1`
- `linters/test/test_amp_autoflake.py::TestAutoflake::test2`
- `linters/test/test_isort.py::TestISort::test1`

Fails in: **build2, build3**.

### E — `hdocker`/`hserver` shared-path & mount-info logic is stale (real code bug)
Actual output uses an old shared-folder naming convention / is missing GP-Mac-specific
docker-info fields; not path-prefix noise, the values themselves are wrong or
undefined. Needs a code fix, not a golden-file update.

- `helpers/test/test_hdocker.py::Test_replace_shared_root_path1::test1` — `/data/shared1/asset1` != `/shared_folder1/asset1`
- `helpers/test/test_hdocker.py::Test_replace_shared_root_path1::test2` — `/data/shared/ecs_tokyo/...` != `/shared_folder/ecs/...`
- `helpers/test/test_hdocker.py::Test_get_docker_mount_info1::test1` — mount root not resolved to `/path/only/on/outer/host`
- `helpers/test/test_hserver.py::Test_hserver_outside_docker_container_on_gp_mac1::test_get_docker_info1` — `has_docker_sibling_containers_support`/`has_docker_children_containers_support` come back `*undef*`

Fails in: **build2, build3**.

### F — Engine-specific branch in `Test_get_docker_command1` is one-sided
Exactly one of the two engine variants fails per run (`'docker' != 'container'`
under `apple`, and the reverse under `docker`), i.e. the code path that switches on
`CSFY_DOCKER_ENGINE` doesn't produce the right command for both engines. Likely a
real (small) bug in the docker/apple engine branch, worth a direct look.

- `helpers/test/test_hdocker.py::Test_get_docker_command1::test6` — fails only in **build2** (`docker` engine)
- `helpers/test/test_hdocker.py::Test_get_docker_command1::test1` — fails only in **build3** (`apple` engine)

### G — `helpers/hllm.py` test/implementation skew (unrelated to Mac/Docker)
Tests reference attributes that don't exist on the module, and others need a
pre-recorded LLM-response cache that isn't present.

- `helpers/test/test_hllm.py::Test_retrieve_openrouter_model_info::test_missing_data_key_raises` — `AttributeError: module 'helpers.hllm' has no attribute '_retrieve_openrouter_model_info'`
- `helpers/test/test_hllm.py::Test_retrieve_openrouter_model_info::test_retrieve_success` — same
- `helpers/test/test_hllm.py::Test_save_models_info_to_csv::test_save_models_info` — `no attribute '_save_models_info_to_csv'`
- `helpers/test/test_hllm.py::Test_calculate_cost::test_openai_cost` — `no attribute 'LLMCostTracker'`
- `helpers/test/test_hllm.py::Test_calculate_cost::test_openai_unknown_model` — same
- `helpers/test/test_hllm.py::Test_calculate_cost::test_openrouter_load_existing_csv` — same
- `helpers/test/test_hllm.py::Test_get_completion::test1..4` (4) — `ValueError: Cache miss for key=...` (missing recorded fixture)

Fails in: **build2, build3**. Not platform-related — looks like the test file is ahead
of (or out of sync with) `helpers/hllm.py`; needs its own investigation independent of
this Mac-tests task.

### H — Python-version-dependent `OrderedDict` repr
Python 3.12 changed `OrderedDict.__repr__` to `OrderedDict({...})`; this host runs
Python 3.11.11 (`OrderedDict([(...)])`), so the golden (captured on a newer Python,
presumably the container's) no longer matches.

- `helpers/test/test_hnumpy.py::Test_OrderedDict_repr_str::test_repr_full1`
- `helpers/test/test_hnumpy.py::Test_OrderedDict_repr_str::test_str_full1`

Fails in: **build2, build3**.

### I — pandas/numpy package-version skew (memory-usage byte counts differ)
`df.memory_usage()` byte counts differ from golden, consistent with a pandas/numpy
version difference between the host venv and the container image.

- `helpers/test/test_hpandas_utils.py::Test_df_to_str::test_df_to_str10`

Fails in: **build2, build3**.

### J — Mac-specific `open` behavior needs investigation
Golden expects `None`, actual is the literal `open a.pdf` command string — looks like
the code path meant to be a no-op/mock in this test environment is instead returning
the command it would have run. Needs a closer look at `hopen`/`test_hopen.py::Test_open_pdf::test_mac1`.

- `helpers/test/test_hopen.py::Test_open_pdf::test_mac1`

Fails in: **build2, build3**.

### K — Meta-test of the diff-printing format itself
`Test_AssertEqual1.test_not_equal1` deliberately compares two unequal strings to check
`hunit_test`'s diff-formatting output, and that formatted output is itself checked
against a golden file. The mismatch is a formatting/column-width difference in the
diff renderer, not a functional regression. This is also the source of the stray
`actual.txt`/`expected.txt` files left in the repo root.

- `helpers/test/test_hunit_test.py::Test_AssertEqual1::test_not_equal1`

Fails in: **build2, build3**.

## Tally

| Category | # tests | build2 | build3 |
|---|---|---|---|
| A — container-path golden | 8 | fail | fail |
| B — module-qualname prefix | 20 | fail | fail |
| C — missing `pydeps` | 27 | fail | fail |
| D — formatter/linter version skew | 8 | fail | fail |
| E — stale shared-path/mount-info code | 4 | fail | fail |
| F — engine-specific docker-command bug | 1 | fail (`test6`) | fail (`test1`) |
| G — `hllm` test/impl skew | 10 | fail | fail |
| H — `OrderedDict` repr (Python version) | 2 | fail | fail |
| I — pandas/numpy version skew | 1 | fail | fail |
| J — `hopen` Mac behavior | 1 | fail | fail |
| K — diff-format meta-test | 1 | fail | fail |
| **Total** | **83 shared + 1 engine-specific each = 85 per build** | | |
