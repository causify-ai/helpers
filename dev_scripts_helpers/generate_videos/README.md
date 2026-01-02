<!-- toc -->

- [Video Narration Tools](#video-narration-tools)
  * [Setup](#setup)
  * [Tools Overview](#tools-overview)
    + [`convert_png_to_movie.py`](#convert_png_to_moviepy)
    + [`create_presentation_video.py`](#create_presentation_videopy)
    + [`download_synthesia_video.py`](#download_synthesia_videopy)
    + [`extract_png_from_ppt.py`](#extract_png_from_pptpy)
    + [`generate_slide_script.py`](#generate_slide_scriptpy)
    + [`generate_synthesia_videos.py`](#generate_synthesia_videospy)
    + [`get_synthesia_status.py`](#get_synthesia_statuspy)
    + [`pdf_to_flip_video.py`](#pdf_to_flip_videopy)
    + [`stop_synthesia_videos.py`](#stop_synthesia_videospy)
  * [Synthesia Workflow](#synthesia-workflow)
- [To Reorg](#to-reorg)

<!-- tocstop -->

# Video Narration Tools

## Setup

- Install the needed packages

  ```bash
  > python3 -m venv ~/src/venv/client_venv.movie

  # Activate venv
  > source ~/src/venv/client_venv.movie/bin/activate

  > pip install -r dev_scripts_helpers/videos/requirements_video.txt
  ```

- Activate env
  ```bash
  > source ~/src/venv/client_venv.movie/bin/activate
  ```

## Tools Overview

### `convert_png_to_movie.py`

Converts individual PNG files to separate MP4 movies using moviepy. Each movie
displays a single image for a specified duration.

Example:

```bash
> convert_png_to_movie.py --in_dir ./slides --duration 3.0
```

### `create_presentation_video.py`

Creates a composite presentation video from slide MP4 files with
picture-in-picture (PIP) overlays. Supports both default positioning and custom
plan-based positioning for pip and comment videos.

Example:

```bash
> create_presentation_video.py --in_dir ./videos --out_file final.mp4
```

### `download_synthesia_video.py`

Downloads completed videos from the Synthesia API using their download URLs and
saves them with meaningful names.

Example:

```bash
> download_synthesia_video.py --ids "id1 id2 id3"
```

### `extract_png_from_ppt.py`

Extracts images and converts slides from PowerPoint presentations to PNG files.
Can extract both embedded images and convert slides to images.

### `generate_slide_script.py`

Generates presentation scripts from markdown slides using LLM processing.
Processes markdown slides (identified by headers starting with '\*') and creates
scripts by passing groups of N slides to an LLM for analysis.

Example:

```bash
> generate_slide_script.py --in_file slides.md --out_file script.md --slides_per_group 3
```

### `generate_synthesia_videos.py`

Creates videos from text scripts using the Synthesia API with chosen avatars.
Supports dry-run mode for testing.

Example:

```bash
> generate_synthesia_videos.py --in_dir videos --limit "1:3" --dry_run
```

### `get_synthesia_status.py`

Retrieves and displays the status of video generation jobs from the Synthesia
API in a formatted table.

Example:

```bash
> get_synthesia_status.py
ID                                    Created              Updated              Title                          Status    Download
------------------------------------  -------------------  -------------------  -----------------------------  --------  --------
260927bd-aedf-4a62-8dd8-06abdd434900  2025-08-30 10:26:33  2025-08-30 10:30:16  Untitled                       complete  Yes
```

### `pdf_to_flip_video.py`

Creates a movie from a PDF that simulates turning pages. Supports different
transition styles like crossfade and slide animations.

Example:

```bash
> pdf_to_flip_video.py file.pdf --out out.mp4 --fps 30 --page-duration 2.0 --transition 0.5 --style crossfade
```

### `stop_synthesia_videos.py`

Cancels video generation jobs from the Synthesia API using their Cancel Video
Generation endpoint.

Example:

```bash
> stop_synthesia_videos.py --ids "id1 id2 id3"
```

## Synthesia Workflow

- Check the status of Synthesia:

  ```bash
  > get_synthesia_status.py
  ID                                    Created              Updated              Title                          Status    Download
  ------------------------------------  -------------------  -------------------  -----------------------------  --------  --------
  260927bd-aedf-4a62-8dd8-06abdd434900  2025-08-30 10:26:33  2025-08-30 10:30:16  Untitled                       complete  Yes
  ```

- Generate Synthesia videos
  ```
  > generate_synthesia_videos.py --dry_run --in_dir videos -v DEBUG
  ```

- Check the status of Synthesia:
  ```bash
  > get_synthesia_status.py
  ID                                    Created              Updated              Title                          Status       Download
  ------------------------------------  -------------------  -------------------  -----------------------------  -----------  --------
  a3bd32dd-87f7-4653-aac9-d1d07968f358  2025-09-10 12:09:20  2025-09-10 12:09:24  slide1                         in_progress  No
  ```

# To Reorg

./dev_scripts_helpers/video_narration/generate_synthesia_videos.py --in_file
script.txt --out_file output --test

# Generate images from prompt
generate_images.py
dev_scripts_helpers/generate_images.py "A sunset over mountains" --dst_dir ./images --low_res
OpenAI

# Create videos from storyboards
Veo3
dev_scripts_helpers/google_veo3/
dev_scripts_helpers/google_veo3/generate_images.py --test_name test --dst_dir images2 --use_rest_api

# Create video lessons with picture-in-picture
dev_scripts_helpers/video_narration/
dev_scripts_helpers/video_narration/README.md

# Create videos of GP talking (Synthesia)
generate_synthesia_videos.py
./dev_scripts_helpers/video_narration/generate_synthesia_videos.py --in_file script.txt --out_file output
generate_synthesia_videos.py --dry_run --in_dir videos -v DEBUG --slide 002:009

# Create voice of GP talking (ElevenLabs)
generate_elevenlabs_voice.py

# Create map of Google maps
./create_google_drive_map.py --in_dir '/Users/saggese/Library/CloudStorage/GoogleDrive-gp@causify.ai/Shared drives' --action tree
./create_google_drive_map.py --in_dir '/Users/saggese/Library/CloudStorage/GoogleDrive-gp@causify.ai/Shared drives' --action table

# Process slides
dev_scripts_helpers/documentation/process_slides.py --in_file Lesson04-Models.txt --out_file test.txt --limit 0:10 --action slide_reduce

# Create narration from slides
generate_slide_script.py

# Lint slides
lint_txt.py
i docker_bash --base-image=623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp --skip-pull
sudo /bin/bash -c "(source /venv/bin/activate; pip install openai)"
process_slides.py --in_file msml610/lectures_source/Lesson04-Models.txt --out_file test.txt --limit 0:10 --action slide_reduce
lint_txt.py -i test.txt --use_dockerized_prettier
