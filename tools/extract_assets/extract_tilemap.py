"""SNES Tilemap Parsing.

Parses SNES standard tilemap format (2 bytes per entry) into a 2D grid of
tile references with palette, priority, and flip attributes.

SNES tilemap entry format (16-bit little-endian word):
  Bits 0-9:   Tile index (10 bits, 0-1023)
  Bits 10-12: Palette index (3 bits, 0-7)
  Bit 13:     Priority flag
  Bit 14:     Horizontal flip (X)
  Bit 15:     Vertical flip (Y)

Usage:
    # Show tilemap info
    python extract_tilemap.py --input tilemap.bin --width 32 --height 28 --info

    # Render tilemap as ASCII using tiles + palette
    python extract_tilemap.py --input tilemap.bin --width 32 --height 28 \
        --tiles gfx.bin --bpp 4 --palette pal.bin --ascii

    # Export tilemap as PNG
    python extract_tilemap.py --input tilemap.bin --width 32 --height 28 \
        --tiles gfx.bin --bpp 4 --palette pal.bin --png output.png --png-scale 2

    # Parse tilemap as 4x4 blocks (for animation refs)
    python extract_tilemap.py --input tilemap.bin --width 32 --height 28 \
        --block --block-w 4 --block-h 4 --info
"""

import argparse
import math
import os
import struct
import sys


# ── Constants ──────────────────────────────────────────────────────────────

TILE_SIZE = 8


# ── Entry Parsing ──────────────────────────────────────────────────────────

def parse_entry(word: int) -> dict:
    """Parse a single 16-bit SNES tilemap entry.

    Args:
        word: 16-bit little-endian tilemap entry value.

    Returns:
        Dict with keys: tile (int), palette (int),
                        priority (bool), hflip (bool), vflip (bool).
    """
    return {
        'tile': word & 0x03FF,
        'palette': (word >> 10) & 0x07,
        'priority': bool((word >> 13) & 1),
        'hflip': bool((word >> 14) & 1),
        'vflip': bool((word >> 15) & 1),
    }


def encode_entry(entry: dict) -> int:
    """Encode a tilemap entry dict back into a 16-bit word.

    Inverse of parse_entry. Intended for testing.

    Args:
        entry: Dict with tile, palette, priority, hflip, vflip keys.

    Returns:
        16-bit tilemap entry word.
    """
    word = entry['tile'] & 0x03FF
    word |= (entry['palette'] & 0x07) << 10
    if entry.get('priority'):
        word |= 1 << 13
    if entry.get('hflip'):
        word |= 1 << 14
    if entry.get('vflip'):
        word |= 1 << 15
    return word


# ── Tilemap Parsing ────────────────────────────────────────────────────────

def parse_tilemap(
    data: bytes,
    width_tiles: int,
    height_tiles: int,
) -> list[list[dict]]:
    """Parse raw tilemap data into a 2D grid of entry dicts.

    Args:
        data: Raw tilemap bytes (2 bytes per entry, little-endian).
        width_tiles: Number of tiles horizontally in the tilemap.
        height_tiles: Number of tiles vertically in the tilemap.

    Returns:
        2D list (height_tiles x width_tiles) of entry dicts.
        Entry dict keys: tile, palette, priority, hflip, vflip.

    Raises:
        ValueError: If data is too short for the given dimensions.
    """
    needed = width_tiles * height_tiles * 2
    if len(data) < needed:
        raise ValueError(
            f'Tilemap data too short: need {needed}B for '
            f'{width_tiles}x{height_tiles} entries, got {len(data)}B'
        )

    grid: list[list[dict]] = []
    for y in range(height_tiles):
        row: list[dict] = []
        for x in range(width_tiles):
            offset = (y * width_tiles + x) * 2
            word = struct.unpack_from('<H', data, offset)[0]
            row.append(parse_entry(word))
        grid.append(row)

    return grid


def parse_tilemap_blocks(
    data: bytes,
    block_width: int = 4,
    block_height: int = 4,
) -> list[list[list[list[dict]]]]:
    """Parse tilemap data into blocks of tiles.

    SNES tilemaps often group tiles into blocks (e.g. 4x4 tiles) for
    animation or metatile references. This function parses the flat
    entry array into blocks of the given size.

    Args:
        data: Raw tilemap bytes (flat array, row-major).
        block_width: Tiles per block horizontally (default: 4).
        block_height: Tiles per block vertically (default: 4).

    Returns:
        List of blocks. Each block is a 2D grid (block_height x block_width)
        of entry dicts. Blocks are in row-major order.
    """
    block_tiles = block_width * block_height
    total_entries = len(data) // 2
    num_blocks = total_entries // block_tiles

    blocks: list[list[list[dict]]] = []
    for b in range(num_blocks):
        base = b * block_tiles
        block: list[list[dict]] = []
        for by in range(block_height):
            row: list[dict] = []
            for bx in range(block_width):
                idx = base + by * block_width + bx
                word = struct.unpack_from('<H', data, idx * 2)[0]
                row.append(parse_entry(word))
            block.append(row)
        blocks.append(block)

    return blocks


