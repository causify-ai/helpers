# Summary

Unified markdown file manager script and documentation for managing research ideas,
blog posts, short stories, and Claude Code skills across multiple repositories.

# Overview

The `md.py` script provides a single, consistent interface for managing markdown
files across four different content types and repositories. It unifies and simplifies
the existing bash script families (`skill*`, `blog*`, `res*`, `story*`) into one
tool with prefix-matching CLI arguments.

# Content Types

- `research`: Research ideas stored in `<umd_classes1>/research/ideas/`
- `blog`: Blog posts stored in `<blog_repo>/blog/posts/`
- `story`: Short stories stored in `<notes1>/short_stories/`
- `skill`: Claude Code skills stored in `<helpers_root>/.claude/skills/`

# Actions

- `list`: List markdown files in the directory (with optional name filter)
  - For skills: shows skill names only (e.g., `blog.add_figures`)
  - For other types: shows full file paths
- `full_list`: List markdown files with full paths (with optional name filter)
- `edit`: Open a file in vim for editing (creates with template if not found)
- `directory`: Print the directory path for the given type

# Usage Examples

List all skills (shows skill names only).

```bash
> python dev_scripts_helpers/md.py skill list
```

List all skills with full file paths.

```bash
> python dev_scripts_helpers/md.py skill full_list
```

List research items matching a pattern.

```bash
> python dev_scripts_helpers/md.py research list causal
```

Edit or create a blog post (creates with YAML template if new).

```bash
> python dev_scripts_helpers/md.py blog edit My_Post
```

Edit or create a short story.

```bash
> python dev_scripts_helpers/md.py story edit buzzati.una_cosa
```

Print the research ideas directory path.

```bash
> python dev_scripts_helpers/md.py research directory
```

# Prefix Matching

Type and action arguments support prefix matching (first match wins):

- `sk` matches `skill`
- `bl` matches `blog`
- `res` matches `research`
- `l` matches `list`
- `f` matches `full_list`
- `e` matches `edit`
- `d` matches `directory`

# Unified Interface

The `md.py` script replaces these individual bash script families:

- `skillc`, `skilld`, `skille`, `skilll`: skill management
- `blogc`, `blogd`, `bloge`, `blogl`: blog management
- `resc`, `resd`, `rese`, `resl`: research management
- `storyc`, `storyd`, `storye`, `storyl`: story management

# Templates

When creating a new file with the `edit` action, `md.py` automatically generates
templates appropriate for each content type:

- `blog`: YAML frontmatter with title, author, date, and TL;DR section
- `skill`: Summary section header
- `research`: Header with the idea name
- `story`: YAML frontmatter with title, author, and date fields
