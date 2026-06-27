---
description: Write architecture documentation for a Python file
model: haiku
---

# Goal

- Analyze a Python file `<FILE>` passed by the user and generate or update
  `README.<FILE>.md` with architecture documentation in Markdown using bullet
  points

# Workflow

## Step 1: Read File

- Read the file `<FILE>` to understand its code structure:
  - Parse all function and class definitions
  - Identify the public API (exported functions, classes, constants)
  - Trace function call relationships (which functions call which)
  - Identify external dependencies (imports from other modules, libraries)
  - Note the module's purpose and role in the broader system

## Step 2: Check the Existing Readme

- Check if `<FILE>.README.md` already exists:
  - If it exists, read it and plan what to update
  - If it does not exist, plan content from scratch

- Make sure there is a note in the docstring of the corresponding files
  pointing to `<FILE>.README.md`, e.g.,
  ```
  For a description of the architecture of this file 

## Step 3: Generate Document

- Follow the template `.claude/templates/architecture_doc.template.md`

- Generate the documentation with these sections using markdown and
  bullet points following 
  - Follow the rules in `.claude/skills/markdown.rules.md` for markdown formatting
  - Follow the rules in `.claude/skills/text.rules.md` for text formatting

## Step 4: Update Document

- Write the results to `<FILE>.README.md` in the same directory as `<FILE>`

## Step 5: Lint Document
  ```bash
  > lint_txt.py -i `<FILE>.README.md`
  ```

# Conventions

- Use conventions summarized in 
  `docs/documentation_meta/all.architecture_diagrams.explanation.md`

- Use Mermaid diagrams (` ```mermaid `) for all architecture diagrams
- The C4 notation with Mermaid should follow the standard C4 layout:
  - `Person` for external users
  - `System` for external systems
  - `Container` for application containers/processes
  - `Component` for internal components
  - Use `Rel` for relationships between elements
- Label diagrams clearly with what they represent
- Reference actual code artifacts (function names, class names, file paths)
  when available
- Distinguish facts from assumptions:
  - For facts (code-derived):
    - E.g., "The function `process_data()` calls `validate_input()` before
      computing results"
  - For assumptions:
    - E.g., "This likely handles error cases based on the try-except blocks
      present"

- Focus documentation on:
  - Maintainability: How easy is it to modify and extend this code?
  - Extensibility: How well does the design accommodate new features?
  - Operational understanding: What does someone need to know to work with
    this code?

## Formatting
- Follow the rules in `.claude/skills/coding.rules.md` for Python code style
- Follow the rules in `.claude/skills/markdown.rules.md` for markdown formatting
- Follow the rules in `.claude/skills/text.rules.md` for text formatting

# Constraints

- Do not modify the original `<FILE>`
  - Only create/update `<FILE>.README.md`
- Do not over-document: avoid repeating what is obvious from the code
- Keep diagrams focused: one clear diagram is better than three cluttered
  ones
- Do not invent architecture that is not present in the code
- When uncertain about intent, mark the observation as an assumption
- Do not use emojis or decorative formatting

# Verification

- Verify that `<FILE>.README.md` was created or updated
- Verify that at least one Mermaid diagram is present
- Verify that assumptions are clearly labeled as assumptions
- Verify that the file renders correctly as GitHub-flavored Markdown
