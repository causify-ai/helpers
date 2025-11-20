# Create a script from scratch

- Use the template in `ai.instruction_template.md`
  ```
  > cp docs/ai_coding/ai.instruction_template.md instr.md
  ```

- Modify `instr.md`
```
1) Write a Python script `dev_scripts_helpers/documentation/summarize_md.py` that
reads a markdown file --input file.md

- Read the content of the file

- Summarize it with a prompt like """ Summarize the content of the text in 3 to 5
  bullet points. """

- Use llm CLI using a specific model

- Looks for a `# Summary` section in file.md and replaces it or adds it with the
  summary of the file

- For all the code you must follow the instructions in
  `docs/ai_coding/ai.coding_instructions.md`

2) Update the documentation in dev_scripts_helpers/documentation/README.md using
   the instructions in `docs/ai_coding/ai.md_instructions.md`
```

- Run Claude Code
  ```
  claude> execute instr.md
  ```
