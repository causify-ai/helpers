"""
Unit tests for dockerized_utils.py

Import as:

import dev_scripts_helpers.dockerize.test.test_dockerized_utils as tst_dshddout
"""

import os
from unittest.mock import patch

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout


# #############################################################################
# Test_test_container_build1
# #############################################################################


class Test_test_container_build1(hunitest.TestCase):
    """
    Test the `test_container_build` helper function.
    """

    def test1(self) -> None:
        """
        Test basic container build with simple input and output.
        """
        # Prepare inputs.
        input_content = """
            # Test Document
            Hello world
            """
        input_content = hprint.dedent(input_content)
        input_ext = "md"
        output_ext = "pdf"

        def mock_run_func(
            input_file: str,
            output_file: str,
            **_kwargs: object,
        ) -> None:
            self.assertTrue(os.path.exists(input_file))
            hio.to_file(output_file, "output content")

        # Run test.
        dshddout.test_container_build(
            self,
            input_content,
            input_ext,
            output_ext,
            mock_run_func,
        )
        # Check outputs.
        # Test passes if no assertion errors.

    def test2(self) -> None:
        """
        Test container build with additional keyword arguments.
        """
        # Prepare inputs.
        input_content = """
            pandoc test
            """
        input_content = hprint.dedent(input_content)
        input_ext = "md"
        output_ext = "html"
        run_kwargs = {"container_type": "pandoc_texlive"}

        def mock_run_func(
            _input_file: str,
            output_file: str,
            **kwargs: object,
        ) -> None:
            self.assertEqual(kwargs.get("container_type"), "pandoc_texlive")
            hio.to_file(output_file, "output content")

        # Run test.
        dshddout.test_container_build(
            self,
            input_content,
            input_ext,
            output_ext,
            mock_run_func,
            run_kwargs=run_kwargs,
        )
        # Check outputs.
        # Test passes if no assertion errors.

    def test3(self) -> None:
        """
        Test input file is properly created with dedented content.
        """
        # Prepare inputs.
        input_content = """
            Line 1
                Indented line 2
            Line 3
            """
        input_ext = "txt"
        output_ext = "out"
        # Prepare outputs.
        expected = """
            Line 1
                Indented line 2
            Line 3
            """
        # Track what content was in the input file.
        actual_input_content_list = []

        def mock_run_func(
            input_file: str,
            output_file: str,
            **_kwargs: object,
        ) -> None:
            actual = hio.from_file(input_file)
            actual_input_content_list.append(actual)
            hio.to_file(output_file, "output content")

        # Run test.
        dshddout.test_container_build(
            self,
            input_content,
            input_ext,
            output_ext,
            mock_run_func,
        )
        # Check outputs.
        self.assert_equal(
            actual_input_content_list[0],
            expected,
            dedent=True,
        )

    def test4(self) -> None:
        """
        Test that helper fails if output file is not created.
        """
        # Prepare inputs.
        input_content = "test"
        input_ext = "md"
        output_ext = "pdf"

        def mock_run_func(
            _input_file: str,
            _output_file: str,
            **_kwargs: object,
        ) -> None:
            pass

        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dshddout.test_container_build(
                self,
                input_content,
                input_ext,
                output_ext,
                mock_run_func,
            )
        # Check outputs.
        self.assertIn("Output file", str(cm.exception))
        self.assertIn("was not created", str(cm.exception))

    def test5(self) -> None:
        """
        Test that use_sudo and force_rebuild are set correctly.
        """
        # Prepare inputs.
        input_content = "test"
        input_ext = "md"
        output_ext = "pdf"
        # Prepare outputs.
        captured_kwargs = {}

        def mock_run_func(
            _input_file: str,
            output_file: str,
            **kwargs: object,
        ) -> None:
            nonlocal captured_kwargs
            captured_kwargs = kwargs
            hio.to_file(output_file, "output content")

        # Run test.
        with patch("helpers.hdocker.get_use_sudo", return_value=False):
            dshddout.test_container_build(
                self,
                input_content,
                input_ext,
                output_ext,
                mock_run_func,
            )
        # Check outputs.
        self.assertEqual(captured_kwargs["force_rebuild"], True)
        self.assertEqual(captured_kwargs["use_sudo"], False)
