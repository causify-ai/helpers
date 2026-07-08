#!/bin/bash -xe
pytest_failed.py -i ~/src/csfy1/helpers_root/tmp.failure.fast_tests.helperstask1273_get_mac_tests_to_pass.txt
pytest_failed.py -i /Users/saggese/src/csfy1/helpers_root/build1.txt
pytest_failed.py -i /Users/saggese/src/csfy1/helpers_root/build2.txt
pytest_failed.py -i /Users/saggese/src/csfy1/helpers_root/build3.txt

# ~/src/csfy1/helpers_root/tmp.failure.fast_tests.helperstask1273_get_mac_tests_to_pass.txt /Users/saggese/src/csfy1/helpers_root/build1.txt /Users/saggese/src/csfy1/helpers_root/build2.txt /Users/saggese/src/csfy1/helpers_root/build3.txt
