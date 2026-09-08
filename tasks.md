### [ ] Sync Raindrop bookmarks to Obsidian with a short summary

* Affected repo: helpers

* Solution

- process_gsheet_links.py should be applicable to both gsheet and local_csv in the
  same way

- Do not use gsheet as default but force all the scripts to specify --dest_type
  and inputs

- Rename process_gsheet_links.py -> pre_process_bookmarks.py

- download_link_articles.py make the --input approach the default one

- In CSV-Based Bookmark Processing Workflow, the stages of transform are the same
  as the gsheet ones (including process_gsheet_links.py -> pre_process_bookmarks.py)

- Update src/umd_classes3/helpers_root/dev_scripts_helpers/download/README.md
  - Remove the reference to the past interface and iteration. A README should
  only explain how things are right now
  - Do not make reference to PRs and how we got the current behavior
