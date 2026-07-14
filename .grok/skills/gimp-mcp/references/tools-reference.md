# gimp-mcp tools reference

MCP tools return JSON strings. CLI: `gimp-mcp call <tool> key=value …`.

## Diagnostics

| Tool | Params |
| --- | --- |
| `gimp_mode` | `mode?` (`mock`\|`live`) |
| `gimp_doctor` | — |
| `gimp_list_images` | — |
| `gimp_seed_demo` | — (mock only) |

## I/O

| Tool | Params |
| --- | --- |
| `gimp_new_image` | `width=800`, `height=600`, `color=#ffffff` |
| `gimp_open` | `path` |
| `gimp_info` | `image_id` |
| `gimp_export` | `image_id`, `path`, `format?` |

## Transforms

| Tool | Params |
| --- | --- |
| `gimp_resize` | `image_id`, `width`, `height` |
| `gimp_crop` | `image_id`, `x`, `y`, `width`, `height` |
| `gimp_flip` | `image_id`, `direction=horizontal` |
| `gimp_rotate` | `image_id`, `degrees=90` |
| `gimp_blur` | `image_id`, `radius=2.0` |
| `gimp_desaturate` | `image_id` |
| `gimp_invert` | `image_id` |
| `gimp_text_overlay` | `image_id`, `text`, `x=10`, `y=10`, `size=32`, `color=#000000` |
| `gimp_batch_resize` | `input_dir`, `output_dir`, `width=256`, `height=256` |

## Engines

| Op | Mock | Live GIMP 3 | Live GIMP 2 |
| --- | --- | --- | --- |
| resize | Pillow | python-fu-eval + `--quit` | Script-Fu |
| other filters | Pillow | Pillow assist | Pillow assist |
| export | copy | copy | copy |
