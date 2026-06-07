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

# Test File Organization

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

# Writing Test Code

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

## Code Formatting in Tests

### Dedent Strings to the Code

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

### Avoid Replicated Assignment

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

## Avoid Base Test Classes for Shared Code

- Do not create derived test classes to share testing utilities
- Instead, create helper methods within the test class that perform the shared
  operations

- Reason:
  - Base test classes complicate the inheritance hierarchy, make test discovery
    harder, and obscure the test structure
  - Helper methods are simpler, more explicit, and easier to understand

- **Bad** (using base test class to share utilities)
  ```python
  class Test_mdm_py_base(hunitest.TestCase):
      """
      Base class with shared utilities for mdm executable tests.
      """

      def _run_mdm(self, topic: str, action: str, *names: str) -> str:
          """
          Run mdm executable and capture output...
          """
          # ... implementation ...
          return result


  class Test_mdm_py(Test_mdm_py_base):
      """
      Test mdm executable.
      """

      def test1(self) -> None:
          """
          Test...
          """
          result = self._run_mdm("research", "list")
          # ... assertions ...
  ```

- **Good** (create helper method in the test class)
  ```python
  def _run_mdm(
      self: hunitest.TestCase,
      topic: str,
      action: str, 
      *names: str) -> str:
      """
      Run mdm executable and capture output...
      """
      # ... implementation ...
      return result


  class Test_mdm_py(hunitest.TestCase):
      """
      Test mdm executable.
      """

      def test1(self) -> None:
          """Test..."""
          result = _run_mdm(self, "research", "list")
          # ... assertions ...
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

# Test Input and Output Handling

## String Formatting for Test Inputs and Assertions

- Use multi-line strings with `hprint.dedent()` instead of escaped newline
  strings for improved readability and maintainability
- Always align multi-line strings to the variable indentation, then call
  `hprint.dedent()` to remove the indentation
- Alternative: use `self.assert_equal(actual, expected, dedent=True)` to dedent
  during comparison

- Examples:

  - **Bad**: Escaped newlines (hard to read)
    ```python
    text = "# Chapter 1\n\n## Section 1.1\nContent 1.1\n## Section 1.2\nContent 1.2"
    ```

  - **Bad**: Text not aligned to variable indentation
    ```python
    # Prepare inputs.
    text = """
line1
line2
line3
    """
    ```

  - **Good**: Multi-line string aligned and dedented (readable and maintainable)
    ```python
    # Prepare inputs.
    text = """
    # Chapter 1

    ## Section 1.1
    Content 1.1
    ## Section 1.2
    Content 1.2
    """
    text = hprint.dedent(text)
    ```

  - **Good**: Using dedent in assertion (convenient for comparisons)
    ```python
    # Prepare outputs.
    expected = """
    line1
    line2
    line3
    """
    # Check outputs.
    self.assert_equal(actual, expected, dedent=True)
    ```

## Use an Expected Output and `assert_equal`

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

## Do Not Use `hdbg.dassert` to Test Assertions

- Do not use `hdbg.dassert` since it guards production invariants and is not a
  substitute for test assertions
  - Always use `self.assert*` family instead

## Replace Checking Invariants with `assert_equal`
- Do not use multiple `assertIn()` calls to check individual pieces of a string
  output; instead compare the entire output with `assert_equal()`
  - **Bad** (multiple assertIn checks on parts of the output)
    ```python
    actual = <function_that_returns_string>()
    # Check outputs.
    self.assertIn('"A"', actual)
    self.assertIn('"B"', actual)
    self.assertIn('"C"', actual)
    self.assertIn('"A" -> "B"', actual)
    self.assertIn('"B" -> "C"', actual)
    ```
  - **Good** (single assert_equal with full expected output)
    ```python
    actual = <function_that_returns_string>()
    # Prepare outputs.
    expected = """
    digraph {
        rankdir=TB;
        "A" [fillcolor="#A6C8F4"];
        "B" [fillcolor="#A6C8F4"];
        "C" [fillcolor="#A6C8F4"];
        "A" -> "B" [color="#555555"];
        "B" -> "C" [color="#555555"];
    }
    """
    # Check outputs.
    self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)
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

## Never Use `self.check_string()

- Always use `self.assert_equal()` to do a comparison of actual with the expected
  value hardwired in the code

# End-to-end Unit Tests for Executables

