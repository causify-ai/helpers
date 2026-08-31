These are rules to produce publication-quality GraphViz diagrams: flowcharts,
causal graphs, networks, and system/architecture diagrams

For the copy-paste skeletons and worked examples, see
`.claude/templates/graphviz.template.md`, which covers both styles in
separate sections: "Flat Style" and "Architecture Style"

# Choosing a Style

## Flat vs Hierarchy-Aware
- Use the default flat style (`.claude/templates/graphviz.template.md`,
  "Flat Style" section) for flowcharts, causal graphs, networks, and process
  flows
- Use the hierarchy-aware architecture style
  (`.claude/templates/graphviz.template.md`, "Architecture Style" section)
  when the diagram needs subsystem clustering, a two-tier label (name +
  subtitle), or a color legend, e.g. service architectures, market/pipeline
  diagrams, agent loops
- The architecture style is a muted, compact variant of the flat style, tuned
  for professional architecture diagrams rather than causal or flowchart
  diagrams

# Graph-Level Settings

## Layout Direction and Spacing
- Use `splines=spline` for organic, curved edges; use `orthogonal` for
  grid-like diagrams
- Adjust `nodesep` and `ranksep` based on diagram complexity
- Set `compound=true` for complex edge routing with subgraphs
- Use `newrank=true` for better layout when mixing rank-constrained nodes
- For the architecture style, pick `rankdir=LR` for pipelines/architectures
  with parallel lanes, `rankdir=TB` for sequential/vertical flows (e.g. a loop
  or process)
- For the architecture style, use `bgcolor="transparent"` so the diagram
  blends into the surrounding document

## Rank Control and Alignment
- Use `{ rank=same; A; B; C; }` to force nodes onto the same horizontal level,
  e.g. to align nodes into columns/rows when two parallel groups should line
  up
- Use invisible edges (`style=invis`) to guide layout without visual noise,
  e.g. to align two nodes vertically without showing a connection between them
- Use `{ rank=min; START; }` / `{ rank=max; END; }` to force a node to the top
  or bottom
- Use `constraint=false` on an edge that would otherwise distort the rank
  order, e.g. a feedback loop drawn on the side, or a cross-cluster shortcut

# Node Styling

## Shape Selection
- `box`: default for most nodes, decision points
- `ellipse`: state, concepts, inputs/outputs
- `diamond`: decision outcomes, rewards, final values
- `circle`: compact nodes, simple states
- `plaintext`: labels without borders
- `Mrecord`: structured data with ports
- For the architecture style, all real entities are rounded boxes
  (`shape=box, style="rounded,filled"`); never use plain rectangles, circles,
  or diamonds for entities
  - Reserve `shape=note` only for a document/reference-style node (e.g. an
    external citation or data sheet)

## Color Scheme (Flat Style)
- Give each semantic category a triad, same as the architecture style —
  `fillcolor`, `color` (border, same hue), `fontcolor` (dark, same hue):
  - `fillcolor="#A9DDB0", color="#4F9A5C", fontcolor="#1F4E2E"` — green:
    states, inputs
  - `fillcolor="#FFC98A", color="#D98E2B", fontcolor="#6B4517"` — orange:
    actions, processes
  - `fillcolor="#9CC4F2", color="#3C6FB0", fontcolor="#1F4E79"` — blue:
    outputs, rewards
  - `fillcolor="#FFB3B3", color="#D64545", fontcolor="#6B1F1F"` — red:
    errors, warnings
  - `fillcolor="#E8D9F7", color="#9B7DB1", fontcolor="#4A2E5C"` — purple:
    metadata, annotations
- Flat style may also borrow any triad straight from the Color Scheme
  (Architecture Style) table below when its hue fits a node better, e.g.
  coral for a tool/action node, cyan for an observation node, teal for a
  planning node
- `fillcolor` sets the interior color, `color` sets the border/outline color,
  `fontcolor` sets the label text color
- Avoid high-contrast combinations that strain the eyes

