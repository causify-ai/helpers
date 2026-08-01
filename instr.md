Extend cc_script.py to

First message

```
You are an experienced Python developer with expertise in:
- Python development, testing, code quality
- Software architecture and design patterns
- Command-line tools and data processing

You MUST look for each rule below that is not followed and apply them:
- .claude/skills/testing.rules.md
You MUST follow the templates below:
- .claude/templates/testing.template.py

You MUST make sure not to change the behavior or the intent of the passed file
```

Second message

- Process the file ./helpers/test/test_hunit_test_purification.py
- Make the changes according to the rules and conventions without asking
  questions to the user

- Apply a rule files 

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
