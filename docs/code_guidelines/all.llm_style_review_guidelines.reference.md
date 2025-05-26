# Guidelines for automated PR reviews

## Python code

### Naming

- Name functions using verbs and verbs/actions
  - E.g., `download_data()`
- Name classes using nouns
  - E.g., `Downloader()`
- Name decorators with an adjective or a past tense verb
  - E.g., `timed`
- Variable and function names should not reference implementation details, and
  things that can change or details that are not important
  - E.g., the name of a variable should not include its type
    - E.g. use `embeddings` instead of `embeddings_list`
- Abbreviations in the names should be avoided, except for the following
  - `df` for dataframe
  - `srs` for series
  - `idx` for index
  - `id` for identifier
  - `val` for value
  - `var` for variable
  - `args` for arguments and `kwargs` for keyword arguments
  - `col` for columns and `row` for rows
- Do not repeat in a function name what is already included in the library name
  (avoid "code stutter")
- Use `dir` and not `directory` or `folder`
- Use `file_name` and not `filename`
- Use `dir_name` and not `dirname`
- Use `timestamp` and not `ts` or `datetime`
- To refer to the name of a column, use `..._col` and not `..._col_name` or
  `..._column`

### Docstrings

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

### Comments

- Add a comment for every logically distinct chunk of code
- Use comments to separate chunks of code instead of blank lines
- We do not use inline comments; every comment should be on its own separate
  line, before the line it refers to
  - In `if-elif-else` statements, the comments are placed underneath each
    statement in order to explain the code that belongs to each statement in
    particular
- Avoid mentioning concrete names of variables, functions, classes, files, etc.
  in the comments
  - If it is unavoidable, wrap their names in backticks
- Avoid referring to the type of a variable in the comments
- Do not include implementation details in comments
  - Describe "what" and "why" the code does something and not "how" the code
    does it
- If some code is commented out in a PR, a comment should be added to explain
  the reason why

### Code design

- Follow DRY principle (Don't Repeat Yourself):
  - Factor out common code in a separate function / method
  - Do not copy-and-paste parameter descriptions, instead write them in only one
    function and put a reference to it in the other functions where the same
    parameters are used
  - E.g., "See `func_name()` for the param description"
- Keep public functions in an order representing the typical flow of use, e.g.,
  - Common functions, used by all other functions
  - Read data
  - Process data
  - Save data

### Type annotations

- For type hints use `List[<type of list elements>]` instead of `list`,
  `Dict[<type of keys>, <type of values>]` instead of `dict`,
  `Tuple[<type of tuple elements>]` instead of `tuple`, etc.

### Functions

- Avoid pure functions without side effects, i.e. for the same input arguments
  the returned value should not change (in contrast to, e.g., functions that rely
  upon global state)
- Functions should not modify the function inputs
  - E.g., if a function `f()` accepts a dataframe `df` as its argument, then
    `f()` will not modify `df` but make a copy and work on it
- The preferred order of function parameters is:
  - Input parameters
  - Output parameters
  - In-out parameters
  - Default parameters
- Default parameters should be used sparingly and only for parameters that 99%
  of the time are constant
- All the default parameters should be keyword-only
  - They should be separated from the other parameters by `*`
- Do not use mutable objects (such as lists, maps, objects) as default value for
  functions, instead pass `None` and then initialize the default parameter inside
  the function
- Use a default value of `None` when a function needs to be wrapped and the
  default parameter needs to be propagated
- Do not use use a boolean parameter as a switch controlling some function
  behavior, instead use a string parameter `mode`, which is allowed to take a
  small well-defined set of values
- For functions dealing with dataframes, avoid hard-wired column name
  dependencies, instead allow the caller to pass the column name to the function
  as a parameter
- Do not put computations of the output in the `return` line
  - Instead compute the output first, assign it to a variable and then return
    this variable
- A function should have a single exit point, i.e., one single line with `return`
- A function should ideally return objects of only one type (or `None`)
- When calling a function, assign all the input parameter values to variables on
  separate lines and then pass these variables to the function
- Explicitly bind default parameters, i.e. specify the parameter name when
  calling a function, and do not bind non-default parameters
  - E.g., call `func()` like `func(param1, param2, param3=param3)` if `param3`
    is the only parameter with a default value

### Logging

- Use logging `_LOG.debug()` and not `print()` for tracing execution
- Use positional args in logging and not inline formatting
  - E.g., `_LOG.debug("cmd=%s", cmd1)` instead `_LOG.debug(f"cmd={cmd1}")`
- Use the following idiom to configure logging:

  ```python
  import helpers.hdbg as hdbg

  _LOG = logging.getLogger(__name__)

  hdbg.init_logger(verbosity=logging.DEBUG)
  ```

### Unit tests

- A test class should test only one function or class
- A test method should only test a single case
  - E.g., "for these inputs the function responds with this output"
- Adhere to the following conventions for naming:
  - Class `TestFooBar` tests the class `FooBar` and its methods
    `TestFooBar.test_method_a`, `TestFooBar.test_method_b` test the methods
    `FooBar.method_a` and `FooBar.method_b`
  - Class `Test_foo_bar` tests the function `foo_bar()`
  - `Test_foo_bar.test1`, `Test_foo_bar.test2` for different cases / inputs
- A unit test should be independent of all the other unit tests
- If there is a lot of common code across individual test methods, it should be
  factored out in a helper method within the test class
- If some code needs to be repeated at the beginning / end of each test method,
  it should be moved to `set_up_test()` / `tear_down_test()` methods and the
  following idiom should be added to the test class:
  ```python
  @pytest.fixture(autouse=True)
  def setup_teardown_test(self):
      # Run before each test.
      self.set_up_test()
      yield
      # Run after each test.
      self.tear_down_test()
  ```
- Each test method should have a docstring describing briefly what case is being
  tested
- Test methods should have type hint annotations
- Do not create temporary files for tests (e.g., with `tempfile`) but use
  `hunittest.TestCase.get_scratch_space()` instead
- If the input to the test is a large piece of code / text, it should be moved
  to a separate file in the `input` dir corresponding to the test
  - E.g., `outcomes/<TestClassName.test_method_name>/input` and read through the
    function `self.get_input_dir()` of `TestCase`
- Do not use pickle files for test inputs
- In every test method, separate logically distinct code chunks with comments
  - E.g.,
    ```
    # Prepare inputs.
    ...
    # Run test.
    ...
    # Check outputs.
    ```
- Do not use `hdbg.dassert` in testing but use `self.assert*()` methods
- Prefer `self.assert_equal()` instead of `self.assertEqual()`
- Use strings to compare actual and expected outputs instead of data structures
  - E.g., use a string representation of a list instead of a list
- Use `self.check_string()` to compare the actual output to a golden output in
  the `outcomes` dir, when the output is large or needs to be modified easily
- When testing for an assertion, check that you are getting the exact exception
  that is expected

### Misc

- Encode the assumptions made in the code using assertions and report as much
  information as possible in an assertion to make it easy to debug the output
  - E.g., `hdbg.dassert_lt(start_date, end_date)`
- Do not use f-strings in `hdbg.dassert()`
- Use f-strings in exceptions
  - E.g., `raise ValueError(f"Invalid server_name='{server_name}'")`)
