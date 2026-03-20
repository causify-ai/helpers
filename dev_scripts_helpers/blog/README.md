# Summary

This directory contains bash utilities for managing blog posts with YAML
frontmatter in a centralized blog/posts directory.

# Description of Executables

## `blogc`

- **What It Does**
  - Creates a new draft blog post with YAML frontmatter template

- Create a new blog post named "My_New_Post":
  ```bash
  > blogc My_New_Post
  ```

## `blogd`

- **What It Does**
  - Reports the path to the blog/posts directory

- Use the blog directory in another command:
  ```bash
  > ls -la $(blogd)
  ```

## `bloge`

- **What It Does**
  - Opens a blog post in vi editor for editing
  - Searches for matching blog post files by name pattern

- Edit a blog post matching "My_New_Post" or using partial name match:
  ```bash
  > bloge My_New_Post
  ```

## `blogl`

- **What It Does**
  - Lists all blog posts in the blog/posts directory
  - Supports filtering by name pattern

- List all blog posts:
  ```bash
  > blogl
  ```

- List only draft blog posts:
  ```bash
  > ./blogl draft
  ```
