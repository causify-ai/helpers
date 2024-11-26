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

APT_GET_OPTS="-y --no-install-recommends"

# - Install sudo.
apt-get install $APT_GET_OPTS sudo

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

# - Install AWS CLI V2.
if [[ 1 == 1 ]]; then
  # For more info see https://docs.aws.amazon.com/cli/latest/userguide/getting-started-version.html.
  # Changelog: https://raw.githubusercontent.com/aws/aws-cli/v2/CHANGELOG.rst.
  apt-get install $APT_GET_OPTS ca-certificates unzip curl
  # Get the latest version of AWS CLI based on the architecture.
  ARCH=$(uname -m)
  echo "ARCH=$ARCH"
  if [[ $ARCH == "x86_64" ]]; then
      echo "Installing AWS CLI V2 for x86_64(Linux) architecture"
      curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  elif [[ $ARCH == "aarch64" ]]; then
      echo "Installing AWS CLI V2 for aarch64(Mac) architecture"
      curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
  else
      echo "Unknown architecture $ARCH"
      exit 1
  fi;
  unzip awscliv2.zip
  rm awscliv2.zip
  ./aws/install
  echo "AWS_CLI VERSION="$(aws --version)
fi;

## - Install Github CLI.
if [[ 1 == 1 ]]; then
  apt-get install $APT_GET_OPTS wget
  sudo mkdir -p -m 755 /etc/apt/keyrings
  wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null
  sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
  sudo apt update
  sudo apt install gh -y
  echo "GH VERSION="$(gh --version)
fi;

# - Install graphviz.
if [[ 1 == 1 ]]; then
  # This is needed to install pygraphviz.
  # See https://github.com/alphamatic/amp/issues/1311.
  # It needs tzdata so it needs to go after installing tzdata.
  apt-get install $APT_GET_OPTS libgraphviz-dev
  # This is needed to install dot.
  apt-get install $APT_GET_OPTS graphviz
fi;

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
