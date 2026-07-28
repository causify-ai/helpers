import os
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
        expected_removed: list,
        expected_deny_list: list,
    ) -> None:
        """
        Test helper for _enable_git_commands.

        :param settings: Input settings dictionary
        :param expected_removed: Expected removed denials
        :param expected_deny_list: Expected deny list after execution
        """
        # Run test.
        removed, modified_settings = cc_control._enable_git_commands(settings)
        # Check outputs.
        self.assertEqual(removed, expected_removed)
        self.assertEqual(
            modified_settings["permissions"]["deny"], expected_deny_list
        )

    def test1(self) -> None:
        """
        Test enabling when all git denials are in the deny list.
        """
        # Prepare inputs.
        settings: Dict = {
            "permissions": {
                "deny": [
                    "Bash(*git commit*)",
                    "Bash(*git push*)",
                    "SomeOtherDenial",
                ]
            }
        }
        # Prepare outputs.
        expected_removed = [
            "Bash(*git commit*)",
            "Bash(*git push*)",
        ]
        expected_deny_list = ["SomeOtherDenial"]
        # Run test.
        self.helper(settings, expected_removed, expected_deny_list)

    def test2(self) -> None:
        """
        Test enabling when there are no git denials to remove.
        """
        # Prepare inputs.
        settings: Dict = {"permissions": {"deny": ["SomeOtherDenial"]}}
        # Prepare outputs.
        expected_removed = []
        expected_deny_list = ["SomeOtherDenial"]
        # Run test.
        self.helper(settings, expected_removed, expected_deny_list)

    def test3(self) -> None:
        """
        Test enabling when only some git denials are present.
        """
        # Prepare inputs.
        settings: Dict = {
            "permissions": {
                "deny": [
                    "Bash(*git commit*)",
                    "SomeOtherDenial",
                ]
            }
        }
        # Prepare outputs.
        expected_removed = ["Bash(*git commit*)"]
        expected_deny_list = ["SomeOtherDenial"]
        # Run test.
        self.helper(settings, expected_removed, expected_deny_list)

    def test4(self) -> None:
        """
        Test enabling when deny list is empty.
        """
        # Prepare inputs.
        settings: Dict = {"permissions": {"deny": []}}
        # Prepare outputs.
        expected_removed = []
        expected_deny_list = []
        # Run test.
        self.helper(settings, expected_removed, expected_deny_list)

    def test5(self) -> None:
        """
        Test enabling when permissions key doesn't exist.
        """
        # Prepare inputs.
        settings: Dict = {}
        # Prepare outputs.
        expected_removed = []
        expected_deny_list = []
        # Run test.
        self.helper(settings, expected_removed, expected_deny_list)

    def test6(self) -> None:
        """
        Test enabling when deny key doesn't exist under permissions.
        """
        # Prepare inputs.
        settings: Dict = {"permissions": {}}
        # Prepare outputs.
        expected_removed = []
        expected_deny_list = []
        # Run test.
        self.helper(settings, expected_removed, expected_deny_list)


# #############################################################################
# Test_Backup_and_Restore
# #############################################################################


