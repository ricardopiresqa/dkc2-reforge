"""DKC2 Reforge — Asset extraction and ROM patching tools.

Provides:
- scan_rom(): Find all PAC1 headers in a ROM.
- extract_asset(): Extract a single asset (header + compressed + decompressed).
- extract_all(): Extract all valid assets.
- recompress_asset(): Re-compress decompressed data and fit into original space.
- parse_bpp_tiles(): Parse SNES BPP planar graphics into tiles.
- parse_palette(): Parse SNES RGB555 palette data.
- parse_brr(): Decode BRR compressed audio into PCM16 samples.
- brr_to_wav(): Export BRR samples as WAV file.
- find_brr_samples(): Scan data for candidate BRR sequences.
- detect_pac1_audio(): Scan PAC1 archives for BRR audio.
"""

from .extract_pac1 import scan_rom, extract_asset, extract_all, list_assets
from .patch_rom import recompress_asset, patch_rom
from .extract_bpp import parse_bpp_tiles, tile_count, tile_to_ascii, tile_to_pixels, tiles_to_grid, tiles_to_png
from .extract_palette import parse_palette, rgb555_to_rgb, palette_to_hex, palette_to_ascii
from .extract_tilemap import (
    parse_entry, encode_entry,
    parse_tilemap, parse_tilemap_blocks,
    tilemap_to_ascii, tilemap_to_ascii_simple,
    tilemap_to_png, tilemap_info,
)
from .extract_audio import parse_brr, brr_to_wav, find_brr_samples, detect_pac1_audio, brr_info

__all__ = [
    'scan_rom',
    'extract_asset',
    'extract_all',
    'list_assets',
    'recompress_asset',
    'patch_rom',
    'parse_bpp_tiles',
    'tile_count',
    'tile_to_ascii',
    'tile_to_pixels',
    'tiles_to_grid',
    'tiles_to_png',
    'parse_palette',
    'rgb555_to_rgb',
    'palette_to_hex',
    'palette_to_ascii',
    'parse_entry',
    'encode_entry',
    'parse_tilemap',
    'parse_tilemap_blocks',
    'tilemap_to_ascii',
    'tilemap_to_ascii_simple',
    'tilemap_to_png',
    'tilemap_info',
    'parse_brr',
    'brr_to_wav',
    'find_brr_samples',
    'detect_pac1_audio',
    'brr_info',
]
