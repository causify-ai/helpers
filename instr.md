In ./helpers_root/helpers/hllm_cli.py make sure that all the functions that
accept `model`, have it before the * so that it's mandatory

  - Bad
    *,
    model: str,

  - Bad
    *,
    system_prompt: str = "",
    model: str = "",

  - Good
    model: str,
    *,
    system_prompt: str = "",

Make sure the changed functions call model using positional argument
and not model=model,

    - Bad
        response, token_stats = _apply_llm_via_executable(
            input_str,
            system_prompt=system_prompt,
            model=model,
            expected_num_chars=expected_num_chars,
        )

    - Good
        response, token_stats = _apply_llm_via_executable(
            input_str,
            model,
            system_prompt=system_prompt,
            expected_num_chars=expected_num_chars,
        )


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
