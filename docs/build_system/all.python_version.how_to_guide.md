<!-- toc -->

- [Python Version - How to Guide](#python-version---how-to-guide)
  * [Where the Python version lives](#where-the-python-version-lives)
  * [Why this matters](#why-this-matters)
  * [Procedure for bumping Python](#procedure-for-bumping-python)
  * [Sweep checklist (per repo)](#sweep-checklist-per-repo)
  * [Rolling back](#rolling-back)
  * [Tool reference](#tool-reference)

<!-- tocstop -->

# Python Version - How to Guide

This document is the procedure for upgrading the Python interpreter version
used by the dev container, the thin env, and any related surfaces (Lambda
runtimes, IaC, etc.).

## Where the Python version lives

The single source of truth is `repo_config.yaml`:

```yaml
python_info:
  python_version: "3.12"
```

The value is read by:

- `dev_scripts_helpers/thin_client/build.py` - drives the thin env, calls
  `uv venv --python ${python_version}` so the host venv matches the
  container venv interpreter.
- `devops/docker_build/dev.Dockerfile` - passes the value as the
  `PINNED_PYTHON_VERSION` build arg.
- `devops/docker_build/install_os_packages.sh` - asserts that the base
  image's `python3 --version` matches the pin and fails the build on
  drift.
- `helpers.repo_config_utils.RepoConfig.get_python_version()` - the
  Python accessor used wherever else the version needs to be read
  programmatically.

The pin is at **major.minor** granularity (e.g., `"3.12"`). Patch-level
upgrades inside the Ubuntu base image (or `uv python install`) do not
require a config bump.

## Why this matters

Without a single source of truth the dev container, the thin env, Lambda
runtimes, CI workers, and IaC templates drift independently. That has
already caused subtle bugs (e.g., the legacy `pyyaml == 5.3.1` thin-env
workaround was incompatible with Python 3.12 and only surfaced when the
thin env was test-built on a fresh host). Centralizing the version makes
drift impossible to introduce silently: the dev container build fails
fast on mismatch, and the thin env build refuses to create a venv on an
interpreter that does not match the pin.

## Procedure for bumping Python

1. **Pick the new version.** Confirm the target interpreter is supported
   by every transitive dependency (Poetry deps for the container,
   `requirements.txt` for the thin env, AWS Lambda for serverless).

2. **Update `repo_config.yaml`** in the `helpers` repo (and in any
   consumer repo that has its own copy, e.g., `csfy/repo_config.yaml`).
   Set `python_info.python_version` to the new value.

3. **Update the dev container base image.** Edit
   `devops/docker_build/dev.Dockerfile` so `FROM ubuntu:<release>` ships
   the requested Python by default; the pin check in
   `install_os_packages.sh` will fail the build otherwise.

4. **Rebuild the thin env locally.** Run
   `dev_scripts_helpers/thin_client/build.py` (default flow; uses `uv`).
   The script will:
   - Bootstrap `uv` if missing.
   - Run `uv python install <new_version>`, which downloads an Astral-
     managed Python build if the host does not have it.
   - Create the venv with the pinned interpreter.
   - Install `requirements.txt`.

5. **Rebuild the dev container.**
   - `invoke docker_build_local_image --version <new>`
   - For the uv-installer flow: pass `BUILD_TOOL=uv` as a docker build
     arg.

6. **Run the regression suites.**
   - `invoke run_fast_tests`
   - `invoke run_slow_tests`
   - `invoke run_superslow_tests`
   - Run the Allure workflows from a branch via
     `gh workflow run "Allure fast tests" --ref <branch>` to validate the
     CI image with the new pin.

7. **Sweep the other Python references.** See the checklist below.

8. **Open the PR** with title `Upgrade Python to <new_version>` and link
   to this how-to.

## Sweep checklist (per repo)

When bumping Python, audit and update these locations if they reference
the version explicitly:

- `repo_config.yaml#python_info.python_version` (this repo and any
  consumer repo).
- `devops/docker_build/dev.Dockerfile` - the `FROM ubuntu:<release>` line
  and the `PINNED_PYTHON_VERSION` default.
- `devops/docker_build/pyproject.toml` - Poetry's `python = "..."`
  constraint, if it forbids the new version.
- `infra/devops/docker_build/` - the standalone infra Docker build (not a
  symlink to the main `devops/`); update its `FROM ubuntu` and any
  Python-version comments to match.
- `infra/terraform/.../terraform.tfvars` - Lambda `runtime = "python3.X"`
  declarations.
- `infra/terraform/modules/lambda/templates/layer-build.sh` - the SAM
  build image (`public.ecr.aws/sam/build-python3.X:latest`).
- Any pre-built Lambda layer ARNs referencing the old Python version
  (e.g., `AWSLambdaPowertoolsPythonV3-python3XY-...`).
- `dev_scripts_*/thin_client/requirements.txt` - cap or floor specific
  packages whose wheels do not yet ship for the new interpreter.

## Rolling back

If the post-merge bake reveals a regression (test failures only on the
new interpreter, missing wheels on PyPI, etc.):

1. Revert the `python_info.python_version` bump in `repo_config.yaml`.
2. Revert the `FROM ubuntu:<release>` change in `dev.Dockerfile`.
3. Rebuild the dev image and the thin env on the previous pin.
4. File a follow-up issue with the specific failure mode.

The pin check in `install_os_packages.sh` will fail the build instead of
silently shipping a mismatched image, so a half-rolled-back state is not
possible.

## Tool reference

- `uv` (Astral) - the default installer for the thin env and an opt-in
  installer for the dev container (`BUILD_TOOL=uv`). Faster than pip and
  Poetry, can manage interpreters via `uv python install`.
- `poetry` - the historical dev-container installer (`BUILD_TOOL=poetry`,
  default). Remains supported for backward compatibility with the
  existing CI image.
- `pip` - the historical thin-env installer; available as the
  `--use_pip` fallback on `build.py` for hosts where `uv` cannot be
  bootstrapped.

See:

- [Pytest Allure explanation](all.pytest_allure.explanation.md)
- [Pytest Allure how-to](all.pytest_allure.how_to_guide.md)
