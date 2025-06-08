#!/bin/bash -xe
export GIT_ROOT=$(pwd)
if [[ -z $GIT_ROOT ]]; then
    echo "Can't find GIT_ROOT=$GIT_ROOT"
    exit -1
fi;
FILE_NAME=$GIT_ROOT/papers/arxiv_template/template.tex

lint_notes.py -i $FILE_NAME --use_dockerized_prettier
