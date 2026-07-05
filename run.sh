# > Summarize the output of the script run.sh which has already been run and update HelpersTask1273_report.md

#TARGET="dev_scripts_helpers/documentation/test/test_notes_to_pdf.py"
#TARGET="dev_scripts_helpers"
TARGET="."
manage_cache.py --action clear_all
(export CSFY_DOCKER_ENGINE="docker"; i docker_cmd --stage=local -v 1.6.0 --cmd "pytest $TARGET") 2>&1 | tee build1.txt
#
manage_cache.py --action clear_all
(export CSFY_DOCKER_ENGINE="docker"; pytest_log $TARGET) 2>&1 | tee build2.txt
#
manage_cache.py --action clear_all
(export CSFY_DOCKER_ENGINE="apple"; pytest_log $TARGET) 2>&1 | tee build3.txt
