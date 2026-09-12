---
description: Identify and replace Python code with code in the `helpers` package
model: haiku
---

# Goal
I will provide references to one or more Python source files `<FILES>`. Read
and analyze the code across these files and identify what functions can be
replaced with functions from `helpers`.

# Workflow
- The most important packages are:
  - `helpers/hdbg.py`
    - Debugging utilities with specialized assertions, logging, and fatal error
      handling
  - `helpers/hio.py`
    - Filesystem operations, file read/write, and directory management utilities
  - `helpers/hsystem.py`
    - System interaction: shell commands, environment variables, process
      management
- Do not change the behavior of the code

# Verification
- [ ] Confirm replaced calls preserve the original behavior
- [ ] Run the file's unit tests to confirm nothing broke
