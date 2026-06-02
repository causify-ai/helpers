In helpers/hmarkdown_formatting.py add a function

def format_md(input: str, backend: str, mode: str, width: int = 80):

where
backend = "prettier" calls prettier_on_str ./dev_scripts_helpers/dockerize/lib_prettier.py

the mode is "dockerized", "global"

backend = "mdformat" calls 
  https://github.com/hukkin/mdformat?utm_source=chatgpt.com
  the mode is "library", "uvx", "global"

backend = "flowmark" calls
  https://github.com/jlevy/flowmark
  the mode is "library", "uvx-rs", "uvx", "global", "global-rs"
  use the --auto option

For everything that is not "library" save the content to file and call the
executable there like in prettier_on_str ./dev_scripts_helpers/dockerize/lib_prettier.py

Add unit tests to test all the various combinations

Create a unit test to
- compare the output of the various tools and combinations
- collect also times

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
