In the code to purify the output of a test remove lines like since they come from
Apple container

[0/6] [0s]
[1/6] Fetching image [0s]
[2/6] Unpacking image [0s]
[3/6] Fetching kernel [0s]
[4/6] Fetching init image [0s]
[5/6] Unpacking init image [0s]
[6/6] Starting container [0s]
[6/6] Starting container [1s]
[6/6] Starting container [1s]

Make sure that

pytest dev_scripts_helpers/dockerize/test/test_lib_graphviz.py::Test_build_graphviz_container1

passes without changes

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
