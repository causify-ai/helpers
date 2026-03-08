---
description: Create a markdown file from a PDF book together with its table of content
---

Given a file $FILE and a $CHAPTER to read

/Users/saggese/src/notes1/books/2023.Facure.Causal_Inference.md

$DST_DIR=/Users/saggese/src/notes1/books

## Step 1: Convert to Markdown, if needed

If the file is PDF use 
convert_pdf_to_md.sh

to convert it into 

## Step 2: Create index

Create a table of content from
$DST_DIR/XYZ.md
$DST_DIR/XYZ.index.md with a list of chapters to the line where they start in the
markdown file

Save the results in $DST_DIR

## Step 3: W


