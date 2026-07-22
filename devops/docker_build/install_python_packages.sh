#!/usr/bin/env bash
#
# Install Python packages into the dev container's virtual environment.
#
# Two build tools are supported, selected via the `BUILD_TOOL` build arg
# (forwarded by `dev.Dockerfile`):
#
#   - `poetry` (default): the historical flow using `pyproject.toml`'s
#     `[tool.poetry]` section and `poetry.lock`. Kept as the default for
#     backward compatibility with the existing CI image.
#   - `uv`: the new flow that installs the same Poetry-declared
#     dependencies into the venv via `uv pip install`. `uv` resolves and
#     installs orders of magnitude faster than Poetry; the lock file
#     stays Poetry-managed (single source of truth) and is exported to a
#     plain `requirements.txt` for `uv` to consume.
#

echo "#############################################################################"
echo "##> $0"
echo "#############################################################################"

set -ex

source utils.sh

echo "# Disk space before $0"
report_disk_usage

echo "PYTHON VERSION="$(python3 --version)
echo "PIP VERSION="$(pip3 --version)
echo "POETRY VERSION="$(poetry --version)
echo "UV VERSION="$(uv --version || echo 'not installed')

# Default to poetry to preserve the existing image behavior when the build
# arg is omitted; uv is opt-in until the rollout is complete.
BUILD_TOOL=${BUILD_TOOL:-poetry}
echo "BUILD_TOOL=${BUILD_TOOL}"

echo "# Installing ${ENV_NAME} via ${BUILD_TOOL}"

if [[ "${BUILD_TOOL}" == "poetry" ]]; then
  # Poetry flow.
  echo "# Building environment with poetry"
  # Print config.
  poetry config --list --local
  echo "POETRY_MODE=$POETRY_MODE"
  if [[ $POETRY_MODE == "update" ]]; then
    # Compute dependencies.
    poetry lock -v
    cp poetry.lock /install/poetry.lock.out
  elif [[ $POETRY_MODE == "no_update" ]]; then
    # Reuse the lock file.
    cp /install/poetry.lock.in poetry.lock
  else
    echo "ERROR: Unknown POETRY_MODE=$POETRY_MODE"
    exit 1
  fi;
  # Install with poetry inside a venv.
  echo "# Install with venv + poetry"
  python3 -m ${ENV_NAME} /${ENV_NAME}
  source /${ENV_NAME}/bin/activate
  #pip3 install wheel
  poetry install --no-root
  poetry env list
  # Clean up.
  if [[ $CLEAN_UP_INSTALLATION ]]; then
    poetry cache clear --all -q pypi
  else
    echo "WARNING: Skipping clean up installation"
  fi;
  pip freeze 2>&1 >/install/pip_list.txt
  #
  if [[ $CLEAN_UP_INSTALLATION ]]; then
    pip cache purge
  else
    echo "WARNING: Skipping clean up installation"
  fi;
elif [[ "${BUILD_TOOL}" == "uv" ]]; then
  # uv flow: keep Poetry as the source-of-truth for dependency declaration
  # and lock data, but install via uv (much faster, deterministic). Export
  # the locked deps to a plain requirements file that uv consumes.
  echo "# Building environment with uv (Poetry-declared deps, uv installer)"
  poetry config --list --local
  echo "POETRY_MODE=$POETRY_MODE"
  if [[ $POETRY_MODE == "update" ]]; then
    # Refresh the lock file from `pyproject.toml`.
    poetry lock -v
    cp poetry.lock /install/poetry.lock.out
  elif [[ $POETRY_MODE == "no_update" ]]; then
    # Reuse the lock file pinned by the caller.
    cp /install/poetry.lock.in poetry.lock
  else
    echo "ERROR: Unknown POETRY_MODE=$POETRY_MODE"
    exit 1
  fi;
  # Export the resolved deps to a hash-free `requirements.txt` that uv can
  # consume. `--without-hashes` is required because `uv` does not always
  # mirror Poetry's hash format.
  pip3 install poetry-plugin-export --break-system-packages
  poetry export \
    --format requirements.txt \
    --output /install/requirements.uv.txt \
    --without-hashes \
    --with dev || \
  poetry export \
    --format requirements.txt \
    --output /install/requirements.uv.txt \
    --without-hashes
  # Create the venv with the pinned Python interpreter, then install.
  uv venv --python python3 --seed --clear /${ENV_NAME}
  source /${ENV_NAME}/bin/activate
  uv pip install --python /${ENV_NAME}/bin/python \
    --requirements /install/requirements.uv.txt
  # Snapshot for parity with the poetry flow.
  pip freeze 2>&1 >/install/pip_list.txt
  if [[ $CLEAN_UP_INSTALLATION ]]; then
    # `uv cache clean` is the equivalent of `pip cache purge`.
    uv cache clean
  else
    echo "WARNING: Skipping clean up installation"
  fi;
else
  echo "ERROR: Unknown BUILD_TOOL='${BUILD_TOOL}' (expected: poetry | uv)"
  exit 1
fi;

# Custom package installation.
echo "# Checking for custom package installation..."
if [[ -f "./install_custom_packages.sh" ]]; then
    echo "# Found custom installation script, executing..."
    chmod +x "./install_custom_packages.sh"
    source "./install_custom_packages.sh"
else
    echo "# No custom installation script found, skipping"
fi

# Clean up.
if [[ $CLEAN_UP_INSTALLATION ]]; then
  echo "Cleaning up installation..."
  DIRS="/usr/lib/gcc /tmp/* /install/tmp.pypoetry"
  echo "Cleaning up installation... done"
  du -hs $DIRS | sort -h
  rm -rf $DIRS
else
  echo "WARNING: Skipping clean up installation"
fi;

echo "# Disk space before $0"
report_disk_usage
