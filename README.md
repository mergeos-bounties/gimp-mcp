# gimp-mcp

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0-0E8A16.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MergeOS](https://img.shields.io/badge/MergeOS-bounties-5319E7.svg)](https://github.com/mergeos-bounties)

**gimp-mcp** is an MCP server so AI agents can drive **GIMP-style image operations**: open/create images, resize, crop, flip, rotate, blur, desaturate, text overlay, export, and batch resize.

| Mode | Backend | When |
| --- | --- | --- |
| **mock** (default) | Pillow | CI, offline, no GIMP install |
| **live** | `gimp-console` batch + Pillow assist | Machine with GIMP 2.10 / 3.x |

**Product:** [mergeos-bounties/gimp-mcp](https://github.com/mergeos-bounties/gimp-mcp) · Funded: **`prj_0525`**

---

## Highlights

| Capability | Description |
| --- | --- |
| **MCP tools** | `gimp_doctor`, `gimp_open`, `gimp_resize`, `gimp_export`, … |
| **CLI** | `gimp-mcp demo`, `doctor`, `live-smoke`, `serve` |
| **Offline demo** | Always works with Pillow mock |
| **Live batch** | Detects `gimp-console` for scale/batch via Script-Fu |

---

## Quick start

```powershell
cd mcp\GIMP-mcp
pip install -e ".[dev]"
gimp-mcp version
gimp-mcp doctor
gimp-mcp demo
pytest -q
```

### Live GIMP (optional)

```powershell
# Install GIMP 3.x, then:
$env:GIMP_MCP_MODE = "live"
# optional override:
# $env:GIMP_MCP_BIN = "C:\Program Files\GIMP 3\bin\gimp-console-3.0.exe"
gimp-mcp doctor
gimp-mcp live-smoke
```

### MCP host config

See [examples/claude_desktop_config.json](examples/claude_desktop_config.json) and [examples/cursor_mcp.json](examples/cursor_mcp.json).

```json
{
  "mcpServers": {
    "gimp-mcp": {
      "command": "gimp-mcp",
      "args": ["serve"],
      "env": { "GIMP_MCP_MODE": "mock" }
    }
  }
}
```

---

## CLI / tools

| Command | Purpose |
| --- | --- |
| `gimp-mcp version` | Package + detected console |
| `gimp-mcp doctor` | Backend health |
| `gimp-mcp demo` | Mock end-to-end smoke |
| `gimp-mcp live-smoke` | Live console smoke (skips if missing) |
| `gimp-mcp tools list` | MCP tool names |
| `gimp-mcp serve` | Stdio MCP server |

MCP tools: `gimp_mode`, `gimp_doctor`, `gimp_seed_demo`, `gimp_list_images`, `gimp_new_image`, `gimp_open`, `gimp_info`, `gimp_resize`, `gimp_crop`, `gimp_flip`, `gimp_rotate`, `gimp_blur`, `gimp_desaturate`, `gimp_invert`, `gimp_text_overlay`, `gimp_export`, `gimp_batch_resize`.

Env:

| Variable | Meaning |
| --- | --- |
| `GIMP_MCP_MODE` | `mock` (default) or `live` |
| `GIMP_MCP_BIN` | Path to `gimp-console` |
| `GIMP_MCP_WORKSPACE` | Working directory for temp images |
| `GIMP_MCP_TIMEOUT` | Batch timeout seconds |

---

## Development

```powershell
pip install -e ".[dev]"
ruff check src tests
pytest -q
```

---

## MergeOS bounties

**Follow** [mergeos-bounties](https://github.com/mergeos-bounties) + **star** [mergeos](https://github.com/mergeos-bounties/mergeos) and [mergeos-contracts](https://github.com/mergeos-bounties/mergeos-contracts). Claim issues → PR to **master** → **25–200 MRG**.

See [docs/BOUNTY.md](docs/BOUNTY.md).

---

## License

MIT — see [LICENSE](LICENSE).

## Live test note (maintainer)

Verified on Windows with GIMP **3.2.4** at:
`%LOCALAPPDATA%\Programs\GIMP 3\bin\gimp-console.exe`

- `gimp-mcp doctor` (live) detects console and version
- `gimp-mcp live-smoke` completes (resize may use Pillow assist if Script-Fu batch times out on GIMP 3)
