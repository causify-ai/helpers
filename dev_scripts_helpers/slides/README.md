# Summary

This directory contains tools for processing lecture slides and generating images
using AI services.

# Description of Files

- `generate_class_images.py`
  - Generates multiple images using OpenAI's DALL-E API from text prompts with
    quality options
- `process_lessons.py`
  - Generates PDF slides and reading scripts for lecture materials from text
    source files
- `process_slides.py`
  - Processes markdown slides using LLM prompts for transformation and quality
    checks

# Description of Executables

## `generate_class_images.py`

### What It Does

- Generates multiple images using OpenAI's DALL-E 3 API from text prompts
- Supports both standard and HD quality image generation in 1024x1024 resolution
- Includes special workload mode for generating predefined image sets for course
  materials

### Examples

- Generate 5 HD quality images from a prompt:
  ```bash
  > ./generate_class_images.py "A sunset over mountains" --dst_dir ./images
  ```

- Generate standard quality images with custom count:
  ```bash
  > ./generate_class_images.py "A cat wearing a hat" --dst_dir ./images --count 3 --low_res
  ```

- Generate images for MSLM610 course workload:
  ```bash
  > ./generate_class_images.py --dst_dir ./course_images --workload MSLM610
  ```

- Provide custom OpenAI API key:
  ```bash
  > ./generate_class_images.py "Abstract art" --dst_dir ./images --api_key YOUR_API_KEY
  ```

## `process_lessons.py`

### What It Does

- Converts lecture text source files to PDF slides using notes_to_pdf.py
- Generates reading scripts from lecture materials with transition text
- Supports batch processing of multiple lectures using pattern matching

### Examples

- Generate PDF slides for all lectures in lesson 01:
  ```bash
  > ./process_lessons.py --lectures "01*" --class msml610 --action pdf
  ```

- Generate both PDF and script for a specific lecture:
  ```bash
  > ./process_lessons.py --lectures "01.1" --class data605 --action pdf --action script
  ```

- Process specific slide range in a single lecture:
  ```bash
  > ./process_lessons.py --lectures "02.3" --class msml610 --limit "5:10" --action pdf
  ```

- Process multiple lecture patterns with dry run:
  ```bash
  > ./process_lessons.py --lectures "01*:02*:03.1" --class data605 --dry_run
  ```

## `process_slides.py`

### What It Does

- Extracts individual slides from markdown files and processes each with LLM
  prompts
- Supports various actions like slide reduction, text checking, and improvement
- Provides parallel processing with incremental execution and error recovery

### Examples

- Process slides with LLM transformation:
  ```bash
  > ./process_slides.py --in_file lecture.txt --action slide_reduce --out_file output.txt --use_llm_transform
  ```

- Check slide quality and generate report:
  ```bash
  > ./process_slides.py --in_file lecture.txt --action text_check --out_file check_report.txt --use_llm_transform
  ```

- Process specific slide range with parallel execution:
  ```bash
  > ./process_slides.py --in_file lecture.txt --action slide_reduce --out_file output.txt --limit "1:5" --num_threads 4
  ```

- Continue processing on errors with multiple attempts:
  ```bash
  > ./process_slides.py --in_file lecture.txt --action slide_reduce --out_file output.txt --no_abort_on_error --num_attempts 3 --skip_on_error
  ```
