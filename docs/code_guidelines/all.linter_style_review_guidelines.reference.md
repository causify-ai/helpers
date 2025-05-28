# Guidelines for automated PR reviews

## Python code

### Naming

- Name executable Python scripts using verbs and actions
  - E.g., `download.py` and not `downloader.py`
- Name non-executable files using nouns 
  - E.g., `downloader.py`
- Use `dir` and not `directory` or `folder`
  - E.g., `dir_path`
- Use `file_name` and not `filename`
  - E.g., `file_name` for storing the name of a file
- Use `dir_name` and not `dirname`
  - E.g., `dir_name` for storing the name of a directory
- Use `timestamp` and not `ts` or `datetime`
  - E.g., `event_timestamp`
- To refer to the name of a column, use `..._col` and not `..._col_name` or
  `..._column`
  - E.g., `age_col` for a column storing age values

### Docstrings

- The first docstring line is followed by a blank line and then, optionally, by
  a longer description (possibly on multiple lines) with a more detailed
  explanation of what the function does
- The more detailed description is followed by a blank line and then the param
  and return description section in REST style
- The more detailed description is followed by a blank line and then the param
  and return description section in REST style
  - Use lowercase after `:param XYZ: ...` / `:return:` unless the description
    starts with a proper noun
- Do not mention default values of parameters in parameter descriptions
- Docstrings should be wrapped in triple quotation marks (`"""`)
  - The opening and closing triple quotation marks should be located on their
    own separate lines
- Every docstring should start with a capital letter
- Every docstring should start with a verb in the imperative form
- Every docstring should begin with a one-line description of what the function
  does, fit into a single line and end with a period
- Adding examples (e.g., of input and output) to the docstring is encouraged
- References to variables, file paths, functions, classes, etc. should be
  wrapped in backticks

### Comments

- Avoid empty comments and line inside the code when possible
- Every comment should start with a capital letter
- Every comment should start with a verb in the imperative form
- Every comment should end with a period
- Comments with TODOs should have the format of `# TODO(username): ...`

### Code design

- Order functions / classes in a topological order so that the ones at the top
  of the files are the "innermost" and the ones at the end of the files are the
  "outermost"
- Use banners to separate large sections of code, e.g.:
  ```python
  # #############################################################################
  # Read data.
  # #############################################################################
  ```
  - The text inside the banner should start with a capital letter and end with a
    period

### Imports

- All imports should be located at the top of the file
- Do not use `import *`
- Do not use `from ... import ...`, unless it is the `typing` package, e.g.,
  `from typing import Iterable, List`
- Always import with a full path from the root of the repo / submodule
- Each module that can be imported should have a docstring at the very beginning
  describing how it should be imported
  - Linter adds it automatically
- No import cycles should be introduced by the changes in the PR

### Type annotations
- All functions and methods, including constructors, must have type annotations
  for all the parameters and returned structures
  - Use `-> None` if a function doesn't return anything
  - The only exception are invoke tasks, i.e. functions with the `@task`
    decorator, they shouldn't have type annotations
- Type annotation `Any` should be avoided, if possible

### Functions
- Make a function private (e.g., `_foo_bar()`) when it is a helper of another
  private or public function

### Scripts

- Use Python and not bash for scripting
- All Python scripts that are meant to be executed directly should:
  - Be marked as executable files with `> chmod +x foo_bar.py`
  - Have the standard Unix shebang notation at the top: `#!/usr/bin/env python`
  - Use the following idiom at the bottom:
    ```python
    if __name__ == "__main__":
        ...
    ```
  - Use `argparse` for argument parsing

### Unit tests
- Unit tests should be placed in a `test_*.py` file in the `test` directory,
  close to the library / code it tests
  - Test file `test_file_name.py` testing the library `file_name.py`
- Every test class should inherit from `hunitest.TestCase`
- We use `pytest` as test harness so do not add the following idiom in the
  testing file
  ```python
  if __name__ == "__main__":
      unittest.main()
  ```
- If a unit test is renamed or removed in a PR, the corresponding files in the
  `outcomes` dir should also be renamed or removed

### Misc
- If a PR includes renaming a file, variable, parameter, function, class, etc.,
  then all the instances and references to it throughout the codebase should be
  updated

## Notebooks

### General

- The name of a notebook should generally be the same as the branch name, unless
  it's a Master notebook
- All notebooks should have a table of contents
  - Linter automatically adds and updates the table of contents
- At the top of the notebook there should be a Markdown cell `# Description`,
  followed by a Markdown cell with an explanation of the notebook's goal, what
  it does, etc.
- Immediately below the description, there should be a Markdown cell
  `# Imports`, followed by a code cell importing all the needed libraries
  - It should include autoreload modules to keep the local code updated in real
    time:
    ```python
    %load_ext autoreload
    %autoreload 2
    ```
  - All the imports should be located in a single cell
- Below the cell with the imports, there should be a code cell that configures
  the logging and notebook style, and reports execution info:
  ```python
  # Configure logger.
  hdbg.init_logger(verbosity=logging.INFO)
  _LOG = logging.getLogger(__name__)
  # Print system signature.
  _LOG.info("%s", henv.get_system_signature()[0])
  # Configure the notebook style.
  hprint.config_notebook()
  ```
- The rest of the notebook should be clearly organized using Markdown cells with
  headings of different levels
- There should be no errors in the executed notebook
- Ideally, there should be no warnings in the executed notebook

### Jupytext

- Each notebook must have an accompanying Python file, linked via `jupytext`,
  which contains a synchronized copy of the notebook's code
- The notebook and its paired Python file should share the same name, differing
  only in their file extensions
- Ensure that the code in the notebook and its paired Python file remains
  synchronized at all times
- If you update or delete the notebook, you must also update or delete its
  paired Python file, and vice versa

## Markdowns

- Names of documentation files should follow the format 
  `docs/{component}/{audience}.{topic}.{diataxis_tag}.md`
  to help in organizing and categorizing documentation files effectively
  - E.g., `docs/documentation_meta/all.diataxis.explanation.md`
  - The `{component}` part specifies the part of the project the documentation
    is related to
  - The `{audience}` part indicates who the documentation is intended for
  - The `{topic}` part describes the subject matter of the documentation
  - The `{diataxis_tag}` part categorizes the documentation according to the
    Diátaxis framework (e.g., explanation, tutorial)
- All Markdown files should have a table of contents
  - Linter automatically adds and updates the table of contents
- There should be one and only one level 1 heading (with one `#`) in a Markdown
  - The level 1 heading serves as the main title of the document
  - It should clearly convey the primary topic or purpose of the document
  - The level 1 heading should be located above the table of contents
- Headings should not be boldfaced
- Headings should not be overcapitalized
  - E.g., `Data schema` instead of `Data Schema`
- Text should be reflowed to the maximum of 80 columns per line
- Fenced code blocks should always be accompanied by language markers
  - E.g., `bash`, `python`
- Indent fenced code blocks at the same level as the previous line

## Spelling

- Spell commands in lower case and programs with the first letter in upper case
  - E.g., `git` as a command, `Git` as a program
  - E.g., capitalize the first letter of `Python`
- Spell `Linter` with the first letter in upper case and do not use an article
  - E.g., `Linter` instead of `the Linter`
- Capitalize `JSON`, `CSV`, `DB` and other abbreviations
- Represent intervals with `[a, b), (a, b], (a, b), [a, b]`, not `[a, b[`
- Write `hyperparameter` without a hyphen
- Use `Python` for scripting and automation tasks
