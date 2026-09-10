# SVG Figure Creation Conventions

Rules for producing SVG figures that are clean and publication-quality
(suitable for a technical book, paper, thesis, or technical presentation).

# Canvas & Layout

## Canvas Dimensions

- viewBox="0 0 680 [H]": always 680px wide, height fitted to content + 40px padding
- Include viewBox for scalability: never hardcode pixel width/height on the
  root <svg> when a viewBox is set
- Safe drawing area: x=40–640, y=40–(H-40)
- No backgrounds: figures embed on white or gray pages

## Regions

- Left margin (x=40–140): y-axis labels, row annotations
- Right margin (x=540–640): callout labels with dashed leader lines
- Center (x=140–540): the actual figure

## Alignment

- Align all text and shapes to consistent anchor points or grid alignment
- Use absolute positioning or clear grid offsets, no eyeballed coordinates
- Position text at proper reference points relative to shapes

## Spacing

- Box padding: 24px horizontal, 12px vertical
- Minimum gap between adjacent boxes: 20px
- Arrow must not cross any unrelated box: use L-bend <path> detours
- For N boxes in a row: verify (N × box_width) + ((N-1) × gap) ≤ 500px
- Two-line boxes: height ≥ 56px, title-to-subtitle spacing = 18px
- Add adequate padding and element spacing so nothing looks cramped
- Tight cropping: minimize whitespace around content

# Typography

## Sizes and Weights

- 14px, weight 500: component names, axis titles (class="th")
- 12px, weight 400: sub-labels, callouts, tick marks (class="ts")
- Use a clear label-size hierarchy (titles > body labels > annotations)

## Text Styling

- Sentence case everywhere. Never ALL CAPS or Title Case.
- All <text> must carry class="t", "ts", or "th": never unclassed
- SVG <text> never wraps: use explicit <tspan dy="1.2em"> for line breaks
- Match the figure's font to the surrounding document when no class system
  applies (e.g., `font-family: 'Helvetica', 'Arial', sans-serif`)
- Avoid oblique/italic fonts for plain text unless emphasizing
- Ensure sufficient text-anchor alignment (start, middle, end) for readability

# Color System

## Semantic Color Roles

Color encodes meaning, not sequence. Use these ramp classes on <g> or shape
elements:
- c-blue: primary subject / main flow
- c-teal: secondary system / output
- c-purple: algorithmic / ML concepts
- c-amber: warnings, heat, energy, active state
- c-coral: errors, pressure, forces
- c-gray: structural, neutral, background elements
- c-green: biological, growth, success states

## Palette Restraint

- Use a single, restrained color palette (3-5 colors max), each with a
  consistent semantic role
- Max 3 color ramps per figure; add a 1-line legend if color encodes data
- Avoid raw `#FF0000`/`#00FF00`/`#0000FF`; use muted tones instead
  (e.g., `#E8F4F8` for light fills, `#4A90B8` for strokes)

## Color Application

- Light mode: 50-stop fill + 600-stop stroke + 800 title / 600 subtitle text
- Subtle fills only (e.g., `#F0F5F8` for light backgrounds), never saturated
  default colors
- Use `opacity` sparingly (max 0.7-0.9 for overlays, avoid near-transparent
  elements)

# Strokes & Geometry

## Paths and Connectors

- All connector/arrow paths: fill="none" stroke-width="1.5"
- Box borders: stroke-width="0.5" (refined, not heavy)
- Box corners: rx="4" default, rx="8" for emphasized nodes
- Standardize stroke widths across the figure (no more than 2-3 distinct widths)
- Standardize shape style: consistent corner rounding, consistent arrow
  markers across all edges

## Arrow Markers

Always include this exact <defs> block:

```svg
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5"
    markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
      stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
</defs>
```

## Leader Lines and Effects

