import logging
import os
from typing import Tuple

import pytest

import dev_scripts_helpers.llms.llm_prompts_utils as dshllprut
import helpers.hdbg as hdbg
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
    """
    Run the script `llm_transform.py` in a Docker container.
    """

    def test_get_transforms(self) -> None:
        """
        Check retrieving the available LLM transforms.
        """
        transforms = dshllprut.get_transforms()
        _LOG.debug(hprint.to_str("transforms"))
        self.assertGreater(len(transforms), 0)

    def setup_test(self) -> Tuple[str, str, str]:
        """
        Set up the test environment by creating an input markdown file and
        determining the script and output file paths.

        :returns: A tuple containing the script path, input file path,
            and output file path.
        """
        txt = """
        - If there is no pattern we can try learning, measure if learning works and, in the worst case, conclude that it does not work
        - If we can find the solution in one step or program the solution, machine learning is not the recommended technique, but it still works
        - Without data we cannot do anything: data is all that matters
        """
        txt = hprint.dedent(txt)
        in_file_name = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(in_file_name, txt)
        script = hsystem.find_file_in_repo("llm_transform.py")
        out_file_name = os.path.join(self.get_scratch_space(), "output.md")
        return script, in_file_name, out_file_name

    def test1(self) -> None:
        """
        Run the `llm_transform.py` script with a specific prompt tag and verify
        the output.
        """
        script, in_file_name, out_file_name = self.setup_test()
        # Run test.
        # We use this prompt since it doesn't call OpenAI, but it exercises all
        # the code.
        prompt_tag = "md_format"
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

    @pytest.mark.skip(reason="Run manually since it needs OpenAI credentials")
    def test2(self) -> None:
        """
        Run the `llm_transform.py` script with various prompt tags and print
        the output.
        """
        script, in_file_name, out_file_name = self.setup_test()
        # Run test.
        transforms = dshllprut.get_transforms()
        for prompt_tag in transforms:
            # Remove the output file.
            cmd = "rm -f " + out_file_name
            hsystem.system(cmd)
            hdbg.dassert(not os.path.exists(out_file_name))
            # Run the test.
            cmd = (
                f"{script} -i {in_file_name} -o {out_file_name}"
                f" -t {prompt_tag}"
            )
            hsystem.system(cmd)
            # Check.
            hdbg.dassert_file_exists(out_file_name)
            # Print.
            res = hio.from_file(out_file_name)
            _LOG.info("\n" + hprint.frame(prompt_tag))
            _LOG.info("\n" + res)
