In TODO(ai_gp2) in src/umd_classes1/helpers_root/dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py

Use
  expected = """
  ...
  """
  expected = hprint.dedent(expected)
  instead of 
  ```
  # Check outputs.
  expected_sys_calls = [
      {
          "args": (
              "jupytext --update-metadata "
              """'{"jupytext":{"formats":"ipynb,py:percent"}}' """
              f"{ipynb_file}",
          ),
          "function": "hsystem.system",
          "kwargs": {},
      },
      {
          "args": (
              f"jupytext --test --stop --to py:percent {ipynb_file}",
          ),
          "function": "hsystem.system",
          "kwargs": {},
      },
      {
          "args": (f"jupytext --to py:percent {ipynb_file}",),
          "function": "hsystem.system",
          "kwargs": {},
      },
      {
          "args": (f"git add {scratch_dir}/test_notebook.py",),
          "function": "hsystem.system",
          "kwargs": {},
      },
  ]
  expected_str = pprint.pformat(expected_sys_calls)
  hunteuti.assert_sys_calls(self, sys_calls, expected_str)
  ```

No test should call hunteuti.sys_calls_to_str or pprint.pformat(expected_sys_calls)

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing testing code you must always follow the instructions in
  `.claude/skills/testing.rules.md`

# Create a plan, if needed
- If the task is not perfectly clear:
  - You MUST not perform it
  - Ask for clarifications
  - Create a `plan.md` in the same directory with 5 bullet points explaining what
    the plan is
  - Wait for the user to confirm

