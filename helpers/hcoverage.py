"""
Import as:

import helpers.hcoverage as hcovera
"""

import glob
import logging
import os
import pathlib
import site
import subprocess
import sysconfig

import helpers.hdbg as hdbg
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _detect_site_packages() -> pathlib.Path:
    """
    Return the Path to the site-packages directory for the active interpreter.

    - Try sysconfig first
    - Fall back to site.getsitepackages() or user-site.
    """
    try:
        purelib = sysconfig.get_path("purelib")
        if purelib:
            return pathlib.Path(purelib)
    except (KeyError, IOError):
        _LOG.debug(
            "sysconfig.get_path('purelib') failed, falling back to site packages"
        )
    try:
        sp_dirs = site.getsitepackages()
    except AttributeError:
        sp_dirs = []
    for d in sp_dirs:
        if "site-packages" in d:
            return pathlib.Path(d)
    return pathlib.Path(site.getusersitepackages())


def inject(coveragerc: str = ".coveragerc") -> None:
    """
    Install the coverage startup hook into this env site-packages.
    """
    rc = pathlib.Path(coveragerc).resolve()
    os.environ["COVERAGE_PROCESS_START"] = str(rc)
    _LOG.debug("Set COVERAGE_PROCESS_START to %s", rc)
    sp = _detect_site_packages()
    target = sp / "coverage.pth"
    hook_line = "import coverage; coverage.process_startup()"
    cmd = f'echo "{hook_line}" | sudo tee "{target}" > /dev/null'
    try:
        hsystem.system(cmd)
        _LOG.debug("Installed coverage hook to %s via sudo tee", target)
    except (OSError, subprocess.SubprocessError) as e:
        hdbg.dassert(False, f"Failed to install coverage hook via sudo tee: {e}")


def remove() -> None:
    """
    Remove the coverage startup hook from this env site-packages.
    """
    sp = _detect_site_packages()
    target = sp / "coverage.pth"
    if target.is_file():
        cmd = f'sudo rm -f "{target}"'
        try:
            hsystem.system(cmd)
            _LOG.info("Removed coverage hook from %s via sudo rm", target)
        except Exception as e:
            _LOG.error("Failed to remove coverage hook via sudo rm: %s", e)
            raise
    else:
        # TODO(Maddy): Is this acceptable?
        _LOG.warning("No coverage.pth found in %s", sp)
    # Remove coverage environment variables.
    try:
        if "COVERAGE_PROCESS_START" in os.environ:
            del os.environ["COVERAGE_PROCESS_START"]
            _LOG.info("Removed COVERAGE_PROCESS_START from environment")
        else:
            _LOG.debug("COVERAGE_PROCESS_START not found in environment")
    except Exception as e:
        _LOG.error("Failed to remove COVERAGE_PROCESS_START: %s", e)
        raise


def generate_coverage_dockerfile() -> str:
    """
    Build a Dockerfile string that appends coverage support.
    """
    # This requires to:
    # - Install coverage, pytest, pytest-cov at build time
    # - Create /coverage_data and writes .coveragerc
    # - Set ENV COVERAGE_PROCESS_START to /coverage_data/.coveragerc
    # - Write a coverage.pth into site-packages so coverage auto-starts
    txt = """
    # Install coverage and testing dependencies.
    RUN pip install --no-cache-dir coverage pytest pytest-cov

    # Create coverage data directory with proper permissions.
    RUN mkdir -p /app/coverage_data && chmod 777 /app/coverage_data

    # Setup coverage configuration.
    COPY .coveragerc /app/coverage_data/.coveragerc
    ENV COVERAGE_PROCESS_START=/app/coverage_data/.coveragerc

    # Create coverage.pth file for automatic startup.
    # This ensures coverage tracking starts automatically when Python runs.
    RUN python - <<PYCODE
    import site, os
    site_dir = site.getsitepackages()[0]
    pth_file = os.path.join(site_dir, 'coverage.pth')
    with open(pth_file, 'w') as f:
        f.write('import coverage; coverage.process_startup()')
    PYCODE
    """
    return str(hprint.dedent(txt))


def coverage_commands_subprocess() -> None:
    """
    Execute shell commands to run coverage steps in a Docker container.

    Assumes:
      - A valid .coveragerc exists in the current working directory.
      - coverage_data/ is the mounted folder inside the container.
    """
    commands = [
        "mkdir -p coverage_data",
        "chmod 777 coverage_data",
        "cp .coveragerc coverage_data/.coveragerc",
        "chmod 644 coverage_data/.coveragerc",
    ]
    for cmd in commands:
        hsystem.system(cmd, suppress_output=False)


def coverage_combine() -> None:
    """
    Execute shell commands to combine coverage data.

    Assumes:
      - .coverage.* files are present in the current directory or coverage_data/.
    """
    # Check if there are any coverage files in coverage_data/ and copy them.
    if os.path.exists("coverage_data"):
        coverage_files_cmd = (
            "find coverage_data -name '.coverage.*' 2>/dev/null | wc -l"
        )
        rc = hsystem.system(coverage_files_cmd, abort_on_error=False)
        if rc == 0:
            # Use a simple existence check instead of parsing command output.
            coverage_files = glob.glob("coverage_data/.coverage.*")
            if coverage_files:
                _LOG.info(
                    "Found coverage files in coverage_data/, copying to current directory"
                )
                commands = [
                    "cp coverage_data/.coverage.* . 2>/dev/null || true",
                    "rm -rf coverage_data/.coverage.* 2>/dev/null || true",
                ]
                for cmd in commands:
                    hsystem.system(cmd, suppress_output=False)
    # Check if there are any .coverage.* files to combine.
    coverage_files = glob.glob(".coverage.*")
    num_files = len(coverage_files)
    if num_files > 0:
        _LOG.info("Found %d coverage data files to combine", num_files)
        commands = [
            "coverage combine",
            "coverage report --skip-empty",
        ]
        for cmd in commands:
            hsystem.system(cmd, suppress_output=False)
    else:
        _LOG.warning("No .coverage.* files found to combine")
