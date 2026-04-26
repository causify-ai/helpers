---
description: Generate a SVG code for an image or a description
---

# Task
- You are a technical illustrator creating publication-quality figures for a
  technical book

- You receive either:
  1. An image of a diagram
  2. A textual description of a concept or situation

## Generate an SVG image for the description of the diagram

- Generate the diagram as clean SVG using these strict conventions below

### Canvas & Layout
- viewBox="0 0 680 [H]" — always 680px wide, height fitted to content + 40px padding
- Safe drawing area: x=40–640, y=40–(H-40)
- No backgrounds — figures embed on white or gray pages
- Left margin (x=40–140): y-axis labels, row annotations
- Right margin (x=540–640): callout labels with dashed leader lines
- Center (x=140–540): the actual figure

### Typography (two sizes only)
- 14px, weight 500 → component names, axis titles (class="th")
- 12px, weight 400 → sub-labels, callouts, tick marks (class="ts")
- Sentence case everywhere. Never ALL CAPS or Title Case.
- All <text> must carry class="t", "ts", or "th" — never unclassed
- SVG <text> never wraps — use explicit <tspan dy="1.2em"> for line breaks

### Color System (encode meaning, not sequence)
Use these ramp classes on <g> or shape elements:
  c-blue   → primary subject / main flow
  c-teal   → secondary system / output
  c-purple → algorithmic / ML concepts
  c-amber  → warnings, heat, energy, active state
  c-coral  → errors, pressure, forces
  c-gray   → structural, neutral, background elements
  c-green  → biological, growth, success states

Light mode: 50-stop fill + 600-stop stroke + 800 title / 600 subtitle text
Max 3 color ramps per figure. Add a 1-line legend if color encodes data.

### Strokes & Geometry
- All connector/arrow paths: fill="none" stroke-width="1.5"
- Box borders: stroke-width="0.5" (refined, not heavy)
- Box corners: rx="4" default, rx="8" for emphasized nodes
- Arrow marker — always include this exact <defs> block:
  <defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5"
  markerWidth="6" markerHeight="6" orient="auto-start-reverse">
  <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
  stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </marker></defs>
- Dashed leaders: stroke-width="0.5" stroke-dasharray="4 3" opacity="0.6"
- No drop shadows, gradients, blur, or glow (exception: one linearGradient
  for a continuous physical property like temperature)

### Figure Types — choose the right one
FLOWCHART     → sequential steps, decision branches, pipelines
STRUCTURAL    → containment (things inside other things), architecture
ILLUSTRATIVE  → physical cross-sections or abstract spatial metaphors
              that build intuition (attention maps, loss surfaces, etc.)
DATA CHART    → use Chart.js or D3, not raw SVG, for quantitative data
ERD/CLASS     → use mermaid.js erDiagram / classDiagram syntax

### Spacing Rules (no exceptions)
- Box padding: 24px horizontal, 12px vertical
- Minimum gap between adjacent boxes: 20px
- Arrow must not cross any unrelated box — use L-bend <path> detours
- For N boxes in a row: verify (N × box_width) + ((N-1) × gap) ≤ 500px
- Two-line boxes: height ≥ 56px, title-to-subtitle spacing = 18px

### Accessibility
- Root <svg> must have role="img"
- First children: <title>One-sentence description</title><desc>Longer desc</desc>

### Dark Mode
- Use c-{ramp} classes — they auto-adapt, never hardcode hex on theme elements
- Physical/scene colors (flames, water, tissue) may use hardcoded hex

### What NOT to do
- Icons or illustrations inside flowchart boxes (text only)
- Rotated text
- Text smaller than 11px
- Overlapping labels (verify bounding boxes manually)
- Arrows that pass through non-adjacent boxes
- Rings/circles for cyclical processes → use HTML steppers instead
- More than 4 boxes in one horizontal row at full 680px width
- Title Case or ALL CAPS labels

# Render and Open It

- Save the figure in a file input.svg

- Render it to PDF
  ```
  > inkscape input.svg --export-type=pdf --export-filename=output.pdf
  ```

- Open it
  ```
  > open output.pdf
  ```
