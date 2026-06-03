# Step 1

Add an option --stat_file to llm_cli.py to save a json of the stats from running
a call to a model

# Step 2
Create a script llm_compare.py that accepts an option
--models "xyz,abc,..." where xyz and abc and so on are models
or --models_from_file with a file storing model codes on each line

--output_dir

Call llm_cli.py with the same options that were not parsed
that runs the same workload with different models by calling
llm_cli.py, saving the results in output_dir/{model}.output.txt

--stat_file $output_dir/{model}.stat.txt

Then read all the stats and create a table of

model
costs
time elapsed
length of output
file


- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
