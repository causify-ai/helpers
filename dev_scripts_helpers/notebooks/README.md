# Notebooks Directory

Tools and utilities for working with Jupyter notebooks, including format
conversion, image extraction, publishing, and testing workflows.

## Structure of the Dir

- `test/`
  - Unit tests for notebook utilities and image extraction tools
- `test/outcomes/`
  - Test result files and expected outputs for notebook test cases

## Description of Files

- `__init__.py`
  - Package initialization importing notebook test case utilities for testing workflows

- `conftest.py`
  - pytest configuration and fixtures for notebook-related tests

- `add_toc_to_notebook.py`
  - Automatically generates and adds a table of contents to Jupyter notebooks

- `all.extract_notebook_images.how_to_guide.md`
  - Guide for extracting images from annotated Jupyter notebook cells

- `dockerized_extract_notebook_images.py`
  - Extracts marked regions from notebooks and converts them to images using Docker

- `extract_notebook_images.py`
  - Wrapper to run notebook image extraction inside Docker container with dynamic build

- `ipynb_format.py`
  - Formats code cells in Jupyter notebooks using yapf style configuration

- `process_jupytext.py`
  - Automates jupytext workflows including pairing, syncing, testing, and
    comparing notebook conversions

- `profile_test_durations.py`
  - Notebook for analyzing and visualizing test execution durations and performance

- `publish_notebook.py`
  - Converts notebooks to HTML and publishes to browser, S3, or webserver

- `run_jupyter_server.py`
  - Manages Jupyter notebook server lifecycle including start, stop, and port management

- `run_notebook_test_case.py`
  - Test case base class for running notebooks end-to-end with configuration

- `run_notebook.py`
  - Executes notebooks with specified configs and handles parallel execution and publishing

- `test/test_dockerized_extract_notebook_images.py`
  - Tests for extracting regions from notebooks using Docker-based extraction

- `test/test_extract_notebook_images.py`
  - Integration tests for dockerized notebook image extractor with container rebuild

## Description of Executables

### `add_toc_to_notebook.py`

- **What It Does**:
  - Scans notebook cells for markdown headings and generates a clickable table
    of contents
  - Adds navigation anchors to each heading for easy linking
  - Updates or creates a TOC cell at the beginning of the notebook

- **Examples**:

  - Add TOC to a single notebook file:

    ```bash
    > ./add_toc_to_notebook.py --input_files my_notebook.ipynb
    ```

  - Add TOC to all notebooks in a directory:

    ```bash
    > ./add_toc_to_notebook.py --input_dir ./notebooks/
    ```

  - Add TOC to multiple specific files:

    ```bash
    > ./add_toc_to_notebook.py --input_files "notebook1.ipynb notebook2.ipynb"
    ```

### `extract_notebook_images.py`

- **What It Does**:
  - Builds a Docker container with Playwright and nbconvert for screenshot
    capture
  - Extracts annotated regions from notebooks based on special comment markers
  - Saves extracted content as PNG images or HTML files to specified directory

- **Examples**:

  - Extract images from a notebook to a screenshots directory:

    ```bash
    > ./extract_notebook_images.py \
        --in_notebook_filename ./test/input/test_notebook.ipynb \
        --out_image_dir ./screenshots
    ```

  - Extract images with forced Docker container rebuild:

    ```bash
    > ./extract_notebook_images.py \
        --in_notebook_filename my_notebook.ipynb \
        --out_image_dir ./output \
        --dockerized_force_rebuild
    ```

  - Extract images using sudo for Docker operations:

    ```bash
    > ./extract_notebook_images.py \
        --in_notebook_filename notebook.ipynb \
        --out_image_dir ./images \
        --dockerized_use_sudo
    ```

### `ipynb_format.py`

- **What It Does**:
  - Formats Python code cells in notebooks using yapf style configuration
  - Skips magic commands, shell commands, and special IPython syntax
  - Reports number of cells modified and writes changes back to notebook

- **Examples**:

  - Format a single notebook with default style:

    ```bash
    > ./ipynb_format.py my_notebook.ipynb
    ```

  - Format multiple notebooks:

    ```bash
    > ./ipynb_format.py notebook1.ipynb notebook2.ipynb notebook3.ipynb
    ```

  - Format with custom yapf style:

    ```bash
    > ./ipynb_format.py --style google my_notebook.ipynb
    ```

### `process_jupytext.py`

- **What It Does**:
  - Pairs unpaired notebooks with Python files using percent format
  - Synchronizes changes between notebooks and paired Python files
  - Tests round-trip conversion to ensure no data loss
  - Compares notebooks with paired Python files using vimdiff

- **Examples**:

  - Pair a notebook with a Python file:

    ```bash
    > ./process_jupytext.py \
        --file vendors/kibot/data_exploratory_analysis.ipynb \
        --action pair
    ```

  - Sync changes between notebook and paired file:

    ```bash
    > ./process_jupytext.py \
        --file vendors/kibot/data_exploratory_analysis.ipynb \
        --action sync
    ```

  - Test round-trip conversion without strict checks:

    ```bash
    > ./process_jupytext.py \
        --file my_notebook.ipynb \
        --action test
    ```

  - Test with strict validation:

    ```bash
    > ./process_jupytext.py \
        --file my_notebook.ipynb \
        --action test_strict
    ```

  - Compare notebook with its paired Python file:

    ```bash
    > ./process_jupytext.py \
        --file my_notebook.ipynb \
        --action diff
    ```

  - Compare Python file with its paired notebook:

    ```bash
    > ./process_jupytext.py \
        --file my_script.py \
        --action diff
    ```

