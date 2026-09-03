// Template for a UMD Typst chapter. See the rules in
// `.claude/skills/typst.rules.md` for why/when; this file is only the
// copy-paste skeleton.
//
// Compile:  dev_scripts_helpers/typst/run_typst.py --input <this file>
// Lint:     typstyle --inplace --wrap-text -l 80 <this file>

// Import AIMA style formatting and macros.
#import "/helpers_root/dev_scripts_helpers/typst/aima_style.typ": (
  aima-style, algorithm, chapter, glossary, styled-table, wrap-content,
)
// Import the custom citation/bibliography system.
#import "/helpers_root/dev_scripts_helpers/typst/umd_references.typ": (
  cite, references,
)

// Document metadata.
#set document(
  title: "Example Chapter",
  author: "MSML610: Advanced Machine Learning",
)

// Apply the AIMA document template (page/text/heading set + show rules).
#show: aima-style

// Unnumbered chapter (one `.typ` file per lesson): `#chapter(3, "Title")`
// instead for one chapter of a single larger numbered book.
#chapter("Example Chapter")

// `#` (H1) in the source becomes a bold paragraph, not a heading: the
// `#chapter(...)` call above already carries the document's top title.
#strong[Introduction]

Lead with intuition before formalism. Use #strong[text] only for the term
or claim being defined; use #emph[text] for other emphasis. Decide by role
in the sentence, checking the source `.smd`'s bold/italic as a signal, not
a literal template: bold a named concept that anchors its own paragraph
even if the source left it untagged, but demote a source bullet's bold
lead-in claim to `#emph` when it isn't itself being defined (see
`typst.rules.md`).

// `##` (H2) in the source.
== Key Methods

// A slide-level (`*Heading*`) marker also becomes a bold paragraph.
#strong[Mathematical Content]

Inline math uses native Typst syntax, never LaTeX command names:
`$f(n) = g(n) + h(n)$`. A single variable mentioned in prose uses a
Unicode character instead of math mode: parameter θ, not `$\theta$`.

Display math stands on its own line:

$ Y_t = beta_0 + beta_1 t + beta_2 D_t + beta_3 (t - t_0) D_t + u_t $

#algorithm(
  "Algorithm Name",
  [
    *Input:* description of input parameters \
    #h(1em) *for* each iteration *do* \
    #h(2em) perform operation \
    #h(1em) *return* result \
    *Output:* description of result
  ],
)

=== Figures and Tables

// Every caption below is one line, plain (no bold), sentence case (not
// Title Case), and states what the visual shows — never a restatement of
// its labels (see `typst.rules.md`).

// A multi-element diagram (flowchart, mind map, ...) is a bare figure at
// 70%+ width, never squeezed into `wrap-content` (see `typst.rules.md`).
#figure(
  image("figures/example-diagram.png", width: 100%),
  caption: [What the diagram shows and why it matters.],
  kind: "figure",
  supplement: [Fig.],
  placement: auto,
) <fig:example-diagram>

Paragraph text discussing the diagram, referencing it as
@fig:example-diagram.

// A single-subject image (a portrait, a photo) pairs with its paragraph
// via `wrap-content`; the second `columns` width is never below 30%. The
// paragraph must carry enough text to run the full height of the image —
// a one-sentence blurb next to a tall portrait leaves a blank gap below
// the text while the image continues alone beside it.
#wrap-content(
  [
    #figure(
      image("figures/example-portrait.jpg", width: 100%),
      caption: [Description of the subject.],
      kind: "figure",
      supplement: [Fig.],
      placement: auto,
    ) <fig:example-portrait>
  ],
  align: right,
  column-gutter: 1em,
  columns: (1fr, 30%),
)[
  Paragraph text that wraps around the figure, referencing it as
  @fig:example-portrait. Keep discussing the subject for a sentence or
  two more — context, why it matters, what follows — so the text runs
  alongside the image instead of stopping a few lines in.
]

// A narrow table (2-3 short columns, single-word cells) pairs with its
// paragraph via `#grid`, same as `wrap-content` but for a rectangular
// block instead of something text should reflow around.
#grid(
  columns: (1fr, 45%),
  column-gutter: 1em,
  align: (left, top),
)[
  Paragraph text discussing the table, referencing it as
  @tab:example-table.
][
  #figure(
    styled-table(
      headers: ("Header 1", "Header 2", "Header 3"),
      rows: (
        ("Row 1 Col 1", "Row 1 Col 2", "Row 1 Col 3"),
        ("Row 2 Col 1", "Row 2 Col 2", "Row 2 Col 3"),
      ),
      bold-first-col: true,
    ),
    caption: [What the table compares.],
    kind: "table",
    supplement: [Table.],
    placement: auto,
  ) <tab:example-table>
]

// A wide table (4+ columns, or any multi-word cell value) is a bare,
// full-width figure instead — never `#grid`/`wrap-content`.
// `styled-table`'s columns share the container width equally, so
// squeezing several of them into a narrow side column forces long cell
// text to wrap letter-by-letter (see `typst.rules.md`). A table figure
// may use `width: 100%`; there's no reason to leave one narrower.
#figure(
  styled-table(
    headers: ("Metric", "2010", "2019", "2026", "Growth"),
    rows: (
      ("AI papers", "1,000", "20,000", "60,000", "60x"),
      ("Enrollment", "10,000", "50,000", "120,000", "12x"),
    ),
    bold-first-col: true,
  ),
  caption: [Growth of AI activity across four benchmarks, 2010-2026.],
  kind: "table",
  supplement: [Table.],
  placement: auto,
) <tab:example-wide-table>

Paragraph text discussing the wide table, referencing it as
@tab:example-wide-table.

== Conclusion

#strong[Summary]

- Point 1: first key insight
- Point 2: second key insight

// End every chapter that cites sources with the references section.
== References

#references("/msml610/lectures_source/refs.bib")
