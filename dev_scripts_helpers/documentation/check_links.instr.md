## Step 1
1) Write a Python script dev_scripts_helpers/documentation/check_links.py that accepts a file and checks
if all the URL links are reachable

check_links.py --in_file foobar.md

- Links appear in several forms for example
[https://github.com/gpsaggese/umd_classes/tree/master](https://github.com/gpsaggese/umd_classes/tree/master)
[List of projects](https://docs.google.com/spreadsheets/d/1H_Ev1psuPpUrrRcmBrBb2chfurSo5rPcAdd6i2SIUTQ/edit?gid=0#gid=0)
https://github.com/gpsaggese/umd_classes/blob/master/class_project/DATA605/Spring2025/project_description.md

- Output a list of all the URLs that were found and whether they are reachable or
  not
- Print the number of URLs that are broken
- For all the code you must follow the instructions in `ai.coding.prompt.md`

2) Generate unit tests for the code following the instructions in ai.unit_test.prompt.md

3) Generate a short description of how to use the script in a file close to the
   script with extension .md

## Step 2

- Ignore everything in the table of content between the following tags 

<!-- toc -->

<!-- tocstop -->

using one function in helpers/hmarkdown*.py. If you can't find it stop.

## Step 3

- Generate a cfile with the errors using the functions inside
  helpers/hmarkdown*.py. If you can't find it stop.

- Implement the TODO(ai) in dev_scripts_helpers/documentation/check_links.py

## Step 4

Implement logic for converting references inside the repo like

/tutorial_template/tutorial_template/README.md

to URL using code equivalent to

# git@github.com:causify-ai/helpers.git
REPO_URL=$(git remote get-url origin | sed -e 's/.git$//' -e 's/git@github.com:/https:\/\/github.com\//')
BRANCH_NAME=$(git branch --show-current)

url="${REPO_URL}/blob/${BRANCH_NAME}/${FILE_PATH}"
echo "$url"

## Step 5

When reporting the lines where there are the errors make sure to keep in account
the lines that were removed from the table of content, since the references
should be to the original file and not the one after the TOC was removed

Write the cfile by default in the file `cfile` and report that
