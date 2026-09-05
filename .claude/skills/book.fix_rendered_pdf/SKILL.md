---
description: Make sure that the PDF rendered from a Typst file looks good
model: haiku
---

# Goal

- Make sure that the book chapter from `<TYP_FILE>` compiles and the PDF looks good

# Inputs

- `<TYP_FILE>`: Typst file
  - E.g., `msml610/book/Lesson01.2-AI_and_Machine_Learning.typ`

# Workflow

## Step 1: Generate the PDF

- Create the PDF from the `<TYP_FILE>`

  ```bash
  > run_typst.py -i <TYP_FILE>
  ```

- The generated file is in the same dir as `<TYP_FILE>`
  - E.g., `msml610/book/Lesson01.2-AI_and_Machine_Learning.pdf`

## Step 2: Check the Typst Source Code

- Make sure the Typst file follows the rules in `.claude/skills/typst.rules.md` and
  `.claude/templates/typst.template.typ`

## Step 3: Check the PDF

- Read the generated PDF `<PDF_FILE>` and for each page make sure the layout looks
  good, e.g.,
  - The figures are readable and not too small
  - There is no excessive space around the figure due to poorly wrapping text
- If there are visual problems, change the Typst file without changing the text and
  re-run Step 1 until the PDF looks good