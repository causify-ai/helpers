#!/bin/bash -e
DIR="$HOME/src/venv/mkdocs"
if [ -d $DIR ]; then
    echo "$DIR already exists: skipping"
else
    python3 -m venv $DIR
    source $DIR/bin/activate
    pip install mkdocs-material mkdocs-shadcn mkdocs-graphviz
    # Patch shadcn bug: katex_options=None causes AttributeError when pymdownx.arithmatex is enabled.
    # config.theme.get("katex_options", {}) returns None (not {}) because the key exists explicitly.
    KATEX=$DIR/lib/python3.*/site-packages/shadcn/plugins/mixins/katex.py
    sed -i.bak 's/config\.theme\.get("katex_options", {})/(config.theme.get("katex_options") or {})/' $KATEX
fi;

echo "Run: 'source $DIR/bin/activate' to activate"
