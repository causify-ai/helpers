# Step 1)

- Run all the requested tests with pytest
- Find out which ones are failing due to a mismatch between `actual` and
  `expected` string
- Print the list of test cases that are failing

# Step 2)

- Run each failing test one at the time, e.g.,
  ```bash
  > pytest helpers/test/test_hlatex.py::Test_frame_sections1::test_all_section_types
  ```
- Print the test case that is failing and that we are fixing

# Step 3)

- Update the `expected` variable in the `test_*.py` code by changing the
  expected variables to match what is saved by pytest in
  `tmp.final.expected.txt`
- Use the idiom below
  ```python
  expected = r"""
  ...
  """
  expected = hprint.dedent(expected)
  ```
- Run to make sure the test is passing
