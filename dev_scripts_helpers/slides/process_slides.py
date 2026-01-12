#!/usr/bin/env python3

"""
Process markdown slides using LLM prompts.

Import as:

import process_slides
"""

import argparse
import logging
from typing import List, Optional, Tuple

from tqdm import tqdm

import dev_scripts_helpers.llms.llm_prompts as dshlllpr
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hmarkdown_slides as hmarslid
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _get_system_prompt_from_tag(prompt_tag: str) -> str:
    """
    Get the system prompt from a prompt tag.

    :param prompt_tag: tag of the prompt to get
    :return: system prompt string
    """
    # Get the info corresponding to the prompt tag.
    prompt_tags = list(zip(*dshlllpr.get_prompt_tags()))[0]
    hdbg.dassert_in(prompt_tag, prompt_tags)
    # Call the prompt function to get its return value.
    python_cmd = f"{prompt_tag}()"
    system_prompt, _, _, _ = eval(python_cmd)
    # Dedent the system prompt.
    system_prompt = hprint.dedent(system_prompt)
    return system_prompt


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
        # Convert to 0-indexed.
        start_line = header_info.line_number - 1
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
        llm_transform_script,
        "-i",
        tmp_in_path,
        "-o",
        tmp_out_path,
        "-p",
        action,
    ]
    # Execute the command.
    hsystem.system(" ".join(cmd), suppress_output=False)
    # Read the output.
    hdbg.dassert_file_exists(tmp_out_path)
    result = hio.from_file(tmp_out_path)
    return result


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
        # Use apply_llm with use_llm_executable=False.
        # Use gpt-4 model for processing.
        model = "gpt-4o"
        # Get the system prompt from the action.
        system_prompt = _get_system_prompt_from_tag(action)
        # Call apply_llm with use_llm_executable=False.
        try:
            result, cost = hllmcli.apply_llm(
                input_str=slide_content,
                system_prompt=system_prompt,
                model=model,
                use_llm_executable=False,
            )
            _LOG.debug("LLM processing completed with cost: $%.6f", cost)
        except Exception as e:
            # Handle errors based on --no_abort_on_error flag.
            if no_abort_on_error:
                _LOG.warning(
                    "LLM processing failed: %s, continuing with original content",
                    str(e),
                )
                result = slide_content
            else:
                hdbg.dfatal("LLM processing failed for slide: %s", str(e))
        return result


def _process_single_slide(
    slide_title: str,
    slide_content: str,
    action: str,
    use_llm_transform: bool,
    no_abort_on_error: bool,
) -> str:
    """
    Process a single slide.

    :param slide_title: title of the slide
    :param slide_content: content of the slide to process
    :param action: action to perform on the slide
    :param use_llm_transform: if True, use llm_transform script
    :param no_abort_on_error: if True, continue processing even if LLM
        fails
    :return: formatted processed result for the slide
    """
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
    return result_entry


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
    # Process slides sequentially with progress bar.
    processed_results = []
    for slide_title, slide_content in tqdm(slides, desc="Processing slides"):
        result = _process_single_slide(
            slide_title,
            slide_content,
            action,
            use_llm_transform,
            no_abort_on_error,
        )
        processed_results.append(result)
    return processed_results


# #############################################################################


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
