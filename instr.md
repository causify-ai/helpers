Create a script called lint_cc.py that accepts a list of files and calls
claude code with a prompt referring to the proper files

Read .claude/rules.md and create a mapping from file type to rules to use

> ls .claude/skills/*lint*/SKILL.md
.claude/skills/lint.check/SKILL.md
.claude/skills/notebook.lint/SKILL.md

> ls -1 .claude/skills/*format*/SKILL.md
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
