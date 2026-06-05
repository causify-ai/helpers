# Step 1
- Run pyright and save the result to pyright.before.txt

# Step 2
Apply these changes

.claude/skills/coding.rules.md:848 ## Use Single Types With Meaningful Defaults for Parser Inputs
.claude/skills/coding.rules.md:584 ## Minimize Default Values of None in Function Interfaces

In

./dev_scripts_helpers/documentation/convert_pdf_to_md.py
./dev_scripts_helpers/documentation/generate_images.py
./dev_scripts_helpers/documentation/notes_to_pdf.py
./dev_scripts_helpers/documentation/piper_markdown_reader.py
./dev_scripts_helpers/documentation/test/test_lint_txt.py
./dev_scripts_helpers/documentation/test/test_notes_to_pdf.py
./dev_scripts_helpers/documentation/test/test_preprocess_notes.py


The goal is to replace in the functions
- Optional[str] = None with str = ""
- Optional[int] with a suitable default int = XYZ

- Replace in

    parser.add_argument(
        "-o",
        "--output",
        required=False,
        type=str,
        default=None,
        help="Output directory for markdown and images (default: same directory as input)",
    )

default=None with default="" so that input parameters are only strings

# Step 3: Verification

- grep the code for Optional[str] and Optional[int] and make sure there is no
  instance

- Run the unit test corresponding to the changed files (e.g., file.py ->
  test/test_file.py) and make sure that there is no failure

- Run pyright and save the result to pyright.after.txt

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
