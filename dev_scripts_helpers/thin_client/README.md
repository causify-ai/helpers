# Thin Client

Scripts for setting up and managing thin client repositories using `helpers_root` as a submodule. Automates configuration linking, environment setup, and testing workflows.

## Structure of the Dir

This directory has no subdirectories.

## Description of Files

- `build.py`
  - Install required dependencies for thin environment
- `create_all_helpers_links.py`
  - Create symbolic links to configuration files in helpers_root
- `setenv.sh`
  - Set up environment variables for thin client development
- `sync_super_repo.sh`
  - Synchronize files between super-repo and helpers_root
- `test_helpers.sh`
  - Test helpers setup in thin environment
- `test_super_repo.sh`
  - Test super-repo setup in thin environment
- `tmux.py`
  - Create and manage tmux sessions for development

# Description of Executables

## `create_all_helpers_links.py`

### What It Does

- Automates creation of symbolic links to helpers_root configuration files
- Links standard config files to enable repository configuration sharing
- Reduces duplication and ensures consistency across thin client repos
- Supports force recreation and dry-run modes

### Examples

- Create all missing configuration links:
  ```bash
  > create_all_helpers_links.py
  ```

- Force recreate all links (overwrite existing):
  ```bash
  > create_all_helpers_links.py --force
  ```

- Preview changes without executing:
  ```bash
  > create_all_helpers_links.py --dry_run
  ```

## `build.py`

### What It Does

- Installs required dependencies for thin environment setup
- Configures Python packages and system requirements
- Prepares development environment for thin client workflows

### Examples

- Build thin environment:
  ```bash
  > build.py
  ```

## `setenv.sh`

### What It Does

- Configures environment variables for thin client development
- Sets up paths and development configuration
- Activates thin client environment settings

### Examples

- Source environment configuration:
  ```bash
  > source setenv.sh
  ```

## `sync_super_repo.sh`

### What It Does

- Synchronizes files between super-repo and helpers_root submodule
- Ensures consistency across multiple repositories
- Updates linked configurations and shared utilities

### Examples

- Sync super-repo configuration:
  ```bash
  > sync_super_repo.sh
  ```

## `tmux.py`

### What It Does

- Creates and manages tmux sessions for development workflows
- Configures terminal multiplexing for parallel development
- Sets up project-specific session layouts

### Examples

- Create tmux session:
  ```bash
  > tmux.py
  ```

## `test_helpers.sh`

### What It Does

- Validates helpers setup in thin environment
- Runs sanity checks on helper module installation
- Verifies thin environment configuration

### Examples

- Test helpers installation:
  ```bash
  > test_helpers.sh
  ```

## `test_super_repo.sh`

### What It Does

- Validates super-repo setup in thin environment
- Runs integration tests for super-repo configuration
- Verifies submodule and symlink integrity

### Examples

- Test super-repo setup:
  ```bash
  > test_super_repo.sh
  ```
