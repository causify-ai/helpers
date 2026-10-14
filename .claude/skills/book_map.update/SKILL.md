---
description: Renumber a book map, reorder its Detailed TOC to follow the Short TOC, and rename the matching lecture and tutorial files
model: opus
---

# Goal

- Given a book map `<BOOK_MAP>` (e.g., `book_Modern_AI_for_Finance/book_map.md`),
  bring it in line with `.claude/skills/book_map.rules.md`:
  - Renumber the chapters
  - Reorder the chapters in `# Detailed TOC` to follow the order of `## Short TOC`
  - Keep the Roadmap table consistent with both
  - Rename the files in `<BOOK>/lectures_source/` and `<BOOK>/tutorials/` whose
    names embed a chapter number, so that they match the new numbers, and update
    every reference to them
- Produce a bullet list of the changes for the user to approve
- Edit `<BOOK_MAP>` and rename files only after the user approves

# Inputs

- `<BOOK_MAP>`: the book map to update
  - E.g., `book_Modern_AI_for_Finance/book_map.md`
- `<BOOK>`: the directory that holds `<BOOK_MAP>`
  - E.g., `book_Modern_AI_for_Finance/`
  - It has the subdirectories `lectures_source/` and `tutorials/`, when the book
    has them

# Conventions

- Follow the rules in `.claude/skills/book_map.rules.md`, in particular:
  - `# Overall Structure`
  - `## Short TOC`
  - `## Chapter Template`
- Follow the template `.claude/templates/book_map.template.md`
- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
  for the text that is added or moved

# Workflow

## Read the Inputs

- Read `.claude/skills/book_map.rules.md` in full
- Read `<BOOK_MAP>` in full
- List the files and directories under `<BOOK>/lectures_source/` and
  `<BOOK>/tutorials/` whose names embed a chapter number
  - They are derived from the map and go stale after a renumbering
  - A name embeds a chapter number when `Lesson` or `L` is followed by two
    digits `<NN>` and then `.` or `_`
  - E.g.,
    - `<BOOK>/lectures_source/Lesson<NN>.<MM>_<Title>.smd`
    - `<BOOK>/lectures_source/figures/L<NN>.<MM>.<Name>.png`
    - `<BOOK>/tutorials/L<NN>_<title>/`
    - `<BOOK>/tutorials/L<NN>_<title>/L<NN>_<MM>_<title>.ipynb`
    - `<BOOK>/tutorials/L<NN>_<title>/L<NN>_<MM>_<title>.py`
    - `<BOOK>/tutorials/L<NN>_<title>/L<NN>_<MM>_<title>_utils.py`
    - `<BOOK>/tutorials/L<NN>_<title>/figures/L<NN>.<MM>.<Name>.png`
  - Walk the directories recursively
  - Skip what is not derived from the map:
    - `__pycache__/`, `*.pyc`, `*.log`
    - `OLD/`, `old/`
    - Names that do not embed a chapter number (e.g., `Dockerfile`, `README.md`,
      `refs.bib`, `test/`)
- List the other files in the repo that mention one of these names
  - E.g., other book maps, `// From:` comments, notebooks, READMEs
  - Search the repo for each old name with `grep -rF`
- Do not list `<BOOK>/book/` chapter files: they are handled by
  `.claude/skills/book_chapter.update_from_source/SKILL.md`

## Build the Inventory

- Extract from `## Short TOC`, in file order:
  - Part names
  - Chapter entries as `(old number or ?, title, topic bullets)`
  - Every `// TODO(ai_gp): ...` marker
- Extract from `# Detailed TOC`, in file order:
  - Each `# Part <N>: <Part Title>` heading
  - Each `## <NN>: <Chapter Title>` heading with its line range
- Extract from `# Roadmap`:
  - Each bold `**Part Title**` row
  - Each `NN. Chapter Title` row with its cell values
