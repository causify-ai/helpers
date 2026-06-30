- Make the following executables compatible in terms of options
  ```
  i git_files
  i git_branch_diff
  linters2/lint.py
  linters2/lint_cc.py
  ```

by using

  # File selection arguments using hparser helper.
  hseinout.add_file_selection_args(parser)
  # File type filters using hparser helper.
  hseinout.add_file_type_filter_args(parser, file_types_default="py,ipynb")

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

# Create a plan, if needed
- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
