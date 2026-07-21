from typing import Dict

import helpers.hunit_test as hunitest
import control_cc_commit as cc_control


# #############################################################################
# Test_enable_git_commands
# #############################################################################


class Test_enable_git_commands(hunitest.TestCase):
    """
    Test cases for _enable_git_commands function.
    """

    def helper(
        self,
        settings: Dict,
        expected_result: bool,
        expected_deny_list: list,
    ) -> None:
        """
        Test helper for _enable_git_commands.

        :param settings: Input settings dictionary
        :param expected_result: Expected return value
        :param expected_deny_list: Expected deny list after execution
        """
        # Run test.
        result = cc_control._enable_git_commands(settings)
        # Check outputs.
        self.assertEqual(result, expected_result)
        self.assertEqual(settings["permissions"]["deny"], expected_deny_list)

    def test1(self) -> None:
        """
        Test enabling when all git denials are in the deny list.
        """
        # Prepare inputs.
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
        # Prepare outputs.
        expected_result = True
        expected_deny_list = ["SomeOtherDenial"]
        # Run test.
        self.helper(settings, expected_result, expected_deny_list)

    def test2(self) -> None:
        """
        Test enabling when there are no git denials to remove.
        """
        # Prepare inputs.
        settings: Dict = {"permissions": {"deny": ["SomeOtherDenial"]}}
        # Prepare outputs.
        expected_result = False
        expected_deny_list = ["SomeOtherDenial"]
        # Run test.
        self.helper(settings, expected_result, expected_deny_list)

    def test3(self) -> None:
        """
        Test enabling when only some git denials are present.
        """
        # Prepare inputs.
        settings: Dict = {
            "permissions": {
                "deny": [
                    "Bash(*git commit:*)",
                    "SomeOtherDenial",
                ]
            }
        }
        # Prepare outputs.
        expected_result = True
        expected_deny_list = ["SomeOtherDenial"]
        # Run test.
        self.helper(settings, expected_result, expected_deny_list)

    def test4(self) -> None:
        """
        Test enabling when deny list is empty.
        """
        # Prepare inputs.
        settings: Dict = {"permissions": {"deny": []}}
        # Prepare outputs.
        expected_result = False
        expected_deny_list = []
        # Run test.
        self.helper(settings, expected_result, expected_deny_list)

    def test5(self) -> None:
        """
        Test enabling when permissions key doesn't exist.
        """
        # Prepare inputs.
        settings: Dict = {}
        # Prepare outputs.
        expected_result = False
        expected_deny_list = []
        # Run test.
        self.helper(settings, expected_result, expected_deny_list)

    def test6(self) -> None:
        """
        Test enabling when deny key doesn't exist under permissions.
        """
        # Prepare inputs.
        settings: Dict = {"permissions": {}}
        # Prepare outputs.
        expected_result = False
        expected_deny_list = []
        # Run test.
        self.helper(settings, expected_result, expected_deny_list)


# #############################################################################
# Test_disable_git_commands
# #############################################################################


class Test_disable_git_commands(hunitest.TestCase):
    """
    Test cases for _disable_git_commands function.
    """

    def helper(
        self,
        settings: Dict,
        expected_result: bool,
        expected_deny_set: set,
    ) -> None:
        """
        Test helper for _disable_git_commands.

        :param settings: Input settings dictionary
        :param expected_result: Expected return value
        :param expected_deny_set: Expected deny list as a set after execution
        """
        # Run test.
        result = cc_control._disable_git_commands(settings)
        # Check outputs.
        self.assertEqual(result, expected_result)
        self.assertEqual(set(settings["permissions"]["deny"]), expected_deny_set)

    def test1(self) -> None:
        """
        Test disabling when git denials don't already exist.
        """
        # Prepare inputs.
        settings: Dict = {"permissions": {"deny": ["SomeOtherDenial"]}}
        # Prepare outputs.
        expected_result = True
        expected_deny_set = {
            "SomeOtherDenial",
            "Bash(*git commit:*)",
            "Bash(*git commit -m *)",
            "Bash(*git push:*)",
        }
        # Run test.
        self.helper(settings, expected_result, expected_deny_set)

    def test2(self) -> None:
        """
        Test disabling when all git denials already exist.
        """
        # Prepare inputs.
        settings: Dict = {
            "permissions": {
                "deny": [
                    "Bash(*git commit:*)",
                    "Bash(*git commit -m *)",
                    "Bash(*git push:*)",
                ]
            }
        }
        # Prepare outputs.
        expected_result = False
        expected_deny_set = set(cc_control._GIT_DENIALS)
        # Run test.
        self.helper(settings, expected_result, expected_deny_set)

    def test3(self) -> None:
        """
        Test disabling when only some git denials already exist.
        """
        # Prepare inputs.
        settings: Dict = {
            "permissions": {
                "deny": [
                    "Bash(*git commit:*)",
                    "SomeOtherDenial",
                ]
            }
        }
        # Prepare outputs.
        expected_result = True
        expected_deny_set = {
            "Bash(*git commit:*)",
            "SomeOtherDenial",
            "Bash(*git commit -m *)",
            "Bash(*git push:*)",
        }
        # Run test.
        self.helper(settings, expected_result, expected_deny_set)

    def test4(self) -> None:
        """
        Test disabling when deny list is empty.
        """
        # Prepare inputs.
        settings: Dict = {"permissions": {"deny": []}}
        # Prepare outputs.
        expected_result = True
        expected_deny_set = set(cc_control._GIT_DENIALS)
        # Run test.
        self.helper(settings, expected_result, expected_deny_set)

    def test5(self) -> None:
        """
        Test disabling when permissions key doesn't exist.
        """
        # Prepare inputs.
        settings: Dict = {}
        # Prepare outputs.
        expected_result = True
        expected_deny_set = set(cc_control._GIT_DENIALS)
        # Run test.
        self.helper(settings, expected_result, expected_deny_set)

    def test6(self) -> None:
        """
        Test disabling when deny key doesn't exist under permissions.
        """
        # Prepare inputs.
        settings: Dict = {"permissions": {}}
        # Prepare outputs.
        expected_result = True
        expected_deny_set = set(cc_control._GIT_DENIALS)
        # Run test.
        self.helper(settings, expected_result, expected_deny_set)

    def test7(self) -> None:
        """
        Test that disabling preserves unrelated denials.
        """
        # Prepare inputs.
        other_denials = ["Bash(*rm:*)", "Edit(*dangerous*)"]
        settings: Dict = {"permissions": {"deny": other_denials.copy()}}
        # Prepare outputs.
        expected_result = True
        expected_deny_set = set(other_denials + cc_control._GIT_DENIALS)
        # Run test.
        self.helper(settings, expected_result, expected_deny_set)
