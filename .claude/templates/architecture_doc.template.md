# Overview

- One paragraph (or a few bullets) summarizing what the component does
- What problem it solves and its role in the broader codebase
- Key design decisions visible from the code
- Who uses it and how (CLI, library import, service, etc.)

# Architecture (C4 Model)

- Organize the documentation using the four C4 levels, one `##` subsection each
- Each level has:
  - A one-line description of what the level captures
  - Exactly one focused Mermaid diagram (add more only when one cannot stay
    readable)
  - A short prose explanation referencing actual code artifacts (function,
    class, file names)

## C1 (Context)

- Describes how the component fits in the world

- Mermaid diagram showing the component, its users, and the external
  systems/services/tools it interacts with

- Prose: what role the component plays, who its users are, and which external
  systems it coordinates

## C2 (Container)

- Describes the high-level technical blocks inside the component

- Mermaid diagram (e.g. class or grouped graph) showing the main internal
  blocks and how they relate

- Prose: list each block and its responsibility

## C3 (Component)

- Describes the components inside a container and how they interact

- Mermaid flowchart diagram for the main call chain or runtime flow

- Prose: describe the key interactions between components (state shared, data
  passed between stages, control flow)

- Keep this focused: include only architecturally significant interactions, not
  every call

## C4 (Code)

- Describes how the components are implemented

- Primary call flow as a nested code block, e.g.:
  ```
  entry_point()
    - orchestrator()
      - stage_a()
      - stage_b()
      - finalize() [optional]
  ```

- Notable code patterns, algorithms, or data structures
  - Include only what is non-obvious or architecturally significant

## Key Functions / Classes

- Table of the main public functions/classes:

  | Name | Purpose | Returns |
  |------|---------|---------|
  | `name()` | What it does | What it returns / produces |

- One row per public API member; omit private helpers unless central to the
  design

## External Dependencies

- Table of external libraries and modules the component depends on:

  | Module | Purpose |
  |--------|---------|
  | `module_name` | What it is used for |

- Include external CLI tools or services as rows when relevant

# Critique and Improvements

## Strengths

- What the design and implementation do well
- One bullet per strength, tied to a concrete aspect of the code

## Weaknesses and Assumptions

- One numbered item per issue or limitation, each with:
  - A short description of the problem
  - A **Fact** or **Assumption** label:
    - **Fact** (code-derived)
    - **Assumption** (inferred): state what is being assumed, e.g. "Assumes a
      single execution per process"
  - An **Impact** line: what breaks or degrades because of it
