# mdm - Unified Markdown File Manager

- Single command to manage research ideas, blog posts, Claude Code skills, and short stories across multiple repositories
- Instead of remembering different commands and directory paths, access all markdown content from anywhere with one interface

## Quick Start

- List all skills:
  ```bash
  > mdm skill list
  ```
- Edit a skill (or create if it doesn't exist):
  ```bash
  > mdm skill edit blog.add_figures
  ```
- Find research items matching a pattern:
  ```bash
  > mdm research list causal
  ```
- Get the full path to a content directory:
  ```bash
  > mdm blog directory
  ```

## The Problem Solved

- Without `mdm`, managing markdown content required:
  - Remembering separate bash script families: `skill*`, `blog*`, `res*`, `story*`
  - Navigating to different directories for different content types
  - Context switching between multiple workflows and commands
  - Looking up directory locations and specific syntax for each type
- `mdm` provides one command with a single interface across all types

## Content Types

- `mdm` manages four types of markdown content, each stored in its own location:

| Type | Location | Purpose |
| :--- | :--- | :--- |
| `skill` | `<helpers_root>/.claude/skills/` | Claude Code skills and extensions |
| `blog` | `<blog_repo>/blog/posts/` | Blog posts |
| `research` | `<umd_classes1>/research/ideas/` | Research ideas and notes |
| `story` | `<notes1>/short_stories/` | Short stories |

## Usage Syntax

- Command format:
  ```bash
  > mdm <type> <action> [name_filter]
  ```
- `type`: Content type (skill, blog, research, story)
- `action`: What to do with the content
- `name_filter`: Optional pattern to narrow results (not all actions support this)

## Actions

- **list**: Show markdown files
  - Lists markdown files for the given type, formatted for easy scanning
  - Usage:
    ```bash
    > mdm skill list
    > mdm blog list search
    > mdm research list
    ```
  - Output format varies by type:
    - Skills: clean skill names (e.g., `blog.add_figures`)
    - Other types: full file paths with directory context

- **full_list**: Show all files with paths
  - Displays complete file paths for understanding directory structure
  - Usage:
    ```bash
    > mdm skill full_list
    > mdm blog full_list tutorial
    ```

- **describe**: Show file descriptions
  - Displays metadata and descriptions (primarily for skills with frontmatter)
  - Usage:
    ```bash
    > mdm skill describe blog.add_figures
    ```

- **edit**: Open or create files
  - Opens file in vim with automatic template generation for new files:
    - Blog posts: YAML frontmatter (title, author, date, TL;DR)
    - Skills: summary section headers
    - Research items: headers with idea names
  - Usage:
    ```bash
    > mdm skill edit new_feature_name
    > mdm blog edit "My Blog Post"
    > mdm research edit analysis
    ```

- **directory**: Get content path
  - Prints the directory path for the given type (useful for scripting)
  - Usage:
    ```bash
    > mdm skill directory
    > mdm blog directory
    ```

- **types**: List unique prefixes
  - Shows unique type prefixes from skill names (useful when organized by category)
  - Usage:
    ```bash
    > mdm skill types
    ```

## Smart Prefix Matching

- Both type and action names support prefix matching where the first match wins
- Reduces typing by using abbreviations

- Type shortcuts:
  - `sk` -> `skill`
  - `bl` -> `blog`
  - `res` -> `research`
  - `st` -> `story`

- Action shortcuts:
  - `l` -> `list`
  - `f` -> `full_list`
  - `d` -> `describe` (first match; `directory` also starts with `d`)
  - `e` -> `edit`
  - `t` -> `types`

- Examples with shortcuts:
  ```bash
  > mdm sk l
  > mdm bl e My_Post
  > mdm res l causal
  > mdm st f
  ```

## Common Workflows

- Creating new content:
  ```bash
  > mdm skill edit your_skill_name
  > mdm blog edit "My New Article"
  > mdm research edit "Idea Title"
  ```

- Finding existing content:
  ```bash
  > mdm skill list test
  > mdm blog full_list
  > mdm research list
  ```

- Working with directories:
  ```bash
  > mdm skill directory
  > cd "$(mdm research directory)"
  > ls "$(mdm blog directory)"
  ```

- Viewing metadata:
  ```bash
  > mdm skill describe blog.add_figures
  ```

## Tips and Conventions

- **Naming**: Use underscores for spaces in file names (e.g., `My_Blog_Post.md`)
- **Skills**: Follow the dot-separated naming convention (e.g., `category.skill_name`)
- **Filtering**: Use lowercase patterns when searching; matching is case-sensitive
- **Templates**: `edit` action automatically creates properly formatted templates for new files
- **Scripting**: Use `directory` action to get paths for shell scripts and automation
