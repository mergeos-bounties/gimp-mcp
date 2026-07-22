"""Shared Pillow image operations used by mock + live assist."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps, ImagePalette


def load_image(path: str | Path, keep_alpha: bool = True) -> Image.Image:
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    if keep_alpha and im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        return im.convert("RGBA")
    return im.convert("RGB")


def load_rgb(path: str | Path) -> Image.Image:
    return load_image(path, keep_alpha=False).convert("RGB")


def ensure_rgba(im: Image.Image) -> Image.Image:
    if im.mode == "RGBA":
        return im
    return im.convert("RGBA")


def ensure_rgb(im: Image.Image) -> Image.Image:
    if im.mode == "RGB":
        return im
    if im.mode == "RGBA":
        bg = Image.new("RGB", im.size, (0, 0, 0))
        bg.paste(im, mask=im.split()[-1])
        return bg
    return im.convert("RGB")


def auto_orient(im: Image.Image) -> Image.Image:
    return ImageOps.exif_transpose(im)


def resize(im: Image.Image, width: int, height: int) -> Image.Image:
    return im.resize((max(1, int(width)), max(1, int(height))), Image.Resampling.LANCZOS)


def thumbnail(im: Image.Image, max_width: int, max_height: int) -> Image.Image:
    """Fit inside box preserving aspect ratio (no upscale beyond original)."""
    out = im.copy()
    out.thumbnail((max(1, int(max_width)), max(1, int(max_height))), Image.Resampling.LANCZOS)
    return out


def crop(im: Image.Image, x: int, y: int, width: int, height: int) -> Image.Image:
    box = (int(x), int(y), int(x) + max(1, int(width)), int(y) + max(1, int(height)))
    return im.crop(box)


def crop_bottom(im: Image.Image, keep_height: int) -> Image.Image:
    """Keep only the top `keep_height` pixels (drop bottom strip)."""
    h = max(1, min(int(keep_height), im.height))
    return im.crop((0, 0, im.width, h))


def crop_percent(
    im: Image.Image,
    left: float = 0.0,
    top: float = 0.0,
    right: float = 1.0,
    bottom: float = 1.0,
) -> Image.Image:
    """Crop by fractional bounds 0..1."""
    w, h = im.size
    x0 = int(max(0.0, min(1.0, float(left))) * w)
    y0 = int(max(0.0, min(1.0, float(top))) * h)
    x1 = int(max(0.0, min(1.0, float(right))) * w)
    y1 = int(max(0.0, min(1.0, float(bottom))) * h)
    if x1 <= x0:
        x1 = min(w, x0 + 1)
    if y1 <= y0:
        y1 = min(h, y0 + 1)
    return im.crop((x0, y0, x1, y1))


def flip(im: Image.Image, direction: str = "horizontal") -> Image.Image:
    d = (direction or "horizontal").lower()
    if d in ("vertical", "v"):
        return ImageOps.flip(im)
    return ImageOps.mirror(im)


def rotate(im: Image.Image, degrees: float = 90) -> Image.Image:
    fill = (0, 0, 0, 0) if im.mode == "RGBA" else "#000000"
    return im.rotate(-float(degrees), expand=True, fillcolor=fill)


def _apply_pil_filter(im: Image.Image, filter_type: ImageFilter.Filter | ImageFilter.Kernel) -> Image.Image:
    """Apply a PIL ImageFilter, preserving RGBA alpha."""
    if im.mode == "RGBA":
        a = im.split()[-1]
        rgb = im.convert("RGB")
        out = rgb.filter(filter_type)
        out.putalpha(a)
        return out
    return im.convert("RGB").filter(filter_type)


def blur(im: Image.Image, radius: float = 2.0) -> Image.Image:
    return im.filter(ImageFilter.GaussianBlur(radius=max(0.0, float(radius))))


def sharpen(im: Image.Image, percent: float = 150.0, radius: float = 2.0) -> Image.Image:
    return im.filter(
        ImageFilter.UnsharpMask(
            radius=max(0.1, float(radius)), percent=int(max(1, percent)), threshold=3
        )
    )


def emboss(im: Image.Image) -> Image.Image:
    """Apply emboss filter for a raised 3D effect."""
    return _apply_pil_filter(im, ImageFilter.EMBOSS)


def contour(im: Image.Image) -> Image.Image:
    """Apply contour filter to highlight edges."""
    return _apply_pil_filter(im, ImageFilter.CONTOUR)


def edge_enhance(im: Image.Image) -> Image.Image:
    """Enhance edges in the image."""
    return _apply_pil_filter(im, ImageFilter.EDGE_ENHANCE)


def find_edges(im: Image.Image) -> Image.Image:
    """Detect and highlight edges (edge-detect filter)."""
    return _apply_pil_filter(im, ImageFilter.FIND_EDGES)


def detail(im: Image.Image) -> Image.Image:
    """Enhance image detail/ texture."""
    return _apply_pil_filter(im, ImageFilter.DETAIL)


def smooth(im: Image.Image) -> Image.Image:
    """Smooth the image slightly (reduce noise/grain)."""
    return _apply_pil_filter(im, ImageFilter.SMOOTH)


def desaturate(im: Image.Image) -> Image.Image:
    if im.mode == "RGBA":
        a = im.split()[-1]
        g = ImageOps.grayscale(im.convert("RGB")).convert("RGB")
        g.putalpha(a)
        return g
    return ImageOps.grayscale(im).convert("RGB")


def invert(im: Image.Image) -> Image.Image:
    if im.mode == "RGBA":
        a = im.split()[-1]
        inv = ImageOps.invert(im.convert("RGB"))
        inv.putalpha(a)
        return inv
    return ImageOps.invert(im.convert("RGB"))


def brightness(im: Image.Image, factor: float = 1.2) -> Image.Image:
    if im.mode == "RGBA":
        a = im.split()[-1]
        out = ImageEnhance.Brightness(im.convert("RGB")).enhance(float(factor))
        out.putalpha(a)
        return out
    return ImageEnhance.Brightness(im.convert("RGB")).enhance(float(factor))


def contrast(im: Image.Image, factor: float = 1.2) -> Image.Image:
    if im.mode == "RGBA":
        a = im.split()[-1]
        out = ImageEnhance.Contrast(im.convert("RGB")).enhance(float(factor))
        out.putalpha(a)
        return out
    return ImageEnhance.Contrast(im.convert("RGB")).enhance(float(factor))


def saturation(im: Image.Image, factor: float = 1.2) -> Image.Image:
    if im.mode == "RGBA":
        a = im.split()[-1]
        out = ImageEnhance.Color(im.convert("RGB")).enhance(float(factor))
        out.putalpha(a)
        return out
    return ImageEnhance.Color(im.convert("RGB")).enhance(float(factor))


def _font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    size = max(8, int(size))
    candidates = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in candidates:
        if Path(path).is_file():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def text_overlay(
    im: Image.Image,
    text: str,
    x: int = 10,
    y: int = 10,
    size: int = 32,
    color: str = "#000000",
) -> Image.Image:
    out = im.copy()
    if out.mode not in ("RGB", "RGBA"):
        out = out.convert("RGBA")
    draw = ImageDraw.Draw(out)
    font = _font(size)
    draw.text((int(x), int(y)), str(text), fill=color, font=font)
    return out


def erase_rect(
    im: Image.Image,
    x: int,
    y: int,
    width: int,
    height: int,
    fill: str = "#000000",
    transparent: bool = False,
) -> Image.Image:
    """Fill a rectangle (erase region). If transparent=True, use alpha 0."""
    out = ensure_rgba(im) if transparent else im.copy()
    draw = ImageDraw.Draw(out)
    box = (int(x), int(y), int(x) + max(1, int(width)), int(y) + max(1, int(height)))
    if transparent:
        draw.rectangle(box, fill=(0, 0, 0, 0))
    else:
        draw.rectangle(box, fill=fill)
    return out


def fill_rect(
    im: Image.Image, x: int, y: int, width: int, height: int, color: str = "#000000"
) -> Image.Image:
    return erase_rect(im, x, y, width, height, fill=color, transparent=False)


def remove_background(
    im: Image.Image,
    mode: str = "black",
    threshold: int = 28,
    soft: int = 40,
) -> Image.Image:
    """
    Make near-black (or near-white) pixels transparent.
    mode: black | white | layer (layered hard matte + defringe)
    """
    rgba = ensure_rgba(im)
    m = str(mode).lower()
    if m in ("layer", "layers", "matte", "hard"):
        from gimp_mcp.layers import cutout_layers

        return cutout_layers(
            rgba,
            mode="gold" if m != "luma" else "luma",
            thr=float(threshold),
            soft=max(1.0, float(soft) * 0.25),
            hard=True,
            hard_thr=90.0,
            defringe_on=True,
            aa=0.55,
            unpremult=True,
        )["rgba"]

    arr = np.array(rgba).astype(np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    if m in ("white", "w"):
        presence = 255.0 - np.maximum(np.maximum(r, g), b)
    else:
        presence = np.maximum(np.maximum(r, g), b)
    thr = float(threshold)
    soft_v = max(1.0, float(soft))
    alpha = np.clip((presence - thr) / soft_v, 0.0, 1.0) * 255.0
    arr[:, :, 3] = np.minimum(arr[:, :, 3], alpha)
    low = arr[:, :, 3] < 2
    arr[low, 0:3] = 0
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def cutout(
    im: Image.Image,
    thr: float = 40.0,
    hard: bool = True,
    defringe: bool = True,
) -> Image.Image:
    """Layered cutout: color + matte + defringe (best for logos on black)."""
    from gimp_mcp.layers import cutout_layers

    return cutout_layers(
        ensure_rgba(im),
        mode="gold",
        thr=float(thr),
        soft=6.0,
        hard=bool(hard),
        hard_thr=90.0,
        defringe_on=bool(defringe),
        aa=0.55 if hard else 0.0,
        unpremult=True,
    )["rgba"]

def trim(
    im: Image.Image,
    padding: int = 8,
    alpha_threshold: int = 10,
    bg_mode: str = "auto",
) -> Image.Image:
    """
    Autocrop empty margins.
    For RGBA uses alpha; for RGB uses near-black/near-white detection.
    """
    pad = max(0, int(padding))
    if im.mode == "RGBA":
        arr = np.array(im)
        alpha = arr[:, :, 3]
        ys, xs = np.where(alpha > int(alpha_threshold))
        if len(xs) == 0:
            return im
    else:
        arr = np.array(im.convert("RGB"))
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        if str(bg_mode).lower() == "white":
            mask = (r < 250) | (g < 250) | (b < 250)
        else:
            # black background content
            mask = (r > 20) | (g > 20) | (b > 20)
        ys, xs = np.where(mask)
        if len(xs) == 0:
            return im
    x0 = max(0, int(xs.min()) - pad)
    x1 = min(im.width, int(xs.max()) + pad + 1)
    y0 = max(0, int(ys.min()) - pad)
    y1 = min(im.height, int(ys.max()) + pad + 1)
    return im.crop((x0, y0, x1, y1))


def pad(
    im: Image.Image,
    padding: int = 32,
    color: str = "#000000",
    transparent: bool = False,
) -> Image.Image:
    p = max(0, int(padding))
    if p == 0:
        return im.copy()
    w, h = im.size
    if transparent or im.mode == "RGBA":
        canvas = Image.new("RGBA", (w + 2 * p, h + 2 * p), (0, 0, 0, 0))
        canvas.paste(ensure_rgba(im), (p, p))
        return canvas
    canvas = Image.new("RGB", (w + 2 * p, h + 2 * p), color)
    canvas.paste(ensure_rgb(im), (p, p))
    return canvas


def border(
    im: Image.Image, width: int = 4, color: str = "#ffffff"
) -> Image.Image:
    w = max(1, int(width))
    if im.mode == "RGBA":
        out = ImageOps.expand(ensure_rgba(im), border=w, fill=(0, 0, 0, 0))
        draw = ImageDraw.Draw(out)
        draw.rectangle([0, 0, out.width - 1, out.height - 1], outline=color, width=w)
        return out
    return ImageOps.expand(ensure_rgb(im), border=w, fill=color)


def opacity(im: Image.Image, factor: float = 1.0) -> Image.Image:
    """Multiply alpha by factor (0..1+)."""
    rgba = ensure_rgba(im)
    arr = np.array(rgba).astype(np.float32)
    arr[:, :, 3] = np.clip(arr[:, :, 3] * float(factor), 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def export(im: Image.Image, path: str | Path, format: str | None = None) -> dict[str, Any]:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fmt = (format or out.suffix.lstrip(".") or "png").upper()
    if fmt == "JPG":
        fmt = "JPEG"
    save_im = im
    save_kwargs: dict[str, Any] = {}
    if fmt == "JPEG":
        save_im = ensure_rgb(im)
        save_kwargs["quality"] = 92
        save_kwargs["optimize"] = True
    elif fmt == "PNG" and im.mode not in ("RGB", "RGBA", "L", "P"):
        save_im = im.convert("RGBA")
    save_im.save(out, format=fmt, **save_kwargs)
    return {"path": str(out), "format": fmt, "width": save_im.width, "height": save_im.height}


# Pipeline step names → callable
PIPELINE_OPS = {
    "auto_orient": lambda im, **kw: auto_orient(im),
    "resize": lambda im, **kw: resize(im, int(kw["width"]), int(kw["height"])),
    "thumbnail": lambda im, **kw: thumbnail(
        im,
        int(kw.get("max_width") or kw.get("width", 512)),
        int(kw.get("max_height") or kw.get("height", 512)),
    ),
    "crop": lambda im, **kw: crop(im, int(kw["x"]), int(kw["y"]), int(kw["width"]), int(kw["height"])),
    "crop_bottom": lambda im, **kw: crop_bottom(im, int(kw.get("keep_height", im.height))),
    "crop_percent": lambda im, **kw: crop_percent(
        im,
        float(kw.get("left", 0)),
        float(kw.get("top", 0)),
        float(kw.get("right", 1)),
        float(kw.get("bottom", 1)),
    ),
    "flip": lambda im, **kw: flip(im, str(kw.get("direction", "horizontal"))),
    "rotate": lambda im, **kw: rotate(im, float(kw.get("degrees", 90))),
    "blur": lambda im, **kw: blur(im, float(kw.get("radius", 2.0))),
    "sharpen": lambda im, **kw: sharpen(im, float(kw.get("percent", 150)), float(kw.get("radius", 2.0))),
    "emboss": lambda im, **kw: emboss(im),
    "contour": lambda im, **kw: contour(im),
    "edge_enhance": lambda im, **kw: edge_enhance(im),
    "find_edges": lambda im, **kw: find_edges(im),
    "detail": lambda im, **kw: detail(im),
    "smooth": lambda im, **kw: smooth(im),
    "desaturate": lambda im, **kw: desaturate(im),
    "invert": lambda im, **kw: invert(im),
    "brightness": lambda im, **kw: brightness(im, float(kw.get("factor", 1.2))),
    "contrast": lambda im, **kw: contrast(im, float(kw.get("factor", 1.2))),
    "saturation": lambda im, **kw: saturation(im, float(kw.get("factor", 1.2))),
    "text": lambda im, **kw: text_overlay(
        im,
        str(kw.get("text", "")),
        int(kw.get("x", 10)),
        int(kw.get("y", 10)),
        int(kw.get("size", 32)),
        str(kw.get("color", "#ffffff")),
    ),
    "erase_rect": lambda im, **kw: erase_rect(
        im,
        int(kw["x"]),
        int(kw["y"]),
        int(kw["width"]),
        int(kw["height"]),
        str(kw.get("fill", "#000000")),
        bool(kw.get("transparent", False)),
    ),
    "fill_rect": lambda im, **kw: fill_rect(
        im, int(kw["x"]), int(kw["y"]), int(kw["width"]), int(kw["height"]), str(kw.get("color", "#000000"))
    ),
    "remove_background": lambda im, **kw: remove_background(
        im,
        str(kw.get("mode", "black")),
        int(kw.get("threshold", 28)),
        int(kw.get("soft", 40)),
    ),
    "cutout": lambda im, **kw: cutout(
        im,
        float(kw.get("thr", 40)),
        bool(kw.get("hard", True)),
        bool(kw.get("defringe", True)),
    ),
    "trim": lambda im, **kw: trim(
        im,
        int(kw.get("padding", 8)),
        int(kw.get("alpha_threshold", 10)),
        str(kw.get("bg_mode", "auto")),
    ),
    "pad": lambda im, **kw: pad(
        im, int(kw.get("padding", 32)), str(kw.get("color", "#000000")), bool(kw.get("transparent", False))
    ),
    "border": lambda im, **kw: border(im, int(kw.get("width", 4)), str(kw.get("color", "#ffffff"))),
    "opacity": lambda im, **kw: opacity(im, float(kw.get("factor", 1.0))),
}


def apply_pipeline(im: Image.Image, steps: list[dict[str, Any]]) -> tuple[Image.Image, list[str]]:
    applied: list[str] = []
    cur = im
    for step in steps:
        op = str(step.get("op") or step.get("name") or "").lower().strip()
        if op not in PIPELINE_OPS:
            raise ValueError(f"unknown pipeline op: {op}; known={sorted(PIPELINE_OPS)}")
        params = {k: v for k, v in step.items() if k not in ("op", "name")}
        cur = PIPELINE_OPS[op](cur, **params)
        applied.append(op)
    return cur, applied