## Test Name
- For testing an executable like `<process_file.py>` use a test class called
  `Test_process_file_py`

## Test Behavior, Not Implementation
- Prefer validating externally observable behavior over internal implementation details
- E.g., Verify:
	- generated files
	- stdout/stderr
	- exit codes
	- constructed commands
	- side effects on disk

## Create Files in the Scratch Space
- Always create test files under `self.get_scratch_space()` rather than mocking
  file access

- The goal is to exercise as much real code as possible, so do not mock:
	- filesystem operations
	- argument parsing
	- orchestration logic

- This keeps tests closer to real execution and validates more of the system end
  to end
- Use realistic:
	- Directory layouts
	- File names
	- File contents
	- Command-line arguments

## Call Main Directly for Simple Executables (with Mock)
- When testing a simple end-to-end executable that doesn't require special
  packages installed through uv, use the idiom of mocking `sys.argv` with
  `mock.patch()` and then calling the `main()` function directly

- **Good** (when executable is simple and can be called directly)
  ```python
  # Prepare inputs.
  parser = your_module._parse()
  argv = ["script_name.py", "--arg1", "value1"]
  # Run test.
  with mock.patch("sys.argv", argv):
      your_module._main(parser)
  # Check outputs.
  # ... assertions on file system state or captured output ...
  ```
- This approach is suitable when:
  - The executable is simple enough to call directly in a test
  - You want to test the full argument parsing and main logic flow
  - You don't need subprocess isolation for the test

## Locate Script Paths Dynamically
- Do not hardwire paths to executable scripts in tests, instead, use
  `hgit.find_file_in_git_tree()` to locate the script path dynamically
- This ensures tests work regardless of where the code is run from and handles
  cases where scripts are relocated

- **Bad** (hardcoded path)
  ```python
  executable = "dev_scripts_helpers/system_tools/mdm"
  result = hsystem.system(f"{executable} --help")
  ```

- **Good** (dynamic path lookup)
  ```python
  executable = hgit.find_file_in_git_tree("mdm")
  result = hsystem.system(f"{executable} --help")
  ```

## Use the Mocking Infrastructure
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

## Document Output Assertions When Exact Matching is Not Possible
- When checking end-to-end output from a test, if it is not possible to check the
  exact output (e.g., since the output depends on environment-specific details),
  add a comment above the assertion showing:
  1. How the output should look like from the actual command
  2. The invariant being checked (what property must hold true)

- This documents the intent of the test for future maintainers when exact string
  matching is not feasible

- **Good** (comment shows expected format and what is being validated)
  ```python
  # Check outputs.
  # Expected: contains the output from the command (paths are variable)
  # Invariant: output contains expected sections and key values
  self.assertIn("Processing complete", actual)
  self.assertIn("Files: ", actual)
  self.assertIn("Status: SUCCESS", actual)
  ```

- **Good** (with fuzzy matching and explanatory comment)
  ```python
  # Check outputs.
  # Expected from command: "Processed /path/to/file.txt in 0.123s"
  # Invariant: message format is consistent and success status is present
  expected = """
  Processed .*/path/to/file.txt in [0-9.]+s
  Status: SUCCESS
  """
  self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)
  ```

## Mock LLM APIs

- When testing code that calls LLM APIs (e.g., OpenAI, Claude), use
  `hllmcli.mock_apply_llm()` to mock the API calls and pass `--backend mock`
  via the command line to disable real API calls
- This avoids:
  - Real API costs and rate limits during testing
  - Dependency on network connectivity or API keys
  - Non-deterministic responses from live models

- This enables running end-to-end tests that exercise the full code path
  (argument parsing, orchestration, file I/O) without needing a real LLM
  backend

### Via `hllmcli.mock_apply_llm`

- **In end-to-end test code**: use `hllmcli.mock_apply_llm()` as a context
  manager to mock `apply_llm()` calls:
  # Example in a test:
  ```
  def test_my_function(self):
      with mock_apply_llm():
          # Code that calls apply_llm() will now return mocked values
          response, token_stats = apply_llm(
              "some input",
              system_prompt="some prompt",
          )
          # `response` will be the MD5 hash of "some inputsome prompt"
          # `token_stats` will be TokenStats() with zeros.
  ```

## Via `--backend mock`

- **From the command line**: pass `--backend mock` as a CLI argument to skip
  real LLM API calls:
  ```bash
  > script.py --backend mock
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
