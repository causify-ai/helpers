---
description: Propose a reorganization of the slides, without removing any content
model: sonnet
---

# Goal
- Given a markdown file `<FILE>` with slides about technical material propose how to
  reorganize the slides without removing any content, but only moving / reorganizing
  the content

# Workflow
- Read the conventions in `.claude/skills/slides.rules.md`

## Extract Table of Content
- Extract the current table of content of the slides
  ```
  > extract_toc_from_txt.py -i <FILE> --max_level 5 --mode headers 2>&1 | tee slides.before.txt
  ```

## Propose Reorganization
- Propose how to organize the slides in a different flow, separating cohesive chunks
  with:
  - level 1 `# ...`
  - level 2 headers `## ...`
  - slides `* ...`

- E.g.,
  ```
  # Topic 1

  ## Topic 1.1

  * Slide 1
  ...

  * Slide 2
  ...
  ```

- Do not delete any slide, only move slides around, without changing them

## Propose Slides to Remove or Merge

- Propose slides whose content is redundant or unclear to be removed
- Propose slides to merge to consolidate or remove redundant content

## Wait for User

- Save the entire proposal in `plan.slides.reorganize.md` in the current dir
- Save the proposal in the file `plan.slides.after.txt` in the same format as
  `plan.slides.before.txt`

## Perform Reorganization

- Wait for the user to approve the changes
- After the user approves, perform the changes in place reorganizing the slides,
  but without removing any slide or content

## Verify Rendering
- [ ] Make sure that the updated slides render correctly, e.g.,
  ```bash
  > gen_slides.py -i <FILE> --notes_to_pdf_args="--skip_action open_pdf"
  ```
