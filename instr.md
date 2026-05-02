- Create a python script to convert a markdown table or a CSV / TSV file into CSV, TSV, markdown

  --input <input>.{md,csv,tsv} --output <output>.{md,csv,tsv} --pbcopy

  for --pbcopy use
  hsystem.to_pbcopy(github_url, pbcopy=True)

- Allow to use input and output to be - for stdin and stdout but then
  there should be a --input_mode and --output_mode with md, csv, tsv
  - Use hparser.add_input_output_args


- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a plan.md with 5 bullet points explaining what
    the plan is

- When writing code you must always follow the instructions in
  `@.claude/skills/coding.rules.md`
