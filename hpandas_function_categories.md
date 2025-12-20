Create a script that perform the following operations

> reorder_python_code.py --input_file XYZ.py --map_file XYZ.md

- For all the code you must follow the instructions in
  `docs/ai_coding/ai.coding.prompt.md`

Step 1. Read and parse hpandas_map.md which is a markdown file 
that organizes all the functions in `helpers/hpandas.py` into different
files based on their functionality.

- The header of level 1 is the file that the code needs to go in
  - E.g., `# hpandas_dassert.py` means that all the code needs to go in
    `helpers/hpandas_dassert.py`

- The header of level 2 represent a framed text that separates the functions
```
# #############################################################################
# Index/Axis Validation & Assertions
# #############################################################################
```

The functions are in a bullet list
- _get_index()
- dassert_index_is_datetime()
- dassert_unique_index()
- dassert_increasing_index()
- dassert_strictly_increasing_index()

Step 2. Create a list of lists representing the data in `helpers/hpandas.py`

Step 3. Copy the file helpers/hpandas.py in each of the needed files

Step 4. Remove all the functions that don't need to be in a specific file
according to the map