- Match chapters across the three places by title, not by number
  - Numbers are what is wrong, so they are not a reliable key
  - Treat titles that differ only in case, `and`, or a trailing `s` as a match
  - Mark a match as `uncertain` when more than one candidate fits

## Compute the New Numbering

- Treat `## Short TOC` as the source of truth for:
  - The order of the chapters
  - The grouping of chapters into parts
  - The name of each part
- Assign consecutive two-digit numbers `01`, `02`, ... to the chapters in Short
  TOC order
  - Number the entries marked `?` as well
  - Do not leave gaps and do not reuse a number
- Build the map `old number -> new number` for every chapter that exists in the
  Detailed TOC

## Map the Files to Chapters

- Assign each file and directory from `## Read the Inputs` to a chapter, in this
  order of preference:
  - The chapter whose Roadmap row, `### Slides`, or `### Tutorials` names the file
    - The match is by file name, so it does not depend on the old number
  - The chapter whose old number equals the `<NN>` in the name
- Mark the assignment `uncertain` and put it under `## Questions` when:
  - The two rules above give different chapters
  - The `<NN>` matches no chapter in the Detailed TOC
- Do not rename an `uncertain` file or a file with no chapter
- Build the new name by replacing only the `<NN>` token with the new number of the
  chapter
  - Keep `<MM>`, the title part, and the extension unchanged
  - Replace `<NN>` in every place of the name
    - E.g., `L05_forecasting/L05_01_forecasting_utils.py` ->
      `L07_forecasting/L07_01_forecasting_utils.py`
  - Do not rename the title part when a chapter title changes: ask under
    `## Questions` instead
- Keep the directory and its files in the same chapter
  - E.g., all files in `L05_forecasting/` get the number of the same chapter
- Check the names before proposing them:
  - A new name does not collide with an existing path that is not itself being
    renamed
  - Two files do not get the same new name
  - A `.ipynb` and its paired `.py` keep the same base name

## Find the Problems

- Check each item below and record every violation with its line number
- Violations this skill fixes:
  - Short TOC is not nested bullets of the form part name / `<NN>, <Title>`
    (e.g., it uses `###` headings for the parts)
  - Short TOC entry has `?` instead of a number
  - Short TOC part names differ from `# Part` headings or Roadmap part rows
  - Detailed TOC chapter order differs from Short TOC order
  - Detailed TOC chapter is not in the part the Short TOC puts it in
  - Chapter number differs between Short TOC, Detailed TOC, and Roadmap
  - Chapter title differs between Short TOC, Detailed TOC, and Roadmap
  - Short TOC chapter has no `## <NN>:` section in the Detailed TOC
  - Detailed TOC chapter has no entry in the Short TOC
  - Chapter subsections are out of order
  - Prose refers to a chapter by its old number (e.g., `chapter 02`, `ch 7`)
  - A file or directory in `<BOOK>/lectures_source/` or `<BOOK>/tutorials/`
    embeds a chapter number that differs from the new number of its chapter
  - A reference to such a file or directory (in `<BOOK_MAP>`, in the renamed
    files, or elsewhere in the repo) uses the old name
- Violations this skill only reports, because they need content judgment:
  - A required chapter subsection is missing
  - `### Goals` does not have 3 bullets, or a bullet is 100 characters or more
  - `### Topics` is over 25 lines or 200 words
  - `### Lesson Materials` points to `<BOOK>/lectures_source/*.smd`
  - Short TOC topic bullets differ from the chapter's `### Topics`
  - Coverage percentages look wrong
- For a content review, point the user to
  `.claude/skills/book.criticize_toc/SKILL.md`

## Write the Plan

- Create the file `plan-book_map.update.md` in the same directory as
  `<BOOK_MAP>`
- Write the plan as a checkbox list, with a global index on every item so the user
  can approve by index
