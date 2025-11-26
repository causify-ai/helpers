## Coding conventions
- Test methods should have type hint annotations
  - E.g., `def test_addition(self) -> None:`
- To write unit test follow the template `docs/ai_coding/unit_test_template.py`

## Imports and logging
- Always import `logging` at the top
- Always define a logger constant after imports:
  ```python
  _LOG = logging.getLogger(__name__)
  ```
- Import testing utilities:
  ```python
  import helpers.hunit_test as hunitest
  import helpers.hprint as hprint
  ```

## Test class separators
- Separate test classes with a separator comment:
  ```python
  # #############################################################################
  # Test_function_name1
  # #############################################################################


  class Test_function_name1(hunitest.TestCase):
      ...
  ```

## Naming files
- For a file `XYZ.py` add a file `test/test_XYZ.py`
  - E.g., for `helpers/hdbg.py` its test code is `helpers/test/test_hdbg.py`

## Test class / method
- Each tested function has a different test class
- Each test case corresponds to a single test method
  - E.g., "for these inputs the function responds with this output"
- For each tested function add enough unit tests to cover average and corner
  cases
- Each test method should have a docstring describing briefly what case is being
  tested
  - E.g., "Tests the addition of two positive integers."
  - E.g., "Verifies that an exception is raised when dividing by zero."

- Each unit test should be independent of all the other unit tests
  - Ensures that tests do not affect each other and can be run in isolation

## Naming tests
- Adhere to the following conventions for naming:
  - Class `TestFooBar` tests the class `FooBar` and its methods
    - `TestFooBar.test_method_a`, `TestFooBar.test_method_b` test the methods
      `FooBar.method_a` and `FooBar.method_b`
  - Class `Test_foo_bar` tests the function `foo_bar()`
    - E.g., `Test_foo_bar.test_valid_input`, `Test_foo_bar.test_invalid_input`
      for different cases / inputs
  - `Test_foo_bar.test1`, `Test_foo_bar.test2` for different cases / inputs

## Factor out common code
- When testing the same function with multiple inputs, use a helper method to
  reduce code duplication
- Helper methods should have descriptive docstrings explaining their purpose
- Helper methods typically take test inputs and expected outputs as parameters
- Call helper methods using `self.helper(...)` in test methods

- Bad
  ```
  class Test_remove_empty_lines(hunitest.TestCase):
      def test_empty_list(self) -> None:
          """
          Test with an empty list.
          """
          # Prepare inputs.
          lines = []
          # Run test.
          actual = function_under_test(lines)
          # Check outputs.
          expected = []
          self.assert_equal(str(actual), str(expected))

      def test_no_empty_lines(self) -> None:
          """
          Test with no empty lines in the input.
          """
          # Prepare inputs.
          lines = """
          line1
          line2
          line3
          """
          lines = hprint.dedent(lines)
          lines = lines.split("\n")
          # Run test.
          actual = function_under_test(lines)
          # Check outputs.
          expected = ["line1", "line2", "line3"]
          self.assert_equal(str(actual), str(expected))
  ```

- Good:
  ```
  class Test_remove_empty_lines(hunitest.TestCase):
      def helper(self, in_lines: List[str], expected: List[str]) -> None:
          """
          Test helper for remove_empty_lines function.

          :param in_lines: Input lines to test
          :param expected: Expected output lines
          """
          # Run test.
          actual = function_under_test(in_lines)
          # Check outputs.
          self.assert_equal(str(actual), str(expected))

      def test_empty_list(self) -> None:
          """
          Test with an empty list.
          """
          # Prepare inputs.
          lines = []
          # Prepare outputs.
          expected = []
          # Run test.
          self.helper(lines, expected)

      def test_no_empty_lines(self) -> None:
          """
          Test with no empty lines in the input.
          """
          # Prepare inputs.
          lines = """
          line1
          line2
          line3
          """
          lines = hprint.dedent(lines)
          lines = lines.split("\n")
          # Prepare outputs.
          expected = ["line1", "line2", "line3"]
          # Run test.
          self.helper(lines, expected)
  ```

