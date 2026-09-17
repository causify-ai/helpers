This file clarifies how to execute a task in the current repo

# Conventions
- Follow all the conventions in `.claude/rules.md` depending on what is the type of file
  involved in the task to execute
- For example:
  - When writing code you must always follow the instructions in
    `.claude/skills/coding.rules.md`
  - When writing testing code you must always follow the instructions in
    `.claude/skills/testing.rules.md`

# Workflow

## Create a Plan
- Create a plan with a TODO list in the file with the instructions
  - Add the plan to the instruction files, right after the actual instructions
  - If there is no clear instruction files, create a file `plan.md` in the current
    directory

- Always write wrapping text in 85 columns

- Use nested bullet points explaining what needs to be executed, example
  ```
  ## Plan
  - [ ] Do this
  - [ ] Do that
  ...
  ```

## Ask Questions if the Task is Unclear 
- If the task is not perfectly clear:
  - You MUST not perform it
  - Ask for clarifications
  - Wait for the user to confirm the plan for execution

## Execute the Plan
- As you make progress on the plan, keep the plan updated by:
  - Marking a task as in progress with `[-]`
  - Checking the box when it's complete `[x]`

- Once you are done executing the plan, add after the plan 2-3 bullet points about:
  - What was done
  - What was **not done** and why
- Example
  ```
  ## Result

  ### Done
  - Done this and that
    - This
    - That

  ### Not done
  - Not done XYZ
    - ...
  ```

## Add Files to the Repo
- When creating new files that belong to the repo (e.g., Python files, scripts) 
  as part of the task, run `git add` but do not commit them
- You must not add temporary files (e.g., logs to the repo, temporary files, e.g.,
  `dev_scripts_helpers/coding_tools/notify.py.log`, `tmp.precommit_output.txt`)
- If you are not sure, ask the user at the very end of the task
