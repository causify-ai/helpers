---
description: Incorporate content into other material (books, slides, papers, blog ideas)
model: sonnet
---

# Goal
- The user passes, in this order:
  1. the content `<CONTENT>` to incorporate
  2. the target `<TARGET>`: a file (e.g., a book, slides, paper, blog) or a
     reference to a part of a file (e.g., a chapter, section, slide number)
- Propose where and how to include `<CONTENT>` in `<TARGET>`

# Workflow
- Read the proposed content `<CONTENT>`

- Resolve `<TARGET>`
  - If `<TARGET>` is a reference to a part of a file (e.g., "chapter 3",
    "slide 12"), open that file and jump to that part
  - If `<TARGET>` is a whole file and it belongs to a book / course (e.g.,
    `book_springer/map.md`), read the `map.md` to understand the structure of
    the material covered
- Find out which part of `<TARGET>` the content is relevant for
  - If more than one location is plausible, or no location fits well, STOP
    and ask the user to clarify where to add the content instead of guessing
- Propose how to integrate the `<CONTENT>` in `<TARGET>` using bullet points
  following `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`

# Verification
- [ ] Confirm the proposed location exists in `<TARGET>` (e.g., a real
      chapter or slide)
- [ ] Confirm the proposal follows `.claude/skills/markdown.rules.md` and
      `.claude/skills/text.rules.md`
- [ ] Confirm the user was asked for clarification if the location was
      ambiguous, rather than the location being guessed
