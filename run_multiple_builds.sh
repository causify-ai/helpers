#!/bin/bash -xe
# > Summarize the output of the script run.sh which has already been run and update HelpersTask1273_report.md

if [ 1 == 1 ]; then
rm -rf build1.txt build2.txt build3.txt
#TARGET="dev_scripts_helpers/documentation/test/test_notes_to_pdf.py"
#TARGET="dev_scripts_helpers"
#TARGET="."
#TARGET="helpers/test/test_hunit_test_purification.py helpers/test/test_hintrospection.py helpers/test/test_hnumpy.py helpers/test/test_hunit_test.py"
TARGET="linters2/test/test_linter_utils.py::Test_is_executable::test2"
CMD="pytest_log $TARGET"
#
#CMD="./pr_test.sh"
#
manage_cache.py --action clear_all
(export CSFY_DOCKER_ENGINE="docker"; $CMD) 2>&1 | tee build1.txt
#
manage_cache.py --action clear_all
(export CSFY_DOCKER_ENGINE="apple"; $CMD) 2>&1 | tee build2.txt
#
manage_cache.py --action clear_all
(export CSFY_DOCKER_ENGINE="docker"; i docker_cmd --stage=local -v 1.6.0 --cmd "$CMD") 2>&1 | tee build3.txt
fi;

if [ 0 == 1 ]; then
manage_cache.py --action clear_all
i pytest_failed -f build1.txt --only-file
(export CSFY_DOCKER_ENGINE="docker"; i docker_cmd --stage=local -v 1.6.0 --cmd "tmp.pytest_failed.sh") 2>&1 | tee build1.incr.txt
fi;