class Test_backup_and_restore(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test that --enable creates a backup file with removed denials.
        """
        # Prepare file paths.
        scratch_dir = self.get_scratch_space()
        settings_path = os.path.join(scratch_dir, "settings.json")
        backup_path = os.path.join(scratch_dir, "settings.backup")
        # Prepare settings with git denials.
        settings = {
            "permissions": {
                "deny": [
                    "Bash(*git commit*)",
                    "Bash(*git push*)",
                    "Bash(*rm:*)",
                ]
            }
        }
        cc_control._save_settings(settings_path, settings)
        # Enable git commands.
        loaded_settings = cc_control._load_settings(settings_path)
        removed, _ = cc_control._enable_git_commands(loaded_settings)
        cc_control._save_backup(backup_path, removed)
        # Verify backup was created with correct content.
        backup_content = cc_control._load_backup(backup_path)
        self.assertEqual(len(backup_content), 2)
        self.assertIn("Bash(*git commit*)", backup_content)
        self.assertIn("Bash(*git push*)", backup_content)

    def test2(self) -> None:
        """
        Test that --disable restores denials from backup.
        """
        # Prepare file paths.
        scratch_dir = self.get_scratch_space()
        settings_path = os.path.join(scratch_dir, "settings.json")
        backup_path = os.path.join(scratch_dir, "settings.backup")
        # Prepare settings without git denials.
        settings = {"permissions": {"deny": ["Bash(*rm:*)"]}}
        cc_control._save_settings(settings_path, settings)
        # Create backup with git denials.
        backup_denials = [
            "Bash(*git commit*)",
            "Bash(*git push*)",
        ]
        cc_control._save_backup(backup_path, backup_denials)
        # Restore from backup.
        loaded_settings = cc_control._load_settings(settings_path)
        _, modified_settings = cc_control._restore_from_backup(
            loaded_settings, backup_path
        )
        # Verify denials were restored.
        restored_deny_list = modified_settings["permissions"]["deny"]
        self.assertIn("Bash(*rm:*)", restored_deny_list)
        self.assertIn("Bash(*git commit*)", restored_deny_list)
        self.assertIn("Bash(*git push*)", restored_deny_list)
        # Verify backup was deleted.
        self.assertFalse(os.path.exists(backup_path))

    def test3(self) -> None:
        """
        Test that enable followed by disable returns to original state.
        """
        # Prepare file paths.
        scratch_dir = self.get_scratch_space()
        settings_path = os.path.join(scratch_dir, "settings.json")
        backup_path = os.path.join(scratch_dir, "settings.backup")
        # Prepare original settings.
        original_settings = {
            "permissions": {
                "deny": [
                    "Bash(*git commit*)",
                    "Bash(*git push*)",
                    "Bash(*rm:*)",
                ]
            }
        }
        cc_control._save_settings(settings_path, original_settings)
        # Step 1: Enable (remove git denials and save backup).
        settings_after_enable = cc_control._load_settings(settings_path)
        removed, modified_settings_1 = cc_control._enable_git_commands(
            settings_after_enable
        )
        cc_control._save_backup(backup_path, removed)
        cc_control._save_settings(settings_path, modified_settings_1)
        # Verify only non-git denial remains.
        enabled_settings = cc_control._load_settings(settings_path)
        self.assertEqual(enabled_settings["permissions"]["deny"], ["Bash(*rm:*)"])
        # Step 2: Disable (restore from backup).
        settings_after_disable = cc_control._load_settings(settings_path)
        _, modified_settings_2 = cc_control._restore_from_backup(
            settings_after_disable, backup_path
        )
        cc_control._save_settings(settings_path, modified_settings_2)
        # Verify settings match original.
        final_settings = cc_control._load_settings(settings_path)
        self.assertEqual(
            set(final_settings["permissions"]["deny"]),
            set(original_settings["permissions"]["deny"]),
        )

    def test4(self) -> None:
        """
        Test that --disable fails if backup file is missing.
        """
        # Prepare file paths.
        scratch_dir = self.get_scratch_space()
        settings_path = os.path.join(scratch_dir, "settings.json")
        backup_path = os.path.join(scratch_dir, "settings.backup")
        # Prepare settings.
        settings = {"permissions": {"deny": ["Bash(*rm:*)"]}}
        cc_control._save_settings(settings_path, settings)
        # Try to restore without backup file.
        loaded_settings = cc_control._load_settings(settings_path)
        with self.assertRaises(AssertionError):
            cc_control._restore_from_backup(loaded_settings, backup_path)

    def test5(self) -> None:
        """
        Test that enable removes all denials containing git commit or git push.
        """
        # Prepare settings with various git patterns.
        settings = {
            "permissions": {
                "deny": [
                    "Bash(*git commit*)",
                    "Bash(*git commit -m *)",
                    "Bash(*git push*)",
                    "Bash(*git push --force*)",
                    "Edit(*git commit*)",
                    "Bash(*rm:*)",
                ]
            }
        }
        # Enable git commands.
        removed, modified_settings = cc_control._enable_git_commands(settings)
        # Verify all git patterns were removed.
        self.assertEqual(len(removed), 5)
        # Verify only non-git denial remains.
        self.assertEqual(
            modified_settings["permissions"]["deny"], ["Bash(*rm:*)"]
        )
