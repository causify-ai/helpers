# Step 1
In update_hn_gsheet_from_raindrop.py --action combine

Remove from the Title field the string "| HackerNews"

# Step 2
Change 

dev_scripts_helpers/scraping_script/process_hn_article.py
--url XYZ

Use an approach using from_gsheet and to_gsheet similar to update_hn_gsheet_from_raindrop.py

Use --action download, update, upload

Action: download
Read the hn gsheet to a file

Action: update_article_url
Scan the rows of the CSV one by one and fill the empty cell corresponding to
title
If the Url is an Hackenews link then extract Article_url with one of the
functions in ./process_hn_article.py

Action: update_article_tag

Action: update_article_cluster

Action: upload

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
