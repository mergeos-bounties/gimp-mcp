"""Tests for PNG fixture roundtrip."""

import os
import pytest
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"

def test_png_fixture_exists():
    png_file = FIXTURE_DIR / "test.png"
    assert png_file.exists()

def test_png_fixture_readable():
    png_file = FIXTURE_DIR / "test.png"
    with open(png_file, "rb") as f:
        header = f.read(8)
    assert header[:4] == b"\x89PNG"

def test_png_fixture_size():
    png_file = FIXTURE_DIR / "test.png"
    size = png_file.stat().st_size
    assert 100 < size < 10_000_000
