---
description: Generate a TikZ code for an image or a description
---

## Purpose
- Convert images or textual descriptions into publication-quality TikZ LaTeX code
  Generate a compilable LaTeX file, render it to PNG, and iteratively refine the
  output to match the input precisely

## When to Use
Use this skill when you need to:

- Create publication-quality diagrams, plots, or visualizations
- Convert hand-drawn sketches or existing images into reproducible TikZ code
- Generate diagrams for inclusion in LaTeX documents

## When NOT to Use
Do not use this skill for:

- Complex photographs requiring photorealistic rendering
- Plots from large datasets (use dedicated plotting libraries instead)
- Diagrams requiring advanced 3D visualization

## Workflow

### Step 1: Generate TikZ Code
Generate valid LaTeX code using the TikZ package. Wrap the code in a complete
minimal working example:
```latex
\documentclass{standalone}
\usepackage{tikz}
\begin{document}
\begin{tikzpicture}
...
\end{tikzpicture}
\end{document}
```

**Preserve layout accurately**

- If converting from an image `<image>`, reproduce the layout precisely
- Preserve proportions, relative positions, and symmetry
- Use coordinates and scaling where appropriate
- Approximate complex curves with TikZ paths when needed

**Use appropriate TikZ features**

- Nodes for labeled elements
- `draw`, `fill`, `shade` for shapes
- Arrows and edge styles for connections
- Rounded corners for blocks: `[rounded corners=1cm]`
- `positioning` and `calc` libraries if helpful

**Keep code clean and readable**

- Use indentation for nested structures
- Define reusable styles for repeated elements

**Handle ambiguity**

- Make reasonable assumptions about unclear inputs
- Prioritize clarity and visual correctness over perfection

### Step 2: Save the File
- Save the generated LaTeX code to `./tikz_figure.tex` in the current directory
  (not in `.claude/`). Output only valid TikZ code without markdown formatting or
  explanations

### Step 3: Render to Image
- Generate a PNG image using the rendering script:
  ```bash
  > ./helpers_root/dev_scripts_helpers/documentation/dockerized_tikz_to_bitmap.py \
      -i tikz_figure.tex \
      -o output.png
  ```

- Open the generated image to inspect the output:
  ```bash
  > open output.png
  ```

### Step 4: Iterate and Refine
Compare the generated PNG to the original input. If there are significant
differences:

- Identify layout discrepancies
- Update `./tikz_figure.tex` to better match the input
- Re-render and verify the result

## Examples
- **Good**: Converting a circuit diagram sketch into TikZ with accurate node
  positioning, labeled connections, and proper symmetry
- **Bad**: Attempting to convert a photograph of a natural scene into TikZ
  (infeasible; use image inclusion instead)
