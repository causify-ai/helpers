---
description: Fix the slides incrementally
---

# Goal

- The user will pass `<FILE>` a pointer to a file storing slides you will fix
  `<FILE>` 5 slides at the time, to allow the user to review and fix things up

# Workflow

- Read `.claude/skills/slides.rules.md`

- Process 5 slides at the time from `<FILE>`
  - Each slide is a chunk of text starting with `* <TITLE>`

- Find which rules from `.claude/skills/slides.rules.md` are not followed by the
  5 slides being processed

- Apply changes to make the current 5 slides follow the rules

- Wait for the user to confirm before moving forward to the next chunk of 5 slides
