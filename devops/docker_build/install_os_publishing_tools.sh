#!/usr/bin/env bash

set -ex

FILE_NAME="devops/docker_build/install_publishing_tools.sh"
echo "##> $FILE_NAME"

APT_GET_OPTS="-y --no-install-recommends"

# Update since sometimes it throws `404 Not Found` error, see
# `https://askubuntu.com/questions/1159096/ubuntu-18-04-throws-404-error-while-fetching-dependencies`.
apt-get update

# Install plantuml.
# Create necessary dir to install plantuml.
if [[ ! -d /usr/share/man/man1/ ]]; then
    mkdir /usr/share/man/man1/
fi;
apt-get install $APT_GET_OPTS plantuml

# Install `nodejs` which is required for `prettier`.
# `https://github.com/nodesource/distributions#ubuntu-versions`
mkdir -p /etc/apt/keyrings
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
NODE_MAJOR=20
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list
apt-get update && apt-get install -y nodejs
# Install Prettier.
npm install -g prettier
# Install `markdown-toc` to generate the table of contents in the
# markdown files.
npm install -g markdown-toc
