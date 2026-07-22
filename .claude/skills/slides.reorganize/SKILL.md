---
description: Propose a reorganization of the slides, without removing any content
model: opus
---

# Goal
- Given a markdown file `<FILE>` with slides about technical material propose how
  to reorganize the slides without removing any content

# Workflow

- Read the conventions in `.claude/skills/slides.rules.md`

## Step 1
- Extract the current table of content of the slides
  ```
  > extract_toc_from_txt.py -i <FILE> --max_level 5 --mode headers 2>&1 | tee slides.before.txt
  ```

## Step 2
- Propose how to organize the slides in a different flow, separating cohesive
  chunks with level 1 `# ...`, 2 headers `## ...`, and slides `* ...`
  - E.g.,
    ```
    # Topic 1
    ## Topic 1.1
    * Slide 1
    * Slide 2
    ...
    ```
- Do not delete any slide, only move them around

- Save the proposal in the file `slides.after.txt` in the same format as
  `slides.before.txt`

## Step 3
- Wait for the user to approve the changes
- After the user approves, perform the changes in place reorganizing the slides,
  but without removing any slide or content
