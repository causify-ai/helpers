#!/bin/bash -xe
#GIT_ROOT="/Users/saggese/src/cmamp1"
export GIT_ROOT=$(pwd)
if [[ -z $GIT_ROOT ]]; then
    echo "Can't find GIT_ROOT=$GIT_ROOT"
    exit -1
fi;

PWD=$(pwd)

cd $GIT_ROOT/papers/Causify_development_system

FILE_NAME=Causify_dev_system.tex

PDF_FILE_NAME=$(basename $FILE_NAME).pdf

dockerized_latex.py -i ${FILE_NAME} -o $PDF_FILE_NAME
dockerized_latex.py -i ${FILE_NAME} -o $PDF_FILE_NAME

# From open_file_cmd.sh
/usr/bin/osascript << EOF
set theFile to POSIX file "$PDF_FILE_NAME" as alias
tell application "Skim"
activate
set theDocs to get documents whose path is (get POSIX path of theFile)
if (count of theDocs) > 0 then revert theDocs
open theFile
end tell
EOF

cd $PWD
