# Delete cache.
(export CSFY_DOCKER_ENGINE="docker"; i docker_cmd --stage=local -v 1.6.0 --cmd "pytest dev_scripts_helpers") 2>&1 | tee build1.txt
# Delete cache.
(export CSFY_DOCKER_ENGINE="docker"; pytest_log dev_scripts_helpers) 2>&1 | tee build2.txt
# Delete cache.
(export CSFY_DOCKER_ENGINE="apple"; pytest_log dev_scripts_helpers) 2>&1 | tee build3.txt
