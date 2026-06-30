---
description: Summarize a markdown text, keeping the same header structure
model: sonnet
---

- The user will pass:
  - Text `<INPUT>`
  - A number of words `<NUM_WORDS>`
  - Max level of header `<MAX_HEADER_LEV>`

# Read Content
- Read the file `<INPUT>` passed by the user

# Summarize Content in Bullet Points
- Write a summary in bullet points of `<INPUT>` using the rules in:
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

# Keep the Structure

### No Header Structure
- If there is no structure (i.e., the passed text is just a chunk of text) then
  do not use any headers

### No `<MAX_HEADER_LEV>`
- If there is a structure, use the same structure of the chapter and subchapter
  in markdown headers, if the user has not specified `<MAX_HEADER_LEV>`
  - Use numbers of chapter (e.g., 1.) and subchapters (e.g., 1.1)

- An example of the output is:
  ```
  # 1. Hello

  ## 1.1. Hello world

  - Point
    - Subpoint
    - Subpoint
  - Point

  ## 1.2. Good bye world

  # 2. Hello again
  ```

### Use `<MAX_HEADER_LEV>`
- If the user specifies a `<MAX_HEADER_LEV>`, then keep only the structure of
  the paper that has header level lower than `<MAX_HEADER_LEV>`

- For instance if `<MAX_HEADER_LEV>` = 1, then all the text in H1 header needs
  to be summarized, and the output is like:
  ```
  # 1. Hello

  - Point
    - Subpoint
    - Subpoint
  - Point

  # 2. Hello again
  ```

# Styling
- Use nested bullet points
- Use Latex formulas

# Length
- Target the length of the entire output to be around `<NUM_WORDS>`

# Write Output
- Write the result in the passed file `<output>`
  - If not specified use `summary.md` in the current directory as `<output>`
- Print on screen the path of the file as
  ```
  # Summary file: <output>
  ```

# Run Lint
- Run
  ```
  > $(find /Users/saggese/src/notes1 -name "lint_txt.py") -i <output>
  ```

# Answer Follow-up Questions
- Do not do anything else, but wait for the user to ask questions
- Answer any questions the user asks about the content just read, referencing
  specific sections or concepts from the chapter summary
