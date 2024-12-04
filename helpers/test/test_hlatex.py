import logging

import helpers.hlatex as hlatex
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################


class Test_remove_latex_formatting1(hunitest.TestCase):
    def test1(self) -> None:
        txt = r"""
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
        txt = hprint.dedent(txt)
        exp = r"""
        - If there is no pattern, we can try learning:
          - Measure if learning works.
          - In the worst case, conclude that it
            does not work.
        - If we can find the solution in one step or
          program the solution:
          - Machine learning is not the recommended
            technique, but it still works.
        - Without data, we cannot do anything:
          data is all that matters."""
        exp = hprint.dedent(exp)
        act = hlatex.remove_latex_formatting(txt)
        self.assert_equal(act, exp)
