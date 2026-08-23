---
description: Enrich slides with references to academic papers and books
model: sonnet
---

# Goal
- Review the passed slides file `<FILE>.smd` and add references to books and
  technical papers

# Workflow

## Conventions
- Follow the role specified in `.claude/skills/role.ai_researcher.md`
- Follow the reference format and conventions in
  `.claude/skills/references.rules.md`

## Find References
- If `<FILE>` already has references to technical papers, give priority to
  those references (e.g., at the beginning in the form of `//` comments)

- Add supporting references, following the source types and retrieval
  methods in `.claude/skills/references.rules.md`
  `# When Searching for References`

## Add Citations
- Find the text in `<FILE>` that can use a citation and add it
- Be sure that the citation is correct: if unsure, do not add it

- Citations:
  - Are in the typst format (e.g., `[@su2024dualformer]`)
  - Correspond to entries in the file `refs.bib` in the same directory as
    `<FILE>`

## Verification

- [ ] Check that each paper reference exists
- [ ] Make sure that the updated document works by running the flow, e.g.,
  `gen_slides.py` or `notes_to_pdf.py` with `--skip_action open_pdf` (the
  goal is to confirm it runs, not render it)
  ```bash
  > gen_slides.py book.Agentic_AI/12.1 --skip_action open_pdf
  ```
  - Too many references on the same page (e.g., more than 4) can generate
    problems like:
    ```text
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
    which requires searching for the problematic reference through bisection
