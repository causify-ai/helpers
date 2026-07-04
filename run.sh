# > Summarize the output of the script run.sh which has already been run
#TARGET="dev_scripts_helpers/documentation/test/test_notes_to_pdf.py"
#TARGET="dev_scripts_helpers"
#TARGET="."
TARGET="helpers/test/test_hdocker.py::Test_get_docker_mount_info1::test1 helpers/test/test_hserver.py::Test_hserver_inside_docker_container_on_gp_mac1::test_get_docker_info1 helpers/test/test_hsystem.py::Test_system1::test7 import_check/test/test_detect_import_cycles.py::Test_detect_import_cycles::test11 import_check/test/test_detect_import_cycles.py::Test_detect_import_cycles::test12 import_check/test/test_detect_import_cycles.py::Test_detect_import_cycles::test13 import_check/test/test_detect_import_cycles.py::Test_detect_import_cycles::test9 import_check/test/test_show_imports.py::Test_show_imports::test10 linters/test/test_amp_check_md_toc_headers.py::Test_verify_toc_postion::test1 linters/test/test_amp_dev_scripts.py::Test_linter_py1::test_DevToolsTask408 linters/test/test_amp_dev_scripts.py::Test_linter_py1::test_linter1 linters/test/test_amp_dev_scripts.py::Test_linter_py1::test_linter2 linters/test/test_amp_dev_scripts.py::Test_linter_py1::test_linter_ipynb1 linters/test/test_amp_normalize_import.py::TestEndToEndShortImports::test_normalize_imports linters2/test/test_linter_utils.py::Test_is_executable::test2 linters2/test/test_normalize_import.py::TestEndToEndShortImports::test_normalize_imports"
manage_cache.py --action clear_all
(export CSFY_DOCKER_ENGINE="docker"; i docker_cmd --stage=local -v 1.6.0 --cmd "pytest $TARGET") 2>&1 | tee build1.txt
#
manage_cache.py --action clear_all
(export CSFY_DOCKER_ENGINE="docker"; pytest_log $TARGET) 2>&1 | tee build2.txt
#
manage_cache.py --action clear_all
(export CSFY_DOCKER_ENGINE="apple"; pytest_log $TARGET) 2>&1 | tee build3.txt
