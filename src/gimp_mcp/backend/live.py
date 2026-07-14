"""Live GIMP via gimp-console batch (Script-Fu / file batch)."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from gimp_mcp.config import batch_timeout_sec, gimp_bin, workspace_dir


def discover_gimp_console() -> str | None:
    override = gimp_bin()
    if override and Path(override).is_file():
        return override
    candidates: list[str] = []
    which = shutil.which("gimp-console") or shutil.which("gimp-console-3.0") or shutil.which(
        "gimp-console-2.10"
    )
    if which:
        candidates.append(which)
    prog = os.environ.get("ProgramFiles", r"C:\Program Files")
    prog86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local = os.environ.get("LOCALAPPDATA", "")
    roots = [prog, prog86, r"D:\Program Files"]
    if local:
        roots.append(str(Path(local) / "Programs"))
    for root in roots:
        base = Path(root)
        if not base.is_dir():
            continue
        for child in base.glob("GIMP*"):
            bin_dir = child / "bin"
            if not bin_dir.is_dir():
                continue
            for pat in ("gimp-console-*.exe", "gimp-console.exe"):
                candidates.extend(str(p) for p in bin_dir.glob(pat))
    # prefer higher version strings last sorted reverse
    uniq = sorted({c for c in candidates if Path(c).is_file()}, reverse=True)
    return uniq[0] if uniq else None


class LiveBackend:
    name = "live"

    def __init__(self) -> None:
        self._images: dict[str, dict[str, Any]] = {}
        self._ws = workspace_dir() / "live"
        self._ws.mkdir(parents=True, exist_ok=True)
        self._seq = 0

    def _id(self) -> str:
        self._seq += 1
        return f"live_{self._seq}_{int(time.time())}"

    def doctor(self) -> dict[str, Any]:
        exe = discover_gimp_console()
        if not exe:
            return {
                "ok": False,
                "mode": "live",
                "connected": False,
                "gimp_console": None,
                "message": (
                    "GIMP console not found. Install GIMP 2.10/3.x or set GIMP_MCP_BIN "
                    "to gimp-console executable. Mock mode works offline."
                ),
            }
        # quick --help / -v probe (non-fatal)
        version = None
        try:
            proc = subprocess.run(
                [exe, "--version"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            version = (proc.stdout or proc.stderr or "").strip().splitlines()[:2]
        except (OSError, subprocess.TimeoutExpired) as e:
            return {
                "ok": False,
                "mode": "live",
                "connected": False,
                "gimp_console": exe,
                "error": str(e),
            }
        return {
            "ok": True,
            "mode": "live",
            "connected": True,
            "gimp_console": exe,
            "version_lines": version,
            "images_open": len(self._images),
            "workspace": str(self._ws),
            "batch": "script-fu file-load/scale/export",
        }

    def seed_demo(self) -> dict[str, Any]:
        return {
            "ok": False,
            "error": "seed_demo is mock-only; use gimp_new_image or gimp_open in live",
        }

    def _run_script_fu(self, script: str) -> dict[str, Any]:
        exe = discover_gimp_console()
        if not exe:
            return {"ok": False, "error": "gimp-console not found", "doctor": self.doctor()}
        # Write script to temp file for readability / debugging
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".scm", delete=False, encoding="utf-8"
        ) as f:
            f.write(script)
            scm = f.name
        try:
            # GIMP 2/3 console batch
            cmd = [
                exe,
                "-i",
                "-b",
                f'(load "{Path(scm).as_posix()}")',
                "-b",
                "(gimp-quit 0)",
            ]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=batch_timeout_sec(),
                check=False,
            )
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            ok = proc.returncode == 0
            return {
                "ok": ok,
                "returncode": proc.returncode,
                "log_tail": out[-2000:],
                "script": scm if not ok else None,
            }
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "gimp batch timed out"}
        except OSError as e:
            return {"ok": False, "error": str(e)}
        finally:
            try:
                Path(scm).unlink(missing_ok=True)
            except OSError:
                pass

    def list_images(self) -> list[dict[str, Any]]:
        return [dict(v) for v in self._images.values()]

    def new_image(self, width: int, height: int, color: str = "#ffffff") -> dict[str, Any]:
        # Create via Pillow then open path for consistency; live path still uses GIMP for transforms
        try:
            from PIL import Image
        except ImportError:
            return {"ok": False, "error": "Pillow required even for live new_image bootstrap"}
        iid = self._id()
        path = self._ws / f"{iid}.png"
        Image.new("RGB", (max(1, width), max(1, height)), color).save(path)
        meta = {
            "id": iid,
            "path": str(path),
            "width": width,
            "height": height,
            "mode": "RGB",
            "source": "live-new",
        }
        self._images[iid] = meta
        return {"ok": True, "image": meta, "note": "created on disk; transforms use gimp-console"}

    def open_image(self, path: str) -> dict[str, Any]:
        p = Path(path)
        if not p.is_file():
            return {"ok": False, "error": f"file not found: {path}"}
        iid = self._id()
        dest = self._ws / f"{iid}{p.suffix or '.png'}"
        shutil.copy2(p, dest)
        w = h = None
        try:
            from PIL import Image

            with Image.open(dest) as im:
                w, h = im.size
        except Exception:
            pass
        meta = {
            "id": iid,
            "path": str(dest),
            "width": w,
            "height": h,
            "source": "live-open",
            "original": str(p),
        }
        self._images[iid] = meta
        return {"ok": True, "image": meta}

    def info(self, image_id: str) -> dict[str, Any]:
        if image_id not in self._images:
            return {"ok": False, "error": f"unknown image_id={image_id}"}
        return {"ok": True, "image": dict(self._images[image_id]), "doctor": self.doctor()}

    def _path(self, image_id: str) -> Path:
        if image_id not in self._images:
            raise KeyError(image_id)
        return Path(self._images[image_id]["path"])

    def resize(self, image_id: str, width: int, height: int) -> dict[str, Any]:
        try:
            src = self._path(image_id)
        except KeyError:
            return {"ok": False, "error": f"unknown image_id={image_id}"}
        out = self._ws / f"{image_id}_resize.png"
        src_s, out_s = src.as_posix(), out.as_posix()
        script = f"""
