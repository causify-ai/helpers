# Visual Elements

- Illustrations can be of different types:
  - Table
  - Mermaid graph
  - Graphviz diagram
  - TikZ diagram
  - Images
  - Website screenshots

## Tables

- Use markdown tables for structured data comparisons

- Example:
  ```markdown
  \begingroup \scriptsize
  | **Column1** | **Column2** | **Column3** |
  | ----------- | ----------- | ----------- |
  | Value 1     | Value 2     | Value 3     |
  | Value 4     | Value 5     | Value 6     |
  \endgroup
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

- When to use: flowcharts, networks, agent interactions, system relationships, process flows
- Follow the template `.claude/templates/graphviz.template.md`
- Standard template with styling:
  ```graphviz
  digraph DiagramName {
      splines=true;
      nodesep=1.0;
      ranksep=0.75;

      node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=12, penwidth=1.4];

      NodeName [label="Display Name", fillcolor="#A6C8F4"];
      OtherNode [label="Other", fillcolor="#B2E2B2"];

      { rank=same; Node1; Node2; }

      NodeName -> OtherNode [label="  relationship"];
  }
  ```

# Color Palette

- Use consistently throughout all diagrams:
  - **Red/Pink** `#F4A6A6`: Agents, actors, primary entities
  - **Orange** `#FFD1A6`: Input data, sources
  - **Green** `#B2E2B2`: Processed data, environments
  - **Teal** `#A0D6D1`: Algorithms, processes, transformations
  - **Light Blue** `#A6E7F4`: Parameters, configuration, settings
  - **Blue** `#A6C8F4`: Outputs, results, final states
  - **Purple** `#C6A6F4`: External entities, mixed dependencies
