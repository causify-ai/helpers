#!/usr/bin/env python
"""
Run actionlint on GitHub Actions workflow files.
"""

import logging
import os
from typing import List

import helpers.hsystem as hsystem
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


class _Actionlint(liaction.Action):
    def __init__(self) -> None:
        super().__init__("actionlint")

    def check_if_possible(self) -> bool:
        return hsystem.check_exec(self._executable)

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        is_workflow = (
            file_name.startswith(os.path.join(".github", "workflows"))
            and file_name.endswith((".yml", ".yaml"))
        )
        if not is_workflow:
            _LOG.debug("Skipping file_name='%s'", file_name)
            return []
        cmd = f"{self._executable} {file_name}"
        _, output = liutils.tee(cmd, self._executable, abort_on_error=False)
        return output
