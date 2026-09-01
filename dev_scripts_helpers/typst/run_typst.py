#!/usr/bin/env python

r"""
Compile a Typst file to PDF inside a Docker container.

The script drives `typst compile` through
`dev_scripts_helpers/dockerize/lib_typst.py`, so no local Typst installation
is required. It also renders embedded diagram code (mermaid, tikz,
graphviz, ...) via `render_images.py` before compiling. The script also
reports any `warning:` diagnostics emitted by `typst compile` and, by
default, asserts if any are found.

# Usage Example

- Render diagrams, compile a Typst file to PDF, and open it (default actions):
> run_typst.py --input lecture.typ

- Compile without opening the PDF:
> run_typst.py --input lecture.typ --skip_action open_pdf

- Don't fail the build if `typst compile` emits warnings:
> run_typst.py --input lecture.typ --no_abort_on_warnings

- Don't fail the build if `typst compile` errors out:
> run_typst.py --input lecture.typ --no_abort_on_errors

- Watch mode: rebuild on file changes, skip opening on subsequent runs:
> run_typst.py --input lecture.typ --daemon

Import as:

import dev_scripts_helpers.typst.run_typst as dshtyrt
"""

import argparse
import logging
import os
import re
import sys
from typing import List

import helpers.hdaemon as hdaemon
import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hopen as hopen
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hselect_action as hselacti
import helpers.hsystem as hsystem
import helpers.hunit_test_purification as huntepur
import dev_scripts_helpers.dockerize.lib_typst as dshdlity

_LOG = logging.getLogger(__name__)

# #############################################################################
# Actions
# #############################################################################

_VALID_ACTIONS = [
    "render_images",
    "compile",
    "open_pdf",
]

_DEFAULT_ACTIONS = [
    "render_images",
    "compile",
    "open_pdf",
]

# #############################################################################
# Render images
# #############################################################################


def _render_images(in_file_path: str) -> None:
    """
    Render embedded diagram code (mermaid, tikz, graphviz, ...) in place.

    :param in_file_path: path to the `.typ` file to render images in
    """
    _LOG.debug(hprint.func_signature_to_str())
    exec_file = hgit.find_file("render_images.py")
    cmd = f"{exec_file} --input {in_file_path} --action render"
    hsystem.system(cmd, suppress_output=False, log_level=logging.DEBUG)


# #############################################################################
# Compilation
# #############################################################################

# Matches the `warning:` diagnostic lines emitted by `typst compile`.
_WARNING_REGEX = re.compile(r"^warning:")


def _report_compile_warnings(output: str) -> List[str]:
    """
    Log any `warning:` diagnostics found in `typst compile` output.

    :param output: combined stdout / stderr of the `typst compile` invocation
    :return: list of matched warning lines
    """
    lines = output.splitlines()
    warnings = [line for line in lines if _WARNING_REGEX.match(line)]
    for warning in warnings:
        _LOG.warning("%s", warning)
    return warnings


def _compile_typst(
    in_file_path: str,
    out_file_path: str,
    root: str,
    *,
    abort_on_warnings: bool = True,
    abort_on_errors: bool = True,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
    """
    Compile a `.typ` file to PDF with a single `typst compile` pass.

    Unlike `pdflatex`, `typst compile` fully resolves cross-references in a
    single pass, so no multiple-pass support is needed.

    :param in_file_path: path to the `.typ` file to compile
    :param out_file_path: path to the resulting PDF
    :param root: project root passed to `typst compile --root`
    :param abort_on_warnings: assert if `typst compile` emits any `warning:`
        diagnostics
    :param abort_on_errors: assert if `typst compile` fails (non-zero exit
        code).
    :param force_rebuild: whether to force rebuild the Docker container
    :param use_sudo: whether to use sudo for Docker commands
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Build the Docker command without executing it, so its output can be
    # captured here and scanned for warnings (mirroring what
    # `hdocker.process_docker_cmd()`'s "system" mode does internally, since
    # that mode discards the captured output instead of returning it).
    docker_cmd = dshdlity.run_dockerized_typst(
        in_file_path,
        out_file_path,
        [],
        typst_root_dir=root,
        mode="return_cmd",
        force_rebuild=force_rebuild,
        use_sudo=use_sudo,
    )
    rc, output = hsystem.system_to_string(docker_cmd, abort_on_error=False)
    output = huntepur.purify_apple_container_output(output)
    if output:
        print(output)
    warnings = _report_compile_warnings(output)
    if warnings:
        msg = (
            f"Found {len(warnings)} `typst compile` warning(s) for "
            f"'{in_file_path}'"
        )
        if abort_on_warnings:
            hdbg.dfatal(msg)
        else:
            _LOG.warning(msg)
    if rc != 0:
        msg = f"`typst compile` failed with rc={rc} for '{in_file_path}'"
        if abort_on_errors:
            hdbg.dfatal(msg)
        else:
            _LOG.error(msg)


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        action="store",
        required=True,
        help="Typst file to compile",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store",
        default="",
        help="Output PDF file (default: input file with a `.pdf` extension)",
    )
    parser.add_argument(
        "--root",
        action="store",
        default="",
        help=(
            "Project root passed to `typst compile --root` (default: the "
            "Git repo root)"
        ),
    )
    parser.add_argument(
        "--no_abort_on_warnings",
        action="store_true",
        default=False,
        help="Don't assert if `typst compile` emits warnings",
    )
    parser.add_argument(
        "--no_abort_on_errors",
        action="store_true",
        default=False,
        help=(
            "Don't assert if `typst compile` fails (e.g., useful in "
            "`--daemon` mode, so one bad save doesn't kill the watcher)"
        ),
    )
    hdaemon.add_daemon_arg(parser)
    hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hdocker.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    in_file_path = os.path.abspath(args.input)
    hdbg.dassert_file_extension(in_file_path, "typ")
    out_file_path = args.output
    if out_file_path == "":
        out_file_path = hio.change_filename_extension(in_file_path, "typ", "pdf")
    out_file_path = os.path.abspath(out_file_path)
    # Use the outermost Git root by default, so that root-absolute paths
    # (e.g., `image("/foo.png")`) resolve correctly.
    root = args.root if args.root else hgit.find_git_root()
    # Handle daemon mode.
    if args.daemon:
        # Skip "open_pdf" action on watch runs (viewer auto-reloads).
        cmd_line = " ".join(sys.argv)
        hdaemon.run_reactive_daemon_mode(
            in_file_path,
            cmd_line,
            "run_typst",
            watch_cmd_suffix=" --skip_action=open_pdf",
        )
    else:
        # Get actions.
        actions = hselacti.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
        print(
            hselacti.actions_to_string(actions, _VALID_ACTIONS, add_frame=True)
        )
        while actions:
            action = actions[0]
            to_execute, actions = hselacti.mark_action(action, actions)
            if not to_execute:
                continue
            if action == "render_images":
                _render_images(in_file_path)
            elif action == "compile":
                _compile_typst(
                    in_file_path,
                    out_file_path,
                    root,
                    abort_on_warnings=not args.no_abort_on_warnings,
                    abort_on_errors=not args.no_abort_on_errors,
                    force_rebuild=args.dockerized_force_rebuild,
                    use_sudo=args.dockerized_use_sudo,
                )
                _LOG.info("Output written to '%s'", out_file_path)
            elif action == "open_pdf":
                hopen.open_file(out_file_path)
            else:
                raise ValueError(f"Invalid action='{action}'")
        hdbg.dassert_eq(
            len(actions or []),
            0,
            "There are unprocessed actions: %s",
            str(actions),
        )


if __name__ == "__main__":
    _main(_parse())
