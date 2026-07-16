In lint_txt.py

- [x] Add documentation to dev_scripts_helpers/documentation/lint_txt.README.md
  based on lint_txt.py using .claude/skills/markdown.rules.md and
  .claude/skills/text.rules.md

- [x] Add a command line option to force recognizing a certain format, instead of
  inferring them from the extension
  - tex, txt, md, emd

- [x] Document in dev_scripts_helpers/documentation/lint_txt.README.md

- [x] Propose which actions should be possible depending given the file format
  - Implemented _ACTIONS_BY_FORMAT mapping (md, tex, txt, emd)
  - Added _get_supported_actions_for_format() helper
  - Added _filter_actions_by_format() to auto-filter unsupported actions
  - Integration: _perform_actions() now filters based on file format

- [ ] Move the code from lint_txt.py to lib_lint_txt.py, using an approach
  similar to
  ./dev_scripts_helpers/documentation/lib_notes_to_pdf.py
  ./dev_scripts_helpers/documentation/notes_to_pdf.py
  ./dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py
  ./dev_scripts_helpers/documentation/test/test_notes_to_pdf.py

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
