export CSFY_DOCKER_ENGINE="docker"; i docker_cmd --stage=local -v 1.6.0 -cmd "pytest_log dev_scripts_helpers"
export CSFY_DOCKER_ENGINE="docker"; pytest_log dev_scripts_helpers
export CSFY_DOCKER_ENGINE="apple"; pytest_log dev_scripts_helpers
