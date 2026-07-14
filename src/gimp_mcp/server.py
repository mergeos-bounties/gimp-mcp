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
        "GIMP MCP server. Prefer mock mode offline (Pillow). "
        "Live mode uses gimp-console batch when installed. "
        "Typical flow: gimp_doctor → gimp_seed_demo / gimp_open → "
        "gimp_resize / gimp_blur / gimp_text_overlay → gimp_export."
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
def gimp_new_image(width: int = 800, height: int = 600, color: str = "#ffffff") -> str:
    """Create a new blank image."""
    return _j(get_backend().new_image(width, height, color))


@mcp.tool()
def gimp_open(path: str) -> str:
    """Open an image file into the session."""
    return _j(get_backend().open_image(path))


@mcp.tool()
def gimp_info(image_id: str) -> str:
    """Image metadata (size, path)."""
    return _j(get_backend().info(image_id))


@mcp.tool()
def gimp_resize(image_id: str, width: int, height: int) -> str:
    """Resize image (live prefers gimp-console Script-Fu scale)."""
    return _j(get_backend().resize(image_id, width, height))


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
def gimp_desaturate(image_id: str) -> str:
    """Convert to grayscale."""
    return _j(get_backend().desaturate(image_id))


@mcp.tool()
def gimp_invert(image_id: str) -> str:
    """Invert colors."""
    return _j(get_backend().invert(image_id))


@mcp.tool()
def gimp_text_overlay(
    image_id: str,
    text: str,
    x: int = 10,
    y: int = 10,
    size: int = 32,
    color: str = "#000000",
) -> str:
    """Draw text on the image."""
    return _j(get_backend().text_overlay(image_id, text, x, y, size, color))


@mcp.tool()
def gimp_export(image_id: str, path: str, format: str | None = None) -> str:
    """Export image to disk path."""
    return _j(get_backend().export(image_id, path, format))


@mcp.tool()
def gimp_batch_resize(input_dir: str, output_dir: str, width: int = 256, height: int = 256) -> str:
    """Resize all images in a folder."""
    return _j(get_backend().batch_resize(input_dir, output_dir, width, height))


def run_stdio() -> None:
    mcp.run(transport="stdio")
