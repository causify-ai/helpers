#!/usr/bin/env python

"""
Parse a file with a traceback and generate a cfile to be used with vim to
navigate the stack trace.

# Usage Example

- Run pytest, save the output to a file, and navigate the stack trace with
  vim:
> pytest helpers/test/test_traceback.py 2>&1 | tee tmp.pytest.log
> traceback_to_cfile.py -i log.txt
> vim -c "cfile cfile"

- Navigate the stack trace from the system clipboard:
> pbpaste | traceback_to_cfile.py -i -

- Navigate the stack trace from the system clipboard using the --from_pb
  option:
> traceback_to_cfile.py --from_pb

- Find and parse the latest .log file:
> traceback_to_cfile.py --from_latest_file

Import as:

import dev_scripts_helpers.traceback_to_cfile as dstrtocf
"""

import argparse
import logging
import os
import subprocess
import sys

import helpers.hclipboard as hclipbo
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hselect_input_output as hseinout
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.htraceback as htraceb

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    # Mutually exclusive input methods
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "-i",
        "--input",
        dest="input",
        type=str,
        help="Input file or `-` for stdin",
    )
    input_group.add_argument(
        "--from_pb",
        action="store_true",
        help="Read traceback from system clipboard",
    )
    input_group.add_argument(
        "--from_latest_file",
        action="store_true",
        help="Find and use the latest .log file",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        type=str,
        default="cfile",
        help="Output file (default: cfile)",
    )
    parser = hparser.add_bool_arg(
        parser,
        "purify_from_client",
        default_value=True,
        help_="Make references to files in the current client",
    )
    parser.add_argument(
        "--open_vim",
        action="store_true",
        help="Open vim with cfile for navigation after parsing",
    )
    parser = hparser.add_verbosity_arg(parser)
    return parser  # type: ignore[no-any-return]


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    out_file_name = args.output
    if args.from_pb:
        # Handle --from_pb option.
        _LOG.info("Reading traceback from clipboard")
        txt_list = [hclipbo.get_clipboard_content()]
    elif args.from_latest_file:
        # Handle --from_latest_file option.
        _LOG.info("Finding latest .log file")
        cmd = 'find . -type f -name "*.log" | xargs ls -1 -t'
        dir_name = None
        remove_files_non_present = False
        files = hsystem.system_to_files(cmd, dir_name, remove_files_non_present)
        in_file_name = files[0]
        _LOG.info("in_file_name=%s", in_file_name)
        if out_file_name != "-":
            hio.delete_file(out_file_name)
        txt_list = hseinout.from_file(in_file_name)
    elif args.input:
        # Handle --input option.
        in_file_name = args.input
        if out_file_name != "-":
            os.system("clear")
        _LOG.info("in_file_name=%s", in_file_name)
        _LOG.info("out_file_name=%s", out_file_name)
        if out_file_name != "-":
            hio.delete_file(out_file_name)
        txt_list = hseinout.from_file(in_file_name)
    else:
        raise ValueError("Invalid input argument specification")
    # Transform.
    txt_tmp = "\n".join(txt_list)
    cfile, traceback = htraceb.parse_traceback(
        txt_tmp, purify_from_client=args.purify_from_client
    )
    if traceback is None:
        _LOG.error("Can't find traceback in the file")
        sys.exit(-1)
    print(hprint.frame("traceback", char1="-") + "\n" + traceback)
    cfile_as_str = htraceb.cfile_to_str(cfile)
    print(hprint.frame("cfile", char1="-") + "\n" + cfile_as_str)
    # Write file.
    if out_file_name != "-":
        hio.delete_file(out_file_name)
    hseinout.to_file(cfile_as_str.split("\n"), out_file_name)
    # Open vim with cfile if requested.
    if args.open_vim:
        if os.path.exists(out_file_name):
            cmd = f'vim -c "cfile {out_file_name}"'
            subprocess.run(cmd, shell=True, check=False)
        else:
            _LOG.warning("Can't find %s", out_file_name)


if __name__ == "__main__":
    _main(_parse())
