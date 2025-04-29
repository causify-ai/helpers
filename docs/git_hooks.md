# Git Hooks Management Documentation

This document describes the custom Git hooks implemented for the repository. The hooks are managed by the script `dev_scripts_helpers/git/git_hooks/install_hooks.py` and are used to enforce code quality and other policies.

## Overview

The Git hooks system provides three main actions:

- **install**: Creates symbolic links for Git hooks (such as `pre-commit` and `commit-msg`) in the target Git hooks directory. This ensures that custom scripts are executed during the Git commit process.
- **remove**: Deletes the installed Git hooks from the target Git hooks directory.
- **status**: Displays the current status of the hooks in both the source (within the repository) and the target Git hooks directory.

## How It Works

1. **Determining the Repository Path**:  
   The script first identifies the absolute path of the repository using helper functions, ensuring that all operations are performed in the correct context.

2. **Locating the Source of Hooks**:  
   The hooks are located in the directory `dev_scripts_helpers/git/git_hooks`. Each hook script is named after its corresponding Git phase, with a `.py` extension (e.g., `pre-commit.py`).

3. **Installing Hooks**:  
   - The script determines the target Git hooks directory by running `git rev-parse --git-path hooks`.
   - For each hook (e.g., `pre-commit`, `commit-msg`), it creates a symbolic link from the source hook file to the target directory.
   - It then applies executable permissions to both the original hook file and the symbolic link.

4. **Removing Hooks**:  
   - The script checks if the target hook file exists; if so, it uses the `unlink` command to remove it.

5. **Checking Status**:  
   - In status mode, the script lists the contents of both the source and target directories. This helps to verify that the hooks have been installed or removed as expected.

## Usage

Run the script with the appropriate action:

- **Install Hooks**:  
  ```bash
  ./dev_scripts_helpers/git/git_hooks/install_hooks.py --action install
  ```

- **Remove Hooks**:  
  ```bash
  ./dev_scripts_helpers/git/git_hooks/install_hooks.py --action remove
  ```

- **Check Hooks Status**:  
  ```bash
  ./dev_scripts_helpers/git/git_hooks/install_hooks.py --action status
  ```

## Logging and Debugging

The script uses a logging framework to record its operations. Log messages provide insight into the steps being executed, such as identifying directories, linking files, and changing permissions. These logs can be helpful for debugging issues with hook installation.

## Dependencies

The script depends on several helper modules:
- `helpers.hdbg` for error checking and debugging assertions.
- `helpers.hgit` for Git-related path manipulations.
- `helpers.hparser` for command-line argument parsing.
- `helpers.hsystem` for executing system-level commands.

## Conclusion

This custom Git hooks system provides a streamlined method to ensure that essential checks and operations are run during the commit process. For any changes or troubleshooting, the logging output offers valuable insights into the script's execution.

For further questions or contributions, please consult the repository's contributing guidelines.
