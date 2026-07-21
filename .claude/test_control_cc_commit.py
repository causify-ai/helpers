"""
Unit tests for control_cc_commit.py
"""

from typing import Dict

import helpers.hunit_test as hunitest

# Import the module to test
import control_cc_commit as cc_control


class Test_enable_git_commands(hunitest.TestCase):
    """Test cases for _enable_git_commands function."""

    def test_enable_when_denials_exist(self) -> None:
        """Test enabling when git denials are in the deny list."""
        settings: Dict = {
            "permissions": {
                "deny": [
                    "Bash(*git commit:*)",
                    "Bash(*git commit -m *)",
                    "Bash(*git push:*)",
                    "SomeOtherDenial",
                ]
            }
        }
        result = cc_control._enable_git_commands(settings)
        self.assertTrue(result)
        self.assertEqual(settings["permissions"]["deny"], ["SomeOtherDenial"])

    def test_enable_when_no_denials_exist(self) -> None:
        """Test enabling when there are no git denials to remove."""
        settings: Dict = {
            "permissions": {"deny": ["SomeOtherDenial"]}
        }
        result = cc_control._enable_git_commands(settings)
        self.assertFalse(result)
        self.assertEqual(settings["permissions"]["deny"], ["SomeOtherDenial"])

    def test_enable_when_partial_denials_exist(self) -> None:
        """Test enabling when only some git denials are present."""
        settings: Dict = {
            "permissions": {
                "deny": [
                    "Bash(*git commit:*)",
                    "SomeOtherDenial",
                ]
            }
        }
        result = cc_control._enable_git_commands(settings)
        self.assertTrue(result)
        self.assertEqual(settings["permissions"]["deny"], ["SomeOtherDenial"])

    def test_enable_with_empty_deny_list(self) -> None:
        """Test enabling when deny list is empty."""
        settings: Dict = {"permissions": {"deny": []}}
        result = cc_control._enable_git_commands(settings)
        self.assertFalse(result)
        self.assertEqual(settings["permissions"]["deny"], [])

    def test_enable_when_no_permissions_key(self) -> None:
        """Test enabling when permissions key doesn't exist."""
        settings: Dict = {}
        result = cc_control._enable_git_commands(settings)
        self.assertFalse(result)
        self.assertIn("permissions", settings)
        self.assertEqual(settings["permissions"]["deny"], [])

    def test_enable_when_no_deny_key(self) -> None:
        """Test enabling when deny key doesn't exist under permissions."""
        settings: Dict = {"permissions": {}}
        result = cc_control._enable_git_commands(settings)
        self.assertFalse(result)
        self.assertEqual(settings["permissions"]["deny"], [])


class Test_disable_git_commands(hunitest.TestCase):
    """Test cases for _disable_git_commands function."""

    def test_disable_when_denials_dont_exist(self) -> None:
        """Test disabling when git denials don't already exist."""
        settings: Dict = {
            "permissions": {"deny": ["SomeOtherDenial"]}
        }
        result = cc_control._disable_git_commands(settings)
        self.assertTrue(result)
        expected_denials = [
            "SomeOtherDenial",
            "Bash(*git commit:*)",
            "Bash(*git commit -m *)",
            "Bash(*git push:*)",
        ]
        # Check that all expected denials are present (order may vary).
        self.assertEqual(set(settings["permissions"]["deny"]), set(expected_denials))

    def test_disable_when_all_denials_exist(self) -> None:
        """Test disabling when all git denials already exist."""
        settings: Dict = {
            "permissions": {
                "deny": [
                    "Bash(*git commit:*)",
                    "Bash(*git commit -m *)",
                    "Bash(*git push:*)",
                ]
            }
        }
        result = cc_control._disable_git_commands(settings)
        self.assertFalse(result)
        self.assertEqual(
            set(settings["permissions"]["deny"]),
            set(cc_control._GIT_DENIALS),
        )

    def test_disable_when_partial_denials_exist(self) -> None:
        """Test disabling when only some git denials already exist."""
        settings: Dict = {
            "permissions": {
                "deny": [
                    "Bash(*git commit:*)",
                    "SomeOtherDenial",
                ]
            }
        }
        result = cc_control._disable_git_commands(settings)
        self.assertTrue(result)
        expected_denials = [
            "Bash(*git commit:*)",
            "SomeOtherDenial",
            "Bash(*git commit -m *)",
            "Bash(*git push:*)",
        ]
        self.assertEqual(set(settings["permissions"]["deny"]), set(expected_denials))

    def test_disable_with_empty_deny_list(self) -> None:
        """Test disabling when deny list is empty."""
        settings: Dict = {"permissions": {"deny": []}}
        result = cc_control._disable_git_commands(settings)
        self.assertTrue(result)
        self.assertEqual(set(settings["permissions"]["deny"]), set(cc_control._GIT_DENIALS))

    def test_disable_when_no_permissions_key(self) -> None:
        """Test disabling when permissions key doesn't exist."""
        settings: Dict = {}
        result = cc_control._disable_git_commands(settings)
        self.assertTrue(result)
        self.assertIn("permissions", settings)
        self.assertEqual(set(settings["permissions"]["deny"]), set(cc_control._GIT_DENIALS))

    def test_disable_when_no_deny_key(self) -> None:
        """Test disabling when deny key doesn't exist under permissions."""
        settings: Dict = {"permissions": {}}
        result = cc_control._disable_git_commands(settings)
        self.assertTrue(result)
        self.assertEqual(set(settings["permissions"]["deny"]), set(cc_control._GIT_DENIALS))

    def test_disable_preserves_other_denials(self) -> None:
        """Test that disabling preserves unrelated denials."""
        other_denials = ["Bash(*rm:*)", "Edit(*dangerous*)"]
        settings: Dict = {"permissions": {"deny": other_denials.copy()}}
        result = cc_control._disable_git_commands(settings)
        self.assertTrue(result)
        # All denials should be present.
        expected = set(other_denials + cc_control._GIT_DENIALS)
        self.assertEqual(set(settings["permissions"]["deny"]), expected)
