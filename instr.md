Create a Python script clean_markdown.py to clean up HTML markup in markdown
files

--input

--output

# Step 1
Read --input file

# Step 2
Remove span tags with multiple attributes (remove entire tag, not just content):
Example: `<span id="ch01.html_id388" contenteditable="false" primary="association" secondary="definition of association" data-type="indexterm"></span>`
These have complex attribute structures and should be completely removed.

# Step 3
Remove only `class="label"` span tags but keep their content:
Example: `<span class="label">Part I. </span>` -> `Part I. `

# Output
Write in the output file

# Requirements
- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications

- When writing code you must always follow the instructions in
  `@.claude/skills/coding.rules.md`
