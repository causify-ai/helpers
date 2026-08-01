Run the skill /coding.todoai_gp on each of the TODO, one at the time

./dev_scripts_helpers/ai/try_openrouter_api.py:3:# TODO(ai_gp): Add the uv package
./dev_scripts_helpers/ai/cc_lib.py:18:# TODO(ai_gp): Use import and not from import
./dev_scripts_helpers/ai/cc_lib.py:64:        # TODO(ai_gp): Use hprint.to_str
./dev_scripts_helpers/ai/test/test_cc_lib.py:53:        # TODO(ai_gp): Use self.get_scratch_space()
./helpers/hmarkdown_coloring.py:380:                # TODO(ai_gp): They seem exactly the same operation. Keep the second one.
./helpers/test/test_hunit_test_utils.py:824:# TODO(ai_gp): Factor out the common code with /coding.factor_common_code
./helpers/test/test_hunit_test.py:62:# TODO(ai_gp): Split in multiple classes, one per testing function,
./helpers/test/test_hunit_test.py:269:# TODO(ai_gp): Indent the """ strings to align with the rest of the code code
./helpers/test/test_hunit_test.py:412:# TODO(ai_gp): Rename the methods to test1, test2, ... and use
./helpers/test/test_hunit_test.py:622:# TODO(ai_gp): Rename the methods to test1, test2, ... and use

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
