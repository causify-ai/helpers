import logging
import os

import helpers.hio as hio
import helpers.hunit_test as hunitest
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

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
        exec = hsystem.find_file_in_repo("llm_transform.py")
        out_file_name = os.path.join(self.get_scratch_space(), "output.md")
        cmd = (f"{exec} -i {in_file_name} -o {out_file_name}"
               " -t improve_markdown_slide")
        hsystem.system(cmd)
        # Check.
        act = hio.from_file(out_file_name)
        exp = """
        - If there is no pattern we can try learning, measure if learning works and, in
          the worst case, conclude that it does not work
        - If we can find the solution in one step or program the solution, machine
          learning is not the recommended technique, but it still works
        - Without data we cannot do anything: data is all that mattersV
        """
        exp = hprint.dedent(txt)
        self.assert_equal(act, exp)
