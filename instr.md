- In dev_scripts_helpers/documentation/piper_markdown_reader.py 
  use the functions in helpers/hmarkdown_select.py to apply --md_start and
  --md_end to select a chunk of markdown input, similar to extract_text_from_txt

- Create an intermediate file `tmp.piper_markdown_reader.extract.md` <tmp> with
  the extracted file

- Run on the intermediate file to unroll the bullet list breaks
  > lint_txt.py -i <tmp> -w 1000

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications

- When writing code you must always follow the instructions in
  `@.claude/skills/coding.rules.md`

- Generate unit tests for the new code following the instructions in
  `@.claude/skills/testing.rules.md`