- Group the items under these headers, omitting a header with no items:
  - `## Short TOC`
  - `## Parts`
  - `## Renumbering`
  - `## Reordering`
  - `## New Chapters`
  - `## Chapters Without a Short TOC Entry`
  - `## Roadmap`
  - `## Cross References`
  - `## Lecture Files`
  - `## Tutorials`
  - `## File References`
  - `## Findings Not Fixed`
  - `## Questions`
- Make each item state the exact change, the line number, and the reason:
  - Renumbering: one item per chapter, as `old -> new`
  - Reordering: one item per chapter that moves, naming the chapter heading and
    the heading it goes after
  - Parts: rename, create, or remove a `# Part` heading, so that it matches the
    Short TOC
- Use the following rules to decide what to propose
  - **Short TOC format**
    - Convert part `###` headings to level-1 bullets, chapters to level-2 bullets
      `<NN>, <Title>`, and topic bullets to level-3 bullets
  - **Part headings**
    - Use the Short TOC part names and Roman numerals `I`, `II`, ... in the order of
      the Short TOC
    - Keep the numeral style that the file already uses
  - **Chapter titles**
    - Propose the Short TOC title in Title Case as the new title in all three
      places
    - Ask the user when the two titles differ in meaning, not only in wording
  - **New chapters** (in the Short TOC, not in the Detailed TOC)
    - Create the `## <NN>: <Title>` section with the subsections of the Chapter
      Template, in order
    - Fill `### Goals` with 3 bullets and `### Topics` from the Short TOC bullets
    - Set `### Slides` to `- N/A: no dedicated deck yet`
    - Do not invent coverage percentages: write `### Lesson Materials` with only
      the `_Not covered_` bullet and a `// TODO(gp): Fill the lesson materials`
      line at column 0
  - **Chapters without a Short TOC entry** (in the Detailed TOC, not in the
    Short TOC)
    - Never propose to delete the content
    - Offer three options: add the chapter to the Short TOC, merge it into a named
      chapter, or remove it
    - Put the question under `## Questions`
  - **Roadmap**
    - Reorder the rows and the part rows to match the Short TOC
    - Renumber the rows as `NN. Title`
    - Keep each chapter's cell values when its row moves
    - Add a row with `N/A` and empty cells for a new chapter
  - **Cross references**
    - Propose one item per prose reference that uses an old number, as
      `chapter 02` -> `chapter 03`
    - Use the `old -> new` map for the replacement
  - **Lecture files** (everything under `<BOOK>/lectures_source/`)
    - Propose one item per chapter that lists each `old path -> new path`, so that
      a deck and its figures are approved together
    - Include the `figures/` files whose names embed the chapter number
  - **Tutorials** (everything under `<BOOK>/tutorials/`)
    - Propose one item per chapter that lists each `old path -> new path`
    - Rename the tutorial directory and every file in it as one item, since the
      notebook, its paired `.py`, and `_utils.py` import each other by name
  - **File references**
    - Propose one item per file that mentions an old name, as
      `<path>:<line>: <old name> -> <new name>`
    - Cover the places below, and nothing else:
      - `<BOOK_MAP>`: Roadmap cells, `### Slides`, `### Tutorials`,
        `### Lesson Materials`, the tutorial inventory block, and `## TODOs`
      - The renamed files: `figures/...` paths in `.smd`, and `import`/`from`
        lines, figure paths, and file names in tutorial `.py`, `.ipynb`, and
        README files
      - Other files in the repo: other book maps and `// From:` comments that cite
        this book's lectures
    - Match whole old names only
      - Never replace a bare `L02` or `Lesson02`, which also appears inside
        other names
    - For references in other Git repos, point the user to
      `.claude/skills/git.update_references/SKILL.md` instead of editing them
  - **`// TODO(ai_gp):` markers**
    - Propose to remove a marker once the plan resolves it, and cite the marker
      text in the item
    - Leave a marker that the plan does not resolve, and list it under
      `## Questions`

## Wait for Approval

