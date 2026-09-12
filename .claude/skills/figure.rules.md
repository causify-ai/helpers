# Visual Elements

## Types of Illustrations
- Illustrations can be of different types:
  - Table
  - Mermaid graph
  - Graphviz diagram
  - TikZ diagram
  - Images
  - Portrait photo (for a named person)
  - Website screenshots

## Color Palette

- Use consistently throughout all diagrams:
  - **Red/Pink** `#F4A6A6`: Agents, actors, primary entities
  - **Orange** `#FFD1A6`: Input data, sources
  - **Green** `#B2E2B2`: Processed data, environments
  - **Teal** `#A0D6D1`: Algorithms, processes, transformations
  - **Light Blue** `#A6E7F4`: Parameters, configuration, settings
  - **Blue** `#A6C8F4`: Outputs, results, final states
  - **Purple** `#C6A6F4`: External entities, mixed dependencies
  - **Lavender** `#F0E6FF`: Reference or auxiliary notes, used with `shape=note`

- These are anchor hues and meanings, not final fill/border/font values: each
  format builds its own concrete triad (fill/border/font) and syntax from
  these anchors, documented in that format's rules file
  - GraphViz: `.claude/skills/graphviz.rules.md` "Color Scheme" tables
  - TikZ: `.claude/skills/tikz.rules.md` "Colors" section
  - SVG: `.claude/skills/svg.rules.md` "Color System" section (`c-{ramp}`
    classes)
- Keep one hue meaning one thing across every diagram in a document set, e.g.
  orange always means "input/source", never "action" in one diagram and
  "input" in another

## Tables

- Use markdown tables for structured data comparisons and side-by-side content

- For simple data comparison:
  ```markdown
  \begingroup \scriptsize
  | **Column1** | **Column2** | **Column3** |
  | ----------- | ----------- | ----------- |
  | Value 1     | Value 2     | Value 3     |
  | Value 4     | Value 5     | Value 6     |
  \endgroup
  ```

- For side-by-side content (symmetric columns):
  ```markdown
  | **Left Heading** | **Right Heading** |
  |---|---|
  | - Point 1<br>- Point 2 | - Point 1<br>- Point 2 |
  ```

## Mermaid Graph

- When to use: Mind maps, hierarchical taxonomies, classification structures
- Start every Mermaid diagram with this `%%{init: ...}%%` directive to apply
  the project theme:
  ```
  %%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#EEEDFE', 'primaryBorderColor': '#7F77DD', 'primaryTextColor': '#26215C', 'lineColor': '#888888', 'fontFamily': 'Helvetica'}}}%%
  ```
- Example:
  ```mermaid
  %%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#EEEDFE', 'primaryBorderColor': '#7F77DD', 'primaryTextColor': '#26215C', 'lineColor': '#888888', 'fontFamily': 'Helvetica'}}}%%
  mindmap
    root((**Machine Learning**))
      (**Paradigms**)
        Supervised
        Unsupervised
        RL
      (**Models**)
        Linear
        Neural networks
        SVM
  ```

## TikZ Graph

- Follow the template `.claude/templates/tikz.template.md`
- Example:
  ```tikz
  ...
  ```

## Website Screenshots

- Use `website_screenshot.py` to take snapshots of notebooks
- Crop images to include only necessary content

## Custom Images

- Follow the template `.claude/templates/image.template.md`

## Portraits of People

- When a slide names a specific historical figure or researcher, illustrate
  with a real portrait photo, not an AI-generated illustration
  - Do not use a portrait for each references to avoid clutter, but use the most
    notable named figures
- Prefer current Wikipedia infobox photo for that person or a picture from the
  Internet
  - Pick a clear, sharp headshot; reject small, blurry, or cluttered photos
  - Save as `figures/<Lesson>.<Person_Name>.png`, matching this file's
    existing figure-naming convention
- Place the portrait in a narrow right column next to the slide's text, with
  a captioned attribution below the image:
  ```markdown
  ::: columns
  :::: {.column width=80%}
  ...
  ::::
  :::: {.column width=20%}

  ![](msml610/lectures_source/figures/L01.3.Judea_Pearl.png)

  \footnotesize _Judea Pearl (2010)_
  ::::
  :::
  ```
  - Caption format: `\footnotesize _<Name> (<year>)_`
  - Do not add attribution

