---
description: Add internal and external links to the passed blog
model: haiku
---

# Goal
- Add internal and external links to the passed blog

# Workflow

## Collect Material

- Read the passed blog text `<BLOG_FILE>` and the other blogs in `<BLOG_DIR>`
  `website/docs/blog/posts/*.md`
  (both published ones and drafts)

## Add Internal Links
- Find which parts of the blog `<BLOG_FILE>` can point to the other blogs and add
  references to each other

## Add External Links
- Find references to the content of the blog `<BLOG_FILE>` that are meaningful
  and expand on it by adding more links

## Format
- At the end, format the text with
  ```bash
  > website/format_blog.sh <BLOG_FILE>
  ```

# Constraints
- Make sure to follow rules from `.claude/skills/blog.rules.md`
- Do not change the content of the blog, but only add links

# Verification
- [ ] Confirm every added link resolves to an existing blog post or a valid
      external URL
- [ ] Confirm no existing wording was changed, only links added
- [ ] Confirm `website/format_blog.sh` ran without errors
