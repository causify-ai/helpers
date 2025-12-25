# Rename files

Step 1) Rename the files in docs/ai_coding/ that have instructions.md

docs/ai_prompts/blog.format_text.md
docs/ai_prompts/coding.format_code.md
docs/ai_coding/ai.paper.prompt.md
docs/ai_prompts/coding.format_unit_tests.md

replacing _instructions.md with .prompt.md

Step 2) Make sure that all the files in the repo are updated

# Implement script

Step 1) Write a Python script in 
...
that
...

The interface is like:
...

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications

- For all the code you must follow the instructions in
  `docs/ai_prompts/coding.format_code.md`

Step 2) Update the file README.md in the same directory of the
   script following the instructions in 
   `in docs/ai_coding/ai.create_readme.prompt.md`

Step 3) Generate unit tests for the code following the instructions in
  `docs/ai_prompts/coding.format_unit_tests.md`
  - Write test class and methods
  - Do not implement code
  - Preview unit tests that need to be written by creating input and expected
    outputs

# Implement function

Step 1) Write a Python function XYZ that ...

The interface is like:

- For all the code you must follow the instructions in
  `docs/ai_prompts/coding.format_code.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications

Step 2) Update the file README.md in the same directory of the
   script following the instructions in 
   `in docs/ai_coding/ai.create_readme.prompt.md`

Step 3) Generate unit tests for the code following the instructions in
  `docs/ai_prompts/coding.format_unit_tests.md`

# Implement an invoke target

- Add an invoke target in helpers/lib_tasks_git.py to create a zip file with
  all the files that are modified or untracked for both the current repo, using

   > git status --porcelain -u | cut -c4- | grep -vFf <(git config -f .gitmodules --get-regexp path | awk '{print $2}'

   and the subrepos

- There should be an option --dry-run to just print what needs to be done

# Implement code with preview

## Step 1)
  - Describe the goal, listing the main steps
  - Mention any edge cases
  - If the task is not perfectly clear, you MUST not perform it, but ask for
    clarifications
  - Write the plan in a file `claude.plan.md`
  - Wait for my response before executing the plan

## Step 2)
  - Write the interfaces and the docstrings of the needed code in the places of
    the code base
  - Add comment explaining what functions should do
  - Do not implement the body of the code
  - Wait for my response

## Step 4)
  - Implement unit tests following the instructions in 
    `docs/ai_prompts/coding.format_unit_tests.md`

## Step 5)
  - If it's a new script, find where the documentation of this change should go
  - Generate a short description of how to use the script in a file close to the
    script with extension .md
  - Explain the goal of the script
  - Report some examples of how to use the script

## Step 6)
  - Update the file README.md in the same directory of the script following the
    instructions in `in docs/ai_coding/ai.create_readme.prompt.md`

## Step 7)
  - Implement the code following the instructions in
    `docs/ai_prompts/coding.format_code.md`
