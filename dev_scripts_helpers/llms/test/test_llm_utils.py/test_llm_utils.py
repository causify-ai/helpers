import os
import unittest.mock as umock

import dev_scripts_helpers.llms.llm_utils as dshlllut
import helpers.hio as hio
import helpers.hunit_test as hunitest


class Test_convert_file_names1(hunitest.TestCase):
    """Test converting container paths in LLM output."""

    def test1(self) -> None:
        """Only replace the Docker path for the actual input file."""
        # Prepare inputs.
        out_file_name = os.path.join(self.get_scratch_space(), "output.txt")
        hio.to_file(
            out_file_name,
            "/app/input.py:12: note\n/other.py:3: untouched\n",
        )
        docker_mount_context = umock.Mock()
        docker_mount_context.convert_path.return_value = "/app/input.py"
        # Run test.
        with umock.patch.object(
            dshlllut.hdocker,
            "get_docker_mount_context",
            return_value=docker_mount_context,
        ):
            dshlllut._convert_file_names(
                "input.py",
                "input.py",
                out_file_name,
            )
        # Check output.
        actual = hio.from_file(out_file_name)
        expected = "input.py:12: note\n/other.py:3: untouched"
        self.assert_equal(actual, expected)
        docker_mount_context.convert_path.assert_called_once_with(
            "input.py",
            check_if_exists=False,
            is_input=True,
        )
