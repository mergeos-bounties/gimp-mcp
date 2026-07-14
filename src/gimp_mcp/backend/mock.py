"""Offline GIMP-style image ops via Pillow (CI-safe)."""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from gimp_mcp.config import workspace_dir


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
            path = self._ws / f"{image_id}.png"
        im.save(path)
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
            "ops": [
                "new",
                "open",
                "resize",
                "crop",
                "flip",
                "rotate",
                "blur",
                "desaturate",
                "invert",
                "text",
                "export",
                "batch_resize",
            ],
        }

    def seed_demo(self) -> dict[str, Any]:
        self._images.clear()
        im = Image.new("RGB", (640, 360), "#1e293b")
        draw = ImageDraw.Draw(im)
        draw.rectangle((40, 40, 600, 320), outline="#38bdf8", width=4)
        draw.text((80, 160), "gimp-mcp demo", fill="#e2e8f0")
        iid = self._new_id()
        meta = self._save_meta(iid, im)
        return {"ok": True, "mode": "mock", "image": meta, "count": 1}

    def list_images(self) -> list[dict[str, Any]]:
        return [dict(v) for v in self._images.values()]

    def new_image(self, width: int, height: int, color: str = "#ffffff") -> dict[str, Any]:
        w, h = max(1, int(width)), max(1, int(height))
        im = Image.new("RGB", (w, h), color)
        iid = self._new_id()
        return {"ok": True, "image": self._save_meta(iid, im)}

    def open_image(self, path: str) -> dict[str, Any]:
        p = Path(path)
        if not p.is_file():
            return {"ok": False, "error": f"file not found: {path}"}
        im = Image.open(p).convert("RGB")
        iid = self._new_id()
        dest = self._ws / f"{iid}{p.suffix or '.png'}"
        return {"ok": True, "image": self._save_meta(iid, im, dest)}

    def info(self, image_id: str) -> dict[str, Any]:
        try:
            return {"ok": True, "image": dict(self._get(image_id))}
        except KeyError as e:
            return {"ok": False, "error": str(e)}

    def _load(self, image_id: str) -> Image.Image:
        meta = self._get(image_id)
        return Image.open(meta["path"]).convert("RGB")

    def resize(self, image_id: str, width: int, height: int) -> dict[str, Any]:
        try:
            im = self._load(image_id)
            im = im.resize((max(1, int(width)), max(1, int(height))), Image.Resampling.LANCZOS)
            return {"ok": True, "image": self._save_meta(image_id, im)}
        except KeyError as e:
            return {"ok": False, "error": str(e)}

    def crop(self, image_id: str, x: int, y: int, width: int, height: int) -> dict[str, Any]:
        try:
            im = self._load(image_id)
            box = (int(x), int(y), int(x) + max(1, int(width)), int(y) + max(1, int(height)))
            im = im.crop(box)
            return {"ok": True, "image": self._save_meta(image_id, im)}
        except KeyError as e:
            return {"ok": False, "error": str(e)}

    def flip(self, image_id: str, direction: str = "horizontal") -> dict[str, Any]:
        try:
            im = self._load(image_id)
            d = direction.lower()
            if d in ("vertical", "v"):
                im = ImageOps.flip(im)
            else:
                im = ImageOps.mirror(im)
            return {"ok": True, "image": self._save_meta(image_id, im)}
        except KeyError as e:
            return {"ok": False, "error": str(e)}

    def rotate(self, image_id: str, degrees: float = 90) -> dict[str, Any]:
        try:
            im = self._load(image_id)
            im = im.rotate(-float(degrees), expand=True, fillcolor="#000000")
            return {"ok": True, "image": self._save_meta(image_id, im)}
        except KeyError as e:
            return {"ok": False, "error": str(e)}

    def blur(self, image_id: str, radius: float = 2.0) -> dict[str, Any]:
        try:
            im = self._load(image_id)
            im = im.filter(ImageFilter.GaussianBlur(radius=max(0.0, float(radius))))
            return {"ok": True, "image": self._save_meta(image_id, im)}
        except KeyError as e:
            return {"ok": False, "error": str(e)}

    def desaturate(self, image_id: str) -> dict[str, Any]:
        try:
            im = ImageOps.grayscale(self._load(image_id)).convert("RGB")
            return {"ok": True, "image": self._save_meta(image_id, im)}
        except KeyError as e:
            return {"ok": False, "error": str(e)}

    def invert(self, image_id: str) -> dict[str, Any]:
        try:
            im = ImageOps.invert(self._load(image_id))
            return {"ok": True, "image": self._save_meta(image_id, im)}
        except KeyError as e:
            return {"ok": False, "error": str(e)}

    def text_overlay(
        self,
        image_id: str,
        text: str,
        x: int = 10,
        y: int = 10,
        size: int = 32,
        color: str = "#000000",
    ) -> dict[str, Any]:
        try:
            im = self._load(image_id)
            draw = ImageDraw.Draw(im)
            # default font; size is approximate for default bitmap font
            draw.text((int(x), int(y)), str(text), fill=color)
            return {"ok": True, "image": self._save_meta(image_id, im), "text": text, "size": size}
        except KeyError as e:
            return {"ok": False, "error": str(e)}

    def export(self, image_id: str, path: str, format: str | None = None) -> dict[str, Any]:
        try:
            im = self._load(image_id)
            out = Path(path)
            out.parent.mkdir(parents=True, exist_ok=True)
            fmt = (format or out.suffix.lstrip(".") or "png").upper()
            if fmt == "JPG":
                fmt = "JPEG"
            im.save(out, format=fmt)
            return {"ok": True, "path": str(out), "format": fmt, "image_id": image_id}
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
            im = Image.open(p).convert("RGB")
            im = im.resize((max(1, int(width)), max(1, int(height))), Image.Resampling.LANCZOS)
            dest = outp / p.name
            im.save(dest)
            done.append(str(dest))
        return {"ok": True, "count": len(done), "files": done, "width": width, "height": height}
