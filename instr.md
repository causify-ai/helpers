❯ 1) Factor out the code to extract the test files

  2) Add functions to find the directory including a set of files

  dev_scripts_helpers/scraping/process_hn_article.py
  dev_scripts_helpers/scraping/test/__init__.py
  helpers/hgit.py
  helpers/lib_tasks_utils.py

  ->
  dev_scripts_helpers/scraping/
  helpers/

  Remove the dirs that are included in others

  3) Test the functions in 1) and 2)

  4) Add an option to i git_files
  - --test_files to report the test files using the function in 1)
  - --test_dir and report the list of dirs including the files  using the function
     in 2)

  - If the task is not perfectly clear, you MUST not perform it, but ask for
    clarifications
    - When the task is complex, create a plan.md with 5 bullet points explaining what
      the plan is

  - When writing code you must always follow the instructions in
    `@.claude/skills/coding.rules.md`

