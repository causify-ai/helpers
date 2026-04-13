#!/bin/bash -e
#GIT_ROOT="/Users/saggese/src/cmamp1"
export GIT_ROOT=$(pwd)
if [[ -z $GIT_ROOT ]]; then
    echo "Can't find GIT_ROOT=$GIT_ROOT"
    exit -1
fi;

PAPER_DIR=$(dirname $0)
echo "PAPER_DIR=$PAPER_DIR"

FILE_NAME=$PAPER_DIR/paper.tex
TARGET_DIR=arxiv

if [[ -d $TARGET_DIR ]]; then
    rm -r $TARGET_DIR
fi

mkdir $TARGET_DIR
cp -r $GIT_ROOT/$PAPER_DIR/figs $TARGET_DIR
cp -r $PAPER_DIR/*.tex $TARGET_DIR
cp -r $PAPER_DIR/references.bib $TARGET_DIR
cp $FILE_NAME $TARGET_DIR

mkdir -p $TARGET_DIR/helpers_root/dev_scripts_helpers/documentation/
cp helpers_root/dev_scripts_helpers/documentation/latex_abbrevs.sty $TARGET_DIR/helpers_root/dev_scripts_helpers/documentation

mkdir -p $TARGET_DIR/papers/template
cp papers/template/style.tex $TARGET_DIR/papers/template

(cd $TARGET_DIR; tar czf ../arxiv.tgz .)

# Check the archive.
echo "arxiv.tgz"
tar tzfv arxiv.tgz
