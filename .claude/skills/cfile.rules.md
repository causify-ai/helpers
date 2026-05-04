- This file describe the format of a cfile quickfile for vim

- Given a summary of file locations, create a vim quickfile cfile so that the
  user can navigate the proposed locations with a command like
  ```bash
  > vim -c "cfile cfile"
  ```
- The cfile has a format
  ```verbatim
  /path/to/file1.py:10:1: Replace with function ...
  /path/to/file1.py:12:1:
  /path/to/file1.py:12:1:
  ```
- The file should be saved in `cfile`
