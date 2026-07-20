from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from gimp_mcp import __version__
from gimp_mcp.backend import get_backend, switch_mode
from gimp_mcp.backend.live import discover_gimp_console, probe_gimp_version
from gimp_mcp.config import get_mode, set_mode

app = typer.Typer(help="gimp-mcp — MCP server for GIMP image ops", no_args_is_help=True)
tools_app = typer.Typer(help="List tools")
app.add_typer(tools_app, name="tools")
console = Console()

TOOL_NAMES = [
    "gimp_mode",
    "gimp_doctor",
    "gimp_seed_demo",
    "gimp_list_images",
    "gimp_close",
    "gimp_new_image",
    "gimp_open",
    "gimp_info",
    "gimp_resize",
    "gimp_thumbnail",
    "gimp_crop",
    "gimp_crop_bottom",
    "gimp_crop_percent",
    "gimp_flip",
    "gimp_rotate",
    "gimp_blur",
    "gimp_sharpen",
    "gimp_desaturate",
    "gimp_invert",
    "gimp_brightness",
    "gimp_contrast",
    "gimp_saturation",
    "gimp_auto_orient",
    "gimp_erase_rect",
    "gimp_fill_rect",
    "gimp_remove_background",
    "gimp_cutout",
    "gimp_trim",
    "gimp_pad",
    "gimp_border",
    "gimp_opacity",
    "gimp_text_overlay",
    "gimp_pipeline",
    "gimp_export",
    "gimp_batch_resize",
    "gimp_list_layers",
    "gimp_new_layer",
    "gimp_flatten",
]


@app.command("version")
def version_cmd() -> None:
    ver = probe_gimp_version()
    rprint(
        {
            "version": __version__,
            "mode": get_mode(),
            "gimp_console": discover_gimp_console(),
            "gimp_major": ver.get("major"),
            "gimp_version_lines": ver.get("lines"),
        }
    )


@app.command("doctor")
def doctor_cmd() -> None:
    b = get_backend()
    info = b.doctor()
    info["gimp_mcp_version"] = __version__
    info["mode"] = get_mode()
    info["detected_gimp_console"] = discover_gimp_console()
    rprint(info)


@app.command("demo")
def demo_cmd() -> None:
    """Offline smoke: seed, resize, blur, export."""
    set_mode("mock")
    b = get_backend()
    seed = b.seed_demo()
    rprint(seed)
    iid = seed["image"]["id"]
    rprint(b.doctor())
    rprint(b.resize(iid, 320, 180))
    rprint(b.blur(iid, 1.5))
    rprint(b.text_overlay(iid, "MergeOS", 20, 20))
    out = b.export(iid, str(b._ws / "demo_export.png"))  # noqa: SLF001
    rprint(out)
    rprint({"images": b.list_images()})
    rprint("gimp-mcp demo complete (mock).")


@app.command("live-smoke")
def live_smoke_cmd(
    image: Optional[str] = typer.Option(None, "--image", help="Optional input image path"),
) -> None:
    """Run against real gimp-console if installed; else report doctor."""
    set_mode("live")
    b = get_backend()
    d = b.doctor()
    rprint({"doctor": d})
    if not d.get("ok"):
        rprint({"skipped": True, "reason": "GIMP console not available"})
        raise typer.Exit(0)
    if image:
        opened = b.open_image(image)
    else:
        opened = b.new_image(400, 300, "#334155")
    rprint(opened)
    if not opened.get("ok"):
        raise typer.Exit(1)
    iid = opened["image"]["id"]
    resized = b.resize(iid, 200, 150)
    rprint(resized)
    rprint(b.export(iid, str(b._ws / "live_smoke.png")))  # noqa: SLF001
    engine = (resized.get("gimp") or {}).get("engine") or (resized.get("gimp") or {}).get(
        "fallback"
    )
    rprint({"live_smoke": "complete", "resize_engine": engine})
    rprint("gimp-mcp live-smoke complete.")


