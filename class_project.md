Write a script create_class_projects.py that accepts files and actions and
generate a class project for a college level class about machine learning

create_class_projects.py --in_file input_file.md --action XYZ --o output_dir

## Action summarize

1) Read the markdown file `input_file` using the library in helpers/hmarkdown*.py
  like we do in extract_headers_from_markdown.py

2) For each section of level 2 headers create a summary in bullet points of the
  content of that section
  ```
  ## Header 2
  Content
  ```
- Use the Python package llm to invoke LLMs
- The prompt is like
  """
  Given the following markdown text summarize it into a few bullets
  """
- The output is a markdown file with the same structure of headers of level 1 and
  2 but with the content of level 2 headers replaced with the summary

3) Save the result in the output dir --output_dir using the same name of the input file
  but using a suffix ${input_file}.summary.txt

## Action create_project

1) Read the summary stored in --output_dir dir corresponding to the file
input_file.md

2) For each file apply the following prompt
  """
  Come up with the description of 3 projects that can be used to clarify the
  content of the file 
  Look for Python packages that can be used to implement those projects
  """

You must follow the instructions in general_instr.md
