Create a extract_text_from_txt.py to extract a chunk of a file 

-i <file>

between an initial and final header which is specified as 
--start <header> --end <header>

where <header> is specified as a markdown headers "# XYZ", "## XYZ", "### ..."

Reuse the code from extract_toc_from_txt.py to extract the line number of the files
including the start and end header and then simply extract the [start_line_num,
end_line_num) and save it to 

-o <file>

In extract_text_from_txt.py

if --start or --end are passed to None it means start or end of the file

--start needs to be specified

when --end is not specified the end_line_num is the one of the next header at the
same level of the --start
- E.g., --start "## Header", it means that --end is the next header of level <= 2

Add unit tests to check these behaviors

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a plan.md with 5 bullet points explaining what
    the plan is

- When writing code you must always follow the instructions in
  `@.claude/skills/coding.rules.md`