## Color Scheme (Architecture Style)
- Give every semantic category a triad — `fillcolor` (pastel), `color`
  (saturated border, same hue), `fontcolor` (dark, same hue) — so fill,
  border, and text always belong to one hue family and stay legible on their
  own fill:

  | Category (example use)               | fill      | border    | font      |
  |---------------------------------------|-----------|-----------|-----------|
  | Default (uncategorized entity)         | `#FFFFFF` | `#9AA9B8` | `#243B53` |
  | Rose (actor / demand)                  | `#F6E1E8` | `#D98CA8` | `#6B2A44` |
  | Orange (source / goal / supply)        | `#FBEBD4` | `#D9A85F` | `#6B4517` |
  | Blue (core process / pluggable step)   | `#D3E3F3` | `#7CA6CE` | `#1F4E79` |
  | Teal (planning / stateful step)        | `#B7DDD0` | `#6FA890` | `#1F4E39` |
  | Cyan (observation / feedback capture)  | `#C7ECF0` | `#7CC6D0` | `#1F4E56` |
  | Sage green (monitoring / verification) | `#DFEDE0` | `#8FB79A` | `#2E5A3D` |
  | Coral (tool call / action)             | `#F6C6C6` | `#D98C8C` | `#6B2A2A` |
  | Violet (external reference)            | `#E9E1F7` | `#A88FD9` | `#45296B` |
  | Rose/red (critical feedback edge)      | n/a       | `#C0455B` | `#C0455B` |
  | Neutral gray (hierarchy/containment)   | `#F7F9FB` | `#C7D0DA` | `#3A4A5C` |

- The default triad (white fill, gray border, navy font) is set once in the
  `node [...]` graph default and applies to any entity that hasn't been given
  a category override
- The default edge (before any narrative bump) is `color="#A3B1C0"`,
  `fontcolor="#7B8794"` — the same muted blue-gray family as the default node
  border

- To add a new category not in the table:
  1. Pick a hue not already used in the diagram
  2. Fill = that hue mixed ~85-90% toward white (pastel, low saturation)
  3. Border = same hue at medium saturation/lightness (readable as an
     outline, not neon)
  4. Font = same hue, dark and desaturated enough for body-text contrast on
     the pastel fill
  5. Keep one category meaning one thing throughout the whole diagram (e.g.
     "blue always means pluggable component"); state that mapping in a `//`
     comment near the top of the DOT source, e.g.
     `// actor : rose | process : blue | monitoring : sage green | external : violet`

## General-Purpose Palette
- For a palette that applies across GraphViz, Mermaid, and TikZ diagrams, use
  the palette in `.claude/skills/visuals.rules.md` `## Color Palette`

## Emphasis and Multi-line Labels
- Use `\n` for line breaks in labels
- Add `rounded` style to box shapes for a softer appearance
- Increase `penwidth` for emphasis or importance
- When the first line of a multi-line label is a title/heading (e.g. a step
  name, a phase number), bold it with an HTML-like label so it stands out
  from the detail line(s) below it: `label=<<b>1. Selection</b><br/>Tree
  policy (UCT)>`
  - HTML-like labels use `<br/>` for line breaks, not `\n`
  - This applies in flat style too, not only the architecture two-tier
    pattern (see "Avoid HTML-like Labels for Plain Text")

# Edge Styling

## Edge Semantics (Flat Style)
- Solid, regular flow: `N1 -> N2 [label="normal"]`
- Weak link, optional: `style="dashed", color="#8C8C8C"`
- Implied, reference: `style="dotted", color="#AAAAAA"`
- Strong, critical: `style="bold", penwidth=2.0, color="#B23A48"`

## Edge Semantics (Architecture Style)
- Solid edge = normal/required data or control flow
- `style=dashed` edge = optional, pluggable, feedback, or "iterate/loop back"
  flow
  - Label it with the short, capitalized verb phrase describing the flow (e.g.
    "Iterate", "Gates eligibility", "Fan-out")
- Bump `penwidth` (e.g. 1.6) and give a saturated `color`/`fontcolor` (e.g.
  `#C0455B`) only on the one or two edges that carry the diagram's key
  narrative (the "so what" flow), to make them pop against the neutral
  default edges
- Use `dir=both` for a request/response pair on one edge instead of two
  separate arrows
- Use `style=invis` edges purely to coax layout/alignment, never for a real
  relationship

## Labels and Arrows
- Center label text with spaces, e.g. `"  Label  "` (looks better than the
  default)
- Capitalize the first letter of edge label text, e.g. `label="  Loop  "`, not
  `label="  loop  "`
