"""
Unit tests for to_github.py.

Import as:

import dev_scripts_helpers.github.test.test_to_github as dscghttto
"""

from typing import Any, Tuple
from unittest import mock

import helpers.hunit_test as hunitest

import dev_scripts_helpers.github.to_github as dshgtogi


def _mock_system_to_string(
    cmd: str, *_args: Any, **_kwargs: Any
) -> Tuple[int, str]:
    """
    Stand in for `hsystem.system_to_string()` for the `git` commands used by
    `_get_github_url()`.

    :param cmd: command string, dispatched on to decide the canned output
    :return: `(return_code, output)` tuple mimicking a successful `git` call
    """
    if "rev-parse" in cmd:
        output = "/repo"
    elif "remote get-url" in cmd:
        output = "git@github.com:owner/repo.git"
    elif "branch --show-current" in cmd:
        output = "main"
    else:
        raise ValueError(f"Unexpected command: {cmd}")
    return (0, output)


# #############################################################################
# Test_check_url_exists
# #############################################################################


class Test_check_url_exists(hunitest.TestCase):
    """
    Test `to_github._check_url_exists()` function.
    """

    def test1(self) -> None:
        """
        Test that a URL returning HTTP 200 is reported as existing.
        """
        # Prepare inputs.
        url = "https://github.com/owner/repo/blob/main/file.py"
        mock_response = mock.Mock(status_code=200)
        # Run test.
        with mock.patch(
            "dev_scripts_helpers.github.to_github.requests.get",
            return_value=mock_response,
        ) as mock_get:
            actual = dshgtogi._check_url_exists(url)
        # Check outputs.
        self.assertTrue(actual)
        mock_get.assert_called_once_with(url, timeout=10)

    def test2(self) -> None:
        """
        Test that a URL returning HTTP 404 is reported as not existing.
        """
        # Prepare inputs.
        url = "https://github.com/owner/repo/blob/main/missing.py"
        mock_response = mock.Mock(status_code=404)
        # Run test.
        with mock.patch(
            "dev_scripts_helpers.github.to_github.requests.get",
            return_value=mock_response,
        ):
            actual = dshgtogi._check_url_exists(url)
        # Check outputs.
        self.assertFalse(actual)


# #############################################################################
# Test_get_github_url
# #############################################################################


class Test_get_github_url(hunitest.TestCase):
    """
    Test `to_github._get_github_url()` function, focused on the
    `check_exists` option.
    """

    def test1(self) -> None:
        """
        Test that `check_exists=False` (the default) never calls out to
        check the URL.
        """
        # Prepare inputs.
        file_path = "/repo/some/file.py"
        # Prepare outputs.
        expected = "https://github.com/owner/repo/blob/main/some/file.py"
        # Run test.
        with (
            mock.patch(
                "helpers.hsystem.system_to_string",
                side_effect=_mock_system_to_string,
            ),
            mock.patch(
                "dev_scripts_helpers.github.to_github.requests.get"
            ) as mock_get,
        ):
            actual = dshgtogi._get_github_url(
                file_path=file_path, use_master=False
            )
        # Check outputs.
        self.assertEqual(actual, expected)
        mock_get.assert_not_called()

    def test2(self) -> None:
        """
        Test that `check_exists=True` with a resolving URL returns the URL
        without raising.
        """
        # Prepare inputs.
        file_path = "/repo/some/file.py"
        mock_response = mock.Mock(status_code=200)
        # Prepare outputs.
        expected = "https://github.com/owner/repo/blob/main/some/file.py"
        # Run test.
        with (
            mock.patch(
                "helpers.hsystem.system_to_string",
                side_effect=_mock_system_to_string,
            ),
            mock.patch(
                "dev_scripts_helpers.github.to_github.requests.get",
                return_value=mock_response,
            ),
        ):
            actual = dshgtogi._get_github_url(
                file_path=file_path, use_master=False, check_exists=True
            )
        # Check outputs.
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test that `check_exists=True` with a non-resolving URL raises
        `AssertionError`.
        """
        # Prepare inputs.
        file_path = "/repo/some/file.py"
        mock_response = mock.Mock(status_code=404)
        # Prepare outputs.
        expected = (
            "GitHub URL does not resolve: "
            "'https://github.com/owner/repo/blob/main/some/file.py'"
        )
        # Run test.
        with (
            mock.patch(
                "helpers.hsystem.system_to_string",
                side_effect=_mock_system_to_string,
            ),
            mock.patch(
                "dev_scripts_helpers.github.to_github.requests.get",
                return_value=mock_response,
            ),
        ):
            with self.assertRaises(AssertionError) as cm:
                dshgtogi._get_github_url(
                    file_path=file_path, use_master=False, check_exists=True
                )
        # Check outputs.
        self.assertIn(expected, str(cm.exception))


# #############################################################################
# Test_parse
# #############################################################################


class Test_parse(hunitest.TestCase):
    """
    Test `_parse()` function.
    """

    def test1(self) -> None:
        """
        Test parser sets `check_exists` to `False` by default.
        """
        # Prepare inputs.
        arg_list = ["--input", "helpers/hdbg.py"]
        # Run test.
        parser = dshgtogi._parse()
        args = parser.parse_args(arg_list)
        # Check outputs.
        self.assertFalse(args.check_exists)

    def test2(self) -> None:
        """
        Test parser sets `check_exists` to `True` when `--check_exists` is
        passed.
        """
        # Prepare inputs.
        arg_list = ["--input", "helpers/hdbg.py", "--check_exists"]
        # Run test.
        parser = dshgtogi._parse()
        args = parser.parse_args(arg_list)
        # Check outputs.
        self.assertTrue(args.check_exists)
