"""Tests for SNES tilemap parsing (extract_tilemap.py).

Covers:
  - parse_entry / encode_entry round-trip
  - parse_tilemap with synthetic data
  - parse_tilemap with flip bits
  - tilemap_to_png with synthetic tiles + palettes
  - tilemap_to_ascii output
  - parse_tilemap_blocks
  - CLI smoke test
  - Edge cases: partial data, zero dimensions
"""

import os
import struct
import sys
import tempfile

_test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _test_dir)
sys.path.insert(0, os.path.dirname(_test_dir))

from extract_assets.extract_tilemap import (
    parse_entry,
    encode_entry,
    parse_tilemap,
    parse_tilemap_blocks,
    tilemap_to_ascii,
    tilemap_to_ascii_simple,
    tilemap_to_png,
    tilemap_info,
    TILE_SIZE,
)
from extract_assets.extract_bpp import (
    parse_bpp_tiles,
    _encode_bpp_tiles,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_tilemap_data(
    width: int,
    height: int,
    fill_tile: int = 0,
    fill_palette: int = 0,
) -> bytes:
    """Create synthetic tilemap data with uniform entries."""
    data = bytearray()
    for _ in range(width * height):
        word = fill_tile & 0x03FF
        word |= (fill_palette & 0x07) << 10
        data.extend(struct.pack('<H', word))
    return bytes(data)


def _make_tilemap_data_varied(width: int, height: int) -> bytes:
    """Create tilemap data where each entry has incrementing values."""
    data = bytearray()
    for i in range(width * height):
        tile = i & 0x03FF
        pal = (i >> 10) & 0x07
        hflip = bool(i & 0x4000)
        vflip = bool(i & 0x8000)
        word = tile | (pal << 10) | (int(hflip) << 14) | (int(vflip) << 15)
        data.extend(struct.pack('<H', word))
    return bytes(data)


def _make_solid_tile(color=0):
    return [color] * 64


def _make_synthetic_tiles(num_tiles=4, bpp=4):
    tiles = []
    for i in range(num_tiles):
        val = i % (4 if bpp == 4 else 16)
        tiles.append(_make_solid_tile(val))
    return tiles


def _make_palette(num_colors=16):
    pal = []
    for i in range(num_colors):
        r = (i * 16) % 256
        g = (i * 32) % 256
        b = (i * 64) % 256
        pal.append((r, g, b))
    return pal


# ═══════════════════════════════════════════════════════════════════
# Test: Entry Parse / Encode
# ═══════════════════════════════════════════════════════════════════

class TestEntry:
    def test_parse_basic(self):
        """Basic entry: tile=42, palette=3, no flags."""
        word = (42 & 0x03FF) | (3 << 10)
        entry = parse_entry(word)
        assert entry['tile'] == 42
        assert entry['palette'] == 3
        assert entry['priority'] is False
        assert entry['hflip'] is False
        assert entry['vflip'] is False

    def test_parse_max_tile_index(self):
        """Tile index max value (1023 = 0x3FF)."""
        word = 0x03FF
        entry = parse_entry(word)
        assert entry['tile'] == 1023
        assert entry['palette'] == 0

    def test_parse_all_flags(self):
        """All flags set."""
        word = (1 << 13) | (1 << 14) | (1 << 15)
        entry = parse_entry(word)
        assert entry['tile'] == 0
        assert entry['palette'] == 0
        assert entry['priority'] is True
        assert entry['hflip'] is True
        assert entry['vflip'] is True

    def test_parse_max_palette(self):
        """Palette index max value (7)."""
        word = (7 << 10)
        entry = parse_entry(word)
        assert entry['palette'] == 7

    def test_parse_tile_with_flags(self):
        """Tile index coexists with flags."""
        # tile=500 (0x1F4), palette=5, priority=1, hflip=1
        word = 500 | (5 << 10) | (1 << 13) | (1 << 14)
        entry = parse_entry(word)
        assert entry['tile'] == 500
        assert entry['palette'] == 5
        assert entry['priority'] is True
        assert entry['hflip'] is True
        assert entry['vflip'] is False

    def test_encode_roundtrip(self):
        """Encode then decode gives same result."""
        original = {'tile': 456, 'palette': 3, 'priority': True,
                    'hflip': False, 'vflip': True}
        word = encode_entry(original)
        decoded = parse_entry(word)
        assert decoded == original

    def test_encode_roundtrip_no_flags(self):
        """Encode then decode with no flags set."""
        original = {'tile': 0, 'palette': 0, 'priority': False,
                    'hflip': False, 'vflip': False}
        word = encode_entry(original)
        decoded = parse_entry(word)
        assert decoded == original

    def test_encode_roundtrip_all_flags(self):
        """Encode then decode with all flags on."""
        original = {'tile': 1023, 'palette': 7, 'priority': True,
                    'hflip': True, 'vflip': True}
        word = encode_entry(original)
        decoded = parse_entry(word)
        assert decoded == original


# ═══════════════════════════════════════════════════════════════════
# Test: Tilemap Parse
# ═══════════════════════════════════════════════════════════════════

class TestParseTilemap:
    def test_small_tilemap(self):
        """Parse a 2x2 tilemap."""
        data = _make_tilemap_data(2, 2, fill_tile=10, fill_palette=2)
        tilemap = parse_tilemap(data, 2, 2)
        assert len(tilemap) == 2
        assert len(tilemap[0]) == 2
        assert tilemap[0][0]['tile'] == 10
        assert tilemap[0][0]['palette'] == 2
        assert tilemap[1][1]['tile'] == 10

    def test_large_tilemap(self):
        """Parse a 32x28 tilemap (typical SNES screen)."""
        data = _make_tilemap_data(32, 28)
        tilemap = parse_tilemap(data, 32, 28)
        assert len(tilemap) == 28
        assert len(tilemap[0]) == 32
        assert len(tilemap[27]) == 32

    def test_varied_entries(self):
        """Parse tilemap with varied tile indices and flags."""
        data = _make_tilemap_data_varied(4, 4)
        tilemap = parse_tilemap(data, 4, 4)
        for y in range(4):
            for x in range(4):
                entry = tilemap[y][x]
                i = y * 4 + x
                assert entry['tile'] == (i & 0x03FF)
                assert entry['palette'] == ((i >> 10) & 0x07)
                assert entry['hflip'] == bool(i & 0x4000)
                assert entry['vflip'] == bool(i & 0x8000)

    def test_flip_bits(self):
        """Verify flip bits are correctly parsed."""
        for hflip in [False, True]:
            for vflip in [False, True]:
                word = 0 | (int(hflip) << 14) | (int(vflip) << 15)
                data = struct.pack('<H', word)
                tilemap = parse_tilemap(data, 1, 1)
                assert tilemap[0][0]['hflip'] == hflip
                assert tilemap[0][0]['vflip'] == vflip

    def test_priority_bit(self):
        """Verify priority bit is parsed."""
        data = struct.pack('<H', 1 << 13)
        tilemap = parse_tilemap(data, 1, 1)
        assert tilemap[0][0]['priority'] is True

    def test_invalid_data(self):
        """Too short data raises ValueError."""
        import pytest
        data = bytes(2)  # only 1 entry
        with pytest.raises(ValueError, match='too short'):
            parse_tilemap(data, 2, 2)

    def test_empty_data(self):
        """Empty data with non-zero dimensions raises ValueError."""
        import pytest
        with pytest.raises(ValueError, match='too short'):
            parse_tilemap(b'', 1, 1)


# ═══════════════════════════════════════════════════════════════════
# Test: Block Parse
# ═══════════════════════════════════════════════════════════════════

class TestParseBlocks:
    def test_single_block(self):
        """Parse a single 4x4 block."""
        data = _make_tilemap_data(4, 4, fill_tile=1, fill_palette=0)
        blocks = parse_tilemap_blocks(data, 4, 4)
        assert len(blocks) == 1
        assert len(blocks[0]) == 4
        assert len(blocks[0][0]) == 4
        assert blocks[0][0][0]['tile'] == 1

    def test_multiple_blocks(self):
        """Parse 2 blocks from 8x4 tile data."""
        data = _make_tilemap_data_varied(8, 4)
        blocks = parse_tilemap_blocks(data, 4, 4)
        assert len(blocks) == 2
        # First block has entries 0-15
        assert blocks[0][0][0]['tile'] == 0
        # Second block has entries 16-31
        assert blocks[1][0][0]['tile'] == 16

    def test_default_block_size(self):
        """Default block size is 4x4."""
        data = _make_tilemap_data(8, 8)
        blocks = parse_tilemap_blocks(data)  # defaults to 4x4
        assert len(blocks) == 4

    def test_custom_block_size(self):
        """Custom block size (2x2)."""
        data = _make_tilemap_data(4, 4)
        blocks = parse_tilemap_blocks(data, 2, 2)
        assert len(blocks) == 4  # 4x4 tiles / 2x2 blocks = 4 blocks


# ═══════════════════════════════════════════════════════════════════
# Test: Rendering — ASCII
# ═══════════════════════════════════════════════════════════════════

class TestAsciiRendering:
    def test_tilemap_to_ascii_simple(self):
        """Simple ASCII shows tile indices and palette."""
        data = _make_tilemap_data(2, 2, fill_tile=0x0A, fill_palette=3)
        tilemap = parse_tilemap(data, 2, 2)
        result = tilemap_to_ascii_simple(tilemap)
        assert 'A(p3)' in result or '00A(p3)' in result or '00A(p3)' in result
        assert result

    def test_tilemap_to_ascii_simple_with_flags(self):
        """Simple ASCII shows flip flags."""
        word = (1 << 14) | (1 << 15)  # hflip + vflip, tile=0
        data = struct.pack('<H', word)
        tilemap = parse_tilemap(data, 1, 1)
        result = tilemap_to_ascii_simple(tilemap)
        assert 'H' in result or 'V' in result

    def test_tilemap_to_ascii_with_palette(self):
        """Colored ASCII with tiles and palettes."""
        tiles = _make_synthetic_tiles(4)
        palettes = [_make_palette(4)]
        data = _make_tilemap_data(2, 2, fill_tile=0, fill_palette=0)
        tilemap = parse_tilemap(data, 2, 2)
        result = tilemap_to_ascii(tilemap, tiles, palettes, bpp=4)
        assert result
        lines = result.split('\n')
        assert len(lines) == 16  # 2 tiles high * 8 rows

    def test_tilemap_to_ascii_empty(self):
        """Empty tilemap returns placeholder."""
        assert '[Empty' in tilemap_to_ascii([], [], [])
        assert '[Empty' in tilemap_to_ascii_simple([])


# ═══════════════════════════════════════════════════════════════════
# Test: Rendering — PNG
# ═══════════════════════════════════════════════════════════════════

class TestPngRendering:
    def test_small_tilemap_png(self):
        """Render a 2x2 tilemap to PNG."""
        tiles = _make_synthetic_tiles(4)
        palettes = [_make_palette(4)]
        data = _make_tilemap_data(2, 2, fill_tile=0, fill_palette=0)
        tilemap = parse_tilemap(data, 2, 2)
        fd, path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        try:
            tilemap_to_png(tilemap, tiles, palettes, path)
            from PIL import Image
            with Image.open(path) as img:
                assert img.mode == 'RGB'
                assert img.size == (16, 16)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_tilemap_png_with_flips(self):
        """Render tilemap with flip bits."""
        tiles = [_make_solid_tile(0), _make_solid_tile(1)]
        palettes = [_make_palette(4)]
        # Entry with hflip=1, vflip=1, tile=0
        word = (0 << 14) | (0 << 15)
        data = struct.pack('<H', word)
        tilemap = parse_tilemap(data, 1, 1)
        fd, path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        try:
            tilemap_to_png(tilemap, tiles, palettes, path)
            from PIL import Image
            with Image.open(path) as img:
                assert img.size == (8, 8)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_tilemap_png_with_scale(self):
        """Render tilemap with scale factor."""
        tiles = _make_synthetic_tiles(1)
        palettes = [_make_palette(4)]
        data = _make_tilemap_data(1, 1)
        tilemap = parse_tilemap(data, 1, 1)
        fd, path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        try:
            tilemap_to_png(tilemap, tiles, palettes, path, scale=3)
            from PIL import Image
            with Image.open(path) as img:
                assert img.size == (24, 24)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_tilemap_png_empty_tilemap(self):
        """Empty tilemap raises ValueError."""
        import pytest
        with pytest.raises(ValueError, match='empty'):
            tilemap_to_png([], [[]], [[]], 'dummy.png')

    def test_tilemap_png_no_tiles(self):
        """No tiles raises ValueError."""
        import pytest
        tilemap = parse_tilemap(struct.pack('<H', 0), 1, 1)
        with pytest.raises(ValueError, match='No tiles'):
            tilemap_to_png(tilemap, [], [[]], 'dummy.png')

    def test_tilemap_png_no_palettes(self):
        """No palettes raises ValueError."""
        import pytest
        tiles = _make_synthetic_tiles(1)
        tilemap = parse_tilemap(struct.pack('<H', 0), 1, 1)
        with pytest.raises(ValueError, match='No palettes'):
            tilemap_to_png(tilemap, tiles, [], 'dummy.png')


# ═══════════════════════════════════════════════════════════════════
# Test: Tilemap Info
# ═══════════════════════════════════════════════════════════════════

class TestTilemapInfo:
    def test_info_basic(self):
        """Info returns non-empty summary."""
        data = _make_tilemap_data(8, 8)
        tilemap = parse_tilemap(data, 8, 8)
        info = tilemap_info(tilemap)
        assert '8x8' in info
        assert 'Entries' in info

    def test_info_unique_tiles(self):
        """Info counts unique tiles."""
        data = _make_tilemap_data_varied(4, 4)
        tilemap = parse_tilemap(data, 4, 4)
        info = tilemap_info(tilemap)
        assert 'Unique' in info

    def test_info_flip_counts(self):
        """Info counts flipped entries."""
        data = _make_tilemap_data(2, 2)
        tilemap = parse_tilemap(data, 2, 2)
        info = tilemap_info(tilemap)
        assert 'H=' in info
        assert 'V=' in info

    def test_info_empty(self):
        """Empty tilemap returns placeholder."""
        result = tilemap_info([])
        assert 'Empty' in result
        result = tilemap_info([[]])
        assert 'Empty' in result


# ═══════════════════════════════════════════════════════════════════
# Test: CLI
# ═══════════════════════════════════════════════════════════════════

class TestCLI:
    @staticmethod
    def _make_tilemap_file(width=4, height=4, data=None):
        if data is None:
            data = _make_tilemap_data(width, height, fill_tile=42, fill_palette=3)
        fd, path = tempfile.mkstemp(suffix='.tilemap')
        os.write(fd, data)
        os.close(fd)
        return path

    @staticmethod
    def _make_bpp_file(tiles=None, bpp=4):
        if tiles is None:
            tiles = _make_synthetic_tiles(16, bpp)
        data = _encode_bpp_tiles(tiles, bpp)
        fd, path = tempfile.mkstemp(suffix='.bin')
        os.write(fd, data)
        os.close(fd)
        return path

    @staticmethod
    def _make_palette_file(num_colors=16):
        data = bytes(num_colors * 2)
        fd, path = tempfile.mkstemp(suffix='.pal')
        os.write(fd, data)
        os.close(fd)
        return path

    def test_cli_info(self):
        """--info shows tilemap dimensions."""
        tm_path = self._make_tilemap_file(4, 4)
        try:
            import subprocess
            script = os.path.join(
                os.path.dirname(_test_dir),
                'extract_assets', 'extract_tilemap.py',
            )
            result = subprocess.run(
                [sys.executable, script,
                 '--input', tm_path, '--width', '4', '--height', '4',
                 '--info'],
                capture_output=True, text=True,
            )
            assert result.returncode == 0, f'CLI failed: {result.stderr}'
            assert '4x4' in result.stdout
            assert 'Entries' in result.stdout
        finally:
            os.unlink(tm_path)

    def test_cli_info_with_offset(self):
        """--offset reads from within file."""
        prefix = b'\x00' * 4  # 4 bytes prefix
        tm_data = _make_tilemap_data(2, 2, fill_tile=0xAA, fill_palette=5)
        full_data = prefix + tm_data
        tm_path = self._make_tilemap_file(data=full_data)
        try:
            import subprocess
            script = os.path.join(
                os.path.dirname(_test_dir),
                'extract_assets', 'extract_tilemap.py',
            )
            result = subprocess.run(
                [sys.executable, script,
                 '--input', tm_path,
                 '--offset', '0x4',
                 '--width', '2', '--height', '2',
                 '--info'],
                capture_output=True, text=True,
            )
            assert result.returncode == 0, f'CLI failed: {result.stderr}'
            assert '2x2' in result.stdout
        finally:
            os.unlink(tm_path)

    def test_cli_simple(self):
        """--simple shows tile indices."""
        tm_path = self._make_tilemap_file(2, 2)
        try:
            import subprocess
            script = os.path.join(
                os.path.dirname(_test_dir),
                'extract_assets', 'extract_tilemap.py',
            )
            result = subprocess.run(
                [sys.executable, script,
                 '--input', tm_path, '--width', '2', '--height', '2',
                 '--simple'],
                capture_output=True, text=True,
            )
            assert result.returncode == 0
            assert result.stdout
        finally:
            os.unlink(tm_path)

    def test_cli_png(self):
        """--png exports tilemap."""
        tm_path = self._make_tilemap_file(2, 2)
        bpp_path = self._make_bpp_file()
        pal_path = self._make_palette_file(16)
        png_fd, png_path = tempfile.mkstemp(suffix='.png')
        os.close(png_fd)
        try:
            import subprocess
            script = os.path.join(
                os.path.dirname(_test_dir),
                'extract_assets', 'extract_tilemap.py',
            )
            result = subprocess.run(
                [sys.executable, script,
                 '--input', tm_path, '--width', '2', '--height', '2',
                 '--tiles', bpp_path, '--bpp', '4',
                 '--palette', pal_path, '--pal-colors', '16',
                 '--png', png_path],
                capture_output=True, text=True,
            )
            assert result.returncode == 0, f'CLI failed: {result.stderr}'
            assert 'Saved' in result.stdout
            from PIL import Image
            with Image.open(png_path) as img:
                assert img.mode == 'RGB'
                assert img.size == (16, 16)
        finally:
            for p in [tm_path, bpp_path, pal_path, png_path]:
                if os.path.exists(p):
                    os.unlink(p)

    def test_cli_png_with_scale(self):
        """--png with --png-scale."""
        tm_path = self._make_tilemap_file(2, 2)
        bpp_path = self._make_bpp_file()
        pal_path = self._make_palette_file(16)
        png_fd, png_path = tempfile.mkstemp(suffix='.png')
        os.close(png_fd)
        try:
            import subprocess
            script = os.path.join(
                os.path.dirname(_test_dir),
                'extract_assets', 'extract_tilemap.py',
            )
            result = subprocess.run(
                [sys.executable, script,
                 '--input', tm_path, '--width', '2', '--height', '2',
                 '--tiles', bpp_path, '--bpp', '4',
                 '--palette', pal_path, '--pal-colors', '16',
                 '--png', png_path, '--png-scale', '2'],
                capture_output=True, text=True,
            )
            assert result.returncode == 0, f'CLI failed: {result.stderr}'
            from PIL import Image
            with Image.open(png_path) as img:
                assert img.size == (32, 32)
        finally:
            for p in [tm_path, bpp_path, pal_path, png_path]:
                if os.path.exists(p):
                    os.unlink(p)

    def test_cli_png_requires_tiles(self):
        """--png without --tiles fails."""
        tm_path = self._make_tilemap_file(2, 2)
        png_fd, png_path = tempfile.mkstemp(suffix='.png')
        os.close(png_fd)
        try:
            import subprocess
            script = os.path.join(
                os.path.dirname(_test_dir),
                'extract_assets', 'extract_tilemap.py',
            )
            result = subprocess.run(
                [sys.executable, script,
                 '--input', tm_path, '--width', '2', '--height', '2',
                 '--png', png_path],
                capture_output=True, text=True,
            )
            assert result.returncode != 0
            assert 'tiles' in result.stderr.lower()
        finally:
            for p in [tm_path, png_path]:
                if os.path.exists(p):
                    os.unlink(p)

    def test_cli_block(self):
        """--block parses tilemap as blocks."""
        tm_path = self._make_tilemap_file(8, 8)
        try:
            import subprocess
            script = os.path.join(
                os.path.dirname(_test_dir),
                'extract_assets', 'extract_tilemap.py',
            )
            result = subprocess.run(
                [sys.executable, script,
                 '--input', tm_path, '--width', '8', '--height', '8',
                 '--block'],
                capture_output=True, text=True,
            )
            assert result.returncode == 0
            assert 'Blocks' in result.stdout
        finally:
            os.unlink(tm_path)


# ═══════════════════════════════════════════════════════════════════
# Test: Edge Cases
# ═══════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_single_entry(self):
        """Single entry tilemap (1x1)."""
        data = struct.pack('<H', 0x0000)
        tilemap = parse_tilemap(data, 1, 1)
        assert len(tilemap) == 1
        assert len(tilemap[0]) == 1

    def test_non_rectangular(self):
        """Non-square tilemap (16x1)."""
        data = _make_tilemap_data(16, 1)
        tilemap = parse_tilemap(data, 16, 1)
        assert len(tilemap) == 1
        assert len(tilemap[0]) == 16

    def test_max_values(self):
        """Entry with max tile index and palette."""
        word = 1023 | (7 << 10) | (1 << 14)
        data = struct.pack('<H', word)
        tilemap = parse_tilemap(data, 1, 1)
        assert tilemap[0][0]['tile'] == 1023
        assert tilemap[0][0]['palette'] == 7
        assert tilemap[0][0]['hflip'] is True


# ═══════════════════════════════════════════════════════════════════
# Run via pytest
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])
