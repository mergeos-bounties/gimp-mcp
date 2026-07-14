# GIMP 3 vs 2.10 Batch Flags Matrix

## Overview

GIMP 3 introduces significant changes to batch processing. This document covers the key differences.

## Batch Mode Invocation

| Feature | GIMP 2.10 | GIMP 3 |
|---------|-----------|--------|
| Batch script | `gimp -i -b '(script-fu-command)'` | `gimp -i -b '(python-fu-eval "code")'` |
| Python support | Script-Fu only | Python-Fu (default) |
| Headless mode | `-i` flag | `-i` flag (same) |
| Output redirect | `--batch-interpreter` | `--batch-interpreter` |

## Common Flags

```bash
# GIMP 2.10
gimp -i -b '(gimp-quit 0)'

# GIMP 3
gimp -i -b '(python-fu-eval "import sys; sys.exit(0)")'
```

## Python-Fu in GIMP 3

```python
# Batch processing with GIMP 3
import subprocess

def run_gimp_batch(script):
    cmd = [
        'gimp', '-i', '-b',
        f'(python-fu-eval \"{script}\")'
    ]
    return subprocess.run(cmd, capture_output=True)
```

## Migration Notes

1. Script-Fu scripts need conversion to Python-Fu
2. Some APIs have changed signatures
3. New `Gimp.run()` context manager available
4. Improved error handling in batch mode
