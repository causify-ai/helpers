# Generate Videos

Tools for video generation and manipulation. Supports conversion between media formats, Synthesia API integration, PDF animation, and presentation video composition with picture-in-picture overlays.

## Structure of the Dir

This directory has no subdirectories.

## Description of Files

- `convert_pdf_to_flip_video.py`
  - Create page-flip animation from PDF with customizable transitions
- `convert_png_to_movie.py`
  - Convert PNG images to separate MP4 files with specified duration
- `create_presentation_video.py`
  - Compose presentation video from slides with picture-in-picture overlays
- `download_synthesia_video.py`
  - Download completed Synthesia API videos using download URLs
- `extract_png_from_ppt.py`
  - Extract images and convert PowerPoint slides to PNG format
- `generate_slide_script.py`
  - Generate presentation scripts from markdown slides using LLM
- `generate_synthesia_videos.py`
  - Create avatar videos from text scripts via Synthesia API
- `get_synthesia_status.py`
  - Retrieve and display Synthesia video generation job status
- `stop_synthesia_videos.py`
  - Cancel Synthesia video generation jobs via API

# Description of Executables

## `convert_png_to_movie.py`

### What It Does

- Converts individual PNG files to separate MP4 videos using moviepy
- Each image displayed for specified duration
- Batch processing support for directory of images

### Examples

- Convert PNG directory to MP4s:
  ```bash
  > convert_png_to_movie.py --in_dir ./slides --duration 3.0
  ```

## `create_presentation_video.py`

### What It Does

- Composes presentation video from slide MP4s with picture-in-picture overlays
- Supports custom PIP positioning via plan-based configuration
- Handles multiple video layers and transitions

### Examples

- Create presentation with PIP:
  ```bash
  > create_presentation_video.py --in_dir ./videos --out_file final.mp4
  ```

## `extract_png_from_ppt.py`

### What It Does

- Extracts embedded images from PowerPoint presentations
- Converts PowerPoint slides to PNG format
- Batch processing for multiple presentations

### Examples

- Extract images from presentation:
  ```bash
  > extract_png_from_ppt.py --input presentation.pptx --output ./images
  ```

## `generate_slide_script.py`

### What It Does

- Generates presentation scripts from markdown slides using LLM
- Groups N slides per LLM call for efficient processing
- Identifies slides by markdown headers starting with '\*'

### Examples

- Generate script from slides:
  ```bash
  > generate_slide_script.py --in_file slides.md --out_file script.md --slides_per_group 3
  ```

## `generate_synthesia_videos.py`

### What It Does

- Creates avatar videos from text scripts via Synthesia API
- Supports avatar selection and customization
- Dry-run mode for testing without API calls

### Examples

- Generate videos with dry run:
  ```bash
  > generate_synthesia_videos.py --dry_run --in_dir videos -v DEBUG
  ```

- Generate specific slide range:
  ```bash
  > generate_synthesia_videos.py --in_dir videos --slide 002:009
  ```

## `get_synthesia_status.py`

### What It Does

- Retrieves video generation job status from Synthesia API
- Displays formatted table with job IDs, timestamps, and status
- Shows download availability for completed videos

### Examples

- Check Synthesia job status:
  ```bash
  > get_synthesia_status.py
  ```

## `download_synthesia_video.py`

### What It Does

- Downloads completed Synthesia videos using download URLs
- Saves videos with meaningful filenames
- Batch download support for multiple jobs

### Examples

- Download completed videos:
  ```bash
  > download_synthesia_video.py --ids "id1 id2 id3"
  ```

## `stop_synthesia_videos.py`

### What It Does

- Cancels in-progress Synthesia video generation jobs
- Uses Synthesia API cancel endpoint
- Batch cancellation support

### Examples

- Cancel video generation jobs:
  ```bash
  > stop_synthesia_videos.py --ids "id1 id2 id3"
  ```

## `convert_pdf_to_flip_video.py`

### What It Does

- Creates page-flip animation from PDF documents
- Supports multiple transition styles (crossfade, slide)
- Customizable frame rate and page duration

### Examples

- Convert PDF to flip video:
  ```bash
  > convert_pdf_to_flip_video.py file.pdf --out out.mp4 --fps 30 --page-duration 2.0 --transition 0.5 --style crossfade
  ```

# Description of Workflows

## Complete Synthesia Video Pipeline

1. Check current Synthesia job status:
   ```bash
   > get_synthesia_status.py
   ```

2. Generate new Synthesia videos in dry-run mode:
   ```bash
   > generate_synthesia_videos.py --dry_run --in_dir videos -v DEBUG
   ```

3. Monitor job completion status:
   ```bash
   > get_synthesia_status.py
   ```

4. Download completed videos:
   ```bash
   > download_synthesia_video.py --ids "job_id1 job_id2"
   ```

## Video Composition Workflow

1. Convert slides to PNG format:
   ```bash
   > extract_png_from_ppt.py --input slides.pptx --output ./slides_png
   ```

2. Convert PNGs to individual MP4s:
   ```bash
   > convert_png_to_movie.py --in_dir ./slides_png --duration 3.0
   ```

3. Compose presentation with overlays:
   ```bash
   > create_presentation_video.py --in_dir ./slide_videos --out_file presentation.mp4
   ```
