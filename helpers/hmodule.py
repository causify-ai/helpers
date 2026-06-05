"""
Import as:

import helpers.hmodule as hmodule
"""

import logging
import os
import subprocess
import textwrap
from typing import Any, Dict, List, Optional, Tuple, Union

import helpers.hdbg as hdbg
import helpers.hserver as hserver

_LOG = logging.getLogger(__name__)

_WARNING = "\033[33mWARNING\033[0m"


# Use this to avoid extra dependencies from `hsystem`.
def _system_to_string(cmd: str) -> Tuple[int, str]:
    """
    Run a command and return the output and the return code.

    :param cmd: command to run
    :return: tuple of (return code, output)
    """
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        # Redirect stderr to stdout.
        stderr=subprocess.STDOUT,
        shell=True,
        text=True,
    )
    rc = result.returncode
    output = result.stdout
    output = output.strip()
    return rc, output


def has_module(module: str) -> bool:
    """
    Return whether a Python module can be imported or not.
    """
    if module == "gluonts" and hserver.is_host_mac():
        # Gluonts and mxnet modules are not properly supported on the ARM
        # architecture yet, see CmTask4886 for details.
        return False
    code = f"""
    try:
        import {module}
        has_module_ = True
    except ImportError as e:
        _LOG.warning("%s: %s", _WARNING, str(e))
        has_module_ = False
    """
    code = textwrap.dedent(code)
    # To make the linter happy.
    has_module_ = True
    locals_: Dict[str, Any] = {}
    # Need to explicitly declare and pass `locals_`:
    # https://docs.python.org/3/library/functions.html#exec
    # `Pass an explicit locals dictionary if you need to see effects
    # of the code on locals after function exec() returns.`
    exec(code, globals(), locals_)
    has_module_ = locals_["has_module_"]
    return has_module_


def install_module_if_not_present(
    import_name: Union[str, List[str]],
    *,
    package_name: Union[Optional[str], List[str], None] = None,
    use_sudo: bool = True,
    use_activate: bool = False,
    venv_path: Optional[str] = None,
    quiet: bool = True,
) -> None:
    r"""
    Install a Python module if it is not already installed.

    :param import_name:
        - If str: name used to import the module (e.g., "openai")
        - If List[str]: list of module names to check and install
    :param package_name:
        - If None: use `import_name` as the package name
        - If str: name of the package on PyPI (used when `import_name` is str)
        - If List[str]: list of package names corresponding to `import_name` list
        (must have same length as `import_name` if `import_name` is a list)
    :param use_sudo: whether to use sudo to install the module
    :param use_activate:
        whether to use the activate script to install the module
        (e.g., "source /venv/bin/activate; pip install --quiet --upgrade openai")
    :param venv_path: path to the virtual environment
        (e.g., /Users/saggese/src/venv/client_venv.helpers)
    :param quiet: whether to install the module quietly
    """
    # Normalize inputs to lists for uniform processing.
    if isinstance(import_name, str):
        import_names = [import_name]
    else:
        import_names = import_name
    #
    if package_name is None:
        package_names = import_names
    elif isinstance(package_name, str):
        package_names = [package_name]
    else:
        package_names = package_name
    # Validate that lists have matching lengths.
    hdbg.dassert_eq(
        len(import_names),
        len(package_names),
        "import_name and package_name lists must have the same length",
    )
    # Install each module.
    for import_n, package_n in zip(import_names, package_names):
        _has_module = has_module(import_n)
        if _has_module:
            print(f"Module '{import_n}' is already installed.")
            continue
        print(f"Installing module '{import_n}'...")
        # Sometime the package name is different from the import name.
        # E.g., we import using `import dash_bootstrap_components` but the
        # package name is `dash-bootstrap-components`.
        if quiet:
            quiet_flag = "--quiet"
        else:
            quiet_flag = ""
        _venv_path = venv_path
        if _venv_path is None:
            _venv_path = "/venv"
        _venv_path = os.path.join(_venv_path, "bin/activate")
        hdbg.dassert_file_exists(
            _venv_path,
            "Can't find venv_path='%s'",
            _venv_path,
        )
        if use_activate:
            cmd = f'/bin/bash -c "(source {_venv_path}; pip install {quiet_flag} --upgrade {package_n})"'
        else:
            cmd = f"pip install {quiet_flag} {package_n}"
        if use_sudo:
            cmd = f"sudo {cmd}"
        rc, output = _system_to_string(cmd)
        if rc != 0:
            raise RuntimeError(
                f"Failed to install module '{package_n}'. Output:\n{output}"
            )
        print(output)
