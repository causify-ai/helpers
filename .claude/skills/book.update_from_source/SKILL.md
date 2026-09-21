---
description: Update a book's content to match changes in its source file
model: opus
---

# Goal
- Given the content of a book in the form of a markdown or tex file `<TARGET>` and
  a source file `<SOURCE>`, find and incorporate the changes from `<SOURCE>` into
  `<TARGET>`

# Workflow

## Read the Version Header
- The file `<SOURCE>` contains a header with the last version, in terms of Git hash
  and timestamp, of the material used to generate the current version of
  `<TARGET>`
  - E.g.,
    ```text
    % git_hash=<GIT_HASH>, timestamp=<TIMESTAMP>
    % <SOURCE>
    ```
  - E.g.,
    ```text
    % git_hash=f15bc6b9, timestamp=2026-07-15 14:41:12 EDT
    % book_springer/lectures_source/Lesson02.1_From_Data_Science_To_Decision_Science.txt
    ```
- Get the diff of `<SOURCE>` since `<GIT_HASH>` once, up front, instead of re-diffing
  piecemeal per section:
  ```bash
  > git diff <GIT_HASH> -- <SOURCE>
  ```

## Incorporate Changes
- Find what changed in `<SOURCE>` from `<GIT_HASH>` to now, and modify `<TARGET>` to
  incorporate those changes
- Follow the same style as `<TARGET>` (e.g., read the corresponding
  `.claude/skills/*.rules.md`)
- `<TARGET>` is allowed to be a superset of `<SOURCE>` (e.g., a `.typ` book chapter
  routinely has headings, diagrams, or explanatory paragraphs that group or expand
  several flat `.smd` slides, per `typst.rules.md`'s "Structural Hierarchy"). When
  `<SOURCE>` drops a heading or a diagram that `<TARGET>` already built on, do not
  delete the corresponding `<TARGET>` content just because it no longer has a direct
  counterpart: only remove it if the diff shows the underlying fact/example was
  itself changed or retracted, not merely reorganized out of the slide deck
- Update the header at the top of `<TARGET>` to the new hash/timestamp once done:
  ```text
  // git_hash=<NEW_GIT_HASH> timestamp=<NEW_TIMESTAMP>
  ```

## Compare Entire Flow
- Make sure the flow of the `<TARGET>` book chapter (in typst, latex, md format)
  follows the flow of the `<SOURCE>`
- E.g., you can run `extract_toc_from_txt.py` on `<SOURCE>` and `<TARGET>` and
  compare
  ```bash
  > extract_toc_from_txt.py -i msml610/lectures_source/Lesson03.3-Non_classical_logics.smd

  > extract_toc_from_txt.py -i msml610/book/Lesson03.3-Non_classical_logics.typ
  ```
- Ensure that the flow of `<TARGET>` is consistent with `<SOURCE>`

## Update Source-Line References
- A `.typ` `<TARGET>` carries a `// From: <SOURCE>:<LINE> '<slide title>'` comment
  above each section, pointing at the exact `<SOURCE>` line it was generated from
- Any edit to `<SOURCE>` above a given slide shifts every later line number: after
  incorporating the changes, re-walk `<TARGET>`'s `// From:` comments top to bottom
  and update each `<LINE>` to match the slide's current position in `<SOURCE>` (grep
  `<SOURCE>` for the slide's `*`/`#` title to find it)

## Update Rendered Images
- When `<SOURCE>`'s diff changes a `graphviz`/`mermaid`/`tikz`/... code block (new
  styling, new nodes, a swapped static image for a rendered diagram, or vice versa),
  carry that same code change into `<TARGET>`'s matching
  `rendered_images:begin`/`rendered_images:end` placeholder (see
  `typst.rules.md`'s "Diagram Placeholders and `wrap-content`")
- Never touch the numbered `.png` filenames
  (`<Chapter>.typ.figs/<Chapter>.<N>.png`) or the figure `#figure(image(...))` calls
  by hand for content that already renders correctly: `render_images.py` regenerates
  both the images and their numbering from the placeholders on the next render
- If a section gains or loses a rendered figure, every later figure's `<N>` shifts;
  after editing the placeholders, grep `<TARGET>` for
  `\.typ\.figs/.*\.[0-9]+\.png` and renumber every `#figure(image(...))` call (and
  its matching `label=`/`caption=` metadata line) sequentially from 1, in document
  order, so the bare `#figure(...)` blocks stay in sync with what the next render
  will produce
- Carry over caption/label wording changes the same way you would prose: if
  `<SOURCE>`'s diff renames or rewords what a diagram depicts, update the figure's
  `caption=`/`caption:` to match, following `typst.rules.md`'s "Figures: Required
  Elements" (sentence case, one plain line, no node-by-node listing)

# Verification
- [ ] Confirm every change in `<SOURCE>` since `<GIT_HASH>` is reflected in
  `<TARGET>`
- [ ] Confirm `<TARGET>` still follows the style of its corresponding
  `.claude/skills/*.rules.md` (`typst.rules.md`, `latex.rules.md`, or
  `markdown.rules.md`, depending on `<TARGET>`'s format)
- [ ] Confirm `<TARGET>` compiles
  - For a `.typ` `<TARGET>`, use `render_book_chapter.py -i <TARGET>` when a working
    Docker/graphviz setup is available
  - As a lighter syntax-only check that doesn't need Docker (and avoids
    `render_book_chapter.py`'s Docker/graphviz image-tagging bug, and its
    side-effect of re-rendering other `.typ` files if a `gen_slides.py --daemon` is
    watching the same book directory), stub out any not-yet-rendered figure PNGs
    and compile directly:
    ```bash
    > typst compile --root . <TARGET> /tmp/check.pdf
    ```
  - After either check, `git status`/`git diff` the whole book directory, not just
    `<TARGET>`, to catch an unintended side effect on a sibling chapter
- [ ] Confirm every `// From: <SOURCE>:<LINE>` comment in `<TARGET>` points at the
  correct, current line in `<SOURCE>`
- [ ] Confirm every figure's numbered `.png` filename is sequential in document
  order with no gaps or duplicates
