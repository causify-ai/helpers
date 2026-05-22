# Simple Change
- Do ...

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications

- For all the code you must follow the instructions in
  @.claude/skills/coding.rules.md

# Rules

- .claude/skills/blog.rules.md
- .claude/skills/coding.rules.md
- .claude/skills/markdown.rules.md
- .claude/skills/notebook.rules.md
- .claude/skills/testing.rules.md

# Implement Code

Implement one step at the time asking user for confirmation, before moving to the
next step

## Step 1)

- Write a Python script XYZ ... that ...

- The interface is like:
  ...

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
- When the task is complex, create a plan.md with 5 bullet points explaining what
  the plan is

- For all the code you must follow the instructions in
  @.claude/skills/coding.rules.md

## Step 2)
- Update the file README.md in the same directory of the script following the
  instructions in @.claude/skills/readme.create.md

## Step 3)
- Generate unit tests for the code following the instructions in
  @.claude/skills/testing.format.md
  - Write test class and methods
  - Preview unit tests that need to be written by creating input and expected
    outputs
  - Do not implement code for the testing yet

## Step 4)
- Implement unit test code for the code following the instructions in
  @.claude/skills/testing.format.md

# Implement Notebook Script

source = `msml610/lectures_source/Lesson05.1-Learning_Theory.txt`
notebook = `msml610/tutorials/L5_01_Learning_Theory.Bin_Analogy_ML.ipynb`
script = `msml610/tutorials/L5_01_Learning_Theory.Bin_Analogy_ML.md

## Build the Notebook Script
- Read $source and understand the bin analogy
- Execute @.claude/skills/notebook.create_visual_script.md to create the script
  for the concept

## Build the Notebook
- If there is no $notebook
  ```bash
  > cp ./msml610/tutorials/template.ipynb $notebook
  > git add $notebook
  ```
- Execute @.claude/skills/notebook.implement_script.md for cells between
  <start> and <end> of $script
- Update $notebook

# Test Code

Given the passed code

## Step 1)
- Generate unit tests for the code following the instructions in
  @.claude/skills/testing.format.md
- Focus on writing test class and methods and their docstring without implement
  testing code

## Step 2)
- Once the user has approved the testing code, implement the testing code
- For all the code you must follow the instructions in
  @.claude/skills/coding.rules.md

# Rename Files

## Step 1)
- Rename the files in ... that have ...

## Step 2)
- Make sure that all the files in the repo are updated with this change

# Implement an Invoke Target

- Add an invoke target in helpers/lib_tasks_git.py to create a zip file with
  all the files that are modified or untracked for both the current repo, using

   > git status --porcelain -u | cut -c4- | grep -vFf <(git config -f .gitmodules --get-regexp path | awk '{print $2}'

   and the subrepos

- There should be an option --dry-run to just print what needs to be done

# Plan and Then Implement Code

## Step 1) Come Up with a Plan for the Code
  - Describe the goal, listing the main steps
  - Mention any edge cases
  - If the task is not perfectly clear, you MUST not perform it, but ask for
    clarifications
  - Write the plan in a file `claude.plan.md
  - Wait for my response before executing the plan

## Step 2) Implement Interfaces
  - Write the interfaces and the docstrings of the needed code in the places of
    the code base
  - Add comment explaining what each function does
  - Do not implement the body of the code
  - Wait for my response

## Step 3) Implement Code
  - Implement the code following the instructions in
    @.claude/skills/coding.rules.md

## Step 4) Come Up with a Plan for the Tests
  - Implement unit tests following the instructions in 
    @.claude/skills/testing.format.md

## Step 5) Implement Tests
  - Implement unit tests following the instructions in 
    @.claude/skills/testing.format.md

## Step 6) Create New README
  - If it's a new script, find where the documentation of this change should go
  - Generate a short description of how to use the script in a file close to the
    script with extension .md
  - Explain the goal of the script
  - Report some examples of how to use the script
  - Update the file README.md in the same directory of the script following the
    instructions in @.claude/skills/readme.create.md

# Write Short Tutorial

- Execute @.claude/skills/blog.write_tutorial.md about ripgrep

- Write the result in `website/docs/blog/drafts/ripgrep.md
