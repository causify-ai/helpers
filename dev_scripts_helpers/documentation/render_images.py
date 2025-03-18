#!/usr/bin/env python

"""
Replace sections of image code with rendered images, commenting out the
original code, if needed.

See `docs/work_tools/documentation_toolchain/all.render_images.explanation.md`.

Usage:

# Create a new Markdown file with rendered images:
> render_images.py -i ABC.md -o XYZ.md --action render --run_dockerized

# Render images in place in the original Markdown file:
> render_images.py -i ABC.md --action render --run_dockerized

# Render images in place in the original LaTeX file:
> render_images.py -i ABC.tex --action render --run_dockerized

# Open rendered images from a Markdown file in HTML to preview:
> render_images.py -i ABC.md --action open --run_dockerized
"""

import argparse
import logging
import os
import re
import tempfile
from typing import List, Tuple

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################


def _get_rendered_file_paths(
    out_file: str, image_code_idx: int, dst_ext: str
) -> Tuple[str, str, str]:
    """
    Generate paths to files for image rendering.

    The name assigned to the target image is relative to the name of the
    original file where the image code was extracted from and the order number
    of that code block in the file. E.g., image rendered from the first image
    code block in a Markdown file called `readme.md` would be called
    `figs/readme.1.png`. This way if we update the image, its name does not
    change.

    :param out_file: path to the output file where the rendered image should be
        inserted
    :param image_code_idx: order number of the image code block in the input
        file
    :param dst_ext: extension of the target image file
    :return:
        - path to the temporary file with the image code (e.g., `readme.1.txt`)
        - absolute path to the dir with rendered images (e.g., `/usr/docs/figs`)
        - relative path to the image to be rendered (e.g., `figs/readme.1.png`)
    """
    sub_dir = "figs"
    # E.g., "docs/readme.md" -> "/usr/docs", "readme.md".
    out_file_dir, out_file_name = os.path.split(os.path.abspath(out_file))
    # E.g., "readme".
    out_file_name_body = os.path.splitext(out_file_name)[0]
    # Create the name for the image file, e.g., "readme.1.png".
    img_name = f"{out_file_name_body}.{image_code_idx}.{dst_ext}"
    # Get the absolute path to the dir with images, e.g., "/usr/docs/figs".
    abs_img_dir_path = os.path.join(out_file_dir, sub_dir)
    # Get the relative path to the image, e.g., "figs/readme.1.png".
    rel_img_path = os.path.join(sub_dir, img_name)
    # Get the path to a temporary file with the image code, e.g., "readme.1.txt".
    code_file_path = f"{out_file_name_body}.{image_code_idx}.txt"
    return (code_file_path, abs_img_dir_path, rel_img_path)


def _render_code(
    image_code: str,
    image_code_idx: int,
    image_code_type: str,
    out_file: str,
    dst_ext: str,
    *,
    force_rebuild: bool = False,
    use_sudo: bool = False,
    dry_run: bool = False,
) -> str:
    """
    Render the image code into an image file.

    :param image_code: the code of the image
    :param image_code_idx: order number of the image code block in the
        file
    :param image_code_type: type of the image code according to its
        language, e.g., "plantuml", "mermaid"
    :param out_file: path to the output file where the image will be
        inserted
    :param dst_ext: extension of the rendered image, e.g., "svg", "png"
    :param dry_run: if True, the rendering command is not executed
    :return: path to the rendered image
    """
    _LOG.debug(hprint.func_signature_to_str("image_code"))
    if image_code_type == "plantuml":
        # TODO(gp): we should always add the start and end tags.
        if not image_code.startswith("@startuml"):
            image_code = f"@startuml\n{image_code}"
        if not image_code.endswith("@enduml"):
            image_code = f"{image_code}\n@enduml"
    elif image_code_type == "tikz":
        image_code_tmp = r"""
        \documentclass[tikz, border=10pt]{standalone}
        \usepackage{tikz}
        \begin{document}
        """
        image_code_tmp = hprint.dedent(image_code_tmp)
        image_code_tmp += image_code
        image_code_tmp += r"\end{document}"
        image_code = image_code_tmp
    # Get paths for rendered files.
    hio.create_enclosing_dir(out_file, incremental=True)
    in_code_file_path, abs_img_dir_path, out_img_file_path = _get_rendered_file_paths(
        out_file, image_code_idx, dst_ext
    )
    hio.create_dir(abs_img_dir_path, incremental=True)
    # Save the image code to a temporary file.
    hio.to_file(in_code_file_path, image_code)
    # Run the rendering.
    _LOG.info(
        "Creating the image from '%s' source and saving image to '%s'",
        in_code_file_path,
        abs_img_dir_path,
    )
    # Run as a dockerized executable.
    if dry_run:
        _LOG.warning("Skipping image generation because dry_run is set")
    else:
        if image_code_type == "plantuml":
            hdocker.run_dockerized_plantuml(
                in_code_file_path, abs_img_dir_path, dst_ext,
                force_rebuild=force_rebuild, use_sudo=use_sudo
            )
        elif image_code_type == "mermaid":
            hdocker.run_dockerized_mermaid(in_code_file_path, out_img_file_path,
                force_rebuild=force_rebuild, use_sudo=use_sudo)
        elif image_code_type == "tikz":
            cmd_opts: List[str] = []
            hdocker.dockerized_tikz_to_bitmap(in_code_file_path, cmd_opts, out_img_file_path,
                force_rebuild=force_rebuild, use_sudo=use_sudo)
        elif image_code_type == "graphviz_dot":
            cmd_opts: List[str] = []
            hdocker.run_dockerized_graphviz_dot(in_code_file_path, cmd_opts, out_img_file_path,
                force_rebuild=force_rebuild, use_sudo=use_sudo)
        else:
            raise ValueError(f"Invalid type: {image_code_type}")
    # Remove the temp file.
    os.remove(in_code_file_path)
    return out_img_file_path


