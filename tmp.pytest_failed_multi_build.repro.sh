#!/bin/bash
# Consolidated repro script for multiple builds.

BUILD_TAG=pytest_multi_build

# Build: dev_container
export CSFY_DOCKER_ENGINE='docker'; invoke docker_cmd --stage=local -v 1.6.0 --cmd "pytest_log dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf_output_types::test1 $*" 2>&1 | tee tmp.$BUILD_TAG.dev_container.txt

