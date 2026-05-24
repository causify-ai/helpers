---
description: Create a detailed markdown outline (notebook_outline file) for a Jupyter notebook, specifying each cell's content, purpose, visuals, and interactivity to teach concepts through example and discovery
---

## Description

- **Input**: Teaching concepts, learning objectives, or educational content
- **Output**: A `notebook_outline.<tag>.md` markdown file that describes each
  notebook cell
  - Do not write actual code, but describe what each cell will contain and
    accomplish
- **Purpose**: Design the pedagogical structure and flow of an interactive
  tutorial notebook

# Pedagogical Goals

Design the notebook to achieve:
- **Strong intuition**: Build understanding through concrete examples, not theory
- **Visual explanation**: Use plots, diagrams, and visual feedback
- **Incremental building**: Each cell builds on previous concepts
- **Interactive discovery**: Use widgets to let students change variables and see
  results in real-time

# Cell Outline Structure

For each cell, specify:
- **Cell type** (markdown, code, or visualization)
- **Purpose** (what concept or skill it teaches)
- **Content description** (what examples, explanations, or demonstrations it
  includes)
- **Key variables or parameters** (for interactive widgets)
- **Expected output or visualization** (what the student will see)

# Format of Notebook

## Rules and Conventions
- Always follow the conventions and guidelines in
  `.claude/skills/notebook.rules.md`

## Content Focus
- Focus only on examples without repeating content from the slides
- Each cell should build incrementally on previous concepts
- Emphasize discovery through interaction rather than explanation

# Important
- When writing markdown you must follow the rules and conventions in
  `.claude/skills/markdown.rules.md`

- When writing bullet points you must follow the rules and conventions in
  `.claude/skills/text.rules.md`