- Use `fontcolor` to match or contrast with the edge `color`
- `labelpos="t"` places the label at the top, useful for tall diagrams
- Arrow types: `arrowhead="normal"` (default), `arrowhead="diamond"`,
  `arrowhead="none"` (directional via position only), `dir="both"`
  (bidirectional), `dir="back"` (reverse direction)

# Subgraph Clustering

## Basic Clusters
- Cluster name must start with the `cluster_` prefix
- `label` is the displayed title
- `style="rounded,filled"` gives a modern appearance
- `margin=18` adds padding inside the cluster box; architecture-style
  clusters use a tighter `margin=16` (`14` for the legend cluster) to stay
  compact
- `fontcolor` should contrast with `fillcolor`
- Use nested subgraphs for hierarchical organization (a cluster inside
  another cluster)

## Hierarchy and Containment (Architecture Style)
- When one element conceptually contains others (a subsystem, a grouping, a
  bounding context — not a real edge), draw it as `subgraph cluster_X`, not a
  node
- Fill with a very light neutral gray (`#F7F9FB`, near white, never a
  saturated color) — containment must recede behind the entities it holds
- Border light gray (`#C7D0DA`), same `style="rounded,filled"` as real
  entities — containment reads as "boundary/grouping" through its
  unsaturated fill and border, not through a distinct border style, so it
  stays visually quiet next to the saturated category-color fills on real
  entities
- Never fill a hierarchy cluster with a category color — that color budget is
  reserved for the entities inside it
- Nest clusters for multi-level hierarchy; each level keeps the same gray
  fill/border convention, only the label changes

## Legend
- For any diagram with 3+ color categories, add a trailing
  `subgraph cluster_legend` with one small swatch node per category (label =
  the category's meaning, not its name), all on `{ rank=same; ... }` so they
  sit in one row
- Style the legend cluster like any hierarchy container: light-gray, filled,
  no title color coding of its own

# Typography

## Fonts
- Use a consistent font across graphs; Helvetica is the default recommended
  choice
- `fontname="Helvetica"`: clean, professional
- `fontname="Courier"`: code, monospace
- `fontname="Times"`: formal, serif

## Unicode and Special Characters
- Most Unicode works (e.g. `→`, `π₁`, `≤`, `●`, `◆`); test in the target PDF
  viewer before the final render

## Avoid HTML-like Labels for Plain Text
- For complex formatting, avoid HTML labels — they render inconsistently
- Use multiple lines with `\n` instead
- Reserve HTML-like labels for the two-tier name+subtitle pattern in the
  architecture style (see the "Architecture Style" section of
  `.claude/templates/graphviz.template.md`), or for bolding the first line of
  a flat-style multi-line label (see "Emphasis and Multi-line Labels")

# Color Palettes for Different Domains

## Machine Learning / Reinforcement Learning
- State: `fillcolor="#A9DDB0", color="#4F9A5C"` (soft green)
- Action: `fillcolor="#FFC98A", color="#D98E2B"` (warm orange)
- Reward: `fillcolor="#9CC4F2", color="#3C6FB0"` (cool blue)
- Value: `fillcolor="#E8D9F7", color="#9B7DB1"` (purple)
- Policy: `fillcolor="#FFD4D4", color="#B23A48"` (soft red)

## Data Flow / ETL
- Source: `fillcolor="#C8E6C9", color="#2E7D32"` (green)
- Transform: `fillcolor="#FFECB3", color="#F57F17"` (amber)
- Sink: `fillcolor="#BBDEFB", color="#1565C0"` (blue)
- Error: `fillcolor="#FFCDD2", color="#C62828"` (red)

## System Architecture (Flat Style)
- Frontend: `fillcolor="#E1BEE7", color="#6A1B9A"` (purple)
- Backend: `fillcolor="#B3E5FC", color="#0277BD"` (light blue)
- Database: `fillcolor="#C8E6C9", color="#558B2F"` (dark green)
- Cache: `fillcolor="#FFE0B2", color="#E65100"` (orange)
- External: `fillcolor="#F8BBD0", color="#AD1457"` (pink)

# Footer (Architecture Style)

- After the closing code fence for an architecture-style diagram, always emit
  two lines:
  ```
  label=fig:<short-kebab-slug>
  caption=<one sentence: what the diagram shows, plus what the colors mean>
  ```
