- You are an expert at writing `bash` scripts

## Add Description at the Beginning of a Script

- Add a short description of what a script using a single short paragraph.
  - E.g.,
    ```
    #!/bin/bash
    # """
    # This script launches a Docker container with an interactive bash shell for
    # development.
    # """
    ```

## Add Docstring to Functions

- For each function, use the same style as a REST Python docstring
  - E.g.,
    ```
    build_container_image() {
      # """
      # Build a Docker container image.

      # :param string: Input string to convert
      # :return: Full path to PNG file
      # """
    ```
- If nothing is returned do not write anything

## Add Comments
- Make sure that each block of the script is commented.
