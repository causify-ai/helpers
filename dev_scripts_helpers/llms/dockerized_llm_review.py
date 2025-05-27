#!/usr/bin/env python3

"""
Review code using LLMs. It requires certain dependencies to be present (e.g.,
`openai`) and thus it is executed within a Docker container.

To use this script, you need to indicate the file to be reviewed and the
path to the document with review guidelines.
"""

import argparse
import logging
import re
from typing import Dict, List

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hlist as hlist
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


def _extract_bullet_points(text: str) -> List[str]:
    """
    Extract bullet point list items from text.

    Sub-lists nested under first-level items are extracted together with
    the first-level items.

    :param text: text to process
    :return: extracted bullet points, e.g.,
        ```
        [
            "- Item 1",
            '''
            - Item 2
               - Item 3
            '''
        ]
        ```
    """
    lines = text.split("\n")
    bullet_points = []
    current_item = ""
    for line in lines:
        if re.match(r"^- ", line):
            # Match first-level bullet point item.
            if current_item:
                # Store the previous item, if any.
                bullet_points.append(current_item.strip())
            # Start a new first-level bullet point item.
            current_item = line
        elif re.match(r"^\s+- ", line):
            # Match a sub-item (non first-level bullet point item).
            # Append sub-item to the current item.
            current_item += "\n" + line
    if current_item:
        bullet_points.append(current_item.strip())
    return bullet_points


def _load_review_guidelines(guidelines_doc_filename: str) -> Dict[str, List[str]]:
    """
    Load automated review guidelines.

    :param guidelines_doc_filename: name of the file with the review guidelines
    :return: review guidelines organized by topic/target file types, e.g.,

        ```
        "Python code": ["All functions and methods must have a docstring", ...],
        "Notebooks": ["All notebooks should have a table of contents", ...],
        "Markdowns": ["Headings should not be boldfaced", ...],
        "Spelling": ["Capitalize the first letter of `Python`", ...],
        "File system structure": ["Unit tests should be located under the `test` dir", ...]
        ```
    """
    guidelines_doc = hio.from_file(guidelines_doc_filename)
    # Extract headers from the guidelines file.
    headers = [
        header.description
        for header in hmarkdo.extract_headers_from_markdown(
            guidelines_doc, max_level=2
        )
    ]
    # Define headers of the categories of guidelines.
    guidelines_categories = [
        "Python code",
        "Notebooks",
        "Markdowns",
        "Spelling",
        "File system structure",
    ]
    guidelines: Dict[str, List[str]] = {}
    for category in guidelines_categories:
        hdbg.dassert_in(category, headers)
        # Extract the section under the header.
        section = hmarkdo.extract_section_from_markdown(guidelines_doc, category)
        # Extract individual guidelines from bullet points.
        individual_guidelines = _extract_bullet_points(section)
        guidelines[category] = individual_guidelines
    return guidelines


def _review(
    file_path: str,
    guidelines_doc_filename: str,
) -> List[str]:
    """
    Get an LLM to find violations of the guidelines in an input file.

    :param file_path: path to the file to review
    :param guidelines_doc_filename: name of the file with the review
        guidelines
    :return: automatically generated review comments for the input file
    """
    # Load the review guidelines.
    guidelines = _load_review_guidelines(guidelines_doc_filename)
    # Load the file.
    code = hio.from_file(file_path)
    # Select relevant guidelines for the file.
    guidelines_for_file: List[str] = []
    if file_path.endswith(".py"):
        # Use guidelines for Python code.
        # Python files paired to notebooks by jupytext should also follow these guidelines.
        guidelines_for_file = guidelines["Python code"]
    elif file_path.endswith(".ipynb"):
        # Use guidelines for notebooks.
        guidelines_for_file = guidelines["Notebooks"]
    elif file_path.endswith(".md"):
        # Use guidelines for Markdowns.
        guidelines_for_file = guidelines["Markdowns"]
    # Add general guidelines.
    guidelines_for_file.extend(guidelines["Spelling"])
    guidelines_for_file.extend(guidelines["File system structure"])
    #
    comments: List[str] = []
    system_prompt = hprint.dedent(
        """
        You are a proficient reviewer of Python code and technical documentation.
        You pay a lot of attention to detail.
        I will pass you the code and a guideline that the code must follow.
        """
    )
    _LOG.debug(hprint.to_str("system_prompt"))
    # We need to import this here since we have this package only when
    # running inside a Dockerized executable. We don't want an import to
    # this file assert since openai is not available in the local dev
    # environment.
    import helpers.hopenai as hopenai

    for guideline in guidelines_for_file:
        # Check if the file follows the specific guideline.
        guideline_prompt = hprint.dedent(
            f"""
            Check if the following code violates the following guideline:
            \n<GUIDELINE>\n
            {guideline}
            \n</GUIDELINE>\n\n
            \n<CODE>\n
            {code}
            \n</CODE>\n\n

            If no violations are found, do not output anything.
            For every line that violates the guideline, output the following:

            '<VIOLATION>{file_path}: line number: {guideline}</VIOLATION>'

            where line number is the number of the line that violates the guideline.
            - If the whole chunk of code violates the guideline, use the number of the first
            line in the chunk.
            - If the violation cannot be associated with a particular line, use line number = 0.
            """
        )
        response = hopenai.get_completion(
            guideline_prompt, system_prompt=system_prompt, print_cost=True
        )
        txt_out = hopenai.response_to_txt(response)
        hdbg.dassert_isinstance(txt_out, str)
        # Extract review comments from the response.
        cur_comments = re.findall(r"<VIOLATION>(.*?)</VIOLATION>", txt_out)
        comments.extend(cur_comments)
    return comments


def _process_comments(comments: List[str], log_filepath: str) -> None:
    """
    Post-process, save and output generated review comments.

    :param comments: automatically generated review comments
    :param log_filepath: path to the file to save the comments to
    """
    # Clean up.
    hdbg.dassert_list_of_strings(comments)
    comments = sorted(comments)
    comments = hprint.remove_empty_lines_from_string_list(comments)
    comments = hlist.remove_duplicates(comments)
    # Write into a file.
    hio.to_file(log_filepath, "\n".join(comments))
    # Output to the user.
    output_from_file = hio.from_file(log_filepath)
    print(hprint.frame(log_filepath, char1="/").rstrip("\n"))
    print(output_from_file + "\n")
    print(hprint.line(char="/").rstrip("\n"))


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # File selection.
    parser.add_argument("-i", "--in_file_path", type=str, help="File to review")
    # Reviewer guidelines file.
    parser.add_argument(
        "--guidelines_doc_filename",
        action="store",
        help="Name of the document with the guidelines for automated reviewing",
        default="all.automated_review_guidelines.reference.md",
    )
    # Run parameters.
    parser.add_argument(
        "--reviewer_log",
        default="./reviewer_warnings.txt",
        help="File for storing the warnings",
    )
    hparser.add_verbosity_arg(parser, log_level="CRITICAL")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Run.
    comments = _review(args.in_file_path, args.guidelines_doc_filename)
    _process_comments(comments, args.reviewer_log)


if __name__ == "__main__":
    _main(_parse())
