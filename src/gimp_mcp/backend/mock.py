"""Offline GIMP-style image ops via Pillow (CI-safe)."""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

from PIL import Image

from gimp_mcp import ops
from gimp_mcp.config import workspace_dir

OPS_LIST = [
    "new",
    "open",
    "resize",
    "thumbnail",
    "crop",
    "crop_bottom",
    "crop_percent",
    "flip",
    "rotate",
    "blur",
    "sharpen",
    "desaturate",
    "invert",
    "brightness",
    "contrast",
    "saturation",
    "auto_orient",
    "text",
    "erase_rect",
    "fill_rect",
    "remove_background",
    "cutout",
    "trim",
    "pad",
    "border",
    "opacity",
    "export",
    "batch_resize",
    "pipeline",
    "close",
    "list_layers",
    "new_layer",
    "flatten",
]


class MockBackend:
    name = "mock"

    def __init__(self) -> None:
        self._images: dict[str, dict[str, Any]] = {}
        self._ws = workspace_dir() / "mock"
        self._ws.mkdir(parents=True, exist_ok=True)

    def _new_id(self) -> str:
        return f"img_{uuid.uuid4().hex[:10]}"

    def _get(self, image_id: str) -> dict[str, Any]:
        if image_id not in self._images:
            raise KeyError(f"unknown image_id={image_id}")
        return self._images[image_id]

    def _save_meta(self, image_id: str, im: Image.Image, path: Path | None = None) -> dict[str, Any]:
        meta = self._images.get(image_id) or {"id": image_id}
        if path is None:
            ext = ".png" if im.mode == "RGBA" else ".png"
            path = self._ws / f"{image_id}{ext}"
        if im.mode == "RGBA":
            im.save(path)
        else:
            im.convert("RGB").save(path)
        meta.update(
            {
                "id": image_id,
                "path": str(path),
                "width": im.width,
                "height": im.height,
                "mode": im.mode,
                "updated_at": time.time(),
            }
        )
        self._images[image_id] = meta
        return dict(meta)

    def doctor(self) -> dict[str, Any]:
        return {
            "ok": True,
            "mode": "mock",
            "backend": "pillow",
            "connected": True,
            "images_open": len(self._images),
            "workspace": str(self._ws),
            "message": "Mock backend active — no GIMP install needed",
            "ops": list(OPS_LIST),
        }

    def seed_demo(self) -> dict[str, Any]:
        self._images.clear()
        im = Image.new("RGB", (640, 360), "#1e293b")
        from PIL import ImageDraw

        draw = ImageDraw.Draw(im)
        draw.rectangle((40, 40, 600, 320), outline="#38bdf8", width=4)
        im = ops.text_overlay(im, "gimp-mcp demo", 80, 160, 28, "#e2e8f0")
        iid = self._new_id()
        meta = self._save_meta(iid, im)
        return {"ok": True, "mode": "mock", "image": meta, "count": 1}

    def list_images(self) -> list[dict[str, Any]]:
        return [dict(v) for v in self._images.values()]

    def close_image(self, image_id: str) -> dict[str, Any]:
        if image_id not in self._images:
            return {"ok": False, "error": f"unknown image_id={image_id}"}
        del self._images[image_id]
        return {"ok": True, "closed": image_id, "remaining": len(self._images)}

    def new_image(self, width: int, height: int, color: str = "#ffffff") -> dict[str, Any]:
        w, h = max(1, int(width)), max(1, int(height))
        im = Image.new("RGB", (w, h), color)
        iid = self._new_id()
        return {"ok": True, "image": self._save_meta(iid, im)}

    def open_image(self, path: str) -> dict[str, Any]:
        p = Path(path)
        if not p.is_file():
            return {"ok": False, "error": f"file not found: {path}"}
        try:
            im = ops.load_image(p, keep_alpha=True)
        except Exception as e:
            return {"ok": False, "error": str(e)}
        iid = self._new_id()
        dest = self._ws / f"{iid}.png"
        return {"ok": True, "image": self._save_meta(iid, im, dest), "original": str(p)}

    def info(self, image_id: str) -> dict[str, Any]:
        try:
            return {"ok": True, "image": dict(self._get(image_id))}
        except KeyError as e:
            return {"ok": False, "error": str(e)}

    def _load(self, image_id: str) -> Image.Image:
        meta = self._get(image_id)
        return ops.load_image(meta["path"], keep_alpha=True)

    def _apply(self, image_id: str, fn, **kwargs: Any) -> dict[str, Any]:
        try:
            im = self._load(image_id)
            im = fn(im, **kwargs) if kwargs else fn(im)
            return {"ok": True, "image": self._save_meta(image_id, im)}
        except KeyError as e:
            return {"ok": False, "error": str(e)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def resize(self, image_id: str, width: int, height: int) -> dict[str, Any]:
        return self._apply(image_id, ops.resize, width=width, height=height)

    def thumbnail(self, image_id: str, max_width: int = 512, max_height: int = 512) -> dict[str, Any]:
        return self._apply(image_id, ops.thumbnail, max_width=max_width, max_height=max_height)

    def crop(self, image_id: str, x: int, y: int, width: int, height: int) -> dict[str, Any]:
        return self._apply(image_id, ops.crop, x=x, y=y, width=width, height=height)

    def crop_bottom(self, image_id: str, keep_height: int) -> dict[str, Any]:
        return self._apply(image_id, ops.crop_bottom, keep_height=keep_height)

    def crop_percent(
        self,
        image_id: str,
        left: float = 0.0,
        top: float = 0.0,
        right: float = 1.0,
        bottom: float = 1.0,
    ) -> dict[str, Any]:
        return self._apply(
            image_id, ops.crop_percent, left=left, top=top, right=right, bottom=bottom
        )

    def flip(self, image_id: str, direction: str = "horizontal") -> dict[str, Any]:
        return self._apply(image_id, ops.flip, direction=direction)

    def rotate(self, image_id: str, degrees: float = 90) -> dict[str, Any]:
        return self._apply(image_id, ops.rotate, degrees=degrees)

    def blur(self, image_id: str, radius: float = 2.0) -> dict[str, Any]:
        return self._apply(image_id, ops.blur, radius=radius)

    def sharpen(self, image_id: str, percent: float = 150.0, radius: float = 2.0) -> dict[str, Any]:
        return self._apply(image_id, ops.sharpen, percent=percent, radius=radius)

    def desaturate(self, image_id: str) -> dict[str, Any]:
        return self._apply(image_id, ops.desaturate)

    def invert(self, image_id: str) -> dict[str, Any]:
        return self._apply(image_id, ops.invert)

    def brightness(self, image_id: str, factor: float = 1.2) -> dict[str, Any]:
        return self._apply(image_id, ops.brightness, factor=factor)

    def contrast(self, image_id: str, factor: float = 1.2) -> dict[str, Any]:
        return self._apply(image_id, ops.contrast, factor=factor)

    def saturation(self, image_id: str, factor: float = 1.2) -> dict[str, Any]:
        return self._apply(image_id, ops.saturation, factor=factor)

    def auto_orient(self, image_id: str) -> dict[str, Any]:
        return self._apply(image_id, ops.auto_orient)

    def text_overlay(
        self,
        image_id: str,
        text: str,
        x: int = 10,
        y: int = 10,
        size: int = 32,
        color: str = "#000000",
    ) -> dict[str, Any]:
        r = self._apply(
            image_id, ops.text_overlay, text=text, x=x, y=y, size=size, color=color
        )
        if r.get("ok"):
            r["text"] = text
            r["size"] = size
        return r

    def erase_rect(
        self,
        image_id: str,
        x: int,
        y: int,
        width: int,
        height: int,
        fill: str = "#000000",
        transparent: bool = False,
    ) -> dict[str, Any]:
        return self._apply(
            image_id,
            ops.erase_rect,
            x=x,
            y=y,
            width=width,
            height=height,
            fill=fill,
            transparent=transparent,
        )

    def fill_rect(
        self, image_id: str, x: int, y: int, width: int, height: int, color: str = "#000000"
    ) -> dict[str, Any]:
        return self._apply(
            image_id, ops.fill_rect, x=x, y=y, width=width, height=height, color=color
        )

    def remove_background(
        self, image_id: str, mode: str = "black", threshold: int = 28, soft: int = 40
    ) -> dict[str, Any]:
        return self._apply(
            image_id, ops.remove_background, mode=mode, threshold=threshold, soft=soft
        )

    def cutout(
        self,
        image_id: str,
        thr: float = 40.0,
        hard: bool = True,
        defringe: bool = True,
    ) -> dict[str, Any]:
        return self._apply(image_id, ops.cutout, thr=thr, hard=hard, defringe=defringe)

    def trim(
        self,
        image_id: str,
        padding: int = 8,
        alpha_threshold: int = 10,
        bg_mode: str = "auto",
    ) -> dict[str, Any]:
        return self._apply(
            image_id,
            ops.trim,
            padding=padding,
            alpha_threshold=alpha_threshold,
            bg_mode=bg_mode,
        )

    def pad(
        self,
        image_id: str,
        padding: int = 32,
        color: str = "#000000",
        transparent: bool = False,
    ) -> dict[str, Any]:
        return self._apply(
            image_id, ops.pad, padding=padding, color=color, transparent=transparent
        )

    def border(self, image_id: str, width: int = 4, color: str = "#ffffff") -> dict[str, Any]:
        return self._apply(image_id, ops.border, width=width, color=color)

    def opacity(self, image_id: str, factor: float = 1.0) -> dict[str, Any]:
        return self._apply(image_id, ops.opacity, factor=factor)

    def pipeline(self, image_id: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
        try:
            im = self._load(image_id)
            im, applied = ops.apply_pipeline(im, steps)
            meta = self._save_meta(image_id, im)
            return {"ok": True, "image": meta, "applied": applied}
        except KeyError as e:
            return {"ok": False, "error": str(e)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def export(self, image_id: str, path: str, format: str | None = None) -> dict[str, Any]:
        try:
            im = self._load(image_id)
            info = ops.export(im, path, format)
            return {"ok": True, "image_id": image_id, **info}
        except KeyError as e:
            return {"ok": False, "error": str(e)}
        except OSError as e:
            return {"ok": False, "error": str(e)}

    def batch_resize(
        self, input_dir: str, output_dir: str, width: int, height: int
    ) -> dict[str, Any]:
        inp, outp = Path(input_dir), Path(output_dir)
        if not inp.is_dir():
            return {"ok": False, "error": f"input_dir not found: {input_dir}"}
        outp.mkdir(parents=True, exist_ok=True)
        done: list[str] = []
        for p in sorted(inp.iterdir()):
            if p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}:
                continue
            im = ops.load_image(p, keep_alpha=False)
            im = ops.resize(im, width, height)
            dest = outp / (p.stem + ".png")
            im.save(dest)
            done.append(str(dest))
        return {"ok": True, "count": len(done), "files": done, "width": width, "height": height}

    def list_layers(self, image_id: str) -> dict[str, Any]:
        """List layers in the image (mock mode only)."""
        try:
            _ = self._get(image_id)
            return {
                "ok": True,
                "layers": [
                    {"name": "Background", "visible": True, "opacity": 1.0},
                    {"name": "Layer 1", "visible": True, "opacity": 1.0},
                ],
            }
        except KeyError as e:
            return {"ok": False, "error": str(e)}

    def new_layer(self, image_id: str, name: str = "New Layer") -> dict[str, Any]:
        """Create a new transparent layer."""
        try:
            im = self._load(image_id)
            # In mock mode, we just return success
            # In real GIMP, this would create a new layer in the image
            return {
                "ok": True,
                "message": f"Created new layer '{name}' in image {image_id}",
                "layer_name": name,
            }
        except KeyError as e:
            return {"ok": False, "error": str(e)}

    def flatten(self, image_id: str) -> dict[str, Any]:
        """Flatten all layers into a single background layer."""
        try:
            im = self._load(image_id)
            # In mock mode, flatten just converts to RGB
            flattened = im.convert("RGB")
            return {"ok": True, "image": self._save_meta(image_id, flattened)}
        except KeyError as e:
            return {"ok": False, "error": str(e)}
