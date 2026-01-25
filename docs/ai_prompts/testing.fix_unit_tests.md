When I pass you a test file apply the following transformations to the code,
making sure that there is no change in behavior.

## Step 1: Align strings to the code

- Instead of this

```
  def hello()
    ...
    content = """<start:file1.txt>
Content for file1
<start:file2.txt>
Content for file2
"""
```

  align the content of the string to the rest of the code

```
  def hello()
    ...
    content = """
    <start:file1.txt>
    Content for file1
    <start:file2.txt>
    Content for file2
    """
    content = hprint.dedent(content)
```

## Step 2: Rename the test methods as test1, test2, ...

## Step 3: Factor out common coded

Aggressively factor out common code in helper code so that each test method sets
the inputs and the expected value and then calls the helper function with the
common code

- Instead of:

    ```
    def test_first_line(self) -> None:
        """
        Test position in first line returns line 1.
        """
        # Prepare inputs.
        content = "Line 1\nLine 2\nLine 3"
        position = 3
        # Run test.
        actual = dshctsifi._get_line_number(content, position)
        # Check outputs.
        expected = 1
        self.assertEqual(actual, expected)

    def test_second_line(self) -> None:
        """
        Test position in second line returns line 2.
        """
        # Prepare inputs.
        content = "Line 1\nLine 2\nLine 3"
        position = 10
        # Run test.
        actual = dshctsifi._get_line_number(content, position)
        # Check outputs.
        expected = 2
        self.assertEqual(actual, expected)
    ```

- Do

    ```
    def helper(self, content: str, position: int, expected: int) -> None:
        # Run test.
        actual = dshctsifi._get_line_number(content, position)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test position in first line returns line 1.
        """
        # Prepare inputs.
        content = "Line 1\nLine 2\nLine 3"
        position = 3
        expected = 1
        # Run test.
        self.helper(content, position, expected)

    def test2(self) -> None:
        """
        Test position in second line returns line 2.
        """
        # Prepare inputs.
        content = "Line 1\nLine 2\nLine 3"
        position = 10
        expected = 2
        # Run test.
        self.helper(content, position, expected)
    ```

# Important

For all the code you must follow the instructions in
  `docs/ai_prompts/coding.format_code.md`
