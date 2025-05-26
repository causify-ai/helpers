# Guidelines for automated PR reviews

## Python code

### Naming

- Name functions using verbs and verbs/actions
  - E.g., `download_data()`, `process_input()`, `calculate_sum()`
  - Python internal functions as `__repr__`, `__init__` are valid
  - Functions names like `to_dict()`, `_parse()`, `_main()`  are valid
- Name classes using nouns
  - E.g., `Downloader()`, `DataProcessor()`, `User()`
- Name decorators with an adjective or a past tense verb
  - E.g., `timed`, `cached`, `logged`
- Variable and function names should not reference implementation details, and
  things that can change or details that are not important
  - E.g., the name of a variable should not include its type
    - E.g., use `embeddings` instead of `embeddings_list`
    - E.g., use `data` instead of `data_dict`
- Abbreviations in the names of variables and functions should be avoided, except
  for the following
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
  - E.g., if using a library named `math`, avoid naming a function
    `math_calculate()`
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
  - The text should describe the goal of the function, the interface and what the user
    needs to know to use the function
    - E.g., "This function calculates the sum of two numbers and returns the
      result."
  - The text should not describe parameters / what is being returned
  - The text should not describe implementation details that can be changed
- The more detailed description is followed by a blank line and then the param
  and return description section in REST style
  - Use lowercase after `:param XYZ: ...` / `:return:` unless the description
    starts with a proper noun
  - Do not add a period at the end of the param and return descriptions
  - Do not mention the type of the parameters and return structures
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
  - E.g.,
    ```
    # Example usage:
    result = add_numbers(3, 5)
    # result is 8
    ```
- References to variables, file paths, functions, classes, etc. should be
  wrapped in backticks
  - E.g., "The `add_numbers` function takes two arguments."
- Multi-line representations of data structures (e.g., an output example) should
  be wrapped in triple backticks
  - E.g.,
    ```
    { "name": "John", "age": 30, "city": "New York" }
    ```

### Comments

- Add a comment for every logically distinct chunk of code
- Use comments to separate chunks of code instead of blank lines
- Do not use inline comments; every comment should be on its own separate line,
  before the line it refers to
  - In `if-elif-else` statements, the comments are placed underneath each
    statement in order to explain the code that belongs to each statement in
    particular
    ```python
    if ...:
      # Do this.
    else:
      # Do that.
    ```
- Avoid mentioning concrete names of variables, functions, classes, files, etc.
  in the comments
  - If it is unavoidable, wrap their names in backticks
- Avoid referring to the type of a variable in the comments
  - Keeps comments focused on functionality rather than implementation specifics
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
  - E.g., `hdbg.dassert_lt(start_date, end_date)`
  - Ensure that assertions provide detailed information for debugging
  - Use assertions to validate input parameters and preconditions
- Do not use f-strings in `hdbg.dassert()`, but use traditional string formatting
  methods in assertions
  - E.g.,
    `hdbg.dassert_eq(len(list1), len(list2), "Lists must be of equal length: %d vs %d" % (len(list1), len(list2)))`
- Use f-strings in exceptions
  - E.g., `raise ValueError(f"Invalid server_name='{server_name}'")`
  - Provide clear and informative error messages using f-strings
  - E.g., `raise TypeError(f"Expected type int, but got {type(var).__name__}")`
- Use complete `if-elif-else` statements instead of a sequence of `if`
  statements
  - Ensure logical flow and clarity in conditional statements
  - E.g.,
    ```python
    if condition1:
      # Execute block for condition1.
    elif condition2:
      # Execute block for condition2.
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
- Use `isinstance()` instead of `type()` to check the type of an object

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
    - E.g., `read_csv()`, `load_json()`
  - Process data
    - E.g., `clean_data()`, `transform_data()`
  - Save data
    - E.g., `write_csv()`, `export_json()`
- Ensure that function names are descriptive and convey their purpose
- Use comments to explain complex logic or calculations
- Implement error handling to manage exceptions and edge cases
- Use inheritance or composition to reuse code in object-oriented programming

### Type annotations

- For type hints use use `List`, `Dict`, and `Tuple` to provide more explicit type information
  and help with static type checking
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
  the returned value should not change (in contrast to functions that
  rely upon external state)
- Functions should not modify the function inputs
  - E.g., if a function `f()` accepts a dataframe `df` as its argument, then
    `f()` will not modify `df` but make a copy and work on it
  - This ensures that the original data remains unchanged and can be reused
- The preferred order of parameters in a function declaration is:
  - Input parameters
  - Output parameters
  - In-out parameters
  - Default parameters
  - This order helps in maintaining clarity and consistency in function
    definitions
- Default parameters should be used sparingly and only for parameters that 99%
  of the time are constant
- All the default parameters should be keyword-only
  - They should be separated from the other parameters by `*`
  - This ensures that default parameters are always explicitly specified by
    name, improving readability
- Do not use mutable objects (such as lists, maps, objects) as default value for
  functions; instead, pass `None` and then initialize the default parameter
  inside the function
  - E.g., instead of using a list as a default parameter, use `None` and
    initialize the list inside the function:
    ```
    def add_item(item: str, *, items: Optional[List[str]]) -> List[str]:
      if items is None:
        items = []
      items.append(item)
      return items
    ```

- Use a default value of `None` when a function needs to be wrapped and the
  default parameter needs to be propagated
- Do not use a boolean parameter as a switch controlling some function behavior;
  instead, use a string parameter `mode`, which is allowed to take a small
  well-defined set of values
  - E.g., `def process_data(mode='fast'):` where `mode` can be `'fast'`,
    `'slow'`, etc
- For functions dealing with dataframes, avoid hard-wired column name
  dependencies; instead, allow the caller to pass the column name to the
  function as a parameter
  - E.g., `def calculate_average(df: pd.DataFrame, column_name: str):`
- Do not put computations of the output in the `return` line
  - Instead, compute the output first, assign it to a variable, and then return
    this variable
  - E.g.,
    ```
    result = compute_value()
    return result
    ```
- A function should have a single exit point, i.e., one single line with
  `return`
- A function should ideally return objects of only one type (or `None`)
- When calling a function, assign all the input parameter values to variables on
  separate lines and then pass these variables to the function
  - E.g.,
    ```
    param1 = value1
    param2 = value2
    result = my_function(param1, param2)
    ```
- Explicitly bind default parameters, i.e., specify the parameter name when
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

- Each plot should have a descriptive title to understand the context of the plot
  at a glance
  - E.g., "Monthly Sales Data for 2023" instead of just "Sales Data"
- Each plot should have axes labels
  - E.g., label the x-axis as "Months" and the y-axis as "Revenue in USD"
- If there are several multiple data series on the same plot, it should have a legend
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
  - Items in bullet point lists should not end with a period
- Wrap file paths, names of variables, functions, and classes in backticks
  - E.g., `file_path`, `variable_name`, `function_name()`, `ClassName`
- Use `>` to indicate a command line
  - E.g., `> git push` or `docker> pytest`
- Avoid using screenshots whenever possible and instead copy-and-paste text with
  the right highlighting
  - E.g., instead of a screenshot of a terminal command, provide the command
    text: `> ls -la`
- Use active voice most of the time and use passive voice sparingly
  - E.g., "The user updates the file" instead of "The file is updated by the
    user"
- Be efficient
  - Do not explain things in a repetitive way
  - Rewrite long-winded AI-generated texts in a concise way
  - E.g., instead of "The process of updating the software can be done by
    following these steps," use "Update the software by following these steps"
