#!/bin/bash -xe
export GIT_ROOT=$(pwd)
if [[ -z $GIT_ROOT ]]; then
    echo "Can't find GIT_ROOT=$GIT_ROOT"
    exit -1
fi;
FILE_NAME=$GIT_ROOT/papers/KaizenFlow/kaizen_flow.paper.tex

dev_scripts/latex/lint_latex.sh $FILE_NAME
