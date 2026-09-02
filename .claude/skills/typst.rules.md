# Document Structure

## Boilerplate and Imports

- Every `.typ` chapter starts with the same boilerplate, in this order: the AIMA
  style import, the citation import, `#set document(...)` metadata,
  `#show: aima-style`, then a single `#chapter(...)` call
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

- A source Markdown heading level maps to Typst as follows:
  - `#` (H1) → `#strong[Title]`, a bold paragraph, not a section heading —
    `#chapter(...)` already carries the document's top-level title, so a body-level
    H1 would just be a redundant second title
  - `##` (H2) → `== Title`
  - `###` (H3) → `=== Title`, and deeper levels continue with one more `=` each
  - A slide-level heading (a `*Heading*` line in the `.smd` source) also becomes
    `#strong[Heading]`, followed by its body text as a paragraph: it is a subsection
    label, not a real Typst heading
- **Bad** (repeats the chapter title as a section, and skips the bold-paragraph form
  for a plain H1):

  ```typst
  #chapter("Brief History of AI")
  = Brief History of AI
  ```

- **Good**:

  ```typst
  #chapter("Brief History of AI")
  == Origins and Early AI (1943-1990)
  #strong[The Beginning (1943-1956)]
  ```

# Text Formatting

## Highlighting and Emphasis

- `#strong[...]` (or native `*text*`) is for the term or claim being formally defined
  or named for the first time, usually in a sentence shaped like "#strong[Term]
  is/refers to/means ...". Use it sparingly: a handful of times per section, never
  for a list item's lead phrase
- `#emph[...]` (or native `_text_`) is for everything else marked for emphasis: a
  bold list-item lead phrase from the source, a term already defined earlier and
  mentioned again, or rhetorical emphasis
- Decide `#strong` vs `#emph` by the role the phrase plays in the sentence, not by
  mechanically mapping the source's markdown (`**bold**` does not automatically mean
  `#strong`)
- Prefer the function form (`#strong[...]`, `#emph[...]`) over the native shorthand
  (`*...*`, `_..._`) for any phrase containing an underscore, hyphen, or other
  punctuation: Typst's shorthand delimiters look for the next matching character and
  misparse around it. Plain single/multi-word phrases with no such characters may use
  either form
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
    citation/author name plain (or in `#cite(...)`): never swap them so the person's
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
- Always use native Typst math syntax, never LaTeX command names, inside `$...$`:
  | LaTeX             | Typst                |
  | ----------------- | -------------------- |
  | `\subseteq`       | `subset.eq`          |
  | `\in`             | `in`                 |
  | `\prod`           | `product_(i=1)^n`    |
  | `\sum`            | `sum_(...)`          |
  | `\arg\min`        | `arg min_(...)`      |
  | `\mathcal{D}`     | `cal(D)`             |
  | `\leq`, `\geq`    | `lt.eq`, `gt.eq`     |
  | `\to`, `\gets`    | `arrow.r`, `arrow.l` |
  | `\cdot`, `\times` | `dot.op`, `times`    |
  | `\infty`          | `oo`                 |
  | `\|x\|`           | `\|x\|` (unchanged)  |
- For a single variable mentioned inline in prose (not a full formula), use a Unicode
  character instead of math mode, to avoid Pandoc mangling a `$\theta$` into stray
  characters: θ, α, β, μ, σ, ∈, ⊆, ∪, 𝒟, 𝒢, ℝ, 
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
  package) only for a single-subject image: a portrait, a photo, one icon: paired
  with the paragraph(s) discussing it, so the text flows beside it
- A rendered diagram: a `graphviz`/`mermaid`/`tikz`/... figure with multiple labeled
  nodes, boxes, or arrows (a flowchart, mind map, architecture diagram, timeline,
  etc.): must NOT be squeezed into a `#wrap-content` side column: at the 30-45%
  width that column allows, its node labels become too small to read. Give it a bare
  `#figure(...)` instead (no wrapping, `width: 70%` or more; see "Sizing" below),
  even though this means it no longer sits directly beside one paragraph
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

- **Good** (the same diagram, full width; a single-subject photo still uses
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
  - **Bad** (multi-line, bold, restates every node label):

    ```typst
    caption: [Diagram relating #strong[Reunification], #strong[Contributing
      fields] and #strong[Reunified subfields]],
    ```

  - **Good**:

    ```typst
    caption: [Fields that converged into the reunified AI research agenda.],
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

## Sizing: Minimum Width and Readability

- Every visual must be legible at its printed size, not merely present. The minimum
  on-page width depends on which construct it uses:
  - `wrap-content`'s `columns: (1fr, <width>)`, for a single-subject image: `<width>`
    must never go below **30%**, even for a narrow portrait photo
  - A bare `#figure(...)`, for a multi-element diagram or a wide table (see "Every
    Visual Pairs With Its Text" above): `width:` must be **70%** or more: the whole
    reason it isn't in `wrap-content` is that its detail needs more room than that
    column allows
- Pick the exact width within that floor to roughly match the figure's aspect ratio
  (e.g. `30%` for a portrait, `80–100%` for a wide diagram or timeline)
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
  via `#grid` per "Every Visual Pairs With Its Text" above. A wide table: 4+
  columns, or any column with multi-word cell values: stays a bare, full-width
  `#figure(...)` per the same section's exception; a table `#figure` may use
  `width: 100%`, there is no reason to leave one narrower
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
