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
or claim being defined; use #emph[text] for other emphasis.

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

// Every visual pairs with the text that discusses it: `wrap-content` for
// a figure/diagram, `grid` for a table (see `typst.rules.md`). The
// second `columns` width is never below 30%.
#wrap-content(
  [
    #figure(
      image("figures/example.png", width: 100%),
      caption: [Description of what the figure shows and its relevance.],
      kind: "figure",
      supplement: [Fig.],
      placement: auto,
    ) <fig:example-diagram>
  ],
  align: right,
  column-gutter: 1em,
  columns: (1fr, 30%),
)[
  Paragraph text that wraps around the figure, referencing it as
  @fig:example-diagram.
]

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
    caption: [Table description explaining contents and purpose.],
    kind: "table",
    supplement: [Table.],
    placement: auto,
  ) <tab:example-table>
]

== Conclusion

#strong[Summary]

- Point 1: first key insight
- Point 2: second key insight

// End every chapter that cites sources with the references section.
== References

#references("/msml610/lectures_source/refs.bib")
