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


def _open_html(out_file: str) -> None:
    """
    Convert the output file to HTML using `notes_to_pdf.py` and open it.

    :param out_file: path to the output file to open
    """
    _LOG.info("\n%s", hprint.frame("Convert file to HTML using notes_to_pdf.py"))
    # Compose the command.
    cur_path = os.path.abspath(os.path.dirname(__file__))
    tmp_dir = os.path.split(out_file)[0]
    cmd = (
        f"{cur_path}/notes_to_pdf.py -t html -i {out_file} --skip_action "
        f"copy_to_gdrive --skip_action cleanup_after --tmp_dir {tmp_dir}"
    )
    # Run.
    hsystem.system(cmd)


def _get_rendered_file_paths(
    out_file: str, image_code_idx: int, dst_ext: str
) -> Tuple[str, str, str]:
    """
    Generate paths to files for image rendering.

    The name assigned to the target image is relative to the name of the original
    file where the image code was extracted from and the order number of
    that code block in the file. E.g., image rendered from the first image code block
    in a Markdown file called `readme.md` would be called `figs/readme.1.png`.
    This way if we update the image, its name does not change.

    :param out_file: path to the output file where the rendered image should be inserted
    :param image_code_idx: order number of the image code block in the input file
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
    # Create the name for the image file.
    # E.g., "readme.1.png".
    img_name = f"{out_file_name_body}.{image_code_idx}.{dst_ext}"
    # Get the absolute path to the dir with images.
    # E.g., "/usr/docs/figs".
    abs_img_dir_path = os.path.join(out_file_dir, sub_dir)
    # Get the relative path to the image.
    # E.g., "figs/readme.1.png".
    rel_img_path = os.path.join(sub_dir, img_name)
    # Get the path to a temporary file with the image code.
    # E.g., "readme.1.txt".
    code_file_path = f"{out_file_name_body}.{image_code_idx}.txt"
    return (code_file_path, abs_img_dir_path, rel_img_path)


def _get_render_command(
    code_file_path: str,
    abs_img_dir_path: str,
    rel_img_path: str,
    dst_ext: str,
    image_code_type: str,
) -> str:
    """
    Create the command for rendering the image.

    :param code_file_path: path to the file with the image code
    :param abs_img_dir_path: absolute path to a dir where the image will
        be saved
    :param rel_img_path: relative path to the image to be rendered
    :param dst_ext: extension of the rendered image, e.g., "svg", "png"
    :param image_code_type: type of the image code according to its
        language, e.g., "plantuml", "mermaid"
    :return: rendering command
    """
    # Verify that the image file extension is valid.
    valid_extensions = ["svg", "png"]
    hdbg.dassert_in(dst_ext, valid_extensions)
    # Create the command.
    if image_code_type == "plantuml":
        cmd = f"plantuml -t{dst_ext} -o {abs_img_dir_path} {code_file_path}"
    elif image_code_type == "mermaid":
        cmd = f"mmdc --puppeteerConfigFile puppeteerConfig.json -i {code_file_path} -o {rel_img_path}"
    else:
        raise ValueError(
            f"Invalid type: {image_code_type}; should be one of 'plantuml', 'mermaid'"
        )
    return cmd


def _render_code(
    image_code: str,
    image_code_idx: int,
    image_code_type: str,
    out_file: str,
    dst_ext: str,
    run_dockerized: bool,
    dry_run: bool,
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
    :param run_dockerized: if True, the command is run as a dockerized
        executable
    :param dry_run: if True, the rendering command is not executed
    :return: path to the rendered image
    """
    if image_code_type == "plantuml":
        # Ensure the plantUML code is in the correct format to render.
        if not image_code.startswith("@startuml"):
            image_code = f"@startuml\n{image_code}"
        if not image_code.endswith("@enduml"):
            image_code = f"{image_code}\n@enduml"
    # Get paths for rendered files.
    hio.create_enclosing_dir(out_file, incremental=True)
    code_file_path, abs_img_dir_path, rel_img_path = _get_rendered_file_paths(
        out_file, image_code_idx, dst_ext
    )
    # Save the image code to a temporary file.
    hio.to_file(code_file_path, image_code)
    # Run the rendering.
    cmd = _get_render_command(
        code_file_path, abs_img_dir_path, rel_img_path, dst_ext, image_code_type
    )
    _LOG.info("Creating the image from %s source.", code_file_path)
    _LOG.info("Saving image to %s.", abs_img_dir_path)
    _LOG.info("> %s", cmd)
    if dry_run:
        # Do not execute the command.
        hsystem.system(cmd, dry_run=True)
    else:
        if run_dockerized:
            # Run as a dockerized executable.
            if image_code_type == "plantuml":
                hdocker.run_dockerized_plantuml(
                    abs_img_dir_path, code_file_path, dst_ext
                )
            elif image_code_type == "mermaid":
                hdocker.run_dockerized_mermaid(rel_img_path, code_file_path)
            else:
                raise ValueError(
                    f"Invalid type: {image_code_type}; should be one of 'plantuml', 'mermaid'"
                )
        else:
            # Run the package installed on the host directly.
            hsystem.system(cmd)
    # Remove the temp file.
    os.remove(code_file_path)
    return rel_img_path


