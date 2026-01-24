# Implement code

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
  `docs/ai_prompts/coding.format_code.md`

## Step 2)
- Update the file README.md in the same directory of the script following the
  instructions in `docs/ai_prompts/readme.create.md`

## Step 3)
- Generate unit tests for the code following the instructions in
  `docs/ai_prompts/testing.format_unit_tests.md`
  - Write test class and methods
  - Do not implement code
  - Preview unit tests that need to be written by creating input and expected
    outputs

# Implement notebook
- Add examples to explain the code below to <file> following
  `docs/ai_prompts/notebooks.format_code.md`

<content>
* Entropy and Probability Density Function (PDF)
- Entropy is related to variance but is not the same
  - Variance measures how far values are from the mean
  - Entropy measures how unpredictable a random draw is

- If a distribution has more spread, typically its entropy is larger
  - It is possible that variance increases, but entropy doesn't
    - E.g., a uniform distribution increasing its support

- Entropy is related to information and uncertainty
  - A flatter distribution has high entropy
  - A sharply peaked distribution has low entropy
  - A distribution with two close peaks has low variance but high entropy
</content>

- If the task is not perfectly clear (e.g., where to add the code, what code to
  add), you MUST not perform it, but ask for clarifications

# Rename files

## Step 1)

- Rename the files in ... that have ...

## Step 2)
- Make sure that all the files in the repo are updated with this change

# Implement function

## Step 1)
- Write a Python function XYZ that ...

- The interface is like:
  - For all the code you must follow the instructions in
    `docs/ai_prompts/coding.format_code.md`

  - If the task is not perfectly clear, you MUST not perform it, but ask for
    clarifications

## Step 2)
- Update the file README.md in the same directory of the script following the
  instructions in `docs/ai_prompts/readme.create.md`

## Step 3)
- Generate unit tests for the code following the instructions in
  `docs/ai_prompts/testing.format_unit_tests.md`

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
    `docs/ai_prompts/testing.format_unit_tests.md`

## Step 5)
  - If it's a new script, find where the documentation of this change should go
  - Generate a short description of how to use the script in a file close to the
    script with extension .md
  - Explain the goal of the script
  - Report some examples of how to use the script

## Step 6)
  - Update the file README.md in the same directory of the script following the
    instructions in `docs/ai_prompts/readme.create.md`

## Step 7)
  - Implement the code following the instructions in
    `docs/ai_prompts/coding.format_code.md`
