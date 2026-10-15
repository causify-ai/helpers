---
description: Renumber a book map, reorder its Detailed TOC to follow the Short TOC, and rename the matching lecture and tutorial files
model: opus
---

# Goal

- Given a book map `<BOOK_MAP>` (e.g., `book_Modern_AI_for_Finance/book_map.md`),
  make it follow `.claude/skills/book_map.rules.md`:
  - Renumber the chapters
  - Reorder `# Detailed TOC` to follow `## Short TOC`
  - Keep the Roadmap table in sync
  - Rename the numbered files in `<BOOK>/lectures_source/` and
    `<BOOK>/tutorials/`, and fix the references to them
- Write a plan, wait for the user to approve it, then apply it

# Inputs

- `<BOOK_MAP>`: the book map to update
- `<BOOK>`: the directory that contains `<BOOK_MAP>`

# Workflow

## Read

- Read `.claude/skills/book_map.rules.md` and `<BOOK_MAP>` in full
- Use `.claude/templates/book_map.template.md` for the structure of new chapters
- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
  for any text you add

## Compute the New Numbers

- `## Short TOC` is the source of truth for the order of the chapters, the parts,
  and the part names
  - Do not trust the chapter numbers in the file
- Match chapters across Short TOC, Detailed TOC, and Roadmap by title
  - Treat titles that differ only in case, `and`, or a trailing `s` as equal
- Number the chapters `01`, `02`, ... in Short TOC order, with no gaps
  - Number the entries marked `?` too
- Keep the map `old number -> new number`

## Map the Files

- Look recursively in `<BOOK>/lectures_source/` and `<BOOK>/tutorials/`
- A name is numbered when `Lesson` or `L` is followed by `<NN>` and `.` or `_`
  - E.g., `Lesson05.01_Forecasting.smd`, `L05_forecasting/`,
    `L05_01_forecasting.ipynb`, `figures/L05.01.Drawdown.png`
- Skip `__pycache__/`, `*.pyc`, `*.log`, `OLD/`, `old/`, and names with no number
- Assign each file to a chapter:
  - First by the file name in the Roadmap, `### Slides`, or `### Tutorials`
  - Then by the old number in the name
- Build the new name by replacing only `<NN>`
  - Keep `<MM>`, the title, and the extension
- Do not rename a file when the two rules disagree or no chapter matches: ask
  under `## Questions`

## Write the Plan

- Create `plan-book_map.update.md` next to `<BOOK_MAP>`
- Write a checkbox list with a global index on each item, so the user can approve
  by index
- Make each item state the exact change, the line number, and the reason
- Group the items under these headers, omitting the empty ones:
  - `## Short TOC`, `## Parts`, `## Renumbering`, `## Reordering`,
    `## New Chapters`, `## Chapters Without a Short TOC Entry`, `## Roadmap`,
    `## Cross References`, `## Lecture Files`, `## Tutorials`,
    `## File References`, `## Findings Not Fixed`, `## Questions`

Propose these changes:
- **Short TOC**: nested bullets (part, then `<NN>, <Title>`, then topics)
- **Parts**: make `# Part` headings and Roadmap part rows use the Short TOC names
  and order, keeping the numeral style of the file
- **Titles**: use the Short TOC title in the three places
  - Ask when the meaning differs, not only the wording
- **Renumbering and reordering**: one item per chapter that changes
  - Move a chapter as one block, from its `## <NN>:` heading to the next `##`
- **New chapter** (in Short TOC, not in Detailed TOC): create the section from
  the Chapter Template
  - Fill `### Goals` with 3 bullets and `### Topics` from the Short TOC
  - Write `### Slides` as `- N/A: no dedicated deck yet`
  - Write `### Lesson Materials` with only `_Not covered_` and a
    `// TODO(gp): Fill the lesson materials` line
  - Do not invent coverage percentages
- **Chapter without a Short TOC entry**: never propose to delete it
  - Ask: add it to the Short TOC, merge it into a chapter, or remove it
- **Roadmap**: reorder and renumber the rows, keep the cell values, and use the
  new file names in the cells
- **Cross references**: replace old chapter numbers in prose (`chapter 02`)
- **Lecture files and tutorials**: one item per chapter and directory, listing
  each `old path -> new path`
  - Keep a tutorial directory and its files in one item, since the notebook,
    its `.py`, and `_utils.py` import each other by name
