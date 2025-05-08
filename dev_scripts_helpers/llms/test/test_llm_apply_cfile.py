import logging

import pytest

import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_llm_apply_cfile1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_llm_apply_cfile1(hunitest.TestCase):
    """
    Run the script `llm_transform.py` in a Docker container.
    """

    # i lint --files dev_scripts_helpers/llms/llm_prompts.py

    # llm_apply_cfile.py --cfile linter_warnings.txt -p code_apply_linter_instructions -v DEBUG


# cmd line='./linters/base.py --files dev_scripts_helpers/llms/llm_prompts.py --num_threads serial'
# file_paths=1 ['dev_scripts_helpers/llms/llm_prompts.py']
# actions=25 ['add_python_init_files', 'add_toc_to_notebook', 'fix_md_links', 'lint_md', 'check_md_toc_headers', 'autoflake', 'fix_whitespaces', 'doc_formatter', 'isort', 'class_method_order', 'normalize_imports', 'format_separating_line', 'add_class_frames', 'remove_empty_lines_in_func
# tion', 'black', 'process_jupytext', 'check_file_size', 'check_filename', 'check_merge_conflict', 'check_import', 'warn_incorrectly_formatted_todo', 'check_md_reference', 'flake8', 'pylint', 'mypy']
# ////////////////////////////////////////////////////////////////////////////////
# dev_scripts_helpers/llms/llm_prompts.py:106: in public function `test`:D404: First word of the docstring should not be `This` [doc_formatter]
# dev_scripts_helpers/llms/llm_prompts.py:110: error: Need type annotation for "pre_transforms" (hint: "pre_transforms: set[<type>] = ...")  [var-annotated] [mypy]
# dev_scripts_helpers/llms/llm_prompts.py:111: error: Need type annotation for "post_transforms" (hint: "post_transforms: set[<type>] = ...")  [var-annotated] [mypy]
# dev_scripts_helpers/llms/llm_prompts.py:132: error: Need type annotation for "pre_transforms" (hint: "pre_transforms: set[<type>] = ...")  [var-annotated] [mypy]
# dev_scripts_helpers/llms/llm_prompts.py:164: error: Need type annotation for "pre_transforms" (hint: "pre_transforms: set[<type>] = ...")  [var-annotated] [mypy]
# dev_scripts_helpers/llms/llm_prompts.py:193: error: Need type annotation for "pre_transforms" (hint: "pre_transforms: set[<type>] = ...")  [var-annotated] [mypy]
# dev_scripts_helpers/llms/llm_prompts.py:227: error: Need type annotation for "pre_transforms" (hint: "pre_transforms: set[<type>] = ...")  [var-annotated] [mypy]
# dev_scripts_helpers/llms/llm_prompts.py:255: error: Need type annotation for "pre_transforms" (hint: "pre_transforms: set[<type>] = ...")  [var-annotated] [mypy]
# dev_scripts_helpers/llms/llm_prompts.py:275: error: Need type annotation for "pre_transforms" (hint: "pre_transforms: set[<type>] = ...")  [var-annotated] [mypy]
# dev_scripts_helpers/llms/llm_prompts.py:293: error: Need type annotation for "pre_transforms" (hint: "pre_transforms: set[<type>] = ...")  [var-annotated] [mypy]
# dev_scripts_helpers/llms/llm_prompts.py:311: error: Need type annotation for "pre_transforms" (hint: "pre_transforms: set[<type>] = ...")  [var-annotated] [mypy]
# dev_scripts_helpers/llms/llm_prompts.py:390: error: Need type annotation for "pre_transforms" (hint: "pre_transforms: set[<type>] = ...")  [var-annotated] [mypy]
# dev_scripts_helpers/llms/llm_prompts.py:391: error: Need type annotation for "post_transforms" (hint: "post_transforms: set[<type>] = ...")  [var-annotated] [mypy]
