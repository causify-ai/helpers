All tests below using hunteuti.capture_sys_calls 

./dev_scripts_helpers/git/test/test_create_git_worktree.py
./dev_scripts_helpers/notebooks/test/test_jupytext.py
./linters2/test/test_lint.py
./helpers/test/test_hunit_test_utils.py
./dev_scripts_helpers/system_tools/test/test_lib_rig.py
./dev_scripts_helpers/documentation/test/test_replace_latex.py
./dev_scripts_helpers/documentation/test/test_open_md.py
./dev_scripts_helpers/testing/test/test_pytest_multi_build.py
./dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py

should 
1) use hunteuti.assert_sys_calls(self, invocations, expected, dedent=True)
2) use
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
3) No test should call hunteuti.sys_calls_to_str or pprint.pformat(expected_sys_calls)

- Update the actual output since we have updated the function formatting the
  output

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

