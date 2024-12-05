#!/usr/bin/env python

"""
Replace sections of diagram code with rendered diagram images.

Usage:

# Create a new Markdown file with rendered diagrams:
> render_diagrams.py -i ABC.md -o XYZ.md --action render

# Render diagrams in place in the original Markdown file:
> render_diagrams.py -i ABC.md --action render

# Render diagrams in place in the original LaTeX file:
> render_diagrams.py -i ABC.tex --action render

# Open rendered diagrams from a Markdown file in HTML to preview:
> render_diagrams.py -i ABC.md --action open
"""

import argparse
import logging
import os
import tempfile
from typing import List, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################

_ACTION_OPEN = "open"
_ACTION_RENDER = "render"
_VALID_ACTIONS = [_ACTION_OPEN, _ACTION_RENDER]
_DEFAULT_ACTIONS = [_ACTION_OPEN, _ACTION_RENDER]


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
    out_file: str, diagram_idx: int, dst_ext: str
) -> Tuple[str, str, str]:
    """
    Generate paths to files for image rendering.

    The name assigned to the target image is relative to the name of the original
    file where the diagram code was extracted from and the order number of
    that diagram code block in the file.
    This way if we update the image, its name does not change.

    :param out_file: path to the output file where the rendered image should be inserted
    :param diagram_idx: order number of the diagram code block in the input file
    :param dst_ext: extension of the target image file
    :return:
        - name of the temporary file with the diagram code
        - absolute path to the dir with rendered images
        - relative path to the image to be rendered
    """
    sub_dir = "diagram-images"
    # E.g., "docs/readme.md" -> "/usr/docs", "readme.md".
    out_file_dir, out_file_name = os.path.split(os.path.abspath(out_file))
    # E.g., "readme".
    out_file_name_body = os.path.splitext(out_file_name)[0]
    # Create the name for the image file.
    # E.g., "readme.0.png".
    img_name = f"{out_file_name_body}.{diagram_idx}.{dst_ext}"
    # Get the absolute path to the dir with images.
    # E.g., "/usr/docs/diagram-images".
    abs_img_dir_path = os.path.join(out_file_dir, sub_dir)
    # Get the relative path to the image.
    # E.g., "diagram-images/readme.0.png".
    rel_img_path = os.path.join(sub_dir, img_name)
    # Get the name for a temporary file with the diagram code.
    # The extension is omitted to support different requirements
    # of plantUML and mermaid rendering commands.
    # E.g., "readme.0".
    code_file_name = f"{out_file_name_body}.{diagram_idx}"
    return (code_file_name, abs_img_dir_path, rel_img_path)


def _get_render_command(
    code_file_path: str,
    abs_img_dir_path: str,
    rel_img_path: str,
    diagram_type: str,
    dst_ext: str,
) -> str:
    """
    Create the command for rendering the diagram image.

    :param code_file_path: path to the file with the diagram code
    :param abs_img_dir_path: absolute path to a dir where the image will
        be saved
    :param rel_img_path: relative path to the image to be rendered
    :param diagram_type: type of the diagram, e.g., "plantuml",
        "mermaid"
    :param dst_ext: extension of the rendered image, e.g., "svg", "png"
    :return: rendering command
    """
    # Verify that the image file extension is valid.
    valid_extensions = ["svg", "png"]
    hdbg.dassert_in(dst_ext, valid_extensions)
    # Create the command.
    if diagram_type == "plantuml":
        cmd = f"plantuml -t{dst_ext} -o {abs_img_dir_path} {code_file_path}.puml"
    elif diagram_type == "mermaid":
        cmd = f"mmdc -i {code_file_path}.mmd -o {rel_img_path}"
    return cmd


