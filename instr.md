In linters2/cc_lint.py --files dev_scripts_helpers/ai/test/test_cc_lib.py --add_todos --mode stateless --dry_run

1) Print the command in the tmp file

2) Convert

- Do NOT edit the file to comply with a rule. Instead, for every
  violation, add a comment immediately above the offending line in the
  form:
  ```
  # TODO(...): <what to do and why> (<rule_file>:<rule header line>)
  ```
  E.g.:
  ```
  # TODO(...): Do this and that (testing.rules.md:## Use Context Manager Syntax for Multiple Mocks)
  ```
- Look up the rule file to find the `<rule header line>` (the
  header line text, including its leading `#`s) that the violated rule
  came from
- Do not otherwise change the file: do not fix the violation, only add
  the TODO comment

into

- Do NOT edit the file to comply with a rule. Instead, for every
  violation, add a comment immediately above the offending line in the
  form:
  ```
  # TODO(...): <what to do and why> (<rule_file>:<rule header line>)
  ```
  E.g.:
  ```
  # TODO(...): Do this and that (testing.rules.md:## Use Context Manager Syntax for Multiple Mocks)
  ```
  - Look up the rule file to find the `<rule header line>` (the
    header line text, including its leading `#`s) that the violated rule
    came from
  - Do not otherwise change the file: do not fix the violation, only add
    the TODO comment

3) Convert

- Check the files below against the rules and conventions above and add TODO comments for violations without asking questions to the user
  - `dev_scripts_helpers/ai/test/test_cc_lib.py`

into

- Check the files below against the rules and conventions above and add TODO
  comments for violations without asking questions to the user
  - `dev_scripts_helpers/ai/test/test_cc_lib.py`

4) Convert
- Do not revisit rules applied earlier
        ```
        # Testing Philosophy

## Test One Thing
- A test class tests only one function or class
- A test method tests only one case
- Keeps failures easy to diagnose: one thing broken means one test fails
        ```

into

- Do not revisit rules applied earlier
  ```
  # Testing Philosophy

  ## Test One Thing
  - A test class tests only one function or class
  - A test method tests only one case
  - Keeps failures easy to diagnose: one thing broken means one test fails
  ```

4) Create end-to-end unit tests for the various --dry_run using a mocked up
   rules like calling

   linters2/cc_lint.py --files dev_scripts_helpers/ai/test/test_cc_lib.py --add_todos --mode stateless --dry_run

   for different --mode and --add_todos storing how the tmp file will look like

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
