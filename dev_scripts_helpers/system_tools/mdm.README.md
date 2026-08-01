`mdm` unifies management of research ideas, blog posts, and Claude Code
skills across multiple repositories into one powerful command-line tool.

## The Problem: Scattered Content

- Different types of markdown content live in separate directories
    - Blog posts in one location
    - Claude Code skills in another
    - Research ideas in a third
- Each content type requires knowing:
    - Its directory location
    - Its specific command prefix
    - Its unique workflow
- Searching across content types means context switching and remembering
  multiple commands
- `mdm` solves this by unifying everything into a single interface

## What Is Mdm?

- A unified markdown file manager that consolidates four separate bash script
  families into one tool
    - Replaces `skill*`, `blog*`, `res*`, and `story*` command families
    - Provides consistent interface for all content types
    - Supports prefix matching to reduce typing
- Enables you to manage all markdown content from anywhere
    - No need to navigate to specific directories
    - One command for all operations

## Content Types Managed

- `mdm` organizes content into four types, each stored separately:
    - **research**: Research ideas in `<umd_classes1>/research/ideas/`
    - **blog**: Blog posts in `<blog_repo>/blog/posts/`
    - **story**: Short stories in `<notes1>/short_stories/`
    - **skill**: Claude Code skills in `<helpers_root>/.claude/skills/`
- Each type maintains its own directory structure and conventions

## Core Actions

- **list**: List markdown files with optional filtering
    - Shows skill names only for skills (e.g., `blog.add_figures`)
    - Shows full file paths for other content types
    - Supports optional name filters to narrow results
- **full_list**: Display all markdown files with complete paths
    - Useful for seeing directory structure
    - Supports optional name filtering
- **describe**: Show descriptions of markdown files
    - Primarily works with skills containing metadata
- **edit**: Open file in vim with automatic template generation
    - Creates new files with appropriate templates if they don't exist
    - Blog posts get YAML frontmatter with title, author, date, and TL;DR
    - Skills get summary section headers
    - Research items get headers with idea names
- **directory**: Print the directory path for given type
    - Useful for scripting and automation
- **types**: Print unique prefixes before first dot

## Smart Prefix Matching

- Both type and action arguments support prefix matching where first match wins
- Type prefixes:
    - `sk` -> `skill`
    - `bl` -> `blog`
    - `res` -> `research`
    - `st` -> `story`
- Action prefixes:
    - `l` -> `list`
    - `f` -> `full_list`
    - `d` -> `describe` or `directory` (first match)
    - `e` -> `edit`
    - `t` -> `types`
- Allows shortcuts like `mdm bl l` instead of `mdm blog list`

## Practical Usage Examples

- List all skills to inventory what you have available:
    - `mdm skill list` shows skill names only
- See full paths for all skills:
    - `mdm skill full_list` includes directory paths
- Filter research items by pattern:
    - `mdm research list causal` finds items containing "causal"
- Create or edit a new blog post:
    - `mdm blog edit My_New_Post` opens vim with template
- Get the directory path for a content type:
    - `mdm research directory` prints path to research folder
- See unique content types in skills:
    - `mdm skill types` shows unique prefixes
