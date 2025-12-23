# Unit Testing Instructions for LLMs

These instructions guide you in generating unit tests for the helpers repository.
Follow these rules exactly when writing test code.

## Critical Requirements

- **ALWAYS** inherit from `hunitest.TestCase`, never from `unittest.TestCase`
- **ALWAYS** add type hint `-> None:` to test methods
- **ALWAYS** add a docstring to every test method describing what is tested
- **ALWAYS** use three-section structure: Prepare inputs → Run test → Check outputs
- **ALWAYS** use `self.assert_equal()` instead of `self.assertEqual()` if the
  inputs are all strings
- **NEVER** use `hdbg.dassert()` in tests
- **NEVER** use mock objects
- **NEVER** test external library functions (focus on our code logic only)
- **NEVER** create temporary files with `tempfile` (use `self.get_scratch_space()`)

## File Structure Template

When creating a test file for `module_name.py`, generate exactly this structure:

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

## Naming Rules

### Test File Names
- Source file: `helpers/module_name.py`
- Test file: `helpers/test/test_module_name.py`

### Test Class Names
Apply these rules in order:

1. **Testing a function** → Use `Test_<FunctionName>`
   - Function `parse_limit_range()` → `class Test_parse_limit_range(hunitest.TestCase):`
   - Function `apply_limit_range()` → `class Test_apply_limit_range(hunitest.TestCase):`

2. **Testing a class** → Use `Test<ClassName>` (no underscore)
   - Class `Config` → `class TestConfig(hunitest.TestCase):`
   - Class `ConfigBuilder` → `class TestConfigBuilder(hunitest.TestCase):`

### Test Method Names
Choose pattern based on number of test cases:

**Pattern 1: Descriptive names (use when < 5 similar tests)**
```python
def test_<function>_<scenario>(self) -> None:
```
Examples:
- `test_parse_limit_range_valid_input(self) -> None:`
- `test_parse_limit_range_no_colon(self) -> None:`
- `test_parse_limit_range_invalid_start(self) -> None:`

**Pattern 2: Numbered (use when >= 5 similar tests)**
```python
def test_<function>1(self) -> None:
def test_<function>2(self) -> None:
def test_<function>3(self) -> None:
```

## Test Method Structure

**MANDATORY three-section structure for every test method:**

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

### Standard Comment Patterns

**Section 1 - Use ONE of these:**
- `# Prepare inputs.`
- `# Prepare outputs.` (when setting up expected values)

**Section 2 - Use ONE of these:**
- `# Run test.`
- `# Run.`

**Section 3 - Use ONE of these:**
- `# Check output.`
- `# Check outputs.`

## Helper Method Pattern

**When to create a helper method:**
- You are writing 3+ test methods that call the same function
- Only the input values and expected outputs differ
- The test logic (run + check) is identical

**Helper method template:**

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
        """Test description."""
        # Prepare inputs.
        input1 = <value>
        # Prepare outputs.
        expected = <value>
        # Run test.
        self.helper(input1, expected)

    def test_case2(self) -> None:
        """Test description."""
        # Prepare inputs.
        input1 = <different_value>
        # Prepare outputs.
        expected = <different_value>
        # Run test.
        self.helper(input1, expected)
