---
description: Write a conference paper draft from a research idea
model: opus
---

# Goal
- Given a research idea, write a full conference paper draft using the
  template in `papers/template/`

# Workflow

## Step 1: Read the Inputs
- Read the research idea passed by the user (a file under `research/ideas/*.md`,
  or idea text pasted directly)
- Read the paper template `papers/template/paper.md`, including the comment
  block at the top, for usage and section structure
- Read an existing paper for style and depth, e.g.
  `papers/Optimal_strategy_for_racket_sports/paper.md`

## Step 2: Set Up the Paper Directory
- Derive a short `Title_Case` name for the paper from the idea (e.g.
  `RL_for_Automated_EDA`); ask the user if the idea does not suggest an
  obvious name
- Create `papers/<Paper_Name>/` if it does not exist
- Copy `Makefile`, `references.bib`, `ieee-template.typ`, and `figures/` from
  `papers/template/` into the new directory
- Do not overwrite an existing `paper.md` without confirming with the user

## Step 3: Write `paper.md`
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
- [ ] `papers/<Paper_Name>/` contains `Makefile`, `references.bib`,
  `ieee-template.typ`, `figures/`, and `paper.md`
- [ ] No `<...>` placeholder remains in `paper.md`
- [ ] Every claim has a `[@key]` citation with a matching `references.bib`
  entry
- [ ] Run `make` in `papers/<Paper_Name>/` and confirm `paper.md` builds to
  `paper.pdf` without errors
