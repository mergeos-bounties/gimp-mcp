# GIMP Versions: 2.10 vs 3.x Batch CLI & Discovery

## Batch Mode Invocation

| Aspect | GIMP 2.10 | GIMP 3.x |
|--------|-----------|----------|
| **Script engine** | Script-Fu (Scheme) | Python-Fu (Python 3) preferred; Script-Fu deprecated |
| **Batch interpreter flag** | `--batch-interpreter script-fu` (default) | `--batch-interpreter python-fu-eval` |
| **Execute command** | `-b '(script-fu-command args)'` | `-b '(python-fu-eval "exec(open('''script.py''').read())")'` |
| **Headless mode** | `-i` (no X server) | `-i` (same, still works) |
| **Disable data** | `-d` (no fonts, patterns) | `-d` (same) |
| **Disable fonts** | `-f` | `-f` (same) |
| **Exit after batch** | `-b '(gimp-quit 0)'` + `--quit` | `--quit` alone suffices |
| **Script file type** | `.scm` (Scheme) | `.py` (Python) |
| **Error handling** | Silent failures, non-zero exit on crash | Structured stderr, improved crash reporting |
| **Batch marker** | Manual `(gimp-quit 0)` | `--quit` auto-exits after batch command |

## CLI Flag Comparison

### GIMP 2.10 Classic Flags

```bash
# Minimal headless batch
gimp -i -d -f -b '(load "/path/to/script.scm")' -b '(gimp-quit 0)'

# With explicit interpreter
gimp -i --batch-interpreter script-fu -b '(script-fu-command "arg1" "arg2")' -b '(gimp-quit 0)'
```

### GIMP 3.x Flags

```bash
# Python-Fu batch (recommended)
gimp -i -d -f -c --batch-interpreter python-fu-eval \
  -b 'exec(open("/path/to/script.py").read())' --quit

# One-liner
gimp -i -d -f -c --batch-interpreter python-fu-eval \
  -b "from gi.repository import Gimp, Gio; ..." --quit

# Script-Fu fallback (deprecated in 3.x)
gimp -i -d -f -c -b '(load "/path/to/script.scm")' -b '(gimp-quit 0)'
```

## Batch Execution Paths (gimp-mcp)

### GIMP 3.x — `_run_python_fu` (`live.py:201`)

```
Flags: -i -d -f -c --batch-interpreter python-fu-eval -b <code> --quit
Code:  exec(open('/tmp/...py').read())
Detect: OK_ marker in stdout, or "batch command executed successfully"
```

### GIMP 2.10 — `_run_script_fu` (`live.py:253`)

```
Flags: -i -d -f -c -b '(load "...")' -b '(gimp-quit 0)' --quit
Script: Temporary .scm file written to disk
Detect: returncode == 0
```

## GIMP_MCP_BIN Discovery Algorithm

The server locates the `gimp-console` binary through a multi-step fallback
implemented in `discover_gimp_console()` (`src/gimp_mcp/backend/live.py:19`).

### Step 1: Environment variable override

```python
GIMP_MCP_BIN          # Primary override — full path to gimp-console
GIMP_CONSOLE          # Legacy fallback (deprecated, still supported)
```

If `GIMP_MCP_BIN` is set and the file exists, it is returned immediately.
See `config.py:22-25`.

### Step 2: PATH lookup

The function calls `shutil.which()` for each of these names in order:

1. `gimp-console`
2. `gimp-console-3.0`
3. `gimp-console-3`
4. `gimp-console-2.10`

The first match is added as a candidate.

### Step 3: Windows Program Files scan

Common install roots (from environment variables or defaults):

| Variable / Root | Example |
|-----------------|---------|
| `%ProgramFiles%` | `C:\Program Files` |
| `%ProgramFiles(x86)%` | `C:\Program Files (x86)` |
| `%LOCALAPPDATA%\Programs` | `C:\Users\<user>\AppData\Local\Programs` |
| `D:\Program Files` | Hardcoded fallback for secondary drives |

For each root, the scanner globs for `GIMP*` directories, then inside each
checks `bin/` for `gimp-console-*.exe` and `gimp-console.exe`.

### Step 4: Version ranking

Candidates are sorted descending by version number extracted from the
filename (`3.2 > 3.0 > 2.10 > plain`). The highest-ranked existing file
is returned.

```
Rank: gimp-console-3.2.exe > gimp-console-3.0.exe > gimp-console-2.10.exe > gimp-console.exe
```

