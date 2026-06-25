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

// Use DejaVu Sans (available in Alpine) with reduced size.
// Applied AFTER theme to override theme defaults.
#set text(font: "DejaVu Sans", size: 20pt)
#show heading: set text(font: "DejaVu Sans", size: 28pt)

// Use en-dashes for all bullet points (override default circle/triangle markers).
#show list: set list(marker: "–")

$if(title)$
#title-slide[]
$endif$

$body$
