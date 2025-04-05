Extract images from a Jupyter notebook by running inside a Docker container.
This script builds the container dynamically if necessary and extracts images
from the specified Jupyter notebook using the NotebookImageExtractor module.

Extract images from notebook test_images.ipynb and save them to `screenshots`
directory.
```bash
> dev_scripts_helpers/notebooks/extract_notebook_images.py \
    -i dev_scripts_helpers/notebooks/test_images.ipynb \
    -o dev_scripts_helpers/notebooks/screenshots
```

```
# start_extract(mode)=<output_filename>
...
# end_extract
```

Example:

1. To extract only the input code:
    # start_extract(only_input)=input_code.py
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
    # start_extract(all)=full_output.html
    ```python
    print("This is both code and output")
    ```
    # end_extract
    ```
