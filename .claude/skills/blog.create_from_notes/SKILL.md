---
description: Improve blog text from some basic content
model: haiku
---

# Goal
- Improve the passed text for a blog

# Step 1: Read and Follow the Rules from Context
- Read context about rules from `.claude/skills/blog.rules.md`

- When writing follow the rules from:
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

# Step 2: Improve the Text
- Improve the text by following the formatting
- Propose ideas that can sound interesting, relevant, and appropriate for the
  blog
- If the text is just a set of ideas and commands, convert them into a
  meaningful blog
- Add examples and references that you are sure about it

# Step 3: Format
- At the very hand, format the text with
  ```
  > website/format_blog.sh $FILE
  ```
