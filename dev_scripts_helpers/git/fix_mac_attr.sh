#!/bin/bash -e

# """
# Find files carrying the macOS Docker xattr that breaks `docker build`
# (e.g., `lsetxattr ...: xattr "com.docker.grpcfuse.ownership": operation
# not supported`) and clear extended attributes only on those files,
# instead of scanning / touching every file in the repo.
#
# Usage:
# > fix_mac_attr.sh [attr_name]
# """

ATTR=${1:-com.docker.grpcfuse.ownership}

echo "Looking for files with xattr '$ATTR' ..."
FILES=$(find . -type f -print0 | xargs -0 xattr -l 2>/dev/null | \
    sed -n "s/^\(.*\): $ATTR:.*/\1/p" | sort -u)

if [[ -z "$FILES" ]]; then
    echo "No files found with xattr '$ATTR'"
    exit 0
fi;

NUM_FILES=$(echo "$FILES" | wc -l | xargs)
echo "Found $NUM_FILES file(s) with xattr '$ATTR':"
echo "$FILES" | sed 's/^/  /'

echo "Fixing files ..."
echo "$FILES" | tr '\n' '\0' | xargs -0 xattr -c
echo "Done"
