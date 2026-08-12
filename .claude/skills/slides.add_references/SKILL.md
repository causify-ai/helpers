---
description: Enrich slides with references to academic papers and books
model: sonnet
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

- Citations:
  - Are in the typst format (e.g., `[@su2024dualformer]`)
  - Correspond to entries in the file `refs.bib` in the same dir that `<FILE>` is

## Verification

- [ ] Check that the paper reference exist

- [ ] Make sure that the updated document works by running the flow, e.g.,
  `gen_slides.py` or `notes_to_pdf.py` with `--skip_action open_pdf` (since we
  just want to make sure it runs not render it)
  ```
  > gen_slides.py book.Agentic_AI/12.1 --skip_action open_pdf
  ```
  - Too many references in the same page (e.g., more than 4) can generate
    problems like
    ```
    warning: layout did not converge within 5 attempts
     = hint: check if any states or queries are updating themselves

    error: cannot format citation in isolation
        ┌─ @preview/touying:0.7.4/src/magic.typ:175:8
        │
    175 │         cite(it.key, form: "full")
        │         ^^^^^^^^^^^^^^^^^^^^^^^^^^
        │
        = hint: check whether this citation is measured without being inserted into the document
    ```
    which require to search for the problematic reference through bisection