- Dashed leaders: stroke-width="0.5" stroke-dasharray="4 3" opacity="0.6"
- No drop shadows, gradients, blur, or glow (exception: one linearGradient
  for a continuous physical property like temperature)
- Stroke and fill ratios balanced (not overdrawn, not too faint)
- Anti-aliasing: ensure elements render cleanly at typical screen resolutions

# SVG Structure

- Use semantic SVG elements (<text>, <line>, <circle>, <rect>, <path>) for
  cleaner output and accessibility
- Define reusable <defs> for gradients, patterns, and markers (e.g., arrowheads)
- Give meaningful names to each element so it's easy to find them
- Use <g> (groups) to organize logical units and apply transforms uniformly
  (e.g., for elements and their text)
- Apply consistent styling via a CSS <style> block or inline attributes
- No unnecessary background grid or decorative elements

# Figure Types

Choose the appropriate type for your diagram:
- FLOWCHART: sequential steps, decision branches, pipelines
- STRUCTURAL: containment (things inside other things), architecture
- ILLUSTRATIVE: physical cross-sections or abstract spatial metaphors that
  build intuition (attention maps, loss surfaces, etc.)
- DATA CHART: use Chart.js or D3, not raw SVG, for quantitative data
- ERD/CLASS: use mermaid.js erDiagram / classDiagram syntax

# Accessibility

- Root <svg> must have role="img"
- First children: <title>One-sentence description</title><desc>Longer desc</desc>

# Dark Mode

- Use c-{ramp} classes: they auto-adapt, never hardcode hex on theme elements
- Physical/scene colors (flames, water, tissue) may use hardcoded hex

# Advanced Patterns

## Causal Diagrams & Two-Panel Comparisons

- For contrasting scenarios: use two bordered panels side-by-side with
  different color themes (e.g., purple for correct, coral for wrong)
- Enclose each panel in a tall <rect> with stroke-width="3" rx="8": full-height
  borders establish visual separation
- Different panel headers (th class text) encode meaning: "Reality" vs "XYZ"
  signals contrast in epistemic status

## Arrow Markers with Inherited Color

- Define markers with `stroke="context-stroke"` so the arrow color matches
  its parent path stroke
- Create both normal (`marker-width="6"`) and bold (`marker-width="7"
  stroke-width="2"`) versions for emphasis
- Bold arrows signal strong causal effect or mistake severity

## Dashed vs. Solid Lines for Correlation vs. Causation

- Solid arrows: causal claims
- Dashed lines (stroke-dasharray: 5 3): observed correlation without causal
  mechanism
- Parallel curves in charts (one solid, one dashed): show correlated behavior
  from a confound

## Mini Line Charts with Legends

- Group charts with `<g transform="translate(x,y)">` to position axes,
  curves, and legends as units
- Include axis lines (class="axis-line") and label the axes (class="ts")
- Legend: small colored lines with text labels below or inside the chart area
- Curves using Bézier paths (Q) to show smooth trends: avoid jagged polylines

## Error / Negation Indicators

- Large red ✕ character (font-size="32px" fill="#dc2626") to mark incorrect
  outcomes
- Place explanation text nearby (e.g., "Demand didn't change: Occupancy will
  fall")
- Visual weight of ✕ should match the prominence of the mistake in the
  narrative

# What NOT to Do

- Icons or illustrations inside flowchart boxes (text only)
- Rotated text
- Text smaller than 11px
- Overlapping labels (verify bounding boxes manually)
- Arrows that pass through non-adjacent boxes
- Rings/circles for cyclical processes: use HTML steppers instead
- More than 4 boxes in one horizontal row at full 680px width
- Title Case or ALL CAPS labels
- Hardcoded color hex in marker definitions: always use context-stroke
- Single-panel layouts when contrast is the point of the figure

# Output

- Return the full revised SVG code in a single compilable code block without
  comments (unless clarifying complex paths/transforms)
- Verify the SVG is valid XML and renders correctly in standard browsers
