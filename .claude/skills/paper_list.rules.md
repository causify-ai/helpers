Conventions for a paper list (e.g., `book_Modern_AI_for_Finance/paper_list.md`): how
to organize sections, write one entry per paper, and score each paper

# Overview

- A paper list is a reading list of papers, books, datasets, and web resources
  for a book or a course
- Each entry has a title line, a link, a score, and optionally a short summary
- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md` for
  text formatting
- Format of the references follows `.claude/skills/references.rules.md`, except that
  the link moves to a `**Url**` bullet

# File Structure

## Index

- Start the file with an index comment that mirrors the H1 and H2 headers
  ```markdown
  // Index
  // - Causal Analysis for Finance
  //   - Causal Inference Foundations
  //   - Causality in Finance
  // - Causal Macroeconomic Modeling
  //   - Bayesian Macroeconometrics
  ```
- Keep the index in sync when a section is added, renamed, or removed

## Sections

- Use an H1 (`#`) for a broad area and an H2 (`##`) for a topic inside the area
- Put the entries under H2 headers
- Do not use headers of level 3 or deeper to hold a paper: a paper is a list item

## Order of Entries

- Sort the entries of an H2 in reverse chronological order (most recent first)
- Put undated entries (`N.d.`, e.g., a web page) last
- List each paper once, in the section where it fits best

# Entry Format

## Fields

- One entry is a checkbox bullet with the title line, followed by indented bullets in
  this order:
  - `**Url**`: link to the paper (required)
  - `**Code**`: link to the code or dataset (optional)
  - `**Score**`: quality score `x/5` (required, see "Score" below)
  - 2 to 4 summary bullets (optional)
- E.g.,
  ```markdown
  - [ ] 2025, Hünermund Et Al., "Causal Inference and Data Fusion in Econometrics"
    - **Url**: https://arxiv.org/abs/1912.09104
    - **Score**: <N>/5
  ```

## Title Line

- Format the title line as
  ```
  - [ ] <Year>, <Last name of first author> [Et Al.], "<Title>"
  ```
- Use `Et Al.` when the paper has more than one author and the last name alone for a
  single author
- Use the year of the published version. Use the preprint year when only a preprint
  exists. Use `N.d.` when there is no date
- Write the title as published, between double quotes
- Use `- [ ]` for an entry not yet reviewed and `- [x]` once it is reviewed
- Indent the continuation lines of a wrapped title by 6 spaces, to align with the
  text after `- [ ] `
- Do not put a blank line between the title line and its bullets

## Url

- Prefer the abstract page on arXiv (`https://arxiv.org/abs/<ID>`) over the PDF
- Otherwise prefer a stable public link: SSRN, NBER, the publisher, or the author's
  page
- Add ` ???` after the link when the link is not verified
- Never write the link between parentheses in the title line

## Summary Bullets

- When an entry has a summary, write 2 to 4 bullets, each 1 to 2 sentences
- State what the paper does, its method or main idea, and its key result (with
  numbers when available)
- Take the content from the abstract or the paper, never from memory
- Mention the venue in a final sentence only when it adds information
  (e.g., "Published at ICLR 2024")
- Use `:` instead of a dash to separate clauses
- Wrap prose at 85 characters

## Layout

- Indent the field bullets and the summary bullets by 2 spaces under the title line
- Keep the entries of a section one after the other, without blank lines, when
  they have no summary bullets
- Separate entries that have summary bullets with one blank line

# Score

## Meaning

- `**Score**: x/5` where `x` is an integer from 1 (low) to 5 (high)
- The score estimates the authority and impact of the paper: how much a reader
  should trust it and how widely the field uses it
- The score is not a measure of how well the paper fits the book. Topic fit is
  decided by the section the paper is in

## Signals

- **Citations**: the count from Semantic Scholar or Google Scholar, read relative to
  the age of the paper and the size of its field
- **School and institution quality**: top universities and research labs, central
  banks, NBER, and industry research labs of high standing
- **Venue**: top journals and conferences count more than a preprint only on SSRN or
  arXiv
  - E.g., Econometrica, AER, QJE, JF, JFE, RFS, JASA, NeurIPS, ICML, ICLR, ACL
- **Authors**: a recognized researcher in the area
- **Adoption**: use of the paper's method, benchmark, library, or dataset by other
  work, and a maintained code base
- **Recency**: for papers under 2 years old, read the citations per year and the
  other signals, not only the total count

## Scale

- Use the following guideline and adjust it for field and age:
  - `5/5`: field-defining or foundational. Very high citations (roughly 1000 or
    more), top venue, and top authors or institution
  - `4/5`: strong. High citations (roughly 300 to 1000), or a top venue or
    institution with wide adoption
  - `3/5`: solid. Moderate citations (roughly 50 to 300), or a good venue or
    institution
  - `2/5`: modest. Few citations (roughly 10 to 50), a preprint, or less known
    authors
  - `1/5`: little evidence of impact. Under 10 citations, not peer reviewed, and
    unknown authors
- For non-papers (books, datasets, web pages), score the adoption and the authority
  of the publisher or maintainer
- Use whole numbers only: no `3.5/5`
- If the signals disagree, score on the strongest signals and do not average
- Re-score an entry when its signals change a lot (e.g., a recent paper gains
  many citations)

# Verification

- Check every reference against a source before adding it: the arXiv API, Crossref,
  or Semantic Scholar. Do not write a reference from memory
- Check that the first author, year, and title match the source
- Check that the link opens and points to the paper with the same title
- Mark a doubt in the file with a comment at column 0 above the entry
  ```markdown
  // TODO(gp): Check the year of the published version
  ```
- Use `// TODO(ai_gp): <task>` at column 0 for work that the AI assistant must do
