In dev_scripts_helpers/scraping/process_hn_article.py

each action should read one csv file and save another one so that it's possible
to run each action independently, like for update_hn_gsheet_from_raindrop.py

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
