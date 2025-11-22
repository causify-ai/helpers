# Rename files

1) Rename the files in docs/ai_coding/ that have instructions.md

docs/ai_coding/ai.blog.prompt.md
docs/ai_coding/ai.coding.prompt.md
docs/ai_coding/ai.paper.prompt.md
docs/ai_coding/ai.unit_test.prompt.md

replacing _instructions.md with .prompt.md

2) Make sure that all the files in the repo are updated

# Implement script

1) Write a Python script in 
...
that
...

The interface is like:
...

- For all the code you must follow the instructions in
  `docs/ai_coding/ai.coding.prompt.md`

2) Update the file README.md in the same directory of the
   script following the instructions in 
   `in docs/ai_coding/ai.create_readme.prompt.md`

3) Generate unit tests for the code following the instructions in
  `docs/ai_coding/ai.unit_test.prompt.md`

# Implement function

1) Write a Python function XYZ that ...

The interface is like:

- For all the code you must follow the instructions in
  `docs/ai_coding/ai.coding.prompt.md`

2) Update the file README.md in the same directory of the
   script following the instructions in 
   `in docs/ai_coding/ai.create_readme.prompt.md`

3) Generate unit tests for the code following the instructions in
  `docs/ai_coding/ai.unit_test.prompt.md`

# Implement an invoke target
- Add an invoke target in helpers/lib_tasks_git.py to create a zip file with
  all the files that are modified or untracked for both the current repo, using

   > git status --porcelain -u | cut -c4- | grep -vFf <(git config -f .gitmodules --get-regexp path | awk '{print $2}'

   and the subrepos

- There should be an option --dry-run to just print what needs to be done

# Implement code with preview

## Step 1)
  - Always follow the steps
  - Describe the goal
  - List the main steps
  - Mention any edge cases
  - Write the plan in a file `claude.plan.md`
  - Wait for my response

## Step 2)
  - Add a `# TODO(ai_gp): xyz` in all the places that need to be modified in the
    code with a short description of what needs to be done
    - Try to use bullet points
  - Wait for my response

## Step 3)
  - Write the interfaces and the docstrings, but do not implement the code
  - Wait for my response

## Step 4)
  - Implement unit tests following the instructions in ai.unit_test.prompt.md

## Step 5)
  - If it's a new script, find where the documentation of this change should go
  - Generate a short description of how to use the script in a file close to the
    script with extension .md
   - Explain the goal of the script
   - Report some examples of how to use the script
   - Describe the architecture

## Step 6)
  - Implement the code
