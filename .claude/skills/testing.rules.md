- This file contains structural conventions for writing unit tests
- Related rule files:
  - `@.claude/skills/testing.design/SKILL.md` — design principles, data rules, code hygiene
  - `@.claude/skills/testing.mocking/SKILL.md` — mocking philosophy and patching patterns
  - `@.claude/skills/testing.speed/SKILL.md` — speed tiers and environment-conditional skipping
  - `@.claude/skills/testing.assertions/SKILL.md` — DataFrame/Series assertions, repr/str, QA testing

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
  - **Good**
    ```python
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

## Naming Conventions for a Method
- To test `method_a()` of class `FooBar`: class `TestFooBar`, method `test_method_a`
- To test protected `_gozilla()` of `FooBar`: method `test__gozilla` (double
  underscore — distinguishes from testing public `FooBar.gozilla()`)

## Always Use the `1` Suffix
- Always add a `1` suffix to test class names (`TestFooBar1`) and number test
  methods (`test1`, `test2`), even when there is only one class/method
- Rationale: makes adding a second class/method later free — no renaming of
  classes or golden files
- Numbering also signals "simplest case first, more complex cases later"

## Test Method Names
- Always number test methods (`test1`, `test2`, ...): the docstring explains
  what each tests
  - **Good**: `test1`, `test2`
  - **Bad**: `test_preserve_yaml_frontmatter`

## File Placement
- Test file for `foo/bar/module.py` goes in `foo/bar/test/test_module.py`
- Start with one file per directory (`test_<dirname>.py`); split into
  per-module files only when the single file grows too large

## Directory Helpers
- All path methods derive from `hunitest.TestCase` — paths are scoped to the
  running test class and method automatically

  | Method | Returns |
  | :----- | :------ |
  | `get_input_dir()` | Local path for static test fixtures checked into git |
  | `get_output_dir()` | Local path for golden files (managed by `check_string`) |
  | `get_scratch_space()` | Local ephemeral dir, deleted after the test |
  | `get_s3_scratch_dir()` | S3 path for large temporary data, unique per user/server/test |
  | `get_s3_input_dir()` | S3 path for input fixtures stored in the repo's S3 bucket |

- `get_s3_scratch_dir()` builds a path like:
  ```text
  s3://alphamatic-data/tmp/cache.unit_test/<user>.<server>.<project>.<TestClass.test_method>
  ```
- `get_s3_input_dir()` mirrors `get_input_dir()` but on S3; useful when
  fixtures are too large to commit to git

## Directory Structure
```text
module/test/
├── outcomes/
│   └── TestFooBar1.test_method_a/
│       ├── input/              <- get_input_dir()  [static fixtures]
│       └── output/
│           └── test.txt        <- check_string() golden file
├── tmp.scratch/
│   └── TestFooBar1.test_method_a/  <- get_scratch_space() [deleted after test]
└── test_foo.py
```

## Hierarchical `TestCase` Pattern
- When tested classes have inheritance, mirror that hierarchy in test classes:
  - Parent `SomeClientTestCase(hunitest.TestCase)` with private `_test...` helpers
  - Child `TestSomeClient(SomeClientTestCase)` with public `test...` methods that
    delegate to the parent helpers
- Use a `# #####...` separator comment to group each chunk of test logic

## `setUpClass` / `tearDownClass`
- Use only when setup is truly expensive and must run once per class (e.g.,
  opening a DB connection, loading a large shared fixture):
  ```python
  @classmethod
  def setUpClass(cls):
      ...

  @classmethod
  def tearDownClass(cls):
      ...
  ```
- For per-method setup prefer `set_up_test()` / `tear_down_test()` instead

## Update Test Tags
- To add a new tag: open `pytest.ini`, add a line in the `markers` section in
  alphabetical order: `<tag_name>: <short description>`

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

## Use Four Sections in Testing Methods
- Every test method must have four sections with standard comments:
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
      # Prepare outputs.
      <set up expected values>
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
- Use `self.assert_equal()` for short expected values inlined in the test
- Use `self.check_string()` when output is large (longer than ~20 lines) or
  changes frequently — see `@.claude/skills/testing.assertions/SKILL.md` for
  full usage and options

## Input Data Patterns
- Always use multiline text aligned to the variable of the string and then call
  `hprint.dedent()` or use `self.assert_equal(actual, expected, dedent=True)`
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
  scratch_dir = self.get_scratch_space()
  test_file = os.path.join(scratch_dir, "test.txt")
  hio.to_file(test_file, "content")
  ```
- Use input directory for large static fixtures:
  ```python
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
          Test description.
          """
          # Use self.test_data here.
  ```

## Nested Setup and Teardown
- Never override `setUp()` or `tearDown()` in child classes
- Each level in the inheritance chain gets a numbered suffix:
  - Parent: `set_up_test()` / `tear_down_test()`
  - Child: `set_up_test2()` / `tear_down_test2()` — must call the parent
    methods at the start/end respectively
  - Further levels: `set_up_test3()`, etc
  ```python
  class TestParent(hunitest.TestCase):
      @pytest.fixture(autouse=True)
      def setup_teardown_test(self):
          self.set_up_test()
          yield
          self.tear_down_test()

      def set_up_test(self) -> None:
          ...

      def tear_down_test(self) -> None:
          ...

  class TestChild(TestParent):
      @pytest.fixture(autouse=True)
      def setup_teardown_test(self):
          self.set_up_test2()
          yield
          self.tear_down_test2()

      def set_up_test2(self) -> None:
          self.set_up_test()  # Call parent first.
          ...

      def tear_down_test2(self) -> None:
          ...
          self.tear_down_test()  # Call parent last.
  ```

## Do Not Use `hdbg.dassert` in Tests
- `dassert` calls guard code invariants and must be removable without changing
  observable behavior — they cannot substitute for test assertions

# Test-mode Utilities
- Use inside production code that must behave differently during tests

  | Function | Purpose |
  | :------- | :------ |
  | `hunitest.in_unit_test_mode()` | `True` when running under pytest; skip expensive side effects |
  | `hunitest.pytest_print(txt)` | Write to stdout bypassing pytest's capture |
  | `hunitest.pytest_warning(txt, prefix="")` | Like `pytest_print` with a yellow `WARNING:` label |

  ```python
  import helpers.hunit_test as hunitest

  def expensive_side_effect() -> None:
      if hunitest.in_unit_test_mode():
          return  # Skip in tests.
      ...
  ```
