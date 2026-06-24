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

// Match beamer's font (New Computer Modern Sans).
#set text(font: ("New Computer Modern Sans", "DejaVu Sans"), size: 9pt)
#show heading: set text(font: ("New Computer Modern Sans", "DejaVu Sans"))

// Define color functions for markdown-to-Typst color conversion.
#let red(content) = text(fill: red, content)
#let orange(content) = text(fill: orange, content)
#let yellow(content) = text(fill: yellow, content)
#let lime(content) = text(fill: rgb("#00FF00"), content)
#let green(content) = text(fill: green, content)
#let teal(content) = text(fill: teal, content)
#let cyan(content) = text(fill: rgb("#00FFFF"), content)
#let blue(content) = text(fill: blue, content)
#let purple(content) = text(fill: purple, content)
#let violet(content) = text(fill: rgb("#8B00FF"), content)
#let magenta(content) = text(fill: rgb("#FF00FF"), content)
#let pink(content) = text(fill: rgb("#FFC0CB"), content)
#let brown(content) = text(fill: rgb("#8B4513"), content)
#let olive(content) = text(fill: olive, content)
#let gray(content) = text(fill: gray, content)
#let darkgray(content) = text(fill: rgb("#A9A9A9"), content)
#let lightgray(content) = text(fill: rgb("#D3D3D3"), content)
#let black(content) = text(fill: black, content)
#let white(content) = text(fill: white, content)

// Configure theme to match beamer's 4:3 aspect ratio.
// Note: Touying's simple-theme controls page size internally;
// exact beamer dimensions (362.835 x 272.126 pts) cannot be overridden.
#show: simple-theme.with(
  aspect-ratio: "4-3",
  config-common(slide-level: 4),
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

$if(title)$
#title-slide[]
$endif$

$body$
