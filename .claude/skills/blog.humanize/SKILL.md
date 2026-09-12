---
description: Humanize the text of a blog post
model: haiku
---

# Goal
- Humanize the text of a blog post

# Workflow

## Run the Humanize Skill
- Run the skill `/text.humanize` on the blog text
- Use "I" if there is a single author of the blog
- Use "we" if there are multiple authors of the blog

## Format
- At the end, format the text with
  ```bash
  > website/format_blog.sh <FILE>
  ```

# Constraints
- Follow the rules in `.claude/skills/blog.rules.md`
- Do not change the format (e.g., in terms of markdown headers) or content
