You are an expert Python developer.

I will pass you a Python file that needs unit tests or ask you to update
existing tests in the helpers repository.

## File structure

- For a source file `helpers/module_name.py`, create a test file at
  `helpers/test/test_module_name.py`

- Use this exact structure:
  ```python
  import logging

  import helpers.hunit_test as hunitest
  # Add other imports as needed

  _LOG = logging.getLogger(__name__)


  # #############################################################################
  # TestClassName1
  # #############################################################################


  class TestClassName1(hunitest.TestCase):
      """
      Brief description of what this test class tests.
      """

      # Test methods here


  # #############################################################################
  # TestClassName2
  # #############################################################################


  class TestClassName2(hunitest.TestCase):
      """
      Brief description of what this test class tests.
      """

      # Test methods here
  ```

## Naming conventions

- Testing a function → Use `Test_<FunctionName>` (with underscore)
  - Example: function `parse_limit_range()` → `class Test_parse_limit_range(hunitest.TestCase):`
  - Example: function `apply_limit_range()` → `class Test_apply_limit_range(hunitest.TestCase):`

- Testing a class → Use `Test<ClassName>` (no underscore)
  - Example: class `Config` → `class TestConfig(hunitest.TestCase):`
  - Example: class `ConfigBuilder` → `class TestConfigBuilder(hunitest.TestCase):`

- Test method names → Choose based on number of tests:
  - If you have < 5 similar tests: use descriptive names
    ```python
    def test_parse_limit_range_valid_input(self) -> None:
    def test_parse_limit_range_no_colon(self) -> None:
    def test_parse_limit_range_invalid_start(self) -> None:
    ```
  - If you have >= 5 similar tests: use numbered names
    ```python
    def test_parse_limit_range1(self) -> None:
    def test_parse_limit_range2(self) -> None:
    def test_parse_limit_range3(self) -> None:
    ```

## Test method structure - Use three sections

- Every test method must have three sections with standard comments:
  ```python
  def test_something(self) -> None:
      """
      Brief description of what this tests.
      """
      # Prepare inputs.
      <setup test data>
      # Run test.
      <call function under test>
      # Check outputs.
      <verify results>
  ```

- For section 1 use:
  - `# Prepare inputs.` (when setting up input data)
  - `# Prepare outputs.` (when setting up expected values)

- For section 2 use:
  - `# Run test.`
  - `# Run.`

- For section 3 use:
  - `# Check output.`
  - `# Check outputs.`

## Use helper methods when you have repetitive tests

- If you write 3+ test methods that call the same function with only different
  input values and expected outputs, create a helper method

- Example:
  ```python
  class TestFunctionName(hunitest.TestCase):
      """Test description."""

      def helper(self, param1: Type1, expected: Type2) -> None:
          """
          Test helper for function_name.

          :param param1: Description of param1
          :param expected: Expected output
          """
          # Run test.
          actual = function_under_test(param1)
          # Check outputs.
          self.assert_equal(str(actual), str(expected))

      def test_case1(self) -> None:
          """
          Test description.
          """
          # Prepare inputs.
          input1 = <value>
          # Prepare outputs.
          expected = <value>
          # Run test.
          self.helper(input1, expected)

      def test_case2(self) -> None:
          """
          Test description.
          """
          # Prepare inputs.
          input1 = <different_value>
          # Prepare outputs.
          expected = <different_value>
          # Run test.
          self.helper(input1, expected)
  ```

## Assertion patterns

- Compare simple values:
  ```python
  # Check outputs.
  self.assert_equal(actual, expected)
  ```

- Compare data structures as strings:
  ```python
  # Check outputs.
  self.assert_equal(str(actual), str(expected))
  ```

- Compare with fuzzy matching (whitespace differences):
  ```python
  # Check outputs.
  self.assert_equal(actual, expected, fuzzy_match=True)
  ```

