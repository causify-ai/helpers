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
Converts individual PNG files to separate MP4 movies using moviepy. Each movie displays a single image for a specified duration.

Example:
```bash
> convert_png_to_movie.py --in_dir ./slides --duration 3.0
```

### `create_presentation_video.py`
Creates a composite presentation video from slide MP4 files with picture-in-picture (PIP) overlays. Supports both default positioning and custom plan-based positioning for pip and comment videos.

Example:
```bash
> create_presentation_video.py --in_dir ./videos --out_file final.mp4
```

### `download_synthesia_video.py`
Downloads completed videos from the Synthesia API using their download URLs and saves them with meaningful names.

Example:
```bash
> download_synthesia_video.py --ids "id1 id2 id3"
```

### `extract_png_from_ppt.py`
Extracts images and converts slides from PowerPoint presentations to PNG files. Can extract both embedded images and convert slides to images.

### `generate_slide_script.py`
Generates presentation scripts from markdown slides using LLM processing. Processes markdown slides (identified by headers starting with '*') and creates scripts by passing groups of N slides to an LLM for analysis.

Example:
```bash
> generate_slide_script.py --in_file slides.md --out_file script.md --slides_per_group 3
```

### `generate_synthesia_videos.py`
Creates videos from text scripts using the Synthesia API with chosen avatars. Supports dry-run mode for testing.

Example:
```bash
> generate_synthesia_videos.py --in_dir videos --limit "1:3" --dry_run
```

### `get_synthesia_status.py`
Retrieves and displays the status of video generation jobs from the Synthesia API in a formatted table.

Example:
```bash
> get_synthesia_status.py
ID                                    Created              Updated              Title                          Status    Download
------------------------------------  -------------------  -------------------  -----------------------------  --------  --------
260927bd-aedf-4a62-8dd8-06abdd434900  2025-08-30 10:26:33  2025-08-30 10:30:16  Untitled                       complete  Yes
```

### `pdf_to_flip_video.py`
Creates a movie from a PDF that simulates turning pages. Supports different transition styles like crossfade and slide animations.

Example:
```bash
> pdf_to_flip_video.py file.pdf --out out.mp4 --fps 30 --page-duration 2.0 --transition 0.5 --style crossfade
```

### `stop_synthesia_videos.py`
Cancels video generation jobs from the Synthesia API using their Cancel Video Generation endpoint.

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

# To reorg

./dev_scripts_helpers/video_narration/generate_synthesia_videos.py --in_file script.txt --out_file output --test
