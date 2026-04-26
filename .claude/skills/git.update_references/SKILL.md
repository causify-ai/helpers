---
description: Find and update the references in other Git repos to files that were moved, renamed, or deleted in the current Git repo
---

# Step 1
- Find all the files moved, renamed, updated, or deleted in the current repo
  using a command line
  ```bash
  > invoke git_files --branch --only-print-files
  ```

- Print all the file that are moved, renamed, or deleted
  - Print the main functions changed

# Step 2
- For each file `<FILE>`, look for all the references to `<FILE>` in the repos
  - `helper`: the current repo
  - `umd_classes`: located at `~/src/umd_classes1`
  - `csfy`: located at `~/src/csfy1`
  - `orange`: located at `~/src/orange1`
  - `lemonade`: located at `~/src/lemonade1`

- You must
  - ignore searching in any Git sub repository of each repo (e.g.,
    `helpers_root`)
  - only search in files that are under Git control
  - ignore searching in symlinks (e.g., `.claude`)
  using an approach like:
  ```bash
  search_repo() {
    local repo_path=$1
    local search_term=$2

    (cd "$repo_path" && {
      # Get submodule paths to exclude
      submodules=$(git config --file .gitmodules --name-only --get-regexp path 2>/dev/null | sed 's/.*path=//' | tr '\n' '|' | sed 's/|$//')

      if [ -n "$submodules" ]; then
        git ls-files | grep -v "^($submodules)" | while read -r file; do
          [ ! -L "$file" ] && echo "$file"
        done | xargs grep "$search_term" 2>/dev/null
      else
        git ls-files | while read -r file; do
          [ ! -L "$file" ] && echo "$file"
        done | xargs grep "$search_term" 2>/dev/null
      fi
    })
  }
  ```

- Print the references in a table organized by
  - repos
  - files

- Create a vim quickfile cfile for the locations using the conventions in
  `@.claude/skills/cfile.rules.md`

- Pause and ask the user to continue

# Step 3
- Update the references in all the repos
