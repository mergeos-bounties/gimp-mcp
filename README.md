# gimp-mcp

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.1-0E8A16.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MergeOS](https://img.shields.io/badge/MergeOS-bounties-5319E7.svg)](https://github.com/mergeos-bounties)

**gimp-mcp** is an MCP server so AI agents can drive **GIMP-style image operations**: open/create images, resize, crop, flip, rotate, blur, desaturate, text overlay, export, and batch resize.

| Mode | Backend | When |
| --- | --- | --- |
| **mock** (default) | Pillow | CI, offline, no GIMP install |
| **live** | `gimp-console` batch + Pillow assist | Machine with GIMP 2.10 / 3.x |

**Product:** [mergeos-bounties/gimp-mcp](https://github.com/mergeos-bounties/gimp-mcp) · Funded: **`prj_0525`**

---

## Install for Grok (one command)

```bash
grok plugin install mergeos-bounties/gimp-mcp --trust
```

That installs the **skill** + **MCP server config** from this repo. Then install the Python package so `gimp-mcp serve` is on PATH:

```bash
pip install "git+https://github.com/mergeos-bounties/gimp-mcp.git"
```

Check:

```bash
gimp-mcp version
gimp-mcp doctor
gimp-mcp demo
# with GIMP 3.x installed:
gimp-mcp live-smoke
```

Local plugin validate (from a clone):

```bash
grok plugin validate .
grok plugin install . --trust
```

---

## Highlights

| Capability | Description |
| --- | --- |
| **MCP tools** | `gimp_doctor`, `gimp_open`, `gimp_resize`, `gimp_export`, … |
| **CLI** | `gimp-mcp demo`, `doctor`, `live-smoke`, `serve`, `call` |
| **Offline demo** | Always works with Pillow mock |
| **Live GIMP 3** | `python-fu-eval` + `--quit` (~2s scale on Windows) |
| **Live GIMP 2** | Script-Fu batch |
| **Grok plugin** | `skills/gimp-mcp` + `.mcp.json` + `.grok-plugin/plugin.json` |

---

## Quick start (developers)

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
# $env:GIMP_MCP_BIN = "$env:LOCALAPPDATA\Programs\GIMP 3\bin\gimp-console.exe"
gimp-mcp doctor
gimp-mcp live-smoke
```

### MCP host config

Plugin ships [`.mcp.json`](.mcp.json). Manual examples: [examples/claude_desktop_config.json](examples/claude_desktop_config.json), [examples/cursor_mcp.json](examples/cursor_mcp.json).

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

---

## CLI / tools

| Command | Purpose |
| --- | --- |
| `gimp-mcp version` | Package + detected console |
| `gimp-mcp doctor` | Backend health |
| `gimp-mcp demo` | Mock end-to-end smoke |
| `gimp-mcp live-smoke` | Live console smoke (skips if missing) |
| `gimp-mcp tools list` | MCP tool names |
| `gimp-mcp call …` | One-shot tool (`key=value`) |
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

Plugin layout:

```
.grok-plugin/plugin.json   # Grok plugin manifest
.mcp.json                  # MCP stdio server for Grok
skills/gimp-mcp/           # Skill (auto-loaded after plugin install)
.grok/skills/gimp-mcp/     # Same skill for in-repo discovery
```

---

## MergeOS bounties

**Follow** [mergeos-bounties](https://github.com/mergeos-bounties) + **star** [mergeos](https://github.com/mergeos-bounties/mergeos) and [mergeos-contracts](https://github.com/mergeos-bounties/mergeos-contracts). Claim issues → PR to **master** → **25–200 MRG**.

See [docs/BOUNTY.md](docs/BOUNTY.md).

---

## License

MIT — see [LICENSE](LICENSE).

## Live test note (maintainer)

Verified on Windows with GIMP **3.2.4** at  
`%LOCALAPPDATA%\Programs\GIMP 3\bin\gimp-console.exe`

- Live resize uses **python-fu-eval** + `--quit` (not Script-Fu hang)
- `gimp-mcp live-smoke` completes in a few seconds
- Filters may still use Pillow assist by design
