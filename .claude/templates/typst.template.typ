// abc123 2026-06-23
// Template for MSML610 typst chapters. Save to msml610/book/ directory.
// Import AIMA style formatting and macros
#import "../../dev_scripts_helpers/typst/aima_style.typ": aima-style, algorithm, chapter, glossary

// Document metadata
#set document(
  title: "Example Chapter",
  author: "MSML610: Advanced Machine Learning",
)

// Apply the AIMA document template (page/text/heading set + show rules)
#show: aima-style

#chapter(1, "Example Chapter")

== Introduction

=== Getting Started

// Slide: Introduction

Content goes here. Use #strong[text] for bold concepts, definitions, and key
terms. Use *text* for italics sparingly, only for emphasis.

When introducing concepts, provide intuition before formalism. Define unfamiliar
terms clearly. Connect to real-world applications or broader themes.

#strong[Key insight]: State important conclusions and highlight critical points.

Recommended word count: 200–250 words per slide, adjustable based on depth.

=== Key Methods

// Slide: Methods Overview

For mathematical content, use inline math like `$f(n) = g(n) + h(n)$` for
text-like expressions, or display math for important equations on their own
line:

$$Y_t = beta_0 + beta_1 t + beta_2 D_t + beta_3 (t - t_0) D_t + u_t$$

Preserve all mathematical formulas from the original slide material exactly.

For algorithms or structured pseudocode, use the algorithm macro:

#algorithm(
  "Algorithm Name",
  [
    *Input:* description of input parameters
    #h(1em) *for* each iteration *do* #h(2em) \
    #h(2em) perform operation \
    #h(1em) *return* result
    *Output:* description of result
  ],
)

Use `*keyword*` for language keywords (function, if, loop, return, etc.). Use
`#h(1em)` for indentation levels within algorithms.

=== Figures and Tables

// Rendered image goes here with label and caption
// ```graphviz
// digraph ExampleDiagram {
//     rankdir=LR;
//     node [shape=box, style="rounded,filled"];
//     A [label="Node A"];
//     B [label="Node B"];
//     A -> B;
// }
// ```
// label=fig:example-diagram
// caption=Description of what the figure shows and its relevance

// #figure(
//   image("path/to/image.png", width: 80%),
//   caption: [Descriptive caption explaining the figure's relevance.],
// ) <fig:example-diagram>

// Reference figures in text like: @fig:example-diagram shows...

For tables with structured data:

#show table.cell.where(y: 0): set text(weight: "bold")

#figure(
  table(
    columns: (1fr, 1fr, 1fr),
    inset: 6pt,
    align: left + horizon,
    stroke: none,
    table.hline(stroke: 1.2pt),
    [Header 1], [Header 2], [Header 3],
    table.hline(stroke: 0.8pt),
    [Row 1 Col 1], [Row 1 Col 2], [Row 1 Col 3],
    [Row 2 Col 1], [Row 2 Col 2], [Row 2 Col 3],
    table.hline(stroke: 1.2pt),
  ),
  caption: [Table description explaining contents and purpose.],
) <tbl:example-table>

Reference tables like: @tbl:example-table summarizes...

== Applications

=== Practical Examples

// Slide: Real-World Applications

Continue with clear headings and structured content. Each major topic should:

- Have a distinct subsection with a descriptive heading
- Include a slide marker comment indicating source
- Provide intuition before formal definitions
- Use #strong[emphasis] for new concepts
- Include examples or illustrations where helpful

#strong[Definition]: Provide clear, concise definitions of key terms. Use
technical language precisely, avoiding overly fancy synonyms.

=== Best Practices

// Slide: Writing Guidelines

Follow these patterns when expanding slide content:

#strong[1. Structure]: Lead with intuition, follow with formalism.

#strong[2. Emphasis]: Use #strong[...] for concepts, definitions, algorithms, and
key terms. Use *...* only for emphasis, sparingly.

#strong[3. Formulas]: Display important equations on their own line using
$$...$$ notation. Preserve all mathematical notation from slides.

#strong[4. Pseudocode]: Format all algorithms with the `algorithm(...)` macro,
using proper indentation and keyword emphasis.

#strong[5. Figures]: Include all figures from slides with captions and labels.
Reference them explicitly in text.

#strong[6. Workflow]:
1. Start chapter with metadata and imports
2. Add git_hash and timestamp at top
3. Use `== heading` for sections, `=== subheading` for subsections
4. Add `// Slide: [title]` before each major content block
5. Write 200–250 words per slide
6. Include all figures, formulas, and algorithms from source
7. Compile: `typst compile [filename.typ] --root .` or `./.claude/templates/compile.sh [filename.typ]`
8. Lint: `typstyle --inplace --wrap-text -l 80 [filename.typ]`
9. Verify PDF visually for figure sizing and layout

#pagebreak()

== Results

=== Analysis

// Slide: Result Analysis

Use #pagebreak() strategically between major sections to improve readability.

Content for additional sections follows the same pattern: clear headings,
descriptive text, proper emphasis, and integration of figures and formulas.

#strong[Key takeaway]: Each method has distinct strengths. Matching method to
design and checking assumptions carefully produces credible causal inference.

== Conclusion

=== Summary

// Slide: Key Takeaways

Conclude sections with summary points and key insights. Highlight how concepts
connect to the broader framework or course themes.

#strong[Summary]:
- Point 1: First key insight
- Point 2: Second key insight
- Point 3: Third key insight

Complete the chapter by ensuring all source material is covered, all figures are
included, all formulas are preserved, and the document compiles cleanly.
