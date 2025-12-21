<!-- toc -->

- [Step 1](#step-1)
- [Step 2.](#step-2)
- [Step 3.](#step-3)
- [Step 4.](#step-4)
- [Step 5.](#step-5)
- [Step 6.](#step-6)

<!-- tocstop -->

Extend dev_scripts_helpers/coding_tools/reorder_python_code to work also on
classes

> dev_scripts_helpers/coding_tools/reorder_python_code.py --input_file
> input_file.py --map_file map_file.md

> dev_scripts_helpers/coding_tools/reorder_python_code.py --input_file
> test/test_hpandas.py --map_file test/file_map.md

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications

- For all the code you must follow the instructions in
  [`/docs/ai_coding/ai.coding.prompt.md`](/docs/ai_coding/ai.coding.prompt.md)

This script executes the following stages:

# Step 1

Read and parse map_file.md which is a markdown file that organizes all the
functions in a file input_file.py into different files

An example of map_file.md is hpandas_map.md

- The header of level 1 of map_file.md is the file that the code needs to go in
  - E.g., `# hpandas_dassert.py` means that all the following functions needs to
    go in [`/helpers/hpandas_dassert.py`](/helpers/hpandas_dassert.py)

- The header of level 2 of map_file.md represent a framed text that separates
  the functions
  ```
  # #############################################################################
  # Index/Axis Validation & Assertions
  # #############################################################################
  ```

- The functions are in a bullet list, for instance
  ```
  - _get_index()
  - dassert_index_is_datetime()
  - dassert_unique_index()
  - dassert_increasing_index()
  - dassert_strictly_increasing_index()
  ```

# Step 2.

Create a list of lists representing the instructions in map_file.md

# Step 3.

Copy the file input_file.py in each of the needed files according to the
instructions in map_file.md

# Step 4.

Remove all the functions in each of the needed files that don't need to be in
that specific file according to the map_file.md

# Step 5.

The functions are reordered in the same way requested by map_file.md

All the manipulation of code need to be done by not parsing AST but by reading
code as text

# Step 6.

Add the framed text to separate the chunks of functions