### Step 5: Fallback

If no binary is found, `discover_gimp_console()` returns `None`. The
server operates in mock-only mode.

## Version Probing

Once a binary is located, `probe_gimp_version()` (`live.py:67`) runs
`<exe> --version` and parses the output:

- Extracts major version from `"version X."` pattern
- Falls back to filename heuristic (`gimp-console-3*` → major=3,
  `gimp-console-2*` → major=2)
- Caches result per binary path to avoid repeated subprocess calls

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `GIMP_MCP_MODE` | `mock` | Backend mode: `mock` (Pillow) or `live` (gimp-console) |
| `GIMP_MCP_BIN` | — | Full path to `gimp-console` executable |
| `GIMP_CONSOLE` | — | Legacy override (deprecated, use `GIMP_MCP_BIN`) |
| `GIMP_MCP_WORKSPACE` | `~/.gimp-mcp/workspace` | Working directory for temp images |
| `GIMP_MCP_TIMEOUT` | `120` | Batch subprocess timeout in seconds |

## Common Headless Flags

| Flag | 2.10 | 3.x | Meaning |
|------|------|-----|---------|
| `-i` | ✓ | ✓ | No X server (headless) |
| `-d` | ✓ | ✓ | Skip data (fonts, patterns, brushes) |
| `-f` | ✓ | ✓ | Skip fonts |
| `-c` | ✗ | ✓ | No console window (Windows) |
| `--no-data` | ✓ | ✓ | Same as `-d` |
| `--no-fonts` | ✓ | ✓ | Same as `-f` |
| `--batch-interpreter` | ✓ | ✓ | Set script language |
| `-b` | ✓ | ✓ | Execute batch command |
| `--quit` | ✓ | ✓ | Exit after batch |
| `--verbose` | ✓ | ✓ | Verbose output |
| `--stack-trace-mode` | ✓ | ✓ | Error trace detail |

## Migration Guide: 2.10 → 3.x

### Script Conversion

1. **Rewrite Script-Fu (Scheme) to Python-Fu.** GIMP 3 still loads
   Script-Fu, but it is deprecated and may be removed.
2. **Use `gi.repository`** — GIMP 3's Python API is based on GObject
   introspection:
   ```python
   from gi.repository import Gimp, Gio, GLib
   ```
3. **File I/O requires `Gio.File`** — paths must be wrapped:
   ```python
   image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, Gio.File.new_for_path(path))
   ```

### API Signature Changes

| Operation | GIMP 2.10 (Script-Fu) | GIMP 3.x (Python-Fu) |
|-----------|----------------------|----------------------|
| Load image | `(gimp-file-load RUN-NONINTERACTIVE path raw-path)` | `Gimp.file_load(RunMode.NONINTERACTIVE, Gio.File.new_for_path(path))` |
| Scale | `(gimp-image-scale image w h)` | `image.scale(w, h)` |
| Save | `(file-png-save ...)` | `Gimp.file_save(RunMode.NONINTERACTIVE, image, Gio.File.new_for_path(dst), None)` |
| Delete | `(gimp-image-delete image)` | `image.delete()` |
| Get active layer | `(car (gimp-image-get-active-layer image))` | `image.get_active_layer()` |

### Batch Exit

- **2.10:** Must call `(gimp-quit 0)` explicitly as the last batch
  command, otherwise GIMP hangs open.
- **3.x:** `--quit` flag suffices. No explicit quit command needed.

### Error Handling

- **2.10:** Silent failures — Script-Fu errors may not surface in stderr.
  Detect by checking return code and output file existence.
- **3.x:** Structured stderr output. Python exceptions print tracebacks.
  The string `"batch command executed successfully"` in stdout signals
  clean completion.

### Testing Your Migration

```bash
# Check the version
gimp-console --version

# Test Python-Fu batch
gimp-console -i -d -f -c --batch-interpreter python-fu-eval \
  -b "print('hello gimp 3')" --quit

# Expected output: "hello gimp 3" followed by "batch command executed successfully"
```

## References

- [GIMP_BATCH_FLAGS.md](GIMP_BATCH_FLAGS.md) — Original batch flags matrix
- `src/gimp_mcp/backend/live.py` — Discovery & batch execution source
- `src/gimp_mcp/config.py` — Environment variable handling
- [GIMP 3 Release Notes](https://www.gimp.org/release-notes/gimp-3.0.html)
