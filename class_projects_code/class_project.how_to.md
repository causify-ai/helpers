# How to Generate Class Projects

This guide explains how to use the class project generation scripts to create educational materials from lecture content.

## Scripts Overview

The following scripts help generate summaries, projects, and packages from lecture materials:

### 1. `create_markdown_summary.py`
Generates a summary of lecture content with configurable bullet points.

**Example:**
```bash
create_markdown_summary.py \
  --in_file ~/src/umd_msml6101/msml610/lectures_source/Lesson02-Techniques.txt \
  --action summarize \
  --out_file Lesson02-Techniques.summary.txt \
  --use_library \
  --max_num_bullets 3
```

**Parameters:**
- `--in_file`: Path to input lecture file
- `--action`: Action to perform (summarize)
- `--out_file`: Output file for the summary
- `--use_library`: Use library functions for processing
- `--max_num_bullets`: Maximum number of bullet points per section (3)

### 2. `create_class_projects.py` 
Generates projects and finds relevant packages from lecture content.

**Generate Easy Projects:**
```bash
create_class_projects.py \
  --in_file ~/src/umd_msml6101/msml610/lectures_source/Lesson02-Techniques.txt \
  --action create_project \
  --level easy
```

**Find Related Packages:**
```bash
create_class_projects.py \
  --in_file ~/src/umd_msml6101/msml610/lectures_source/Lesson02-Techniques.txt \
  --action find_packages
```

**Parameters:**
- `--in_file`: Path to input lecture file
- `--action`: Action to perform (create_project or find_packages)
- `--level`: Difficulty level for projects (easy, medium, hard)

### 3. `generate_all_projects.py`
Batch processes multiple lecture files to generate both summaries and projects.

**Example:**
```bash
generate_all_projects.py \
  --input_dir ~/src/umd_msml6101/msml610/lectures_source \
  --action both \
  --output_dir class_projects
```

**Parameters:**
- `--input_dir`: Directory containing all lecture files
- `--action`: Action to perform (both generates summaries and projects)
- `--output_dir`: Directory to store generated projects

## Workflow

1. **Single Lecture Processing:**
   - First generate a summary using `create_markdown_summary.py`
   - Create projects at desired difficulty with `create_class_projects.py`
   - Find relevant packages for the lecture topic

2. **Batch Processing:**
   - Use `generate_all_projects.py` to process an entire directory of lectures
   - Automatically generates summaries and projects for all lecture files
   - Organizes output in a structured directory

## Output Files

- **Summaries**: `.summary.txt` files with key lecture points
- **Projects**: `.projects.txt` files with project descriptions at specified difficulty
- **Packages**: `.packages.txt` files listing relevant Python packages and tools
- **Batch Output**: Organized in `class_projects/` directory structure