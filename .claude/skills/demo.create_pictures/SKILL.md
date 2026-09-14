---
description: Generate image prompts per storyboard slide and write them to demo_images.md
model: haiku
---

# Goal
- Given the text of a storyboard for a presentation, generate an image prompt
  for each slide and save the result to `demo_images.md`

# Workflow

## Generate Image Prompts
- For each slide, generate an image prompt in the following format, adding a
  description in `<DESCRIPTION>`
- The prompt should be like:
  ```verbatim
  CHARACTERS
  <DESCRIPTION>

  STYLE ANCHOR:
  Clean, modern vector-illustration style, flat colors, soft gradients, consistent
  lighting, no harsh shadows, slightly rounded shapes, minimal detail, professional
  corporate look, designed for a slide deck, white background, high contrast, 16:9
  aspect ratio, no text, no watermark.

  SETTINGS:
  - No photorealistic elements or textures
  - No slide titles, headers, or explanatory text blocks
  - No decorative elements that don't serve the concept
  - No complex scenes with many small details
  - Minimize the number of distinct elements (5-7 maximum per image)

  CAMERA: Medium shot, straight-on.
  ```

## Create the Output File
- Write the generated prompts to `demo_images.md` so it can be used with the
  command:
  ```bash
  > ./helpers_root/dev_scripts_helpers/documentation/generate_images.py \
     -i demo_images.md \
     --dst_dir demo_images.md.figs
  ```

# Verification
- [ ] Confirm `demo_images.md` has one prompt per storyboard slide
- [ ] Confirm each prompt follows the CHARACTERS / STYLE ANCHOR / SETTINGS /
      CAMERA format
- [ ] Run `generate_images.py` against `demo_images.md` and confirm it succeeds