def _render_images(
    in_lines: List[str],
    out_file: str,
    dst_ext: str,
    run_dockerized: bool,
    dry_run: bool,
) -> List[str]:
    """
    Insert rendered images instead of image code blocks.

    Here, "image code" refers to code that defines the content of
    the image, e.g., plantUML/mermaid code for diagrams.
    In this method,
    - The image code is commented out.
    - New code is added after the image code block to insert
      the rendered image.

    :param in_lines: lines of the input file
    :param out_file: path to the output file
    :param dst_ext: extension for rendered images
    :param run_dockerized: if True, the image rendering command is run as a dockerized executable
    :param dry_run: if True, the text of the file is updated
        but the images are not actually created
    :return: updated file lines
    """
    # Store the output.
    out_lines: List[str] = []
    # Store the image code found in the file.
    image_code_lines: List[str] = []
    # Store the order number of the current image code block.
    image_code_idx = 0
    # Store the state of the parser.
    state = "searching"
    # Define the character that comments out a line depending on the file type.
    if out_file.endswith(".md"):
        comment_prefix = "[//]: # ("
        comment_postfix = ")"
    elif out_file.endswith(".tex"):
        comment_prefix = "%"
        comment_postfix = ""
    else:
        raise ValueError(
            f"Unsupported file type: {out_file}; should be Markdown (.md) or LaTeX (.tex)"
        )
    for i, line in enumerate(in_lines):
        _LOG.debug("%d: %s -> state=%s", i, line, state)
        # The code should look like:
        # ```plantuml
        #    ...
        # ```
        # Or the same with "mermaid" instead of "plantuml".
        if line.strip() in ["```plantuml", "```mermaid"]:
            # Found the beginning of an image code block.
            hdbg.dassert_eq(state, "searching")
            image_code_lines = []
            image_code_idx += 1
            state = "found_image_code"
            image_code_type = line.strip(" `")
            _LOG.debug(" -> state=%s", state)
            # Comment out the beginning of the image code.
            out_lines.append(f"\n{comment_prefix} {line}{comment_postfix}")
        elif line.strip() == "```" and state == "found_image_code":
            # Found the end of an image code block.
            # Render the image.
            rel_img_path = _render_code(
                image_code="\n".join(image_code_lines),
                image_code_idx=image_code_idx,
                image_code_type=image_code_type,
                out_file=out_file,
                dst_ext=dst_ext,
                run_dockerized=run_dockerized,
                dry_run=dry_run,
            )
            # Comment out the end of the image code.
            out_lines.append(f"{comment_prefix} {line}{comment_postfix}\n")
            # Add the code that inserts the image in the file.
            if out_file.endswith(".md"):
                # Use the Markdown syntax.
                out_lines.append(f"![]({rel_img_path})")
            elif out_file.endswith(".tex"):
                # Use the LaTeX syntax.
                out_lines.append(r"\begin{figure}")
                out_lines.append(
                    rf"  \includegraphics[width=\linewidth]{{{rel_img_path}}}"
                )
                out_lines.append(r"\end{figure}")
            else:
                raise ValueError(
                    f"Unsupported file type: {out_file}; should be Markdown (.md) or LaTeX (.tex)"
                )
            # Set the parser to search for a new image code block.
            state = "searching"
            _LOG.debug(" -> state=%s", state)
        elif line.strip != "```" and state == "found_image_code":
            # Record the line from inside the image code block.
            image_code_lines.append(line)
            # Comment out the inside of the image code.
            out_lines.append(f"{comment_prefix} {line}{comment_postfix}")
        else:
            # Keep a regular line.
            out_lines.append(line)
    return out_lines


# #############################################################################

_ACTION_OPEN = "open"
_ACTION_RENDER = "render"
_VALID_ACTIONS = [_ACTION_OPEN, _ACTION_RENDER]
_DEFAULT_ACTIONS = [_ACTION_OPEN, _ACTION_RENDER]


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
    # Add runtime arguments.
    parser.add_argument(
        "--run_dockerized",
        action="store_true",
    )
    # Add an argument for debugging.
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Update the file but do not render images",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Get the paths to the input and output files.
    in_file, out_file = hparser.parse_input_output_args(args)
    # Verify that the input and output file types are valid and equal.
    hdbg.dassert_file_extension(in_file, ["md", "tex"])
    hdbg.dassert_eq(os.path.splitext(in_file)[1], os.path.splitext(out_file)[1])
    # Get the selected actions.
    actions = hparser.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    # Set the extension for the rendered images.
    dst_ext = "png"
    if actions == [_ACTION_OPEN]:
        # Set the output file path and image extension used for the preview action.
        out_file = tempfile.mktemp(suffix="." + in_file.split(".")[-1])
        dst_ext = "svg"
    # Read the input file.
    in_lines = hio.from_file(in_file).split("\n")
    # Get the updated file lines after rendering.
    out_lines = _render_images(
        in_lines, out_file, dst_ext, args.run_dockerized, args.dry_run
    )
    # Save the output into a file.
    hio.to_file(out_file, "\n".join(out_lines))
    # Open if needed.
    if _ACTION_OPEN in actions:
        _open_html(out_file)


if __name__ == "__main__":
    _main(_parse())
