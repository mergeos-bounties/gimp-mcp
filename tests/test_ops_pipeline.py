from pathlib import Path

from gimp_mcp.backend.mock import MockBackend
from gimp_mcp.config import set_mode


def test_new_ops_and_pipeline(tmp_path: Path):
    set_mode("mock")
    b = MockBackend()
    s = b.seed_demo()
    iid = s["image"]["id"]

    assert b.crop_bottom(iid, 200)["ok"]
    assert b.info(iid)["image"]["height"] == 200
    assert b.thumbnail(iid, 200, 200)["ok"]
    assert b.sharpen(iid, 120, 1.0)["ok"]
    assert b.brightness(iid, 1.1)["ok"]
    assert b.contrast(iid, 1.1)["ok"]
    assert b.saturation(iid, 1.1)["ok"]
    assert b.auto_orient(iid)["ok"]

    pipe = b.pipeline(
        iid,
        [
            {"op": "thumbnail", "max_width": 160, "max_height": 90},
            {"op": "desaturate"},
            {"op": "text", "text": "hi", "x": 5, "y": 5, "size": 16, "color": "#fff"},
            {"op": "remove_background", "mode": "black", "threshold": 10, "soft": 20},
            {"op": "trim", "padding": 4},
        ],
    )
    assert pipe["ok"] is True
    assert "desaturate" in pipe["applied"]
    assert "remove_background" in pipe["applied"]
    assert pipe["image"]["width"] <= 160

    out = tmp_path / "p.png"
    exp = b.export(iid, str(out), "PNG")
    assert exp["ok"] is True
    assert out.is_file()

    closed = b.close_image(iid)
    assert closed["ok"] is True
    assert b.list_images() == []


def test_logo_tagline_strip(tmp_path: Path):
    """Simulate luxury logo: drop bottom tagline, transparent bg."""
    from PIL import Image, ImageDraw

    set_mode("mock")
    b = MockBackend()
    canvas = Image.new("RGB", (400, 300), "#000000")
    d = ImageDraw.Draw(canvas)
    d.rectangle((100, 20, 300, 140), fill="#c9a227")  # mark
    d.rectangle((80, 160, 320, 200), fill="#d4af37")  # brand name
    d.rectangle((90, 230, 310, 250), fill="#b8860b")  # subtitle
    d.rectangle((70, 260, 330, 290), fill="#aa8800")  # tagline to remove
    src = tmp_path / "logo_src.png"
    canvas.save(src)
    opened = b.open_image(str(src))
    iid = opened["image"]["id"]
    # keep only top 220px (drop tagline)
    assert b.crop_bottom(iid, 220)["ok"]
    assert b.info(iid)["image"]["height"] == 220
    assert b.remove_background(iid, mode="black", threshold=20, soft=30)["ok"]
    assert b.trim(iid, padding=4)["ok"]
    out = tmp_path / "logo_out.png"
    assert b.export(iid, str(out))["ok"]
    im = Image.open(out)
    assert im.mode == "RGBA"
    assert im.height <= 220


def test_process_cli_mock(tmp_path: Path):
    from typer.testing import CliRunner

    from gimp_mcp.cli import app
    from PIL import Image

    src = tmp_path / "photo.jpg"
    Image.new("RGB", (800, 600), "#336699").save(src, quality=90)
    out = tmp_path / "run"
    runner = CliRunner()
    r = runner.invoke(
        app,
        ["process", str(src), "--out-dir", str(out), "--mode", "mock", "--watermark", "TEST"],
    )
    assert r.exit_code == 0, r.stdout
    assert "process" in r.stdout
    assert list(out.glob("*_processed.png")), r.stdout
