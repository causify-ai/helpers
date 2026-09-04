---
description: Fix heading levels in a generated Typst book chapter to match its .smd source's heading/slide structure
model: sonnet
---

# Goal

- Given a lecture's `.smd` source and the `.typ` book chapter generated from it
  (by `gen_book_chapter.py --mode typst_aima`), fix the chapter's heading levels
  to follow the "Structural Hierarchy" rule in `.claude/skills/typst.rules.md`,
  without changing any other text
- This is a fix-up for chapters generated before that rule existed (or that
  were hand-edited inconsistently): running it on a chapter that already
  follows the rule is a no-op

# Inputs

- `<SMD_FILE>`: the lecture source
  - E.g., `msml610/lectures_source/Lesson02.1-A_Map_of_Machine_Learning.smd`
- `<TYP_FILE>`: the generated book chapter for `<SMD_FILE>`
  - E.g., `msml610/book/Lesson02.1-A_Map_of_Machine_Learning.typ`

# Workflow

## Step 1: Classify every heading/slide in `<SMD_FILE>`

- Walk `<SMD_FILE>` top to bottom, collecting every `#`/`##`/`###`(+) heading
  line and every `* Slide Title` line, in source order, with its line number
- Track one running flag, `seen_subheading`, starting `False`: flip it to
  `True` the first time a `##` or deeper heading is seen. Its value *at the
  point each `* Slide Title` line is reached* (before any `##` on the same
  line updates it) is what Step 3 needs for that slide

## Step 2: Locate the matching line in `<TYP_FILE>`

- `<TYP_FILE>` carries a `// From: <SMD_FILE>:<line_number> '<marker>
  <title>'` comment immediately above every heading/slide it was generated
  from, followed by a `// Slide: <title>` comment. Match each Step 1 entry to
  its block by that comment (line number + marker), not by title text alone —
  titles can repeat (e.g. a lesson and its own first slide sharing a name)
- The heading/title line itself is the next non-comment line after `//
  Slide: <title>` — it may currently be `#strong[Title]`, `= Title` /
  `== Title` / `=== Title`, or missing entirely (blank line straight after
  the comment)

## Step 3: Apply the rule from `typst.rules.md`

For each block found in Step 2, make its title line match:

- **H1** (`#`), title equal to the chapter title already shown by
  `#chapter(...)` (the common case: one `#` per lesson, and it's the lesson
  title): delete the title line entirely, keep the `// From:`/`// Slide:`
  comments. If a body-level H1 has *different* text from the chapter title,
  use `#strong[Title]` instead of deleting it
- **`##`/`###`/deeper**: `==`/`===`/... one more `=` per level. Leave alone if
  already correct
- **`* Slide Title`**:
  - `seen_subheading` was `False` at this slide → `= Title`, a real heading
    (add the line if it's missing, replace it if it's currently
    `#strong[Title]`)
  - `seen_subheading` was `True` at this slide → `#strong[Title]` (add the
    line if missing, replace if currently a `=`/`==`/`===` heading)

Never touch a `#strong[...]`/`#emph[...]` occurring elsewhere in the prose
(mid-paragraph terms, list lead phrases): only the standalone title lines
identified in Step 2.

## Step 4: Verify

- Lint: `typstyle --inplace --wrap-text -l 80 <TYP_FILE>`
- Compile and check the PDF looks right: see
  `.claude/skills/book.fix_rendered_pdf/SKILL.md`
