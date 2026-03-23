---
description: Identify and replace Python code with code in the `helpers` package
---

- You are a senior Python engineer with strong experience in refactoring and
  codebase hygiene.
- I will provide references to one or more Python source files
- Your task is to read and analyze the code across these files and identify
  what functions can be replaced with functions from the `helpers`
- The most important packages are:
  - `helpers/hdbg.py`
    - Debugging utilities with specialized assertions, logging, and fatal error handling
  - `helpers/hio.py`
    - Filesystem operations, file read/write, and directory management utilities
  - `helpers/hsystem.py`
    - System interaction: shell commands, environment variables, process management
- Do not changed the behavior of the code
