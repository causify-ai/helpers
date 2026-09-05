---
description: Make sure that the PDF rendering of a slide smd file is well formed
model: haiku
---

# Goal
- Make sure that the PDF rendering of a slide `.smd` file is well formed

# Inputs
- `<SMD_FILE>` lecture file to check
  - E.g., `msml610/lectures_source/Lesson01.4-Brief_History_of_AI.smd`

# Workflow

## Conventions
- Follow the role specified in `.claude/skills/role.ai_researcher.md`
- Read the conventions in `.claude/skills/slides.rules.md`

- Run
  ```
  > gen_slides.py <SMD_FILE> -- --toc_type=remove_headers
  ```
- Read the generated PDF `<PDF_FILE>`
  - E.g., `msml610/lectures_pdf.tmp/Lesson01.4-Brief_History_of_AI.pdf`

- Check that the number of slides in the `.smd` file `<SMD_FILE>`
  ```
  > grep "^* " <SMD_FILE> | wc -l
  ```
  is the same as the number of pages in the PDF without considering the `References`
  page

- If that's not true it means that some slides `* <title>` are rendered in more than
  one PDF
- Then adjust the size of the pictures and change the text so that each slide fits
  exactly in

## Verification
- [ ] The number of slides in `<SMD_FILE>` is the same number of slides in the
  `<PDF_FILE>` file
