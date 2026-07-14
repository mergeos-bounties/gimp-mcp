"""
Build NHÀ HÀNG GOLD ONE logo variants from emblem + UTM fonts.

Flat style preserves original metallic emblem (soft BG only) and solid flat text
— no aggressive de-glow / white outline.

Usage:
  python scripts/logo_variants.py
  python scripts/logo_variants.py --font HelvetIns --style flat
  python scripts/logo_variants.py --list-fonts
  python scripts/logo_variants.py --all-fonts --styles flat,gradient,twist-depth
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / "assets" / "fonts" / "utm-official"
FULL_PACK = (
    ROOT
    / "assets"
    / "fonts"
    / "utm-full"
    / "extracted"
    / "Font UTM Full"
    / "Font UTM Full"
)
SRC_DEFAULT = Path(r"C:\Users\tupm96\Downloads\Logo-luxury-original.png")
OUT_DEFAULT = Path(r"C:\Users\tupm96\Downloads")
LINE1 = "NHÀ HÀNG"
LINE2 = "GOLD ONE"

# Friendly name → file under utm-official or full pack
FONT_ALIASES: dict[str, str] = {
    "avo": "UTM Avo.ttf",
    "avobold": "UTM AvoBold.ttf",
    "helvetins": "UTM HelvetIns.ttf",
    "times": "UTM Times.ttf",
    "timesbold": "UTMTimesBold.ttf",
    "swiss": "UTM Swiss Condensed.ttf",
    "swissbold": "UTM Swiss CondensedBold.ttf",
    "facebook": "UTM Facebook.ttf",
    "neutra": "UTM Neutra.ttf",
}


def resolve_font(name: str) -> Path:
    key = name.strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    # strip utm prefix for alias
    if key.startswith("utm"):
        key = key[3:]
    fname = FONT_ALIASES.get(key)
    candidates: list[Path] = []
    if fname:
        candidates += [OFFICIAL / fname, FULL_PACK / fname]
    # also try raw name
    candidates += [
        OFFICIAL / name,
        OFFICIAL / f"{name}.ttf",
        FULL_PACK / name,
        FULL_PACK / f"{name}.ttf",
        Path(name),
    ]
    for c in candidates:
        if c.is_file():
            return c
    raise FileNotFoundError(f"font not found: {name}; try --list-fonts")


def list_fonts() -> list[Path]:
    found: list[Path] = []
    for d in (OFFICIAL, FULL_PACK):
        if d.is_dir():
            found.extend(sorted(d.glob("UTM*.ttf")))
            found.extend(sorted(d.glob("UTM*.TTF")))
    # unique by name
    seen: set[str] = set()
    out: list[Path] = []
    for p in found:
        if p.name.startswith("._"):
            continue
        if p.name not in seen:
            seen.add(p.name)
            out.append(p)
    return out


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def trim_rgba(im: Image.Image, pad: int = 12, ath: int = 12) -> Image.Image:
    a = np.array(im)[:, :, 3]
    ys, xs = np.where(a > ath)
    if len(xs) == 0:
        return im
    return im.crop(
        (
            max(0, int(xs.min()) - pad),
            max(0, int(ys.min()) - pad),
            min(im.width, int(xs.max()) + pad + 1),
            min(im.height, int(ys.max()) + pad + 1),
        )
    )


def extract_emblem_layered(
    src: Path,
    keep_bottom: int = 712,
    *,
    hard: bool = True,
    thr: float = 34.0,
    aa: float = 0.0,
    hard_thr: float = 70.0,
    dilate: int = 1,
    erode: int = 0,
    debug_dir: Path | None = None,
) -> Image.Image:
    """
    Layer pipeline:
      color (unpremult) + matte (hard) + defringe → clean RGBA, no soft bloom.
    """
    try:
        from gimp_mcp.layers import cutout_layers, export_layer_debug
    except ImportError:
        sys.path.insert(0, str(ROOT / "src"))
        from gimp_mcp.layers import cutout_layers, export_layer_debug

    raw = Image.open(src).convert("RGBA")
    im = raw.crop((0, 0, raw.width, min(keep_bottom, raw.height)))
    result = cutout_layers(
        im,
        mode="gold",
        thr=thr,
        soft=4.0,
        hard=hard,
        hard_thr=hard_thr,
        erode=erode,
        dilate=dilate,
        defringe_on=True,
        aa=aa,
        unpremult=True,
    )
    if debug_dir is not None:
        debug_dir.mkdir(parents=True, exist_ok=True)
        export_layer_debug(result, debug_dir / "emblem")
    return trim_rgba(result["rgba"], pad=8, ath=10)


def extract_emblem_soft(src: Path, keep_bottom: int = 712) -> Image.Image:
    """Flat: binary matte, no AA; erode 1px to drop dark outer bloom rim."""
    return extract_emblem_layered(
        src,
        keep_bottom,
        hard=True,
        thr=38.0,
        aa=0.0,
        hard_thr=80.0,
        dilate=0,
        erode=1,
    )


def extract_emblem_clean(src: Path, keep_bottom: int = 712) -> Image.Image:
    """Gradient/twist: hard matte + tiny AA."""
    return extract_emblem_layered(
        src, keep_bottom, hard=True, thr=36.0, aa=0.35, hard_thr=75.0, dilate=1
    )

def gold_gradient(size: tuple[int, int], style: str = "vertical") -> Image.Image:
    w, h = size
    stops = np.array(
        [
            [120, 78, 14],
            [188, 140, 42],
            [255, 222, 128],
            [214, 168, 58],
            [148, 98, 22],
        ],
        dtype=np.float32,
    )
    if style == "radial":
        cy, cx = h / 2, w / 2
        yy, xx = np.mgrid[0:h, 0:w]
        t = np.sqrt(((xx - cx) / (w / 2 + 1e-6)) ** 2 + ((yy - cy) / (h / 2 + 1e-6)) ** 2)
        t = np.clip(t * 0.85, 0, 1)
    elif style == "diagonal":
        yy, xx = np.mgrid[0:h, 0:w]
        t = xx / max(w - 1, 1) * 0.5 + yy / max(h - 1, 1) * 0.5
    else:
        t = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        t = np.repeat(t, w, axis=1)
    n = len(stops) - 1
    pos = np.clip(t * n, 0, n - 0.001)
    i0 = np.floor(pos).astype(int)
    f = (pos - i0)[..., None]
    rgb = stops[i0] * (1 - f) + stops[np.clip(i0 + 1, 0, n)] * f
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")


def apply_gradient_to_rgba(im: Image.Image, style: str = "diagonal") -> Image.Image:
    arr = np.array(im)
    alpha = arr[:, :, 3]
    grad = np.array(gold_gradient(im.size, style)).astype(np.float32)
    base = arr[:, :, 0:3].astype(np.float32)
    lum = (0.299 * base[:, :, 0] + 0.587 * base[:, :, 1] + 0.114 * base[:, :, 2]) / 255.0
    mixed = grad * (0.5 + 0.6 * lum[..., None])
    out = arr.copy()
    mask = alpha > 8
    out[mask, 0:3] = np.clip(mixed[mask], 0, 255)
    return Image.fromarray(out, "RGBA")


def render_two_line_mask(font: ImageFont.ImageFont, gap: int = 10) -> Image.Image:
    b1 = font.getbbox(LINE1)
    b2 = font.getbbox(LINE2)
    w1, h1 = b1[2] - b1[0], b1[3] - b1[1]
    w2, h2 = b2[2] - b2[0], b2[3] - b2[1]
    pad = 20
    w = max(w1, w2) + pad * 2
    h = h1 + h2 + gap + pad * 2
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    x1 = (w - w1) // 2 - b1[0]
    x2 = (w - w2) // 2 - b2[0]
    y1 = pad - b1[1]
    y2 = pad + h1 + gap - b2[1]
    draw.text((x1, y1), LINE1, font=font, fill=255)
    draw.text((x2, y2), LINE2, font=font, fill=255)
    return mask


def mask_to_flat(mask: Image.Image, color: tuple[int, int, int] = (212, 168, 52)) -> Image.Image:
    """True flat: solid gold, NO white outline, crisp alpha."""
    # binary for sharp glyph edges
    hard = mask.point(lambda p: 255 if p > 100 else 0)
    face = Image.new("RGBA", mask.size, (*color, 255))
    face.putalpha(hard)
    return face


def mask_to_gradient(mask: Image.Image) -> Image.Image:
    soft = mask.point(lambda p: min(255, int(p * 1.05)) if p > 40 else 0)
    grad = gold_gradient(mask.size, "vertical")
    face = grad.convert("RGBA")
    face.putalpha(soft)
    # subtle drop only (no white stroke)
    sm = soft.transform(mask.size, Image.Transform.AFFINE, (1, 0, 0, 0, 1, -3))
    sh = Image.new("RGBA", mask.size, (40, 22, 4, 0))
    sh.putalpha(sm.point(lambda p: int(p * 0.35)))
    out = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    out = Image.alpha_composite(out, sh)
    out = Image.alpha_composite(out, face)
    return out


def mask_to_twist_depth(mask: Image.Image) -> Image.Image:
    w, h = mask.size
    pad = 32
    cw, ch = w + pad * 2, h + pad * 2
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    depth = 14
    hard = mask.point(lambda p: 255 if p > 100 else 0)
    for i in range(depth, 0, -1):
        t = i / depth
        ox = int(i * 1.1 + math.sin(t * math.pi * 2) * 1.8)
        oy = int(i * 1.3 + math.cos(t * math.pi * 1.5) * 1.4)
        shear = 0.02 * math.sin(t * math.pi)
        m = hard.transform(
            hard.size,
            Image.Transform.AFFINE,
            (1, shear, 0, 0, 1, 0),
            resample=Image.Resampling.BILINEAR,
            fillcolor=0,
        )
        col = (int(85 + 45 * (1 - t)), int(52 + 28 * (1 - t)), int(10 + 10 * (1 - t)), 255)
        layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        layer.paste(col, (pad + ox, pad + oy), m)
        canvas = Image.alpha_composite(canvas, layer)
    top = mask_to_gradient(hard)
    face = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    face.paste(top, (pad, pad), top)
    canvas = Image.alpha_composite(canvas, face)
    return trim_rgba(canvas, pad=4)


def compose(
    emblem: Image.Image,
    text_im: Image.Image,
    gap: int = 32,
    *,
    crisp: bool = False,
) -> Image.Image:
    target_w = int(emblem.width * 1.0)
    if text_im.width != target_w:
        ratio = target_w / max(text_im.width, 1)
        # NEAREST for flat = no semi-transparent fringe from LANCZOS
        resample = Image.Resampling.NEAREST if crisp else Image.Resampling.LANCZOS
        text_im = text_im.resize(
            (target_w, max(1, int(text_im.height * ratio))), resample
        )
        if crisp:
            # re-binarize alpha after nearest scale
            arr = np.array(text_im)
            arr[:, :, 3] = np.where(arr[:, :, 3] > 128, 255, 0).astype(np.uint8)
            text_im = Image.fromarray(arr, "RGBA")
    width = max(emblem.width, text_im.width) + 32
    height = emblem.height + gap + text_im.height + 32
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ex = (width - emblem.width) // 2
    ey = 12
    canvas.alpha_composite(emblem, (ex, ey))
    tx = (width - text_im.width) // 2
    ty = ey + emblem.height + gap
    canvas.alpha_composite(text_im, (tx, ty))
    return trim_rgba(canvas, pad=14, ath=8)


def preview(logo: Image.Image, bg: tuple[int, int, int], path: Path) -> None:
    c = Image.new("RGB", logo.size, bg)
    c.paste(logo, mask=logo.split()[-1])
    c.save(path, "PNG")


def build_one(
    font_path: Path,
    style: str,
    src: Path,
    out_dir: Path,
    set_main: bool = False,
    tag: str | None = None,
) -> Path:
    style = style.lower().strip()
    if style not in ("flat", "gradient", "twist-depth", "twist", "depth"):
        raise ValueError(f"unknown style {style}")
    if style in ("twist", "depth"):
        style = "twist-depth"

    # flat: soft emblem; gradient/twist: slightly cleaner key
    if style == "flat":
        emblem = extract_emblem_soft(src)
    else:
        emblem = extract_emblem_clean(src)

    fsize = max(48, int(emblem.width * 0.12))
    font = load_font(font_path, fsize)
    mask = render_two_line_mask(font, gap=max(6, fsize // 7))

    if style == "flat":
        emb, txt = emblem, mask_to_flat(mask)  # original metal + solid flat type
    elif style == "gradient":
        emb, txt = apply_gradient_to_rgba(emblem, "diagonal"), mask_to_gradient(mask)
    else:
        emb, txt = emblem, mask_to_twist_depth(mask)

    logo = compose(emb, txt, crisp=(style == "flat"))

    # stable tag: UTM-HelvetIns style (spaces → hyphens)
    label = tag or font_path.stem.replace(" ", "-")
    out_path = out_dir / f"Logo-luxury-{label}-{style}.png"
    logo.save(out_path, "PNG")
    preview(logo, (255, 255, 255), out_dir / f"Logo-luxury-{label}-{style}-preview-white.png")
    preview(logo, (12, 12, 14), out_dir / f"Logo-luxury-{label}-{style}-preview-dark.png")

    if set_main or (label.lower().find("helvet") >= 0 and style == "flat"):
        # user preferred HelvetIns flat as reference quality
        pass
    if set_main:
        logo.save(out_dir / "Logo-luxury.png", "PNG")
        preview(logo, (255, 255, 255), out_dir / "Logo-luxury-preview-on-white.png")
        # short aliases
        logo.save(out_dir / f"Logo-luxury-{style}.png", "PNG")

    print(f"OK {out_path.name}  size={logo.size}  font={font_path.name}  style={style}")
    return out_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gold One logo builder (UTM fonts)")
    p.add_argument("--font", default="HelvetIns", help="Font alias or path (default HelvetIns)")
    p.add_argument(
        "--style",
        default="flat",
        help="flat | gradient | twist-depth (default flat)",
    )
    p.add_argument("--styles", default="", help="Comma list of styles")
    p.add_argument("--all-fonts", action="store_true", help="Build for all official UTM fonts")
    p.add_argument("--list-fonts", action="store_true")
    p.add_argument("--src", type=Path, default=SRC_DEFAULT)
    p.add_argument("--out-dir", type=Path, default=OUT_DEFAULT)
    p.add_argument("--main", action="store_true", help="Also write Logo-luxury.png")
    p.add_argument("--proof", action="store_true", help="Write plain font proof PNG")
    args = p.parse_args(argv)

    if args.list_fonts:
        for f in list_fonts():
            print(f.name)
        for alias, fname in sorted(FONT_ALIASES.items()):
            print(f"  alias {alias} -> {fname}")
        return 0

    if not args.src.is_file():
        print(f"missing source logo: {args.src}", file=sys.stderr)
        return 1
    args.out_dir.mkdir(parents=True, exist_ok=True)

    styles = [s.strip() for s in (args.styles or args.style).split(",") if s.strip()]
    if args.all_fonts:
        fonts = [OFFICIAL / n for n in FONT_ALIASES.values() if (OFFICIAL / n).is_file()]
        if not fonts:
            fonts = list_fonts()[:12]
    else:
        fonts = [resolve_font(args.font)]

    for fp in fonts:
        if args.proof:
            font = load_font(fp, 72)
            im = Image.new("RGB", (1100, 140), "white")
            d = ImageDraw.Draw(im)
            d.text((20, 35), f"{LINE1} {LINE2}", font=font, fill="#1a1a1a")
            d.text((20, 100), fp.name, font=load_font(fp, 22), fill="#666")
            im.save(args.out_dir / f"FONT-PROOF-{fp.stem.replace(' ', '')}.png")
        for st in styles:
            set_main = bool(args.main) and st == styles[0] and fp == fonts[0]
            build_one(fp, st, args.src, args.out_dir, set_main=set_main)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
