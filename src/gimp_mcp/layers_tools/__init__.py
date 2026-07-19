"""Layer management tools for gimp-mcp."""

from __future__ import annotations

from typing import Any

from PIL import Image


def list_layers_from_image(im: Image.Image) -> list[dict[str, Any]]:
    """Return mock layer list for an image (mock mode only)."""
    if im.mode == "RGBA":
        return [
            {"name": "Background", "visible": True, "opacity": 1.0},
            {"name": "Foreground", "visible": True, "opacity": 1.0},
        ]
    return [{"name": "Background", "visible": True, "opacity": 1.0}]


def create_new_layer(im: Image.Image, name: str = "New Layer") -> Image.Image:
    """Create a new transparent layer (mock mode only)."""
    new = Image.new("RGBA", im.size, (0, 0, 0, 0))
    return new


def flatten_image(im: Image.Image) -> Image.Image:
    """Flatten all layers (mock mode only)."""
    return im.convert("RGB")