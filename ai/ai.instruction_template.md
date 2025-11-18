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
