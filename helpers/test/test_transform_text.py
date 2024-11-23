import logging

import helpers.transform_text as dshdtrtx
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################


class Test_remove_latex_formatting1(hunitest.TestCase):
    def test1(self) -> None:
        txt = """
        - If there is \textcolor{red}{no pattern}, we can try learning:
          - Measure if \textcolor{blue}{learning works}.
          - In the \textcolor{orange}{worst case}, conclude that it
            \textcolor{green}{does not work}.
        - If we can find the \textcolor{purple}{solution in one step} or
          \textcolor{cyan}{program the solution}:
          - \textcolor{brown}{Machine learning} is not the \textcolor{teal}{recommended
            technique}, but it still works.
        - Without \textcolor{magenta}{data}, we cannot do anything:
          \textcolor{violet}{data is all that matters}.
        """
        exp = """
        """
        act = dshdtrtx.remove_latex_formatting(txt)
        self.assert_equal(act, exp)
