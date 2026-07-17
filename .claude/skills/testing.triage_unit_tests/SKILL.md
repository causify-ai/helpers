Given a target `<TARGET>` (e.g., dev_scripts_helpers/documentation/test/test_notes_to_pdf.py)

## Step 1
Run the tests

> pytest_log `<TARGET>`

## Step 2
- Collect the failing tests

```
> i pytest_failed
...
Failed tests: 25/7
dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_actions::test1
dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_actions::test2
dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_edge_cases::test1
dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_edge_cases::test2
dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_edge_cases::test3
dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_edge_cases::test4
dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_filters::test1
dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_filters::test2
dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_filters::test3
dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_filters::test4
dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_filters::test5
...
13:07:36 - WARN  lib_tasks_pytest.py pytest_failed:1745                 To run the failed tests run: tmp.pytest_failed.sh
...
```

## Step 3
- Analyze each failure and create a plan `plan_fix.md` for fixing the tests in
  chunks

  ```
  # [ ] Group1: short description
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_actions::test1
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_actions::test2
  dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_edge_cases::test1

  - Reason: ...
    - ...

  - Potential fix: ...
    - ...

  # [ ] Group2: ...
  ...
  ```
- Write the comments as bullet points according to `.claude/skills/markdown.rules.md`

- For the tests that involve docker / apple containers run the same tests with
  different builds 

  ```
  manage_cache.py --action clear_all
  (export CSFY_DOCKER_ENGINE="docker"; i docker_cmd --stage=local -v 1.6.0 --cmd "pytest $TARGET") 2>&1 | tee build1.txt
  #
  manage_cache.py --action clear_all
  (export CSFY_DOCKER_ENGINE="docker"; pytest_log $TARGET) 2>&1 | tee build2.txt
  #
  manage_cache.py --action clear_all
  (export CSFY_DOCKER_ENGINE="apple"; pytest_log $TARGET) 2>&1 | tee build3.txt
  ```

  see if the problem / solution is the same for all the 3
  builds

## Step 4
- Rank the issues in terms of easy wins