- Print only the path of `plan-book_map.update.md` and the number of items
- Wait for the user to approve items by index, or to give corrections
- Do not edit `<BOOK_MAP>` or rename any file before the approval

## Apply the Approved Items

- Edit `<BOOK_MAP>` and rename files for the approved items only
- Apply the edits in this order, so that line numbers in the plan stay valid
  as long as possible:
  - Cross references in prose
  - Roadmap table
  - Detailed TOC: move whole `## <NN>:` sections, with all their `###`
    subsections, and fix `# Part` headings
  - Detailed TOC: renumber the `## <NN>:` headings and add new chapters
  - Short TOC: reformat, renumber, and remove resolved `// TODO(ai_gp):` markers
  - Lecture files and tutorials: rename, as described below
  - File references: update, as described below
- Move each chapter as one block, from its `## <NN>:` heading up to the line
  before the next `##` or `#` heading
  - Do not rewrite, shorten, or reflow the text of the chapter

## Rename the Lecture Files and Tutorials

- Use `git mv`, never plain `mv`, so that Git keeps the history
  - If `<BOOK>` is in a subrepo, run `git mv` from inside that repo
  - Follow `.claude/skills/git.move/SKILL.md` for each move
- Rename in two phases, because renumbering permutes the numbers (e.g., `02 -> 03`
  and `03 -> 04`) and a direct rename overwrites a file that is not yet moved:
  - Phase 1: `git mv <old path> <dir>/tmp.<new name>` for every approved item
  - Phase 2: `git mv <dir>/tmp.<new name> <new path>` for every approved item
- Rename a directory before the files in it, and use the new directory path for
  the files
- Confirm that no `tmp.*` path is left behind

## Update the File References

- Build one mapping `old name -> new name` from all approved rename items
- Apply the mapping in one pass over each file, so that a replacement is never
  replaced again
  - E.g., with `02 -> 03` and `03 -> 04`, the name `Lesson02.01_X.smd` becomes
    `Lesson03.01_X.smd` and not `Lesson04.01_X.smd`
- Replace whole names only, never a bare `L02` or `Lesson02`
- Edit only the references listed in the approved `## File References` items
  - Do not touch the other text of a file, including the cells and outputs of a
    notebook
- For a `.ipynb`, edit the source text of the notebook and its paired `.py` the
  same way, so that the pair stays in sync

## Finish

- Format the file:
  ```bash
  > lint_text.py -i <BOOK_MAP>
  ```
- Show the user a diff summary: renumbered chapters, moved chapters, renamed
  files, and anything left open

# Constraints

- Do not edit `<BOOK_MAP>` or rename a file before the user approves the plan
- Do not change the text of a chapter except: its `## <NN>:` heading, its
  chapter-number cross references, and the explicit edits in an approved item
- Do not rename a file or directory outside `<BOOK>/lectures_source/` and
  `<BOOK>/tutorials/`
- Do not rename a file that is `uncertain` or not matched to a chapter
- Do not change the content of a lecture or tutorial file, except the references
  to renamed files in an approved item
- Do not delete a lecture or tutorial file
- Do not delete a chapter, a topic, or a Lesson Materials bullet without an
  explicit approval for that deletion
- Do not guess coverage percentages: they must stay grounded in the lecture
  files, as per `.claude/skills/book_map.rules.md`
- Do not commit: leave the changes in the working tree
- Do not trust the chapter numbers in the file: the Short TOC order is the
  source of truth

# Examples

- Short TOC with a gap and `?` entries, before
  ```markdown
  ### Data engineering
  - 04,:Data engineering
  - ?: News, Filings, Earnings Calls
  - ?: Auto EDA

  ### Prediction and Portfolio Construction
  - 05, Forecasting
  - 06, Limit Order Book Modeling
  ```
