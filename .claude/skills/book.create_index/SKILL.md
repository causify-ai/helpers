---
description: Create a markdown file from a PDF book together with its table of content
---

- Given a file $FILE in PDF or markdown

$DST_DIR=/Users/saggese/src/notes1/books

## Step 1: Convert to Markdown, if needed

- If the file is still a PDF use the script
  > convert_pdf_to_md.py
  to convert it into markdown and save it to $DST_DIR

## Step 2: Create index

- Given the markdown file $DST_DIR/XYZ.md

- Create a table of content with chapters and subchapters, together with the line
  in the $DST_DIR/XYZ.md where the chapter / subchapter starts
- Save the file $DST_DIR/XYZ.index.md with the list of chapters / subchapters and
  the line where they start in the markdown file
  - The output is like a markdown file with nested bullets
    ```
    ## Chapter 1: Introduction to Causal Inference (Line 750)

    ### Subsections
    - Machine Learning and Causal Inference (line 752)
    - Association and Causation (line 795)
    - The Fundamental Problem of Causal Inference (line 906)
    - Causal Models (line 938)
    - The Independence Assumption (line 1621)
    ```
