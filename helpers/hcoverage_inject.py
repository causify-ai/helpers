
#!/usr/bin/env python3
"""
Inject or remove a coverage startup hook in a virtual environment.
If no venv_dir is provided, the script will try to detect the currently active venv.
"""

import argparse
import logging
import os
import subprocess
import sys

_LOG = logging.getLogger(__name__)

def _get_pth_path(venv_dir: str) -> str:
    """Return the path to the coverage .pth file in site-packages."""
    venv_py = os.path.join(venv_dir, "bin", "python3")
    site_pkgs = (
        subprocess.check_output(
            [venv_py, "-c", "import site; print(site.getsitepackages()[0])"]
        )
        .decode()
        .strip()
    )
    return os.path.join(site_pkgs, "coverage.pth")


def hinject(venv_dir: str) -> None:
    """Inject coverage startup by writing a .pth file into the venv's site-packages."""
    pth_path = _get_pth_path(venv_dir)
    content = "import coverage; coverage.process_startup()\n"
    with open(pth_path, "w") as f:
        f.write(content)
    _LOG.info("Coverage startup hook written to %s", pth_path)


def hremove(venv_dir: str) -> None:
    """Remove the coverage startup .pth file from the venv's site-packages."""
    pth_path = _get_pth_path(venv_dir)
    if os.path.isfile(pth_path):
        os.remove(pth_path)
        _LOG.info("Coverage startup hook removed from %s", pth_path)
    else:
        _LOG.warning("No coverage startup hook found at %s", pth_path)
