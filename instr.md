Create a script

dev_scripts_helpers/scraping/download_link_articles.py
  --url XXX
  --column_idx IDX or START:END
  --select_column the name of a column of the Gsheet

to download the articles stored at a certain interval or rows of the Gsheet in
url

Use the same approach as from_gsheet import from update_link_gsheet_from_raindrop.py
to download the gsheet and use --action

--action download_url 
--action download_article_url

to download potentially 2 files (one for the hacker news comments from url
and the article from article_url)

The output files are obtained replacing all the bash unfriendly chars with _

E.g.,
If the article title in `Title`
ATLAS: Autoformalized Textbook Library At Scale

the 2 files are

ATLAS_Autoformalized_Textbook_Library_At_Scale.hn_comments.txt
ATLAS_Autoformalized_Textbook_Library_At_Scale.text.txt

For Hackernews articles download all the comments looking at the code in a past
version of dev_scripts_helpers/scraping/process_link_gsheet.py

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
