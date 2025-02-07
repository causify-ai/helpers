#!/usr/bin/env bash
#
# Install Python packages.
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

echo "# Installing ${ENV_NAME}"

if [[ 1 == 1 ]]; then
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
else
  # Conda flow.
  echo "# Building environment with conda"
  update_env () {
    echo "Installing ${ENV_FILE} in ${ENV_NAME}"
    ENV_FILE=${1}
    conda env update -n ${ENV_NAME} --file ${ENV_FILE}
  }

  AMP_CONDA_FILE="devops/docker_build/conda.yml"
  update_env ${AMP_CONDA_FILE}

  if [[ $CLEAN_UP_INSTALLATION ]]; then
    conda clean --all --yes
  else
    echo "WARNING: Skipping clean up installation"
  fi;
fi;

# Clean up.
if [[ $CLEAN_UP_INSTALLATION ]]; then
  echo "Cleaning up installation..."
  DIRS="/usr/lib/gcc /app/tmp.pypoetry /tmp/*"
  echo "Cleaning up installation... done"
  du -hs $DIRS | sort -h
  rm -rf $DIRS
else
  echo "WARNING: Skipping clean up installation"
fi;

echo "# Disk space before $0"
report_disk_usage
