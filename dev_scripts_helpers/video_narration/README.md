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
