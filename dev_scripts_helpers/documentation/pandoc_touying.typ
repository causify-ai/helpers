// Pandoc Typst template producing Touying slides.
//
// Used by `notes_to_pdf.py --type slides --slides_engine typst`.
//
// - Pandoc maps markdown headings to Typst headings, e.g.,
//   - `#` -> `=`
//   - `####` -> `====`
// - `config-common(slide-level: 4)` makes level-4 headings (`####`) start a
//   new slide, mirroring the beamer `--slide-level 4` convention. Headings of
//   level 1-3 become section/structure slides
// - See https://github.com/touying-typ/touying
#import "@preview/touying:0.6.1": *
#import themes.simple: *

//#include "./typst_abbrevs.typ"
#include "../../helpers_root/dev_scripts_helpers/documentation/typst_abbrevs.typ"

// Configure theme to match beamer's 4:3 aspect ratio.
// Note: Touying's simple-theme controls page size internally;
// exact beamer dimensions (362.835 x 272.126 pts) cannot be overridden.
#show: simple-theme.with(
  aspect-ratio: "4-3",
  config-common(slide-level: 4),
  subslide-preamble: block(below: 1em)[
    #v(-0.6em)
    #text(1.2em, weight: "bold", fill: rgb("#003366"),
      utils.display-current-heading(level: 4))
    #v(-0.5em)
    #line(length: 100%, stroke: 2.0pt + rgb("#003366"))
  ],
  config-info(
$if(title)$
    title: [$title$],
$endif$
$if(subtitle)$
    subtitle: [$subtitle$],
$endif$
$if(author)$
    author: [$for(author)$$author$$sep$, $endfor$],
$endif$
$if(date)$
    date: [$date$],
$endif$
  ),
)

// Make the inline math font bigger.
#show math.equation.where(block: false): set text(size: 1.15em)

// Make the inline verbatim font bigger.
#show raw.where(block: false): set text(size: 1.15em)

// Styled table with zebra striping, lateral lines, and configurable width.
#let styled-table(headers: (), rows: (), caption: none, col-widths: none, bold-first-col: true, size: 0.8em, width: 80%) = {
  // TODO(ai_gp): Add explanation of parameters
  let n = headers.len()
  let widths = if col-widths != none { col-widths } else { (1fr,) * n }

  // Zebra striping: alternate white and darker gray backgrounds on full rows
  let processed-rows = rows.enumerate().map(((idx, row)) => {
    let bg-color = if calc.rem(idx, 2) == 0 { white } else { rgb("#e8e8e8") }
    if bold-first-col {
      (
        table.cell(fill: bg-color, text(fill: black, weight: "bold", row.at(0))),
        ..row.slice(1).map(cell => table.cell(fill: bg-color, text(fill: rgb("#555555"), cell)))
      )
    } else {
      row.map(cell => table.cell(fill: bg-color, text(fill: rgb("#555555"), cell)))
    }
  })

  text(size: size,
    figure(
      align(center,
        block(width: width,
          table(
            columns: widths,
            align: (left,) * n,
            stroke: none,
            table.vline(x: 0, stroke: 2pt),
            table.hline(stroke: 2pt),
            table.header(
              ..headers.map(h => table.cell(fill: black, text(fill: white, weight: "bold", h)))
            ),
            table.hline(stroke: 1.5pt),
            ..processed-rows.flatten(),
            table.hline(stroke: 2pt),
            table.vline(x: n, stroke: 2pt),
          )
        )
      ),
      kind: table,
      caption: caption,
    )
  )
}

// Use Computer Modern Sans - standard TeX font (sans-serif variant).
// Fails if Computer Modern not available in container (no fallback).
#set text(font: "CMU Sans Serif", size: 20pt, fill: black)
#show heading: set text(font: "CMU Sans Serif", size: 28pt)
// Use DejaVu Sans (available in Alpine) with reduced size.
// Applied AFTER theme to override theme defaults.
//#set text(font: "DejaVu Sans", size: 20pt, fill: black)
//#show heading: set text(font: "DejaVu Sans", size: 28pt)

// Track list nesting depth with counter
#let list-nesting = counter("list-nesting")

// Use en-dashes for all bullet points (override default circle/triangle markers).
#show list: set list(marker: "–")

// Reduce font size for nested list levels.
#show list: it => {
  list-nesting.step()
  let depth = list-nesting.get().first()
  let size = if depth == 1 { 1em } else if depth == 2 { 0.95em } else { 0.90em }
  set text(size: size)
  [#it]
  list-nesting.update(n => n - 1)
}

// Make footer text smaller.
#let footer-text(body) = text(size: 0.8em, fill: black, body)

$if(title)$
#title-slide[]
$endif$

$body$
