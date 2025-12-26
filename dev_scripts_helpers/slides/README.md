# Summary

This directory contains tools for processing lecture slides and generating images
using AI services.

# Structure of the Dir

- No subdirectories in this directory

# Description of Files

- `extract_png_from_pdf.py`
  - Extracts PNG images from PDF files with one image per page using sequential
    numbering
- `generate_book_chapter.py`
  - Generates book chapter from markdown with PNG or PDF, YAML preamble with
    title, and centered headers
- `header-style.tex`
  - LaTeX header customization file for pandoc PDF conversion with styled
    section headers
- `generate_class_images.py`
  - Generates multiple images using OpenAI's DALL-E API from text prompts with
    quality options
- `generate_slide_script.py`
  - Generates presentation scripts from markdown slides using LLM processing
- `process_lessons.py`
  - Generates PDF slides and reading scripts for lecture materials from text
    source files
- `process_slides.py`
  - Processes markdown slides using LLM prompts for transformation and quality
    checks
- `slides_utils.py`
  - Utility functions for extracting slides from markdown and processing slide
    images

# Description of Executables

## `extract_png_from_pdf.py`

### What It Does

- Extracts each page of a PDF file as a separate PNG image
- Numbers output files sequentially (slides001.png, slides002.png, etc.)
- Supports customizable DPI for image quality control
- Creates output directory automatically with optional from-scratch mode

### Examples

- Extract all pages from a PDF with default settings:
  ```bash
  > ./extract_png_from_pdf.py --input_file data605/lectures/Lesson01.1-Intro.pdf --output_dir output
  ```

- Extract with higher DPI for better image quality:
  ```bash
  > ./extract_png_from_pdf.py --input_file lecture.pdf --output_dir slides --dpi 300
  ```

- Create output directory from scratch:
  ```bash
  > ./extract_png_from_pdf.py --input_file presentation.pdf --output_dir ./images/ --from_scratch
  ```

- Process with debug logging:
  ```bash
  > ./extract_png_from_pdf.py --input_file slides.pdf --output_dir ./output/ --log_level DEBUG
  ```

## `generate_book_chapter.py`

### What It Does

- Processes markdown slides with PNG images or PDF file to create book chapter
  format
- Extracts title from markdown file (e.g., from `\text{\blue{Lesson 2.1:
  Git}}`) and adds YAML preamble for pandoc metadata
- Extracts PNG images from PDF automatically when --input_pdf_file is provided
- Validates that the number of slides in markdown matches the number of PNG
  files (expects num_slides + 1 = num_pngs to account for title slide)
- Properly aligns title slide (first PNG) with content slides (remaining PNGs)
  to ensure header, slide image, and commentary are synchronized
- First slide (PNG 1) is treated as title slide with only the image (no title
  or commentary)
- Content slides (PNG 2+) are paired with corresponding markdown slides, with
  centered headers formatted as "idx / tot: title" and LLM-based commentary
- Creates pandoc-friendly markdown with page breaks before slides, centered
  images, and configurable image width
- Formats output with prettier for consistent markdown formatting
- Creates markdown output with PNG references and detailed commentary for each
  slide

### Examples

- Generate book chapter from markdown and PNG directory:
  ```bash
  > ./generate_book_chapter.py --input_file data605/lectures_source/Lesson01.1-Intro.txt --input_png_dir output --output_dir test
  ```

- Generate book chapter from markdown and PDF file:
  ```bash
  > ./generate_book_chapter.py --input_file data605/lectures_source/Lesson01.1-Intro.txt --input_pdf_file data605/lectures/Lesson01.1-Intro.pdf --output_dir test
  ```

- Process with custom image width:
  ```bash
  > ./generate_book_chapter.py --input_file lecture.txt --input_pdf_file lecture.pdf --output_dir ./book_chapters/ --image_width 50%
  ```

- Process with custom DPI for PDF extraction:
  ```bash
  > ./generate_book_chapter.py --input_file lecture.txt --input_pdf_file lecture.pdf --output_dir ./book_chapters/ --dpi 300
  ```

- Process slides with verbose logging:
  ```bash
  > ./generate_book_chapter.py --input_file lecture.txt --input_png_dir ./png_slides/ --output_dir ./book_chapters/ -v DEBUG
  ```

### Converting to PDF with pandoc

After generating the book chapter markdown, convert it to PDF using pandoc with
custom header styling:

- Convert markdown to PDF with styled headers:
  ```bash
  > pandoc test/Lesson01.1-Intro.book_chapter.txt -o output.pdf --include-in-header=header-style.tex
  ```

- Convert with additional pandoc options:
  ```bash
  > pandoc test/Lesson01.1-Intro.book_chapter.txt -o output.pdf --include-in-header=header-style.tex --pdf-engine=xelatex
  ```

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

## `generate_slide_script.py`

### What It Does

- Processes markdown slides and generates presentation scripts using LLM
- Groups slides for batch processing to optimize LLM API calls
- Supports limiting slide ranges and customizable grouping strategies

### Examples

- Generate script from markdown slides with default settings:
  ```bash
  > ./generate_slide_script.py --in_file slides.md --out_file script.md
  ```

- Process slides in groups of 5 for more context:
  ```bash
  > ./generate_slide_script.py --in_file lecture.txt --out_file script.txt --slides_per_group 5
  ```

- Process specific slide range:
  ```bash
  > ./generate_slide_script.py --in_file slides.md --out_file script.md --limit "10:20"
  ```

- Enable verbose logging for debugging:
  ```bash
  > ./generate_slide_script.py --in_file slides.md --out_file script.md --log_level DEBUG
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
