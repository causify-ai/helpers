---
description: Incorporate content into other material (books, slides, papers, blog ideas)
model: sonnet
---

# Goal

- The user passes, in this order:
  1. The content `<CONTENT>` to incorporate
  2. Optionally, the target `<TARGET>`: a file (e.g., a book, slides, paper,
     blog) or a reference to a part of a file (e.g., a chapter, section, slide
     number)
- Propose where and how to include `<CONTENT>` in `<TARGET>`

# Workflow

- Read the proposed content `<CONTENT>`
- Resolve `<TARGET>`
  - If `<TARGET>` was passed:
    - If it is a reference to a part of a file (e.g., "chapter 3", "slide 12"),
      open that file and jump to that part
    - If it is a whole file and it belongs to a book / course (e.g.,
      `book_springer/map.md`), read the `map.md` to understand the structure of
      the material covered
  - If `<TARGET>` was not passed, find it
    - List candidate files for `<CONTENT>` (e.g., books, slides, papers, blog
      posts under the relevant course or project directory, using each file's
      `book_map.md` or table of contents when one exists)
    - Compare the topic of `<CONTENT>` against each candidate's content
      (title, headers, structure) and rank candidates by relevance
    - If exactly one candidate is a clear, unambiguous match, use it as
      `<TARGET>` and tell the user which file was picked and why
    - If several candidates are close in relevance, or none is a plausible
      match, STOP and ask the user to confirm or pick the target instead of
      guessing
- Find out which part of `<TARGET>` the content is relevant for
  - If more than one location is plausible, or no location fits well, STOP and ask
    the user to clarify where to add the content instead of guessing
- Propose how to integrate the `<CONTENT>` in `<TARGET>` using bullet points
  following `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`

# Verification

- [ ] Confirm `<TARGET>` is either the one the user passed or one the user
      confirmed, rather than guessed
- [ ] Confirm the proposed location exists in `<TARGET>` (e.g., a real chapter or
      slide)
- [ ] Confirm the proposal follows `.claude/skills/markdown.rules.md` and
      `.claude/skills/text.rules.md`
- [ ] Confirm the user was asked for clarification if the file or the location
      within it was ambiguous, rather than either being guessed
