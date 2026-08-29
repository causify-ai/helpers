---
description: Review slides for structure, content correctness, and readability; propose and apply improvements
model: opus
---

# Goal
- Given a markdown file with slides about technical material, review the content
  for correctness, clarity, and structural organization
- This skill composes `slides.reorganize` (structure) and `slides.criticize`
  (content/clarity critique)

# Workflow

- Read the conventions in `.claude/skills/slides.rules.md`

## Step 1: Propose Structural Improvements
- Run the flow from `.claude/skills/slides.reorganize/SKILL.md` through its
  Step 3, saving the proposal to `slides.after.txt`; do not apply yet

## Step 2: Propose Content Improvements
- Run Step 2 ("Criticize") from `.claude/skills/slides.criticize/SKILL.md` on
  the deck, using the same axes and HIGH/MEDIUM/LOW ranking
- Also propose how to change and improve the titles of the slides

### Ignore TODOs and Comments
- Leave the TODOs or comments in the format
  ```
  // TODO...
  ```
  untouched

## Step 3: Ask User and Implement
- Present the structural proposal (Step 1) and the ranked content findings
  (Step 2) together, numbered so each is easy to refer to
- Ask the user which structural moves and which content fixes to apply
- After the user approves a subset, perform the reorganization and the
  content changes together in place
