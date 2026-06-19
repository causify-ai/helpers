# Overview
- One paragraph summary of what the module does
- What problem it solves and its role in the codebase
- Key design decisions visible from the code

# Architecture (C4 Model)
- Organize documentation using C4 levels:
  - **C1 (Context)**: How this module fits in the broader system
    - What external systems/services it interacts with
    - Mermaid C4 context diagram showing the module and its neighbors
  - **C2 (Container)**: The module's internal structure
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
