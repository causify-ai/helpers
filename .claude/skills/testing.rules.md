- This file contains all the conventions and rules to write unit tests

# Test Design

## Test One Thing
- A test class tests only one function or class; a test method tests only one
  case
- Keeps failures easy to diagnose: one thing broken means one test fails

## Keep Tests Self-Contained
- Each test must be independent and never assume execution order
- Specify input data explicitly inside the test; do not rely on shared state

## Test From the Outside-In
- Start with public-facing behavior before internal helpers
- Interface-level tests survive refactors; implementation-level tests do not

## Keep Testing Code in Sync with Tested Code
- When renaming a tested class or file, rename the test class and test file

# Test Coverage

## What to Test
- For each function, generate tests for:
  - Happy path (normal, expected input)
  - Edge cases (boundary conditions)
    - E.g., empty input, zero, single item, large input

## What not to Test
- Do not test heavily error conditions (e.g., invalid input and assertion)

# File and Test Structure

## File Structure
- For a source file `<module_name>.py`, the corresponding test file is
  `test/test_<module_name>.py`

## Directory Structure
- Golden files: `test/outcomes/<TestClass.test_method>/output/test.txt`
- Ephemeral scratch: `test/scratch/<TestClass.test_method>/`
  - It is automatically deleted by `hunitest.TestCase.tearDown()`
  - Do not delete it explicitly in test code

## Directory Helpers
- All path helpers are methods on `hunitest.TestCase`
- Paths are scoped to the running class and method automatically

  | Method                 | Returns                                                          |
  | ---------------------- | ---------------------------------------------------------------- |
  | `get_input_dir()`      | Local path for static fixtures checked into git                  |
  | `get_output_dir()`     | Local path for golden files (managed by `check_string`)          |
  | `get_scratch_space()`  | Local ephemeral dir, auto-deleted after the test by `tearDown()` |
  | `get_s3_scratch_dir()` | S3 path for large temporary data, unique per user/server/test    |
  | `get_s3_input_dir()`   | S3 path for fixtures too large to commit to git                  |

## Use Text Files, Not Pickle
- Use human readable files (e.g., CSV, JSOn, plain input files) over pickle
  - Pickle is not stable across library versions and not human-readable
- Document how generated test data was produced

## Keep Test Data Small
- Use the smallest dataset that exercises the case

## Unit Test Code Structure

- Always derive testing classes from `hunitest.TestCase`

- Use the code from `.claude/templates/testing.template.py` as reference
- Use this exact structure for a unit test
  ```python
  import logging

  import helpers.hunit_test as hunitest
  # Add other imports as needed

  _LOG = logging.getLogger(__name__)


  class TestClassName1(hunitest.TestCase):
      """
      Brief description of what this test class tests.
      """

      # Test methods here.
      def test1(self): ...

      def test2(self): ...


  class TestClassName2(hunitest.TestCase):
      """
      Brief description of what this test class tests.
      """

      # Test methods here.
      def test1(self): ...

      def test2(self): ...
  ```

## Consolidate Inputs and Outputs

- Organize input variables in a consecutive code block and then organize output
  variables in a consecutive code block
  - **Bad** (the input and output dirs are mixed)
    ```python
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
  - **Good** (first code related to inputs and then code related to output)
    ```python
    # Create inputs.
    input_dir = self_.get_input_dir()
    input_file = os.path.join(input_dir, f"test.{input_ext}")
    input_content = hprint.dedent(input_content)
    hio.to_file(input_file, input_content)
    _LOG.debug("Created input file: %s", input_file)
    # Create outputs.
    output_dir = self_.get_output_dir()
    hio.create_dir(output_dir, incremental=True)
    output_file = os.path.join(output_dir, f"test_output.{output_ext}")
    ```

## Assign Variables and Then Call Functions

- Don't pass hard-coded parameters to a function, but assign each value to a
  variable, and then pass the variables to the function
  - **Bad**
    ```python
    # Run test.
    self.helper(".tex", None, 5)
    ```
  - **Good**
    ```python
    # Prepare inputs.
    extension = ".tex"
    rel_img_path = None
    label = 5
    # Run test.
    self.helper(extension, rel_img_path, user_img_size)
    ```

## Respect Positional Function Parameters

- Do not redundantly pass required positional parameters as keywords, but
	prefer positional invocation for required parameters

- Example
  - Given a called function that looks like:
    ```python
    def helper(
        self,
        args: List[str],
        expected_cmd: Optional[str],
        expected_exit_code: Optional[int],
        *,
        side_effect: Optional[Type[Exception]] = None,
    ) -> None:
    ```
  - **Bad**
    ```python
    self.helper(
      args,
      expected_cmd=expected_cmd,
      expected_exit_code=expected_exit_code,
    )
    ```
  - **Good**
    ```python
    expected_cmd = ...
    expected_exit_code = ...
    self.helper(
      args,
      expected_cmd,
      expected_exit_code
    )
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
  - **Bad**
    - `test_preserve_yaml_frontmatter`
    - `test_page_separator_removal_with_frontmatter`
  - **Good**
    - `test1`
    - `test2`

