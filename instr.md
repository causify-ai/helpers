In dev_scripts_helpers/scraping/download_link_articles.py add another action
summarize that uses llm_cli.py to summarize both the text of the article and
the comments using the prompt from

.claude/skills/text.summarize_hn_in_bullet_points/SKILL.md

Call the summarization using hsystem.system

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
