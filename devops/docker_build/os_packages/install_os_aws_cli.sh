#!/usr/bin/env bash
#
# Install AWS CLI.
#
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
echo "Installing AWS CLI V2 for aarch64(Linux) architecture"
curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
else
echo "Unknown architecture $ARCH"
exit 1
fi;
unzip awscliv2.zip
rm awscliv2.zip
./aws/install
echo "AWS_CLI VERSION="$(aws --version)
