---
description: Extract and summarize specific chapters from a book
model: haiku
---

Given a markdown book ${input}.${extension} and an output file ${output}.md

# Step 1: Extract the Markdown

- If the file is epub, convert ${input}.epub to tmp.md

  ```bash
  > pandoc ${input}.epub -t gfm \
      --extract-media=media \
      --wrap=none \
      --markdown-headings=atx \
      -o tmp.md
  ```

- If the file is PDF convert IN.pdf to tmp.md

  ```bash
  > convert_pdf_to_md.py --input ${input}.pdf --output tmp.md
  ```

- If the file is already markdown, don't to anything

# Step 2: Extract the Index

- Extract the index in terms of Chapters and Subchapters from the markdown
  - Print the index in markdown

# Step 3: Summarize Content

- Write a summary using the same structure of the chapter and subchapter in
  markdown headers
- Use numbers of chapter (e.g., 1.) and subchapters (e.g., 1.1)
- Use the chapter numbers that come from the book

For each chapter and subchapter:
- Create 4-5 bullet points capturing the main ideas
- Use nested markdown bullets with maximal clarity and fewer words
- Use Latex notation for formulas
- Avoid non-ASCII symbols

- An example is like
  ```
  # 1. Hello

  ## 1.1. Hello world

  - Point
    - Subpoint
    - Subpoint
  - Pont

  ## 1.2. Good bye world

  # 2. Hello again
  ```

# Step 4: Write Output

- Write the result in the file {output}.md