def _render_code(
    diagram_code: str,
    out_file: str,
    diagram_idx: int,
    diagram_type: str,
    dst_ext: str,
    dry_run: bool,
) -> str:
    """
    Render the diagram code into an image file.

    :param diagram_code: the code of the diagram
    :param out_file: path to the output file where the image will be
        inserted
    :param diagram_idx: order number of the diagram code block in the
        file
    :param diagram_type: type of the diagram, e.g., "plantuml",
        "mermaid"
    :param dst_ext: extension of the rendered image, e.g., "svg", "png"
    :param dry_run: if True, the rendering command is not executed
    :return: path to the rendered image
    """
    if diagram_type == "plantuml":
        # Ensure the plantUML code is in the correct format to render.
        if not diagram_code.startswith("@startuml"):
            diagram_code = f"@startuml\n{diagram_code}"
        if not diagram_code.endswith("@enduml"):
            diagram_code = f"{diagram_code}\n@enduml"
    # Get paths for rendered files.
    hio.create_enclosing_dir(out_file, incremental=True)
    code_file_name, abs_img_dir_path, rel_img_path = _get_rendered_file_paths(
        out_file, diagram_idx, dst_ext
    )
    # Save the diagram code to a temporary file.
    code_file_path = os.path.join(tempfile.gettempdir(), code_file_name)
    hio.to_file(code_file_path, diagram_code)
    # Run the rendering.
    cmd = _get_render_command(
        code_file_path, abs_img_dir_path, rel_img_path, diagram_type, dst_ext
    )
    _LOG.info("Creating the diagram from %s source.", code_file_path)
    _LOG.info("Saving image to %s.", abs_img_dir_path)
    _LOG.info("> %s", cmd)
    hsystem.system(cmd, dry_run=dry_run)
    return rel_img_path


def _render_diagrams(
    in_lines: List[str], out_file: str, dst_ext: str, dry_run: bool
) -> List[str]:
    """
    Insert rendered diagram images instead of diagram code blocks.

    - The diagram code is commented out.
    - New code is added after the diagram code block to insert
      the rendered image.

    :param in_lines: lines of the input file
    :param out_file: path to the output file
    :param dst_ext: extension for rendered images
    :param dry_run: if True, the text of the file is updated
        but the images are not actually created
    :return: updated file lines
    """
    # Store the output.
    out_lines: List[str] = []
    # Store the diagram code found in the file.
    diagram_lines: List[str] = []
    # Store the order number of the current diagram code block.
    diagram_idx = 0
    # Store the state of the parser.
    state = "searching"
    # Define the character that comments out a line depending on the file type.
    if out_file.endswith(".md"):
        comment_sign = "#"
    elif out_file.endswith(".tex"):
        comment_sign = "%"
    for i, line in enumerate(in_lines):
        _LOG.debug("%d: %s -> state=%s", i, line, state)
        # The code should look like:
        # ```plantuml
        #    ...
        # ```
        # Or the same with "mermaid" instead of "plantuml".
        if line.strip() in ["```plantuml", "```mermaid"]:
            # Found the beginning of a diagram code block.
            hdbg.dassert_eq(state, "searching")
            diagram_lines = []
            diagram_idx += 1
            state = "found_diagram_code"
            diagram_type = line.strip(" `")
            _LOG.debug(" -> state=%s", state)
            # Comment out the beginning of the diagram code.
            out_lines.append(f"{comment_sign} {line}")
        elif line.strip() == "```" and state == "found_diagram_code":
            # Found the end of a diagram code block.
            # Render the image.
            rel_img_path = _render_code(
                diagram_code="\n".join(diagram_lines),
                out_file=out_file,
                diagram_idx=diagram_idx,
                diagram_type=diagram_type,
                dst_ext=dst_ext,
                dry_run=dry_run,
            )
            # Comment out the end of the diagram code.
            out_lines.append(f"{comment_sign} {line}")
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
            # Set the parser to search for a new diagram code block.
            state = "searching"
            _LOG.debug(" -> state=%s", state)
        elif line.strip != "```" and state == "found_diagram_code":
            # Record the line from inside the diagram code block.
            diagram_lines.append(line)
            # Comment out the inside of the diagram code.
            out_lines.append(f"{comment_sign} {line}")
        else:
            # Keep a regular line.
            out_lines.append(line)
    return out_lines


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    hparser.add_input_output_args(parser)
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
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
    # Do not support stdin and stdout.
    hdbg.dassert_ne(in_file, "-")
    hdbg.dassert_ne(out_file, "-")
    # Verify that the input and output file types are valid and equal.
    hdbg.dassert_file_extension(in_file, ["md", "tex"])
    hdbg.dassert_eq(in_file.split(".")[-1], out_file.split(".")[-1])
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
    out_lines = _render_diagrams(in_lines, out_file, dst_ext, args.dry_run)
    # Save the output into a file.
    hio.to_file(out_file, "\n".join(out_lines))
    # Open if needed.
    if _ACTION_OPEN in actions:
        _open_html(out_file)


if __name__ == "__main__":
    _main(_parse())
