"""FastMCP server: GIMP tools for AI agents."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from gimp_mcp.backend import get_backend, switch_mode
from gimp_mcp.config import get_mode

mcp = FastMCP(
    "gimp-mcp",
    instructions=(
        "GIMP MCP server for real image work. "
        "Flow: gimp_doctor → gimp_open(path) → transforms → gimp_export. "
        "Use gimp_pipeline for multi-step recipes. "
        "Live mode uses gimp-console for scale; other filters may use Pillow assist. "
        "Prefer absolute paths for open/export."
    ),
)


def _j(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
def gimp_mode(mode: str | None = None) -> str:
    """Get or set backend mode (mock|live)."""
    if mode:
        return _j(switch_mode(mode))
    b = get_backend()
    return _j({"mode": get_mode(), "backend": b.name, "doctor": b.doctor()})


@mcp.tool()
def gimp_doctor() -> str:
    """Check mock/live GIMP connectivity and workspace."""
    return _j(get_backend().doctor())


@mcp.tool()
def gimp_seed_demo() -> str:
    """Create a demo canvas in mock mode."""
    return _j(get_backend().seed_demo())


@mcp.tool()
def gimp_list_images() -> str:
    """List open image handles in the session."""
    return _j(get_backend().list_images())


@mcp.tool()
def gimp_close(image_id: str) -> str:
    """Close an image handle from the session."""
    return _j(get_backend().close_image(image_id))


@mcp.tool()
def gimp_new_image(width: int = 800, height: int = 600, color: str = "#ffffff") -> str:
    """Create a new blank image."""
    return _j(get_backend().new_image(width, height, color))


@mcp.tool()
def gimp_open(path: str) -> str:
    """Open an image file into the session (absolute path preferred)."""
    return _j(get_backend().open_image(path))


@mcp.tool()
def gimp_info(image_id: str) -> str:
    """Image metadata (size, path)."""
    return _j(get_backend().info(image_id))


@mcp.tool()
def gimp_resize(image_id: str, width: int, height: int) -> str:
    """Resize image (live prefers gimp-console scale)."""
    return _j(get_backend().resize(image_id, width, height))


@mcp.tool()
def gimp_thumbnail(image_id: str, max_width: int = 512, max_height: int = 512) -> str:
    """Fit image inside box preserving aspect ratio."""
    return _j(get_backend().thumbnail(image_id, max_width, max_height))


@mcp.tool()
def gimp_crop(image_id: str, x: int, y: int, width: int, height: int) -> str:
    """Crop image to rectangle."""
    return _j(get_backend().crop(image_id, x, y, width, height))


@mcp.tool()
def gimp_flip(image_id: str, direction: str = "horizontal") -> str:
    """Flip horizontal or vertical."""
    return _j(get_backend().flip(image_id, direction))


@mcp.tool()
def gimp_rotate(image_id: str, degrees: float = 90) -> str:
    """Rotate image by degrees (clockwise)."""
    return _j(get_backend().rotate(image_id, degrees))


@mcp.tool()
def gimp_blur(image_id: str, radius: float = 2.0) -> str:
    """Gaussian blur."""
    return _j(get_backend().blur(image_id, radius))


@mcp.tool()
def gimp_sharpen(image_id: str, percent: float = 150.0, radius: float = 2.0) -> str:
    """Unsharp-mask sharpen."""
    return _j(get_backend().sharpen(image_id, percent, radius))


@mcp.tool()
def gimp_emboss(image_id: str) -> str:
    """Apply emboss filter for a raised 3D effect."""
    return _j(get_backend().emboss(image_id))


@mcp.tool()
def gimp_contour(image_id: str) -> str:
    """Apply contour filter to highlight edges."""
    return _j(get_backend().contour(image_id))


@mcp.tool()
def gimp_edge_enhance(image_id: str) -> str:
    """Enhance edges in the image."""
    return _j(get_backend().edge_enhance(image_id))


@mcp.tool()
def gimp_find_edges(image_id: str) -> str:
    """Detect and highlight edges (edge-detect filter)."""
    return _j(get_backend().find_edges(image_id))


@mcp.tool()
def gimp_detail(image_id: str) -> str:
    """Enhance image detail / texture."""
    return _j(get_backend().detail(image_id))


@mcp.tool()
def gimp_smooth(image_id: str) -> str:
    """Smooth the image slightly (reduce noise/grain)."""
    return _j(get_backend().smooth(image_id))


@mcp.tool()
def gimp_desaturate(image_id: str) -> str:
    """Convert to grayscale."""
    return _j(get_backend().desaturate(image_id))


@mcp.tool()
def gimp_invert(image_id: str) -> str:
    """Invert colors."""
    return _j(get_backend().invert(image_id))


@mcp.tool()
def gimp_brightness(image_id: str, factor: float = 1.2) -> str:
    """Adjust brightness (1.0 = unchanged, >1 brighter)."""
    return _j(get_backend().brightness(image_id, factor))


@mcp.tool()
def gimp_contrast(image_id: str, factor: float = 1.2) -> str:
    """Adjust contrast (1.0 = unchanged)."""
    return _j(get_backend().contrast(image_id, factor))


@mcp.tool()
def gimp_saturation(image_id: str, factor: float = 1.2) -> str:
    """Adjust color saturation (1.0 = unchanged)."""
    return _j(get_backend().saturation(image_id, factor))


@mcp.tool()
def gimp_auto_orient(image_id: str) -> str:
    """Apply EXIF orientation."""
    return _j(get_backend().auto_orient(image_id))


@mcp.tool()
def gimp_crop_bottom(image_id: str, keep_height: int) -> str:
    """Keep only the top keep_height pixels (drop bottom strip / tagline)."""
    return _j(get_backend().crop_bottom(image_id, keep_height))


@mcp.tool()
def gimp_crop_percent(
    image_id: str,
    left: float = 0.0,
    top: float = 0.0,
    right: float = 1.0,
    bottom: float = 1.0,
) -> str:
    """Crop by fractional bounds 0..1."""
    return _j(get_backend().crop_percent(image_id, left, top, right, bottom))


@mcp.tool()
def gimp_erase_rect(
    image_id: str,
    x: int,
    y: int,
    width: int,
    height: int,
    fill: str = "#000000",
    transparent: bool = False,
) -> str:
    """Fill/erase a rectangle (optionally transparent)."""
    return _j(get_backend().erase_rect(image_id, x, y, width, height, fill, transparent))


@mcp.tool()
def gimp_fill_rect(
    image_id: str, x: int, y: int, width: int, height: int, color: str = "#000000"
) -> str:
    """Fill a rectangle with solid color."""
    return _j(get_backend().fill_rect(image_id, x, y, width, height, color))


@mcp.tool()
def gimp_remove_background(
    image_id: str, mode: str = "black", threshold: int = 28, soft: int = 40
) -> str:
    """Remove background. mode=black|white|layer (layer=hard matte+defringe)."""
    return _j(get_backend().remove_background(image_id, mode, threshold, soft))


@mcp.tool()
def gimp_cutout(
    image_id: str, thr: float = 40.0, hard: bool = True, defringe: bool = True
) -> str:
    """
    Layered cutout for logos on black: color layer + matte layer + defringe.
    Kills soft glow / white haze without muddy despeckle.
    """
    return _j(get_backend().cutout(image_id, thr, hard, defringe))

@mcp.tool()
def gimp_trim(
    image_id: str, padding: int = 8, alpha_threshold: int = 10, bg_mode: str = "auto"
) -> str:
    """Autocrop empty margins."""
    return _j(get_backend().trim(image_id, padding, alpha_threshold, bg_mode))


@mcp.tool()
def gimp_pad(
    image_id: str, padding: int = 32, color: str = "#000000", transparent: bool = False
) -> str:
    """Add padding around the image."""
    return _j(get_backend().pad(image_id, padding, color, transparent))


@mcp.tool()
def gimp_border(image_id: str, width: int = 4, color: str = "#ffffff") -> str:
    """Add a border."""
    return _j(get_backend().border(image_id, width, color))


@mcp.tool()
def gimp_opacity(image_id: str, factor: float = 1.0) -> str:
    """Multiply alpha channel by factor."""
    return _j(get_backend().opacity(image_id, factor))


@mcp.tool()
def gimp_text_overlay(
    image_id: str,
    text: str,
    x: int = 10,
    y: int = 10,
    size: int = 32,
    color: str = "#000000",
) -> str:
    """Draw text on the image (TrueType when available)."""
    return _j(get_backend().text_overlay(image_id, text, x, y, size, color))


@mcp.tool()
def gimp_pipeline(image_id: str, steps_json: str) -> str:
    """
    Apply a multi-step recipe. steps_json is a JSON array of objects with 'op' plus params.
    Ops include: auto_orient, resize, thumbnail, crop, crop_bottom, crop_percent, flip,
    rotate, blur, sharpen, emboss, contour, edge_enhance, find_edges, detail, smooth,
    desaturate, invert, brightness, contrast, saturation, text,
    erase_rect, fill_rect, remove_background, trim, pad, border, opacity.
    """
    steps = json.loads(steps_json)
    if not isinstance(steps, list):
        return _j({"ok": False, "error": "steps_json must be a JSON array"})
    return _j(get_backend().pipeline(image_id, steps))


@mcp.tool()
def gimp_export(image_id: str, path: str, format: str | None = None) -> str:
    """Export image to disk path."""
    return _j(get_backend().export(image_id, path, format))


@mcp.tool()
def gimp_batch_resize(input_dir: str, output_dir: str, width: int = 256, height: int = 256) -> str:
    """Resize all images in a folder."""
    return _j(get_backend().batch_resize(input_dir, output_dir, width, height))


@mcp.tool()
def gimp_list_layers(image_id: str) -> str:
    """List layers in the image (mock mode only)."""
    return _j(get_backend().list_layers(image_id))


@mcp.tool()
def gimp_new_layer(image_id: str, name: str = "New Layer") -> str:
    """Create a new transparent layer."""
    return _j(get_backend().new_layer(image_id, name))


@mcp.tool()
def gimp_flatten(image_id: str) -> str:
    """Flatten all layers into a single background layer."""
    return _j(get_backend().flatten(image_id))



@mcp.tool()
def gimp_histogram(image_id: str) -> str:
    """Get image histogram data (RGB channel distribution)."""
    return _j(get_backend().histogram(image_id))


@mcp.tool()
def gimp_exif(image_id: str) -> str:
    """Read EXIF metadata from image (camera, GPS, orientation)."""
    return _j(get_backend().exif(image_id))


def run_stdio() -> None:
    mcp.run(transport="stdio")
