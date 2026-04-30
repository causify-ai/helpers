- This file contains all the conventions and rules to write unit tests

# Test Coverage

## What to Test

- For each function, generate tests for:
  - Happy path (normal, expected input)
  - Edge cases (boundary conditions)
    - E.g., empty input, zero, single item, large input
  - Do not test heavily error conditions (e.g., invalid input)

# File and Test Structure

## File Structure

- For a source file `<module_name>.py`, the corresponding test file is
  `test/test_<module_name>.py`

## Unit Test Code Structure

- Always derive testing classes from `hunitest.TestCase`

- Use this exact structure:

  ```python
  import logging

  import helpers.hunit_test as hunitest
  # Add other imports as needed

  _LOG = logging.getLogger(__name__)


  class TestClassName1(hunitest.TestCase):
      """
      Brief description of what this test class tests.
      """

      # Test methods here


  class TestClassName2(hunitest.TestCase):
      """
      Brief description of what this test class tests.
      """

      # Test methods here
  ```

## Consolidate Inputs and Outputs

- Organize input variables in a consecutive block and organize output variables
  in a consecutive block
  - **Bad** (the input and output dirs are mixed)
    ```
    # Create input and output directories.
    input_dir = self_.get_input_dir()
    output_dir = self_.get_output_dir()
    hio.create_dir(output_dir, incremental=True)
    # Create input file with test content.
    input_file = os.path.join(input_dir, f"test.{input_ext}")
    input_content = hprint.dedent(input_content)
    hio.to_file(input_file, input_content)
    _LOG.debug("Created input file: %s", input_file)
    # Create output file path.
    output_file = os.path.join(output_dir, f"test_output.{output_ext}")
    ```
  - **Good**
    ```
    # Create inputs.
    input_dir = self_.get_input_dir()
    output_dir = self_.get_output_dir()
    input_file = os.path.join(input_dir, f"test.{input_ext}")
    input_content = hprint.dedent(input_content)
    hio.to_file(input_file, input_content)
    _LOG.debug("Created input file: %s", input_file)
    # Create outputs.
    hio.create_dir(output_dir, incremental=True)
    output_file = os.path.join(output_dir, f"test_output.{output_ext}")
    ```

## Assign Variables and Then Call Functions

- Don't just pass data to a function directly, but explain the data first
  by assigning each value to a variable, and then pass the variables to the
  function
  - **Bad**
    ```python
    # Run test.
    self.helper(".tex", "figs/diagram.png", "...", "fig:test_diagram",
    "fig:test_diagram", "Test diagram showing communication")
    ```

  - **Good**
    ```python
    # Prepare inputs.
    extension = ".tex"
    rel_img_path = "figs/diagram.png"
    user_img_size = ""
    label = "fig:test_diagram"
    caption = "Test diagram showing communication"
    # Prepare outputs.
    expected = r"""
    ...
    """
    # Run test.
    self.helper(extension, rel_img_path, user_img_size, expected, label, caption)
    ```

# Naming Conventions

## Naming Conventions for a Function

- For testing a function `<FunctionName>` use `Test_<FunctionName>` (separated by
  underscore since the function name starts with lower case), e.g.,
  - `parse_limit_range()` -> `class Test_parse_limit_range(hunitest.TestCase):`
  - `apply_limit_range()` -> `class Test_apply_limit_range(hunitest.TestCase):`

## Naming Conventions for a Class

- For testing a class `<ClassName>` use `Test<ClassName>` (no underscore since
  the class name starts with capital case), e.g.,
  - `Config` -> `class TestConfig(hunitest.TestCase):`
  - `ConfigBuilder` -> `class TestConfigBuilder(hunitest.TestCase):`

## Test Method Names

- For test method names always number the method tests, as `test1`, `test2`
  since the explanation of what they do is in the docstring
  - **Good**
    - `test1`
    - `test2`
  - **Bad**
    - `test_preserve_yaml_frontmatter`
    - `test_page_separator_removal_with_frontmatter`

## Code Formatting in Tests

### Align Strings to the Code

- Align multi-line strings with the indentation of surrounding code:
  - **Bad**: String starts at column 0
    ```python
    def hello(self) -> None:
        content = """<start:file1.txt>
    Content for file1
    <start:file2.txt>
    Content for file2
    """
    ```
  - **Good**: String is indented and dedented in code
    ```python
    def hello(self) -> None:
        content = """
        <start:file1.txt>
        Content for file1
        <start:file2.txt>
        Content for file2
        """
        content = hprint.dedent(content)
    ```

## Avoid Replicated Assignment

