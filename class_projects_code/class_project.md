Write a script create_lesson_project.py that accepts a markdown file and actions
and generate a class project for a college level class about machine learning

create_lesson_project.py --in_file input_file.md --action XYZ --output_file output_file.md

## Action create_project

1) Read the summary stored in --in_file 

2) For each file apply the following prompt to the file
  """
  Act as a data science professor.

  Given the markdown for a lecture, come up with the description of 3 projects
  that can be used to clarify the content of the file .

  Look for Python packages that can be used to implement those projects

  The Difficulty (1 means easy, should take around 7 days to develop, 2 is medium
  difficulty, should take around 10 days to complete, 3 is hard,should take 14
  days to complete)

  The difficulty level should be medium

  - Title:
  - Difficulty:
  - Tech Description:
  - Project Idea:
  - Python libs:
  - Is it Free?
  - Relevant tool(XYZ) related Resource Links

  Avoid long texts or steps
  """

3) Output the results to a file in the output directory with the format

If the file is not specified use `<base_filename>.projects.txt`

You must follow the instructions in general_testing_instr.md
