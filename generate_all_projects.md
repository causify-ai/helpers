Create a script create_markdown_summary.py
that accepts a markdown file and actions and generates a summary of the input
file that has the same structure in terms of headers

create_markdown_summary.py --in_file input_file.md --action XYZ --out_file output_file.md --max_level 1

--max_level = the header level of markdown to summarize
  - E.g., max_level = 1 summarize an entire section of level 1
--max_num_bullets = the max number of bullet points to use to summarize a chunk of
  test

- Use as many functions as possible from helpers/hmarkdown_*.py to read, parse,
  and process markdown files

## Action summarize

1) Read the markdown file `input_file` using the library in helpers/hmarkdown*.py
  like we do in extract_headers_from_markdown.py

2) Make sure using functions in helpers/hmarkdown_headers.py that every header of
level 1 has headers up to level passed through --max_level inside
- If not asserts and report a clear error explaining which file and at which line
  the error is occurring
- Also check that the markdown is correct using sanity_check_header_list

3) For each section of level --max_level headers create a summary in bullet points of the
  content of that entire section
  ```
  ## Header 2
  Content
  ```
- Use the Python package llm to invoke LLMs to summarize using a prompt like
  """
  Given the following markdown text summarize it into up to max_num_bullets bullets to use
  the most important points
  """
- The output is a markdown file with the same structure of headers up to level
  max_level, but with the content of level 2 headers replaced with the summary
- For each summarized chunk add a comment like
  ```
  // From input_file.md: [start_line, end_line]
  ```
  to represent which part of the code was summarized

4) Save the result in the output dir --output_dir using the same name of the input file
  but using a suffix ${input_file}.summary.txt

## Action preview_chunks

- Output the original markdown annotating which chunks will be summarized using
  ```
  // ---------------------> start chunk N <---------------------
  // ---------------------> end chunk N <---------------------

## Action check_output

- Make sure that the structure of the input file and of the output file is the
  same up to level max_level using the functions
  hmarkdown.extract_headers_from_markdown
  - Write the structure of the two files in two files `tmp.headers_in.md`
    and `tmp.headers_out.md`
  - Compare them with sdiff

You must follow the instructions in general_instr.md
