# Step 1)

- Given the text of a storyboard for a presentation, for each slide generate
  images in the following format, where you can add a description in <Complete>

- The prompt should be like:
  ```verbatim
  CHARACTERS
  <Complete>

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

# Step 2)
- You need to generate a file demo_images.md that can be used with the command
  ```python
  > ./helpers_root/dev_scripts_helpers/documentation/generate_images.py \
     -i demo_images.md \
     --dst_dir demo_images.md.figs
  ```
