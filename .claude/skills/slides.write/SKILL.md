---
description: Write lecture slides for a graduate-level course following academic formatting and pedagogical style
model: sonnet
---

# Goal

- Write a fixed number of slides on a given topic

## Role

- Your role is specified in `.claude/skills/role.ai_researcher.md`

## Read Material

- The user will provide:

  - Information, a topic, or a file `<INPUT_FILE>`
  - (Optional) Number of slides `<NUM_SLIDES>` otherwise assume
    `<NUM_SLIDES> = 3`

- If the user has passed you a file `<INPUT_FILE>` read it

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
  - E.g., For `books/facure/text_7.md` use `books/facure/text_7.slides.md`
  - Make sure that the file was empty, otherwise use a different file

## Lint

- Run `lint_txt.py -i <OUTPUT_FILE>`