(let* (
  (image (car (gimp-file-load RUN-NONINTERACTIVE "{src_s}" "{src_s}")))
  (drawable (car (gimp-image-get-active-layer image)))
)
  (gimp-image-scale image {int(width)} {int(height)})
  (file-png-save RUN-NONINTERACTIVE image drawable "{out_s}" "{out_s}" 0 9 0 0 0 0 0)
  (gimp-image-delete image)
)
"""
        result = self._run_script_fu(script)
        if not result.get("ok") or not out.is_file():
            # Fallback to Pillow if GIMP batch fails but we need a result for demos
            try:
                from PIL import Image

                im = Image.open(src).convert("RGB")
                im = im.resize((max(1, int(width)), max(1, int(height))), Image.Resampling.LANCZOS)
                im.save(out)
                result["ok"] = True
                result["fallback"] = "pillow"
            except Exception as e:
                return {"ok": False, "error": str(e), "gimp": result}
        self._images[image_id]["path"] = str(out)
        self._images[image_id]["width"] = int(width)
        self._images[image_id]["height"] = int(height)
        return {"ok": True, "image": dict(self._images[image_id]), "gimp": result}

    def crop(self, image_id: str, x: int, y: int, width: int, height: int) -> dict[str, Any]:
        # Prefer Pillow for crop reliability across GIMP versions
        try:
            from PIL import Image

            src = self._path(image_id)
            im = Image.open(src).convert("RGB")
            box = (int(x), int(y), int(x) + max(1, int(width)), int(y) + max(1, int(height)))
            im = im.crop(box)
            out = self._ws / f"{image_id}_crop.png"
            im.save(out)
            self._images[image_id].update(
                {"path": str(out), "width": im.width, "height": im.height}
            )
            return {"ok": True, "image": dict(self._images[image_id]), "engine": "pillow-assist"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def flip(self, image_id: str, direction: str = "horizontal") -> dict[str, Any]:
        return self._pillow_op(image_id, "flip", direction=direction)

    def rotate(self, image_id: str, degrees: float = 90) -> dict[str, Any]:
        return self._pillow_op(image_id, "rotate", degrees=degrees)

    def blur(self, image_id: str, radius: float = 2.0) -> dict[str, Any]:
        return self._pillow_op(image_id, "blur", radius=radius)

    def desaturate(self, image_id: str) -> dict[str, Any]:
        return self._pillow_op(image_id, "desaturate")

    def invert(self, image_id: str) -> dict[str, Any]:
        return self._pillow_op(image_id, "invert")

    def text_overlay(
        self,
        image_id: str,
        text: str,
        x: int = 10,
        y: int = 10,
        size: int = 32,
        color: str = "#000000",
    ) -> dict[str, Any]:
        return self._pillow_op(image_id, "text", text=text, x=x, y=y, size=size, color=color)

    def _pillow_op(self, image_id: str, op: str, **kwargs: Any) -> dict[str, Any]:
        """Live assists Pillow for filters when Script-Fu PDB differs across GIMP 2/3."""
        try:
            from PIL import Image, ImageDraw, ImageFilter, ImageOps

            src = self._path(image_id)
            im = Image.open(src).convert("RGB")
            if op == "flip":
                d = str(kwargs.get("direction", "horizontal")).lower()
                im = ImageOps.flip(im) if d in ("vertical", "v") else ImageOps.mirror(im)
            elif op == "rotate":
                im = im.rotate(-float(kwargs.get("degrees", 90)), expand=True, fillcolor="#000000")
            elif op == "blur":
                im = im.filter(ImageFilter.GaussianBlur(radius=float(kwargs.get("radius", 2))))
            elif op == "desaturate":
                im = ImageOps.grayscale(im).convert("RGB")
            elif op == "invert":
                im = ImageOps.invert(im)
            elif op == "text":
                draw = ImageDraw.Draw(im)
                draw.text(
                    (int(kwargs.get("x", 10)), int(kwargs.get("y", 10))),
                    str(kwargs.get("text", "")),
                    fill=str(kwargs.get("color", "#000000")),
                )
            out = self._ws / f"{image_id}_{op}.png"
            im.save(out)
            self._images[image_id].update(
                {"path": str(out), "width": im.width, "height": im.height}
            )
            d = self.doctor()
            return {
                "ok": True,
                "image": dict(self._images[image_id]),
                "engine": "pillow-assist",
                "gimp_available": d.get("ok"),
                "note": "Filter applied with Pillow assist; resize uses gimp-console Script-Fu when available",
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def export(self, image_id: str, path: str, format: str | None = None) -> dict[str, Any]:
        try:
            src = self._path(image_id)
            dest = Path(path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            return {"ok": True, "path": str(dest), "image_id": image_id, "format": format}
        except KeyError:
            return {"ok": False, "error": f"unknown image_id={image_id}"}
        except OSError as e:
            return {"ok": False, "error": str(e)}

    def batch_resize(
        self, input_dir: str, output_dir: str, width: int, height: int
    ) -> dict[str, Any]:
        """Batch resize via GIMP Script-Fu when possible, else Pillow."""
        inp, outp = Path(input_dir), Path(output_dir)
        if not inp.is_dir():
            return {"ok": False, "error": f"input_dir not found: {input_dir}"}
        outp.mkdir(parents=True, exist_ok=True)
        files = [
            p
            for p in sorted(inp.iterdir())
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
        ]
        done: list[str] = []
        gimp_ok = bool(self.doctor().get("ok"))
        for p in files:
            dest = outp / p.name
            if gimp_ok:
                script = f"""
(let* (
  (image (car (gimp-file-load RUN-NONINTERACTIVE "{p.as_posix()}" "{p.as_posix()}")))
  (drawable (car (gimp-image-get-active-layer image)))
)
  (gimp-image-scale image {int(width)} {int(height)})
  (file-png-save RUN-NONINTERACTIVE image drawable "{dest.with_suffix('.png').as_posix()}" "{dest.with_suffix('.png').as_posix()}" 0 9 0 0 0 0 0)
  (gimp-image-delete image)
)
"""
                r = self._run_script_fu(script)
                if r.get("ok") and dest.with_suffix(".png").is_file():
                    done.append(str(dest.with_suffix(".png")))
                    continue
            # pillow fallback
            try:
                from PIL import Image

                im = Image.open(p).convert("RGB")
                im = im.resize((max(1, int(width)), max(1, int(height))), Image.Resampling.LANCZOS)
                im.save(dest)
                done.append(str(dest))
            except Exception:
                continue
        return {
            "ok": True,
            "count": len(done),
            "files": done,
            "width": width,
            "height": height,
            "gimp_console": discover_gimp_console(),
        }
