

<!-- toc -->

- [Managing Symbolic Links Between Directories](#managing-symbolic-links-between-directories)
  * [Define](#define)
  * [Why Do We Need This Approach?](#why-do-we-need-this-approach)
  * [Workflow and Commands](#workflow-and-commands)
    + [Step 1: Replace Files with Symbolic Links](#step-1-replace-files-with-symbolic-links)
    + [Step 2: Stage Files for Modification](#step-2-stage-files-for-modification)
    + [Step 3: Restore Symbolic Links After Modifications](#step-3-restore-symbolic-links-after-modifications)
    + [Workflow Summary](#workflow-summary)
    + [Example Directory Structure](#example-directory-structure)
    + [Notes and Best Practices](#notes-and-best-practices)
    + [Conclusion](#conclusion)

<!-- tocstop -->

# Managing Symbolic Links Between Directories

## Summary

- This document describes two scripts, `create_links.py` and
  `stage_linked_file.py` used to manage symbolic links between a
  source directory and a destination directory
- These tools simplify workflows where you want to create read-only symbolic
  links for files, stage modifications, and later restore the links

## Why Do We Need This Approach?

- In our codebases, it is common to have duplicate files or files
  that are identical between two directories. Maintaining these files manually
  can lead to inefficiencies and errors:
  - Synchronization: If changes are made in one location, they may not reflect
    in the other, leading to inconsistencies
  - Accidental Modifications: Directly modifying files that should remain
    synchronized can result in unintended discrepancies

- With our approach:
  - We avoid file duplication by creating links that point to the original files
  - Links in the destination directory remain read-only, reducing the risk of
    accidental changes
  - If modifications are needed, the "staging process" ensures you can work
    safely on copies without altering the original source files
  - After the code has been developed, one can then convert copies of files, back
    to links

## Workflow and Commands

- Below is the step-by-step workflow for using these scripts

### Step 1: Replace Files with Symbolic Links

- Use `create_links.py` to replace files in `dst_dir` with read-only symbolic
  links to the corresponding files in `src_dir`

  Command:
  ```
  > create_links.py --src_dir /path/to/src --dst_dir /path/to/dst --replace_links
  ```

- What it does:
  - Scans all files in `src_dir` and checks for files with the same name and
    content in `dst_dir`
  - For each match, the file in `dst_dir` is replaced with a symbolic link
    pointing to the file in `src_dir`
  - Sets the symbolic link to `read-only` (permission 444) to prevent accidental
    modifications

- Why it is important:
  - This ensures that all common files are linked to a single source,
    eliminating duplication and keeping the directories in sync

### Step 2: Stage Files for Modification

- If you want to edit the files in `dst_dir` (which are currently symbolic
  links), use `stage_linked_file.py` to stage them. Staging replaces the
  symbolic links with writable copies of the original files

- Command:
  ```
  > stage_linked_file.py --dst_dir /path/to/dst
  ```

- What it does:
  - Finds all the symbolic links in `dst_dir`
  - Replaces each symbolic link with a writable copy of the file it points
    to
  - Sets file permissions to `644` (writable)

- Why it is important:
  - It allows safe modifications to the files without directly editing the
    original source files in `src_dir`. This ensures a clean and reversible
    workflow

### Step 3: Restore Symbolic Links After Modifications

- Once you’ve finished modifying the files, you can restore the symbolic links
  by running `create_links.py` again with the `--replace_links` flag

- Command:
  ```
  > create_links.py --src_dir /path/to/src --dst_dir /path/to/dst --replace_links
  ```

- What it does:
  - Compares the modified files in `dst_dir` to those in `src_dir`
  - Replaces the matching files with symbolic links, resetting them to
    `read-only`

- Why it is important:
  - This step cleans up your workspace and restores the optimized
    `symbolic link` structure, ensuring minimal disk usage and consistent file
    management

### Workflow Summary

- Set up `symbolic links`:
  ```
  > create_links.py --src_dir /path/to/src --dst_dir /path/to/dst --replace_links
  ```

- Stage `symbolic links` for modification:
  ```
  > stage_linked_file.py --dst_dir /path/to/dst
  ```

- Modify files as required

- After modifications, restore the `symbolic links`:
  ```
  > create_links.py --src_dir /path/to/src --dst_dir /path/to/dst --replace_links
  ```

### Example Directory Structure

- Before running `create_links.py`
  ```
  src_dir/
      file1.txt
      subdir/
          file2.txt

  dst_dir/
      file1.txt  (identical content)
      subdir/
          file2.txt  (identical content)
  ```

- After running `create_links.py`
  ```
  dst_dir/
      file1.txt -> src_dir/file1.txt  (symlink, read-only)
      subdir/
          file2.txt -> src_dir/subdir/file2.txt  (symlink, read-only)
  ```

- After running `stage_linked_file.py`
  ```
  dst_dir/
      file1.txt  (writable copy of src_dir/file1.txt)
      subdir/
          file2.txt  (writable copy of src_dir/subdir/file2.txt)
  ```
