In lint_txt.py

- [x] 1 Add documentation to dev_scripts_helpers/documentation/lint_txt.README.md
  based on lint_txt.py using .claude/skills/markdown.rules.md and
  .claude/skills/text.rules.md

- [x] 2 Add a command line option to force recognizing a certain format, instead of
  inferring them from the extension
  - tex, txt, md, emd

- [x] 3 Document in dev_scripts_helpers/documentation/lint_txt.README.md

- [x] 4 Propose which actions should be possible depending given the file format
  - Implemented _ACTIONS_BY_FORMAT mapping (md, tex, txt, emd)
  - Added _get_supported_actions_for_format() helper
  - Added _filter_actions_by_format() to auto-filter unsupported actions
  - Integration: _perform_actions() now filters based on file format

- [x] 5 Fix extract_protected_content so that
  ```
  % git_hash=f15bc6b9, timestamp=2026-07-15 14:41:12 EDT
  %%%% Chapter file for Why Decisions, Not Predictions %%%%
  % This chapter file can be compiled standalone or included in the root book.tex
  ```
  is left alone and not converted to
  ```
  % git_hash=f15bc6b9, timestamp=2026-07-15 14:41:12 EDT %%%% Chapter file for Why Decisions, Not Predictions %%%% % This chapter file can be compiled standalone or included in the root book.tex
  ```
  - Also 
    ```
    % From: '* Why Traditional ML Falls Short'
    \textbf{Why Traditional ML Falls Short}
    ```
    is converted into
    ```
    % From: '* Why Traditional ML Falls Short' \textbf{Why Traditional ML Falls Short}
    ```
    while it should be left unchanged

- [x] 6 Move extract_protected_content inside preprocess

- [x] 7 Add a --daemon mode to run_latex.py similar to notes_to_pdf.py (with the
  debounce) and also change the tmux name using the context manager

- [ ] 8 Rename the phase prettier to beautify

- [ ] 9 Move the code from lint_txt.py to lib_lint_txt.py, using an approach
  similar to
  ./dev_scripts_helpers/documentation/lib_notes_to_pdf.py
  ./dev_scripts_helpers/documentation/notes_to_pdf.py
  ./dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py
  ./dev_scripts_helpers/documentation/test/test_notes_to_pdf.py

- [ ] preprocess and postprocess should be used to transform / comment out stuff
  that the beautifier doesn't like, or support (e.g., since it's not markdown
  like *)

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
