# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`
- When writing testing code you must always follow the instructions in
  `.claude/skills/testing.rules.md`

# Add Files
- When creating new files that belong to the repo (e.g., Python files, scripts)
  run `git add` but do not commit them

# Create a Plan
- Create a plan with a TODO list in the file with the instructions close to the
  actual instructions (or in `plan.md` if there is no instruction file)
- Use nested bullet points explaining what needs to be executed
  ```
  ## Plan
  - [ ] Do this
  - [ ] Do that
  ...
  ```
- Keep the plan updated as you make progress by:
  - Marking a task as in progress `[-]`
  - Checking the boxes `[x]`

- When writing text follow the conventions in `.claude/skills/markdown.rules.md`

# Ask Questions if the Task is Unclear 
- If the task is not perfectly clear:
  - You MUST not perform it
  - Ask for clarifications
  - Wait for the user to confirm the plan for execution

# Update the File
- Once you are done add to the instruction file, close to the actual
  instructions, (or in `plan.md` if there is no instruction file) a short comment
  using 2-3 bullet points about:
  - What was done
  - What was **not done** and why
  ```
  ## Result
  - Done this
    - This
    - That
  - Done that
    - ...
  ```