- Use complete `if-elif-else` statements instead of a sequence of `if`
  statements
- Compile a regex expression only if it's called more than once
- Use `if var is (not) None` to check if `var` is (not) `None` (instead of
  `if (not) var`)
- Use `isinstance()` instead of `type()` to check the type of an object

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
- If any data is discarded / filtered, display the percentage of the rows
  dropped
- Progress bars should be added where applicable

### Jupytext

- Every notebook should be accompanied by a Python file paired with the notebook
  by `jupytext`, containing a synchronized copy of the notebook code
- The name of the notebook and the name of its paired Python file should be the
  same, except the extension
- The code in the notebook and in its paired Python file should always be in
  sync
- If the notebook is updated or deleted, then its paired Python file should also
  by updated or deleted, and vice versa
- Linter should be used on both the notebook and its paired Python file

### Plotting

- Each plot should have a descriptive title
- Each plot should have axes labels
- If there are several lines on the plot, it should have a legend
- In a plotting function, `plt.show()` should not be added at the end
- In a plotting function, the `ax` parameter should be exposed
- If a function plots multiple plots, they should be generally plotted in a
  single figure

## Markdowns

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

## File system structure

- If a new directory with code is added, it should contain an empty
  `__init__.py` file
- Notebooks should generally be located under the `notebooks` dir
- Unit tests should be located under the `test` dir
  - Golden outcomes for tests should be located under the `test/outcomes` dir
- Documentation files should generally be located under the `docs` dir

## Spelling

- Capitalize the first letter of `Python`
- Spell `Linter` with the first letter in upper case and do not use an article
  (`Linter` instead of `the Linter`)
- Capitalize `JSON`, `CSV`, `DB` and other abbreviations
- Spell commands in lower case and programs with the first letter in upper case
  (e.g., `git` as a command, `Git` as a program)
- Represent intervals with `[a, b), (a, b], (a, b), [a, b]`, not `[a, b[`
- Write `hyperparameter` without a hyphen
