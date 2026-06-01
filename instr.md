Create a script dev_scripts_helpers/scraping/download_link_articles.py
--url XXX
--column_idx IDX
--column_idx START:END

to download the articles stored at a certain interval or rows of the Gsheet in
url

Use the same approach as from_gsheet import from update_hn_gsheet_from_raindrop.py
to download the gsheet and use --action

--action download_url 
--action download_article_url

download the files as replacing all the bash unfriendly chars to _

E.g.,
ATLAS: Autoformalized Textbook Library At Scale

ATLAS_Autoformalized_Textbook_Library_At_Scale.hn_comments.txt
ATLAS_Autoformalized_Textbook_Library_At_Scale.text.txt

for Hackernews articles download all the comments

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
