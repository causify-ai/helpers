- For each file XYZ.py add a file test/test_XYZ.py

- See example of helpers/hdbg.py and helpers/test/test_hdbg.py

- Follow the template ./unit_test_template.py

- Each function should be tested using inputs and outputs
  - In tested code change code accessing files to use data structures so that it
    is easier to test

- Do not test external library functions but focus on the logic specific of the
  script

- Do not test the script calling it as system, but test the script end-to-end

- For each function add enough unit tests to cover average and corner cases
