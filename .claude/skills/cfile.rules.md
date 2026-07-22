- This file describe the format of a cfile quickfile for vim

# File Format
- Given file locations, create a vim quickfile cfile so that the user can
  navigate the proposed locations with a command like
  ```bash
  > vim -c "cfile cfile"
  ```
- The cfile has a format:
  ```verbatim
  /path/to/file1.py:10:1: Replace with function ...
  /path/to/file1.py:12:1:
  /path/to/file1.py:12:1:
  ```

# Example
```verbatim
msml610/lectures_source/README.md:12:1 [HIGH] Claims "pip install X" but pip package is named "X-lib"
msml610/lectures_source/README.md:5:1 [HIGH] Add example of basic usage after the description
helpers/docs.md:8:1 [MEDIUM] Link to API docs is outdated (2023 version, current is 2024)
```

# File Name
- The file should be saved in `cfile`, unless specified