# Code Formatting in Tests

## Dedent Strings to the Code

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
  - **Good**: String is indented to the variable and then
    `hprint.dedent(content)`
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
          > rm Dockerfile.ubuntu
        """
        # Expected: no changes needed.
        expected = """
        - Delete unused reference files
          > rm Dockerfile.ubuntu
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
          > rm Dockerfile.ubuntu
        """
        # Expected: no changes needed.
        expected = txt
        # Run test.
        self.helper(txt, expected)
    ```

# Test Method Conventions

## Use Three Sections in Testing Methods

- Every test method must have three sections with standard comments:
  - `# Prepare inputs.`: Input data
  - `# Prepare outputs.`: Expected output
  - `# Run test.`: Test execution
  - `# Check outputs.`: Result verification

  ```python
  def test_something(self) -> None:
      """
      Brief description of what this tests.
      """
      # Prepare inputs.
      <setup input test data>
      # Prepare outputs.
      <setup output test data>
      # Run test.
      <call function under test>
      # Check outputs.
      <verify results>
  ```

- You must preserve test structure comments that organize test logic into
  sections to provide consistent structure for unit tests and improve readability
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

## Use Input and Scratch Space from `hunittest`

- When the inputs are too big (e.g., more than 2000 characters) use a file in
  the input directory:
  ```python
  # Prepare inputs.
  input_file = os.path.join(self.get_input_dir(), "test_data.json")
  data = hio.from_json(input_file)
  ```

- When the unit test needs some intermediate file, use the scratch space:
  ```python
  # Prepare inputs.
  scratch_dir = self.get_scratch_space()
  test_file = os.path.join(scratch_dir, "test.txt")
  hio.to_file(test_file, "content")
  ```

## Setup and Teardown

- Use `set_up_test()` and `tear_down_test()` via `@pytest.fixture(autouse=True)`
  for per-method setup
  - Never override `setUp()` / `tearDown()` directly
- For inherited test classes that both need setup, add a numeric suffix:
  - Parent: `set_up_test()`, `tear_down_test()`
  - Child: `set_up_test2()`, `tear_down_test2()`, which must call parent hooks
  - Next level: `set_up_test3()`, etc.
- Use `setUpClass` and `tearDownClass` only for expensive one-time class-scoped
  setup (DB connection, shared file) and decorate with `@classmethod`
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
          Test description.
          """
          # Use self.test_data here.
  ```

# Format Test Inputs

## String Formatting for Assertions

- Use multi-line strings with `hprint.dedent()` for values instead of escaped
  newline strings to improve readability:
  - **Bad**: (Escaped newlines)
    ```python
    text = "# Chapter 1\n\n## Section 1.1\nContent 1.1\n## Section 1.2\nContent 1.2"
    ```
  - **Good**: (Use multi-line strings, since they are human-readable)
    ```python
    text = """
    # Chapter 1

    ## Section 1.1
    Content 1.1
    ## Section 1.2
    Content 1.2
    """
    text = hprint.dedent(text)
    ```

## Input Data Patterns

- Always use multiline text aligned to the variable of the string and then call
  `hpring.dedent()` or use `self.assert_equal(actual, expected, dedent=True)`
  - **Bad** (the text is not aligned to the variable)
    ```python
    # Prepare inputs.
    text = """
line1
line2
line3
    """
    ```
  - **Good** (the text is aligned to the variable and then dedent-ed)
    ```python
    # Prepare inputs.
    text = """
    line1
    line2
    line3
    """
    text = hprint.dedent(text)
    ```

# Checking Test Outputs

## Use an Expected Output

- Do not use assertion to check each part of the output, but convert the output
  in a human-readable representation (e.g., with `pprint.pformat`) and then
  compare it to a string representing the expected value

  - **Bad** (check each component of the actual output to its expected value)
    ```python
    actual = ...
    # Check outputs.
    self.assertEqual(
        actual["repo_info"]["repo_name"],
        expected_repo_name,
    )
    self.assertEqual(
        actual["docker_info"]["docker_image_name"],
        expected_docker_image,
    )
    self.assertEqual(
        actual["s3_bucket_info"]["unit_test_bucket_name"],
        expected_bucket_name,
    )
    self.assertEqual(
        actual["container_registry_info"]["ecr"],
        expected_ecr,
    )
    self.assertFalse(
        actual["runnable_dir_info"]["use_helpers_as_nested_module"]
    )
    ```
  - **Good** (convert the actual output into a string and then compare it to the
    expected value)
    ```python
    actual = pprint.pfromat(actual)
    expected = """
    {
      "repo_info": {
          "repo_name": expected_repo_name,
      },
      "docker_info": {
          "docker_image_name": expected_docker_image,
      },
      "s3_bucket_info": {
          "unit_test_bucket_name": expected_bucket_name,
      },
      "container_registry_info": {
          "ecr": expected_ecr,
      },
      "runnable_dir_info": {
          "use_helpers_as_nested_module": False,
      },
    }
    """
    self.assert_equal(actual, expected, dedent=True)
    ```

## Assertion Patterns

- Use `self.assertEqual()` to compare simple values (e.g., floats, ints)
  ```python
  # Check outputs.
  self.assertEqual(actual, expected)
  ```

- Always Use `self.assert_equal()` when the arguments are strings

- Compare data structures `XYZ` (e.g., lists, dicts) as strings with
  `self.assert_equal()`
  ```python
  # Check outputs.
  self.assert_equal(str(actual), str(expected))
  ```

- Compare with fuzzy matching `self.assert_equal(..., fuzzy_match=True)` which
  ignores whitespace differences when needed:
  ```python
  # Check outputs.
  self.assert_equal(actual, expected, fuzzy_match=True)
  ```

- Compare with text purification `self.assert_equal(..., purify_text=True)` to
  remove implementation details (e.g., memory addresses, paths, usernames,
  timestamps, and other machine/environment-specific details that would cause
  test failures when run on different systems)
  ```python
  # Check outputs.
  self.assert_equal(actual, expected, purify_text=True)
  ```

- Compare strings with `self.assert_equal()`
  ```python
  # Check outputs.
  expected = """
  line1
  line2
  """
  self.assert_equal(actual, expected, dedent=True)
  ```

- Do not use `hdbg.dassert` since it guards production invariants and is not a
  substitute for test assertions
  - Always use `self.assert*` family instead

## Testing Exceptions

- Full exception testing with message verification:
  ```python
  def test1(self) -> None:
      """
      Test that function raises `ExceptionType` for invalid input.
      """
      # Prepare inputs.
      invalid_input = <value>
      # Prepare outputs.
      expected = """
      Expected error message
      """
      # Run test.
      with self.assertRaises(ExceptionType) as cm:
          function_under_test(invalid_input)
      # Check output.
      actual = str(cm.exception)
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
      # Prepare outputs.
      expected = "expected substring"
      # Run test.
      with self.assertRaises(AssertionError) as cm:
          function_under_test(invalid_input)
      # Check output.
      self.assertIn(expected, str(cm.exception))
  ```

## Use Golden File Testing Only for Large Outputs

- Always use `self.assert_equal()` to do a comparison of actual with the expected
  value hardwired in the code
- The only exception is when output is large (e.g., longer than 20 lines) or
  changes frequently use `self.check_string()` instead of `self.assert_equal()`
  - E.g.,
    ```python
    def test_large_output(self) -> None:
        """
        Test description.
        """
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

