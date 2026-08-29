---
description: Add links from lecture slides to the corresponding sections of a rendered tutorial notebook
model: sonnet
---

# Goal
- Given a slides file `<FILE>` and a rendered HTML tutorial `<TUTORIAL_URL>`,
  add links from each slide to the tutorial section it corresponds to
  - E.g., `<FILE>` =
    `msml610/lectures_source/Lesson09.3-Multi_Armed_Bandits.txt` and
    `<TUTORIAL_URL>` =
    `https://raw.githack.com/gpsaggese/gpsaggese.github.io/gp_scratch/msml610/tutorials/L09_multi_armed_bandits/L09_03_02_multi_armed_bandits.html`

# Workflow

## Conventions
- Follow the role specified in `.claude/skills/role.ai_researcher.md`
- Follow the conventions in `.claude/skills/slides.rules.md`

## Find the Relationship
- Read `<FILE>` and `<TUTORIAL_URL>`
- If a companion tutorial markdown file exists next to the notebook (e.g.,
  `<tutorial_dir>/<tutorial_name>.md`), use it to help match slide content to
  tutorial cells
- Match each slide to the tutorial cell(s) that cover the same concept

## Add Links
- For each match, add a link in the slide to the tutorial anchor for that
  cell
  - The anchor is the rendered HTML's cell heading, e.g.
    `<TUTORIAL_URL>#Cell-1:-Introduction---Casino-Slot-Machines`
- Do not add a link when no tutorial cell clearly corresponds to the slide

## Leave Structure and Content Unchanged
- Do not change the structure of the text (titles, bullet hierarchy, div
  fenced blocks) or the substantive content: add only the link

## Verification
- [ ] Check that each added anchor points to an actual heading in
  `<TUTORIAL_URL>`, not a guessed slug
