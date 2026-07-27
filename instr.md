Change Test_notes_to_pdf_latex_colors so that there are multiple tests

1) 3 tests end-to-end to check that the PDF is generated
--type pdf
--type slides --slides_engine beamer
- type slides --slides_engine typst

2) 3 tests generating only the tex and typ intermediate file and then
checking that each file contains the right color 

for tex
        self.assertIn(r"\textcolor{red}", output_txt)
        self.assertIn(r"\textcolor{blue}", output_txt)

for typst
  #text(fill: red)[This is red]

--no_pdf --type pdf -> check tex
--no_pdf --type slides --slides_engine beamer -> check tex
--no_pdf --type slides --slides_engine typst -> check typst

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
