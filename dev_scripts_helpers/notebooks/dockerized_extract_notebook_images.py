#!/usr/bin/env python3

"""
This script is designed to run a transformation script using LLMs. It requires
certain dependencies to be present (e.g., `openai`) and thus it is executed
within a Docker container.

To use this script, you need to provide the input file, output file, and
the type of transformation to apply.
"""

import argparse
import logging
import os
import re
from typing import Dict, List, Tuple

import nbconvert
import nbformat

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################
# NotebookImageExtractor
# #############################################################################


class _NotebookImageExtractor:
    """
    Extract marked regions from a Jupyter notebook, convert them to HTML and
    captures screenshots.
    Initialize with input notebook path and output directory.
    """

    def __init__(self, notebook_path: str, output_dir: str) -> None:
        self.notebook_path = notebook_path
        self.output_dir = output_dir

    @staticmethod
    def _extract_regions_from_notebook(notebook_path: str) -> List[Tuple[str, str, List]]:
        """
        Extract regions from a notebook based on extraction markers.

        This function reads a Jupyter notebook and searches for all regions
        indicated by the markers inside cells:
        ```
        # start_extract(mode)=<output_filename>
        ...
        # end_extract
        ```

        Example:
         1. To extract only the input code:
            # start_extract(only_input)=input_code.png
            ```python
            def test_func():
                return "Test"
            ```
            # end_extract

        2. To extract only the output of code:
            # start_extract(only_output)=output.png
            ```python
            print("This is the output")
            ```
            # end_extract

        3. To extract both code and output:
            # start_extract(all)=full_output.png
            ```python
            print("This is both code and output")
            ```
            # end_extract

        :return: tuples (mode, out_filename, region_cells) for each extraction
        region.
        """
        # Read notebook.
        nb = nbformat.read(notebook_path, as_version=4)
        # Define the regex for the start / endmarker.
        start_marker_regex = re.compile(
            r"""
            \#               # Match the literal '#' character (comment indicator)
            \s*              # Allow optional whitespace after the '#'
            start_extract    # Match the literal text 'start_extract'
            \(               # Match the literal '(' (escaped since it's a special character)
            \s*              # Allow optional whitespace after '('
            (\S+)            # Capture the extraction mode (one of: only_input, only_output, or all)
            \s*              # Allow optional whitespace after the extraction mode
            \)               # Match the literal ')' (escaped)
            \s*              # Allow optional whitespace after ')'
            =                # Match the literal '=' sign
            \s*              # Allow optional whitespace after '='
            (\S+)            # Capture the output filename (one or more non-whitespace characters)
             """,
            re.VERBOSE,
        )
        end_marker_regex = re.compile(r"#\s*end_extract\s*")
        # Initialize variables.
        regions = []
        in_extract = False
        current_mode = None
        current_out_filename = None
        current_cells = []
        # Iterate over the cells in the notebook.
        for cell_idx, cell in enumerate(nb.cells):
            if cell.cell_type != "code":
                continue
            # Check if the cell contains a start marker.
            m = start_marker_regex.search(cell.source)
            if m:
                hdbg.dassert(
                    not in_extract,
                    "Found a start marker while in an extraction region at cell %s\n%s",
                    cell_idx, cell.source
                )
                # A start marker was found.
                # Capture the mode and output filename
                current_mode = m.group(1)
                hdbg.dassert_in(
                    current_mode,
                    ["only_input", "only_output", "all"],
                )
                current_out_filename = m.group(2)
                in_extract = True
                # Remove the start marker from the cell.
                cell.source = start_marker_regex.sub("", cell.source).strip()
            else:
                # We are inside an extraction region, so continue adding cells
                # to the region.
                m = end_marker_regex.search(cell.source)
                if m:
                    hdbg.dassert(
                        in_extract,
                        "Found an end marker while not in an extraction region at cell %s\n%s",
                        cell_idx, cell.source
                    )
                    current_cells.append(cell)
                    regions.append(
                        (current_mode, current_out_filename, current_cells)
                    )
                    current_cells = []
                    in_extract = False
                    # Remove the end marker from the cell.
                    cell.source = end_marker_regex.sub("", cell.source).strip()
                else:
                    # If there's no end marker, just keep adding cells to the current region.
                    current_cells.append(cell)
        if not regions:
            _LOG.warning("No extraction markers found in the notebook.")
        return regions

    def _convert_notebook_to_html(
        self, nb: nbformat.NotebookNode, output_html: str
    ) -> None:
        """
        Convert a notebook object to an HTML file using `nbconvert`.

        :param nb: notebook object containing the extracted cells.
        :param output_html: filename for the temporary HTML output.
        """
        html_exporter = nbconvert.HTMLExporter()
        body, _ = html_exporter.from_notebook_node(nb)
        with open(output_html, "w", encoding="utf-8") as f:
            f.write(body)

    def _capture_screenshot(
        self, html_file: str, screenshot_path: str, *, timeout: int = 2000
    ) -> None:
        """
        Capture a screenshot of an HTML file using Playwright.

        This function launches a headless Chromium browser, opens the provided
        HTML file, waits for a specified timeout to ensure the page is fully
        rendered, and then takes a screenshot saving it to the provided
        screenshot path.

        :param html_file: path to the HTML file.
        :param screenshot_path: path where the screenshot will be saved.
        :param timeout: time in milliseconds to wait for the page to render.
        """
        # Import playwright only when this function is called.
        from playwright.sync_api import sync_playwright

        file_url = "file:///" + os.path.abspath(html_file)
        with sync_playwright() as p:
            # Launch a headless Chromium browser.
            browser = p.chromium.launch(headless=True)
            # Open the HTML file.
            page = browser.new_page(viewport={"width": 1200, "height": 800})
            page.goto(file_url)
            # Wait for a specified timeout to ensure the page.
            page.wait_for_timeout(timeout)
            # Take a screenshot, saving to file.
            page.screenshot(path=screenshot_path)
            browser.close()

    def extract_and_capture(self) -> list:
        """
        Extract notebook regions, convert each to HTML, and capture separate
        screenshots.

        The function orchestrates the extraction of all marked regions from a
        Jupyter notebook
        - Process each region independently: adjusting cells according to its
        extraction mode
        - Convert the region to an HTML file
        - Capture a screenshot using Playwright
        - Clean up the temporary HTML file
        
        Screenshots are saved in the "screenshots" folder with filenames based
        on the name provided in the extraction marker. If a name is repeated, a
        counter suffix (_1, _2, etc.) is appended to ensure unique filenames. A
        list of screenshot file paths is returned.

        :return: list of paths to the screenshot files.
        """
        regions = self._extract_regions_from_notebook()
        screenshot_files = []
        # Create screenshots folder if it doesn't exist.
        screenshots_folder = self.output_dir
        hio.create_dir(screenshots_folder, incremental=True)
        # Keep track of filename usage to handle duplicates.
        filename_counter: Dict[str, int] = {}
        # Process each region.
        for mode, out_filename, cells in regions:
            # Adjust each cell in the region according to the extraction mode.
            for cell in cells:
                if mode == "only_input":
                    cell.outputs = []
                elif mode == "only_output":
                    cell.source = ""
            # Create a new notebook for the region.
            new_nb = nbformat.v4.new_notebook(cells=cells)
            temp_html = f"tmp.dockerized_extract_notebook_images.html"
            self._convert_notebook_to_html(new_nb, temp_html)
            # Determine the final screenshot filename.
            base, ext = os.path.splitext(out_filename)
            if ext == "":
                ext = ".png"
            final_name = out_filename
            if final_name in filename_counter:
                filename_counter[final_name] += 1
                final_name = f"{base}_{filename_counter[out_filename]}{ext}"
            else:
                filename_counter[final_name] = 1
            screenshot_path = os.path.join(screenshots_folder, final_name)
            self._capture_screenshot(temp_html, screenshot_path)
            os.remove(temp_html)
            screenshot_files.append(screenshot_path)
            _LOG.info("Saved screenshot to %s", screenshot_path)
        return screenshot_files


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--in_notebook_filename",
        required=True,
        type=str,
        help="Input notebook filename",
    )
    parser.add_argument(
        "--out_image_dir",
        required=True,
        type=str,
        help="Output image directory",
    )
    hparser.add_verbosity_arg(parser, log_level="CRITICAL")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info("Extracting images from notebook %s", args.in_notebook_filename)
    extractor = _NotebookImageExtractor(
        args.in_notebook_filename,
        args.out_image_dir,
    )
    extractor.extract_and_capture()
    _LOG.info("Extraction completed. Images saved in '%s'", args.out_image_dir)

if __name__ == "__main__":
    _main(_parse())