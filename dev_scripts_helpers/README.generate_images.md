# generate_images.py

## `generate_images.py`

### What It Does

- Generates multiple images using OpenAI's DALL-E 3 (default) or DALL-E 2 (with reference image) from text prompts
- Supports reading prompts from command line or formatted text files with multiple prompts
- Creates HD or standard quality images (1024x1024 resolution) and saves them to a specified directory
- Supports reference images for image editing using DALL-E 2 edit endpoint
- Includes dry-run mode to preview operations without making API calls

### Input Format

When using `--input` with a file, the format must be:

```
# prompt_name
text describing the image...
more text...

# another_prompt_name
more text for another image...
```

- Each prompt starts with `# prompt_name` (header line with a single word)
- Following lines contain the prompt text (can be multi-line)
- Prompts are separated by blank lines or by the next header
- All non-empty content must be part of a prompt (content before first header will cause an error)

### Examples

- **Generate 3 HD images from a single prompt:**
  ```bash
  > generate_images.py "A futuristic cityscape at sunset" --dst_dir ./images --count 3
  ```

- **Generate images from multiple prompts in a file:**
  ```bash
  > generate_images.py --input prompts.txt --dst_dir ./output --count 2
  ```

- **Generate standard quality images (lower cost):**
  ```bash
  > generate_images.py --input descr.txt --dst_dir ./images --low_res
  ```

- **Preview what will be generated without API calls:**
  ```bash
  > generate_images.py --input prompts.txt --dst_dir ./images --dry_run
  ```

- **Create output directory from scratch:**
  ```bash
  > generate_images.py --input prompts.txt --dst_dir ./images --from_scratch
  ```

- **Use custom API key:**
  ```bash
  > generate_images.py --input prompts.txt --dst_dir ./images --api_key YOUR_API_KEY
  ```

- **Generate images with a reference image using DALL-E 2 edit:**
  ```bash
  > generate_images.py --input prompts.txt --dst_dir ./images --reference_image reference.png
  ```

- **Generate images with reference image from a single prompt:**
  ```bash
  > generate_images.py "A cat in the same style" --dst_dir ./images --reference_image style_ref.png --count 3
  ```

### Output

- Images are saved as PNG files in the specified destination directory
- Naming patterns:
  - For single prompt: `image_01_hd.png`, `image_02_hd.png`, etc.
  - For multiple prompts from file: `image.prompt_A.01.hd.png`, `image.prompt_B.01.hd.png`, etc.
- Standard quality images use `standard` instead of `hd` in the filename

### API Model Selection

- **DALL-E 3** (default): Used when no reference image is provided. Supports HD and standard quality modes.
- **DALL-E 2**: Automatically selected when `--reference_image` is specified. Uses the image edit endpoint to generate variations based on the reference image and prompt.

