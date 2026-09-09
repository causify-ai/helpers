# Document Structure

## Boilerplate and Imports

- Every `.typ` chapter starts with the same boilerplate, in this order
  - the AIMA style import
  - the citation import
  - `#set document(...)` metadata,
  - `#show: aima-style`
  - a single `#chapter(...)` call
- Follow the template `.claude/templates/typst.template.typ`
- Import both shared modules with a root-absolute path (resolved against
  `typst compile --root`), never a relative `../../` path: a relative path breaks as
  soon as the `.typ` file moves to a different directory depth:

  ```typst
  #import "/helpers_root/dev_scripts_helpers/typst/aima_style.typ": (
    aima-style, algorithm, chapter, glossary, styled-table, wrap-content,
  )
  #import "/helpers_root/dev_scripts_helpers/typst/umd_references.typ": (
    cite, references,
  )
  ```

- Only import the names actually used, but expect `wrap-content` and `styled-table`
  in almost every chapter (see "Visuals" below)
- `#set document(title: ..., author: ...)` uses the chapter/lesson title and the
  course title; `title` should match what `#chapter(...)` shows

## The `#chapter(...)` Call

- `#chapter("Title")` (one argument): an unnumbered chapter: shows `Title` directly
  in the purple bar, no counter reset. Use this for a standalone lesson chapter (one
  `.typ` file per lesson, the normal case in this repo)
- `#chapter(3, "Title")` (two arguments): a numbered chapter: shows "CHAPTER 3" with
  `Title` below it, and resets the heading counter so sections number `3.1`, `3.2`,
  ... Use this only when the `.typ` file is one chapter of a single larger numbered
  book
- Call `#chapter(...)` exactly once, right after `#show: aima-style`; never call it a
  second time for a second top-level topic in the same file

## Structural Hierarchy

- A `.typ` chapter's heading tree must contain every heading and slide title from
  its source `.smd`, in the same order and at the same relative nesting
  - An `.smd` `#`/`##`/`###`(+) heading maps to a `.typ` `=`/`==`/`===`(+) heading,
    one level of `=` per level of `.smd` nesting
- The `.typ` file is allowed a *more* complex hierarchy than the `.smd`
  - Extra `===`/deeper subsections that group several flat `.smd` slides under a
    label the source never spelled out
  - The `.typ` outline is always a superset of the `.smd` outline, never a subset:
    every `.smd` heading/slide still needs a matching `.typ` heading somewhere in the
    tree, but the `.typ` tree may add levels the `.smd` never had
- Compare the two outlines with `extract_toc_from_txt.py` before/after any
  structural edit rather than guessing:

  ```bash
  > extract_toc_from_txt.py -i msml610/lectures_source/Lesson01.2*smd
  - What Is Intelligence? What is AI?
  - What Is Machine Learning?

  > extract_toc_from_txt.py -i msml610/book/Lesson01.2*typ
  - Roadmap
  - What Is Intelligence? What is AI?
    - ML, AI, and Intelligence
      - A Formal Definition of AI
      - AI as Thinking Humanly
      - AI as Thinking Rationally
      - AI as Acting Humanly
      - AI as Acting Rationally
      - Acting Rationally as Ultimate Goal of AI
  - What Is Machine Learning?
  - Summary
  - References
  ```

- The `.typ` side nests `ML, AI, and Intelligence` and its six `===` subsections
  under a heading the flat `.smd` slide list never grouped that way, and adds
  `Roadmap`/`Summary`/`References` (see below). Both of the `.smd`'s own headings
  (`What Is Intelligence? What is AI?`, `What Is Machine Learning?`) still appear
  at the matching top level
