import difflib
import logging
import os

import pytest

import dev_scripts_helpers.notebooks.process_jupytext as dshnprju
import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_process_jupytext
# #############################################################################


class Test_process_jupytext(hunitest.TestCase):

    @pytest.mark.slow("~7 seconds.")
    def test_end_to_end(self) -> None:
        """
        Test file syncing with `process_jupytext.py` end-to-end.

        Test that `process_jupytext.py` updates an `.ipynb` notebook when the
        paired `.py` file is changed.
        - Create two paired files: `.py` and `.ipynb`
        - Change the code in the `.py` file
        - Run `sync` and `test` in `process_jupytext.py`
        - Check that the `.ipynb` file was updated
        """
        file_name = "notebook_for_test"
        # Create .py and .ipynb files for testing.
        py_text = hio.from_file(
            os.path.join(self.get_input_dir(), f"{file_name}.py.txt")
        )
        ipynb_text = hio.from_file(
            os.path.join(self.get_input_dir(), f"{file_name}.ipynb.txt")
        )
        file_path = os.path.join(self.get_scratch_space(), f"{file_name}.py")
        ipynb_path = os.path.join(self.get_scratch_space(), f"{file_name}.ipynb")
        hio.to_file(file_path, py_text)
        hio.to_file(ipynb_path, ipynb_text)
        # Pair files.
        cmd = f"jupytext --set-formats ipynb,py {ipynb_path}"
        hsystem.system(cmd)
        # Add a string to python file to check if sync works.
        py_text += "\na = 0"
        hio.to_file(file_path, py_text)
        # Run processor.
        cmd = f"$(find -wholename '*dev_scripts_helpers/notebooks/process_jupytext.py') -f {file_path} --action sync 2>&1"
        hsystem.system(cmd)
        cmd = f"$(find -wholename '*dev_scripts_helpers/notebooks/process_jupytext.py') -f {file_path} --action test 2>&1"
        hsystem.system(cmd)
        # Check that notebook content was changed.
        new_ipynb_text = hio.from_file(ipynb_path)
        differ = difflib.Differ()
        diffs = []
        old_lines = ipynb_text.splitlines()
        new_lines = new_ipynb_text.splitlines()
        for line in list(differ.compare(old_lines, new_lines)):
            if not line.startswith(" "):
                diffs.append(line)
        self.check_string("\n".join(diffs))

    def test_is_jupytext_version_different_true(self) -> None:
        """
        Test jupytext version comparison: when the versions are different.
        """
        txt = """
--- expected
+++ actual
@@ -5,7 +5,7 @@
 #       extension: .py
 #       format_name: percent
 #       format_version: '1.3'
-#       jupytext_version: 1.3.3
+#       jupytext_version: 1.3.0
 #   kernelspec:
 #     display_name: Python [conda env:.conda-amp_develop] *
 #     language: python
"""
        self.assertTrue(dshnprju._is_jupytext_version_different(txt))

    def test_is_jupytext_version_different_false(self) -> None:
        """
        Test jupytext version comparison: when the versions are not different.
        """
        txt = """
--- expected
+++ actual
@@ -5,7 +5,7 @@
 #       extension: .py
-#       format_name: percent
+#       format_name: plus
 #       format_version: '1.3'
 #       jupytext_version: 1.3.3
 #   kernelspec:
 #     display_name: Python [conda env:.conda-amp_develop] *
 #     language: python
"""
        self.assertFalse(dshnprju._is_jupytext_version_different(txt))