# ── Rendering: ASCII ───────────────────────────────────────────────────────

def tilemap_to_ascii(
    tilemap: list[list[dict]],
    tiles: list[list[int]],
    palettes: list[list[tuple[int, int, int]]],
    bpp: int = 4,
) -> str:
    """Render tilemap as colored ASCII art.

    Each tile entry in the tilemap is rendered as an 8x8 ANSI-colored
    block grid, respecting the tile index, palette selection, and
    horizontal/vertical flip from the entry.

    Args:
        tilemap: 2D grid of entry dicts from parse_tilemap.
        tiles: List of tiles (each: list of 64 pixel values).
        palettes: List of palette lists. Each palette is list of (R,G,B).
                  The entry's 'palette' field indexes into this list.
        bpp: Bits per pixel (4 or 8, default: 4).

    Returns:
        Multi-line string with colored ASCII representation.
    """
    if not tilemap or not tiles:
        return '[Empty tilemap or no tiles]'

    height_tiles = len(tilemap)
    width_tiles = len(tilemap[0]) if tilemap else 0

    if width_tiles == 0:
        return '[Empty tilemap row]'

    output_lines: list[str] = []

    for entry_row_idx, entry_row in enumerate(tilemap):
        for tile_row in range(TILE_SIZE):
            line_parts: list[str] = []
            for entry in entry_row:
                tile_idx = entry['tile']
                pal_idx = entry['palette']
                hflip = entry['hflip']
                vflip = entry['vflip']

                if tile_idx >= len(tiles):
                    line_parts.append(' ' * TILE_SIZE)
                    continue

                tile = tiles[tile_idx]
                palette = []
                if pal_idx < len(palettes):
                    palette = palettes[pal_idx]

                src_row = (TILE_SIZE - 1 - tile_row) if vflip else tile_row

                for col in range(TILE_SIZE):
                    src_col = (TILE_SIZE - 1 - col) if hflip else col
                    pixel_val = tile[src_row * TILE_SIZE + src_col]

                    if 0 <= pixel_val < len(palette):
                        r, g, b = palette[pixel_val]
                        line_parts.append(f'\033[48;2;{r};{g};{b}m \033[0m')
                    else:
                        line_parts.append('?')

            output_lines.append(''.join(line_parts))

    return '\n'.join(output_lines)


def tilemap_to_ascii_simple(
    tilemap: list[list[dict]],
    bpp: int = 4,
) -> str:
    """Render tilemap as simple ASCII showing tile indices.

    Args:
        tilemap: 2D grid of entry dicts from parse_tilemap.
        bpp: Bits per pixel (4 or 8, affects hex width).

    Returns:
        Multi-line string showing tile indices in hex.
    """
    if not tilemap:
        return '[Empty tilemap]'

    hex_digits = 3  # 10 bits max = 0x3FF
    fmt = f'{{:0{hex_digits}X}}'
    output_lines: list[str] = []

    for entry_row in tilemap:
        parts = []
        for entry in entry_row:
            flags = ''
            if entry['hflip']:
                flags += 'H'
            if entry['vflip']:
                flags += 'V'
            if entry['priority']:
                flags += 'P'
            idx_str = fmt.format(entry['tile'])
            pal_str = str(entry['palette'])
            if flags:
                parts.append(f'{idx_str}(p{pal_str},{flags})')
            else:
                parts.append(f'{idx_str}(p{pal_str})')
        output_lines.append(' '.join(parts))

    return '\n'.join(output_lines)


# ── Rendering: PNG ─────────────────────────────────────────────────────────

