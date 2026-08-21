---
description: Incorporate content into other material (such as books, slides, papers, blog ideas)
model: sonnet
---

# Goal
Given the content `<CONTENT>` passed by the user propose where to include it in the
referred book / slides / blogs `<TARGET>`

# Workflow
- Read the proposed content `<CONTENT>`

- For a book / course (e.g., `book_springer/map.md`) , read the `map.md` to
  understand the structure of the material covered
- Find out which part of the `<TARGET>` material, the content is relevant for

- Propose how to integrate the `<CONTENT>` in `<TARGET>` using bullet points
  following `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
