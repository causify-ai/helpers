Make the default mode for i git_files --branch

Add a switch to i git_files called --mode to print

--mode "files" (default): print the files

--mode "test_files": print the test associated to the tests
Using
./helpers/hunit_test_utils.py:534:def get_test_files_for_sources(files: List[str]) -> List[str]:

--mode "test_dirs": print the test dirs associated to the tests

./helpers/hunit_test_utils.py:553:def get_parent_dirs(files: List[str]) -> List[str]:

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a plan.md with 5 bullet points explaining what
    the plan is

- When writing code you must always follow the instructions in
  `@.claude/skills/coding.rules.md`
