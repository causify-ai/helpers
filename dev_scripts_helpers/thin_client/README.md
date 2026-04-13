# Thin Client Scripts

This directory contains scripts for setting up and managing thin client
repositories that use `helpers_root` as a submodule.

## Scripts

### `create_all_helpers_links.py`

Creates symbolic links from the current repository to standard configuration
files in `helpers_root`.

**Purpose:**

- Automates the creation of symbolic links for common configuration files
- Enables thin client repositories to share configuration with `helpers_root`
- Reduces duplication and ensures consistency across repositories

**Standard Files Linked:**

- `.claude/` - Claude Code configuration
- `.coveragerc` - Test coverage configuration
- `.gitignore` - Git ignore patterns
- `.gitleaksignore` - Gitleaks scan exclusions
- `.isort.cfg` - Import sorting configuration
- `.pre-commit-config.yaml` - Pre-commit hooks
- `CLAUDE.md` - Claude Code project context
- `conftest.py` - Pytest configuration
- `linters2/` - Linting scripts
- `pyproject.toml` - Python project configuration
- `pytest.ini` - Pytest settings

**Usage:**

```bash
# Create all missing links
> create_all_helpers_links.py

# Force recreate all links (even if they exist)
> create_all_helpers_links.py --force

# Preview what would be done without making changes
> create_all_helpers_links.py --dry_run
```

**Import as:**

```python
import dev_scripts_helpers.thin_client.create_all_helpers_links as dstcrcahl
```

**See also:**

- [Managing common files](/docs/tools/dev_system/all.runnable_repo.reference.md#managing-common-files)
- [Creating a super-repo with helpers](/docs/tools/dev_system/all.create_a_super_repo_with_helpers.how_to_guide.md#create-symbolic-links)

### `build.py`

Builds the thin environment by installing required dependencies.

**Usage:**

```bash
> build.py
```

### `setenv.sh`

Sets up the environment variables for the thin client.

**Usage:**

```bash
> source setenv.sh
```

### `tmux.py`

Creates and manages tmux sessions for development.

**Usage:**

```bash
> tmux.py
```

### `sync_super_repo.sh`

Synchronizes files between a super-repo and its `helpers_root` directory.

**Usage:**

```bash
> sync_super_repo.sh
```

### `test_helpers.sh`

Tests the helpers setup in the thin environment.

**Usage:**

```bash
> test_helpers.sh
```

### `test_super_repo.sh`

Tests the super-repo setup in the thin environment.

**Usage:**

```bash
> test_super_repo.sh
```

## Related Documentation

- [Thin Environment Reference](/docs/tools/thin_environment/all.thin_environment.reference.md)
- [Creating a Super-Repo with Helpers](/docs/tools/dev_system/all.create_a_super_repo_with_helpers.how_to_guide.md)
- [Managing Symbolic Links Between Directories](/docs/tools/dev_system/all.replace_common_files_with_script_links.md)
