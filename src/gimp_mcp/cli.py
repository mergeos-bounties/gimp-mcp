from __future__ import annotations

import json
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
    "gimp_new_image",
    "gimp_open",
    "gimp_info",
    "gimp_resize",
    "gimp_crop",
    "gimp_flip",
    "gimp_rotate",
    "gimp_blur",
    "gimp_desaturate",
    "gimp_invert",
    "gimp_text_overlay",
    "gimp_export",
    "gimp_batch_resize",
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

    def _need(*keys: str) -> None:
        missing = [k for k in keys if k not in kv or kv[k] in ("", None)]
        if missing:
            raise typer.Exit(f"missing args: {', '.join(k + '=...' for k in missing)}")

    dispatch = {
        "gimp_mode": lambda: switch_mode(str(kv.get("mode", get_mode()))),
        "gimp_doctor": b.doctor,
        "gimp_seed_demo": b.seed_demo,
        "gimp_list_images": b.list_images,
        "gimp_new_image": lambda: b.new_image(
            int(kv.get("width", 800)), int(kv.get("height", 600)), str(kv.get("color", "#ffffff"))
        ),
        "gimp_open": lambda: b.open_image(str(kv.get("path", ""))),
        "gimp_info": lambda: b.info(str(kv.get("image_id", ""))),
        "gimp_resize": lambda: b.resize(
            str(kv.get("image_id", "")), int(kv.get("width", 256)), int(kv.get("height", 256))
        ),
        "gimp_crop": lambda: (
            _need("image_id", "x", "y", "width", "height")
            or b.crop(
                str(kv["image_id"]),
                int(kv["x"]),
                int(kv["y"]),
                int(kv["width"]),
                int(kv["height"]),
            )
        ),
        "gimp_flip": lambda: b.flip(
            str(kv.get("image_id", "")), str(kv.get("direction", "horizontal"))
        ),
        "gimp_rotate": lambda: b.rotate(
            str(kv.get("image_id", "")), float(kv.get("degrees", 90))
        ),
        "gimp_blur": lambda: b.blur(str(kv.get("image_id", "")), float(kv.get("radius", 2.0))),
        "gimp_desaturate": lambda: b.desaturate(str(kv.get("image_id", ""))),
        "gimp_invert": lambda: b.invert(str(kv.get("image_id", ""))),
        "gimp_text_overlay": lambda: b.text_overlay(
            str(kv.get("image_id", "")),
            str(kv.get("text", "")),
            int(kv.get("x", 10)),
            int(kv.get("y", 10)),
            int(kv.get("size", 32)),
            str(kv.get("color", "#000000")),
        ),
        "gimp_export": lambda: b.export(
            str(kv.get("image_id", "")), str(kv.get("path", "out.png")), kv.get("format")
        ),
        "gimp_batch_resize": lambda: b.batch_resize(
            str(kv.get("input_dir", "")),
            str(kv.get("output_dir", "")),
            int(kv.get("width", 256)),
            int(kv.get("height", 256)),
        ),
    }
    if name not in dispatch:
        raise typer.Exit(f"unknown tool {name}; try: gimp-mcp tools list")
    rprint(dispatch[name]())


@app.command("serve")
def serve_cmd() -> None:
    """Run MCP stdio server."""
    from gimp_mcp.server import run_stdio

    run_stdio()
