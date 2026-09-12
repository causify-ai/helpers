---
description: Improve blog text from some basic content
model: haiku
---

# Goal
- Use the passed text to write a blog

# Workflow

## Read and Follow the Rules to Write a Blog
- Read context about rules from `.claude/skills/blog.rules.md`

- When writing follow the rules from:
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

## Improve the Text

## Add Visuals
- Add visuals following instructions from
  `.claude/skills/blog.add_visuals/SKILL.md`

## Format
- At the end, format the text with
  ```bash
  > website/format_blog.sh <FILE>
  ```

# Verification
- [ ] Confirm the blog follows `.claude/skills/blog.rules.md`
- [ ] Confirm `website/format_blog.sh` ran without errors
