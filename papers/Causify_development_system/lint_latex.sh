#!/bin/bash -xe
export GIT_ROOT=$(pwd)
if [[ -z $GIT_ROOT ]]; then
    echo "Can't find GIT_ROOT=$GIT_ROOT"
    exit -1
fi;
FILE_NAME=$GIT_ROOT/papers/Causify_development_system/Causify_dev_system.tex

lint_txt.py -i $FILE_NAME --use_dockerized_prettier
