1) Write a Python script ...

The interface is like:

- For all the code you must follow the instructions in ai.coding_instructions.md

2) Generate unit tests for the code following the instructions in ai.unit_test_instructions.md

3) Generate a short description of how to use the script in a file close to the
   script with extension .md
   - Explain the goal of the script
   - Report some examples of how to use the tool
   - Describe the architecture

4) Always follow the steps
  - Describe the goal
  - List the main steps
  - Mention any edge cases
  - Stop and ask: "Should I proceed with this plan?"
  - Write the plan in claude.plan.md
  - Wait for my response. Do not run or finalize code until I say yes.

- Add a `# TODO(ai_gp): xyz` in the code with a short description of what needs to be done

///////////

# Task description
- Add an invoke target in helpers/lib_tasks_git.py to create a zip file with
   all the files that are modified or untracked for both the current repo, using

   git status --porcelain -u | cut -c4- | grep -vFf <(git config -f .gitmodules --get-regexp path | awk '{print $2}'

   and the subrepos

- There should be an option --dry-run to just print what needs to be done

# Step 1)
  - Always follow the steps
  - Describe the goal
  - List the main steps
  - Mention any edge cases
  - Write the plan in claude.plan.md
  - Wait for my response

# Step 2)
  - Add a `# TODO(ai_gp): xyz` in all the places that need to be modified in the
    code with a short description of what needs to be done
    - Try to use bullet points
  - Wait for my response

# Step 3)
  - Write the interfaces and the docstrings, but do not implement the code
  - Wait for my response

# Step 4)
  - Implement unit tests following the instructions in ai.unit_test_instructions.md

# Step 5)
  - If it's a new script, find where the documentation of this change should go
  - Generate a short description of how to use the script in a file close to the
    script with extension .md
   - Explain the goal of the script
   - Report some examples of how to use the script
   - Describe the architecture

# Step 6)
  - Implement the code