- A heading is always real Typst heading syntax, `=`/`==`/`===`(+): never
  `#strong[Title]` sitting alone on its own line standing in for a heading.
  `#strong[...]` renders bold text, not a heading: it is invisible to the
  outline, to cross-references, and to `extract_toc_from_txt.py`, so it hides the
  document's real structure from every tool that reads it
  - **Bad** (fake heading, doesn't show up in the outline):

    ```typst
    #strong[ML, AI, and Intelligence]

    Machine Learning is a subset of Artificial Intelligence (AI). ...
    ```

  - **Good**:

    ```typst
    == ML, AI, and Intelligence

    Machine Learning is a subset of Artificial Intelligence (AI). ...
    ```

  This bans only a standalone `#strong[...]` line playing the role of a heading;
  `#strong[...]`/`#emph[...]` remain correct for inline emphasis inside prose (see
  "Highlighting and Emphasis" below)

## Mandatory Sections

- Every chapter has exactly three mandatory level-1 (`=`) sections, in this
  order:
  - `= Roadmap` right after `#chapter(...)`, before the first content
  section
  - `= Summary`
  - `= References` at the end
  - All three are required even when the `.smd` has no slide by that exact name:
    normalize whatever the source calls its opening/closing slide (`Overview`,
    `Outline`, `Agenda`, `Key Takeaways`, `Conclusion`, `Wrap-up`, ...) to `Roadmap`
    / `Summary`, and write the section from scratch when the `.smd` has no such slide
    at all. Keep the `// Slide: <original title>` comment above the heading either
    way, for traceability back to the source

# Text Formatting

## Highlighting and Emphasis

- `#strong[...]` is for the term or claim being formally defined or named for the
  first time, usually in a sentence shaped like "#strong[Term] is/refers to/means
  ...". Use it sparingly: a handful of times per section, never for a list item's
  lead phrase
- `#emph[...]` is for everything else marked for emphasis: a bold list-item lead
  phrase from the source, a term already defined earlier and mentioned again, or
  rhetorical emphasis
- Decide `#strong` vs `#emph` by the role the phrase plays in the sentence, not by
  mechanically mapping the source's markdown (`**bold**` does not automatically mean
  `#strong`)
- Always use the function form (`#strong[...]`, `#emph[...]`) over the native shorthand
  (`*...*`, `_..._`)
- Never leave Markdown-only syntax that has no meaning in Typst body text:
  `**double-star bold**`, `~~strikethrough~~`, or a lone `*`/`_` used the Markdown
  way: Typst renders these as literal punctuation, not emphasis
- A plain quoted phrase (`"..."`) stays a plain quoted string: never prefix it with
  `#`: `#"text"` is a Typst string _expression_ and drops the visible quote marks