- If a variable `var` and `expected` need to always be the same (e.g., to show
  that a variable doesn't change), instead of replicating the assignment, assign
  `expected = var`:
  - **Bad**: Duplicated text
    ```python
    def test2(self) -> None:
        """
        Test indented code block with correct indentation.
        """
        # Prepare inputs.
        txt = """
        - Delete unused reference files
          ```bash
          > rm Dockerfile.ubuntu
          ```
        """
        # Expected: no changes needed.
        expected = """
        - Delete unused reference files
          ```bash
          > rm Dockerfile.ubuntu
          ```
        """
        # Run test.
        self.helper(txt, expected)
    ```
  - **Good**: Assign expected from txt
    ```python
    def test2(self) -> None:
        """
        Test indented code block with correct indentation.
        """
        # Prepare inputs.
        txt = """
        - Delete unused reference files
          ```bash
          > rm Dockerfile.ubuntu
          ```
        """
        # Expected: no changes needed.
        expected = txt
        # Run test.
        self.helper(txt, expected)
    ```

# Test Method Conventions

## Use Three Sections in Testing Methods

- Every test method must have three sections with standard comments:
  - `# Prepare inputs.`: Input data setup
  - `# Prepare outputs.`: Expected output setup
  - `# Run test.`: Test execution
  - `# Check outputs.`: Result verification

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

- You must preserve test structure comments that organize test logic into
  sections
  - These comments provide consistent structure for unit tests and improve
    readability
  - **Good**: (test structure is clear)
    ```python
    def test1(self) -> None:
        """
        Test extraction from valid file path.
        """
        # Prepare inputs.
        file_path = "msml610/lectures_source/Lesson10-Name.md"
        # Prepare outputs.
        expected_dir = "msml610"
        expected_lesson = "10"
        # Run test.
        actual_dir, actual_lesson = _extract_lesson_from_file(file_path)
        # Check outputs.
        self.assertEqual(actual_dir, expected_dir)
        self.assertEqual(actual_lesson, expected_lesson)
    ```

## Use Helper Methods When You Have Repetitive Tests

- If you write two or more test methods that call the same function with only
  different input values and expected outputs, create a helper method
  - **Good** (`test1` and `test2` share code in `helper`)
    ```python
    class TestFunctionName(hunitest.TestCase):
        """
        Test description.
        """

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

        def test1(self) -> None:
            """
            Test description.
            """
            # Prepare inputs.
            input1 = <value>
            # Prepare outputs.
            expected = <value>
            # Run test.
            self.helper(input1, expected)

        def test2(self) -> None:
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

## Assertion Patterns

- Use `self.assertEqual()` to compare simple values (e.g., floats, ints)
  ```python
  # Check outputs.
  self.assertEqual(actual, expected)
  ```

- Use `self.assert_equal()` when the arguments are strings

- Compare data structures `XYZ` (e.g., lists, dicts) as strings:
  ```python
  # Check outputs.
  self.assert_equal(str(actual), str(expected))
  ```

- Compare with fuzzy matching which ignores whitespace differences when needed:
  ```python
  # Check outputs.
  self.assert_equal(actual, expected, fuzzy_match=True)
  ```

- Compare with text purification to remove implementation details (e.g., memory
  addresses, paths, usernames, timestamps, and other machine/environment-specific
  details that would cause test failures when run on different systems)
  ```python
  # Check outputs.
  self.assert_equal(actual, expected, purify_text=True)
  ```

- Compare strings with auto-dedent:
  ```python
  # Check outputs.
  expected = """
      line1
      line2
      """
  self.assert_equal(actual, expected, dedent=True)
  ```

## Testing Exceptions

- Full exception testing with message verification:
  ```python
  def test1(self) -> None:
      """
      Test that function raises `ExceptionType` for invalid input.
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
  def test2(self) -> None:
      """
      Test that function raises `AssertionError` for invalid input.
      """
      # Prepare inputs.
      invalid_input = <value>
      # Run test and check output.
      with self.assertRaises(AssertionError):
          function_under_test(invalid_input)
  ```

- Check for partial message:
  ```python
  def test3(self) -> None:
      """
      Test that error message contains expected text.
      """
      # Prepare inputs.
      invalid_input = <value>
      # Run test and check output.
      with self.assertRaises(AssertionError) as cm:
          function_under_test(invalid_input)
      self.assertIn("expected substring", str(cm.exception))
  ```

## Use Golden File Testing for Large Outputs

- Always use `self.assert_equal()` to do a comparison of actual with the expected
  value hard wired in the code
- The only exception is when output is large (e.g., longer than 20 lines) or
  changes frequently use `self.check_string()` instead of `self.assert_equal`
  - E.g.,
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

## Input Data Patterns

- Always use multiline text aligned to the variable of the string and then call
  `hpring.dedent()` or use `self.assert_equal(actual, expected, dedent=True)`
  - **Good**
    ```python
    # Prepare inputs.
    text = """
    line1
    line2
    line3
    """
    text = hprint.dedent(text)
    ```
  - **Bad**
    ```python
    # Prepare inputs.
    text = """
line1
line2
line3
    """
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

## Setup and Teardown

- Use this idiom when multiple test methods need the same setup/teardown code:
  ```python
  class TestClassName(hunitest.TestCase):
      """
      Test description.
      """

      @pytest.fixture(autouse=True)
      def setup_teardown_test(self):
          """
          Setup and teardown for each test.
          """
          # Run before each test.
          self.set_up_test()
          yield
          # Run after each test.
          self.tear_down_test()

      def set_up_test(self) -> None:
          """
          Setup code that runs before each test.
          """
          self.test_data = <initialize>

      def tear_down_test(self) -> None:
          """
          Cleanup code that runs after each test.
          """
          <cleanup>

      def test_method1(self) -> None:
          """
          Test description.i
          """
          # Use self.test_data here.
  ```
