# Guidelines for automated PR reviews

<!-- toc -->

- [PR workflows](#pr-workflows)
  * [Working in a branch](#working-in-a-branch)
  * [Filing a PR](#filing-a-pr)
  * [Before requesting review](#before-requesting-review)
  * [During the review cycle](#during-the-review-cycle)
- [Code style](#code-style)
  * [Python code](#python-code)
    + [Naming](#naming)
    + [Docstrings](#docstrings)
    + [Comments](#comments)
    + [Code design](#code-design)
    + [Imports](#imports)
    + [Type annotations](#type-annotations)
    + [Functions](#functions)
    + [Scripts](#scripts)
    + [Logging](#logging)
    + [Unit tests](#unit-tests)
    + [Misc](#misc)
  * [Notebooks](#notebooks)
    + [General](#general)
    + [Jupytext](#jupytext)
    + [Plotting](#plotting)
  * [Markdowns](#markdowns)
  * [Spelling](#spelling)
  * [File system structure](#file-system-structure)

<!-- tocstop -->

This document outlines the rules that all PRs and checked-in code must follow.
It can serve as a guideline for automated PR reviews.

## PR workflows

### Working in a branch

- The branch should be named following the format
  `RelatedIssueTag_Normalized_issue_title`
  - E.g., `HelpersTask123_Provide_branch_name_example`, if the branch is for
    working on the issue #123 in the `helpers` repo with the title "Provide
    branch name example"
- Commit messages should be short and informative
  - Ideally, they should follow the format
    `RelatedIssueTag: High-level commit description`
  - E.g., `HelpersTask123: Add example`
  - Commit messages should not mention the name of the file that has been
    changed by the commit

### Filing a PR

- The title of the PR should match the name of the branch
- The starting post of the PR should briefly describe the content of the PR on a
  high level
- The issue related to the PR must be mentioned in the starting post of the PR
- The PR must not be linked to any issues under the "Development" section
- At least one reviewer must be assigned under "Reviewers"
- The PR author must be listed under "Assignees"

### Before requesting review

- All the checks performed by GitHub Actions must pass
- The branch must be up to date with the master branch
- There should be no conflicts with the master branch
- There should be no files checked in by mistake (such as tmp and log files)
- All checked in files should be checked and formatted by Linter
- No files larger than 500 KB should be checked in
- Screenshots should not be used in PR posts to describe the situation or report
  an error -- copy-and-paste instead

### During the review cycle

- Label "PR_for_reviewers" should be present when a review is requested
- Fixes addressing a review comment should be applied everywhere, not just where
  the reviewer pointed out the issue
- After addressing a review comment, the corresponding conversation should be
  marked as "resolved"
- After all review comments are resolved, "re-request review" button should be
  used to request another round of review

## Code style

### Python code

#### Naming

- Name executable files (scripts) and library functions using verbs (e.g.,
  `download.py`, `download_data()`)
- Name classes and non-executable files using nouns (e.g., `Downloader()`,
  `downloader.py`)
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

#### Docstrings

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
- The more detailed description is followed by a blank line and then the
  param/return description section
  - Use lowercase after `:param XYZ: ...`/`:return:` unless the description
    starts with a proper noun
  - Do not add a period at the end of the param/return descriptions
  - Do not mention the type of the parameters/returned structures
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

#### Comments

- Add a comment for every logically distinct chunk of code
- Use comments to separate chunks of code instead of blank lines
- Avoid empty comments when possible
- Every comment should start with a capital letter
- Every comment should start with a verb in the imperative form
- Every comment should end with a period
- We do not use inline comments; every comment should be on its own separate
  line
- Comments should be placed above the lines that they are referring to
- In `if-elif-else` statements, the comments are placed underneath each
  statement in order to explain the code that belongs to each statement in
  particular
- Avoid mentioning concrete names of variables, functions, classes, files, etc.
  in the comments
  - If it is unavoidable, wrap their names in backticks
- Avoid referring to the type of a variable in the comments
- Do not include implementation details in comments (describe "what" and not
  "how")
- If some code is commented out in a PR, a comment should be added to explain
  the reason why
- Comments with TODOs should have the format of `# TODO(username): ...`

#### Code design

- Follow DRY principle (Don't Repeat Yourself):
  - Factor out common code in a separate function/method
  - Do not copy-and-paste parameter descriptions, instead write them in only one
    function and put a reference to it in the other functions where the same
    parameters are used, e.g., "See `func_name()` for the param description"
- Order functions / classes in a topological order so that the ones at the top
  of the files are the "innermost" and the ones at the end of the files are the
  "outermost"
- Keep public functions in an order representing the typical flow of use, e.g.,
  - Common functions, used by all other functions
  - Read data
  - Process data
  - Save data
- Use banners to separate large sections of code, e.g.:
  ```python
  # #############################################################################
  # Read data.
  # #############################################################################
  ```
  - The text inside the banner should start with a capital letter and end with a
    period

#### Imports

- All imports should be located at the top of the file
- Do not use `import *`
- Do not use `from ... import ...`
  - The only exception is the `typing` package, e.g.,
    `from typing import Iterable, List`
- Always import with a full path from the root of the repo / submodule
- Each module that can be imported should have a docstring at the very beginning
  describing how it should be imported
  - Linter adds it automatically
- No import cycles should be introduced by the changes in the PR

#### Type annotations

- All functions and methods, including constructors, must have type annotations
  for all the parameters and returned structures
  - We use `-> None` if a function doesn't return anything
  - The only exception are invoke tasks, i.e. functions with the `@task`
    decorator - they shouldn't have type annotations
- We use `List[<type of list elements>]` instead of `list`,
  `Dict[<type of keys>, <type of values>]` instead of `dict`,
  `Tuple[<type of tuple elements>]` instead of `tuple`, etc.
- Type annotation `Any` should be avoided, if possible

#### Functions

- Avoid modifying the function input
  - For example, if a function `f` accepts a dataframe `df` as its (sole)
    argument, then, ideally, `f(df)` will not modify `df`
- Use pure functions, i.e. if the function arguments do not change, then the
  returned value should not change (in contrast to, e.g., functions that rely
  upon global state)
- Make a function private (e.g., `_foo_bar()`) when it is a helper of another
  private or public function
- The preferred order of function parameters is:
  - Input parameters
  - Output parameters
  - In-out parameters
  - Default parameters
- Default parameters should be used sparingly and only for parameters that 99%
  of the time are constant
- All the default parameters should be keyword-only
  - They should be separated from the other parameters by `*`
- Do not use lists, maps, objects, etc. as the default value -- instead pass
  `None` and then initialize the default parameter inside the function
- Use a default value of `None` when a function needs to be wrapped and the
  default parameter needs to be propagated
- Do not use use a boolean parameter as a switch controlling some function
  behavior -- instead use a string parameter `mode`, which is allowed to take a
  small well-defined set of values
- For functions dealing with dataframes, avoid hard-wired column name
  dependencies -- instead allow the caller to pass the column name to the
  function as a parameter
- Do not put computations of the output in the `return` line -- instead compute
  the output first, assign it to a variable and then return this variable
- A function should ideally have a single exit point (one line with `return`)
- A function should ideally return objects of only one type (or `None`)
- When calling a function, assign all the input parameter values to variables on
  separate lines and then pass these variables to the function
- Explicitly bind default parameters, i.e. specify the parameter name when
  calling a function, and do not bind non-default parameters
  - E.g., call `func()` like `func(param1, param2, param3=param3)` if `param3`
    is the only parameter with a default value

#### Scripts

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

#### Logging

- Use extensive logging (and not `print()`) for monitoring execution
- Use the following idiom to configure logging:

  ```python
  import helpers.hdbg as hdbg

  _LOG = logging.getLogger(__name__)

  hdbg.init_logger(verbosity=logging.DEBUG)
  ```

- Use positional args in logging (e.g.,
  `_LOG.debug("cmd=%s %s %s", cmd1, cmd2, cmd3)`)

#### Unit tests

- Unit tests should be placed in a `test_*.py` file in the `test` directory,
  close to the library / code it tests
- A test class should test only one function / class
- A test method should only test a single case (e.g., "for these inputs the
  function responds with this output")
- Every test class should inherit from `hunitest.TestCase`
- Adhere to the following conventions for naming:
  - Test file `test_file_name.py` testing the library `file_name.py`
  - Test class `TestFooBar` for the class `FooBar`, and test methods
    `TestFooBar.test_method_a`, `TestFooBar.test_method_b` for the methods
    `FooBar.method_a` and `FooBar.method_b`
  - Test class `Test_foo_bar` for the function `foo_bar()`, and test methods
    `Test_foo_bar.test1`, `Test_foo_bar.test2` for different cases/inputs
- - Do not add the following idiom in the testing file
  ```python
  if __name__ == "__main__":
      unittest.main()
  ```
- A unit test should be independent of all other unit tests
- If there is a lot of common code in individual test methods, it should be
  factored out in a helper method within the test class
- If some code needs to be repeated at the beginning/end of each test method, it
  can be moved to `set_up_test()`/`tear_down_test()` methods and the following
  idiom should be added to the test class:
  ```python
  @pytest.fixture(autouse=True)
  def setup_teardown_test(self):
      # Run before each test.
      self.set_up_test()
      yield
      # Run after each test.
      self.tear_down_test()
  ```
- Test methods should have a docstring describing briefly what case is being
  tested
- Test methods should have param/return type annotations
- Do not create temporary files for tests with `tempfile` -- use
  `self.get_scratch_space()` instead
- If the input to the test is a large piece of code/text, it should be moved to
  a separate file in the `input` dir corresponding to the test
  (`outcomes/<TestClassName.test_method_name>/input`)
- Do not use pickle files for test inputs
- In every test method, separate logically distinct code chunks with comments
  `# Prepare inputs.`, `# Run.` and `# Check.`
- Specify all the input parameter values on separate lines before passing them
  to the function that is being tested
- Do not use `hdbg.dassert` in testing
- Use `self.assert_equal()` instead of `self.assertEqual()`
- Use strings to compare actual and expected outputs instead of data structures
  (e.g., a string representation of a list instead of a list)
- Use `self.check_string()` to compare the actual output to a golden output in
  the `outcomes` dir
- When testing for an assertion, check that you are getting the exact exception
  that is expected
- If a unit test is renamed or removed in a PR, the corresponding files in the
  `outcomes` dir should also be renamed or removed

#### Misc

- If a PR includes renaming a file/variable/parameter/function/class/etc., then
  all the instances and references to it throughout the codebase should be
  updated
- Encode the assumptions made in the code using assertions, e.g.,
  `hdbg.dassert_lt(start_date, end_date)`
  - Report as much information as possible in an assertion
  - Use positional args in `hdbg.dassert` (e.g.,
    `hdbg.dassert_eq(a, 1, msg="No info for %s", method)`)
- Use f-strings in exceptions (e.g.,
  `raise ValueError(f"Invalid server_name='{server_name}'")`)
- Use complete `if-elif-else` statements instead of a sequence of `if`
  statements
- Compile a regex expression only if it's called more than once
- Use `if var is (not) None` to check if `var` is (not) `None` (instead of
  `if (not) var`)
- Use `isinstance()` instead of `type()` to check the type of an object

### Notebooks

#### General

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
- The code in the notebook should adhere to the same style and formatting
  guidelines as the code in libraries and scripts
- Common or general-purpose code should be factored out in functions and moved
  from the notebook to a Python library, which would then be imported in the
  notebook
- There should be no errors in the executed notebook
- Ideally, there should be no warnings in the executed notebook
- Notebook cells should be idempotent, i.e. able of being executed multiple
  times without changing their output value
- If the data is transformed, display a few lines to show the outcome (e.g.,
  `df.head(3)`)
- If any data is discarded/filtered, display the percentage of the rows dropped
- Progress bars should be added where applicable

#### Jupytext

- Every notebook should be accompanied by a Python file paired with the notebook
  by `jupytext`, containing a synchronized copy of the notebook code
- The name of the notebook and the name of its paired Python file should be the
  same, except the extension
- The code in the notebook and in its paired Python file should always be in
  sync
- If the notebook is updated or deleted, then its paired Python file should also
  by updated or deleted, and vice versa
- Linter should be used on both the notebook and its paired Python file

#### Plotting

- Each plot should have a descriptive title
- Each plot should have axes labels
- If there are several lines on the plot, it should have a legend
- In a plotting function, `plt.show()` should not be added at the end
- In a plotting function, the `ax` parameter should be exposed
- If a function plots multiple plots, they should be generally plotted in a
  single figure

### Markdowns

- Names of documentation files should follow the format
  `docs/{component}/{audience}.{topic}.{diataxis_tag}.md`
  - E.g., `docs/documentation_meta/all.diataxis.explanation.md`
- All Markdown files should have a table of contents
  - Linter automatically adds and updates the table of contents
- There should be one and only one level 1 heading (with one `#`) in a Markdown
- The level 1 heading should be located above the table of contents
- Headings should not be boldfaced
- Headings should not be overcapitalized
  - E.g., `Data schema` instead of `Data Schema`
- Text should be reflowed to the maximum of 80 columns per line
- Boldface should be used sparingly
- The use of bullet point lists is encouraged
  - For the items, `-` should be used instead of `*` or circles
- Items in bullet point lists should not end with a period
- Wrap file paths, names of variables, functions and classes in backticks
- Use `>` to indicate a command line (e.g., `> git push` or `docker> pytest`)
- Fenced code blocks should always be accompanied by language markers (e.g.
  `bash`, `python`)
- Indent fenced code blocks one level more than the previous line
- Avoid to use screenshots whenever possible and instead copy-and-paste text
  with the right highlighting
- Use active voice most of the time and use passive voice sparingly
- Be efficient
  - Do not explain things in a repetitive way
  - Rewrite long-winded AI-generated texts in a concise way

### Spelling

- Capitalize the first letter of `Python`
- Spell `Linter` with the first letter in upper case and do not use an article
  (`Linter` instead of `the Linter`)
- Capitalize `JSON`, `CSV`, `DB` and other abbreviations
- Spell commands in lower case and programs with the first letter in upper case
  (e.g., `git` as a command, `Git` as a program)
- Represent intervals with `[a, b), (a, b], (a, b), [a, b]`, not `[a, b[`
- Write `hyperparameter` without a hyphen

### File system structure

- If a new directory with code is added, it should contain an empty
  `__init__.py` file
- Notebooks should generally be located under the `notebooks` dir
- Unit tests should be located under the `test` dir
  - Golden outcomes for tests should be located under the `test/outcomes` dir
- Documentation files should generally be located under the `docs` dir
