---
description: Write architecture documentation for a Python file
model: haiku
---

# Goal

- Analyze a Python file `<FILE>` passed by the user and generate or update
  `README.<FILE>.md` with architecture documentation in Markdown using bullet
  points

# Workflow

## Step 1

- Read the file `<FILE>` to understand its code structure:
  - Parse all function and class definitions
  - Identify the public API (exported functions, classes, constants)
  - Trace function call relationships (which functions call which)
  - Identify external dependencies (imports from other modules, libraries)
  - Note the module's purpose and role in the broader system

## Step 2

- Check if `README.<FILE>.md` already exists:
  - If it exists, read it and plan what to update
  - If it does not exist, plan content from scratch

## Step 3
- Generate the documentation with these sections (using `## ` headers):

  ```
  # Overview
  - One paragraph summary of what the module does
  - What problem it solves and its role in the codebase
  - Key design decisions visible from the code

  # Architecture (C4 Model)
  - Organize documentation using C4 levels:
    - **C1 - Context**: How this module fits in the broader system
      - What external systems/services it interacts with
      - Mermaid C4 context diagram showing the module and its neighbors
    - **C2 - Container**: The module's internal structure
      - Main classes, their responsibilities, and how they relate
      - Mermaid class diagram showing relationships
    - **C3 - Component**: Key functions and their interactions
      - Function call graph showing which functions call which
      - Mermaid flowchart or sequence diagram for the main call chain
    - **C4 - Code**: Key implementation details
      - Notable code patterns, algorithms, or data structures
      - Only include what is non-obvious or architecturally significant

  ## Key Functions and Call Flow
  - List the main public functions/classes with:
    - Function signature
    - Short description of purpose
    - What it returns
  - Describe the call flow between the main functions using a Mermaid
    sequence or flowchart diagram

  ## External Dependencies
  - List external libraries and modules the file depends on
  - For each dependency, note what it is used for

  ## Critique and Improvements
  - Analyze the current architecture and implementation:
    - **Strengths**: What the code does well
    - **Weaknesses**: Identified issues or design limitations
    - **Improvement suggestions**: Concrete, actionable recommendations
  - Clearly label which observations are:
    - Derived directly from code (facts)
    - Inferred or assumed (assumptions)
  ```

## Step 4

- Write the results to `README.<FILE>.md` in the same directory as `<FILE>`

# Conventions

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
  - Only create/update `README.<FILE>.md`
- Do not over-document: avoid repeating what is obvious from the code
- Keep diagrams focused: one clear diagram is better than three cluttered
  ones
- Do not invent architecture that is not present in the code
- When uncertain about intent, mark the observation as an assumption
- Do not use emojis or decorative formatting

# Verification

- Verify that `README.<FILE>.md` was created or updated
- Verify that at least one Mermaid diagram is present
- Verify that the Critique and Improvements section contains at least 2
  improvement suggestions
- Verify that assumptions are clearly labeled as assumptions
- Verify that the file renders correctly as GitHub-flavored Markdown