### `publish_notebook.py`

- **What It Does**:
  - Converts Jupyter notebooks to HTML format
  - Opens notebooks in browser from local or S3 storage
  - Publishes notebooks to S3 buckets or webservers with optional tagging

- **Examples**:

  - Publish a notebook to S3:

    ```bash
    > ./publish_notebook.py \
        --file nlp/notebooks/PTask768_event_filtering.ipynb \
        --action publish \
        --aws_profile 'am'
    ```

  - Open an archived notebook from S3 in browser:

    ```bash
    > ./publish_notebook.py \
        --file s3://.../notebooks/PTask768_event_filtering.html \
        --action open \
        --aws_profile 'am'
    ```

  - Convert notebook to HTML locally:

    ```bash
    > ./publish_notebook.py \
        --file my_notebook.ipynb \
        --action convert \
        --target_dir ./html_output
    ```

  - Publish with custom tag:

    ```bash
    > ./publish_notebook.py \
        --file my_notebook.ipynb \
        --action publish \
        --tag "version_2.0" \
        --aws_profile 'default'
    ```

### `run_jupyter_server.py`

- **What It Does**:
  - Starts Jupyter notebook server on specified port with Chrome browser
  - Checks for existing servers and reports running instances
  - Kills processes squatting on the desired port when needed

- **Examples**:

  - Start a Jupyter server (kills existing if needed):

    ```bash
    > ./run_jupyter_server.py force_start
    ```

  - Check what notebook servers are running:

    ```bash
    > ./run_jupyter_server.py check
    ```

  - Start server only if port is free:

    ```bash
    > ./run_jupyter_server.py start
    ```

  - Kill server on specific port:

    ```bash
    > ./run_jupyter_server.py kill
    ```

### `run_notebook.py`

- **What It Does**:
  - Executes notebooks with configuration builders for parameterized experiments
  - Supports parallel execution with multiple threads or serial processing
  - Publishes results and handles incremental execution with retry logic

- **Examples**:

  - Run notebook with config builder and parallel execution:

    ```bash
    > ./run_notebook.py \
        --notebook nlp/notebooks/NLP_RP_pipeline.ipynb \
        --config_builder "nlp.build_configs.build_PTask1088_configs()" \
        --dst_dir nlp/test_results \
        --num_threads 2
    ```

  - Run notebook serially with single config:

    ```bash
    > ./run_notebook.py \
        --notebook analysis.ipynb \
        --config_builder "build_analysis_config()" \
        --dst_dir ./results \
        --num_threads serial
    ```

  - Run with publishing enabled:

    ```bash
    > ./run_notebook.py \
        --notebook experiment.ipynb \
        --config_builder "build_configs()" \
        --dst_dir ./output \
        --publish_notebook
    ```

### `process_all_jupytext.sh`

- **What It Does**:
  - Batch processes all .ipynb files in a directory tree with jupytext
  - Applies sync action to every notebook found recursively
  - Skips .ipynb_checkpoints directories
  - Uses xargs for efficient batch operations

- **Examples**:

  - Sync all notebooks in current directory and subdirectories:

    ```bash
    > ./process_all_jupytext.sh
    ```

### `jupytext_pair.sh`

- **What It Does**:
  - Pairs all .ipynb files in current directory with Python files
  - Sets jupytext format to ipynb with percent-style Python pairing
  - Convenience script for bulk pairing operations

- **Examples**:

  - Pair all notebooks in current directory:

    ```bash
    > ./jupytext_pair.sh
    ```

### `notebook.pair.sh`

- **What It Does**:
  - Lists and pairs all .ipynb files in current directory with Python files
  - Configures jupytext format as ipynb,py:percent for each notebook
  - Initial setup script for notebook pairing in a project

- **Examples**:

  - Set up jupytext pairing for all notebooks:

    ```bash
    > ./notebook.pair.sh
    ```

### `notebook.sync.sh`

- **What It Does**:
  - Synchronizes paired notebooks and Python files across a directory
  - Handles bidirectional conversion between .ipynb and .py formats
  - Preserves cell structure and metadata during synchronization

- **Examples**:

  - Sync all paired notebook/Python files:

    ```bash
    > ./notebook.sync.sh
    ```

### `notebook.restore.sh`

- **What It Does**:
  - Restores paired Python files from their corresponding notebooks
  - Reverts changes to Python files to match current notebook state
  - Useful after accidental modifications to paired Python files

- **Examples**:

  - Restore Python files from notebooks:

    ```bash
    > ./notebook.restore.sh
    ```

### `notebook.remove.sh`

- **What It Does**:
  - Removes jupytext pairing configuration from notebooks
  - Cleans up paired Python files associated with notebooks
  - Reverts notebooks to standalone format without Python pairing

- **Examples**:

  - Remove jupytext pairing:

    ```bash
    > ./notebook.remove.sh
    ```

### `profile_test_durations.py`

- **What It Does**:
  - Analyzes and visualizes test execution time distributions
  - Parses test logs to extract duration data
  - Creates histograms and statistics for performance profiling
  - Identifies slow tests and performance bottlenecks

- **Examples**:

  - Profile test execution durations from log data:

    ```bash
    > ./profile_test_durations.py
    ```

### `fix_vim_plugin.sh`

- **What It Does**:
  - Resolves compatibility issues with Vim notebook editing plugins
  - Patches or reinstalls Vim extensions for Jupyter integration
  - Ensures Vim mode works correctly with notebook environment

- **Examples**:

  - Fix Vim plugin integration issues:

    ```bash
    > ./fix_vim_plugin.sh
    ```
