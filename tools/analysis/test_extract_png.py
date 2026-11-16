"""Tests for PNG export from BPP graphics (extract_bpp.py).

Covers:
  - tiles_to_png with synthetic tiles + palette
  - PNG output verification (mode, size, pixel values)
  - Edge cases: empty tiles, no palette, out-of-range indices
  - Scale factor
  - CLI --png flag
"""

import os
import sys
import tempfile

_test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _test_dir)
sys.path.insert(0, os.path.dirname(_test_dir))

from extract_assets.extract_bpp import (
    parse_bpp_tiles,
    _encode_bpp_tiles,
    tile_count,
    tiles_to_png,
    TILE_SIZE,
)
from extract_assets.extract_palette import (
    parse_palette,
    rgb555_to_rgb,
)


def _make_solid_tile(color=0):
    return [color] * 64


def _make_synthetic_tiles(num_tiles=4, bpp=4):
    tiles = []
    for i in range(num_tiles):
        val = i % (4 if bpp == 4 else 16)
        tiles.append(_make_solid_tile(val))
    return tiles


def _make_palette(num_colors=16):
    palette = []
    for i in range(num_colors):
        r = (i * 16) % 256
        g = (i * 32) % 256
        b = (i * 64) % 256
        palette.append((r, g, b))
    return palette


class TestTilesToPNG:
    def test_single_tile(self):
        pal = _make_palette(4)
        tiles = [[0] * 64]
        fd, path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        try:
            tiles_to_png(tiles, pal, path, columns=1)
            from PIL import Image
            with Image.open(path) as img:
                assert img.mode == 'RGB'
                assert img.size == (8, 8)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_four_tiles_grid(self):
        pal = _make_palette(4)
        tiles = [[0] * 64, [1] * 64, [2] * 64, [3] * 64]
        fd, path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        try:
            tiles_to_png(tiles, pal, path, columns=2)
            from PIL import Image
            with Image.open(path) as img:
                assert img.size == (16, 16)
                px = img.load()
                assert px[0, 0] == pal[0]
                assert px[0, 8] == pal[2]
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_pixel_values_correct(self):
        pal = [(255, 0, 0), (0, 255, 0)]
        tile = [0] * 32 + [1] * 32
        fd, path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        try:
            tiles_to_png([tile], pal, path, columns=1, scale=1)
            from PIL import Image
            with Image.open(path) as img:
                px = img.load()
                assert px[0, 0] == (255, 0, 0)
                assert px[0, 4] == (0, 255, 0)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_out_of_range_index_renders_black(self):
        pal = [(255, 0, 0)]
        tile = [99] * 64
        fd, path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        try:
            tiles_to_png([tile], pal, path, columns=1)
            from PIL import Image
            with Image.open(path) as img:
                px = img.load()
                assert px[0, 0] == (0, 0, 0)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_empty_tiles(self):
        import pytest
        pal = _make_palette(4)
        with pytest.raises(ValueError, match='No tiles'):
            tiles_to_png([], pal, 'dummy.png')

    def test_empty_palette(self):
        import pytest
        tiles = [[0] * 64]
        with pytest.raises(ValueError, match='Palette required'):
            tiles_to_png(tiles, [], 'dummy.png')

    def test_scale_factor(self):
        pal = [(255, 0, 0)]
        tile = [0] * 64
        fd, path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        try:
            tiles_to_png([tile], pal, path, columns=1, scale=3)
            from PIL import Image
            with Image.open(path) as img:
                assert img.size == (24, 24)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_16_tiles_default_columns(self):
        pal = _make_palette(16)
        tiles = [[i % 16] * 64 for i in range(64)]
        fd, path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        try:
            tiles_to_png(tiles, pal, path, columns=16)
            from PIL import Image
            with Image.open(path) as img:
                assert img.size == (128, 32)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_roundtrip_with_real_parse(self):
        tiles_in = _make_synthetic_tiles(8, bpp=4)
        pal = _make_palette(4)
        encoded = _encode_bpp_tiles(tiles_in, bpp=4)
        tiles_out = parse_bpp_tiles(encoded, bpp=4)
        fd, path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        try:
            tiles_to_png(tiles_out, pal, path, columns=4)
            from PIL import Image
            with Image.open(path) as img:
                assert img.size == (32, 16)
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestPNGCLI:
    @property
    def _script(self):
        return os.path.join(
            os.path.dirname(_test_dir),
            'extract_assets', 'extract_bpp.py',
        )

    def _make_bpp_file(self, tiles=None, bpp=4):
        if tiles is None:
            tiles = _make_synthetic_tiles(16, bpp)
        data = _encode_bpp_tiles(tiles, bpp)
        fd, path = tempfile.mkstemp(suffix='.bin')
        os.write(fd, data)
        os.close(fd)
        return path

    def _make_palette_file(self, num_colors=16):
        data = bytes(num_colors * 2)
        fd, path = tempfile.mkstemp(suffix='.pal')
        os.write(fd, data)
        os.close(fd)
        return path

    def test_cli_png_export(self):
        bpp_path = self._make_bpp_file()
        pal_path = self._make_palette_file(16)
        png_fd, png_path = tempfile.mkstemp(suffix='.png')
        os.close(png_fd)
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, self._script,
                 '--input', bpp_path, '--bpp', '4',
                 '--palette', pal_path, '--pal-colors', '16',
                 '--png', png_path],
                capture_output=True, text=True,
            )
            assert result.returncode == 0, f'CLI failed: {result.stderr}'
            assert 'Saved' in result.stdout
            from PIL import Image
            with Image.open(png_path) as img:
                assert img.mode == 'RGB'
        finally:
            for p in [bpp_path, pal_path, png_path]:
                if os.path.exists(p):
                    os.unlink(p)

    def test_cli_png_with_columns_and_scale(self):
        bpp_path = self._make_bpp_file()
        pal_path = self._make_palette_file(16)
        png_fd, png_path = tempfile.mkstemp(suffix='.png')
        os.close(png_fd)
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, self._script,
                 '--input', bpp_path, '--bpp', '4',
                 '--palette', pal_path, '--pal-colors', '16',
                 '--png', png_path,
                 '--png-columns', '8',
                 '--png-scale', '2'],
                capture_output=True, text=True,
            )
            assert result.returncode == 0, f'CLI failed: {result.stderr}'
            from PIL import Image
            with Image.open(png_path) as img:
                assert img.size == (128, 32)
        finally:
            for p in [bpp_path, pal_path, png_path]:
                if os.path.exists(p):
                    os.unlink(p)

    def test_cli_png_requires_palette(self):
        bpp_path = self._make_bpp_file()
        png_fd, png_path = tempfile.mkstemp(suffix='.png')
        os.close(png_fd)
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, self._script,
                 '--input', bpp_path, '--bpp', '4',
                 '--png', png_path],
                capture_output=True, text=True,
            )
            assert result.returncode != 0
            assert 'palette' in result.stderr.lower()
        finally:
            for p in [bpp_path, png_path]:
                if os.path.exists(p):
                    os.unlink(p)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])
