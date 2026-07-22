---
description: Propose visuals for the slides
model: haiku
---

# Goal
- Given a markdown file with slides, propose visuals (e.g., diagrams, pictures,
  tables)

## Read Context
- Read `.claude/skills/slides.rules.md` for the slides conventions and rules
- Read `.claude/skills/visuals.rules.md` to understand the rules for the visuals

## Propose a Visual for Each Slide
- If a slide doesn't contain a visual element, consider what can be used to
  illustrate the concepts visually
- E.g., from `## Types of Illustrations` in `.claude/skills/visuals.rules.md`
  - Table
  - Mermaid graph
  - Graphviz diagram
  - TikZ diagram
  - Images
  - Website screenshots

## Ask User to Confirm and Decide
- Make numbered list of proposed changes for the user
- Once user confirms changes, perform the changes

## Constraints
- Maintain the structure of the text and keep the content of the existing text
