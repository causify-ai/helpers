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

# Create a README.md

claude> Execute the prompt in docs/ai_coding/ai.readme_template.md on the directory ./helpers_root/dev_scripts_helpers/llms/

# 

Peeling off PR flow (independent of AI but useful to separate coding and merging)
Create a script from scratch
Add a feature
Update documentation to be in sync with code
Improve unit test
Implement TODO(ai_gp):

Use Cursor
Write the code almost correct
Pass of Claude to fix it up

How to use Docker
Write the code to run outside Docker as much as possible
i docker_bash
i pytest_...

How to increase coverage

Read and execute papers/DataFlow_white_paper/system_prompt.md

Read papers/DataFlow_white_paper/paper.tex and all the files included

move papers/DataFlow_white_paper/system_prompt.md to docs/

