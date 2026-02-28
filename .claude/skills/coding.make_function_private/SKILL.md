---
name: coding.make_function_private
description: Identify functions not called externally and rename them with a leading underscore to make them private
---

You are an expert Python software engineer

For each function and class in the passed Python file, check if it's a function
called by other Python files or Jupyter notebooks

If the function is not called by any other file, then it should be a private
function and should be rename and prepended with a `_`

- E.g., `def function` -> `def _function`

Then modify the callers of the function to use the new name
