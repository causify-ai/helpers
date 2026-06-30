// Manning-style formatting template
// Reusable style configuration for textbook chapters
//
// Font Specifications:
//   Base: Times New Roman, 9.5pt
//   Chapter title: Times New Roman, 24pt (italic)
//   Chapter number: Times New Roman, 72pt (bold)
//   Section headings (level 2): Times New Roman, 11pt (bold, italic)
//   Subsection headings (level 3): Times New Roman, 10pt (bold, italic)
//   "This chapter covers" header: Times New Roman, 9.5pt (bold)
//   Chapter intro content: Times New Roman, 9pt (regular)
//   Fact box: Times New Roman, 9.5pt
//   Page header: Times New Roman, 8.5pt
//
// Usage:
//   #import "manning_style.typ": manning-style, chapter, chapter-intro, fact-box, section-heading
//   #show: manning-style
//   #chapter("1", "Probabilistic programming in a nutshell")
//   #chapter-intro[
//     - What is probabilistic programming?
//     - Why should I care about it?
//   ]
//
// NOTE: the page/text/heading `set` and `show` rules MUST live inside the
// `manning-style` template applied via `#show: manning-style`. A plain `#import`
// does not apply a module's top-level set/show rules to the importing
// document, which is why these rules cannot sit at module top level.

// Color definitions (Manning palette)
#let manning-sage = rgb("#9CAF88")
#let manning-dark-sage = rgb("#6B8E5F")
#let manning-black = rgb("#000000")
#let manning-gray = rgb("#F5F5F5")

// Document-wide template: apply with `#show: manning-style`
#let manning-style(body) = {
  // Page and text configuration
  set page(
    margin: (left: 1.2in, right: 1.2in, top: 0.85in, bottom: 0.85in),
    header: context {
      let page-num = counter(page).get().first()
      if page-num > 1 [
        #set text(font: "Times New Roman", size: 8.5pt, fill: black)
        #if page-num == 3 {
          [Chapter 1 Probabilistic programming in a nutshell]
        } else {
          [Section 1.1 What is probabilistic programming?]
        }
        #h(1fr)
        #page-num
      ]
    },
  )

  set text(font: "Times New Roman", size: 9.5pt, lang: "en")
  set par(justify: true, leading: 0.6em)
  set heading(numbering: "1.1.1")

  // Configure heading styles
  show heading: it => {
    let nums = counter(heading).at(it.location())
    if it.level == 2 {
      block(spacing: 0.5em)[
        #v(0.5em)
        #set text(font: "Times New Roman", size: 11pt, weight: "bold", style: "italic", fill: manning-black)
        #numbering("1.1", ..nums)
        #h(0.4em)
        #it.body
        #v(0.5em)
      ]
    } else if it.level == 3 {
      block(spacing: 0.6em)[
        #v(0.4em)
        #set text(font: "Times New Roman", size: 10pt, weight: "bold", style: "italic", fill: manning-black)
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

// Chapter heading style (Manning style)
// Features: large decorative number on right, italic title, horizontal line
#let chapter(num, title) = {
  pagebreak()

  // Reset heading counter to chapter number
  counter(heading).update((int(num),))

  // Layout with title on left, large number on right
  grid(
    columns: (1fr, auto),
    align: (left, right),
    column-gutter: 20pt,
  )[
    #block[
      #set text(font: "Times New Roman", size: 24pt, style: "italic", fill: manning-black)
      #title
      #v(0.2em)
      #line(length: 100%, stroke: 0.8pt + manning-dark-sage)
    ]
  ][
    #set text(font: "Times New Roman", size: 72pt, weight: "bold", fill: manning-sage)
    #num
  ]

  v(1.2em)
}

// Chapter introduction box (Manning style)
// Green background box with "This chapter covers" header and bullet points
#let chapter-intro(content) = {
  block(
    fill: manning-sage,
    inset: 12pt,
    radius: 0pt,
    width: 65%,
  )[
    #set text(font: "Times New Roman", size: 9.5pt, weight: "bold", fill: manning-black)
    This chapter covers
    #v(0.4em)
    #set text(font: "Times New Roman", size: 9pt, weight: "regular", fill: manning-black)
    #content
  ]
}

// Fact box (Manning style)
// Bold "FACT" label followed by italicized content
#let fact-box(content) = {
  block(
    inset: 10pt,
    width: 100%,
  )[
    #set text(font: "Times New Roman", size: 9.5pt, fill: manning-black)
    #strong[FACT]
    #h(0.4em)
    #content
  ]
}

// Section heading helper
#let section-heading(num, title) = {
  set text(font: "Times New Roman", size: 11pt, weight: "bold", style: "italic", fill: manning-black)
  numbering("1.1", num) + h(0.4em) + title
}

// Emphasis for terms (italic)
#let term(text-content) = {
  emph(text-content)
}