## Inputs
- Prefer to use inputs and outputs as chunks of texts like
  ```
  input = """
  hello
  world
  """
  input_txt = hprint.dedent(input_txt)
  ```
  instead of 
  ```
  input = ["hello", "world"]
  ```

- Do not use mock

- Do not test external library functions but focus on the logic specific of the
  code

- Do not test scripts calling it with a `systemn()`, but test the script
  end-to-end calling it as functions

## Use set_up_test() / tear_down_test(), when possible
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

- Do not create temporary files for tests (e.g., with `tempfile`) but use
  `hunittest.TestCase.get_scratch_space()` instead

## Large input files
- If the input to the test is a large piece of code/text, it should be moved to
  a separate file in the `input` dir corresponding to the test
  - E.g., `outcomes/<TestClassName.test_method_name>/input` and read through the
    function `self.get_input_dir()` of `TestCase`
  - This approach allows for easy updates and modifications to test inputs
    without altering the test code itself
- Do not use pickle files for test inputs
  - Use JSON, YAML, CSV files for test inputs as they are more secure and
    human-readable

## Test structure
- In every test method separate logically distinct code chunks using standard
  comments:
  - `# Prepare inputs.` - Set up test data and parameters
  - `# Run test.` or `# Run.` or `# Evaluate the function.` - Execute the code
    under test
  - `# Check outputs.` or `# Check.` or `# Check output.` - Verify results
  - Example:
    ```python
    def test_addition(self) -> None:
        """
        Test addition of two positive integers.
        """
        # Prepare inputs.
        input_data = [1, 2, 3]
        # Run test.
        result = my_function(input_data)
        # Check outputs.
        expected_output = 6
        self.assert_equal(result, expected_output)
    ```

## Check output
- Do not use `hdbg.dassert` in testing but use `self.assert*()` methods
- Prefer `self.assert_equal()` instead of `self.assertEqual()`
  - Always use actual and then expected value
  - E.g., `self.assert_equal(actual, expected)`
  - Use `fuzzy_match=True` when comparing strings that may have whitespace
    differences or non-deterministic formatting
    - E.g., `self.assert_equal(actual, expected, fuzzy_match=True)`
  - Use `purify_text=True` when comparing strings with object references (like
    memory addresses) that need to be normalized
    - E.g., `self.assert_equal(actual, expected, purify_text=True)`
  - Use `dedent=True` to automatically dedent multiline strings before
    comparison
    - E.g., `self.assert_equal(actual, expected, dedent=True)`
- Use strings to compare actual and expected outputs instead of data structures
  - E.g., use `self.assert_equal(str(actual_list), str(expected_list))`
- Use `self.check_string()` to compare the actual output to a golden output in
  the `outcomes` dir, when the output is large or needs to be modified easily
  - E.g., `self.check_string(actual_output)`
  - Can also use `fuzzy_match=True` parameter with `check_string()`
    - E.g., `self.check_string(actual_output, fuzzy_match=True)`

## Testing assertions
- When testing for an assertion, check that you are getting the exact exception
  that is expected
- Use the `with self.assertRaises()` context manager pattern
- Extract the exception message using `str(cm.exception)`
- Verify the exception message using `self.check_string()` or
  `self.assert_equal()`
- Example:
  ```python
  def test_invalid_input_raises_error(self) -> None:
      """
      Test that function raises AssertionError for invalid input.
      """
      with self.assertRaises(AssertionError) as cm:
          my_function(invalid_input)
      actual = str(cm.exception)
      expected = """
      * Failed assertion *
      Invalid input
      """
      self.assert_equal(actual, expected, fuzzy_match=True)
  ```
- Alternatively, use `self.check_string()` for larger exception messages:
  ```python
  with self.assertRaises(AssertionError) as cm:
      config_list.configs = configs
  actual = str(cm.exception)
  self.check_string(actual, fuzzy_match=True)
  ```

## Test with pytest
- Make sure that all the unit tests pass by running pytest
