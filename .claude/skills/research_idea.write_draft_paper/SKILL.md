---
description: Write a conference paper draft from a research idea
model: opus
---

# Goal
- Given a research idea, write a full conference paper draft using the
  template in `papers/template/`

# Workflow

## Read the Inputs
- Read the research idea passed by the user (a file under `research/ideas/*.md`,
  or idea text pasted directly)
- Read the paper template `papers/template/paper.md`, including the comment
  block at the top, for usage and section structure
- Read an existing paper for style and depth, e.g.
  `papers/Optimal_strategy_for_racket_sports/paper.md`

## Set Up the Paper Directory
- Derive a short `Title_Case` name for the paper from the idea (e.g.
  `RL_for_Automated_EDA`); ask the user if the idea does not suggest an
  obvious name
- Create `papers/<Paper_Name>/` if it does not exist
- Link `Makefile` to `papers/template/Makefile` with a symlink, so that all the
  paper dirs stay in sync, e.g.,
  `ln -s ../template/Makefile papers/<Paper_Name>/Makefile`
  - Do not copy it and do not edit it for a single paper
- Copy `references.bib`, `ieee-template.typ`, and `figures/` from
  `papers/template/` into the new directory
- Do not copy `run_latex.sh`, `lint_latex.sh`, or `template.pdf`, since they
  are obsolete or build outputs
  - Build with `make` (which calls `run_latex.py` for LaTeX, which also renders
    the diagrams with `render_images.py`)
  - Lint with `lint_text.py -i <file> --use_dockerized_prettier`
- If the paper is written in LaTeX instead of Markdown, also copy `paper.tex`
  and keep the `\input{papers/template/style.tex}` line in `paper.tex`, which
  is shared by all the papers
- Do not overwrite an existing `paper.md` without confirming with the user

## Write `paper.md`
- Fill in every `<...>` placeholder with content derived from the idea:
  title, author(s) (use the assignee(s) listed in `research/ideas/README.md`
  for this idea, plus GP Saggese), abstract, keywords, and all body sections
- Keep the template's section structure (`Introduction`, `Related Work`,
  `Problem Formulation`, core methodology, `Discussion/Limitations`,
  `Conclusion`); add, remove, or rename sections only where the template says
  it's allowed
- Turn the idea's `Core Idea`, `Formalization`, `Key Examples`, and `Research
  Topics` into the `Introduction` and `Problem Formulation` sections
- Turn the idea's `Questions` and `Next steps` into `Discussion/Limitations`
  and `Conclusion/Future Work` material
- State plainly, per the template, what has not been validated (e.g. no
  computational implementation or empirical evaluation) instead of
  fabricating results the idea does not support
- Delete the template's guidance bullets and HTML comment once replaced with
  real content

# Conventions
- Follow `.claude/skills/research_idea.rules.md`, `.claude/skills/markdown.rules.md`,
  and `.claude/skills/text.rules.md`
- Fit text in 80-90 character lines
- Cite claims with `[@key]` and add matching entries to `references.bib`

# Constraints
- Do not fabricate experimental results the idea does not support; state
  explicitly what remains unvalidated
- Do not overwrite an existing `paper.md` without user confirmation

# Examples
- `papers/Optimal_strategy_for_racket_sports/paper.md`

# Verification
- [ ] `papers/<Paper_Name>/Makefile` is a symlink to `../template/Makefile`
- [ ] `papers/<Paper_Name>/` contains `references.bib`,
  `ieee-template.typ`, `figures/`, and `paper.md`
- [ ] No `<...>` placeholder remains in `paper.md`
- [ ] Every claim has a `[@key]` citation with a matching `references.bib`
  entry
- [ ] Run `make` in `papers/<Paper_Name>/` and confirm `paper.md` builds to
  `paper.pdf` without errors
