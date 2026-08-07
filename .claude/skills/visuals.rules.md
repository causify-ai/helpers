# Visual Elements

## Types of Illustrations
- Illustrations can be of different types:
  - Table
  - Mermaid graph
  - Graphviz diagram
  - TikZ diagram
  - Images
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
- Example:
  ```mermaid
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

## GraphViz Diagrams

- When to use: flowcharts, networks, agent interactions, system relationships,
  process flows

- Follow the template `.claude/templates/graphviz.template.md`

## GraphViz Architecture Diagram Style

- When to use: system and architecture diagrams that group components into
  subsystems and highlight feedback loops, e.g., service architectures,
  market/pipeline diagrams
- This is a muted, compact variant of the default style in
  `.claude/templates/graphviz.template.md`, tuned for professional
  architecture diagrams rather than causal or flowchart diagrams

- Graph-level settings:
  ```graphviz
  bgcolor  = "white";
  rankdir  = LR;
  splines  = spline;
  nodesep  = 0.35;
  ranksep  = 0.70;
  pad      = 0.30;
  ```

- Node and edge defaults use a muted gray instead of colored borders and lines:
  ```graphviz
  node [shape=box, style="rounded,filled", fontname="Helvetica",
        fontsize=13, penwidth=1.2, margin="0.20,0.12", height=0.50,
        color="#7B8794"];
  edge [color="#9AA5B1", penwidth=1.1, arrowsize=0.75,
        fontname="Helvetica", fontsize=10, fontcolor="#616E7C"];
  ```
  - Fill node backgrounds with colors from `## Color Palette`
  - Keep node borders and edges in the muted gray tones above, not palette
    colors

- Group related components into a `subgraph cluster_<name>` to show subsystem
  boundaries:
  - `label` and `labelloc = "t"` for a top-aligned cluster title
  - `fontname = "Helvetica-Bold"`, `fontsize = 12`, `fontcolor = "#52606D"`
    for the cluster title
  - `style = "rounded,filled"`, `fillcolor = "#F7F9FC"`, `color = "#CBD2D9"`,
    `penwidth = 1.0`, `margin = 14` for the cluster box
  - Use `{ rank=same; NodeA; NodeB; }` inside a cluster to align sibling
    components on one row

- Use `shape=note` with fill `#F0E6FF` for external reference sources that are
  not part of the core system, e.g., a third-party data provider

- For feedback or cross-cutting relationships that would distort the main
  layout, use a dashed edge with `constraint=false`, a distinct accent color,
  and a heavier `penwidth`:
  ```graphviz
  Metering:sw -> Market:se [label="reputation and pricing feedback",
                             style=dashed, penwidth=1.5,
                             color="#B23A48", fontcolor="#B23A48",
                             constraint=false];
  ```

- Use `dir=both` on an edge to represent a request/response or bidirectional
  relationship

## Text and Typography

- Use HTML subscript/superscript tags in diagram text labels instead of LaTeX or
  unicode notation
  - **Good** (renders correctly in all diagram formats):
    ```
    H<SUB>2</SUB>O
    E = mc<SUP>2</SUP>
    H<SUP>+</SUP> ions
    T<SUB>t-1</SUB>
    ```
  - **Bad** (LaTeX or unicode-style, may not render):
    ```
    H_2 O
    E = mc^2
    H⁺ ions
    H₂O
    ```
- Applies to all diagram types: Graphviz, Mermaid, and TikZ
- HTML tags preserve compatibility across rendering engines

## Best Practices

1. **Consistency**: Use semantic colors consistently across all diagrams
2. **Contrast**: Ensure label text is readable on filled backgrounds
3. **Hierarchy**: Use clustering and color to show conceptual grouping
4. **Simplicity**: Avoid over-styling; let structure speak
5. **Testing**: Always render and review in target format (PDF/SVG/PNG)
6. **Alignment**: Use `rank=same` and invisible edges for professional layout
7. **Spacing**: Adjust `nodesep` and `ranksep` for diagram clarity
8. **Fonts**: Stick with Helvetica or Times for professional appearance