@app.command("logo")
def logo_cmd(
    font: str = typer.Option("HelvetIns", "--font", "-f", help="UTM alias: HelvetIns, AvoBold, TimesBold, SwissBold…"),
    style: str = typer.Option("flat", "--style", "-s", help="flat | gradient | twist-depth"),
    styles: str = typer.Option("", "--styles", help="Comma list, e.g. flat,gradient"),
    src: str = typer.Option(
        str(Path.home() / "Downloads" / "Logo-luxury-original.png"),
        "--src",
        help="Source full logo PNG",
    ),
    out_dir: str = typer.Option(str(Path.home() / "Downloads"), "--out-dir", "-o"),
    main: bool = typer.Option(False, "--main", help="Also write Logo-luxury.png"),
    proof: bool = typer.Option(False, "--proof", help="Write plain font proof"),
    list_fonts: bool = typer.Option(False, "--list-fonts", help="List UTM fonts"),
    all_fonts: bool = typer.Option(False, "--all-fonts"),
) -> None:
    """Build NHÀ HÀNG GOLD ONE logo variants (UTM fonts, quality flat)."""
    import subprocess
    import sys

    script = Path(__file__).resolve().parents[2] / "scripts" / "logo_variants.py"
    if not script.is_file():
        # installed package: look next to site or repo
        script = Path(__file__).resolve().parents[1].parent / "scripts" / "logo_variants.py"
    # develop layout: repo/scripts
    repo_script = Path(r"D:\ThanhTrucSolutions\mcp\GIMP-mcp\scripts\logo_variants.py")
    if repo_script.is_file():
        script = repo_script
    if not script.is_file():
        rprint({"ok": False, "error": f"logo script not found: {script}"})
        raise typer.Exit(1)

    cmd = [sys.executable, str(script)]
    if list_fonts:
        cmd.append("--list-fonts")
    else:
        cmd += ["--font", font, "--src", src, "--out-dir", out_dir]
        if styles:
            cmd += ["--styles", styles]
        else:
            cmd += ["--style", style]
        if main:
            cmd.append("--main")
        if proof:
            cmd.append("--proof")
        if all_fonts:
            cmd.append("--all-fonts")
    rprint({"cmd": cmd})
    raise typer.Exit(subprocess.call(cmd))


@app.command("logo-flat")
def logo_flat_cmd(
    font: str = typer.Option("HelvetIns", "--font", "-f"),
    main: bool = typer.Option(True, "--main/--no-main"),
) -> None:
    """Shortcut: high-quality flat logo (no aggressive de-glow)."""
    logo_cmd(
        font=font,
        style="flat",
        styles="",
        src=str(Path.home() / "Downloads" / "Logo-luxury-original.png"),
        out_dir=str(Path.home() / "Downloads"),
        main=main,
        proof=True,
        list_fonts=False,
        all_fonts=False,
    )


