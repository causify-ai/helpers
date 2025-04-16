import logging
import os
import re
import shutil
from typing import Tuple

import pytest

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import linters.base as libase

_LOG = logging.getLogger(__name__)


# #############################################################################
## base.py
# #############################################################################


class Test_linter_py1(hunitest.TestCase):

    def write_input_file(self, txt: str, file_name: str) -> Tuple[str, str]:
        """
        Write test content to the file.

        :param txt: the content of the file
        :param file_name: the name of the file
        :return: the name of the parent directory and the name of the
            file
        """
        # Get the path to the scratch space.
        dir_name = self.get_scratch_space()
        hdbg.dassert_is_not(file_name, None)
        file_name = os.path.join(dir_name, file_name)
        file_name = os.path.abspath(file_name)
        hio.to_file(file_name, txt)
        return dir_name, file_name

    def run_linter(self, txt: str, file_name: str, as_system_call: bool) -> str:
        """
        Run the processing pipeline:

          - write the text content to the file
          - run linter on the file
          - log the output

        :param txt: the content of the file
        :param file_name: the name of the file
        :param as_system_call: if the command should be run as a system call
        :return: the output log of the processing
        """
        # Create file to lint.
        dir_name, file_name = self.write_input_file(txt, file_name)
        # Run.
        dir_name = self.get_scratch_space()
        linter_log = "linter.log"
        linter_log = os.path.abspath(os.path.join(dir_name, linter_log))
        output = self._run_linter(file_name, linter_log, as_system_call)
        # Modify the outcome for reproducibility.
        output = re.sub(r"[0-9]{2}:[0-9]{2}:[0-9]{2} - ", r"HH:MM:SS - ", output)
        output = re.sub(
            r"(\.py.*:)([0-9]+)",
            r"\1{LINE_NUM}",
            output,
        )
        return output

    # #########################################################################

    @pytest.mark.slow("About 24 sec")
    def test_linter1(self) -> None:
        """
        Run Linter as executable on Python code.
        """
        txt = self._get_horrible_python_code1()
        # Run.
        file_name = "input.py"
        as_system_call = True
        output = self.run_linter(txt, file_name, as_system_call)
        # Check.
        self.check_string(output, purify_text=True)

    @pytest.mark.slow("About 18 sec")
    def test_linter2(self) -> None:
        """
        Run Linter as library on Python code.
        """
        txt = self._get_horrible_python_code1()
        # Run.
        file_name = "input.py"
        as_system_call = False
        output = self.run_linter(txt, file_name, as_system_call)
        # Check.
        self.check_string(output, purify_text=True)

    # #########################################################################

    # TODO(heanh): Remove the skip when the dockerized executable issue is resolved.
    @pytest.mark.slow("About 6 sec")
    @pytest.mark.skip(
        "Skip due to issue related to dockerized executable. See HelpersTask553."
    )
    def test_linter_md1(self) -> None:
        """
        Run Linter as executable on Markdown.
        """
        txt = r"""
# Good.
- Good time management
  1. choose the right tasks
    - Avoid non-essential tasks

## Bad
-  Hello
    - World
        """
        # Run.
        file_name = "hello.md"
        as_system_call = True
        output = self.run_linter(txt, file_name, as_system_call)
        # Remove the line:
        # '12-16_14:59 ^[[33mWARNING^[[0m: _refresh_toc   :138 : No tags for table'
        output = hunitest.filter_text("No tags for table", output)
        # Check.
        self.check_string(output, purify_text=True)

    # TODO(heanh): Remove the skip when the dockerized executable issue is resolved.
    @pytest.mark.slow("About 6 sec")
    @pytest.mark.skip(
        "Skip due to issue related to dockerized executable. See HelpersTask553."
    )
    def test_linter_md2(self) -> None:
        """
        Run Linter as executable on Markdown file with a fenced block.
        """
        txt = r"""
# Header1
```text
test text
nothing should be changed
```
        """
        # Run.
        file_name = "hello.md"
        as_system_call = True
        output = self.run_linter(txt, file_name, as_system_call)
        # Remove the line:
        # '12-16_14:59 ^[[33mWARNING^[[0m: _refresh_toc   :138 : No tags for table'
        output = hunitest.filter_text("No tags for table", output)
        # Check.
        self.check_string(output, purify_text=True)

    def test_linter_txt1(self) -> None:
        """
        Run Linter as executable on a txt file with empty lines at the end.

        The content of txt files is not linted, see DevToolsTask553.
        """
        txt = r"""
//src/linters/test/test_precommit.py
//src/linters/utils.py
//src/zenhub_stats/notebooks/stats.py
//src/zenhub_stats/stats.py
//src/zenhub_stats/test/test_stats.py
//src/zenhub_stats/zenhub_typing/__init__.py
//src/zenhub_stats/zenhub_typing/issue.py







"""
        # Run.
        file_name = "test.txt"
        as_system_call = True
        output = self.run_linter(txt, file_name, as_system_call)
        # Remove the line:
        # '12-16_14:59 ^[[33mWARNING^[[0m: _refresh_toc   :138 : No tags for table'
        output = hunitest.filter_text("No tags for table", output)
        # Check.
        self.check_string(output, purify_text=True)

    def test_linter_txt2(self) -> None:
        """
        Run Linter as executable on a txt file without empty lines.

        The content of txt files is not linted, see DevToolsTask553.
        """
        txt = r"""
//src/linters/test/test_precommit.py
//src/linters/utils.py
//src/zenhub_stats/notebooks/stats.py
//src/zenhub_stats/stats.py
//src/zenhub_stats/test/test_stats.py
//src/zenhub_stats/zenhub_typing/__init__.py
//src/zenhub_stats/zenhub_typing/issue.py
"""
        # Run.
        file_name = "test.txt"
        as_system_call = True
        output = self.run_linter(txt, file_name, as_system_call)
        # Remove the line:
        # '12-16_14:59 ^[[33mWARNING^[[0m: _refresh_toc   :138 : No tags for table'
        output = hunitest.filter_text("No tags for table", output)
        # Check.
        self.check_string(output, purify_text=True)

    @pytest.mark.slow("About 14 sec")
    def test_DevToolsTask408(self) -> None:
        """
        Test pylint's string formatting warnings.
        """
        txt = """
import logging

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)

s = "hello"
a = "Checking {}".format(s)
_LOG.debug("Checking '%s'.", s)
hdbg.dassert(s.startswith("h"), "Checking '%s'.", s)
"""
        # Run.
        file_name = "input.py"
        as_system_call = True
        output = self.run_linter(txt, file_name, as_system_call)
        # Check.
        self.check_string(output, purify_text=True)

    @pytest.mark.slow("About 6 sec")
    def test_linter_ipynb1(self) -> None:
        """
        Run Linter as executable on a notebook.
        """
        contents_ipynb = self._get_ipynb_contents1()
        # Run.
        file_name = "input.ipynb"
        as_system_call = True
        output = self.run_linter(contents_ipynb, file_name, as_system_call)
        # Check.
        self.check_string(output, purify_text=True)

    @pytest.mark.slow("About 19 sec")
    def test_linter_ipynb_paired1(self) -> None:
        """
        Run Linter as executable on a Python file with a paired notebook.
        """
        for file_name in os.listdir(self.get_input_dir()):
            input_file_path = f"{self.get_input_dir()}/{file_name}"
            if not os.path.isfile(input_file_path):
                continue
            scratch_file_path = f"{self.get_scratch_space()}/{file_name}"
            shutil.copy(input_file_path, scratch_file_path)
        # Lint a Python file.
        file_path_py = f"{self.get_scratch_space()}/input.py"
        # Run.
        cmd_as_str = f"linters/base.py --files {file_path_py}"
        suppress_output = _LOG.getEffectiveLevel() > logging.DEBUG
        hsystem.system(
            cmd_as_str,
            abort_on_error=False,
            suppress_output=suppress_output,
        )
        cmd_rm = f"git restore --staged {file_path_py}"
        hsystem.system(cmd_rm, abort_on_error=False)
        # Examine the effect on the paired notebook.
        file_path_ipynb = f"{self.get_scratch_space()}/input.ipynb"
        output = hio.from_file(file_path_ipynb)
        # Check.
        self.check_string(output, purify_text=True)

    @pytest.mark.slow("About 7 sec")
    def test_linter_ipynb_paired2(self) -> None:
        """
        Run Linter as executable on a notebook with a paired Python file.
        """
        for file_name in os.listdir(self.get_input_dir()):
            input_file_path = f"{self.get_input_dir()}/{file_name}"
            if not os.path.isfile(input_file_path):
                continue
            scratch_file_path = f"{self.get_scratch_space()}/{file_name}"
            shutil.copy(input_file_path, scratch_file_path)
        # Lint a notebook.
        file_path_ipynb = f"{self.get_scratch_space()}/input.ipynb"
        # Run.
        cmd_as_str = f"linters/base.py --files {file_path_ipynb}"
        suppress_output = _LOG.getEffectiveLevel() > logging.DEBUG
        hsystem.system(
            cmd_as_str,
            abort_on_error=False,
            suppress_output=suppress_output,
        )
        cmd_rm = f"git restore --staged {file_path_ipynb}"
        hsystem.system(cmd_rm, abort_on_error=False)
        # Examine the effect on the paired Python file.
        file_path_py = f"{self.get_scratch_space()}/input.py"
        output = hio.from_file(file_path_py)
        # Check.
        self.check_string(output, purify_text=True)

    # #########################################################################

    @staticmethod
    def _get_horrible_python_code1() -> str:
        txt = r'''
from typing import Any, List
import helpers.hdbg as hdbg
import helpers.hcache as hcac
import helpers.hio as io
import nltk
import pandas as pd
import python
import tqdm.autonotebook as tqdm

# hcac._get_cache_types()
hcac._get_cache_types()
x = "hcac._get_cache_types()"

def func(a: str, lst: List[str]) -> Any:
    """First comment line."""
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
    io.dassert_is_valid_file_name("test.py")
    b = """
    Before separating line.
    ##########################################################################
    Comments inside string.
    ##########################################################################
    """
    result_df = df.loc[a+b:]
    return result_df

def func3(a: str) -> str:
    """
    Generate "random returns". Use lag + noise as predictor.
    """
    if a is not None:
        assert isinstance(a, str), (f"You passed '{a}' or type '{type(a)}'"
            "instead of str")
    ## [C0330(bad-continuation), ] Wrong hanging indentation before
    ##   block (add 4 spaces).
    return a


# #############################################################################
# New part.
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
        For reference, let

          - N = 2
          - M = 3
        """
        return a

    def _private_regular_method(self, a: str) -> str:
        """
        Read csv file(s) or pd.DataFrame in batches and then constructs the
        financial data structure in the form of a DataFrame. The csv file or
        DataFrame must have only 3 columns: date_time, price, & volume.
        """
        # Returning
        return a

##############################################################################
# New part 2.
##############################################################################

class TestReplaceShortImportInCode:
    def _helper(self, actual: str, expected: str) -> None:
        """
        ......
        """
        assert expected == actual

    def test1(self) -> None:
        """
        No matches.
        """
        code = "import test as te"
        expected = code
        self._helper(code, expected)

# Comment before initializing.
class TestAnother():
    pass

if __name__ == "main":
    txt = "hello"
    m = re.search("\s", txt)
    n = nltk.word_tokenize(txt)
    hdbg.dassert_path_exists("filename.txt")
        '''
        return txt

    @staticmethod
    def _get_ipynb_contents1() -> str:
        contents_ipynb = r"""
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Imports"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import re\n",
    "\n",
    "# TODO: Fix.\n",
    "res = re.findall(r\"[a-z]+\", \"some text\")\n",
    "\n",
    "\n"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
        """
        return contents_ipynb

    def _run_linter(
        self,
        file_name: str,
        linter_log: str,
        as_system_call: bool,
    ) -> str:
        if as_system_call:
            cmd = []
            cmd.append(f"linters/base.py --files {file_name}")
            cmd_as_str = " ".join(cmd)
            ## We need to ignore the errors reported by the script, since it
            ## represents how many lints were found.
            suppress_output = _LOG.getEffectiveLevel() > logging.DEBUG
            hsystem.system(
                cmd_as_str,
                abort_on_error=False,
                suppress_output=suppress_output,
                output_file=linter_log,
            )
            cmd_rm = f"git restore --staged {file_name}"
            hsystem.system(cmd_rm, abort_on_error=False)
        else:
            logger_verbosity = hdbg.get_logger_verbosity()
            parser = libase._parse()
            args = parser.parse_args(
                [
                    "-f",
                    file_name,
                    "--linter_log",
                    linter_log,
                    # TODO(gp): Avoid to call the logger.
                    "-v",
                    "ERROR",
                ]
            )
            libase._main(args)
            hdbg.init_logger(logger_verbosity)

        # Read log.
        _LOG.debug("linter_log=%s", linter_log)
        txt = hio.from_file(linter_log)
        # Process log.
        output = []
        output.append("# linter log")
        for line in txt.split("\n"):
            # Remove the line:
            #   Cmd line='.../linter.py -f input.py --linter_log ./linter.log'
            if "cmd line=" in line:
                continue
            # Filter out code rate because of #2241.
            if "Your code has been rated at" in line:
                continue
            output.append(line)
        # Read output.
        _LOG.debug("file_name=%s", file_name)
        output.append("# linter file")
        txt = hio.from_file(file_name)
        output.extend(txt.split("\n"))
        # //////////////
        output_as_str = "\n".join(output)
        return output_as_str