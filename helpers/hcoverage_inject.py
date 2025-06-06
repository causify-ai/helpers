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


def generate_temp_dockerfile_content() -> str:
    """
    Build a Dockerfile string that:
      1. Starts FROM base_image
      2. Installs coverage, pytest, pytest-cov at build time
      3. Creates /coverage_data and writes .coveragerc
      4. Sets ENV COVERAGE_PROCESS_START to /coverage_data/.coveragerc
      5. Writes a coverage.pth into site-packages so coverage auto-starts
    """
    lines = []
    lines.append("")  # blank line for readability

    # 2) Install coverage & pytest
    lines.append("RUN pip install --no-cache-dir coverage pytest pytest-cov")
    lines.append("")

    # 3) Create /coverage_data
    lines.append("RUN mkdir -p /app/coverage_data && chmod 777 /app/coverage_data")
    lines.append("")

    # 4) Write .coveragerc into /coverage_data
    # 5) Set ENV so every Python run picks up .coveragerc
    lines.append("COPY .coveragerc /app/coverage_data/.coveragerc")
    lines.append("ENV COVERAGE_PROCESS_START=/app/coverage_data/.coveragerc")
    lines.append("")

    # 6) Write coverage.pth into site-packages
    lines.append("RUN python - <<PYCODE")
    lines.append("import site, os")
    lines.append("site_dir = site.getsitepackages()[0]")
    lines.append("pth_file = os.path.join(site_dir, 'coverage.pth')")
    lines.append("with open(pth_file, 'w') as f:")
    lines.append("    f.write('import coverage; coverage.process_startup()')")
    lines.append("PYCODE")

    # Final newline
    return "\n".join(lines)

def coverage_commands_subprocess() :
    """
    Return a list of shell commands to run coverage steps in a Docker container.
    Assumes:
      - A valid .coveragerc exists in the current working directory.
      - coverage_data/ is the mounted folder inside the container.
    """
    commands=[
        "cp .coveragerc coverage_data/.coveragerc",
        "chmod 644 coverage_data/.coveragerc",
   ]
    for cmd in commands:
        hsystem.system(cmd, suppress_output=False)

def coverage_combine() :
    """
    Return a list of shell commands to combine coverage data.
    Assumes:
      - .coverage.* files are present in the current directory.
    """
    commands=[
        "cp coverage_data/.coverage.* .",
        "rm -rf coverage_data/.coverage.*",
        "coverage combine",
        "coverage report",
    ] 
    for cmd in commands:
        hsystem.system(cmd, suppress_output=False)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _LOG.info("Running hcoverage_inject as a script")
    try:
        hinject()
        _LOG.info("Coverage hook installed successfully.")
    except Exception as e:
        _LOG.error("Error installing coverage hook: %s", e)
    
    # Example usage of removing the hook
    # hremove()
    # _LOG.info("Coverage hook removed successfully.")  
    coverage_commands_subprocess()
