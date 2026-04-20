---
description: Extract and summarize specific chapters from a book or a paper
model: haiku
---

Given a document `<input>.<extension>` and an output file `<output>.md`
- Convert the document into Markdown
- Extract chapters from a markdown-based book file
- Summarize their content
- Answer questions about the material

# Extract the Markdown, if needed

- If the passed file `<input>` doesn't have the `.md` extension and is not
  markdown convert it to Markdown as in the follow

1. If the file is `epub`, convert `<input>.epub` to a file `tmp.md` in the current
   dir

  ```bash
  > pandoc <input>.epub -t gfm \
      --extract-media=media \
      --wrap=none \
      --markdown-headings=atx \
      -o tmp.md
  ```

2. If the file is PDF convert `<input>.pdf` to `tmp.md` in the current dir

  ```bash
  > pdf_to_md.py --input <input>.pdf --output tmp.md
  ```

3. If the file is already markdown, don't to anything but use the markdown file
   directly

# Extract the Index

- Given a book markdown file find the corresponding index file `<index_file>` by
  appending `.index.md` to the book filename
  - E.g., for
    `/Users/saggese/src/notes1/books/2023.Facure.Causal_Inference.md`
    the expected index file is
    `/Users/saggese/src/notes1/books/2023.Facure.Causal_Inference.index.md`

- Print the name of the expected index as
  ```
  # Expected index: <index_file>
  ```

- If the index is not present 
  - Print "WARNING: Index not existing creating <index file>`
  - Run the skill `/book.create_index` to generate it like
  ```
  /book.create_index <input>
  ```

- The index file contains a table of contents that maps chapter titles to line
  numbers in the book markdown file
- Extract the index in terms of Chapters and Subchapters from the markdown
  - Print the index in markdown

# Identify Requested Chapters

- Search the index for chapters matching the user's request by:
  - Exact chapter name match (case-insensitive)
  - Chapter number if applicable
  - Partial name matching if exact match not found

- Report which chapters will be read using nested markdown bullets showing the
  chapter hierarchy (chapters and subchapters)

- Write a structure of the chapter and subchapter in markdown headers
  - Use numbers of chapter (e.g., 1.) and subchapters (e.g., 1.1)
  - Use the chapter numbers that come from the book

# Summarize Content in Bullet Points

- Write a summary in bullet points using the rules in `.claude/skills/text.rules.bullet_points.md`

- Use the same structure of the chapter and subchapter in markdown headers
  - Use numbers of chapter (e.g., 1.) and subchapters (e.g., 1.1)
  - Use the chapter numbers that come from the book

- An example of the output is
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

# Write Output

- Write the result in the file `<output>.md` in the current directory
- Print on screen the path of the file as
  ```
  # Summary file: <output>.md
  ```

# Run lint
- Run `lint_txt.py -i <output>.md`

# Answer Follow-up Questions

- Do not do anything else, but wait for the user to ask questions
- Answer any questions the user asks about the content just read, referencing
  specific sections or concepts from the chapter summary
