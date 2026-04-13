<!-- toc -->

- [Explanation: Reorder_Python_Code.Py](#explanation-reorder_python_codepy)
  * [Introduction / Motivation](#introduction--motivation)
  * [Core Concepts](#core-concepts)
- [Section Name](#section-name)
  * [How It Works](#how-it-works)
  * [Prompt](#prompt)

<!-- tocstop -->

# Explanation: Reorder_Python_Code.Py

## Introduction / Motivation

- **What is this about?**
  - A tool for reorganizing Python code from a single monolithic file into
    multiple smaller, logically-organized files
  - Enables splitting large Python modules by extracting and reordering
    functions based on a declarative markdown map

- **What problem does it solve?**
  - Large Python files (e.g., [`/helpers/hpandas.py`](/helpers/hpandas.py) with
    100+ functions) become difficult to maintain and navigate
  - Manual code reorganization is error-prone and time-consuming
  - Need to preserve function implementations exactly while reorganizing them
    across multiple files
  - Maintains consistent section separators and code organization across split
    files

- **Who needs to understand it?**
  - Developers refactoring large Python modules into smaller, more maintainable
    components
  - Teams performing codebase restructuring or modularization initiatives
  - Anyone needing to split monolithic utility libraries into focused
    sub-modules

## Core Concepts

- **Markdown Map File**: A declarative specification that defines how to
  organize functions from a source file
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
  #
  # Section Name
  #
  ```
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

## Prompt

test/test_hpandas.py needs to be split in different files

Create a file file_map.md to map how test files should be organized so that the
file test/test_XYZ.py tests only functions of the file XYZ.py

The format should be the same as
dev_scripts_helpers/coding_tools/reorder_python_code.map_example.md

The file should be usable by reorder_python_code.py to split files
