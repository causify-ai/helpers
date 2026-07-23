#!/bin/bash
# Consolidated repro script for multiple builds.

BUILD_TAG=pytest_multi_build

# Build: docker
export CSFY_DOCKER_ENGINE='docker'; pytest_log helpers/lib_tasks/test/test_lib_tasks_find.py::TestLibTasksRunTests1::test_find_test_class1 $* 2>&1 | tee tmp.$BUILD_TAG.docker.txt

# Build: apple
export CSFY_DOCKER_ENGINE='apple'; pytest_log helpers/lib_tasks/test/test_lib_tasks_find.py::TestLibTasksRunTests1::test_find_test_class1 $* 2>&1 | tee tmp.$BUILD_TAG.apple.txt

# Build: dev_container
export CSFY_DOCKER_ENGINE='docker'; invoke docker_cmd --stage=local -v 1.6.0 --cmd "pytest_log dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf1::test2 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf1::test3 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_actions::test1 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_actions::test2 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_edge_cases::test1 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_edge_cases::test2 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_edge_cases::test3 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_edge_cases::test4 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_filters::test1 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_filters::test2 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_filters::test3 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_filters::test4 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_filters::test5 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_latex_options::test1 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_output_types::test1 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_output_types::test3 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_script_generation::test1 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_script_generation::test2 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_toc_options::test1 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_toc_options::test2 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_toc_options::test3 dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_toc_options::test4 $*" 2>&1 | tee tmp.$BUILD_TAG.dev_container.txt