- **File references**: one item per file that uses an old name, as
  `<path>:<line>: <old> -> <new>`
  - Look in `<BOOK_MAP>`, the renamed files (figure paths, `import` lines), and
    other book maps or `// From:` comments in this repo
  - For other Git repos, point to `.claude/skills/git.update_references/SKILL.md`
- **`// TODO(ai_gp):` markers**: remove a marker the plan resolves, and list the
  others under `## Questions`

Only report these, because they need content judgment:
- Missing chapter subsection
- `### Goals` without 3 bullets, or a bullet of 100 characters or more
- `### Topics` over 25 lines or 200 words
- `### Lesson Materials` pointing to `<BOOK>/lectures_source/*.smd`
- Short TOC topics that differ from `### Topics`
- Wrong coverage percentages
- For a content review, point to `.claude/skills/book.criticize_toc/SKILL.md`

## Wait for Approval

- Print only the path of the plan and the number of items
- Wait for the user to approve items by index, or to give corrections
- Do not edit `<BOOK_MAP>` or rename any file before the approval

## Apply the Approved Items

- Edit `<BOOK_MAP>` in this order, so the line numbers in the plan stay valid:
  - Cross references, Roadmap, Detailed TOC (move, renumber, add), Short TOC
- Rename files with `git mv` (see `.claude/skills/git.move/SKILL.md`), in two
  phases, because renumbering permutes the numbers (`02 -> 03`, `03 -> 04`):
  - Move every approved path to `tmp.<new name>`
  - Move every `tmp.<new name>` to its final path
  - Rename a directory before the files in it
- Update the references with one mapping `old name -> new name`, applied in a
  single pass per file, so that a replacement is never replaced again
  - Replace whole names only, never a bare `L02` or `Lesson02`
- Format `<BOOK_MAP>`:
  ```bash
  > lint_text.py -i <BOOK_MAP>
  ```
- Show a summary: renumbered, moved, and renamed items, and anything left open

# Constraints

- Do not edit anything before the user approves the plan
- Do not change a chapter's text, except its `## <NN>:` heading, its chapter
  number cross references, and the edits in an approved item
- Do not delete a chapter, a topic, a Lesson Materials bullet, or a file
- Do not rename a file outside `<BOOK>/lectures_source/` and `<BOOK>/tutorials/`
- Do not change the content of a lecture or tutorial file, except the references
  to renamed files
- Do not guess coverage percentages
- Do not commit: leave the changes in the working tree

# Example

```markdown
## Renumbering
- [ ] 1. `## 05: Price and Volatility Forecasting` -> `## 07: Forecasting`
      (line 561): Short TOC position 7

## Reordering
- [ ] 2. Move `## 07` (lines 561-690) after `## 06` (line 1012)

## Lecture Files
- [ ] 3. Chapter `05 -> 07`, `lectures_source/`
  - `Lesson05.01_Forecasting.smd` -> `Lesson07.01_Forecasting.smd`
  - `figures/L05.01.Drawdown.png` -> `figures/L07.01.Drawdown.png`

## Tutorials
- [ ] 4. Chapter `05 -> 07`, `tutorials/`
  - `L05_forecasting/` -> `L07_forecasting/`
  - `L05_forecasting/L05_01_forecasting.ipynb` ->
    `L07_forecasting/L07_01_forecasting.ipynb`

## File References
- [ ] 5. `book_map.md:145`: `Lesson05.01_Forecasting.smd` ->
      `Lesson07.01_Forecasting.smd`
```

# Verification

- [ ] Confirm chapter numbers are consecutive, zero-padded, with no `?` left
- [ ] Confirm `## <NN>:` headings, Roadmap rows, and part names follow the Short
      TOC order
- [ ] Confirm no prose reference uses an old chapter number
- [ ] Confirm every numbered file under `lectures_source/` and `tutorials/` has
      the number of its chapter
- [ ] Confirm `git status --short <BOOK>` shows renames, and no `tmp.*` is left
- [ ] Confirm `grep -rF "<old name>" .` finds nothing
- [ ] Confirm `python -I -m py_compile` passes on the renamed tutorial `.py`
      files
- [ ] Confirm `lint_text.py -i <BOOK_MAP>` completes without errors
