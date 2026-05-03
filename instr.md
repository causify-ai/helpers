Create a extract_text_from_txt.py to extract a chunk of a file 

-i <file>

between an initial and final header which is specified as 
--start <header> --end <header>

where <header> is specified as a markdown headers "# XYZ", "## XYZ", "### ..."

Reuse the code from extract_toc_from_txt.py to extract the line number of the files
including the start and end header and then simply extract the [start_line_num,
end_line_num) and save it to 

-o <file>

Make a plan

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a plan.md with 5 bullet points explaining what
    the plan is

- When writing code you must always follow the instructions in
  `@.claude/skills/coding.rules.md`
