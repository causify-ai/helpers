# Guidelines for automated PR reviews

## Python code

### Naming

- Name executable files and library functions using verbs
  - E.g., `download.py` and not `downloader.py`
  - E.g., `download_data()` and not `data_downloader()`
- Name classes and non-executable files using nouns
  - E.g., `Downloader()`, `downloader.py`
- Name decorators with an adjective or a past tense verb (e.g., `timed`)
- Variable and function names should not reference implementation details,
   things that can change or details that are not important
  - E.g., the name of a variable should not include its type, e.g. use
    `embeddings` instead of `embeddings_list`
- Abbreviations in the names should be avoided, except for the following: `df`
  (dataframe), `srs` (series), `idx` (index), `id` (identifier), `val` (value),
  `var` (variable), `args` (arguments), `kwargs` (keyword arguments), `col`
  (column)
- Do not repeat in a function name what is already included in the library name
  (avoid "code stutter")
- Use `dir` and not `directory` or `folder`
- Use `timestamp` and not `ts` or `datetime`
- To refer to the name of a column, use `..._col` and not `..._col_name` or
  `..._column`

### Docstrings

- All functions and methods must have a docstring
- Docstrings should be wrapped in triple quotation marks (`"""`)
  - The opening and closing triple quotation marks should be located on their
    own separate lines
- Every docstring should start with a capital letter
- Every docstring should start with a verb in the imperative form
- Every docstring should begin with a one-line description of what the function
  does
  - It must fit into a single line and end with a period
- The first docstring line is followed by a blank line and then, optionally, by
  a longer description (possibly on multiple lines) with a more detailed
  explanation of what the function does
  - It should not describe parameters / what is being returned
  - It should not describe implementation details that can be changed
  - It should describe the goal of the function, the interface and what the user
    needs to know to use the function
- The more detailed description is followed by a blank line and then the param /
  return description section
  - Use lowercase after `:param XYZ: ...` / `:return:` unless the description
    starts with a proper noun
  - Do not add a period at the end of the param / return descriptions
  - Do not mention the type of the parameters / returned structures
  - Do not mention default values of parameters in parameter descriptions
  - Follow this example for indentation of parameter descriptions:
    ```python
    :param param1: a very very long param description that
        continues into a second line
    :param param2: a param with two possible values
        - first value description
        - second value description that is very long and
          continues into a second line
    ```
- Adding examples (e.g., of input and output) to the docstring is encouraged
- References to variables, file paths, functions, classes, etc. should be
  wrapped in backticks
- Multiline representations of data structures (e.g., an output example) should
  be wrapped in triple backticks

### Docstrings / linter