- After (nested bullets, `?` replaced, consecutive numbers)
  ```markdown
  - Data Engineering
    - 04: Data Engineering
    - 05: News, Filings, Earnings Calls
    - 06: Auto EDA
  - Prediction and Portfolio Construction
    - 07: Forecasting
    - 08: Limit Order Book Modeling
  ```
- Plan items
  ```markdown
  ## Renumbering
  - [ ] 1. `## 05: Price and Volatility Forecasting` -> `## 07: Forecasting`
        (line 561): Short TOC position 7
  - [ ] 2. `## 08: News, Filings, Earnings Calls` -> `## 05` (line 860)

  ## Reordering
  - [ ] 3. Move `## 05` (lines 561-690) after `## 06` (line 1012)

  ## Chapters Without a Short TOC Entry
  - [ ] 4. `## 10: Conversational Finance Assistants` (line 1012) appears in the
        Short TOC only as a sub-bullet of `News, Filings, Earnings Calls`

  ## Lecture Files
  - [ ] 5. Chapter `05 -> 07`, `<BOOK>/lectures_source/`
    - `Lesson05.01_Forecasting.smd` -> `Lesson07.01_Forecasting.smd`
    - `figures/L05.01.Drawdown.png` -> `figures/L07.01.Drawdown.png`

  ## Tutorials
  - [ ] 6. Chapter `05 -> 07`, `<BOOK>/tutorials/`
    - `L05_forecasting/` -> `L07_forecasting/`
    - `L05_forecasting/L05_01_forecasting.ipynb` ->
      `L07_forecasting/L07_01_forecasting.ipynb`
    - `L05_forecasting/L05_01_forecasting.py` ->
      `L07_forecasting/L07_01_forecasting.py`
    - `L05_forecasting/L05_01_forecasting_utils.py` ->
      `L07_forecasting/L07_01_forecasting_utils.py`

  ## File References
  - [ ] 7. `book_map.md:145`: `Lesson05.01_Forecasting.smd` ->
        `Lesson07.01_Forecasting.smd`
  - [ ] 8. `L07_01_forecasting.py:12`: `import L05_01_forecasting_utils` ->
        `import L07_01_forecasting_utils`
  ```

# Verification

- [ ] Confirm `plan-book_map.update.md` exists and lists every chapter, with
      its `old -> new` number
- [ ] Confirm no edit to `<BOOK_MAP>` was made before the user approved the plan
- [ ] Confirm the chapter numbers are consecutive and zero-padded, starting at
      `01`, with no `?` left in the Short TOC
- [ ] Confirm the order of `## <NN>:` headings in `# Detailed TOC` equals the
      order of the chapters in `## Short TOC`
- [ ] Confirm the `# Part` headings and the Roadmap part rows have the same
      names and order as the Short TOC parts
- [ ] Confirm the Roadmap rows have the same numbers and titles as the
      `## <NN>:` headings
- [ ] Confirm the diff only moves chapter blocks and edits headings, table
      rows, cross references, and the Short TOC
      ```bash
      > git diff --stat <BOOK_MAP>
      ```
- [ ] Confirm no prose reference to a chapter uses an old number
- [ ] Confirm every file and directory under `<BOOK>/lectures_source/` and
      `<BOOK>/tutorials/` that embeds a chapter number has the number of its
      chapter in the final `## <NN>:` order
- [ ] Confirm Git sees the moves as renames, not as delete plus add
      ```bash
      > git status --short <BOOK>
      ```
- [ ] Confirm no `tmp.*` path is left under `<BOOK>`
- [ ] Confirm no old name is left in the repo
      ```bash
      > grep -rF "<old name>" .
      ```
- [ ] Confirm each tutorial `.ipynb` has a paired `.py` with the same base name,
      and that the `import` lines in the renamed `.py` files resolve
      ```bash
      > python -I -m py_compile <BOOK>/tutorials/L<NN>_<title>/*.py
      ```
- [ ] Confirm `lint_text.py -i <BOOK_MAP>` completes without errors
