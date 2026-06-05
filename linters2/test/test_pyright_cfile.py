import json
from typing import Any, Dict

import helpers.hunit_test as hunitest
import helpers.hsystem as hsystem
import linters2.pyright_cfile as lpyrcfil


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
        actual = lpyrcfil._transform_pyright_output(json_str)
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
        expected = "test.py:6:11: information: unused variable 'x'"
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
        expected = "module.py:1:1: information: type mismatch\nmodule.py:11:6: information: undefined name"
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
        expected = "src/app.py:43:21: information: Expression is not defined"
        # Run test.
        self.helper(json_data, expected)

    def test6(self) -> None:
        """
        Test message with newlines converted to commas.
        """
        # Prepare inputs.
        json_data = {
            "generalDiagnostics": [
                {
                    "file": "test.py",
                    "message": "error line 1\nerror line 2",
                    "range": {"start": {"line": 0, "character": 0}},
                }
            ]
        }
        # Prepare outputs.
        expected = "test.py:1:1: information: error line 1, error line 2"
        # Run test.
        self.helper(json_data, expected)

    def test7(self) -> None:
        """
        Test long message truncated to 100 characters with ellipsis.
        """
        # Prepare inputs.
        long_msg = "a" * 105
        json_data = {
            "generalDiagnostics": [
                {
                    "file": "test.py",
                    "message": long_msg,
                    "range": {"start": {"line": 0, "character": 0}},
                }
            ]
        }
        # Prepare outputs.
        expected = "test.py:1:1: information: " + "a" * 97 + "..."
        # Run test.
        self.helper(json_data, expected)

    def test8(self) -> None:
        """
        Test message with newlines and long length.
        """
        # Prepare inputs.
        msg = "error " + "line\n" * 20
        json_data = {
            "generalDiagnostics": [
                {
                    "file": "test.py",
                    "message": msg,
                    "range": {"start": {"line": 0, "character": 0}},
                }
            ]
        }
        # Prepare outputs.
        expected = (
            "test.py:1:1: information: "
            "error line, line, line, line, line, line, line, line, "
            "line, line, line, line, line, line, line, l..."
        )
        # Run test.
        self.helper(json_data, expected)

    def test9(self) -> None:
        """
        Test with real-world pyright message with indented newlines.
        """
        # Prepare inputs - real message from pyright with indented newlines
        json_data = {
            "generalDiagnostics": [
                {
                    "file": "convert_table.py",
                    "message": (
                        'Argument of type "list[str]" cannot be assigned to '
                        'parameter "columns" of type "Axes | None"\n'
                        '  Type "list[str]" is not assignable to type '
                        '"Axes | None"\n'
                        '    "list[str]" is not assignable to '
                        '"ExtensionArray"'
                    ),
                    "range": {"start": {"line": 137, "character": 36}},
                }
            ]
        }
        # Prepare outputs.
        expected = (
            "convert_table.py:138:37: information: "
            'Argument of type "list[str]" cannot be assigned to '
            'parameter "columns" of type "Axes | None",   T...'
        )
        # Run test.
        self.helper(json_data, expected)


# #############################################################################
# Test_script_help_command
# #############################################################################


class Test_script_help_command(hunitest.TestCase):
    """
    Test the actual execution of pyright_cfile.py script with -h flag.
    """

    def test1(self) -> None:
        """
        Test that pyright_cfile.py -h returns rc = 0.
        """
        # Prepare inputs.
        cmd = "python linters2/pyright_cfile.py -h"
        # Run test.
        rc = hsystem.system(cmd, suppress_output=True, abort_on_error=False)
        # Check outputs.
        self.assertEqual(rc, 0)
