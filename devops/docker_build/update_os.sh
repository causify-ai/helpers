#!/usr/bin/env bash
#
# Update OS.
#

echo "#############################################################################"
echo "##> $0"
echo "#############################################################################"

set -ex

source utils.sh

echo "# Disk space before $0"
report_disk_usage

# Update the package listing, so we know what package exist.
apt-get update

# - Install security updates.
apt-get -y upgrade

# After clean up.
echo "# Disk space after $0"
report_disk_usage