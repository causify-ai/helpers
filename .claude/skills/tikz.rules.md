These are rules to have a TikZ figure polished to look publication-quality (suitable
for a paper, thesis, or technical presentation), and to fit the fenced-code-block
contract that `render_images.py` uses to render TikZ inside `.smd` lecture slides
For copy-paste skeletons and worked examples, see
`.claude/templates/tikz.template.md`

# Fence Types (Pipeline Contract)

- In `.smd` slides, `dev_scripts_helpers/documentation/render_images.py` renders a
  fenced code block to PNG _before_ pandoc/typst ever see the slide. Each fence type
  has a fixed, non-negotiable contract; picking the wrong one breaks the LaTeX
  compile
- ` ```tikz ` (default, use unless a reason below applies): body is ONLY the drawing
  commands, i.e. what goes between `\begin{tikzpicture}` and `\end{tikzpicture}`
  - Never include `\documentclass`, `\usepackage`, `\begin{document}`,
    `\begin{tikzpicture}`/`\end{tikzpicture}`, or `\end{document}`: the wrapper adds
    all of it automatically
  - Auto-loaded preamble: `tikz`, `amsmath`, `pgfplots`, `mathrsfs`, `xcolor`
    packages, `\pgfplotsset{compat=newest}`, and only the `positioning` TikZ library
    (see "Libraries" below for what this means in practice)
- ` ```raw_latex ` (escape hatch): body is a COMPLETE, self-contained LaTeX document,
  used as-is with no wrapping at all
  - Use it when a figure needs: extra `\usetikzlibrary{...}` beyond `positioning`
    (e.g. `arrows.meta`, `shapes.geometric`), a `\newcommand` shared across multiple
    `\begin{tikzpicture}` blocks, or anything else outside the fixed ` ```tikz `
    preamble
  - Must include everything: `\documentclass[tikz]{standalone}` (or
    `\documentclass{standalone}` + `\usepackage{tikz}`), `\usetikzlibrary{...}`,
    `\begin{document}`, `\begin{tikzpicture}`, `\end{tikzpicture}`, `\end{document}`
- ` ```latex ` is NOT for TikZ: its body goes straight inside `\begin{document}` for
  non-TikZ content (e.g. a `tabularx` table). Its fixed preamble is `tabularx`,
  `enumitem`, `booktabs`: no `tikz` package, and a ` ```latex ` block cannot add one
  (there is no way to reach the preamble from inside `\begin{document}`)
  - Never put `\begin{tikzpicture}` inside a ` ```latex ` block: it will fail to
    compile. Use ` ```tikz ` or ` ```raw_latex ` instead
- Optional fence header: ` ```tikz(name)[width=NN%] `
  - `(name)` overrides the output image file name
  - `[width=NN%]` (or `[height=NN%]`) is inserted verbatim as a Pandoc image
    attribute (`{width=NN%}`) on the generated image: it scales relative to the
    surrounding column, not the page, so tune it against the slide's
    `{.column width=...}`. Most figures that already fit their column at native size
    omit this and rely on the `tikzpicture`'s own `scale=` instead

# Libraries

- ` ```tikz ` blocks get only `\usetikzlibrary{positioning}` for free
- For anything else: `arrows.meta` (scalable arrowheads), `calc`,
  `shapes.geometric`, `fit`, `backgrounds`: switch to ` ```raw_latex ` and declare
  `\usetikzlibrary{...}` explicitly; a ` ```tikz ` block cannot add libraries since
  its content lands _inside_ an already-open `\begin{tikzpicture}`
- Use `arrows.meta` for clean scalable arrowheads (e.g. `-{Latex[length=2.5mm]}`)
  only in ` ```raw_latex `; inside ` ```tikz ` stick to plain TikZ arrow syntax
  (`->`, `<->`)

# Colors

- Reuse the cross-diagram palette in `.claude/skills/visuals.rules.md`
  `## Color Palette` (also used by Graphviz/Mermaid diagrams in these slides),
  converting its hex values to `\definecolor{Name}{RGB}{r,g,b}` decimal triples, e.g
  Red/Pink `#F4A6A6` → `\definecolor{...}{RGB}{244,166,166}`
- For strokes/light fills instead of a named custom color, mix with `!percentage!`,
  e.g. `blue!70!black` (strokes), `red!8` or `gray!20` (light fills/shading): never
  raw saturated `red`/`green`/`blue`
- When a slide's prose already uses `\red{}`/`\green{}`/`\blue{}` callout macros,
  reuse those same colors in the figure so it matches the text that refers to it
- One restrained palette per figure (3-5 colors max), each with one consistent
  semantic role throughout

# Typography

- Match the figure's font to the surrounding document; set `font=\sffamily` once
  instead of per node
  - In ` ```raw_latex `, set it as a `\begin{tikzpicture}[font=\sffamily]` option
  - In ` ```tikz `, there is no access to the `\begin{tikzpicture}[...]` bracket (the
    wrapper already opens it with no options), so set it with
    `\tikzset{every node/.style={font=\sffamily}}` as the first body line instead
- Use a clear label-size hierarchy (titles > body labels > annotations), e.g
  `\Large`/`\large` for headline numbers, `\small`/`\footnotesize` for body labels,
  `\scriptsize` for axis ticks/captions
- Avoid italic math-mode labels for plain text; use `\textbf{}`/`\textrm{}` or
  `\node[align=left, text width=Ncm]` for wrapped multi-line text

# Layout

- Align all nodes to a consistent grid or via `node distance` / `positioning`
  library: no eyeballed coordinates
- Add adequate `inner sep`/spacing so nothing looks cramped
- Connect arrows to proper anchors (`.north`, `.east`, etc.), not approximate
  floating coordinates
- Use `\coordinate` to name reusable points instead of repeating raw coordinates in
  multiple `\draw`/`\node` calls

# Reusable Patterns

- Define repeated node looks once as a named style, then apply with
  `\node[year] at (...) {...}`
  - In ` ```raw_latex `, as a
    `\begin{tikzpicture}[year/.style={font=\large\bfseries, text=blue!70!black}, ...]`
    option
  - In ` ```tikz `, as a `\tikzset{year/.style={...}}` body line (see "Typography"
    above for why)
- Use `\foreach \i/\x/\y in {a/b/c, ...}` to generate repeated elements (timeline
  events, axis ticks, data points) from one tuple list instead of duplicating
  near-identical `\node`/`\draw` lines
- Use `\pgfmathsetmacro{\name}{expr}` for computed coordinates (e.g. points placed
  evenly around a circle via `\angle`, `cos(\angle)`, `sin(\angle)`) instead of
  hardcoding trigonometry by hand
- For a small parameterized sub-figure reused several times in one picture (e.g. a
  colored grid pattern), define it once as `\newcommand{\name}[N]{...}`: this
  requires ` ```raw_latex `, since ` ```tikz ` bodies cannot host a `\newcommand`
  outside `\begin{document}`

# Polish

- Subtle fills only (e.g. `fill=blue!8`), never saturated default colors
- No unnecessary background grid
- No 3D/perspective effects unless functionally necessary
- Tight cropping: compatible with `standalone` document class
- Standardize line weights (no more than 2-3 distinct weights) and shape style
  (consistent corner rounding, consistent arrowheads across all edges)

# Output

- Inside a `.smd` slide: return the fenced block only (` ```tikz `, or
  ` ```raw_latex ` with the full document), matching the "Fence Types" contract
  above, without comments
- For a standalone `.tex` figure (e.g. via `tikz.make_professional`): return the full
  compilable TikZ code in a single code block without comments