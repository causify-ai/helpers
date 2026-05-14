Create a script dev_scripts_helpers/documentation/summarize_chapters.py

summarize all the files passed in input by calling ./helpers/hllm_cli.py like in
./dev_scripts_helpers/slides/process_slides.py (using the options llm_opts)

use the functions parse_input_output_files in src/notes1/helpers_root/helpers/hparser.py

use the parsing arguments 

If a single file is passed in --input, then --output can represent the output
file
If multiple files are passed in output, each input file is transformed as the
input files adding a `.summary` (e.g., `chapter1.md` -> `chapter.summary.md`)


Read the file `.claude/skills/text.rules.bullet_points.md` in <rules>

Use the following prompt

````
## Keep the same structure
- Use the same structure of the chapter and subchapter in markdown headers
  - Use numbers of chapter (e.g., 1.) and subchapters (e.g., 1.1)
  - Use the chapter numbers that come from the book

## Bullet point rules
- Write a summary in bullet points using the following rules
  <rules>

## Example
- An example of the output is
  ```
  # 1. Hello

  ## 1.1. Hello world

  - Point
    - Subpoint
    - Subpoint
  - Pont

  ## 1.2. Good bye world

  # 2. Hello again
  ```
````


- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications

- When writing code you must always follow the instructions in
  `@.claude/skills/coding.rules.md`

- Generate unit tests for the new code following the instructions in
  `@.claude/skills/testing.rules.md`
