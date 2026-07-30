Run the skill /coding.todoai_gp on each of the TODO, one at the time

./dev_scripts_helpers/dockerize/dockerized_pandoc.py:34:# TODO(ai_gp): Move all the non-CLI functions to
./dev_scripts_helpers/testing/pytest_multi_build.py:14:# TODO(ai_gp): Add comments for each command
./dev_scripts_helpers/testing/test/test_pytest_failed_multi_build.py:18:# TODO(ai_gp): Replace a call to this with a call to
./dev_scripts_helpers/testing/test/test_pytest_failed_multi_build.py:700:        # TODO(ai_gp): Add expected and self.assert_equal
./dev_scripts_helpers/testing/test/test_pytest_failed_multi_build.py:728:        # TODO(ai_gp): Pass an expected value and compare it with self.assert_equal
./dev_scripts_helpers/git/git_hooks/gitleaks.py:40:    # TODO(ai_gp): Use only the --no-abort-on-error.
./helpers/hstring.py:85:# TODO(ai_gp): Move to hpython_code.py
./helpers/hstring.py:113:# TODO(ai_gp): Move to hpython_code.py
./helpers/hstring.py:137:# TODO(ai_gp): Move to hpython_code.py
./dev_scripts_helpers/git/git_create_issue_and_branch.py:52:        # TODO(ai_gp): Use hio.from_file.
./dev_scripts_helpers/git/git_create_issue_and_branch.py:208:        # TODO(ai_gp): Move the body of this try-except in a different function
./dev_scripts_helpers/github/print_master_ci_state.py:124:    # TODO(ai_gp): Move up and import as datetime.datetime
./.claude/control_cc_commit.py:36:    # TODO(ai_gp): Is there a function in json in the helpers we can use?
./.claude/control_cc_commit.py:51:    # TODO(ai_gp): Is there a function in json in the helpers we can use?
./.claude/skills/coding.annotate_with_todoai/SKILL.md:29:  # TODO(ai_gp): Apply <rule> before the point with violation
./.claude/skills/coding.annotate_with_todoai/SKILL.md:33:  # TODO(ai_gp): Apply "Replace Checking Invariants with `assert_equal` - Do not use multiple `assertIn()` calls to check individual pieces of a string output; instead compare the entire output with `assert_equal()`"
./helpers/test/test_hunit_test_purification.py:66:    # TODO(ai_gp): Factor out more code in an helper function
./helpers/test/test_hunit_test_purification.py:278:    # TODO(ai_gp): Factor out more code.
./helpers/test/test_hunit_test_purification.py:629:        # TODO(ai_gp): Assign super_module_root and then pass it. Do the same
./helpers/test/test_hunit_test_purification.py:1240:        # TODO(ai_gp): Move the umock.patch to the helper function to simplify
./helpers/test/test_hunit_test_purification.py:1331:        # TODO(ai_gp): Use a """ and dedent instead of "..." "..."
./helpers/test/test_hunit_test_purification.py:1366:        # TODO(ai_gp): Use a """ like the TODO above.
./helpers/test/test_hunit_test_purification.py:1380:        # TODO(ai_gp): Use a """ like the TODO above.
./helpers/test/test_hunit_test_purification.py:1386:        # TODO(ai_gp): Use a """ like the TODO above.

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