- Cross-check against the source `.smd` when deciding `#strong` vs `#emph`, but apply
  the role-based test above rather than copying its markdown verbatim:
  - A term that anchors its own paragraph and is being named for the first time (the
    source's `@Term@` tag, or a `**Term**: definition` bullet whose lead phrase _is_
    the paragraph's subject) is `#strong`, even where the source left it untagged or
    merely bold. Three sibling concepts each introduced this way (e.g. a "King Midas
    problem" / "problem of alignment" / "paperclip problem" trio) should get the same
    treatment for consistency
  - A source `**bold**` that is only a bullet's lead-in claim, not a term being
    defined (e.g. "True step towards **general artificial intelligence**" when AGI is
    properly defined later), becomes `#emph`, not `#strong`
  - When a source line pairs a bold term with an italic citation, e.g
    `**Reinforcement Learning** _(Sutton, 1988)_`, bold the term and leave the
    citation/author name plain or in `#cite(...)`: never swap them so the person's
    name ends up emphasized and the term plain
  - A term already `#strong`-defined earlier and mentioned again later (e.g. a
    second, separate reference to "narrow AI" after "Weak AI ... aka narrow AI" was
    defined) becomes `#emph`, not left unstyled
  - Every italicized phrase in a source bullet carries over: don't drop one of a pair
    (e.g. source italicizes both `_weak methods_` and `_extensive domain knowledge_`
    — carry both into `#emph`, not just the first)

## Typst Vs. Markdown Syntax

- Always close every `#strong[`, `#emph[`, `[...]`, and `(...)` opened
- Never copy pandoc-only wrapping into a `.typ` file: strip a ` ```{=typst} ... ``` `
  fence or an inline `` `code`{=typst} `` span down to the bare Typst code it
  contains: the output document is already native Typst, so that wrapping is inert
  literal text there
- The `@` character is Typst label-reference syntax (`@fig:label` renders as an
  auto-numbered cross-reference). A literal `@word` left over from source annotation
  conventions is a compile error, not a style nit: never leave one verbatim in a
  `.typ` file

# Math

## Formulas

- Inline text-like expression: `` `formula` `` (e.g., `` `f(n) = g(n) + h(n)` ``);
  inline math: `$formula$`
- Display math (standalone formula): `$ formula $` on its own line, or a raw Typst
  code block (` ```{=typst} ... ``` `) when the formula must bypass Pandoc conversion
- Always use native Typst math syntax, never LaTeX command names, inside `$...$`: |
  LaTeX | Typst | | ----------------- | -------------------- | | `\subseteq` |
  `subset.eq` | | `\in` | `in` | | `\prod` | `product_(i=1)^n` | | `\sum` |
  `sum_(...)` | | `\arg\min` | `arg min_(...)` | | `\mathcal{D}` | `cal(D)` | |
  `\leq`, `\geq` | `lt.eq`, `gt.eq` | | `\to`, `\gets` | `arrow.r`, `arrow.l` | |
  `\cdot`, `\times` | `dot.op`, `times` | | `\infty` | `oo` | | `\|x\|` | `\|x\|`
  (unchanged) |
- Keep a formula single-line when possible; a multi-line formula is more likely to
  break Typst's line-wrapping in the `wrap-content` narrow column (see "Visuals"
  below)

# Algorithms and Pseudocode

- Use `#algorithm("Name", [...])` for any structured algorithm or procedure, never a
  bare code block or list
- Use `*keyword*` (native strong) for language keywords (`function`, `if`, `loop`,
  `return`, ...) and `#h(1em)` per indentation level inside the algorithm body

# Lists

- Not every `-` bullet in a source is a real list: a single tagged bullet holding one
  short point (e.g. a lone `@Definition@` or `@Remark@` item) becomes a plain
  sentence in the surrounding paragraph instead of a list item
- Keep a real Typst list only for content meant to be scanned as parallel items: an
  enumerated set of steps, assumptions, properties, or named alternatives
- For a list that is kept, Typst uses the same bullet (`- item`) and numbered
  (`1. item`) syntax as Markdown: copy the structure and nesting as-is and convert
  only each item's text

# Visuals

## Every Visual Pairs with Its Text

- A figure, diagram, or image is never left floating on its own, disconnected from
  the paragraph that discusses it
- Use `#wrap-content(...)` (from `aima_style.typ`, re-exporting the `wrap-it`
  package) for a single-subject image (a portrait, a photo, one icon) OR a simple
  diagram with only a handful of labeled elements (roughly 2-4 nodes/points and at
  most one or two edge labels)
  - E.g. a two-box relationship diagram or a tradeoff curve with three labeled points
    both stay legible at 40-50% width
  - Pair it with the paragraph(s) discussing it, so the text flows beside it
- A denser rendered diagram: a `graphviz`/`mermaid`/`tikz`/... figure with many
  labeled nodes, boxes, or arrows (a flowchart with several steps, a mind map, a
  multi-entity knowledge graph, an architecture diagram, a timeline, etc.) must
  NOT be squeezed into a `#wrap-content` side column: at the width that column
  allows, its node labels become too small to read
  - Give it a bare `#figure(...)` instead (no wrapping, `width: 70%` or more; see
    "Sizing" below), even though this means it no longer sits directly beside one
    paragraph
- The dividing line is legibility, not "photo vs diagram": if every label in the
  diagram stays comfortably readable at the chosen `wrap-content` width, wrapping
  it is fine. If any label would shrink past comfortable reading size, the diagram
  needs a full-width bare figure instead. When in doubt, compile and look at the
  rendered page rather than guessing from the source
- A table is paired with its paragraph via
  `#grid(columns: (1fr, <width>), column-gutter: 1em, align: (left, top))[prose][table]`
  instead of `#wrap-content`: a table is a rectangular block, not something text
  should reflow around
- A visual stays a bare `#figure(...)` with no `wrap-content` / `grid` pairing
  whenever it must span the full text width to remain readable: a multi-element
  diagram (per above), a wide multi-column table, or a multi-panel grid. Say so with
  a short comment when it's a judgment call (e.g
  `// Keep this table full-width: N columns`)
