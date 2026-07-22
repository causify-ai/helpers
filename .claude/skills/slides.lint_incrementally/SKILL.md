---
description: Fix the slides incrementally
---

# Goal
- The user will pass you:
  - `<FILE>` a pointer to a file storing slides
  - `<NUM_SLIDES>` a number of files to fix at the time (the default is 5)
    - The user can specify to fix all the slides in one shot
    
- You will fix the slides in `<FILE>`, `<NUM_SLIDES>` slides at the time, to
  allow the user to review and fix things up

# Workflow
- Read `.claude/skills/slides.rules.md`

## Step 1
- Process `<NUM_SLIDES>` slides at the time from `<FILE>`
  - Each slide is a chunk of text starting with `* <TITLE>`

- Find which rules from `.claude/skills/slides.rules.md` are not followed by the
  `<NUM_SLIDES>` slides being processed

- Apply changes to make the current `<NUM_SLIDES>` slides follow the rules

## Step 2
- Wait for the user to confirm before moving forward to the next chunk of
  `<NUM_SLIDES>` slides
