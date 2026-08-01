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
