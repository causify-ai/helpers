<<<<<<< Updated upstream
Extend `invoke gh_issue_create` to accept a --gh_issue_body_file 

Implement the TODO(ai_gp): in dev_scripts_helpers/git/git_create_issue_and_branch.py 
and dev_scripts_helpers/git/test/test_git_create_issue_and_branch.py 
=======
Create a script ./dev_scripts_helpers/github/run_local_ci.py
--start_time timestamp (e.g., 2am)

- Every night at $start_time run the regressions in the current repo

- For the current dir . and for helpers

- All commands need to be prepended by `cd ${dir}; source setenv.sh` to
  configure the environment

- TARGET=. or .claude for --test

- Check that the repo is at master
- Run git clean -fd
- Check that the client is clean
- Sync `git pull`
- Run tests
  > pytest_multi_build.py --target . --build_names apple dev_container 2>&1 | tee ../local_ci.pytest_multi_build.{timestamp}.{repo}.txt
- Summarize
  > pytest_failed_multi_build.py 2>&1 | tee ../local_ci.pytest_failed_multi_build.{timestamp}.{repo}.txt
>>>>>>> Stashed changes

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
