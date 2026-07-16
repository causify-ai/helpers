In lint_txt.py

- [x] Add documentation to dev_scripts_helpers/documentation/lint_txt.README.md
  based on lint_txt.py using .claude/skills/markdown.rules.md and
  .claude/skills/text.rules.md

- [x] Add a command line option to force recognizing a certain format, instead of
  inferring them from the extension
  - tex, txt, md, emd

- [ ] Decide which actions are possible depending given the file format

- [ ] Rename the phase prettier to beautify
  - For md only lint, ...

- [ ] preprocess and postprocess are used to transform / comment out stuff that the
  beautifier doesn't like, or support (e.g., since it's not markdown like *)

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

# Create a plan, if needed
- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
