#!/bin/bash -xe
export GIT_ROOT=$(pwd)
if [[ -z $GIT_ROOT ]]; then
    echo "Can't find GIT_ROOT=$GIT_ROOT"
    exit -1
fi;

#SCRIPT_SOURCE="${BASH_SOURCE[0]}"
#while [ -h "$SCRIPT_SOURCE" ]; do
#  DIR="$(cd -P "$(dirname "$SCRIPT_SOURCE")" && pwd)"
#  SCRIPT_SOURCE="$(readlink "$SCRIPT_SOURCE")"
#  [[ $SCRIPT_SOURCE != /* ]] && SCRIPT_SOURCE="$DIR/$SCRIPT_SOURCE"
#done
#SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_SOURCE")" && pwd)"
SCRIPT_SOURCE=$0
SCRIPT_DIR=$(dirname $SCRIPT_SOURCE)

for FILE in $SCRIPT_DIR/*.tex; do
    echo "Processing $FILE"
    lint_txt.py -i "$FILE" --use_dockerized_prettier
done
