#!/usr/bin/env python3

"""
Process markdown slides using LLM prompts.

Import as:

import process_slides
"""

import argparse
import logging
from typing import List, Optional, Tuple

import tqdm

import dev_scripts_helpers.llms.llm_prompts as dshlllpr
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hmarkdown_slides as hmarslid
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--in_file",
        action="store",
        required=True,
        help="Input markdown file containing slides",
    )
    parser.add_argument(
        "--action",
        action="store",
        required=True,
        help="Action to perform on each slide",
    )
    parser.add_argument(
        "--out_file",
        action="store",
        required=True,
        help="Output file to write processed results",
    )
    parser.add_argument(
        "--use_llm_transform",
        action="store_true",
        help="Use llm_transform script with slide_format_figures prompt",
    )
    parser.add_argument(
        "--no_abort_on_error",
        action="store_true",
        help="Continue processing even if LLM transformation fails",
    )
    hparser.add_limit_range_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _extract_slides_from_markdown(txt: str) -> List[Tuple[str, str]]:
    """
    Extract slides from markdown text.

    :param txt: markdown text content
    :return: list of tuples (slide_title, slide_content)
    """
    lines = txt.split("\n")
    header_list, _ = hmarslid.extract_slides_from_markdown(lines)
    _LOG.debug("header_list=%s", header_list)
    # Convert header list to slides with content.
    slides: List[Tuple[str, str]] = []
    for i, header_info in enumerate(header_list):
        _LOG.debug("header_info=%s", header_info)
        slide_title = header_info.description
        start_line = header_info.line_number - 1  # Convert to 0-indexed.
        # Determine end line for this slide.
        if i + 1 < len(header_list):
            end_line = header_list[i + 1].line_number - 1
        else:
            end_line = len(lines)
        # Extract slide content.
        slide_lines = lines[start_line:end_line]
        slide_content = "\n".join(slide_lines)
        slides.append((slide_title, slide_content))
    return slides


def _process_slide_with_llm(
    slide_content: str,
    action: str,
    *,
    use_llm_transform: bool = False,
    no_abort_on_error: bool = False,
) -> str:
    """
    Process a single slide using the LLM prompt function.

    :param slide_content: content of the slide to process
    :param action: action to perform (process or critique)
    :param use_llm_transform: if True, use llm_transform script instead
        of calling the function directly
    :param no_abort_on_error: if True, continue processing even if LLM
        fails
    :return: processed slide content
    """
    if use_llm_transform:
        # Use llm_transform script.
        return _process_slide_with_llm_transform(
            slide_content, action, no_abort_on_error=no_abort_on_error
        )
    else:
        # Use the original method with run_prompt.
        # Use gpt-4 model for processing.
        model = "gpt-4o"
        # Call the run_prompt function with the action as prompt_tag.
        result = dshlllpr.run_prompt(
            prompt_tag=action,
            txt=slide_content,
            model=model,
        )
        # Handle errors based on --no_abort_on_error flag.
        if result is None:
            if no_abort_on_error:
                _LOG.warning(
                    "LLM processing failed, continuing with original content"
                )
                result = slide_content  # Return original if processing failed.
            else:
                hdbg.dfatal("LLM processing failed for slide")
        return result


def _process_slide_with_llm_transform(
    slide_content: str,
    action: str,
    *,
    no_abort_on_error: bool = False,
) -> str:
    """
    Process a slide using the `llm_transform` script.

    :param slide_content: content of the slide to process
    :param no_abort_on_error: if True, continue processing even if LLM
        fails
    :return: processed slide content
    """

    # Create temporary files for input and output.
    tmp_in_path = "tmp.process_slide_with_llm_transform.input.txt"
    tmp_out_path = "tmp.process_slide_with_llm_transform.output.txt"

    # Write slide content to temporary input file.
    hio.to_file(tmp_in_path, slide_content)

    # Build the llm_transform command.
    # TODO(ai): Use
    llm_transform_script = hgit.find_file_in_git_tree("llm_transform.py")
    cmd = [
        "python",
        llm_transform_script,
        "-i",
        tmp_in_path,
        "-o",
        tmp_out_path,
        "-p",
        action,
    ]
    # Execute the command.
    rc = hsystem.system(" ".join(cmd), suppress_output=False)
    hdbg.dassert_file_exists(tmp_out_path)

    result = hio.from_file(tmp_out_path)
    return result


def _process_slides(
    slides: List[Tuple[str, str]],
    action: str,
    *,
    limit_range: Optional[Tuple[int, int]] = None,
    use_llm_transform: bool = False,
    no_abort_on_error: bool = False,
) -> List[str]:
    """
    Process all slides with the specified action.

    :param slides: list of (slide_title, slide_content) tuples
    :param action: action to perform on each slide
    :param limit_range: optional range limit for processing
    :param use_llm_transform: if True, use llm_transform script
    :param no_abort_on_error: if True, continue processing even if LLM
        fails
    :return: list of formatted processed results
    """
    # Apply limit range filtering.
    slides = hparser.apply_limit_range(slides, limit_range, item_name="slides")
    # Process slides with progress bar.
    processed_results: List[str] = []
    for slide_title, slide_content in tqdm.tqdm(slides, desc="Processing slides"):
        _LOG.debug("Processing slide: %s", slide_title)
        # Process the slide using LLM.
        processed_content = _process_slide_with_llm(
            slide_content,
            action,
            use_llm_transform=use_llm_transform,
            no_abort_on_error=no_abort_on_error,
        )
        # Format the result.
        if not processed_content.startswith(f"* {slide_title}"):
            result_entry = f"* {slide_title}\n\n{processed_content}"
        else:
            result_entry = processed_content
        processed_results.append(result_entry)
    return processed_results


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function.

    :param parser: command line argument parser
    """
    args = parser.parse_args()
    hparser.parse_verbosity_args(args)
    # Parse limit range.
    limit_range = hparser.parse_limit_range_args(args)
    # Validate input file exists.
    hdbg.dassert_file_exists(args.in_file)
    _LOG.info("Reading input file: %s", args.in_file)
    # Read the input markdown file.
    txt = hio.from_file(args.in_file)
    # Extract slides from the markdown content.
    slides = _extract_slides_from_markdown(txt)
    _LOG.info("Found %d slides to process", len(slides))
    # Process slides.
    processed_results = _process_slides(
        slides,
        args.action,
        limit_range=limit_range,
        use_llm_transform=args.use_llm_transform,
        no_abort_on_error=args.no_abort_on_error,
    )
    # Write results to output file.
    output_content = "\n\n".join(processed_results)
    hio.to_file(args.out_file, output_content)
    _LOG.info("Written processed results to: %s", args.out_file)


if __name__ == "__main__":
    _main(_parse())