## GraphViz Diagrams

- When to use: flowcharts, networks, agent interactions, system relationships,
  process flows
  - Follow the rules `.claude/skills/graphviz.rules.md` and the "Flat Style"
    section of the template `.claude/templates/graphviz.template.md`

- When to use: system and architecture diagrams that group components into
  subsystems and highlight feedback loops, e.g., service architectures,
  market/pipeline diagrams, agent loops
  - This is a muted, compact, hierarchy-aware variant of the default flat
    style, tuned for professional architecture diagrams rather than causal or
    flowchart diagrams
  - Follow the rules `.claude/skills/graphviz.rules.md` and the "Architecture
    Style" section of the template `.claude/templates/graphviz.template.md`

## Typography

- One font family per document set: sans-serif (Helvetica) by default; serif
  (Times) only to match a serif surrounding document; monospace (Courier) for
  code
- Sentence case for every label: never ALL CAPS or Title Case
- A clear size hierarchy: title/heading label > body label > annotation/tick
  label
- Concrete font syntax and size numbers per format: see the "Typography"
  section of `.claude/skills/graphviz.rules.md`, `.claude/skills/tikz.rules.md`,
  and `.claude/skills/svg.rules.md`

### Subscript and Superscript

- The right syntax for e.g. H<SUB>2</SUB>O depends on how the format renders
  text, so it is NOT the same across formats
  - GraphViz and Mermaid render labels as HTML-like markup: use `<SUB>`/`<SUP>`
    tags
    - **Good**: `H<SUB>2</SUB>O`, `E = mc<SUP>2</SUP>`, `T<SUB>t-1</SUB>`
    - **Bad**: `H_2 O`, `E = mc^2`, `H₂O` (LaTeX/unicode notation may not
      render)
  - TikZ renders through LaTeX itself: use native math mode (`$H_2O$`,
    `$x^2$`), never HTML tags — LaTeX does not interpret `<SUB>`/`<SUP>`, they
    show up as literal text on the figure
  - SVG `<text>` has no HTML subscript tag: use
    `<tspan baseline-shift="sub" font-size="70%">2</tspan>`

## Geometry and Restraint

- One restrained palette per diagram: 3-5 semantic colors max, plus neutral
  gray for structure/containment
- 3+ color categories in one diagram: add a compact legend (small swatch +
  meaning, not the category name)
- No more than 2-3 distinct stroke/line weights in one diagram; reserve the
  heaviest weight for the one or two "so what" elements
- Consistent corner rounding across all shapes in one diagram: all sharp, or
  all rounded, never mixed
- Diagrams blend into the surrounding page: transparent or white background,
  never a filled canvas
- Concrete numbers and syntax per format: see `.claude/skills/graphviz.rules.md`,
  `.claude/skills/tikz.rules.md`, and `.claude/skills/svg.rules.md`

## Captions and Labels

- Every rendered diagram gets a short id and a one-sentence caption: what the
  diagram shows, and what the colors mean when color encodes a category
- Implementation differs by format:
  - GraphViz: trailing `label=fig:<slug>` / `caption=<sentence>` lines (see
    `.claude/skills/graphviz.rules.md` "Footer")
  - TikZ: `\label{fig:<slug>}` + `\caption{<sentence>}` inside a `figure`
    environment for a standalone figure; for a `.smd` slide fence, put the
    caption as `\footnotesize _<sentence>_` text below the rendered image in
    the slide markdown, since the fence itself carries no comments
  - SVG: the required `<title>`/`<desc>` (see "Accessibility" in
    `.claude/skills/svg.rules.md`) doubles as the id/caption, no extra footer
    needed

## Best Practices

1. **Consistency**: One semantic color means one thing across every diagram in
   a document set (see "Color Palette")
2. **Contrast**: Label text must stay readable on every filled background
3. **Hierarchy**: Use clustering/grouping and color to show conceptual
   structure, not decoration
4. **Simplicity**: Avoid over-styling; let structure speak (see "Geometry and
   Restraint")
5. **Testing**: Always render and review in the target format (PDF/SVG/PNG)
6. **Documentation**: Every diagram gets an id and a one-sentence caption (see
   "Captions and Labels")
