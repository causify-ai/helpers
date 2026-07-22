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
