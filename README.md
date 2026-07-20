# gimp-mcp

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.2.0-0E8A16.svg)](pyproject.toml)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-5319E7.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MergeOS](https://img.shields.io/badge/MergeOS-bounties-5319E7.svg)](https://github.com/mergeos-bounties)

**gimp-mcp** is an MCP server so AI agents can drive **GIMP-style image operations**: open/create images, resize, crop, flip, rotate, blur, desaturate, text overlay, export, and batch resize.

| Mode | Backend | When |
| --- | --- | --- |
| **mock** (default) | Pillow | CI, offline, no GIMP install |
| **live** | `gimp-console` batch + Pillow assist | Machine with GIMP 2.10 / 3.x |

**Product:** [mergeos-bounties/gimp-mcp](https://github.com/mergeos-bounties/gimp-mcp) · Funded: **`prj_0525`**

---

## Install (one command)

### Grok — recommended

```bash
pip install "git+https://github.com/mergeos-bounties/gimp-mcp.git" && grok plugin install mergeos-bounties/gimp-mcp --trust
```

This installs the **Python CLI** (`gimp-mcp`) and the **Grok plugin** (skill + MCP server from `.mcp.json`).

Check:

```bash
gimp-mcp version
gimp-mcp doctor
gimp-mcp demo
grok plugin list
grok mcp list
```

Local clone:

```bash
git clone https://github.com/mergeos-bounties/gimp-mcp.git
cd gimp-mcp
pip install -e ".[dev]"
grok plugin install . --trust
```

### Other agents (stdio MCP)

After `pip install "git+https://github.com/mergeos-bounties/gimp-mcp.git"`, point any MCP host at:

| Field | Value |
| --- | --- |
| command | `gimp-mcp` |
| args | `["serve"]` |
| env | `GIMP_MCP_MODE=mock` |

**Claude Desktop** — merge [examples/claude_desktop_config.json](examples/claude_desktop_config.json) into Claude MCP config.

**Cursor** — merge [examples/cursor_mcp.json](examples/cursor_mcp.json).

**Grok config.toml** (manual, without plugin):

```toml
[mcp_servers.gimp_mcp]
command = "gimp-mcp"
args = ["serve"]
env = { GIMP_MCP_MODE = "mock" }
enabled = true
```

**One-liner via Grok CLI:**

```bash
pip install "git+https://github.com/mergeos-bounties/gimp-mcp.git"
grok mcp add gimp-mcp -- gimp-mcp serve
```


## Supported AI agents / hosts

| Host | Support | Install |
| --- | --- | --- |
| **Grok** (CLI / TUI / Build) | **Yes** | `grok plugin install mergeos-bounties/gimp-mcp --trust` then `pip install "git+https://github.com/mergeos-bounties/gimp-mcp.git"` |
| **Claude Desktop** | **Yes** | Copy [examples/claude_desktop_config.json](examples/claude_desktop_config.json) into Claude MCP settings |
| **Cursor** | **Yes** | Merge [examples/cursor_mcp.json](examples/cursor_mcp.json) into Cursor MCP config |
| **Claude Code** | **Yes** | stdio MCP: same `command`/`args` as Claude Desktop / Grok |
| **VS Code** (MCP / Continue / Cline) | **Yes** | Generic stdio server config pointing at `gimp-mcp serve` |
| **Windsurf / Cascade** | **Yes** | stdio MCP entry with `gimp-mcp` + `serve` |
| **Codex CLI** | **Yes** (stdio) | Register MCP server command `gimp-mcp serve` in Codex MCP settings |
| **ChatGPT Desktop** | **Partial** | Only if host supports custom MCP stdio servers |
| **Gemini CLI** | **Partial** | Only if MCP stdio plugins are enabled |

All packages speak **MCP over stdio** (`gimp-mcp serve`). Default mode is **mock** (offline, no simulator/terminal/GIMP required).


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
| `gimp-mcp process <image>` | Full real-photo pipeline → multiple exports |
| `gimp-mcp serve` | Stdio MCP server |

### Real photos

```powershell
$env:GIMP_MCP_MODE = "live"
gimp-mcp process "C:\path\to\photo.jpg" --out-dir ".\examples\real-run" --watermark "MergeOS"
```

Writes `*_processed.png`, `*_gray.png`, `*_crop_flip_*.png`, and `batch_thumbs/` (GIMP 3 scale via python-fu-eval).

MCP tools: `gimp_mode`, `gimp_doctor`, `gimp_seed_demo`, `gimp_list_images`, `gimp_close`, `gimp_new_image`, `gimp_open`, `gimp_info`, `gimp_resize`, `gimp_thumbnail`, `gimp_crop`, `gimp_flip`, `gimp_rotate`, `gimp_blur`, `gimp_sharpen`, `gimp_desaturate`, `gimp_invert`, `gimp_brightness`, `gimp_contrast`, `gimp_auto_orient`, `gimp_text_overlay`, `gimp_pipeline`, `gimp_export`, `gimp_batch_resize`.

Env:

| Variable | Meaning |
| --- | --- |
| `GIMP_MCP_MODE` | `mock` (default) or `live` |
| `GIMP_MCP_BIN` | Path to `gimp-console` |
| `GIMP_MCP_WORKSPACE` | Working directory for temp images |
| `GIMP_MCP_TIMEOUT` | Batch timeout seconds |

---

## Documentation

| Doc | Contents |
| --- | -------- |
| [docs/GIMP_VERSIONS.md](docs/GIMP_VERSIONS.md) | GIMP 2.10 vs 3.x batch CLI matrix, GIMP_MCP_BIN discovery, migration guide |
| [docs/GIMP_BATCH_FLAGS.md](docs/GIMP_BATCH_FLAGS.md) | Original batch flags quick reference |
| [docs/BOUNTY.md](docs/BOUNTY.md) | MergeOS bounty info |

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
