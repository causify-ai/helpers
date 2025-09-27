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

