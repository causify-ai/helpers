<!-- toc -->

- [Introduction / Motivation](#introduction--motivation)
- [Core Concepts](#core-concepts)
- [How It Works](#how-it-works)
- [Design Rationale](#design-rationale)
- [Tradeoffs And Alternatives](#tradeoffs-and-alternatives)
  * [Current Approach](#current-approach)
  * [Alternative Approach](#alternative-approach)

<!-- tocstop -->

# Explanation: reorder_python_code.py

## Introduction / Motivation

- **What is this about?**
  - A tool for reorganizing Python code from a single monolithic file into
    multiple smaller, logically-organized files
  - Enables splitting large Python modules by extracting and reordering functions
    based on a declarative markdown map

- **What problem does it solve?**
  - Large Python files (e.g., `helpers/hpandas.py` with 100+ functions) become
    difficult to maintain and navigate
  - Manual code reorganization is error-prone and time-consuming
  - Need to preserve function implementations exactly while reorganizing them
    across multiple files
  - Maintains consistent section separators and code organization across split
    files

- **Who needs to understand it?**
  - Developers refactoring large Python modules into smaller, more maintainable
    components
  - Teams performing codebase restructuring or modularization initiatives
  - Anyone needing to split monolithic utility libraries into focused sub-modules

## Core Concepts

- **Markdown Map File**: A declarative specification that defines how to organize
  functions from a source file
  - Level 1 headers (`# filename.py`) specify target output files
  - Level 2 headers (`## Section Name`) define logical groupings with formatted
    comment separators
  - Bullet lists contain function names to extract and place in each section

- **Text-Based Parsing**: The script operates on source code as text rather than
  using AST (Abstract Syntax Tree) parsing
  - Uses regular expressions to identify function/class boundaries
  - Preserves exact formatting, comments, and whitespace from original source
  - Avoids complexities of AST manipulation while maintaining code fidelity

- **Module Header Preservation**: Each output file maintains the original
  module's header components
  - Module-level docstring
  - Import statements
  - Module-level constants and variables
  - Ensures each split file remains a valid, self-contained Python module

- **Section Separators**: Formatted comment blocks that visually organize
  functions within files ```python
  # #############################################################################
  # Section Name
  # #############################################################################
  ```

## How It Works

The script executes in six logical stages:

**Step 1: Parse Map File**
- Read markdown map file and extract file structure
- Build dictionary mapping target filenames to sections and function lists
- Each section contains section name and list of function names

**Step 2: Extract Function Boundaries**
- Scan source file to identify all top-level functions and classes
- Use regex patterns to find function/class definitions
- Calculate line ranges for each function by finding next definition at same
  indentation level
- Store mapping of function names to (start_line, end_line) tuples

**Step 3: Identify Module Header**
- Locate end of module header (docstring, imports, module-level constants)
- Find first top-level function/class definition
- Everything before first definition becomes reusable header

**Step 4: Create Target Files**
- For each target file specified in map:
  - Start with copy of module header
  - Process sections in order

**Step 5: Add Section Separators**
- Insert formatted comment blocks between sections
- Create visual separation matching level 2 headers from map file

**Step 6: Extract and Reorder Functions**
- For each function in section:
  - Look up line range from function boundaries mapping
  - Extract exact text of function from source
  - Append to target file in order specified by map
  - Add blank line after each function

```text [Map File] → Parse Structure → [File Mapping Dict] ↓ [Source File] →
Extract Functions → [Function Boundaries Dict] ↓ ← Combine Information ← ↓
[Target Files] ← Generate with Header + Sections + Functions ```

## Design Rationale

**Goals:**
- **Exact Preservation**: Maintain source code exactly as written, including all
  formatting, comments, and docstrings
- **Declarative Specification**: Use simple, human-readable markdown format for
  reorganization maps
- **Simplicity**: Avoid complex AST parsing in favor of reliable text-based
  pattern matching
- **Reproducibility**: Same map file always produces same output structure

**Constraints:**
- **Text-Based Only**: Must not parse Python AST to avoid issues with:
  - Syntax errors in partially-written code
  - Complex parsing edge cases
  - Potential formatting changes from AST round-tripping

- **Top-Level Only**: Only handles top-level functions and classes, not nested
  definitions
  - Simplifies boundary detection logic
  - Matches common use case of splitting utility modules

- **Manual Map Creation**: Requires human to create reorganization map
  - Ensures logical, intentional organization decisions
  - Allows semantic grouping that automated tools cannot determine

**What would go wrong with alternate approaches?**
- **AST-based parsing**: Could fail on syntactically invalid code during
  refactoring, introduce subtle formatting changes, require complex AST
  manipulation
- **Automated splitting**: Without human guidance, automated tools cannot
  determine semantic relationships or logical groupings
- **Direct file editing**: Manual copy-paste is error-prone, time-consuming, and
  difficult to reproduce or modify

## Tradeoffs And Alternatives

### Current Approach

**Advantages:**
- Robust handling of any valid Python syntax without parsing complexity
- Preserves exact formatting, whitespace, and comment placement
- Simple, transparent operation that's easy to debug and understand
- Map file serves as documentation of reorganization structure
- Works with incomplete or temporarily invalid Python code

**Drawbacks:**
- Requires manual creation of map file (cannot auto-generate organization)
- Only handles top-level definitions (nested functions/classes stay with parent)
- Cannot automatically detect or update cross-file dependencies
- Does not handle import statement optimization (may leave unused imports)
- Text-based regex matching could theoretically have edge cases with unusual
  formatting

### Alternative Approach

**AST-Based Code Reorganization:**

**Advantages:**
- Could automatically analyze dependencies and suggest groupings
- More "correct" understanding of Python code structure
- Could handle nested definitions properly
- Could automatically update imports and remove unused ones

**Drawbacks:**
- Significantly more complex implementation
- Fails on syntactically invalid code (common during refactoring)
- May introduce formatting changes during AST round-trip
- Harder to debug when issues occur
- Cannot preserve exact original formatting
- Much larger dependency on Python's `ast` module internals

**Decision Rationale:** The text-based approach was chosen because it prioritizes
reliability and simplicity for the common case of reorganizing well-formed
utility modules. The trade-off of requiring manual map creation is acceptable
given the tool's purpose is intentional, human-guided refactoring rather than
automated analysis.
