#!/bin/bash
#
# Open a markdown filename on GitHub.
#

# TODO(gp): Convert to an invoke.

# Check if a file name is passed as an argument.
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <filename>"
    exit 1
fi

# The filename is expected to be the first argument.
FILE_PATH=$1

# Check if the file exists.
if [ ! -f "$FILE_PATH" ]; then
    echo "Error: File '$filename' not found."
    exit 1
fi

# git@github.com:causify-ai/helpers.git
REPO_URL=$(git remote get-url origin | sed -e 's/.git$//' -e 's/git@github.com:/https:\/\/github.com\//')
BRANCH_NAME=$(git branch --show-current)

url="${REPO_URL}/blob/${BRANCH_NAME}/${FILE_PATH}"
echo "$url"

open $url
