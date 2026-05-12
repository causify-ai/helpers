- Write a Python script to convert epub to markdown 
  ./dev_scripts_helpers/documentation/convert_epub_to_md.py

- The interface is similar to ./dev_scripts_helpers/documentation/convert_pdf_to_md.py

- Use a logic similar to 
pandoc <input> \
  --to=gfm \
  --wrap=none \
  --extract-media=images \
  -o <output>.md

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a plan.md with 5 bullet points explaining
    what the plan is

- When writing code you must always follow the instructions in
  `@.claude/skills/coding.rules.md`

- Generate unit tests for the new code following the instructions in
  `@.claude/skills/testing.rules.md`
