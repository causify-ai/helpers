### Extend script ./dev_scripts_helpers/testing/pytest_failed.py

#### [x] For GitHub CI 
~/src/csfy1/helpers_root/tmp.failure.fast_tests.helperstask1273_get_mac_tests_to_pass.txt

Parse this and remove
run_fast_tests / run_tests  UNKNOWN STEP  2026-07-06T17:59:35.1181332Z

Save beginning and end timestamps

####
/Users/saggese/src/csfy1/helpers_root/build1.txt

pytest didn't even start

####
/Users/saggese/src/csfy1/helpers_root/build2.txt

pytest started but didn't finish

####
/Users/saggese/src/csfy1/helpers_root/build3.txt

Started and finished

#### For all

Use the following markers

- pytest started
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- /venv/bin/python

- pytest collection completed
collected 3361 items / 156 deselected / 7 skipped / 3205 selected

- pytest run completed
[31m=========== [31m[1m34 failed[0m, [32m3157 passed[0m, [33m235 skipped[0m[31m in 886.58s (0:14:46)[0m[31m ===========[0m

#### [x] 

- Detect if the run terminated
- Print stats like:
  - how many tests were run, skipped, failed
    - Save result into files
  - total duration

- save the stack traces in different files
- how many are fast, slow, superslow

### [ ] Rename the output of dev_scripts_helpers/testing/pytest_log

file_name="tmp.pytest_script.txt"