# End-to-end Unit Tests for Executables

- For testing an executable like `<process_file.py>` use a test class called
  `Test_process_file_py`

- For testing executables use end-to-end tests that:
  1. Use `capture_system_calls()` from `./helpers/hunit_test_utils.py` to mock
     and record calls to `subprocess.run()`, `hsystem.system()`, and
     `hsystem.system_to_string()`
  2. Verify that the exact commands were called with the correct arguments using
     `assert_invocations()`
  3. Validate that your CLI tool constructs and executes the right commands

- Example
  ```python
  def test1(self) -> None:
      """
      Test command ...
      """
      # Prepare inputs.
      args = ["TODO", "src", "py"]
      # Capture and execute.
      with hunteuti.capture_system_calls() as invocations:
          your_module.main(args)
      # Check expected outputs.
      expected_invocations_str = (
          "[{'args': (['rg', 'TODO', 'src', '-g', '*.py', '--hidden'],),\n"
          "  'function': 'subprocess.run',\n"
          "  'kwargs': {'check': False}}]"
      )
      hunteuti.assert_invocations(self, invocations, expected_invocations_str)
  ```

# Mocking

// TODO(gp): Review

## Mock Only External Dependencies
- Mock only 3rd-party providers, cloud infra (AWS/S3), databases, and external
  APIs, never internal helpers
- Mock the external library, not our internal wrapper on top of it

## Mock at the Call Site
- Patch where the symbol is looked up, not where it is defined:
  `@umock.patch.object(calling_module.dep, "method")`

## Class-Level Patches
- Declare `umock.patch.object(...)` as a class attribute; `start()` / `stop()`
  in `set_up_test()` / `tear_down_test()` so the same patch is reused per test

## Mock AWS / S3 via `S3Mock_TestCase`
- Inherit from `hmoto.S3Mock_TestCase` for in-process S3 mocking via `moto`
- `moto` must be imported before `boto3`; `hmoto.py` enforces this
- Each test gets a fresh bucket named `self.bucket_name`