- **Bad** (a multi-node flowchart squeezed into a `wrap-content` side column: its
  labels will be illegible at this width):

  ```typst
  #wrap-content(
    [
      #figure(
        image("figures/agent_loop_diagram.png", width: 100%),
        caption: [The agent-environment interaction loop],
      ) <fig:agentloop>
    ],
    align: right,
    columns: (1fr, 35%),
  )[
    @fig:agentloop shows how an agent perceives, decides, and acts.
  ]
  ```

- **Good** (the same dense diagram, full width; a single-subject photo still uses
  `wrap-content`):

  ```typst
  #figure(
    image("figures/agent_loop_diagram.png", width: 100%),
    caption: [The agent-environment interaction loop.],
    kind: "figure",
    supplement: [Fig.],
    placement: auto,
  ) <fig:agentloop>

  @fig:agentloop shows how an agent perceives, decides, and acts.

  #wrap-content(
    [
      #figure(
        image("figures/L01.4.Alan_Turing.jpg", width: 100%),
        caption: [Alan Turing (1951)],
        kind: "figure",
        supplement: [Fig.],
        placement: auto,
      ) <fig:alanturing>
    ],
    align: right,
    column-gutter: 1em,
    columns: (1fr, 30%),
  )[
    Turing's 1950 paper #cite("turing1950computing") asked whether
    machines can think, as @fig:alanturing's subject first posed it.
  ]
  ```

- **Good** (a simple two-node diagram, not a photo, still fits `wrap-content`: only
  one edge and one label, so it reads fine at 50%):

  ```typst
  #wrap-content(
    [
      #figure(
        image("figures/model_possible_worlds.png", width: 100%),
        caption: [Diagram relating a model to the possible worlds it grounds.],
        kind: "figure",
        supplement: [Fig.],
        placement: auto,
      ) <fig:modelsandpossibleworlds>
    ],
    align: right,
    column-gutter: 1em,
    columns: (1fr, 50%),
  )[
    Each possible world (or model) assigns a truth value to every relevant
    variable, as @fig:modelsandpossibleworlds shows. A model is the formal bridge
    between the abstract notion of "possible world" and the concrete variable
    assignments that ground our reasoning.
  ]
  ```

- The prose paired with a `wrap-content` image must be long enough to run the full
  height of the image column. A single short sentence next to a tall portrait leaves
  a blank gap under the text while the image runs on alone beside it. Write two or
  three real sentences (background, elaboration, a forward reference to what's next),
  not just the one sentence naming the figure. If there genuinely isn't enough to
  say, shrink the image instead of leaving whitespace

## Figures: Required Elements

- Every figure and table needs: a label (`<fig:...>` / `<tab:...>`), a one-line
  caption, and an in-text reference (`@fig:...` / `@tab:...`) that integrates it into
  the prose: never leave one standing with no sentence pointing at it
- A caption is one plain line: never wrap any part of it in `#strong[...]` / `*...*`,
  and never list out every node or label the figure contains: say what the figure
  shows in a single short clause and let the reader look at the image for specifics
- Write a caption in sentence case: capitalize only the first word and proper nouns,
  never Title Case every word. This applies even when the caption names concepts that
  are capitalized elsewhere (a figure title, a heading, a source label): lowercase
  them into the sentence unless they're proper nouns or acronyms
  - **Bad** (multi-line, bold, restates every node label):

    ```typst
    caption: [Diagram relating #strong[Reunification], #strong[Contributing
      fields] and #strong[Reunified subfields]],
    ```

  - **Bad** (Title Case instead of sentence case):

    ```typst
    caption: [Diagram Relating Learning Paradigms, Label Availability and
      Interactive/Sequential],
    ```

  - **Good**:

    ```typst
    caption: [Fields that converged into the reunified AI research agenda.],
    ```
    ```typst
    caption: [Diagram relating learning paradigms, label availability and
      interactive/sequential],
    ```

- `placement:` takes a bare keyword (`auto`, `none`, `top`, `bottom`), never a string
  — `placement: "auto"` is a type error
- Write a label as `fig:<description>` / `tab:<description>` in all lowercase with no
  separators (`fig:alanturing`, not `fig:Alan_Turing` or `fig:alan-turing`)
- Image paths are relative to the `.typ` file's own location (use `../` to reach a
  sibling directory such as `lectures_source/figures/`)