@app.command("process")
def process_cmd(
    image: str = typer.Argument(..., help="Input image path"),
    out_dir: str = typer.Option(
        "",
        "--out-dir",
        help="Output directory (default: ~/.gimp-mcp/real-run)",
    ),
    mode: str = typer.Option("live", "--mode", help="mock|live"),
    max_side: int = typer.Option(1280, "--max-side", help="Thumbnail max side"),
    watermark: str = typer.Option("gimp-mcp", "--watermark", help="Text overlay"),
) -> None:
    """
    Full real-image pipeline: open → thumbnail → sharpen → contrast → watermark →
    grayscale copy → batch thumbs. Writes multiple outputs for visual verification.
    """
    set_mode(mode)
    b = get_backend()
    src = Path(image)
    if not src.is_file():
        rprint({"ok": False, "error": f"file not found: {image}"})
        raise typer.Exit(1)

    dest_root = Path(out_dir) if out_dir else Path.home() / ".gimp-mcp" / "real-run"
    dest_root.mkdir(parents=True, exist_ok=True)
    stem = src.stem

    doctor = b.doctor()
    rprint({"doctor": doctor, "input": str(src), "out_dir": str(dest_root), "mode": get_mode()})

    opened = b.open_image(str(src))
    rprint({"open": opened})
    if not opened.get("ok"):
        raise typer.Exit(1)
    iid = opened["image"]["id"]

    steps: list[dict[str, Any]] = [
        {"op": "auto_orient"},
        {"op": "thumbnail", "max_width": max_side, "max_height": max_side},
        {"op": "sharpen", "percent": 120, "radius": 1.5},
        {"op": "contrast", "factor": 1.15},
        {"op": "brightness", "factor": 1.05},
        {
            "op": "text",
            "text": watermark,
            "x": 24,
            "y": 24,
            "size": 36,
            "color": "#ffffff",
        },
    ]
    pipe = b.pipeline(iid, steps)
    rprint({"pipeline": {"ok": pipe.get("ok"), "applied": pipe.get("applied"), "image": pipe.get("image")}})
    if not pipe.get("ok"):
        raise typer.Exit(1)

    main_out = dest_root / f"{stem}_processed.png"
    exp = b.export(iid, str(main_out))
    rprint({"export_main": exp})

    # grayscale variant
    gray = b.desaturate(iid)
    gray_out = dest_root / f"{stem}_gray.png"
    rprint({"desaturate": {"ok": gray.get("ok"), "image": gray.get("image")}})
    rprint({"export_gray": b.export(iid, str(gray_out))})

    # reopen original for crop + flip showcase
    o2 = b.open_image(str(src))
    iid2 = o2["image"]["id"]
    w = int(o2["image"].get("width") or 1000)
    h = int(o2["image"].get("height") or 1000)
    cx, cy = w // 4, h // 4
    cw, ch = max(100, w // 2), max(100, h // 2)
    b.crop(iid2, cx, cy, cw, ch)
    b.flip(iid2, "horizontal")
    b.resize(iid2, 640, 360)
    crop_out = dest_root / f"{stem}_crop_flip_640x360.png"
    rprint({"export_crop_flip": b.export(iid2, str(crop_out))})

    # batch: copy 3 inputs into a folder and batch-resize
    batch_in = dest_root / "batch_in"
    batch_out = dest_root / "batch_thumbs"
    if batch_in.exists():
        shutil.rmtree(batch_in, ignore_errors=True)
    batch_in.mkdir(parents=True, exist_ok=True)
    batch_out.mkdir(parents=True, exist_ok=True)
    # seed batch with main + a couple siblings if available
    shutil.copy2(src, batch_in / src.name)
    siblings = list(src.parent.glob("*.jpg"))[:3]
    for s in siblings:
        if s.name != src.name:
            shutil.copy2(s, batch_in / s.name)
    batch = b.batch_resize(str(batch_in), str(batch_out), 320, 180)
    rprint({"batch_resize": batch})

    # inventory outputs
    outputs = sorted(str(p) for p in dest_root.rglob("*") if p.is_file())
    rprint(
        {
            "ok": True,
            "process": "complete",
            "outputs": outputs,
            "main": str(main_out),
            "count": len(outputs),
        }
    )


@tools_app.command("list")
def tools_list() -> None:
    table = Table(title="gimp-mcp tools")
    table.add_column("Tool")
    for n in TOOL_NAMES:
        table.add_row(n)
    console.print(table)


def _parse_kv(arg: Optional[list[str]]) -> dict[str, Any]:
    kv: dict[str, Any] = {}
    for a in arg or []:
        if "=" not in a:
            continue
        k, v = a.split("=", 1)
        try:
            kv[k] = json.loads(v)
        except json.JSONDecodeError:
            kv[k] = v
    return kv


@app.command("call")
def call_cmd(
    tool: str = typer.Argument(..., help="e.g. doctor or gimp_doctor"),
    arg: Optional[list[str]] = typer.Argument(None, help="key=value"),
) -> None:
    b = get_backend()
    name = tool if tool.startswith("gimp_") else f"gimp_{tool}"
    kv = _parse_kv(arg)

    # Dynamically dispatch all TOOL_NAMES from the backend
    dispatch = {}
    for tool_name in TOOL_NAMES:
        if tool_name == "gimp_mode":
            dispatch[tool_name] = lambda: switch_mode(str(kv.get("mode", get_mode())))
        elif tool_name == "gimp_doctor":
            dispatch[tool_name] = b.doctor
        elif tool_name == "gimp_seed_demo":
            dispatch[tool_name] = b.seed_demo
        elif tool_name == "gimp_list_images":
            dispatch[tool_name] = b.list_images
        elif tool_name == "gimp_close":
            dispatch[tool_name] = lambda: b.close_image(str(kv.get("image_id", "")))
        elif tool_name == "gimp_new_image":
            dispatch[tool_name] = lambda: b.new_image(
                int(kv.get("width", 800)), int(kv.get("height", 600)), str(kv.get("color", "#ffffff"))
            )
        elif tool_name == "gimp_open":
            dispatch[tool_name] = lambda: b.open_image(str(kv.get("path", "")))
        elif tool_name == "gimp_info":
            dispatch[tool_name] = lambda: b.info(str(kv.get("image_id", "")))
        elif tool_name == "gimp_resize":
            dispatch[tool_name] = lambda: b.resize(
                str(kv.get("image_id", "")), int(kv.get("width", 256)), int(kv.get("height", 256))
            )
        elif tool_name == "gimp_thumbnail":
            dispatch[tool_name] = lambda: b.thumbnail(
                str(kv.get("image_id", "")),
                int(kv.get("max_width", 512)),
                int(kv.get("max_height", 512)),
            )
        elif tool_name == "gimp_crop":
            dispatch[tool_name] = lambda: b.crop(
                str(kv.get("image_id", "")),
                int(kv.get("x", 0)),
                int(kv.get("y", 0)),
                int(kv.get("width", 100)),
                int(kv.get("height", 100)),
            )
        elif tool_name == "gimp_flip":
            dispatch[tool_name] = lambda: b.flip(
                str(kv.get("image_id", "")), str(kv.get("direction", "horizontal"))
            )
        elif tool_name == "gimp_rotate":
            dispatch[tool_name] = lambda: b.rotate(
                str(kv.get("image_id", "")), float(kv.get("degrees", 90))
            )
        elif tool_name == "gimp_blur":
            dispatch[tool_name] = lambda: b.blur(str(kv.get("image_id", "")), float(kv.get("radius", 2.0)))
        elif tool_name == "gimp_sharpen":
            dispatch[tool_name] = lambda: b.sharpen(
                str(kv.get("image_id", "")),
                float(kv.get("percent", 150)),
                float(kv.get("radius", 2.0)),
            )
        elif tool_name == "gimp_desaturate":
            dispatch[tool_name] = lambda: b.desaturate(str(kv.get("image_id", "")))
        elif tool_name == "gimp_invert":
            dispatch[tool_name] = lambda: b.invert(str(kv.get("image_id", "")))
        elif tool_name == "gimp_brightness":
            dispatch[tool_name] = lambda: b.brightness(
                str(kv.get("image_id", "")), float(kv.get("factor", 1.2))
            )
        elif tool_name == "gimp_contrast":
            dispatch[tool_name] = lambda: b.contrast(
                str(kv.get("image_id", "")), float(kv.get("factor", 1.2))
            )
        elif tool_name == "gimp_saturation":
            dispatch[tool_name] = lambda: b.saturation(
                str(kv.get("image_id", "")), float(kv.get("factor", 1.2))
            )
        elif tool_name == "gimp_auto_orient":
            dispatch[tool_name] = lambda: b.auto_orient(str(kv.get("image_id", "")))
        elif tool_name == "gimp_crop_bottom":
            dispatch[tool_name] = lambda: b.crop_bottom(
                str(kv.get("image_id", "")), int(kv.get("keep_height", 100))
            )
        elif tool_name == "gimp_crop_percent":
            dispatch[tool_name] = lambda: b.crop_percent(
                str(kv.get("image_id", "")),
                float(kv.get("left", 0)),
                float(kv.get("top", 0)),
                float(kv.get("right", 1)),
                float(kv.get("bottom", 1)),
            )
        elif tool_name == "gimp_erase_rect":
            dispatch[tool_name] = lambda: b.erase_rect(
                str(kv.get("image_id", "")),
                int(kv.get("x", 0)),
                int(kv.get("y", 0)),
                int(kv.get("width", 10)),
                int(kv.get("height", 10)),
                str(kv.get("fill", "#000000")),
                bool(kv.get("transparent", False)),
            )
        elif tool_name == "gimp_fill_rect":
            dispatch[tool_name] = lambda: b.fill_rect(
                str(kv.get("image_id", "")),
                int(kv.get("x", 0)),
                int(kv.get("y", 0)),
                int(kv.get("width", 10)),
                int(kv.get("height", 10)),
                str(kv.get("color", "#000000")),
            )
        elif tool_name == "gimp_remove_background":
            dispatch[tool_name] = lambda: b.remove_background(
                str(kv.get("image_id", "")),
                str(kv.get("mode", "black")),
                int(kv.get("threshold", 28)),
                int(kv.get("soft", 40)),
            )
        elif tool_name == "gimp_cutout":
            dispatch[tool_name] = lambda: b.cutout(
                str(kv.get("image_id", "")),
                float(kv.get("thr", 40)),
                bool(kv.get("hard", True)),
                bool(kv.get("defringe", True)),
            )
        elif tool_name == "gimp_trim":
            dispatch[tool_name] = lambda: b.trim(
                str(kv.get("image_id", "")),
                int(kv.get("padding", 8)),
                int(kv.get("alpha_threshold", 10)),
                str(kv.get("bg_mode", "auto")),
            )
        elif tool_name == "gimp_pad":
            dispatch[tool_name] = lambda: b.pad(
                str(kv.get("image_id", "")),
                int(kv.get("padding", 32)),
                str(kv.get("color", "#000000")),
                bool(kv.get("transparent", False)),
            )
        elif tool_name == "gimp_border":
            dispatch[tool_name] = lambda: b.border(
                str(kv.get("image_id", "")),
                int(kv.get("width", 4)),
                str(kv.get("color", "#ffffff")),
            )
        elif tool_name == "gimp_opacity":
            dispatch[tool_name] = lambda: b.opacity(
                str(kv.get("image_id", "")), float(kv.get("factor", 1.0))
            )
        elif tool_name == "gimp_text_overlay":
            dispatch[tool_name] = lambda: b.text_overlay(
                str(kv.get("image_id", "")),
                str(kv.get("text", "")),
                int(kv.get("x", 10)),
                int(kv.get("y", 10)),
                int(kv.get("size", 32)),
                str(kv.get("color", "#000000")),
            )
        elif tool_name == "gimp_pipeline":
            dispatch[tool_name] = lambda: b.pipeline(
                str(kv.get("image_id", "")),
                json.loads(str(kv.get("steps_json", "[]"))),
            )
        elif tool_name == "gimp_export":
            dispatch[tool_name] = lambda: b.export(
                str(kv.get("image_id", "")), str(kv.get("path", "out.png")), kv.get("format")
            )
        elif tool_name == "gimp_list_layers":
            dispatch[tool_name] = lambda: b.list_layers(str(kv.get("image_id", "")))
        elif tool_name == "gimp_new_layer":
            dispatch[tool_name] = lambda: b.new_layer(
                str(kv.get("image_id", "")),
                str(kv.get("name", "New Layer"))
            )
        elif tool_name == "gimp_flatten":
            dispatch[tool_name] = lambda: b.flatten(str(kv.get("image_id", "")))
    
﻿        elif tool_name == "gimp_mode":
            dispatch[tool_name] = lambda: b.doctor() if not kv.get("mode") else switch_mode(str(kv.get("mode", "")))
        elif tool_name == "gimp_batch_resize":
            dispatch[tool_name] = lambda: b.batch_resize(
                str(kv.get("input_dir", "")),
                str(kv.get("output_dir", "")),
                int(kv.get("width", 256)),
                int(kv.get("height", 256)),
            )
        elif tool_name == "gimp_histogram":
            dispatch[tool_name] = lambda: b.histogram(str(kv.get("image_id", "")))
        elif tool_name == "gimp_exif":
            dispatch[tool_name] = lambda: b.exif(str(kv.get("image_id", "")))

    # Verify all TOOL_NAMES are dispatched
    missing = set(TOOL_NAMES) - set(dispatch.keys())
    if missing:
        raise RuntimeError(f"Missing dispatch for: {missing}")
    if name not in dispatch:
        raise typer.Exit(f"unknown tool {name}; try: gimp-mcp tools list")
    rprint(dispatch[name]())


@app.command("layers")
def layers_cmd(image_id: str = typer.Argument(..., help="Image ID to list layers")) -> None:
    """List layers in the specified image."""
    from gimp_mcp.backend import get_backend
    b = get_backend()
    result = b.list_layers(image_id)
    rprint(result)


@app.command("new-layer")
def new_layer_cmd(
    image_id: str = typer.Argument(..., help="Image ID to add layer to"),
    name: str = typer.Option("New Layer", help="Name of the new layer")
) -> None:
    """Create a new layer in the specified image."""
    from gimp_mcp.backend import get_backend
    b = get_backend()
    result = b.new_layer(image_id, name)
    rprint(result)


@app.command("flatten")
def flatten_cmd(image_id: str = typer.Argument(..., help="Image ID to flatten")) -> None:
    """Flatten all layers in the specified image."""
    from gimp_mcp.backend import get_backend
    b = get_backend()
    result = b.flatten(image_id)
    rprint(result)
