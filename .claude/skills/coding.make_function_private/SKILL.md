---
description: Identify private / public functions in a file and rename them with an underscore or not
model: haiku
---

For each function `<FUNC>` in the passed Python file `<FILE>`, determine if it
should be private or public by checking if it's called by Python files or
Jupyter notebooks **outside `<FILE>`** (including sibling scripts, parent
package modules, test files, and CLI entry points)

## Definition: External Files
**External files** = any Python file or Jupyter notebook **outside the target
file**, including:

- Sibling scripts in the same package (e.g., `notes_to_pdf.py` calling functions
  from `lib_notes_to_pdf.py`)
- Parent/sibling modules that import from the target
- Test files that test the target module
- CLI entry point scripts

- **Note:** Functions that form the public API of a library module should be
  PUBLIC, even if they're not called from a `__main__` entry point. If a module
  exports utility functions for use by other scripts in the package, those are
  PUBLIC functions

# Private Functions
- If the function `<FUNC>` is not called by any external file, then it should be
  a private function and should be renamed and prepended with a `_`
  - E.g., `def function` -> `def _function`
  - Include only internal utility functions, helpers, and implementation details
- Modify all the callers of the function `<FUNC>` to use the new name

## Example: Private Functions
```python
# lib_helper.py
def public_function():
    _internal_helper()  # Only called within this file → should be private

def _internal_helper():
    pass
```

# Public Functions
- If the function `<FUNC>` is called by external files, then it should be a
  public function and its name should **NOT** start with `_`
  - This includes functions in shared utility modules called by sibling scripts
- Modify all callers (both external and internal) of the function to use the new
  name

## Example: Public Functions
```python
# lib_notes_to_pdf.py
def preprocess_notes(file_name, prefix):  # Called by notes_to_pdf.py → PUBLIC
    _internal_step_1(file_name)  # Private helper

def _internal_step_1(file_name):  # Only used within lib_notes_to_pdf.py → PRIVATE
    pass
```

# Workflow
1. **Find all functions** in `<FILE>`
2. **For each function**, search the entire codebase for external calls:
   ```bash
   grep -r "module_name.function_name\|from module import function_name" --include="*.py" --include="*.ipynb"
   ```
3. **Classify** as public or private based on external usage
4. **Rename** functions and update all call sites (both files)
5. **Verify** changes

# Verification
- [ ] Grep in the entire codebase to confirm all function calls were renamed
      correctly
  ```bash
  grep -r "old_name\|new_name" --include="*.py" --include="*.ipynb"
  ```
- [ ] Run pyright to verify type correctness of modified function invocations
- [ ] Run unit tests for the modified files to ensure nothing broke