- Never invent a `#figure(image(...))` call for a diagram
  (`graphviz`/`mermaid`/`tikz`) whose rendered PNG does not exist yet: that path is
  produced later by a separate rendering step; guessing one produces a "file not
  found" compile error. Leave the raw source fence, or its placeholder, exactly as
  given

## Diagram Placeholders and `wrap-content`

- `render_images.py` (run by `render_book_chapter.py` on every render) deletes and
  regenerates everything between its `render_images:begin` / `render_images:end`
  markers from scratch, using the `label=` / `caption=` metadata preserved in the
  paired `rendered_images:begin` / `rendered_images:end` comment block right above
  it. Anything else placed between those markers does not survive a rerun
- When a not-yet-rendered diagram belongs in a `#wrap-content(...)` pairing (per
  "Every Visual Pairs With Its Text" above), nest the whole placeholder — the raw
  fence, its `label=`/`caption=` metadata, and all four
  `rendered_images:begin`/`rendered_images:end`/`render_images:begin`/
  `render_images:end` markers — inside `#wrap-content(...)`'s first `[ ... ]`
  argument (the image slot). Keep the `#wrap-content(...)` call itself, its
  `align:`/`column-gutter:`/`columns:` arguments, and the prose in its trailing
  `)[ ... ]` argument OUTSIDE the markers, never between them
- Putting the markers around the whole `#wrap-content(...)` call instead — so the
  paired prose sits inside `render_images:begin`/`render_images:end` too — means the
  next rerun silently deletes that prose and collapses the two-column layout to a
  bare `#figure(...)`: the regenerated block is always just the figure, never the
  wrapper and prose around it
- Write `label=` and `caption=` as two separate lines, `label=fig:...` then
  `caption=...` directly below it: never combine them on one line
  (`label=fig:x caption=...`). The parser treats everything after the first `=` as
  the label's value, so a combined line produces an invalid Typst label
  (`<fig:x caption=...>`) and an "unclosed label" compile error
- **Bad** (markers wrap the whole `#wrap-content` call; the prose is destroyed the
  next time `render_images.py` runs):

  ```typst
  // rendered_images:begin
  // ```graphviz
  //   ...
  // ```
  // label=fig:example
  // caption=One-line description of the diagram.
  // rendered_images:end
  // render_images:begin
  #wrap-content(
    [
      #figure(
        image("...", width: 100%),
        caption: [...],
        kind: "figure",
        supplement: [Fig.],
        placement: auto,
      ) <fig:example>
    ],
    align: right,
    columns: (1fr, 40%),
  )[
    Prose explaining @fig:example, paired beside it.
  ]
  // render_images:end
  ```

- **Good** (markers nested inside the image slot only; the `#wrap-content(...)` call
  and its prose survive every rerun):

  ```typst
  #wrap-content(
    [
      // rendered_images:begin
      //     ```graphviz
      //       ...
      //     ```
      //     label=fig:example
      //     caption=One-line description of the diagram.
      // rendered_images:end
      // render_images:begin
      #figure(
        image("...", width: 100%),
        caption: [...],
        kind: "figure",
        supplement: [Fig.],
        placement: auto,
      ) <fig:example>
      // render_images:end
    ],
    align: right,
    columns: (1fr, 40%),
  )[
    Prose explaining @fig:example, paired beside it.
  ]
  ```

## Sizing: Minimum Width and Readability

- Every visual must be legible at its printed size, not merely present. The minimum
  on-page width depends on which construct it uses:
  - `wrap-content`'s `columns: (1fr, <width>)`, for a single-subject image: `<width>`
    must never go below **30%**, even for a narrow portrait photo
  - `wrap-content`'s `columns: (1fr, <width>)`, for a simple diagram with a handful
    of labeled elements (per "Every Visual Pairs With Its Text" above): lean toward
    the upper end of the range, **40-50%**, so its labels stay as readable as a
    photo's caption would be; the 30% floor is for a plain portrait/icon with no
    internal text of its own
  - A bare `#figure(...)`, for a dense multi-element diagram or a wide table (see
    "Every Visual Pairs With Its Text" above): `width:` must be **70%** or more:
    the whole reason it isn't in `wrap-content` is that its detail needs more room
    than that column allows
