---
description: Summarize a markdown text
model: haiku
---

# Summarize Content in Bullet Points

- Write a summary in bullet points using the rules in
  `.claude/skills/text.rules.bullet_points.md`

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

- Write the result in the file `<output>` called `summary.md` in the current
  directory
- Print on screen the path of the file as
  ```
  # Summary file: <output>
  ```

# Run lint
- Run
  ```
  > $(find /Users/saggese/src/notes1 -name "lint_txt.py") -i <output>
  ```

# Answer Follow-up Questions

- Do not do anything else, but wait for the user to ask questions
- Answer any questions the user asks about the content just read, referencing
  specific sections or concepts from the chapter summary
