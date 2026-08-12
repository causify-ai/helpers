---
description: Enrich slides with references to academic papers and books
model: haiku
---

# Goal
- Your task is to review the content of the passed file with slides `<FILE>` and
  add references to books and technical papers

# Workflow

## Role
- Your role is specified in `.claude/skills/role.ai_researcher.md`
- Follow the format and the conventiosn in `.claude/skills/references.rules.md`
  for the 

## Find References
- If `<FILE>` has already reference to technical papers, give priority to those
  references

- If needed, add supporting academic references (papers, journals, conference papers,
  books, or authoritative articles)
  - Prefer sources from Google Scholar, arXiv, IEEE, ACM, Springer, Elsevier,
    official documentation, and major tech research blogs
  - Add direct arXiv / free-access versions where available
  - Include working URLs for each reference when possible
  - Prefer recent references rather than old

## Add Citations
- Find the text in `<FILE>` that can use a citation and add it
- You must be sure that the citation is correct: if you are not sure, do not add
  it

