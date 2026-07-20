from typing import List, Optional, Union
from unittest import mock

import helpers.hdbg as hdbg
import helpers.hmodule as hmodule
import helpers.hunit_test as hunitest


# #############################################################################
# Test_hmodule1
# #############################################################################


class Test_hmodule1(hunitest.TestCase):
    def test_has_module1(self) -> None:
        """
        Check that the function returns true for the existing package.
        """
        self.assertTrue(hmodule.has_module("numpy"))

    def test_has_not_module1(self) -> None:
        """
        Check that the function returns false for the non-existing package.
        """
        self.assertFalse(hmodule.has_module("no_such_module"))


# #############################################################################
# Test_install_module_if_not_present
# #############################################################################


class Test_install_module_if_not_present(hunitest.TestCase):
    """
    Test install_module_if_not_present function with string and list inputs.
    """

    def helper(
        self,
        import_name: Union[str, List[str]],
        *,
        package_name: Optional[Union[str, List[str]]] = None,
        expected_installed: Optional[List[str]] = None,
        expected_calls: Optional[List[str]] = None,
    ) -> None:
        """
        Helper method to test install_module_if_not_present.

        :param import_name: Input import name(s)
        :param package_name: Input package name(s)
        :param expected_installed: List of modules marked as already installed
        :param expected_calls: List of expected pip install commands
        """
        # Prepare inputs.
        if expected_installed is None:
            expected_installed = []
        if expected_calls is None:
            expected_calls = []

        # Mock `has_module` to track which modules are "already installed".
        def mock_has_module(module: str) -> bool:
            return module in expected_installed

        # Capture system calls while returning proper mock objects.
        system_calls: List[str] = []

        def mock_system_to_string(cmd: str) -> tuple[int, str]:
            system_calls.append(cmd)
            return (0, "")

        # Run test.
        with mock.patch.object(
            hmodule, "has_module", side_effect=mock_has_module
        ):
            with mock.patch.object(
                hmodule, "_system_to_string", side_effect=mock_system_to_string
            ):
                with mock.patch.object(hdbg, "dassert_file_exists"):
                    hmodule.install_module_if_not_present(
                        import_name,
                        package_name=package_name,
                        quiet=True,
                        use_sudo=False,
                        use_activate=False,
                    )
        # Check outputs.
        self.assertEqual(system_calls, expected_calls)

    def test1(self) -> None:
        """
        Test single string input (backward compatibility).
        """
        # Prepare inputs.
        import_name = "openai"
        package_name = None
        expected_installed = []
        expected_calls = ["pip install --quiet openai"]
        # Run test.
        self.helper(
            import_name,
            package_name=package_name,
            expected_installed=expected_installed,
            expected_calls=expected_calls,
        )

    def test2(self) -> None:
        """
        Test single string with custom package name.
        """
        # Prepare inputs.
        import_name = "yaml"
        package_name = "pyyaml"
        expected_installed = []
        expected_calls = ["pip install --quiet pyyaml"]
        # Run test.
        self.helper(
            import_name,
            package_name=package_name,
            expected_installed=expected_installed,
            expected_calls=expected_calls,
        )

    def test3(self) -> None:
        """
        Test already installed module skips installation.
        """
        # Prepare inputs.
        import_name = "numpy"
        package_name = None
        expected_installed = ["numpy"]
        expected_calls = []
        # Run test.
        self.helper(
            import_name,
            package_name=package_name,
            expected_installed=expected_installed,
            expected_calls=expected_calls,
        )

    def test4(self) -> None:
        """
        Test list input with single module.
        """
        # Prepare inputs.
        import_name = ["openai"]
        package_name = None
        expected_installed = []
        expected_calls = ["pip install --quiet openai"]
        # Run test.
        self.helper(
            import_name,
            package_name=package_name,
            expected_installed=expected_installed,
            expected_calls=expected_calls,
        )

    def test5(self) -> None:
        """
        Test list input with multiple modules.
        """
        # Prepare inputs.
        import_name = ["openai", "numpy", "pandas"]
        package_name = None
        expected_installed = []
        expected_calls = [
            "pip install --quiet openai",
            "pip install --quiet numpy",
            "pip install --quiet pandas",
        ]
        # Run test.
        self.helper(
            import_name,
            package_name=package_name,
            expected_installed=expected_installed,
            expected_calls=expected_calls,
        )

    def test6(self) -> None:
        """
        Test list of imports with list of custom package names.
        """
        # Prepare inputs.
        import_name = ["yaml", "PIL"]
        package_name = ["pyyaml", "pillow"]
        expected_installed = []
        expected_calls = [
            "pip install --quiet pyyaml",
            "pip install --quiet pillow",
        ]
        # Run test.
        self.helper(
            import_name,
            package_name=package_name,
            expected_installed=expected_installed,
            expected_calls=expected_calls,
        )

    def test7(self) -> None:
        """
        Test mixed case: some modules already installed, some need installation.
        """
        # Prepare inputs.
        import_name = ["numpy", "openai", "pandas"]
        package_name = None
        expected_installed = ["numpy"]
        expected_calls = [
            "pip install --quiet openai",
            "pip install --quiet pandas",
        ]
        # Run test.
        self.helper(
            import_name,
            package_name=package_name,
            expected_installed=expected_installed,
            expected_calls=expected_calls,
        )

    def test8(self) -> None:
        """
        Test list with multiple modules where some are already installed.
        """
        # Prepare inputs.
        import_name = ["yaml", "PIL", "requests"]
        package_name = ["pyyaml", "pillow", "requests"]
        expected_installed = ["PIL"]
        expected_calls = [
            "pip install --quiet pyyaml",
            "pip install --quiet requests",
        ]
        # Run test.
        self.helper(
            import_name,
            package_name=package_name,
            expected_installed=expected_installed,
            expected_calls=expected_calls,
        )

    def test9(self) -> None:
        """
        Test mismatched list lengths raises assertion error.
        """
        # Prepare inputs.
        import_name = ["openai", "numpy"]
        package_name = ["openai"]
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hmodule.install_module_if_not_present(
                import_name,
                package_name=package_name,
            )
        # Verify error message contains relevant info.
        self.assertIn("same length", str(cm.exception))
