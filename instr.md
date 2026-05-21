In linters2/lint_cc.py 

Implement the TODO(ai_gp)

The prompt is built based on the type of files to process

create a mapping from file type to rules, template files, to use for each type of file

For notebooks
- The rule files are
  `.claude/skills/notebook.rules.md`
  `.claude/skills/interactive_notebook.rules.md
- The templates are
    - `.claude/templates/interactive_notebook.template.py`
    -`.claude/templates/interactive_notebook_utils_template.py`

For blog
- `.claude/skills/blog.rules.md`: for blog formatting rules
- `.claude/skills/markdown.rules.md`: for markdown formatting rules
- `.claude/skills/text.rules.bullet_points.md`: for formatting rules of text in
  bullet points

For python code
- Format the Python files according to the rules in
  `@.claude/skills/coding.rules.md`


Complete the mapping reading the files

# Step 1
Read .claude/rules.md

# Step 2
Read the files
.claude/skills/notebook.lint/SKILL.md
.claude/skills/bash.format/SKILL.md
.claude/skills/blog.format/SKILL.md
.claude/skills/coding.format/SKILL.md
.claude/skills/cxo_slides.format/SKILL.md
.claude/skills/interactive_notebook.format/SKILL.md
.claude/skills/markdown.format/SKILL.md
.claude/skills/notebook.format/SKILL.md
.claude/skills/skill.format/SKILL.md
.claude/skills/slides.format/SKILL.md
.claude/skills/testing.format/SKILL.md
.claude/skills/tool_X_in_30_mins.format/SKILL.md
.claude/skills/tool_X_in_60_mins.format/SKILL.md

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications

- When writing code you must always follow the instructions in
  `@.claude/skills/coding.rules.md`
