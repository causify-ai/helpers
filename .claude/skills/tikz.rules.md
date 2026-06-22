These are rules to have a TikZ figure polished to look publication-quality
(suitable for a paper, thesis, or technical presentation)

# Visual consistency
- Use a single, restrained color palette (3–5 colors max), each assigned
  a consistent semantic role
  - Avoid raw `red`/`green`/`blue`
  - Use muted tones via `\definecolor` or `!percentage` mixes (e.g. `blue!10`
    fills, `blue!60!black` strokes)
- Standardize line weights (no more than 2–3 distinct weights)
- Standardize shape style: consistent corner rounding, consistent arrowheads
  across all edges

# Typography
- Match the figure's font to the surrounding document
- Use a clear label-size hierarchy (titles > body labels > annotations),
  e.g. `\small`, `\footnotesize`
- Avoid italic math-mode labels for plain text, but wrap in `\textrm{}`

# Layout
- Align all nodes to a consistent grid or via `node distance` /
  `positioning` library: no eyeballed coordinates
- Add adequate `inner sep` and spacing so nothing looks cramped
- Connect arrows to proper anchors (`.north`, `.east`, etc.), not
  approximate floating coordinates

# Libraries and modern syntax
- Load: `positioning, arrows.meta, calc, fit, backgrounds`
- Use `arrows.meta` for clean scalable arrowheads
  (e.g. `-{Latex[length=2.5mm]}`), not legacy `\to` arrows

# Polish
- Subtle fills only (e.g. `fill=blue!8`), never saturated default colors
- No unnecessary background grid
- No 3D/perspective effects unless functionally necessary
- Tight cropping — compatible with `standalone` document class

# Output
- Return the full revised TikZ code in a single compilable code block without
  comments
