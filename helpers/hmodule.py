"""
Import as:

import helpers.hmodule as hmodule
"""

import logging
import os
from typing import Any, Dict, Optional

import helpers.hdbg as hdbg
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

_WARNING = "\033[33mWARNING\033[0m"


# TODO(gp): Is this the right place for this function?
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
    code = hprint.dedent(code)
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
    import_name: str,
    *,
    package_name: Optional[str] = None,
    use_sudo: bool = True,
    use_activate: bool = False,
    venv_path: Optional[str] = None,
    quiet: bool = True,
) -> None:
    """
    Install a Python module if it is not already installed.

    :param import_name: name used to import the module (e.g., "openai")
    :param package_name: name of the package on PyPI (if different from `import_name`)
    :param use_sudo: whether to use sudo to install the module
    :param use_activate: whether to use the activate script to install the module
        (e.g., "source /venv/bin/activate; pip install --quiet --upgrade openai")
    :param venv_path: path to the virtual environment
        E.g., /Users/saggese/src/venv/client_venv.helpers
    :param quiet: whether to install the module quietly
    """
    _has_module = has_module(import_name)
    if _has_module:
        print(f"Module '{import_name}' is already installed.")
        return
    print(f"Installing module '{import_name}'...")
    # Sometime the package name is different from the import name.
    # E.g., we import using `import dash_bootstrap_components` but the package
    # name is `dash-bootstrap-components`.
    if package_name is None:
        package_name = import_name
    # Sometime the package name is different from the import name.
    # E.g., we import using `import dash_bootstrap_components` but the package
    # name is `dash-bootstrap-components`.
    if quiet:
        quiet_flag = "--quiet"
    else:
        quiet_flag = ""
    if venv_path is None:
        venv_path = "/venv"
    venv_path = os.path.join(venv_path, "bin/activate")
    hdbg.dassert_file_exists(venv_path, "Can't find venv_path='{venv_path}'")
    if use_activate:
        cmd = f'/bin/bash -c "(source {venv_path}; pip install {quiet_flag} --upgrade {package_name})"'
    else:
        cmd = f"pip install {quiet_flag} {package_name}"
    if use_sudo:
        cmd = f"sudo {cmd}"
    _, output = hsystem.system_to_string(cmd)
    print(output)
