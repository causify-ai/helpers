This script extracts images from a Jupyter notebook annotated with tags to
determine which cells and how they need to be saved:

```bash
# Extract images from notebook and save them to `screenshots` directory:
> dev_scripts_helpers/notebooks/extract_notebook_images.py \
    --in_notebook_filename ./dev_scripts_helpers/notebooks/test/outcomes/Test_run_dockerized_notebook_image_extractor1.test_run_dockerized_notebook_image_extractor/input/test_notebook_image_extractor.ipynb \
    --out_image_dir screenshots
```

The notebook contains tags inside the cells in the format below:
```text
# start_extract(<mode>)=<output_filename>
...
# end_extract
```

Example:

1. To extract only the input code:
    ```python
    # start_extract(only_input)=input_code.py
    def test_func():
        return "Test"
    # end_extract
    ```

2. To extract only the output of code:
    ```python
    # start_extract(only_output)=output.png
    print("This is the output")
    # end_extract
    ```

3. To extract both code and output:
    # start_extract(all)=full_output.html
    ```python
    print("This is both code and output")
    ```
    # end_extract
    ```
