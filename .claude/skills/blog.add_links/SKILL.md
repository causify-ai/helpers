---
description: Add internal and external links to the passed blog
---

# Goal
- Add internal and external links to the passed blog

# Step 1: Collect Material

- Read the passed blog text `<BLOG_FILE>` and the other blogs in `<BLOG_DIR>`
  `website/docs/blog/posts/*.md`
  (both published ones and drafts)

# Step 2: Add Internal Links
- Find which parts of the blog `<BLOG_FILE>` can point to the other blogs and add
  references to each other

# Step 3: Add External Links
- Find references to the content of the blog `<BLOG_FILE>` that are meaningful
  and expand on it by adding more links

# Constrains
- Make sure to follow rules from `.claude/skills/blog.rules.md`
- Do not change the content of the blog, but only add links

# Step 4: Format
- At the very hand, format the text with
  ```
  > website/format_blog.sh $FILE
  ```
