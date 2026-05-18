---
description: Gather information about books
---

- Given information about books (either a partially complete table or a list of
  books), find the following information
    - Title
    - Authors
      - Use the format from `.claude/skills/book.rules.md` and `## Format of Authors`
    - Publisher
    - Year
    - Technical: Yes if it's a technical book, otherwise no
    - Goodreads (1-10): Goodreads rating x 2
    - Reviews (1-10): Relative volume (10 = 1500+ reviews, 1 = <10 reviews)
    - Academic (1-10): Theoretical depth and scientific rigor
    - Practical (1-10): Industry applicability and hands-on utility
    - Clarity (1-10): Accessibility and pedagogical quality
    - Average: Simple mean of the previous values

- Do not print any information on the screen, but only save a file
- Output files:
  - `book_info.md`: Markdown table
  - `book_info.tsv`: Tab-separated values
  - Make sure that there is no file already, otherwise use a file like
    `book_info.<comment>.{md,tsv}`
