<!-- toc -->

- [Guidelines for automated PR reviews](#guidelines-for-automated-pr-reviews)
  * [Python code](#python-code)
    + [Naming](#naming)
    + [Docstrings](#docstrings)
    + [Comments](#comments)
    + [Code implementation](#code-implementation)
    + [Code design](#code-design)
    + [Type annotations](#type-annotations)
    + [Functions](#functions)
    + [Logging](#logging)
    + [Unit tests](#unit-tests)
  * [Notebooks](#notebooks)
    + [General](#general)
    + [Plotting](#plotting)
  * [Markdowns](#markdowns)

<!-- tocstop -->

# Guidelines for PR reviews

## Python code

### Naming

- Name functions using verbs and verbs/actions
  - Good: `download_data()`, `process_input()`, `calculate_sum()`
  - Good: Python internal functions as `__repr__`, `__init__` are valid
  - Good: Functions names like `to_dict()`, `_parse()`, `_main()` are valid
- Name classes using nouns
  - Good: `Downloader()`, `DataProcessor()`, `User()`
  - Bad: `DownloadStuff()`, `ProcessData()`, `UserActions()`
- Name decorators with an adjective or a past tense verb
  - Good: `timed`, `cached`, `logged`
  - Bad: `time`, `cache`, `log`
- Variable and function names should not reference implementation details, and
  things that can change or details that are not important
  - E.g., the name of a variable should not include its type
    - Good: `embeddings`
    - Bad: `embeddings_list`
    - Good: `data`
    - Bad: `data_dict`
- Abbreviations in the names of variables and functions should be avoided
  - Exceptions are the following 
    - `df` for dataframe
    - `srs` for series
    - `idx` for index
    - `id` for identifier
    - `val` for value
    - `var` for variable
    - `args` for arguments and `kwargs` for keyword arguments
    - `col` for columns and `row` for rows
- Do not repeat in a function name what is already included in the library name
  avoiding "code stutter"
  - E.g., if using a library named `math`, avoid naming a function
    `math_calculate()`
    - Good: `calculate()`
    - Bad: `math_calculate()`

### Docstrings

- All functions and methods must have a docstring
  - Good:
    ```
    def add(a, b):
      """
      Add two numbers and return the result
      """
      return a + b
    ```
  - Bad:
    ```
    def add(a, b):
      return a + b
    ```
- The docstring must describe the goal of the function, the interface and what
  the user needs to know to use the function
  - Good: "Calculate the sum of two numbers and return the result."
  - Good
    ```
    def get_repository_settings(
        repo: github.Repository.Repository,
    ) -> Dict[str, Any]:
        """
        Get the current settings of the repository.

        :param repo: GitHub repository object
        :return: dictionary containing repository settings
        """
    ```
- The docstring must use imperative form, whenever possible
  - Good: "Calculate the sum of two numbers and return the result."
  - Bad: "Calculates the sum of two numbers and returns the result."
- The docstring should not describe implementation details that can be changed
  - Good: "Sort the list of integers in ascending order."
  - Bad: "Use the quicksort algorithm to sort the list of integers in ascending
    order."
- Follow this example for indentation of parameter descriptions:
  - Good
    ```python
    :param param1: a very very long param description that
        continues into a second line
    :param param2: a param with two possible values
        - first value description
        - second value description that is very long and
          continues into a second line
    ```
- Adding examples (e.g., of input and output) to the docstring is encouraged
  - Good
    ```
    # Example usage:
    result = add_numbers(3, 5)
    # The result is 8.
    ```
- References to variables, file paths, functions, classes, etc. should be
  wrapped in backticks
  - Good: "The `add_numbers()` function takes two arguments `a` and `b`."
  - Bad: "The add_numbers() function takes two arguments a and b."
- Multi-line representations of data structures (e.g., an output example) should
  be wrapped in triple backticks
  - Good
    ```
    { "name": "John", "age": 30, "city": "New York" }
    ```

### Comments

- Add a comment for every logically distinct chunk of code, spanning 4-5 lines
- Use comments to separate chunks of code instead of blank lines
  - Good:
    ```
    function1()
    # Then do something else.
    function2()
  - Bad:
    ```
    function1()

    function2()
    ```
- Do not use inline comments; every comment should be on its own separate line,
  before the line it refers to
  - Good:
    ```
    # Grant access to admin panel access_admin_panel().
    if user.is_admin(): 
    ```
  - Bad:
    ```
    if user.is_admin(): # Check if the user is an admin access_admin_panel().
    ```
  - In `if-elif-else` statements, the comments are placed underneath each
    statement in order to explain the code that belongs to each statement in
    particular
    Good:
    ```
    if ...:
      # Do this
    else:
      # Do that
    ```
- Avoid referring to the type of a variable in the comments
  - Keeps comments focused on functionality rather than implementation specifics
  - Good: "Store the user's age for validation."
  - Bad: "Store the user's age as an integer for validation."
- Do not include implementation details in comments
  - Describe "what" and "why" the code does something and not "how" the code
    does it
  - Ensures comments remain relevant even if the implementation changes
- If some code is commented out in a PR, a comment should be added to explain
  the reason why
  - Provides context for future reference and helps other developers understand
    the decision
  - E.g., "This section is commented out due to a known bug that needs fixing"
    or "Temporarily disabled for performance testing"

### Code implementation

- Encode the assumptions made in the code using assertions and report as much
  information as possible in an assertion to make it easy to debug the output
  - Good:
    ```
    hdbg.dassert_lt(start_date, end_date,
      msg="start_date needs to be before end_date")
    ```
  - Ensure that assertions provide detailed information for debugging
  - Use assertions to validate input parameters and preconditions
- Do not use f-strings in `hdbg.dassert()`, but use traditional string
  formatting methods in assertions
  - Good:
    `hdbg.dassert_eq(len(list1), len(list2), "Lists must be of equal length: %d vs %d" % (len(list1), len(list2)))`

- Add type hints only to the function definitions, if they are missing.
  - Good:
    ```
    def process_data(data, threshold=0.5):
        results = []
        for item in data:
            if item > threshold:
                results.append(item)
        return results
    ```
  - Bad:
    ```
    def process_data(data: List[float], threshold: float = 0.5) -> List[float]:
        results: List[float] = []
        for item in data:
            if item > threshold:
                results.append(item)
        return results
    ```

- Avoid complex assignments into if-then-else statements.
  - Good:
    ```
    capitalized_parts = []
    for w in parts:
        if is_first_or_last or w.lower() not in small_words:
            w_out = w.capitalize()
        else:
            w_out = w.lower()
    capitalized_parts.append(w_out)
    ```
  - Bad:
    ```
    capitalized_parts = [
        w.capitalize() if is_first_or_last or w.lower() not in small_words else w.lower()
        for w in parts
    ]
    ```
    to:

  - Good:
    ```
    if i == 0:
        is_first_or_last = True
    elif i == len(tokens) - 1:
        is_first_or_last = True
    elif i > 0 and not re.search(r'\w', tokens[i - 1]):
        is_first_or_last = True
    elif i < len(tokens) - 1 and not re.search(r'\w', tokens[i + 1]):
        is_first_or_last = True
    else:
        is_first_or_last = False
    ```
  - Bad:
    ```
    is_first_or_last = (i == 0 or i == len(tokens) - 1 or
                    (i > 0 and not re.search(r'\w', tokens[i - 1])) or
                    (i < len(tokens) - 1 and not re.search(r'\w', tokens[i + 1])))
    ```

- Provide clear and informative error messages in exceptions using f-strings
  - Good: `raise ValueError(f"Invalid server_name='{server_name}'")`
  - Good: `raise TypeError(f"Expected type int, but got {type(var).__name__}")`
- Use complete `if-elif-else` statements instead of a sequence of `if`
  statements
  - Ensure logical flow and clarity in conditional statements
  - Good:
    ```python
    if condition1:
      # Execute block for condition1.
      ...
    elif condition2:
      # Execute block for condition2.
      ...
    else:
      # Execute block if none of the above conditions are met or raise an
      # exception.
    ```
- Compile a regex expression only if it's called more than once
  - Optimize performance by compiling regex expressions that are reused
  - E.g.,
    ```
    import re
    pattern = re.compile(r'\d+')
    if pattern.match(string):
      # Do something.
    ```
- Use `if var is None` to check if `var` is `None` instead of `if not var`
  - Good: `if my_variable is None:`
  - Bad: `if not my_variable:`
- Use `isinstance()` instead of `type()` to check the type of an object
  - Good: `if isinstance(obj, str):`
  - Bad: `if type(obj) == str:`
- Do not use `import *`
  - Good: `from math import sqrt, pi`
  - Bad: `from math import *`
- Do not use `from ... import ...`, unless it is the `typing` package, e.g.,
  `from typing import Iterable, List`
  - Good: `from typing import Dict, Tuple`
  - Bad: `from os import path`
- Always import with a full path from the root of the repo / submodule
  - Good: `import myproject.module.submodule`
  - Bad: `from submodule import my_function`

### Code design

- Follow DRY principle (Don't Repeat Yourself):
  - Factor out common code in a separate function/method
  - Do not copy-and-paste parameter descriptions; instead, write them in only
    one function and put a reference to it in the other functions where the same
    parameters are used
    - E.g., "See `func_name()` for the param description"
  - Avoid redundancy in code logic and comments
- Keep public functions in an order representing the typical flow of use:
  - Common functions, used by all other functions
    - E.g., utility functions like `log_message()`, `validate_input()`
  - Read data
    - Good: `read_csv()`, `load_json()`
  - Process data
    - Good: `clean_data()`, `transform_data()`
  - Save data
    - Good: `write_csv()`, `export_json()`
- Ensure that function names are descriptive and convey their purpose
- Use comments to explain complex logic or calculations
- Implement error handling to manage exceptions and edge cases
- Use inheritance or composition to reuse code in object-oriented programming

### Type annotations

- For type hints use use `List`, `Dict`, and `Tuple` to provide more explicit
  type information and help with static type checking
  - E.g., `List[int]` instead of `list`
  - E.g., `List[str]` instead of `list`
  - Use `Dict` instead of `dict`
    - E.g., `Dict[str, int]` instead of `dict`
    - E.g., `Dict[int, List[str]]` instead of `dict`
  - Use `Tuple` instead of `tuple`
    - E.g., `Tuple[int, str]` instead of `tuple`
    - E.g., `Tuple[str, List[int]]` instead of `tuple`

### Functions

- Avoid pure functions without side effects, i.e., for the same input arguments,
  the returned value should not change (in contrast to functions that rely upon
  external state)
- Functions should not modify the function inputs
  - E.g., if a function `f()` accepts a dataframe `df` as its argument, then
    `f()` will not modify `df` but make a copy and work on it
  - This ensures that the original data remains unchanged and can be reused
- To maintain clarity and consistency in function definitions, use the following
  order of parameters in a function declaration:
  - Input parameters
  - Output parameters
  - In-out parameters
  - Default parameters
- Default parameters should be used sparingly and only for parameters that 99%
  of the time are constant
- All the default parameters should be keyword-only
  - They should be separated from the other parameters by `*`
    - Good: `def example_function(param1: str, *, default_param1: int = 10)`
    - Bad: `def example_function(param1: str, default_param1 : int =10)`
  - This ensures that default parameters are always explicitly specified by
    name, improving readability
- Do not use mutable objects (such as lists, maps, objects) as default value for
  functions; instead, pass `None` and then initialize the default parameter
  inside the function
  - E.g., instead of using a list as a default parameter, use `None` and
    initialize the list inside the function:
  - Good:
    ```
    def add_item(item: str, *, items: Optional[List[str]]) -> List[str]:
      if items is None:
        items = []
      items.append(item)
      return items
    ```

- Do not use a boolean parameter as a switch controlling some function behavior;
  instead, use a string parameter `mode`, which is allowed to take a small
  well-defined set of values
  - Good: `def process_data(mode: str = 'fast'):` where `mode` can be `'fast'`,
    `'slow'`, etc
- For functions dealing with dataframes, avoid hard-wired column name
  dependencies; instead, allow the caller to pass the column name to the
  function as a parameter
  - E.g., `def calculate_average(df: pd.DataFrame, column_name: str):`
- Do not put computations of the output together in a `return` statement,
  instead, compute the output first, assign it to a variable, and then return
  this variable
  - Good
    ```
    result = compute_value()
    return result
    ```
  - Bad
    ```
    return compute_value()
    ```
- A function should have a single exit point, i.e., one single line with
  `return`
  - Good:
    ```python
    def calculate_total(price, tax):
        total = price + (price * tax)
        return total
    ```
  - Bad:
    ```python
    def calculate_total(price, tax):
        if price > 0:
            return price + (price * tax)
        else:
            return 0
    ```
- A function should ideally return objects of only one type (or `None`)
- When calling a function, assign all the input parameter values to variables on
  separate lines and then pass these variables to the function
  - Good:
    ```
    param1 = 10
    param2 = 11
    result = my_function(param1, param2)
    ```
  - Bad:
    ```
    result = my_function(10, 11)
    ```
- Explicitly bind default parameters, i.e., specify the parameter name when
  calling a function, and do not bind non-default parameters
  - Good: `func(10, 20, param3=30)`
  - Bad: `func(10, 20, 30)`

### Logging

- Use logging `_LOG.debug()` and not `print()` for tracing execution
  - Good: `_LOG.debug("value=%s", value)`
  - Bad: `print("value=%s", value)`
- Use positional args in logging and not inline formatting
  - Good: `_LOG.debug("cmd=%s", cmd1)`
  - Bad: `_LOG.debug(f"cmd={cmd1}")`
- Use the following idiom to configure logging:
  ```python
  import helpers.hdbg as hdbg

  _LOG = logging.getLogger(__name__)
  ...

  hdbg.init_logger(verbosity=logging.DEBUG)
  ```

### Unit tests

- A test class should test only one function or class to help understanding test
  failures
- A test method should only test a single case to ensures clarity and precision
  in testing
  - E.g., "for these inputs the function responds with this output"
- Adhere to the following conventions for naming:
  - Class `TestFooBar` tests the class `FooBar` and its methods
    - `TestFooBar.test_method_a`, `TestFooBar.test_method_b` test the methods
      `FooBar.method_a` and `FooBar.method_b`
  - Class `Test_foo_bar` tests the function `foo_bar()`
    - E.g., `Test_foo_bar.test_valid_input`, `Test_foo_bar.test_invalid_input`
      for different cases / inputs
  - `Test_foo_bar.test1`, `Test_foo_bar.test2` for different cases / inputs
- A unit test should be independent of all the other unit tests
  - Ensures that tests do not affect each other and can be run in isolation
- If there is a lot of common code across individual test methods, it should be
  factored out in a helper method within the test class
  - Reduces redundancy and improves maintainability of the test code
  - E.g., a `setUp` method to initialize common test data or configurations
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
  - E.g., "Tests the addition of two positive integers."
  - E.g., "Verifies that an exception is raised when dividing by zero."
- Test methods should have type hint annotations
  - E.g., `def test_addition(self) -> None:`
- Do not create temporary files for tests (e.g., with `tempfile`) but use
  `hunittest.TestCase.get_scratch_space()` instead
- If the input to the test is a large piece of code/text, it should be moved to
  a separate file in the `input` dir corresponding to the test
  - E.g., `outcomes/<TestClassName.test_method_name>/input` and read through the
    function `self.get_input_dir()` of `TestCase`
  - This approach allows for easy updates and modifications to test inputs
    without altering the test code itself
- Do not use pickle files for test inputs
  - Use JSON, YAML, CSV files for test inputs as they are more secure and
    human-readable
- In every test method, separate logically distinct code chunks with comments
  - E.g.,
    ```
    # Prepare inputs
    input_data = [1, 2, 3]
    # Run test
    result = my_function(input_data)
    # Check outputs
    self.assert_equal(result, expected_output)
    ```
- Do not use `hdbg.dassert` in testing but use `self.assert*()` methods
- Prefer `self.assert_equal()` instead of `self.assertEqual()`
  - Always use actual and then expected value
  - E.g., `self.assert_equal(actual, expected)`
- Use strings to compare actual and expected outputs instead of data structures
  - E.g., use `self.assert_equal(str(actual_list), str(expected_list))`
- Use `self.check_string()` to compare the actual output to a golden output in
  the `outcomes` dir, when the output is large or needs to be modified easily
  - E.g., `self.check_string(actual_output)`
- When testing for an assertion, check that you are getting the exact exception
  that is expected
  ```
  # Make sure function raises an error.
  with self.assertRaises(AssertionError) as cm:
      config_list.configs = configs
  act = str(cm.exception)
  self.check_string(act, fuzzy_match=True)
  ```

## Notebooks

### General

- The code in the notebook should adhere to the same style and formatting
  guidelines as the code in libraries and scripts
- Common or general-purpose code should be factored out in functions and moved
  from the notebook to a Python library, which would then be imported in the
  notebook
  - E.g., create a `utils.py` file for helper functions
- Notebook cells should be idempotent, i.e., able to be executed multiple times
  without changing their output value
  - Avoid side effects such as modifying global variables or external states
  - Ensure that cell execution order does not affect the results
- If the data is transformed, display a few lines to show the outcome
  - E.g., `df.head(3)` to preview the first three rows of a DataFrame
- If any data is discarded/filtered, display the percentage of the rows dropped
  - E.g.,
    `print(f"Percentage of rows dropped: {dropped_rows / total_rows * 100:.2f}%")`
  - Provides insight into data cleaning and filtering processes
- Progress bars should be added where applicable
  - Use libraries like `tqdm` to show progress in loops or data processing tasks

### Plotting

- Each plot should have a descriptive title to understand the context of the
  plot at a glance
  - E.g., "Monthly Sales Data for 2023" instead of just "Sales Data"
- Each plot should have axes labels
  - E.g., label the x-axis as "Months" and the y-axis as "Revenue in USD"
- If there are several multiple data series on the same plot, it should have a
  legend
- In a plotting function, `plt.show()` should not be added at the end
  - This allows for further customization or saving of the plot before
    displaying
  - E.g., users might want to save the plot using `plt.savefig('plot.png')`
    before showing it
- In a plotting function, the `ax` parameter should be exposed to allow users to
  customize the plot further
  - E.g., users can modify the axes limits or add additional annotations
- If a function plots multiple plots, they should be generally plotted in a
  single figure
  - E.g., use `plt.subplots()` to create a grid of plots within a single figure

## Markdowns

- Boldface and italics should be used sparingly
- The use of bullet point lists is encouraged
  - For the items, `-` should be used instead of `*` or circles
- Use active voice most of the time and use passive voice sparingly
  - Good: "The user updates the file."
  - Bad: "The file is updated by the user."
- Be efficient
  - Do not explain things in a repetitive way
  - Rewrite long-winded AI-generated texts in a concise way
  - E.g., instead of "The process of updating the software can be done by
    following these steps," use "Update the software by following these steps"

- When describing a tool the format should be the following
  - A description of what the tool does
  - A list of examples of invocations of a tool, with a comment on the command
    line, the command line, and its output if possible
  - A copy-paste version of the tool interface running `-h`
