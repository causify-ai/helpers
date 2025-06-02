import os
import logging
import sysconfig
import site
import helpers.hsystem as hsystem
from pathlib import Path

_LOG = logging.getLogger(__name__)

def _detect_site_packages() -> Path:
    """
    Return the Path to the site-packages directory for the active interpreter.
    Tries sysconfig first; falls back to site.getsitepackages() or user-site.
    """
    try:
        purelib = sysconfig.get_path("purelib")
        if purelib:
            return Path(purelib)
    except (KeyError, IOError):
        pass

    try:
        sp_dirs = site.getsitepackages()
    except AttributeError:
        sp_dirs = []
    for d in sp_dirs:
        if "site-packages" in d:
            return Path(d)

    return Path(site.getusersitepackages())

def hinject(coveragerc: str = ".coveragerc") -> None:
    """Install the coverage startup hook into this env’s site-packages using sudo tee."""
    rc = Path(coveragerc).resolve()
    if not rc.is_file():
        raise FileNotFoundError(f".coveragerc not found at {rc}")
    os.environ.setdefault("COVERAGE_PROCESS_START", str(rc))

    sp = _detect_site_packages()
    target = sp / "coverage.pth"
    hook_line = "import coverage; coverage.process_startup()"

    cmd = f'echo "{hook_line}" | sudo tee "{target}" > /dev/null'
    try:
        hsystem.system(cmd)
        _LOG.info("Installed coverage hook to %s via sudo tee", target)
    except Exception as e:
        _LOG.error("Failed to install coverage hook via sudo tee: %s", e)
        raise

def hremove() -> None:
    """Remove the coverage startup hook from this env’s site-packages using sudo rm."""
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
        _LOG.warning("No coverage.pth found in %s", sp)
