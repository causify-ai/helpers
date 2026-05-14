Create a script dev_scripts_helpers/documentation/summarize_chapters.py

--input "file1.md file2.md ..."
--llm_opts 

summarize all the files passed in input by calling ./helpers/hllm_cli.py like in
./dev_scripts_helpers/slides/process_slides.py (using the options llm_opts)

If a single file is passed in --input, then --output can represent the output
file
If multiple files are passed in output, each input file is transformed as the
input files adding a `.summary` (e.g., `chapter1.md` -> `chapter.summary.md`)



- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications

- When writing code you must always follow the instructions in
  `@.claude/skills/coding.rules.md`

- Generate unit tests for the new code following the instructions in
  `@.claude/skills/testing.rules.md`
