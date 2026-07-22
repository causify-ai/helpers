// AIMA-style formatting template
// Reusable style configuration for textbook chapters
//
// Usage:
//   #import "aima_style.typ": aima-style, chapter, algorithm, glossary, chapter-intro
//   #show: aima-style
//   #chapter("3", "Title")
//
// NOTE: the page/text/heading `set` and `show` rules MUST live inside the
// `aima-style` template applied via `#show: aima-style`. A plain `#import`
// does not apply a module's top-level set/show rules to the importing
// document, which is why these rules cannot sit at module top level.

// Color definitions (AIMA palette)
#let aima-purple = rgb("#8B7BA8")
#let aima-maroon = rgb("#8B3A62")
#let aima-blue = rgb("#0066CC")
#let aima-gray = rgb("#F0F0F0")

// Document-wide template: apply with `#show: aima-style`
#let aima-style(body) = {
  // Page and text configuration
  set page(
    margin: (left: 1.2in, right: 1.2in, top: 0.85in, bottom: 0.85in),
    header: context {
      let page-num = counter(page).get().first()
      if page-num > 2 [
        #set text(size: 8.5pt, fill: black)
        #if page-num == 3 {
          [Chapter 1 Introduction]
        } else {
          [Section 1.1 What Is AI?]
        }
        #h(1fr)
        #page-num
      ]
    },
  )

  set text(font: "CMU Sans Serif", size: 9.5pt, lang: "en")
  //set text(font: "Times New Roman", size: 9.5pt, lang: "en")
  set par(justify: true, leading: 0.6em)
  set heading(numbering: "1.1.1")

  // Configure heading styles
  show heading: it => {
    // counter(heading).at(it.location()) works without `context` and reflects
    // the heading's own auto-incremented number (no manual stepping).
    let nums = counter(heading).at(it.location())
    if it.level == 2 {
      block(spacing: 0.5em)[
        #v(0.8em)
        #set text(size: 11pt, weight: "bold", fill: aima-maroon)
        #numbering("1.1", ..nums)
        #h(0.4em)
        #it.body
        #v(0.15em)
        #line(length: 100%, stroke: 1.2pt + aima-maroon)
        #v(0.4em)
      ]
    } else if it.level == 3 {
      block(spacing: 0.6em)[
        #v(0.6em)
        #set text(size: 10pt, weight: "bold", fill: aima-maroon)
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
#let chapter(num, title) = {
  pagebreak()

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
