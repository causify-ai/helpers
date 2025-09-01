Write a script create_class_projects.py that accepts a markdown file and actions
and generate a class project for a college level class about machine learning

create_class_projects.py --in_file input_file.md --action XYZ --o output_dir

## Action create_project

1) Read the summary stored in --in_file 

2) For each file apply the following prompt to the file
  """
  Act as a data science professor.

  Given the markdown for a lecture, come up with the description of 3 projects
  that can be used to clarify the content of the file .

  Look for Python packages that can be used to implement those projects

  The Difficulty (1 means easy, should take around 7 days to develop, 2 is medium difficulty, should take around 10 days to complete, 3 is hard,should take 14 days to complete)

  The difficulty level should be medium

Write a short bullet-point project brief on how XYZ can be
used for real-time Bitcoin data ingestion in Python.

Include:

- Title
- Difficulty (1 means easy, should take around 7 days to develop, 2 is medium difficulty, should take around 10 days to complete, 3 is hard,should take 14 days to complete)
- Tech Description
- Project Idea
- Python libs
- Is it Free?
- Relevant tool(XYZ) related Resource Links

Avoid long texts or steps
"""
EXAMPLE = """Example:
Title: Ingest bitcoin prices using AWS Glue (AWS Glue is technology XYZ)
Difficulty: 1
Description
AWS Glue is a fully managed extract, transform, and load (ETL) service...
Useful resources: AWS Glue Docs
Is it free?: Free tier available with limits
Python libraries: boto3, PySpark
"""

You must follow the instructions in general_instr.md
