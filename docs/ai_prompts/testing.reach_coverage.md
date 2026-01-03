Given the passed function, increase the test coverage towards
100% following the instructions `docs/ai_prompts/coding.format_unit_tests.md`

- For all the code you must follow the instructions in
  `docs/ai_prompts/coding.format_code.md`

Step 1
- Run the tests in the file corresponding to that function
  (e.g., helpers/hllm_cli.py -> helpers/test/test_hllm_cli.py)
  and compute the coverage

  pytest --cov=yourpkg --cov-report=term-missing --cov-report=html

Step 2
- Come up with a testing plan to address the missing untested code
  - Focus on testing modularly (i.e., testing one function at the
    time and then the cross-product)
  - Focus on end-to-end behavior rather than incidental behaviors
  - Do not test assertions or invalid inputs, unless critical

Step 3
- Write test class and methods
- Preview unit tests that need to be written by creating input and expected
  outputs
- Do not implement code

Step 4
- Once the user is ok with the plan, implement the code
- Compute the coverage and make sure that the target function
- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
