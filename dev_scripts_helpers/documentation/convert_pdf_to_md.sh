#!/bin/bash -xe
EXEC='/Applications/calibre.app/Contents/MacOS/ebook-convert'
SRC_FILE='/Users/saggese/Library/CloudStorage/GoogleDrive-saggese@gmail.com/My Drive/books/Math - Bayesian methods/2023 - Facure - Causal Inference in Python_ Applying Causal Inference in the Tech Industry.pdf'
DST_FILE1="paper.epub"
DST_FILE2="paper.md"

"$EXEC" "$SRC_FILE" "$DST_FILE1" --enable-heuristics --chapter "//*[name()='h1' or name()='h2']"

pandoc $DST_FILE1 \
  --to gfm \
  --wrap=none \
  --extract-media=images \
  -o $DST_FILE2
