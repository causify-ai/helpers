import logging
import os

import pytest

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_llm_transform1(hunitest.TestCase):

    def test1(self) -> None:
        txt = """
        - If there is no pattern we can try learning, measure if learning works and, in the worst case, conclude that it does not work
        - If we can find the solution in one step or program the solution, machine learning is not the recommended technique, but it still works
        - Without data we cannot do anything: data is all that matters
        """
        # Run test.
        txt = hprint.dedent(txt)
        in_file_name = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(in_file_name, txt)
        script = hsystem.find_file_in_repo("llm_transform.py")
        out_file_name = os.path.join(self.get_scratch_space(), "output.md")
        # We use this prompt since it doesn't call OpenAI but it exercises all
        # the code.
        prompt_tag = "format_markdown"
        # prompt_tag = "improve_markdown_slide"
        cmd = f"{script} -i {in_file_name} -o {out_file_name}" f" -t {prompt_tag}"
        hsystem.system(cmd)
        # Check.
        act = hio.from_file(out_file_name)
        exp = r"""
        - If there is no pattern we can try learning, measure if learning works and, in
          the worst case, conclude that it does not work
        - If we can find the solution in one step or program the solution, machine
          learning is not the recommended technique, but it still works
        - Without data we cannot do anything: data is all that matters
        """
        self.assert_equal(act, exp, dedent=True)
