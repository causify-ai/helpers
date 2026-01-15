Given the text of a storyboard for a presentation, for each slide generate images
in the Economist's signature flat graphic illustration style with these
specifications:

## Visual Style
- **Design approach**: Clean, minimalist flat graphics with clear information hierarchy
- **Color palette**: Limited to 3-4 colors maximum - primarily navy blue (#1e3a8a), bright red (#dc2626), and white (#ffffff), with optional accent colors (light blue, gray) for data visualization
- **Background**: Pure white (#ffffff) with no textures or gradients
- **Shapes**: Simple geometric forms only - circles, rectangles, triangles, lines
- **Edges**: Crisp, sharp vector-style edges with no shadows, gradients, or 3D effects
- **Typography**: If text is absolutely necessary, use clean sans-serif fonts, minimal labels only

## Composition Rules
- High contrast between elements for immediate visual clarity
- Generous white space - don't overcrowd the canvas
- Focus on one central concept per image
- Use visual metaphors that are immediately recognizable
- Arrange elements in clear hierarchical relationships (flows, connections, comparisons)

## What to AVOID
- No human figures, faces, or anthropomorphic elements
- No photorealistic elements or textures
- No slide titles, headers, or explanatory text blocks
- No decorative elements that don't serve the concept
- No complex scenes with many small details
- Minimize the number of distinct elements (5-7 maximum per image)

## Output Format
- Professional business infographic quality
- Suitable for presentation slides at standard 16:9 aspect ratio
- Each image should communicate its core concept at a glance

For each slide generate an image that can be used in the presentation
Use a clean flat graphical style like The Economist

You need to generate a file demo_images.md that can be used with the command

helpers_root/dev_scripts_helpers/documentation/render_images.py \
  -i demo_images.md \
  --action render \
  --dst_dir demo_images.md.figs
