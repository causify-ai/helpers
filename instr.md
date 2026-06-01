Implement ./dev_scripts_helpers/coding_tools/pyan.sh

in Python following our convention (using uv, --action, --input)

pyan3 $file --dot > callgraph.dot
dot -Tpng callgraph.dot -o callgraph.png

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