- Compare with text purification (memory addresses):
  ```python
  # Check outputs.
  self.assert_equal(actual, expected, purify_text=True)
  ```

- Compare with auto-dedent:
  ```python
  # Check outputs.
  expected = """
      line1
      line2
      """
  self.assert_equal(actual, expected, dedent=True)
  ```

## Use golden file testing for large outputs

- When output is > 50 lines or changes frequently:
  ```python
  def test_large_output(self) -> None:
      """Test description."""
      # Prepare inputs.
      input_data = <value>
      # Run test.
      actual = function_under_test(input_data)
      # Check outputs.
      self.check_string(actual)
  ```

- With fuzzy matching:
  ```python
  self.check_string(actual, fuzzy_match=True)
  ```

## Testing exceptions

- Full exception testing with message verification:
  ```python
  def test_raises_error(self) -> None:
      """
      Test that function raises ExceptionType for invalid input.
      """
      # Prepare inputs.
      invalid_input = <value>
      # Run test and check output.
      with self.assertRaises(ExceptionType) as cm:
          function_under_test(invalid_input)
      actual = str(cm.exception)
      expected = """
      Expected error message
      """
      self.assert_equal(actual, expected, fuzzy_match=True)
  ```

- Simplified version when exact message doesn't matter:
  ```python
  def test_raises_error(self) -> None:
      """Test that function raises AssertionError for invalid input."""
      # Prepare inputs.
      invalid_input = <value>
      # Run test and check output.
      with self.assertRaises(AssertionError):
          function_under_test(invalid_input)
  ```

- Check for partial message:
  ```python
  def test_error_message_content(self) -> None:
      """Test that error message contains expected text."""
      # Prepare inputs.
      invalid_input = <value>
      # Run test and check output.
      with self.assertRaises(AssertionError) as cm:
          function_under_test(invalid_input)
      self.assertIn("expected substring", str(cm.exception))
  ```

## Test coverage - What to test

- For each function, generate tests for:
  - Happy path (normal, expected input)
    - `test_<function>_valid_input()`
  - Edge cases (boundary conditions)
    - Empty input: `test_<function>_empty_input()`
    - Zero: `test_<function>_zero()`
    - Single item: `test_<function>_single_item()`
    - Large input: `test_<function>_large_input()`
  - Error conditions (invalid input)
    - None: `test_<function>_none_raises_error()`
    - Wrong type: `test_<function>_invalid_type_raises_error()`
    - Invalid value: `test_<function>_invalid_value_raises_error()`

## Input data patterns

- Use multiline text (preferred):
  ```python
  # Prepare inputs.
  text = """
  line1
  line2
  line3
  """
  text = hprint.dedent(text)
  ```

- Use list input:
  ```python
  # Prepare inputs.
  items = ["a", "b", "c"]
  ```

- Use scratch space for file testing:
  ```python
  # Prepare inputs.
  scratch_dir = self.get_scratch_space()
  test_file = os.path.join(scratch_dir, "test.txt")
  hio.to_file(test_file, "content")
  ```

- Use input directory for large test data:
  ```python
  # Prepare inputs.
  input_file = os.path.join(self.get_input_dir(), "test_data.json")
  data = hio.from_json(input_file)
  ```

## Setup and teardown

- Use when multiple test methods need the same setup/teardown code:
  ```python
  class TestClassName(hunitest.TestCase):
      """Test description."""

      @pytest.fixture(autouse=True)
      def setup_teardown_test(self):
          """Setup and teardown for each test."""
          # Run before each test.
          self.set_up_test()
          yield
          # Run after each test.
          self.tear_down_test()

      def set_up_test(self) -> None:
          """Setup code that runs before each test."""
          self.test_data = <initialize>

      def tear_down_test(self) -> None:
          """Cleanup code that runs after each test."""
          <cleanup>

      def test_method1(self) -> None:
          """Test description."""
          # Use self.test_data here
  ```
