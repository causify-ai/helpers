---
description: Rate an academic paper from 1 to 5 by page length, affiliation, citations
model: sonnet
---

# Goal

- Rate the passed paper from 1 (low) to 5 (best) using its page length, the
  affiliation of its authors, and its number of citations
- Follow the rules in `.claude/skills/paper.rules.md`, `# Paper Rating`

# Workflow

## Get the Paper

- Use the PDF passed by the user
- If the input is a URL, an arXiv ID, or a DOI, download only the PDF with
  `download_academic_paper_to_md.py --input <INPUT> --clear_actions --action download`

## Collect the Signals

- Count the pages of the PDF
- Read the affiliations of all the authors on the first page
- Look up the citation count in Semantic Scholar for the DOI or the arXiv ID, and
  note the date
- Do not use memory for any of these values

## Rate

- Score each signal and compute the rating with the tables in
  `.claude/skills/paper.rules.md`

## Write the Rating File

- Save `<BASE>.rating.md` next to the paper, where `<BASE>` is the name of the PDF
  without `.pdf`
- Follow the template `.claude/templates/paper_rating.template.md`
- Report the rating and the three scores to the user

# Constraints

- Use whole numbers only
- If a signal cannot be found, write `unknown` and leave it out of the mean

# Verification

- [ ] The rating is an integer from 1 to 5
- [ ] Each signal has a value and a score
- [ ] The citation count has a source and a date
- [ ] The rating equals the mean of the known scores, rounded half up
