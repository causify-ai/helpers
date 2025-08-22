#!/bin/bash -e
DIR="$HOME/src/venv/mkdocs"
if [ -d $DIR ]; then
    echo "$DIR already exists: skipping"
else
    python3 -m venv $DIR
    source $DIR/bin/activate
    pip install mkdocs-material
fi;

echo "Run: 'source $DIR/bin/activate' to activate"
