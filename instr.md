Fix the issue when calling rig with options like --last_commit --branch that specify a list of
files

rig --last_commit -v DEBUG

rg '^\s*(#|//)\s*TODO\(ai_gp\S*\)' . --hidden dev_scripts_helpers/system_tools/lib_rig.py helpers/hparser.py linters2/lint_cc.py -n --no-heading --color=never -g '!.git'

The directory should be replaced with the list of files

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- When implementing notebooks follow the instructions in
  - `.claude/skills/notebook.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
