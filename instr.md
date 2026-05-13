Create a script `split_text_in_chapters.py`

-i book.md
-o book_chapters
--add_numbers

splitting the markdown in chapters and saving each file in a file in
book_chapters

Each file is named like the chapter removing all the non-friendly linux
characters (there should be a function in helpers for doing these)

1 Introduction _Machine Intelligence_
->
1_Introduction_Machine_Intelligence.md

2 Cheap Changes Everything
->
2_Cheap_Changes_Everything.md

3 Prediction Machine Magic
->
3_Prediction_Machine_Magic.md

If --add_numbers is set then add an index in front of the file name
like `<id>_...`

Read code from `convert_epub_to_md.py` and `extract_toc_from_txt.py`
and reuse whatever is possible

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a plan.md with 5 bullet points explaining
    what the plan is

- When writing code you must always follow the instructions in
  `@.claude/skills/coding.rules.md`

- Generate unit tests for the new code following the instructions in
  `@.claude/skills/testing.rules.md`
