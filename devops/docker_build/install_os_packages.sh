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

# - Install poetry.
pip3 install poetry --break-system-packages
echo "POETRY VERSION="$(poetry --version)

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
    echo "Cleaning up installation... done"
else
    echo "WARNING: Skipping clean up installation"
fi;

# After clean up.
echo "# Disk space after $0"
report_disk_usage
