"""
Import as:

import helpers.hjupyter as hjupyte
"""

import logging
import os
import re
from typing import Dict, List, Tuple

import nbconvert
import nbformat

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def run_notebook(
    file_name: str,
    scratch_dir: str,
    *,
    pre_cmd: str = "",
) -> None:
    """
    Run jupyter notebook.

    Assert if the notebook doesn't complete successfully.

    :param file_name: path to the notebook to run. If this is a .py
        file, convert to .ipynb first
    :param scratch_dir: temporary dir storing the output
    :param pre_cmd:
    """
    file_name = os.path.abspath(file_name)
    hdbg.dassert_path_exists(file_name)
    hio.create_dir(scratch_dir, incremental=True)
    # Build command line.
    cmd = []
    if pre_cmd:
        cmd.append(f"{pre_cmd} &&")
    # Convert .py file into .ipynb if needed.
    root, ext = os.path.splitext(file_name)
    if ext == ".ipynb":
        notebook_name = file_name
    elif ext == ".py":
        cmd.append(f"jupytext --update --to notebook {file_name};")
        notebook_name = f"{root}.ipynb"
    else:
        raise ValueError(f"Unsupported file format for `file_name`='{file_name}'")
    # Execute notebook.
    cmd.append(f"cd {scratch_dir} &&")
    cmd.append(f"jupyter nbconvert {notebook_name}")
    cmd.append("--execute")
    cmd.append("--to html")
    cmd.append("--ExecutePreprocessor.kernel_name=python")
    # No time-out.
    cmd.append("--ExecutePreprocessor.timeout=-1")
    # Execute.
    cmd_as_str = " ".join(cmd)
    hsystem.system(cmd_as_str, abort_on_error=True, suppress_output=False)


def build_run_notebook_cmd(
    config_builder: str, dst_dir: str, notebook_path: str, *, extra_opts: str = ""
) -> str:
    """
    Construct a command string to run dev_scripts/notebooks/run_notebook.py
    with specified configurations.

    :param config_builder: the configuration builder to use for the
        notebook execution
    :param dst_dir: the destination directory where the notebook results
        will be saved
    :param notebook_path: the path to the notebook that should be
        executed
    :param extra_opts: options for "run_notebook.py", e.g., "--
        publish_notebook"
    """
    # Importing inside func to avoid error while creating dockerized executable.
    # TODO(Shaunak): debug why.
    import helpers.hgit as hgit

    # TODO(Vlad): Factor out common code with the
    # `helpers.lib_tasks_gh.publish_buildmeister_dashboard_to_s3()`.
    run_notebook_script_path = hgit.find_file_in_git_tree("run_notebook.py")
    cmd_run_txt = [
        run_notebook_script_path,
        f"--notebook {notebook_path}",
        f"--config_builder '{config_builder}'",
        f"--dst_dir '{dst_dir}'",
        f"{extra_opts}",
    ]
    cmd_run_txt = " ".join(cmd_run_txt)
    return cmd_run_txt


# #############################################################################
# NotebookImageExtractor
# #############################################################################


class NotebookImageExtractor:
    """
    Extract marked regions from a Jupyter notebook, convert them to HTML and
    captures screenshots.

    Initialize with input notebook path and output directory.
    """

    def __init__(self, notebook_path: str, output_dir: str) -> None:
        self.notebook_path = notebook_path
        self.output_dir = output_dir

    def extract_regions_from_notebook(self) -> List[Tuple[str, str, List]]:
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
            # start_extract(only_input) =  input_code.py
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
            # start_extract(all)  =full_output.html
            ```python
            print("This is both code and output")
            ```
            # end_extract

        :return: tuples (mode, out_filename, region_cells) for each extraction region.
        """
        # Read notebook.
        nb = nbformat.read(self.notebook_path, as_version=4)
        start_marker_regex = re.compile(
            r"""
            \#               # Match the literal '#' character (comment indicator)
            \s*              # Allow optional whitespace after the '#'
            start_extract    # Match the literal text 'start_extract'
            \(               # Match the literal '(' (escaped since it's a special character)
            \s*              # Allow optional whitespace after '('
            (only_input|only_output|all)  # Capture the extraction mode (one of: only_input, only_output, or all)
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
        regions = []
        in_extract = False
        current_mode = None
        current_out_filename = None
        current_cells = []
        for cell in nb.cells:
            if cell.cell_type != "code":
                continue
            if not in_extract:
                m = start_marker_regex.search(cell.source)
                if m:
                    # A start marker was found. Capture the mode and output filename
                    current_mode = m.group(1)
                    current_out_filename = m.group(2)
                    in_extract = True
                    # Remove the start marker from the cell.
                    cell.source = start_marker_regex.sub("", cell.source).strip()
                    ## TODO: How can this happen? For me this is an error.
                    # If there's also an end marker in this cell, complete the extraction region.
                    if end_marker_regex.search(cell.source):
                        cell.source = end_marker_regex.sub(
                            "", cell.source
                        ).strip()
                        current_cells.append(cell)
                        regions.append(
                            (current_mode, current_out_filename, current_cells)
                        )
                        current_cells = []
                        in_extract = False
                    else:
                        current_cells.append(cell)
                else:
                    # If there's an end marker without a corresponding start, ignore it.
                    pass
            else:
                # We are inside an extraction region, so continue adding cells to the region.
                if end_marker_regex.search(cell.source):
                    cell.source = end_marker_regex.sub("", cell.source).strip()
                    current_cells.append(cell)
                    regions.append(
                        (current_mode, current_out_filename, current_cells)
                    )
                    current_cells = []
                    in_extract = False
                else:
                    # If there's no end marker, just keep adding cells to the current region.
                    current_cells.append(cell)
        if not regions:
            raise ValueError("No extraction markers found in the notebook.")
        return regions

    def convert_notebook_to_html(
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

    def capture_screenshot(
        self, html_file: str, screenshot_path: str, *, timeout: int = 2000
    ) -> None:
        """
        Capture a screenshot of an HTML file using Playwright.

        This function launches a headless Chromium browser, opens the
        provided HTML file, waits for a specified timeout to ensure the
        page is fully rendered, and then takes a screenshot saving it to
        the provided screenshot path.

        :param html_file: path to the HTML file.
        :param screenshot_path: path where the screenshot will be saved.
        :param timeout: time in milliseconds to wait for the page to
            render.
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

    def _extract_and_capture(self) -> list:
        """
        Extract notebook regions, convert each to HTML, and capture separate
        screenshots.

        The function orchestrates the extraction of all marked regions
        from a Jupyter notebook. It processes each region independently:
        adjusting cells according to its extraction mode, converting the
        region to an HTML file, capturing a screenshot using Playwright,
        and then cleaning up the temporary HTML file. Screenshots are
        saved in the "screenshots" folder with filenames based on the
        name provided in the extraction marker. If a name is repeated, a
        counter suffix (_1, _2, etc.) is appended to ensure unique
        filenames. A list of screenshot file paths is returned.

        :return: list of paths to the screenshot files.
        """
        regions = self.extract_regions_from_notebook()
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
            temp_html = "temp_extract.html"
            self.convert_notebook_to_html(new_nb, temp_html)
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
            self.capture_screenshot(temp_html, screenshot_path)
            os.remove(temp_html)
            screenshot_files.append(screenshot_path)
            _LOG.info("Saved screenshot to %s", screenshot_path)
        return screenshot_files
