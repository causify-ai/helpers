These are rules to have an SVG figure polished to look publication-quality
(suitable for a paper, thesis, or technical presentation)

# Visual consistency
- Use a single, restrained color palette (3–5 colors max), each assigned
  a consistent semantic role
  - Avoid raw `#FF0000`/`#00FF00`/`#0000FF`
  - Use muted tones via hex codes or CSS named colors
  - Mixes: `#E8F4F8` for light fills, `#4A90B8` for strokes
- Standardize stroke widths (no more than 2–3 distinct widths)
- Standardize shape style: consistent corner rounding, consistent arrow markers
  across all edges
- Use `opacity` sparingly (max 0.7–0.9 for overlays, avoid near-transparent
  elements)

# Typography
- Match the figure's font to the surrounding document (e.g., `font-family:
  'Helvetica', 'Arial', sans-serif` for most outputs)
- Use a clear label-size hierarchy (titles > body labels > annotations),
  e.g., `font-size: 16px` for title, `12px` for body, `10px` for annotations
- Avoid oblique/italic fonts for plain text unless emphasizing
- Ensure sufficient `text-anchor` alignment (start, middle, end) for readability

# Layout
- Align all text and shapes to consistent anchor points or grid alignment
- Add adequate `padding` and element spacing so nothing looks cramped
- Use absolute positioning or clear grid offsets, no eyeballed coordinates
- Position text at proper reference points relative to shapes (e.g., `.north`
  equivalent via careful offset calculation)

# SVG Structure
- Use semantic SVG elements (`<text>`, `<line>`, `<circle>`, `<rect>`, `<path>`)
  for cleaner output and accessibility
- Define reusable `<defs>` for gradients, patterns, and markers (e.g., arrowheads)
- Give meaningful names to each element so that it's easy to find them
- Use `<g>` (groups) to organize logical units and apply transforms uniformly
  - E.g., for elements and their text

- Apply consistent styling via CSS `<style>` block or inline attributes
- Include viewBox for scalability: `viewBox="0 0 width height"` with no hardcoded
  pixel sizes when possible

# Polish
- Subtle fills only (e.g., `#F0F5F8` for light backgrounds), never saturated
  default colors
- No unnecessary background grid or decorative elements
- Consistent arrowhead markers via `<marker>` definitions
- Tight cropping — minimize whitespace around content
- Stroke and fill ratios balanced (not overdrawn, not too faint)
- Anti-aliasing: ensure elements render cleanly at typical screen resolutions

# Output
- Return the full revised SVG code in a single compilable code block without
  comments (unless clarifying complex paths/transforms)
- Verify SVG is valid XML and renders in standard browsers
