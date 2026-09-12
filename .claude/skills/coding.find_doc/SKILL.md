---
description: Find and summarize documentation for a dir, file, class, or function
model: haiku
---

- Given the passed object (e.g., dir, file, class, function)
  - Find the files containing the documentation for that specific object
  - Print a short summary of the documentation in 3 bullet points of less than
    200 words using the style of `.claude/skills/text.rules.md`

# Verification
- [ ] Confirm the documentation found matches the passed object
- [ ] Confirm the summary has exactly 3 bullet points under 200 words
