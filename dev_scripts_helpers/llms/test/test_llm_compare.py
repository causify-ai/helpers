import logging
import os
from unittest import mock

import pandas as pd

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.llms.llm_compare as dshllcmp

_LOG = logging.getLogger(__name__)


# TODO(ai_gp): Add tests using hllmcli.mock_apply_llm
# and passing backend="mock" to llm_cli.py


class Test_llm_compare_py(hunitest.TestCase):
    """
    End-to-end tests for llm_compare.py executable.
    """

    def _create_models_file(self, models: str) -> str:
        """
        Create a test models file with one model per line.

        :param models: Newline-separated model names
        :return: Path to created file
        """
        models_file = os.path.join(self.get_scratch_space(), "models.txt")
        hio.to_file(models_file, hprint.dedent(models))
        return models_file

    def test1(self) -> None:
        """
        Test error when neither --benchmark nor --llm_cli_cmds provided.
        """
        # Prepare inputs.
        output_dir = self.get_scratch_space()
        models_file = self._create_models_file("model1")
        argv = [
            "llm_compare.py",
            f"--models_from_file={models_file}",
            f"--output_dir={output_dir}",
        ]
        # Run test: should fail due to missing benchmark/llm_cli_cmds.
        with self.assertRaises(ValueError):
            with mock.patch("sys.argv", argv):
                parser = dshllcmp._parse()
                dshllcmp._main(parser)
