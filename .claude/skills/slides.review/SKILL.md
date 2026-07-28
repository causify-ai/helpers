---
description: Review slides for structure, content correctness, and readability; propose and apply improvements
model: opus
---

# Goal
- Given a markdown file with slides about technical material, review the content
  for correctness, clarity, and structural organization

# Workflow

- Read the conventions in `.claude/skills/slides.rules.md`

## Step 1: Propose Structural Improvements

- Run the flow from `.claude/skills/slides.reorganize/SKILL.md`

## Step 2: Propose Content Improvements
- Propose how to change and improve the titles of the slides
- Look for mistakes in the content and propose improvements

### Fix Content of Slides
- If a slide content is incorrect, propose how to fix it

### Ignore TODOs and Comments
- Leave the TODOs or comments in the format
  ```
  // ...
  ```
  untouched

## Step 3: Ask User and Implement
- Number each suggestion so that it's easy to refer to
- Ask the user which improvements need to be done
- After the user approves a subset of changes, perform the changes in place
