- Given a file passed on the command line, you must improve its appearance
  without changing its behavior

# Rules

- For Python file (e.g., with a `.py` extension) apply the rules from
  `.claude/skills/coding.format/SKILL.md`

- For a file storing unit tests (i.e., whose base name starts with
  `test/test_<file>.py`) apply the rules from
  `.claude/skills/testing.format/SKILL.md`

- For a markdown or text file apply the rules in
  `@.claude/skills/markdown.format/SKILL.md`

- For a blog (e.g., a markdown in the dir `website/docs/blog/posts`) apply the
  rules in `@.claude/skills/blog.format/SKILL.md`

- For Jupyter notebook apply the rules from
  `@.claude/skills/notebook.format/SKILL.md` and then run Jupytext sync
