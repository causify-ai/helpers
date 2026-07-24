Add unit test for 

_sys_calls_to_str

using one of the examples of 
        expected_sys_calls = [
            {
                "function": "hsystem.system",
                "args": (cmd,),
                "kwargs": {
                    "log_level": logging.DEBUG,
                    "suppress_output": False, "print_command": True,
                },
            },
        ]
        expected_str = hunteuti._sys_calls_to_str(expected_sys_calls)

in

Test_run_pandoc_from_ast

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing testing code you must always follow the instructions in
  `.claude/skills/testing.rules.md`

# Create a plan, if needed
- If the task is not perfectly clear:
  - You MUST not perform it
  - Ask for clarifications
  - Create a `plan.md` in the same directory with 5 bullet points explaining what
    the plan is
  - Wait for the user to confirm

