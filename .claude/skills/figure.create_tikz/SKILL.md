---
description: Generate a TikZ code for an image or a description
model: sonnet
---

# Goal
- Convert images or textual descriptions into publication-quality TikZ LaTeX code
- Generate a compilable LaTeX file, render it to PNG, and iteratively refine the
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

# Workflow

## Receive and Understand the Input

- You receive either:
  1. An image of a diagram
  2. A textual description of a concept or situation

## Choose Figure Type

- Pick the diagram structure that fits the input:
  - FLOWCHART: sequential steps, decision branches, pipelines
  - STRUCTURAL: containment (things inside other things), architecture
  - ILLUSTRATIVE: plots, physical cross-sections, or abstract spatial metaphors

## Generate TikZ Code
- Generate valid LaTeX code using the TikZ package. Wrap the code in a complete
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

**Follow the TikZ conventions**

- Generate the diagram using the conventions from
  `.claude/skills/tikz.rules.md`
- Key sections to follow: Colors, Typography, Layout, Reusable Patterns, Polish

**Handle ambiguity**

- Make reasonable assumptions about unclear inputs
- Prioritize clarity and visual correctness over perfection

## Save the File
- Save the generated LaTeX code to `./tikz_figure.tex` in the current directory
  (not in `.claude/`). Output only valid TikZ code without markdown formatting
  or explanations

## Render to Image
- Generate a PNG image using the rendering script:
  ```bash
  > ./helpers_root/dev_scripts_helpers/dockerize/dockerized_tikz_to_bitmap.py \
      -i tikz_figure.tex \
      -o output.png
  ```

- Open the generated image to inspect the output:
  ```bash
  > open output.png
  ```

## Iterate and Refine
- Compare the generated PNG to the original input. If there are significant
  differences:
  - Identify layout discrepancies
  - Update `./tikz_figure.tex` to better match the input
  - Re-render and verify the result

## Verification
- Make sure that:
  - All lines connect cleanly to box edges with no overlap
  - The diagram closely matches the original (e.g., same layout, colors, and
    semantics)

## Compare for User
- Once it's done, build a side-by-side comparison image and open it:
  ```bash
  > montage <original_image> output.png -tile 2x1 -geometry 500x+10+10 \
      -background white comparison.png
  > open comparison.png
  ```
- Remove `comparison.png` after the user has seen it, it is a temp file, not
  a deliverable

## Examples
- **Good**: Converting a circuit diagram sketch into TikZ with accurate node
  positioning, labeled connections, and proper symmetry
- **Bad**: Attempting to convert a photograph of a natural scene into TikZ
  (infeasible; use image inclusion instead)