```

**Alternative: Private helper with underscore prefix:**
```python
def _test_function_name(self, param1: Type1, expected: Type2) -> None:
```

## Assertion Patterns

### Basic Assertions

- **Pattern 1: Compare simple values**
  ```python
  # Check outputs.
  self.assert_equal(actual, expected)
  ```

- **Pattern 2: Compare data structures as strings**
  ```python
  # Check outputs.
  self.assert_equal(str(actual), str(expected))
  ```

- **Pattern 3: Compare with fuzzy matching (whitespace differences)**
  ```python
  # Check outputs.
  self.assert_equal(actual, expected, fuzzy_match=True)
  ```

- **Pattern 4: Compare with text purification (memory addresses)**
  ```python
  # Check outputs.
  self.assert_equal(actual, expected, purify_text=True)
  ```

- **Pattern 5: Compare with auto-dedent**
  ```python
  # Check outputs.
  expected = """
      line1
      line2
      """
  self.assert_equal(actual, expected, dedent=True)
  ```

### Golden File Testing

- **Use when:** Output is > 50 lines OR changes frequently
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

- **With fuzzy matching:**
  ```python
  self.check_string(actual, fuzzy_match=True)
  ```

## Exception Testing Pattern

- **MANDATORY structure for testing exceptions:**
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

- **Simplified version (when exact message doesn't matter):**
  ```python
  def test_raises_error(self) -> None:
      """Test that function raises AssertionError for invalid input."""
      # Prepare inputs.
      invalid_input = <value>
      # Run test and check output.
      with self.assertRaises(AssertionError):
          function_under_test(invalid_input)
  ```

- **Check for partial message:**
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

## Test Coverage Rules

- **For each function, generate tests for:**
  1. **Happy path** - Normal, expected input
     - `test_<function>_valid_input()`

  2. **Edge cases** - Boundary conditions
     - Empty input: `test_<function>_empty_input()`
     - Zero: `test_<function>_zero()`
     - Single item: `test_<function>_single_item()`
     - Large input: `test_<function>_large_input()`

  3. **Error conditions** - Invalid input
     - None: `test_<function>_none_raises_error()`
     - Wrong type: `test_<function>_invalid_type_raises_error()`
     - Invalid value: `test_<function>_invalid_value_raises_error()`

## Input Data Patterns

### Pattern 1: Multiline Text Input (PREFERRED)
```python
# Prepare inputs.
text = """
line1
line2
line3
"""
text = hprint.dedent(text)
```

### Pattern 2: List Input
```python
# Prepare inputs.
items = ["a", "b", "c"]
```

### Pattern 3: Using Scratch Space for File Testing
```python
# Prepare inputs.
scratch_dir = self.get_scratch_space()
test_file = os.path.join(scratch_dir, "test.txt")
hio.to_file(test_file, "content")
```

### Pattern 4: Using Input Directory for Large Test Data
```python
# Prepare inputs.
input_file = os.path.join(self.get_input_dir(), "test_data.json")
data = hio.from_json(input_file)
```

## Setup/Teardown Pattern

**Use when:** Multiple test methods need the same setup/teardown code

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

## Complete Generation Template

When generating a test file, follow this exact sequence:

- Step 1: Imports
  ```python
  import logging

  import helpers.hunit_test as hunitest
  # Add module-specific imports

  _LOG = logging.getLogger(__name__)
  ```

- Step 2: For each function/class to test
  ```python
  # #############################################################################
  # TestClassName
  # #############################################################################


  class TestClassName(hunitest.TestCase):
      """
      Test <brief description>.
      """
  ```

- Step 3: Add helper if needed
  ```python
      def helper(self, input_param: Type, expected: Type) -> None:
          """
          Test helper for <function_name>.

          :param input_param: Description
          :param expected: Expected output
          """
          # Run test.
          actual = function_under_test(input_param)
          # Check outputs.
          self.assert_equal(str(actual), str(expected))
  ```

- Step 4: Generate test methods
  For each test case:
  ```python
      def test_<scenario>(self) -> None:
          """Test <specific behavior>."""
          # Prepare inputs.
          <setup>
          # Prepare outputs.
          expected = <value>
          # Run test.
          actual = function_under_test(<inputs>)
          # Check outputs.
          self.assert_equal(str(actual), str(expected))
  ```

## Real-World Example from Codebase

- An complete example is
  ```python
  import logging

  import helpers.hparser as hparser
  import helpers.hunit_test as hunitest

  _LOG = logging.getLogger(__name__)


  # #############################################################################
  # TestParseLimitRange
  # #############################################################################


  class TestParseLimitRange(hunitest.TestCase):
      """
      Test parsing limit range strings into tuples.
      """

      def test_parse_limit_range_valid1(self) -> None:
          """Test parsing valid range format."""
          # Prepare inputs.
          limit_str = "1:5"
          # Prepare outputs.
          expected = (1, 5)
          # Run test.
          actual = hparser.parse_limit_range(limit_str)
          # Check outputs.
          self.assertEqual(actual, expected)

      def test_parse_limit_range_no_colon(self) -> None:
          """Test that missing colon raises assertion error."""
          # Prepare inputs.
          limit_str = "15"
          # Run test and check output.
          with self.assertRaises(AssertionError):
              hparser.parse_limit_range(limit_str)

      def test_parse_limit_range_invalid_start(self) -> None:
          """Test that non-integer start raises fatal error."""
          # Prepare inputs.
          limit_str = "abc:5"
          # Run test and check output.
          with self.assertRaises(AssertionError):
              hparser.parse_limit_range(limit_str)


  # #############################################################################
  # TestApplyLimitRange
  # #############################################################################


  class TestApplyLimitRange(hunitest.TestCase):
      """
      Test applying limit ranges to item lists.
      """

      def test_apply_limit_range_no_limit(self) -> None:
          """Test that None limit range returns original items."""
          # Prepare inputs.
          items = ["a", "b", "c", "d", "e"]
          # Run test.
          actual = hparser.apply_limit_range(items, None)
          # Check outputs.
          self.assertEqual(actual, items)

      def test_apply_limit_range_valid_range(self) -> None:
          """Test applying valid range to items."""
          # Prepare inputs.
          items = ["a", "b", "c", "d", "e"]
          limit_range = (1, 3)
          # Prepare outputs.
          expected = ["b", "c", "d"]  # 0-indexed, inclusive
          # Run test.
          actual = hparser.apply_limit_range(items, limit_range)
          # Check outputs.
          self.assertEqual(actual, expected)
  ```

## Test Method Generation Checklist

Before completing test generation, verify:

- [ ] Type hint `-> None:` present
- [ ] Docstring present and descriptive
- [ ] Three sections with standard comments
- [ ] Using `self.assert_equal()` not `self.assertEqual()`
- [ ] Actual before expected in assertions
- [ ] Helper method if 3+ similar tests
- [ ] Class separator comment if multiple classes
- [ ] Imports include `logging` and `hunitest`
- [ ] Logger constant `_LOG` defined after imports
- [ ] No mock objects used
- [ ] No `hdbg.dassert()` calls

## End of Instructions

Follow these rules exactly when generating unit tests. Prioritize clarity,
consistency, and adherence to the patterns shown above.
