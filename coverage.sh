#!/bin/bash -xe

coverage erase
#coverage run --rcfile=.coveragerc -m pytest helpers/test/test_hllm_cli.py::Test_apply_llm_prompt_to_df1
pytest helpers/test/test_hllm_cli.py::Test_apply_llm_prompt_to_df1   --cov-branch --cov=.
coverage report --rcfile=.coveragerc -m --include='*/hllm_cli.py'
coverage html --rcfile=.coveragerc -m --include='*/hllm_cli.py'

