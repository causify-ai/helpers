# Step 1
In update_hn_gsheet_from_raindrop.py --action combine

remove from the Title field the string "| HackerNews"

# Step 2
Create a 
dev_scripts_helpers/scraping/process_hn_article.py --url XYZ
to use an approach using from_gsheet.py and to_gsheet.py similar to update_hn_gsheet_from_raindrop.py

It has --action ...

- Action: download
Read the hn gsheet to a file
using a similar approach using from_gsheet.py similar to update_hn_gsheet_from_raindrop.py

- Action: update_article_url
Scan the rows of the CSV one by one and fill the empty cell corresponding to
title
If the Url is an Hackenews link then extract Article_url with one of the
functions in ./process_hn_article.old.py

If the url is not an Hackernews link, then use the same article as url

- Action: update_article_tag
Use topic_to_cluster and other code from ./process_hn_article.old.py

Action: update_article_cluster
Use the mapping from topic_to_cluster to complete the column

Action: upload
use to_gsheet.py similar to update_hn_gsheet_from_raindrop.py

You can copy-paste code from
dev_scripts_helpers/scraping/process_hn_article.old.py
but when you use the code you need to remove it from
dev_scripts_helpers/scraping/process_hn_article.old.py

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
