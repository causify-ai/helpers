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

### 2. `find_lesson_packages.py`
Finds relevant Python packages based on lecture content.

**Example:**
```bash
find_lesson_packages.py \
  --in_file Lesson02-Techniques.summary.txt \
  --output_file Lesson02-Techniques.packages.txt
```

**Parameters:**
- `--in_file`: Path to input file (typically a summary file)
- `--output_file`: Output file for the package list

### 3. `create_lesson_project.py` 
Generates projects from lecture content using found packages.

**Generate Easy Projects:**
```bash
create_lesson_project.py \
  --in_file Lesson02-Techniques.summary.txt \
  --action create_project \
  --level easy \
  --packages_file Lesson02-Techniques.packages.txt
```

**Parameters:**
- `--in_file`: Path to input file (typically a summary file)
- `--action`: Action to perform (create_project)
- `--level`: Difficulty level for projects (easy, medium, hard)
- `--packages_file`: Optional path to packages file to integrate into projects

### 4. `create_all_class_projects.py`
Batch processes multiple lecture files following the complete workflow.

**Example:**
```bash
create_all_class_projects.py \
  --input_dir ~/src/umd_msml6101/msml610/lectures_source \
  --action both \
  --output_dir class_projects
```

**Parameters:**
- `--input_dir`: Directory containing all lecture files
- `--action`: Action to perform (generate_summary, generate_projects, or both)
- `--output_dir`: Directory to store generated files

**Workflow executed by this script:**
1. Creates summaries using `create_markdown_summary.py`
2. Finds packages using `find_lesson_packages.py` (on summaries)
3. Creates projects using `create_lesson_project.py` (with summaries and packages)

## Workflow

1. **Single Lecture Processing:**
   - First generate a summary using `create_markdown_summary.py`
   - Find relevant packages using `find_lesson_packages.py` on the summary
   - Create projects at desired difficulty with `create_lesson_project.py` using both summary and packages

2. **Batch Processing:**
   - Use `create_all_class_projects.py` to process an entire directory of lectures
   - Automatically executes the complete workflow for each lecture file:
     - Generates summaries
     - Finds relevant packages based on summaries
     - Creates projects using summaries and packages
   - Organizes output in a structured directory

## Output Files

- **Summaries**: `.summary.txt` files with key lecture points
- **Packages**: `.packages.txt` files listing relevant Python packages and tools
- **Projects**: `.projects.easy.txt`, `.projects.medium.txt`, `.projects.hard.txt` files with project descriptions at specified difficulty levels
- **Batch Output**: All files organized in the specified output directory