def tilemap_to_png(
    tilemap: list[list[dict]],
    tiles: list[list[int]],
    palettes: list[list[tuple[int, int, int]]],
    output_path: str,
    scale: int = 1,
) -> None:
    """Render tilemap as a PNG image.

    Args:
        tilemap: 2D grid of entry dicts from parse_tilemap.
        tiles: List of tiles (each: list of 64 pixel values).
        palettes: List of palette lists. Entry's 'palette' field indexes.
        output_path: Path to save the PNG file.
        scale: Upscale factor per tile (1 = 8x8 px per tile, etc).

    Raises:
        ValueError: If tilemap, tiles, or palettes are empty.
        ImportError: If Pillow is not installed.
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError(
            'Pillow is required for PNG export. '
            'Install: pip install pillow'
        )

    if not tilemap or not tilemap[0]:
        raise ValueError('Tilemap is empty')
    if not tiles:
        raise ValueError('No tiles provided')
    if not palettes:
        raise ValueError('No palettes provided')

    height_tiles = len(tilemap)
    width_tiles = len(tilemap[0])
    tile_px = TILE_SIZE * scale

    img = Image.new(
        'RGB',
        (width_tiles * tile_px, height_tiles * tile_px),
    )
    pixels = img.load()

    for entry_row_idx, entry_row in enumerate(tilemap):
        for entry_col_idx, entry in enumerate(entry_row):
            tile_idx = entry['tile']
            pal_idx = entry['palette']
            hflip = entry['hflip']
            vflip = entry['vflip']

            if tile_idx >= len(tiles):
                continue

            tile = tiles[tile_idx]
            palette = []
            if pal_idx < len(palettes):
                palette = palettes[pal_idx]

            base_x = entry_col_idx * tile_px
            base_y = entry_row_idx * tile_px

            for py in range(TILE_SIZE):
                src_y = (TILE_SIZE - 1 - py) if vflip else py
                for px in range(TILE_SIZE):
                    src_x = (TILE_SIZE - 1 - px) if hflip else px
                    pixel_val = tile[src_y * TILE_SIZE + src_x]

                    if 0 <= pixel_val < len(palette):
                        color = palette[pixel_val]
                    else:
                        color = (0, 0, 0)

                    for sy in range(scale):
                        for sx in range(scale):
                            pixels[
                                base_x + px * scale + sx,
                                base_y + py * scale + sy,
                            ] = color

    img.save(output_path, 'PNG')


# ── Tilemap Info ───────────────────────────────────────────────────────────

def tilemap_info(tilemap: list[list[dict]]) -> str:
    """Return summary info about a parsed tilemap.

    Args:
        tilemap: 2D grid of entry dicts from parse_tilemap.

    Returns:
        Multi-line summary string.
    """
    if not tilemap or not tilemap[0]:
        return 'Empty tilemap'

    height_tiles = len(tilemap)
    width_tiles = len(tilemap[0])
    total_entries = width_tiles * height_tiles

    unique_tiles = set()
    palettes_used = set()
    hflip_count = 0
    vflip_count = 0
    priority_count = 0

    for row in tilemap:
        for entry in row:
            unique_tiles.add(entry['tile'])
            palettes_used.add(entry['palette'])
            if entry['hflip']:
                hflip_count += 1
            if entry['vflip']:
                vflip_count += 1
            if entry['priority']:
                priority_count += 1

    return (
        f'Dimensions: {width_tiles}x{height_tiles} tiles'
        f'  ({width_tiles * TILE_SIZE}x{height_tiles * TILE_SIZE} px)\n'
        f'Entries:    {total_entries}\n'
        f'Unique tiles: {len(unique_tiles)}\n'
        f'Palettes:   {len(palettes_used)} used ({sorted(palettes_used)})\n'
        f'Flips:      H={hflip_count}, V={vflip_count}\n'
        f'Priority:   {priority_count} entries'
    )


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='DKC2 SNES Tilemap Extractor')

    parser.add_argument('--input', '-i', required=True,
                        help='Raw tilemap data file')
    parser.add_argument('--offset', type=lambda x: int(x, 16),
                        default=0,
                        help='Byte offset into input file (hex)')
    parser.add_argument('--length', type=int,
                        help='Number of bytes to read (default: entire file)')

    parser.add_argument('--width', type=int, required=True,
                        help='Tilemap width in tiles')
    parser.add_argument('--height', type=int, required=True,
                        help='Tilemap height in tiles')

    parser.add_argument('--tiles', type=str, default=None,
                        help='BPP file with tile graphics')
    parser.add_argument('--bpp', type=int, default=4, choices=[4, 8],
                        help='Bits per pixel for tile graphics (default: 4)')

    parser.add_argument('--palette', type=str, default=None,
                        help='Palette file')
    parser.add_argument('--pal-offset', type=lambda x: int(x, 16),
                        default=0,
                        help='Palette offset (hex)')
    parser.add_argument('--pal-colors', type=int, default=16,
                        help='Number of palette colors per palette (default: 16)')
    parser.add_argument('--pal-count', type=int, default=1,
                        help='Number of palettes in file (default: 1)')

    parser.add_argument('--info', action='store_true',
                        help='Show tilemap info')
    parser.add_argument('--ascii', action='store_true',
                        help='Render tilemap as ASCII art')
    parser.add_argument('--simple', action='store_true',
                        help='Render tilemap as simple ASCII (tile indices)')

    parser.add_argument('--png', type=str, default=None, metavar='PATH',
                        help='Export tilemap as PNG image')
    parser.add_argument('--png-scale', type=int, default=1,
                        help='Scale factor per tile (default: 1)')

    parser.add_argument('--block', action='store_true',
                        help='Parse tilemap as blocks')
    parser.add_argument('--block-w', type=int, default=4,
                        help='Block width in tiles (default: 4)')
    parser.add_argument('--block-h', type=int, default=4,
                        help='Block height in tiles (default: 4)')

    args = parser.parse_args()

    # Read tilemap data
    with open(args.input, 'rb') as f:
        data = f.read()

    offset = args.offset or 0
    if offset > 0 or args.length is not None:
        length = args.length or (len(data) - offset)
        data = data[offset:offset + length]

    width = args.width
    height = args.height

    # Load tiles if requested
    tiles = None
    if args.tiles:
        try:
            from extract_assets.extract_bpp import parse_bpp_tiles
        except ImportError:
            _tools_dir = os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))
            if _tools_dir not in sys.path:
                sys.path.insert(0, _tools_dir)
            from extract_assets.extract_bpp import parse_bpp_tiles
        try:
            with open(args.tiles, 'rb') as f:
                tile_data = f.read()
            tiles = parse_bpp_tiles(tile_data, args.bpp)
            print(f'Loaded {len(tiles)} tiles from {args.tiles}',
                  file=sys.stderr)
        except Exception as e:
            print(f'Warning: tile load failed: {e}', file=sys.stderr)

    # Load palettes if requested
    palettes = None
    if args.palette:
        try:
            from extract_assets.extract_palette import parse_palette
        except ImportError:
            _tools_dir = os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))
            if _tools_dir not in sys.path:
                sys.path.insert(0, _tools_dir)
            from extract_assets.extract_palette import parse_palette
        try:
            with open(args.palette, 'rb') as f:
                pal_data = f.read()
            palettes = []
            for i in range(args.pal_count):
                off = args.pal_offset + i * args.pal_colors * 2
                pal = parse_palette(
                    pal_data, offset=off, num_colors=args.pal_colors,
                )
                palettes.append(pal)
            print(f'Loaded {len(palettes)} palette(s) from {args.palette}',
                  file=sys.stderr)
        except Exception as e:
            print(f'Warning: palette load failed: {e}', file=sys.stderr)

    # ── Block mode ─────────────────────────────────────────────────────
    if args.block:
        blocks = parse_tilemap_blocks(
            data, block_width=args.block_w, block_height=args.block_h,
        )
        print(f'Blocks: {len(blocks)} ({args.block_w}x{args.block_h} tiles each)')
        if args.info:
            print(f'  Total entries: {len(blocks) * args.block_w * args.block_h}')
        return

    # Parse tilemap
    try:
        tilemap = parse_tilemap(data, width, height)
    except ValueError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)

    # ── Info ────────────────────────────────────────────────────────────
    if args.info:
        print(tilemap_info(tilemap))

    # ── ASCII ───────────────────────────────────────────────────────────
    if args.ascii:
        if tiles is not None and palettes is not None:
            print(tilemap_to_ascii(tilemap, tiles, palettes, args.bpp))
        else:
            print('Warning: --ascii requires --tiles and --palette',
                  file=sys.stderr)
            print(tilemap_to_ascii_simple(tilemap, args.bpp))

    if args.simple:
        print(tilemap_to_ascii_simple(tilemap, args.bpp))

    # ── PNG ─────────────────────────────────────────────────────────────
    if args.png:
        if tiles is None or palettes is None:
            print('Error: --tiles and --palette required for --png export',
                  file=sys.stderr)
            sys.exit(1)
        try:
            tilemap_to_png(
                tilemap, tiles, palettes,
                args.png, scale=args.png_scale,
            )
            w_px = width * TILE_SIZE * args.png_scale
            h_px = height * TILE_SIZE * args.png_scale
            print(f'Saved tilemap to {args.png} ({width}x{height} tiles, '
                  f'{w_px}x{h_px} px'
                  f'{", scale=" + str(args.png_scale) if args.png_scale > 1 else ""})')
        except (ValueError, ImportError) as e:
            print(f'PNG export failed: {e}', file=sys.stderr)
            sys.exit(1)

    # Default: show info if no output flag
    if not (args.info or args.ascii or args.simple or args.png):
        print(tilemap_info(tilemap))


if __name__ == '__main__':
    main()
