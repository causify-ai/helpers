#!/bin/bash -e

echo "CK_GIT_ROOT_PATH=$CK_GIT_ROOT_PATH"

if [[ ! -d $CK_GIT_ROOT_PATH ]]; then
    echo "ERROR: Can't find the root dir $CK_GIT_ROOT_PATH"
    exit -1
fi;

sudo chown -R $(whoami):$(whoami) $CK_GIT_ROOT_PATH
