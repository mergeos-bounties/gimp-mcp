# gimp-mcp workflows

## Install (user machine)

```bash
grok plugin install mergeos-bounties/gimp-mcp --trust
pip install "git+https://github.com/mergeos-bounties/gimp-mcp.git"
gimp-mcp doctor
```

## Offline demo

```bash
export GIMP_MCP_MODE=mock   # PowerShell: $env:GIMP_MCP_MODE="mock"
gimp-mcp demo
```

## Live smoke (GIMP installed)

```bash
export GIMP_MCP_MODE=live
gimp-mcp live-smoke
# gimp-mcp live-smoke --image /path/to/photo.png
```

Expect resize `gimp.engine` = `python-fu-eval` on GIMP 3.x (not pillow fallback).

## Resize + export via CLI

```bash
gimp-mcp call open path=/abs/in.png
# copy image_id from JSON
gimp-mcp call resize image_id=IMG width=1280 height=720
gimp-mcp call export image_id=IMG path=/abs/out.png
```

## Batch thumbs

```bash
gimp-mcp call batch_resize input_dir=/abs/raw output_dir=/abs/thumbs width=256 height=256
```

## Dev gate

```bash
pip install -e ".[dev]"
ruff check src tests
pytest -q
gimp-mcp demo
gimp-mcp live-smoke
```
