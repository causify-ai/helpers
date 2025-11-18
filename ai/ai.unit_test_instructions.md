- For a file XYZ.py add a file test/test_XYZ.py
  - As an example see `helpers/hdbg.py` and its test code in
    `helpers/test/test_hdbg.py`

- To write unit test follow the template `ai/unit_test_template.py`
  - Each tested function has a test class
  - Each test case corresponds to a single test method
  - For each tested function add enough unit tests to cover average and corner
    cases

- Prefer to use inputs and outputs as chunks of texts like
  ```
  input = """
  hello
  world
  """
  input_txt = hprint.dedent(input_txt)
  ```

- Clearly summarize

- Each function should be tested using its inputs and outputs
  - If a function to be tested uses files, change the code under test to use
    data structures so that it is easier to test and then add functions to read
    / write output

- Do not use mock

- Do not test external library functions but focus on the logic specific of the
  script

- Do not test the script calling it as system, but test the script end-to-end
  calling it as functions

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
- In every test method separate logically distinct code chunks to prepare the
  inputs, run the tests, and check the outputs using comments like below:
  - E.g.,
    ```
    # Prepare inputs.
    input_data = [1, 2, 3]
    # Run test.
    result = my_function(input_data)
    # Check outputs.
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

- When creating inputs for tests instead of using array of strings use
  - E.g., bad
    ```
    # Prepare inputs.
    lines = [
        "# Chapter 1",
        "",
        "Intro text",
        "",
        "## Section 1.1",
        "",
        "Content of section 1.1",
        "",
        "## Section 1.2",
        "",
        "Content of section 1.2",
        "",
        "# Chapter 2",
        "",
        "Chapter 2 intro",
    ]
    ```
  - Good
    ```
    # Prepare inputs.
    lines = """
    # Chapter 1

    Intro text

    ## Section 1.1

    Content of section 1.1

    ## Section 1.2

    Content of section 1.2

    # Chapter 2

    Chapter 2 intro
    """
    lines = hprint.dedent(lines)
    ```

- Make sure that all the unit tests pass by running pytest
