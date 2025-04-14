from typing import Any, List

import nltk
import pandas as pd
import tqdm.autonotebook as tqdm

import helpers.hcache as hcache
import helpers.hdbg as hdbg
import helpers.hio as hio

# hcac._get_cache_types()
hcache._get_cache_types()
x = "hcac._get_cache_types()"


def func(a: str, lst: List[str]) -> Any:
    """
    First comment line.
    """
    import helpers.hcache as hcache

    hcache._get_cache_types()
    for i in tqdm.tqdm(lst):
        a += "string {}".format(i)
    return a


def func2(df: pd.DataFrame, a: str) -> pd.DataFrame:
    """
    Generate "random returns". Use lag + noise as predictor.

    ```
        git@github.com:alphamatic/amp
        https://github.com/alphamatic/amp
    ```

    The stage names refer to Node objects, which are not json serializable.
    We don't use io.dassert_is_valid_file_name().

    E.g.,
    ```
    PostgreSQL 11.5 on x86_64-pc-linux-gnu
        compiled by gcc (GCC) 4.8.3 20140911 (Red Hat 4.8.3-9), 64-bit
    ```
    """
    hio.dassert_is_valid_file_name("test.py")
    b = """
    Before separating line.
    ##########################################################################
    Comments inside string.
    ##########################################################################
    """
    result_df = df.loc[a + b :]  # type: ignore[misc]
    return result_df


def func3(a: str) -> str:
    """
    Generate "random returns".

    Use lag + noise as predictor.
    """
    if a is not None:
        assert isinstance(a, str), (
            f"You passed '{a}' or type '{type(a)}'" "instead of str"
        )
    ## [C0330(bad-continuation), ] Wrong hanging indentation before
    ##   block (add 4 spaces).
    return a


# #############################################################################
# MyClass
# #############################################################################


class MyClass:
    """
    Contains all of the logic to construct the standard bars from chapter 2.
    This class shouldn't be used directly. We have added functions to the
    package such as get_dollar_bars which will create an instance of this class
    and then construct the standard bars, to return to the user.

    This is because we wanted to simplify the logic as much as possible,
    for the end user.
    """

    @staticmethod
    def _private_static_method(a: str) -> str:
        """
        For reference, let.

        - N = 2
        - M = 3
        """
        return a

    def _private_regular_method(self, a: str) -> str:
        """
        Read csv file(s) or pd.DataFrame in batches and then constructs the
        financial data structure in the form of a DataFrame.

        The csv file or
        DataFrame must have only 3 columns: date_time, price, & volume.
        """
        # Returning
        return a


# #############################################################################
# New part 2.
# #############################################################################

# #############################################################################
# TestReplaceShortImportInCode
# #############################################################################


class TestReplaceShortImportInCode:

    def test1(self) -> None:
        """
        No matches.
        """
        code = "import test as te"
        expected = code
        self._helper(code, expected)

    def _helper(self, actual: str, expected: str) -> None:
        """
        ......
        """
        assert expected == actual


# #############################################################################
# TestAnother
# #############################################################################


# Comment before initializing.
class TestAnother:
    pass


if __name__ == "main":
    txt = "hello"
    m = re.search("\s", txt)
    n = nltk.word_tokenize(txt)
    hdbg.dassert_path_exists("filename.txt")
