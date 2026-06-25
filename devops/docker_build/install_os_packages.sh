#!/usr/bin/env bash
#
# Install OS level packages.
#

echo "#############################################################################"
echo "##> $0"
echo "#############################################################################"

set -ex

source utils.sh

echo "# Disk space before $0"
report_disk_usage

DEBIAN_FRONTEND=noninteractive

export APT_GET_OPTS="-y --no-install-recommends"

# - Install sudo, curl, gnupg.
apt-get install $APT_GET_OPTS sudo curl gnupg

# - Install Python3 toolchain.
apt-get $APT_GET_OPTS install python3 python3-pip python3-venv
echo "PYTHON VERSION="$(python3 --version)
echo "PIP VERSION="$(pip3 --version)

# - Verify the installed Python matches the pin in `repo_config.yaml`.
# The pin is the single source of truth; if it diverges from what the base
# image ships, the build must surface that explicitly rather than silently
# drift. `PINNED_PYTHON_VERSION` is passed in as a build arg from
# `dev.Dockerfile` (which reads it from `repo_config.yaml`).
if [[ -n "${PINNED_PYTHON_VERSION:-}" ]]; then
  ACTUAL_PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  echo "PINNED_PYTHON_VERSION=${PINNED_PYTHON_VERSION}"
  echo "ACTUAL_PYTHON_VERSION=${ACTUAL_PYTHON_VERSION}"
  if [[ "${ACTUAL_PYTHON_VERSION}" != "${PINNED_PYTHON_VERSION}" ]]; then
    echo "ERROR: Python version mismatch: base image installed ${ACTUAL_PYTHON_VERSION} but repo_config.yaml pins ${PINNED_PYTHON_VERSION}"
    echo "       Either bump the base image (FROM ubuntu:...) or update python_info.python_version."
    exit 1
  fi
else
  echo "WARNING: PINNED_PYTHON_VERSION build arg not provided; skipping pin check"
fi

# - Install poetry.
# Poetry remains supported as the long-standing dependency manager for the
# dev container; see `install_python_packages.sh` and the BUILD_TOOL arg
# in `dev.Dockerfile` for choosing between Poetry and uv at build time.
pip3 install poetry --break-system-packages
echo "POETRY VERSION="$(poetry --version)

# - Install uv.
# `uv` is the new default thin-env builder (HelpersTask8928); also keep it
# in the container so the BUILD_TOOL=uv path in `install_python_packages.sh`
# works.
pip3 install uv --break-system-packages
echo "UV VERSION="$(uv --version)

# - Install gcc and build tools.
if [[ 0 == 1 ]]; then
  apt-get install $APT_GET_OPTS build-essential
fi;

# - Install Git.
if [[ 1 == 1 ]]; then
  # To update Git to latest version after `2.25.1`.
  # https://www.linuxcapable.com/how-to-install-and-update-latest-git-on-ubuntu-20-04/
  # sudo add-apt-repository ppa:git-core/ppa -y
  apt-get install $APT_GET_OPTS git
fi;

# We need `ip` to test Docker for running in privileged mode.
# See AmpTask2200 "Update tests after pandas update".
# apt-get install $APT_GET_OPTS iproute2

# - Install vim.
if [[ 1 == 1 ]]; then
  apt-get install $APT_GET_OPTS vim
fi;

# - Install optional packages.
DEPENDENCIES_FILE="os_packages/os_packages.txt"

# Check if the file exists.
if [[ ! -f "$DEPENDENCIES_FILE" ]]; then
    echo "Dependencies file not found: $DEPENDENCIES_FILE"
    exit 1
fi

# Read the file line by line and run each script.
while IFS= read -r script_file || [[ -n "$script_file" ]]; do
    # Skip empty lines or lines starting with #.
    [[ -z "$script_file" || "$script_file" =~ ^# ]] && continue
    echo "Running $script_file ..."
    if [[ -x "$INSTALL_DIR/os_packages/$script_file" ]]; then
        bash "$INSTALL_DIR/os_packages/$script_file"
    else
        echo "Warning: $INSTALL_DIR/os_packages/$script_file is not executable or not found."
    fi
done < "$DEPENDENCIES_FILE"

# Some tools refer to `python` and `pip`, so we create symlinks.
if [[ ! -e /usr/bin/python ]]; then
  ln -s /usr/bin/python3 /usr/bin/python
fi;
if [[ ! -e /usr/bin/pip ]]; then
  ln -s /usr/bin/pip3 /usr/bin/pip
fi;

# Before clean up.
echo "# Disk space before clean up"
report_disk_usage

# Clean up.
if [[ $CLEAN_UP_INSTALLATION ]]; then
    echo "Cleaning up installation..."
    apt-get purge -y --auto-remove
    rm -rf $INSTALL_DIR/aws
    echo "Cleaning up installation... done"
else
    echo "WARNING: Skipping clean up installation"
fi;

# After clean up.
echo "# Disk space after $0"
report_disk_usage
