import json
from typing import Any, Dict

import helpers.hunit_test as hunitest
import dev_scripts_helpers.pyright_cfile as dpycfile


# #############################################################################
# Test__transform_pyright_output
# #############################################################################


class Test__transform_pyright_output(hunitest.TestCase):
    """
    Test the transformation of pyright JSON output to cfile format.
    """

    def helper(self, json_data: Dict[str, Any], expected: str) -> None:
        """
        Test helper for _transform_pyright_output.

        :param json_data: Dictionary representing pyright JSON output
        :param expected: Expected cfile-formatted output
        """
        json_str = json.dumps(json_data)
        actual = dpycfile._transform_pyright_output(json_str)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test single diagnostic with standard format.
        """
        # Prepare inputs.
        json_data = {
            "generalDiagnostics": [
                {
                    "file": "test.py",
                    "message": "unused variable 'x'",
                    "range": {"start": {"line": 5, "character": 10}},
                }
            ]
        }
        # Prepare outputs.
        expected = "test.py:6:11: unused variable 'x'"
        # Run test.
        self.helper(json_data, expected)

    def test2(self) -> None:
        """
        Test multiple diagnostics.
        """
        # Prepare inputs.
        json_data = {
            "generalDiagnostics": [
                {
                    "file": "module.py",
                    "message": "type mismatch",
                    "range": {"start": {"line": 0, "character": 0}},
                },
                {
                    "file": "module.py",
                    "message": "undefined name",
                    "range": {"start": {"line": 10, "character": 5}},
                },
            ]
        }
        # Prepare outputs.
        expected = (
            "module.py:1:1: type mismatch\n"
            "module.py:11:6: undefined name"
        )
        # Run test.
        self.helper(json_data, expected)

    def test3(self) -> None:
        """
        Test empty diagnostics list.
        """
        # Prepare inputs.
        json_data = {"generalDiagnostics": []}
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(json_data, expected)

    def test4(self) -> None:
        """
        Test with missing generalDiagnostics key.
        """
        # Prepare inputs.
        json_data = {}
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(json_data, expected)

    def test5(self) -> None:
        """
        Test with zero-indexed positions converted to 1-indexed.
        """
        # Prepare inputs.
        json_data = {
            "generalDiagnostics": [
                {
                    "file": "src/app.py",
                    "message": "Expression is not defined",
                    "range": {"start": {"line": 42, "character": 20}},
                }
            ]
        }
        # Prepare outputs.
        expected = "src/app.py:43:21: Expression is not defined"
        # Run test.
        self.helper(json_data, expected)
