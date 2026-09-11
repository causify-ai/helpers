---
description: Review slide structure and content, then propose and apply improvements
model: opus
---

# Goal
- Given a markdown file with slides about technical material, review the content
  for correctness, clarity, and structural organization
- This skill composes `/slides.reorganize` (structure) and `/slides.criticize`
  (content/clarity critique)

# Workflow

- Read the conventions in `.claude/skills/slides.rules.md`

## Propose Structural Improvements
- Run the flow from `.claude/skills/slides.reorganize/SKILL.md` through its
  `## Wait for User` section, saving the proposal

## Propose Content Improvements
- Run the flow from `.claude/skills/slides.criticize/SKILL.md` on the deck, using the
  same axes and HIGH/MEDIUM/LOW ranking
- Also propose how to change and improve the titles of the slides

### Ignore TODOs and Comments
- Leave the TODOs or comments in the format
  ```
  // TODO...
  ```
  untouched

## Ask User and Implement
- Present the structural proposal and the ranked content findings together,
  numbered so each is easy to refer to
- Ask the user which structural moves and which content fixes to apply
- After the user approves a subset, perform the reorganization and the content
  changes together in place

## Verify Rendering
- [ ] Make sure that the updated slides render correctly, e.g.,
  ```bash
  > gen_slides.py -i <FILE> --notes_to_pdf_args="--skip_action open_pdf"
  ```
