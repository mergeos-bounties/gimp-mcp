---
name: gimp-mcp
description: >
  Drive GIMP-style image ops via gimp-mcp (MCP + CLI): open/create, resize, crop,
  flip, rotate, blur, desaturate, invert, text overlay, export, batch resize.
  Mock Pillow offline or live gimp-console (GIMP 2.10 / 3.x). Use when the user
  mentions GIMP, gimp-mcp, image batch/resize/export, live-smoke, doctor GIMP,
  or runs /gimp-mcp. After install from GitHub, prefer this skill instead of
  reinventing workflows.
metadata:
  short-description: "GIMP MCP image ops (plugin + CLI)"
---

# GIMP-MCP Operator Guide

**One-command install (Grok plugin from GitHub):**

```bash
grok plugin install mergeos-bounties/gimp-mcp --trust
```

Then install the Python package (MCP stdio binary):

```bash
pip install "git+https://github.com/mergeos-bounties/gimp-mcp.git"
# or from a clone:
# pip install -e ".[dev]"
```

Verify:

```bash
gimp-mcp version
gimp-mcp doctor
gimp-mcp demo
# if GIMP is installed:
gimp-mcp live-smoke
```

Repo: https://github.com/mergeos-bounties/gimp-mcp  
Local clone (maintainer): `D:\ThanhTrucSolutions\mcp\GIMP-mcp`

## Modes

| Mode | Backend | When |
| --- | --- | --- |
| **mock** (default) | Pillow | CI, offline, fast demos |
| **live** | `gimp-console` batch + Pillow assist | GIMP 2.10 / 3.x installed |

| Env | Meaning |
| --- | --- |
| `GIMP_MCP_MODE` | `mock` or `live` |
| `GIMP_MCP_BIN` | Path to `gimp-console` / `gimp-console.exe` |
| `GIMP_MCP_WORKSPACE` | Temp workspace (default `~/.gimp-mcp/workspace`) |
| `GIMP_MCP_TIMEOUT` | Batch timeout seconds (default `120`) |

### Live engines

| GIMP | Resize path |
| --- | --- |
| **3.x** | `python-fu-eval` + GI (`Gimp.file_load` / `scale` / `file_save`) + `--quit` (~2s) |
| **2.10** | Script-Fu `gimp-file-load` / `gimp-image-scale` / `file-png-save` |
| Fallback | Pillow LANCZOS if console fails |

Filters (blur, flip, text, …) use **Pillow assist** on live for cross-version PDB stability.

## Agent workflow

```
1. gimp_doctor          → confirm mode + console
2. gimp_seed_demo (mock) OR gimp_new_image / gimp_open
3. mutate (resize/crop/flip/rotate/blur/desaturate/invert/text)
4. gimp_export absolute path
5. optional gimp_batch_resize
```

Rules:

1. Doctor first when switching hosts/modes.
2. Keep `image_id` from open/new/seed for the same MCP/CLI process.
3. Export to absolute paths the user can open.
4. Prefer **mock** unless the user wants real GIMP console proof.
5. `gimp_seed_demo` is **mock-only**.
6. If MCP tools are missing, use CLI: `gimp-mcp call …`.

## CLI

| Command | Purpose |
| --- | --- |
| `gimp-mcp version` | Package + detected console |
| `gimp-mcp doctor` | Backend health |
| `gimp-mcp demo` | Mock e2e |
| `gimp-mcp live-smoke` | Live new → resize → export |
| `gimp-mcp process <image>` | **Real-photo full pipeline** (thumb, sharpen, watermark, gray, crop, batch) |
| `gimp-mcp tools list` | Tool names |
| `gimp-mcp serve` | Stdio MCP server |
| `gimp-mcp call <tool> key=value` | One-shot tool |

### Real photo pipeline (preferred smoke)

```powershell
$env:GIMP_MCP_MODE = "live"
gimp-mcp process "C:\Users\...\photo.jpg" --out-dir "D:\out\gimp-run" --watermark "MergeOS" --max-side 1280
# Opens Explorer-friendly outputs: *_processed.png, *_gray.png, *_crop_flip_*, batch_thumbs/
```

Examples:

```powershell
gimp-mcp call doctor
gimp-mcp call new_image width=800 height=600 color="#1e293b"
gimp-mcp call open path=C:\Photos\in.png
gimp-mcp call resize image_id=live_1_… width=1280 height=720
gimp-mcp call export image_id=live_1_… path=C:\Photos\out.png
```

Helper (plugin / skill scripts):

```powershell
# From installed plugin or repo skills/gimp-mcp/scripts
./doctor.ps1
./doctor.ps1 -Live
```

## MCP tools

Session: `gimp_mode`, `gimp_doctor`, `gimp_seed_demo`, `gimp_list_images`, `gimp_close`, `gimp_new_image`, `gimp_open`, `gimp_info`

Geometry: `gimp_resize`, `gimp_thumbnail`, `gimp_crop`, `gimp_crop_bottom`, `gimp_crop_percent`, `gimp_flip`, `gimp_rotate`, `gimp_trim`, `gimp_pad`, `gimp_border`

Color / FX: `gimp_blur`, `gimp_sharpen`, `gimp_desaturate`, `gimp_invert`, `gimp_brightness`, `gimp_contrast`, `gimp_saturation`, `gimp_auto_orient`, `gimp_opacity`, `gimp_remove_background`

Paint: `gimp_text_overlay`, `gimp_erase_rect`, `gimp_fill_rect`

Batch / recipes: `gimp_pipeline`, `gimp_export`, `gimp_batch_resize`

### Logo cleanup recipe (drop bottom tagline + transparent)

```python
# gimp_pipeline steps_json:
[
  {"op": "crop_bottom", "keep_height": 920},
  {"op": "remove_background", "mode": "black", "threshold": 24, "soft": 45},
  {"op": "trim", "padding": 20},
  {"op": "pad", "padding": 24, "transparent": true}
]
# then gimp_export to absolute PNG path
```

Params: [references/tools-reference.md](references/tools-reference.md)  
Recipes: [references/workflows.md](references/workflows.md)

## Host config (if not using the plugin `.mcp.json`)

```json
{
  "mcpServers": {
    "gimp-mcp": {
      "command": "gimp-mcp",
      "args": ["serve"],
      "env": { "GIMP_MCP_MODE": "live" }
    }
  }
}
```

Windows live bin override:

```json
"env": {
  "GIMP_MCP_MODE": "live",
  "GIMP_MCP_BIN": "C:\\Users\\<you>\\AppData\\Local\\Programs\\GIMP 3\\bin\\gimp-console.exe"
}
```

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| plugin installed, no tools | `pip install git+https://github.com/mergeos-bounties/gimp-mcp.git` then restart Grok |
| live doctor no console | Install GIMP; set `GIMP_MCP_BIN` |
| resize falls back to pillow | Note engine in reply; GIMP 3 should use `python-fu-eval` after 0.1.1 |
| `unknown image_id` | Re-open in same process |
| seed_demo fails in live | Use `new_image` / `open` |

## Do / Don't

**Do:** export absolute paths; report engine (`python-fu-eval` / `script-fu` / `pillow`); doctor first.  
**Don't:** assume GUI automation (console batch only); invent PDB beyond backend; skip package install after plugin install.