def _get_comment_prefix_postfix(extension: str) -> Tuple[str, str]:
    # Define the character that comments out a line depending on the file type.
    if extension == ".md":
        comment_prefix = "[//]: # ("
        comment_postfix = ")"
    elif extension == ".tex":
        comment_prefix = "%"
        comment_postfix = ""
    elif extension == ".txt":
        comment_prefix = "//"
        comment_postfix = ""
    else:
        raise ValueError(f"Unsupported file type: {extension}")
    return comment_prefix, comment_postfix


def _insert_image_code(extension: str, rel_img_path: str) -> str:
    """
    Insert the code to display the image in the output file.
    """
    # Add the code to insert the image in the file.
    if extension in (".md", ".txt"):
        # Use the Markdown syntax.
        txt = f"![]({rel_img_path})"
        # f"![]({rel_img_path})" + "{height=60%}"
    elif extension == ".tex":
        # Use the LaTeX syntax.
        # We need to leave it on a single line to make it easy to find and
        # replace it.
        txt = rf"""\begin{{figure}} \includegraphics[width=\linewidth]{{{rel_img_path}}} \end{{figure}}"""
    else:
        raise ValueError(f"Unsupported file extension: {extension}")
    return txt


def _comment_if_needed(
    state: str, line: str, comment_prefix: str, comment_postfix: str
) -> str:
    if state == "found_image_code":
        if line.startswith(comment_prefix):
            ret = line
        else:
            ret = f"{comment_prefix} {line}{comment_postfix}"
    else:
        ret = line
    return ret


def _render_images(
    in_lines: List[str],
    out_file: str,
    dst_ext: str,
    *,
    force_rebuild: bool = False,
    use_sudo: bool = False,
    dry_run: bool = False,
) -> List[str]:
    """
    Insert rendered images instead of image code blocks.

    Here, "image code" refers to code that defines the content of the image,
    e.g., plantUML/mermaid code for diagrams.
    In this method,
    - The image code is commented out.
    - New code is added after the image code block to insert
      the rendered image.

    :param in_lines: lines of the input file
    :param out_file: path to the output file
    :param dst_ext: extension for rendered images
    :param dry_run: if True, the text of the file is updated but the images are
        not actually created
    :return: updated lines of the file
    """
    _LOG.debug(hprint.func_signature_to_str("in_lines"))
    # Get the extension of the output file.
    extension = os.path.splitext(out_file)[1]
    #
    comment_prefix, comment_postfix = _get_comment_prefix_postfix(extension)
    # Store the output.
    out_lines: List[str] = []
    # Store the image code found in the file.
    image_code_lines: List[str] = []
    # Store the order number of the current image code block.
    image_code_idx = 0
    # Image name explicitly set by the user with `plantuml(...)` syntax.
    user_rel_img_path = ""
    # Store the state of the parser.
    state = "search_image_code"
    # The code should look like:
    # ```plantuml
    #    ...
    # ```
    comment = re.escape(comment_prefix)
    start_regex = re.compile(
        rf"""
        ^\s*                # Start of the line and any leading whitespace
        ({comment}\s*)?     # Optional comment prefix
        ```                 # Opening backticks for code block
        (plantuml|mermaid|tikz|graphviz*)  # Image code type
        (\((.*)\))?         # Optional user-specified image name in parentheses
        \s*$                # Any trailing whitespace and end of the line
        """,
        re.VERBOSE,
    )
    end_regex = re.compile(
        rf"""
        ^\s*                # Start of the line and any leading whitespace
        ({comment}\s*)?     # Optional comment prefix
        ```                 # Opening backticks for code block
        \s*$                # Any trailing whitespace and end of the line
        """,
        re.VERBOSE,
    )
    for i, line in enumerate(in_lines):
        _LOG.debug("%d %s: '%s'", i, state, line)
        m = start_regex.search(line)
        if m:
            # Found the beginning of an image code block.
            hdbg.dassert_eq(state, "search_image_code")
            if m.group(1):
                state = "found_commented_image_code"
            else:
                state = "found_image_code"
            _LOG.debug(" -> state=%s", state)
            image_code_lines = []
            image_code_idx += 1
            # E.g., "plantuml" or "mermaid".
            image_code_type = m.group(2)
            if m.group(3):
                hdbg.dassert_eq(user_rel_img_path, "")
                user_rel_img_path = m.group(4)
                _LOG.debug(hprint.to_str("user_rel_img_path"))
            # Comment out the beginning of the image code.
            out_lines.append(
                _comment_if_needed(state, line, comment_prefix, comment_postfix)
            )
        elif state in ("found_image_code", "found_commented_image_code"):
            m = end_regex.search(line)
            if m:
                # Found the end of an image code block.
                image_code_txt = "\n".join(image_code_lines)
                rel_img_path = _render_code(
                    image_code_txt,
                    image_code_idx,
                    image_code_type,
                    out_file,
                    dst_ext,
                    force_rebuild=force_rebuild,
                    use_sudo=use_sudo,
                    dry_run=dry_run,
                )
                # Override the image name if explicitly set by the user.
                if user_rel_img_path != "":
                    rel_img_path = user_rel_img_path
                    user_rel_img_path = ""
                # Comment out the end of the image code, if needed.
                out_lines.append(
                    _comment_if_needed(
                        state, line, comment_prefix, comment_postfix
                    )
                )
                out_lines.append(_insert_image_code(extension, rel_img_path))
                # Set the parser to search for a new image code block.
                if state == "found_image_code":
                    state = "search_image_code"
                else:
                    state = "replace_image_code"
                _LOG.debug(" -> state=%s", state)
            else:
                # Record the line from inside the image code block.
                image_code_lines.append(line)
                # Comment out the inside of the image code.
                out_lines.append(
                    _comment_if_needed(
                        state, line, comment_prefix, comment_postfix
                    )
                )
        elif state == "replace_image_code":
            # Replace the line with the image code, which should be the next
            # line.
            if line.rstrip().lstrip() != "":
                # Replace the line.
                state = "search_image_code"
                _LOG.debug(" -> state=%s", state)
        else:
            # Keep a regular line.
            out_lines.append(line)
    return out_lines


