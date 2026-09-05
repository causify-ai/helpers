// AIMA-style formatting template
// Reusable style configuration for textbook chapters
//
// Usage:
//   #import "aima_style.typ": aima-style, chapter, algorithm, glossary, chapter-intro
//   #show: aima-style
//   #chapter("L01.2: AI and Machine Learning")
//
// NOTE: the page/text/heading `set` and `show` rules MUST live inside the
// `aima-style` template applied via `#show: aima-style`. A plain `#import`
// does not apply a module's top-level set/show rules to the importing
// document, which is why these rules cannot sit at module top level.

// Re-exported so importing files can pull `wrap-content` from this module
// instead of importing the `wrap-it` package directly in every file.
#import "@preview/wrap-it:0.1.1": wrap-content

// Color definitions (AIMA palette)
#let aima-purple = rgb("#8B7BA8")
#let aima-maroon = rgb("#8B3A62")
#let aima-blue = rgb("#0066CC")
#let aima-gray = rgb("#F0F0F0")
#let aima-rust = rgb("#B5654A")
#let aima-gold = rgb("#C9A96E")

// Document-wide template: apply with `#show: aima-style`
#let aima-style(body) = {
  // Page and text configuration
  set page(
    margin: (left: 1.2in, right: 1.2in, top: 0.85in, bottom: 0.85in),
    header: context {
      let page-num = counter(page).get().first()
      if page-num > 1 [
        #set text(size: 8.5pt, fill: black)
        #if page-num == 2 {
          [Chapter 1 Introduction]
        } else {
          [Section 1.1 What Is AI?]
        }
        #h(1fr)
        #page-num
      ]
    },
  )

  set text(font: "CMU Sans Serif", size: 11pt, lang: "en")
  //set text(font: "Times New Roman", size: 11pt, lang: "en")
  set par(justify: true, leading: 0.6em)
  set heading(numbering: "1.1.1")

  // Configure heading styles
  show heading: it => {
    // counter(heading).at(it.location()) works without `context` and reflects
    // the heading's own auto-incremented number (no manual stepping).
    let nums = counter(heading).at(it.location())
    if it.level == 1 {
      // Top-level section: bigger maroon heading with a rule set close to
      // the text.
      block(spacing: 0.6em)[
        #set par(spacing: 0pt)
        #v(0.8em)
        #set text(size: 22pt, weight: "bold", fill: aima-maroon)
        #numbering("1", ..nums)
        #h(0.4em)
        #it.body
        #v(-0.8em)
        #line(length: 100%, stroke: 2pt + aima-maroon)
        #v(0.4em)
      ]
    } else if it.level == 2 {
      // Subsection: lighter color, no rule.
      block(spacing: 0.5em)[
        #v(0.8em)
        #set text(size: 15pt, weight: "bold", fill: aima-rust)
        #numbering("1.1", ..nums)
        #h(0.4em)
        #it.body
        #v(0.4em)
      ]
    } else if it.level == 3 {
      block(spacing: 0.6em)[
        #v(0.6em)
        #set text(size: 10pt, weight: "bold", fill: aima-gold)
        #numbering("1.1.1", ..nums)
        #h(0.4em)
        #it.body
        #v(0.3em)
      ]
    } else {
      it
    }
  }

  body
}

// Chapter heading style (AIMA style)
//
// Two call forms are supported:
// - `#chapter(num, title)`: numbered chapter, e.g. `#chapter(3, "Solving
//   Problems by Searching")`. Shows "CHAPTER <num>" in the purple bar with
//   `title` below it, and resets the heading counter to `num` so that
//   sections number as `num.1`, `num.2`, ...
// - `#chapter(label)`: unnumbered chapter, e.g. `#chapter("L01.2: AI and
//   Machine Learning")`. Shows `label` directly in the purple bar, with no
//   separate title line and no heading-counter reset.
#let chapter(num, ..rest) = {
  let title = rest.pos().at(0, default: none)

  // `weak: true` skips the break when we are already at the top of a page,
  // so calling `chapter()` as the first thing in the document does not
  // leave a blank leading page.
  pagebreak(weak: true)

  if title == none {
    // Single-argument form: `num` is the full chapter label to show as-is.
    // No counter reset: these documents use real level-1 (`=`) headings for
    // their top-level sections, which auto-number 1, 2, 3, ... on their own.
    block(
      fill: aima-purple,
      width: 100%,
      inset: (x: 12pt, y: 10pt),
    )[
      #set text(size: 20pt, weight: "bold", fill: white)
      #num
    ]

    v(0.8em)
  } else {
    // Two-argument form: numbered chapter.
    // Reset heading counter to chapter number
    counter(heading).update((int(num),))

    // Purple header bar with "CHAPTER" label and number
    block(
      fill: aima-purple,
      width: 100%,
      inset: (x: 12pt, y: 10pt),
    )[
      #set text(size: 13pt, weight: "bold", fill: white)
      CHAPTER
      #h(1fr)
      #set text(size: 32pt, weight: "bold")
      #num
    ]

    v(0.5em)

    // Title in burgundy/maroon
    set text(size: 26pt, weight: "bold", fill: aima-maroon)
    [#title]

    v(0.8em)
  }
}

// Margin glossary term
#let glossary(term) = {
  place(
    right,
    dx: 0.3in,
    dy: 0em,
  )[
    #set text(size: 8.5pt, fill: aima-blue, weight: "regular")
    #term
  ]
}

// Algorithm box (AIMA style)
#let algorithm(name, content) = {
  block(
    fill: rgb("#F5F5F5"),
    inset: 10pt,
    radius: 0pt,
    breakable: false,
    stroke: 0.5pt + rgb("#E0E0E0"),
  )[
    #set text(weight: "bold", size: 8pt, font: "CMU Typewriter")
    //#set text(weight: "bold", size: 8pt, font: "Courier New")
    Figure. #name
    #v(0.2em)
    #set text(weight: "regular", size: 7.8pt, font: "CMU Typewriter", fill: black)
    //#set text(weight: "regular", size: 7.8pt, font: "Courier New", fill: black)
    #content
  ]
}

// Styled comparison table (AIMA style)
// - `headers`: array of column header strings
// - `rows`: array of arrays of cell strings, one inner array per row
// - `bold-first-col`: bold the first column of each data row (e.g. a row
//   label)
#let styled-table(headers: (), rows: (), bold-first-col: false) = {
  let ncols = headers.len()
  let header-cells = headers.map(h => table.cell(
    fill: aima-gray,
    [#set text(weight: "bold", size: 8.5pt, fill: aima-maroon)
     #h],
  ))
  let body-cells = rows.map(row => row.enumerate().map(((i, cell)) => {
    if bold-first-col and i == 0 [#strong[#cell]] else [#cell]
  })).flatten()
  table(
    columns: ncols,
    stroke: 0.5pt + rgb("#CCCCCC"),
    inset: 6pt,
    align: left,
    ..header-cells,
    ..body-cells,
  )
}

// Chapter introduction box (AIMA style)
#let chapter-intro(content) = {
  block(
    fill: aima-gray,
    inset: 11pt,
    radius: 0pt,
    width: 100%,
    stroke: 0.5pt + rgb("#CCCCCC"),
  )[
    #set text(size: 9.5pt, style: "italic", fill: black)
    #content
  ]
}
