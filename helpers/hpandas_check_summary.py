"""
Import as:

import helpers.hpandas as hpandas
"""

import dataclasses
from typing import List, Optional

import pandas as pd

import helpers.hlogging as hloggin

_LOG = hloggin.getLogger(__name__)


# #############################################################################
# _SummaryRow
# #############################################################################


@dataclasses.dataclass
class _SummaryRow:
    """
    Output of a check corresponding to a row of the summary df.
    """

    # Description of the check.
    description: str
    # Description of the output.
    comment: str
    # Whether the check was successful or not.
    is_ok: bool


# #############################################################################
# CheckSummary
# #############################################################################


class CheckSummary:
    """
    Collect and report the results of several checks performed in a notebook.
    """

    def __init__(self, *, title: Optional[str] = ""):
        self.title = title
        # Initialize the array for storing summary rows.
        self._array: List[_SummaryRow] = []

    def add(self, description: str, comment: str, is_ok: bool) -> None:
        """
        Add the result of a single check.
        """
        summary_row = _SummaryRow(description, comment, is_ok)
        self._array.append(summary_row)

    def is_ok(self) -> bool:
        """
        Compute whether all the checks were successful or not.
        """
        is_ok = all(sr.is_ok for sr in self._array)
        return is_ok

    def report_outcome(
        self, *, notebook_output: bool = True, assert_on_error: bool = True
    ) -> Optional[str]:
        """
        Report the result of the entire check.

        :param notebook_output: report the result of the checks for a
            notebook or as a string
        :param assert_on_error: assert if one check failed
        """
        df = pd.DataFrame(self._array)

        # Compute result as a string.
        result = []
        if self.title:
            result.append("# " + self.title)
        result.append(str(df))
        is_ok = self.is_ok()
        result.append(f"is_ok={is_ok}")
        result = "\n".join(result)
        # Display on a notebook, if needed.
        if notebook_output:
            if self.title:
                print(self.title)

            # Convert DataFrame to HTML with colored rows based on 'is_ok' column.
            def _color_rows(row: bool) -> str:
                """
                Apply red/green color based on boolean value in `row["is_ok"]`.
                """
                is_ok = row["is_ok"]
                color = "#FA6B84" if not is_ok else "#ACF3AE"
                return [f"background-color: {color}"] * len(row)

            df_html = df.style.apply(_color_rows, axis=1)
            from IPython.display import display

            display(df_html)
            print(f"is_ok={is_ok}")
        # Assert if at least one of the check failed.
        if not is_ok and assert_on_error:
            raise ValueError("The checks have failed:\n" + result)
        # For notebooks, we want to return None, since the outcome was
        # already displayed.
        if notebook_output:
            result = None
        return result
