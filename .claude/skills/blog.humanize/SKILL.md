---
description: Humanize the text of a blog post
---

## Run skill
- Run the skill `/text.humanize` on the blog text

- Use "I" if there is a single author of the blog
- Use "we" if there are multiple authors of the blog

## Constraints
- Follow the rules in `.claude/skills/blog.rules.md`
- Do not change the format (e.g., in terms of markdown headers) or content

## Format

- At the very hand, format the text with
  ```
  > website/format_blog.sh $FILE
  ```
