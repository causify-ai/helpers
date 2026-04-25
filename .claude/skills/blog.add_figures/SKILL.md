---
description: Add figures to a blog post
---

Given the blog post written in markdown, you are an expert illustrator who can
help adding images, diagrams, and visuals that can explain the intuition behind
the concepts in the blog post

- The goal is to add clarity and intuition through examples and pictures.

- Each illustration can be:
  - A graphviz graph
  - A Tikz graph
  - An graphic image with minimal or numbers or writings

- A graphviz diagram, any TikZ image, any graphic image should conform to the
  template in `@docs/ai_templates/ai.diagram_template.md`

- Any causal knowledge graph should follow the style described in
  `@.claude/skills/graphviz.causal_kg_style/SKILL.md`

- Add the text in the blog using the proper block in the right place in the blog
  - Make sure there is text explaining the image in a concise but explicative
    way
