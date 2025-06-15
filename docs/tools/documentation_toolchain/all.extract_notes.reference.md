# 

- The documentation is:
  - `docs/tools/documentation_toolchain/all.extract_notebook_images.how_to_guide.md`
  - `docs/tools/documentation_toolchain/all.extract_notebook_images.reference.md`

- This is implemented as a dockerized executables and thus there are two scripts:
  - `dev_scripts_helpers/notebooks/extract_notebook_images.py`
    - Parses the command line options
    - Create a Docker image with all the dependencies and run it
  - `dev_scripts_helpers/notebooks/dockerized_extract_notebook_images.py`
    - Instantiate `_NotebookImageExtractor`
    - Run the image extraction

- The testing of the scripts are:
  - `dev_scripts_helpers/notebooks/test/test_extract_notebook_images.py`
    - Test the end-to-end script with a handcrafted notebook
      `dev_scripts_helpers/notebooks/test/outcomes/Test_run_dockerized_notebook_image_extractor1.test_run_dockerized_notebook_image_extractor/input/test_notebook_image_extractor.ipynb`
  - `dev_scripts_helpers/notebooks/test/test_dockerized_extract_notebook_images.py`
