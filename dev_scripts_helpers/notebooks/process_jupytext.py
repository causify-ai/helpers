#!/usr/bin/env python

# pylint: disable=line-too-long
"""
Automate some common workflows with jupytext.

> find . -name "*.ipynb" | grep -v ipynb_checkpoints | head -3 | xargs -t -L 1 process_jupytext.py --action sync --file

# Pair
> process_jupytext.py -f vendors/kibot/data_exploratory_analysis.ipynb --action pair

# Test
> process_jupytext.py -f vendors/kibot/data_exploratory_analysis.ipynb --action test
> process_jupytext.py -f vendors/kibot/data_exploratory_analysis.ipynb --action test_strict

# Sync
> process_jupytext.py -f vendors/kibot/data_exploratory_analysis.ipynb --action sync

Import as:

import dev_scripts_helpers.notebooks.process_jupytext as dshnprju
"""

import argparse
import logging
import re

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import linters.utils as liutils

_LOG = logging.getLogger(__name__)

# #############################################################################

_EXECUTABLE = "jupytext"


def _pair(file_name: str) -> None:
    hdbg.dassert(
        liutils.is_ipynb_file(file_name),
        "'%s' has no .ipynb extension",
        file_name,
    )
    if liutils.is_paired_jupytext_file(file_name):
        _LOG.warning("The file '%s' seems already paired", file_name)
    # It is a ipynb and it is unpaired: create the python file.
    msg = f"There was no paired notebook for '{file_name}': created and added to git"
    _LOG.warning(msg)
    # Convert a notebook into jupytext.
    cmd = []
    cmd.append(_EXECUTABLE)
    cmd.append("--update-metadata")
    cmd.append("""'{"jupytext":{"formats":"ipynb,py:percent"}}'""")
    cmd.append(file_name)
    cmd = " ".join(cmd)
    hsystem.system(cmd)
    # Test the ipynb -> py:percent -> ipynb round trip conversion.
    cmd = _EXECUTABLE + f" --test --stop --to py:percent {file_name}"
    hsystem.system(cmd)
    # Add the .py file.
    cmd = _EXECUTABLE + f" --to py:percent {file_name}"
    hsystem.system(cmd)
    # Add to git.
    py_file_name = liutils.from_ipynb_to_python_file(file_name)
    cmd = f"git add {py_file_name}"
    hsystem.system(cmd)


def _sync(file_name: str) -> None:
    if liutils.is_paired_jupytext_file(file_name):
        if liutils.is_py_file(file_name):
            # Based on the `jupytext` documentation, the `--sync` command should be
            # enough to update the `.ipynb` file based on the updated paired `.py`
            # file. But for some reason these changes are not saved automatically
            # and have to be followed up by manually opening the notebook in Jupyter
            # and saving it. For this reason, we force updating and autosaving the
            # files with `--update`.
            cmd_update = _EXECUTABLE + f" --to ipynb --update {file_name}"
        else:
            cmd_update = _EXECUTABLE + f" --to py {file_name}"
        hsystem.system(cmd_update)
        cmd_sync = _EXECUTABLE + f" --sync {file_name}"
        hsystem.system(cmd_sync)
    else:
        _LOG.warning("The file '%s' is not paired: run --pair", file_name)


def _is_jupytext_version_different(output_txt: str) -> bool:
    """
    Return True if there is a difference in jupytext_version.

    Workaround for https://github.com/mwouts/jupytext/issues/414 to avoid
    report an error due to jupytext version mismatch.

    [jupytext] Reading nlp/notebooks/PTask1081_RP_small_test.py
    nlp/notebooks/PTask1081_RP_small_test.py:
    --- expected
    +++ actual
    @@ -5,7 +5,7 @@
     #       extension: .py
     #       format_name: percent
     #       format_version: '1.3'
    -#       jupytext_version: 1.3.3
    +#       jupytext_version: 1.3.0
     #   kernelspec:
     #     display_name: Python [conda env:.conda-amp_develop] *
     #     language: python
    """
    ret = False
    regex = r"jupytext_version: \d.*"
    m = re.findall(regex, output_txt, re.MULTILINE)
    _LOG.debug("Regex search result: %s", m)
    if m:
        if len(m) == 2:
            ret = True
            _LOG.warning(
                "There is a mismatch of jupytext version: '%s' vs '%s': skipping",
                m[0],
                m[1],
            )
    return ret


def _test(file_name: str, action: str) -> None:
    if action == "test":
        opts = "--test"
    elif action == "test_strict":
        opts = "--test-strict"
    else:
        raise ValueError(f"Invalid action='{action}'")
    cmd = [_EXECUTABLE, opts, f"--stop --to py:percent {file_name}"]
    cmd = " ".join(cmd)
    _LOG.debug("cmd=%s", cmd)
    rc, txt = hsystem.system_to_string(cmd, abort_on_error=False)
    if rc != 0:
        # Here we handle special cases that must be escaped.
        _LOG.debug("rc=%s, txt=\n'%s'", rc, txt)
        if _is_jupytext_version_different(txt):
            pass
        else:
            raise RuntimeError(txt)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-f",
        "--file",
        action="store",
        type=str,
        required=True,
        help="File to process",
    )
    parser.add_argument(
        "--action",
        action="store",
        choices=["pair", "test", "test_strict", "sync"],
        required=True,
        help="Action to perform",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    #
    file_name = args.file
    hdbg.dassert_path_exists(file_name)
    if args.action == "pair":
        _pair(file_name)
    elif args.action == "sync":
        _sync(file_name)
    elif args.action in ("test", "test_strict"):
        _test(file_name, args.action)
    else:
        raise ValueError(f"Invalid action '{args.action}'")


if __name__ == "__main__":
    _main(_parse())
