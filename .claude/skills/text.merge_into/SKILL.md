---
description: Move content from a file into another one without redundancy
model: haiku
---

# Goal

- You are an expert technical writer
- Given a source file `<SRC_FILE>` and a destination file `<DST_FILE>`, you
  will move and merge the content of `<SRC_FILE>` into `<DST_FILE>` following
  conventions in
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

# Workflow

- Move the chunks of text from `<SRC_FILE>` that can be added into `<DST_FILE>`
  without introducing redundancy
  - Add them to the right place in terms of headers in `<DST_FILE>` and following
    the style and the rules of the `<DST_FILE>`
  - When you move chunks you must delete them from `<SRC_FILE>`
- Remove the chunks from `<SRC_FILE>` that are redundant with the content of
  `<DST_FILE>`
- Leave in `<SRC_FILE>` only text can't be moved since it doesn't apply to
  `<DST_FILE>`
