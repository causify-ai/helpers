---
description: Fix heading levels and merge slide-title labels into transition prose in a generated Typst book chapter, to match its .smd source's heading/slide structure
model: sonnet
---

# Goal

- Given a lecture's `.smd` source and the `.typ` book chapter generated from it (by
  `gen_book_chapter.py --mode typst_aima`), fix the chapter's heading levels and
  slide-title handling to follow the "Structural Hierarchy" rule in
  `.claude/skills/typst.rules.md`
- Most of this is mechanical (moving `=`/`==`/`===` markers), but one part is not:
  a slide title that must become a transition (see Step 3 below) requires rewording
  a sentence, not just replacing a marker. That is the only text this skill is
  allowed to change; everything else in the chapter's prose stays untouched
- This is a fix-up for chapters generated before that rule existed (or that were
  hand-edited inconsistently): running it on a chapter that already follows the rule
  is a no-op

# Inputs

- `<SMD_FILE>`: the lecture source
  - E.g., `msml610/lectures_source/Lesson02.1-A_Map_of_Machine_Learning.smd`
- `<TYP_FILE>`: the generated book chapter for `<SMD_FILE>`
  - E.g., `msml610/book/Lesson02.1-A_Map_of_Machine_Learning.typ`

# Workflow

## Classify Every Heading/slide in `<SMD_FILE>`

- Walk `<SMD_FILE>` top to bottom, collecting every `#`/`##`/`###`(+) heading line
  and every `* Slide Title` line, in source order, with its line number
- Track one running flag, `seen_subheading`, starting `False`: flip it to `True` the
  first time a `##` or deeper heading is seen. Its value _at the point each `_ Slide
  Title`line is reached* (before any`##` on the same line updates it) is what Step 3
  needs for that slide

## Locate the Matching Line in `<TYP_FILE>`

- `<TYP_FILE>` carries a
  ```
  // From: <SMD_FILE>:<line_number> '<marker> <title>'
  // Slide: <title>
  ```
  comment immediately above every heading/slide it was generated from.
  Match each Step 1 entry to its block by that comment (line number + marker), not by
  title text alone — titles can repeat (e.g. a lesson and its own first slide sharing
  a name)
- The heading/title line itself is the next non-comment line after
  `// Slide: <title>`: it may currently be `#strong[Title]`, `= Title` / `== Title`
  / `=== Title`, or missing entirely (the block's paragraph starts right after the
  comment, no title line at all)

## Apply the Rule From `typst.rules.md`

For each block found in Step 2, make its title line match:
- **H1** (`#`), title equal to the chapter title already shown by `#chapter(...)`
  (the common case: one `#` per lesson, and it's the lesson title): delete the title
  line entirely, keep the `// From:`/`// Slide:` comments. If a body-level H1 has
  _different_ text from the chapter title, check whether any `##`/`###` appears
  under it before the next `#` (or end of document): if it owns no nested
  subsections, use `#strong[Title]` instead of deleting it; if it owns nested
  `##`/`###` subsections (e.g. a lesson combining two topics under one chapter
  title, each `# Topic` with its own `##` subsections), keep it a real `= Title`
  heading instead — `#strong` would flatten the tree and make each topic's
  identically-named subsections indistinguishable in the outline. Cross-check with
  `extract_toc_from_txt.py -i <SMD_FILE>` vs `grep "^=" <TYP_FILE>` if unsure
- **`##`/`###`/deeper**: `==`/`===`/... one more `=` per level. Leave alone if
  already correct
- **`* Slide Title`**:
  - `seen_subheading` was `False` at this slide → `= Title`, a real heading (add the
    line if it's missing, replace it if it's currently `#strong[Title]` or a
    transitioned-in paragraph)
  - `seen_subheading` was `True` at this slide, and it is the first slide since that
    heading last appeared (no other `* Slide Title` block has occurred since) →
    drop the title entirely: no `#strong[Title]` line, no added transition. Delete
    a `#strong[Title]` line if present (and the blank line after it) and leave the
    paragraph to open with its own first sentence, directly after the `// Slide:`
    comment
  - `seen_subheading` was `True` at this slide, and at least one other slide has
    already appeared since that heading → drop the title and make the paragraph
    transition in from the previous slide's ending instead of restating the title:
    - Read the previous block's last sentence and this block's first sentence
    - If the previous sentence already reads as a lead-in (a forward reference,
      a rhetorical question the next slide answers, a "this raises the question
      of X" close) and the next paragraph's own opening already picks it up
      naturally, deleting the title line is enough — no new sentence needed
    - Otherwise, prepend one short new sentence (or reword the first clause of the
      existing opening sentence) that connects the two: a callback to the term or
      claim the previous slide ended on, a contrast ("beyond X, a second axis
      is..."), or an explicit bridge. Keep it to one sentence; do not summarize or
      repeat content the paragraph itself is about to say
    - A term the slide is centrally about may still get `#strong[...]`, but inside
      that transition sentence or the paragraph's own first sentence, never as its
      own line
  - Either way, remove the blank line that used to separate the title line from the
    body: the comment block is followed directly by the paragraph, no gap (see the
    "Good" examples in `typst.rules.md`)
Never touch a `#strong[...]`/`#emph[...]` occurring elsewhere in the prose
(mid-paragraph terms, list lead phrases), and never touch any sentence beyond the
first one of a transitioned-in paragraph: only the standalone title lines identified
in Step 2, and the single opening sentence next to them, are in scope

## Verify

- Lint: `typstyle --inplace --wrap-text -l 85 <TYP_FILE>`
- Compile and check the PDF looks right: see
  `.claude/skills/book.fix_rendered_pdf/SKILL.md`
