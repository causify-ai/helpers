---
description: Write a practical technical tutorial for engineers, covering one tool or concept in 10-15 mins of reading time
model: opus
---

# Purpose

- Write clear, hands-on tutorials that help engineers quickly learn a new tool,
  technique, or concept
- Tutorials should be practical and immediately applicable, not theoretical
  surveys

# Audience

- Target: Software engineers and technical practitioners
- Skill level: General to intermediate (some programming knowledge assumed)
- Goal: Enable readers to use the tool/technique effectively after reading

# Tutorial Structure

- Follow this outline:

  1. **Introduction** (1-2 paragraphs)
     - What is this tool/concept?
     - Why should engineers care? (What problem does it solve?)
     - When to use it (not just "always")
     - What are other tools that solve similar problems
     - Links to official docs

  2. **Prerequisites** (if any)
     - Required knowledge or tools
     - Assumed environment (OS, languages, etc.)

  3. **Installation/Setup** (if applicable)
     - Clear, copy-paste ready commands
     - Verify installation with a simple test

  4. **Core Concepts** (brief)
     - Explain 2-3 key ideas
     - Use examples, not abstractions

  5. **Hands-On Examples** (bulk of tutorial)
     - 3-5 practical examples of increasing complexity
     - Each example solves a real problem
     - Include expected output
     - Build toward a useful, realistic workflow

  6. **Tips & Gotchas**
     - Common mistakes and how to avoid them
     - Performance or compatibility notes

  7. **Next Steps** (optional)
     - Where to learn more
     - Related tools or advanced topics

# Guidelines

## Length
- Target: 10-15 minutes reading time (roughly 1500-2500 words)
- Avoid: Overly long tutorials that cover everything; focus on the 80% use case

## Template
- Use `website/docs/blog/posts/draft.blog_template.md` as template

## Code Examples
- Use copy-paste ready code blocks with `bash` or language-specific syntax highlighting
- Include expected output so readers know it worked
- For shell commands, show the prompt style, e.g.,
  - On macOS and Linux using the official installer:
    ```bash
    > curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

## Platform Coverage
- Focus on macOS and Linux instructions

## Tone & Voice
- Direct and practical ("use this when..." not "one might consider...")
- Active voice, short sentences
- Assume readers are busy engineers
- Don't be overly casual

## Visuals
- Include diagrams only if they clarify workflow or architecture
- Use simple diagrams using mermaid, graphviz, or reference external images if
  needed
- Don't over-decorate

# Formatting
- Follow `.claude/skills/markdown.rules.md` for markdown conventions
- Use `##` for main sections, `###` for subsections
- Use verbatim for tool names on first mention
  - E.g., `ripgrep` is a search tool
- Use code blocks for all commands, config files, and output

# Examples to Reference
- Located in `website/docs/blog/posts/`
  - `website/docs/blog/posts/uv_in_30_mins.md`: Tool intro with installation,
    core concepts, examples
  - `website/docs/blog/posts/ripgrep_in_30_mins.md`: Search tool with practical
    use cases
  - `website/docs/blog/posts/python_packaging_in_30_mins.md`: Concept-based
    tutorial with workflow
  - `website/docs/blog/posts/mdm_unified_markdown_manager.md`: Multi-tool
    tutorial

- Study these for structure, tone, depth, and length.
