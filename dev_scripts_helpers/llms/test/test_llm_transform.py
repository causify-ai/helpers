import logging

import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)



class Test_llm_transform1(hunitest.TestCase):

    def test1(self) -> None:

        cmd = "dev_scripts_helpers/llms/llm_transform.py -i input.md -o - -t improve_markdown_slide"