# #############################################################################


def _open_html(out_file: str) -> None:
    """
    Convert the output file to HTML using `notes_to_pdf.py` and open it.

    :param out_file: path to the output file to open
    """
    _LOG.info("\n%s", hprint.frame("Convert file to HTML"))
    # Compose the command.
    cur_path = os.path.abspath(os.path.dirname(__file__))
    tmp_dir = os.path.split(out_file)[0]
    cmd = (
        f"{cur_path}/notes_to_pdf.py -t html -i {out_file} --skip_action "
        f"copy_to_gdrive --skip_action cleanup_after --tmp_dir {tmp_dir}"
    )
    # Run.
    hsystem.system(cmd)


# #############################################################################

_ACTION_OPEN = "open"
_ACTION_RENDER = "render"
_VALID_ACTIONS = [_ACTION_OPEN, _ACTION_RENDER]
# _DEFAULT_ACTIONS = [_ACTION_OPEN, _ACTION_RENDER]
_DEFAULT_ACTIONS: List[str] = []


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # Add input and output file arguments.
    parser.add_argument(
        "-i",
        "--in_file_name",
        required=True,
        type=str,
        help="Path to the input file",
    )
    parser.add_argument(
        "-o",
        "--out_file_name",
        type=str,
        default=None,
        help="Path to the output file",
    )
    # Add actions arguments.
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    # Add an argument for debugging.
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Update the file but do not render images",
    )
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Get the paths to the input and output files.
    in_file, out_file = hparser.parse_input_output_args(args)
    # Verify that the input and output file types are valid and equal.
    hdbg.dassert_file_extension(in_file, ["md", "tex", "txt"])
    hdbg.dassert_eq(
        os.path.splitext(in_file)[1],
        os.path.splitext(out_file)[1],
        msg="Input and output files should have the same extension.",
    )
    # Get the selected actions.
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info("Selected actions: %s", actions)
    # Set the extension for the rendered images.
    dst_ext = "png"
    if actions == [_ACTION_OPEN]:
        # Set the output file path and image extension used for the preview
        # action.
        in_file_ext = os.path.splitext(in_file)[1]
        out_file = tempfile.mktemp(suffix="." + in_file_ext)
        dst_ext = "svg"
    # Read the input file.
    in_lines = hio.from_file(in_file).split("\n")
    # Get the updated file lines after rendering.
    out_lines = _render_images(
        in_lines, out_file, dst_ext, 
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
        dry_run=args.dry_run
    )
    # Save the output into a file.
    hio.to_file(out_file, "\n".join(out_lines))
    # Open if needed.
    if _ACTION_OPEN in actions:
        _open_html(out_file)


if __name__ == "__main__":
    _main(_parse())
