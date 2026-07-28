---
description: Write lecture slides for a graduate-level course following academic formatting and pedagogical style
model: opus
---

# Goal
- Given content or topic from the user, write a given number of slides

# Workflow

## Role
- Your role is specified in `.claude/skills/role.ai_researcher.md`

## Input
- The user will provide:
  - Information, a topic, or a file `<TOPIC>`
  - (Optional) Number of slides `<NUM_SLIDES>` otherwise assume
    `<NUM_SLIDES> = 3`
- If the user has passed you a file `<TOPIC>` read it

## Format
- For all formatting rules, templates, and structural guidelines, see
  `.claude/skills/slides.rules.md`

## Create Slides
- Create `<NUM_SLIDES>` slides
- Each slide needs to start with a `* <TITLE>` format

## Add Visuals
- Follow the instructions from `.claude/skills/visuals.rules.md`

## Save Result
- Do not print anything on the screen
- Save the result in a output file `<OUTPUT_FILE>` like `<file>.slides.md`
  - E.g., for an input like `books/dir/text_7.md` use
    `books/dir/text_7.slides.md`
  - If the file already exists, delete it and create a new one
