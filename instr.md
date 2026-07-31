Run the skill /coding.todoai_gp on each of the TODO, one at the time

./helpers/hstring.py:85:# TODO(ai_gp): Move to hpython_code.py
./helpers/hstring.py:113:# TODO(ai_gp): Move to hpython_code.py
./helpers/hstring.py:137:# TODO(ai_gp): Move to hpython_code.py
./dev_scripts_helpers/testing/test/test_pytest_failed_multi_build.py:56:        # TODO(ai_gp): Move this code to helper since it's shared across tests.
./dev_scripts_helpers/testing/test/test_pytest_failed_multi_build.py:105:    # TODO(ai_gp): Can this be factored out outside multiple classes.
./dev_scripts_helpers/testing/test/test_pytest_failed_multi_build.py:136:        # TODO(ai_gp): Move this code to helper since it's shared across tests.
./dev_scripts_helpers/testing/test/test_pytest_failed_multi_build.py:180:        # TODO(ai_gp): Move this code to helper since it's shared across tests.
./dev_scripts_helpers/testing/test/test_pytest_failed_multi_build.py:287:        # TODO(ai_gp): Move this code to helper since it's shared across tests.
./dev_scripts_helpers/testing/test/test_pytest_failed_multi_build.py:380:        # TODO(ai_gp): Move this code to helper since it's shared across tests.
./dev_scripts_helpers/testing/test/test_pytest_failed_multi_build.py:458:        # TODO(ai_gp): Move this code to helper since it's shared across tests.
./dev_scripts_helpers/testing/test/test_pytest_failed_multi_build.py:560:    # TODO(ai_gp): Factor out common code in a helper function.
./dev_scripts_helpers/testing/test/test_pytest_failed_multi_build.py:591:        # TODO(ai_gp): Add an expected = "" and a self.assert_equal inside
./dev_scripts_helpers/testing/test/test_pytest_failed_multi_build.py:625:        # TODO(ai_gp): Add an expected = "" and a self.assert_equal inside
./dev_scripts_helpers/testing/test/test_pytest_failed_multi_build.py:862:        # TODO(ai_gp): Add expected and call self._check_colorized_output

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