- Pick the exact width within that floor to roughly match the figure's aspect ratio
  (e.g. `30%` for a portrait, `40-50%` for a simple labeled diagram, `80–100%` for
  a wide or dense diagram or timeline)
- If no width at or above the applicable floor keeps a `wrap-content` figure's own
  content (not just its label) legible, it does not belong in `wrap-content` at all —
  give it a bare full-width figure instead
- **Bad** (Typst compiles this fine, but the figure is unreadable):

  ```typst
  columns: (1fr, 20%),
  ```

- **Good**:

  ```typst
  columns: (1fr, 30%),
  ```

## Tables

- Build a table with
  `styled-table(headers: (...), rows: (...), bold-first-col: false)` from
  `aima_style.typ`, wrapped in `#figure(...)` for its
  caption/label/`kind: "table"`/`supplement: [Table.]`: never Typst's raw
  `table(...)` call directly in chapter body text
- A narrow table (2-3 short columns, single-word cells) is paired with its paragraph
  via `#grid` per "Every Visual Pairs With Its Text" above. A wide table: 4+ columns,
  or any column with multi-word cell values: stays a bare, full-width `#figure(...)`
  per the same section's exception; a table `#figure` may use `width: 100%`, there is
  no reason to leave one narrower
- `styled-table`'s columns share the container width equally (no per-column sizing)
  Squeezing a table with several columns, or with long cell values, into a narrow
  `#grid`/`wrap-content` side column forces its cell text to wrap letter-by-letter
  and become illegible (e.g. "En-roll-ment", "NeurIPS1,000" running together): give
  it a full-width figure instead
  - **Bad** (5-column table crammed into a narrow column):

    ```typst
    #grid(columns: (1fr, 45%), ...)[prose][
      #figure(styled-table(
        headers: ("Metric", "2010", "2019", "2026", "Growth"),
        rows: (("Enrollment", "10,000", "50,000", "120,000", "12x"), ..),
      ), ...)
    ]
    ```

  - **Good** (same table, full width):

    ```typst
    #figure(
      styled-table(
        headers: ("Metric", "2010", "2019", "2026", "Growth"),
        rows: (("Enrollment", "10,000", "50,000", "120,000", "12x"), ..),
      ),
      caption: [Growth of AI activity across four benchmarks, 2010-2026.],
      kind: "table",
      supplement: [Table.],
      placement: auto,
    ) <tab:growth>

    @tab:growth shows enrollment and research output climbing together.
    ```

# Bibliography and Citations

- Never use Typst's native `#bibliography(...)` / `[@key]` citation syntax: it can
  only hyperlink the raw URL/DOI text, not a custom link label. Use the shared
  `umd_references.typ` module instead (already covered by the boilerplate import
  above)
- Cite inline with `#cite("<bib-key>")`, never `[@<bib-key>]`:

  ```typst
  The Turing test #cite("turing1950computing") remains influential.
  ```

- End the references section with:

  ```typst
  #references("/msml610/lectures_source/refs.bib")
  ```
