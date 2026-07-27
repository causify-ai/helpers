The file in output.html from
download_html_to_md.py -i https://code.claude.com/docs/en/platforms -o output.md -sa lint 

has content but when running the action convert output.md is almost empty

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
