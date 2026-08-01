Extend lint_cc.py to use an option --apply_incrementally and apply
the rules from a file incrementally with multiple calls to claude code
instead all at once

Extract the H1 sections of the rule file using the functions in
helpers/hmarkdown_*.py

Use the code in ./dev_scripts_helpers/ai/cc_lib.py
to apply the rules one by one to one insance of claude code

The first message to send to CC, based on the type of file
```
# Goal
- I will pass you a file and you will update the file to follow rules and
  conventions
- You MUST make sure not to change the behavior or the intent of the passed file
- Make the changes according to the rules and conventions without asking
  questions to the user

# Role
You are an experienced Python developer with expertise in:
- Python development, testing, code quality
- Software architecture and design patterns
- Command-line tools and data processing

# Rules
- Read the rules and conventsions `.claude/skills/testing.rules.md`
- Read the template file `.claude/templates/testing.template.py`
```

The second message is to communicate which file is the target

```
- You will apply the rules that I will give you to
  ./helpers/test/test_hunit_test_purification.py
```

- Apply a rule files using multiple interactions with Claude Code
  one per H1

- Add an option --dry_run to see how messages will be generated without
  sending them to claude code

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
