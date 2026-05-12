Step 1
Factor out the functions with `remove_*` in
./dev_scripts_helpers/documentation/clean_markdown.py to
./dev_scripts_helpers/documentation/documentation_utils.py

Step 2
Create a function `remove_junk` that calls in order all the `remove_*` functions
like in _main of ./dev_scripts_helpers/documentation/clean_markdown.py

Step 3
Add a function to ./dev_scripts_helpers/documentation/documentation_utils.py

- Convert the name of a file (book or paper) into a standard format without
  characters that are unfriendly for Linux (e.g., spaces, `.` `/`, `\`) converting
  them into underscore
- Separate Year, Author and
  ```
  <Year>.<Last_name_of_first_author>_[et_al].<Title>
  ```
- If there are more than one author use `et al`

- Example
  - **Before**
    - Ajay Agrawal, Joshua Gans, Avi Goldfarb - Prediction Machines_ The Simple Economics of Artificial Intelligence (2018, Harvard Business Review Press) - libgen.li.epub
  - **After**
    2018.Agrawal_et_al.Prediction_Machines_The_Simple_Economics_of_Artificial_Intelligence.epub

Step 4
Add dev_scripts_helpers/documentation/convert_epub_to_md.py
Add an --action remove_junk to call `remove_junk`

Step 5
Add an --action lint to lint the file

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a plan.md with 5 bullet points explaining
    what the plan is

- When writing code you must always follow the instructions in
  `@.claude/skills/coding.rules.md`

- Generate unit tests for the new code following the instructions in
  `@.claude/skills/testing.rules.md`
