Given a file passed on the command line, you must improve its appearance without
changing its behavior

- For a file containing Python code apply the rules from
  `@.claude/skills/coding.format_rules/SKILL.md`

- For a file storing unit tests (i.e., whose base name starts with `test_.py`)
  apply the rules from `@.claude/skills/testing.format_rules/SKILL.md`

- For a markdown or text file apply the rules in
  `@.claude/skills/markdown.format_rules/SKILL.md`

- For a blog (e.g., a markdown in the dir `website/docs/blog/posts`) apply the
  rules in `@.claude/skills/blog.format_rules/SKILL.md`

- For Jupyter notebook apply the rules from
  `@.claude/skills/notebook.format_rules/SKILL.md` and then run jupytext sync
