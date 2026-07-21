# GIMP MCP Gallery

This gallery showcases edits performed automatically using the `gimp-mcp` tools driven by large language models.

## 1. Auto-Cropping and Resizing
- **Goal:** Resize a 4K image to 1080p and crop out the center.
- **Process:** The AI called `gimp_scale` and `gimp_crop` in sequence.

## 2. Layer Adjustments
- **Goal:** Add a watermark layer on top of a base image.
- **Process:** The AI called `gimp_new_layer`, `gimp_text_insert`, and `gimp_flatten`.

## 3. Brightness/Contrast
- **Goal:** Fix an underexposed photo.
- **Process:** The AI called `gimp_brightness_contrast` with parameters derived from image histogram analysis.

*(More examples will be added as the MCP toolset expands.)*