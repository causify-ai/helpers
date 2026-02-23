- Implement all the `TODO(ai_gp)` in the passed file

- In a `TODO:` the sign `-> XYZ` means "rename to XYZ"
  - Make sure to update all the references to those objects in the code base
    - E.g., for files, look for and update imports
    - E.g., for functions, find the callers in notebooks ipynb, Python files,
      and other files and update those references
    - Update documentation in txt and md files
  - If needed, run corresponding unit tests to make sure the code works

- For a file containing Python code you MUST apply the rules from
  `docs/ai_prompts/coding.format_rules.md`

- For a file storing unit tests (i.e., whose base name starts with `test_*.py`)
  you must apply the rules from `docs/ai_prompts/testing.format_rules.md`

- For a notebook ipynb and its paired Python file, you MUST apply the rules from
  `docs/ai_prompts/notebook.format_rules.md`
