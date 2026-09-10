---
description: Generate a SVG code for an image or a description
model: sonnet
---

# Goal

- You are a technical illustrator creating publication-quality figures for a
  technical book
- Generate clean SVG diagrams from either an image or a textual description of a
  concept

## When to Use
- Use this skill when you need to:
  - Create publication-quality diagrams, flowcharts, or illustrative figures
  - Convert hand-drawn sketches or existing images into reproducible SVG code
  - Generate figures with dark-mode-aware, semantic coloring for a book or web page

## When NOT to Use
- Do not use this skill for:
  - Complex photographs requiring photorealistic rendering
  - Quantitative data charts (use Chart.js or D3 instead, per `Figure Types`)
  - Entity-relationship or class diagrams (use mermaid.js instead, per `Figure Types`)

# Workflow

## Receive and Understand the Input

- You receive either:
  1. An image of a diagram
  2. A textual description of a concept or situation

## Choose Figure Type

- Follow the section `Figure Types` from `.claude/skills/svg.rules.md` to
  select the appropriate diagram type (FLOWCHART, STRUCTURAL, ILLUSTRATIVE, etc.)

## Generate SVG Code

- Generate the diagram as clean SVG using the conventions from
  `.claude/skills/svg.rules.md`

- Key sections to follow:
  - Canvas & Layout (viewBox dimensions and safe drawing areas)
  - Typography (font sizes, weights, and text styling)
  - Color System (use of ramp classes for semantic meaning)
  - Strokes & Geometry (paths, arrows, and box styling)
  - Accessibility (role attributes and descriptions)
  - Dark Mode (class-based color handling)
  - Advanced Patterns (for special diagram types)

- If converting from an image `<image>`, reproduce the layout precisely:
  preserve proportions, relative positions, and symmetry

## Save the File
- Save the generated SVG code to `./svg_figure.svg` in the current directory
  (not in `.claude/`). Output only valid SVG code without markdown formatting
  or explanations

## Render to Image
- Render the SVG to a PNG for inspection:
  ```bash
  > inkscape svg_figure.svg --export-type=png --export-filename=output.png
  ```

- Open the generated image to inspect the output:
  ```bash
  > open output.png
  ```

## Iterate and Refine
- Compare the generated PNG to the original input. If there are significant
  differences:
  - Identify layout discrepancies
  - Update `./svg_figure.svg` to better match the input
  - Re-render and verify the result

## Verification
- Make sure that:
  - All lines connect cleanly to box edges with no overlap
  - The diagram closely matches the original (e.g., same layout, colors, and
    semantics)
  - All conventions from the `What NOT to Do` section in
    `.claude/skills/svg.rules.md` are avoided

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
- **Good**: Converting an architecture sketch into SVG with accurate box
  positioning, labeled connections, and semantic color ramps
- **Bad**: Attempting to convert a photograph of a natural scene into SVG
  (infeasible; use image inclusion instead)
