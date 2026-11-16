"""SNES BPP Planar Graphics Extraction.

Parses SNES standard bit-planar (BPP) graphics data into 8x8 pixel tiles.
Supports 4-bit (16-color) and 8-bit (256-color) planar formats.

4bpp planar (16 bytes per 8x8 tile):
  8 rows × 2 bytes per row (bitplane 0, bitplane 1)
  Pixel = (bp1 << 1) | bp0

8bpp planar (32 bytes per 8x8 tile):
  8 rows × 4 bytes per row (bitplane 0..3)
  Pixel = (bp3 << 3) | (bp2 << 2) | (bp1 << 1) | bp0

Tile order: sequential in file (tile 0, tile 1, tile 2, ...)

Usage:
    # Show tile info
    python extract_bpp.py --input decompressed.bin --bpp 4 --info

    # Show tile 0 as ASCII art
    python extract_bpp.py --input decompressed.bin --bpp 4 --tile 0 --ascii

    # Show tile range as grid
    python extract_bpp.py --input decompressed.bin --bpp 4 --tiles 0-15 --grid 4

    # Dump raw pixel values for tile 0
    python extract_bpp.py --input decompressed.bin --bpp 4 --tile 0 --dump

    # Show tile with palette colors
    python extract_bpp.py --input decompressed.bin --bpp 4 --tile 0 --ascii \
        --palette palette.bin --pal-colors 16
"""

import argparse
import os
import sys


# ── Constants ──────────────────────────────────────────────────────────────

TILE_SIZE = 8  # 8x8 pixels per tile

# Bytes per tile per BPP mode
BPP_TILE_BYTES = {
    4: 16,  # 8 rows × 2 bitplanes
    8: 32,  # 8 rows × 4 bitplanes
}

# Bitplanes per BPP mode
BPP_PLANES = {
    4: 2,
    8: 4,
}


# ── BPP Parsing ────────────────────────────────────────────────────────────

def _check_bpp(bpp: int) -> None:
    """Validate BPP value."""
    if bpp not in (4, 8):
        raise ValueError(f'Unsupported BPP: {bpp}, must be 4 or 8')


def tile_count(data: bytes, bpp: int = 4) -> int:
    """Return the number of complete 8x8 tiles in the data.

    Args:
        data: Raw BPP planar graphics data.
        bpp: Bits per pixel (4 or 8).

    Returns:
        Number of complete tiles.
    """
    _check_bpp(bpp)
    bytes_per_tile = BPP_TILE_BYTES[bpp]
    return len(data) // bytes_per_tile


def parse_bpp_tiles(data: bytes, bpp: int = 4) -> list[list[int]]:
    """Parse BPP planar graphics data into 8x8 pixel tiles.

    Args:
        data: Raw BPP data (after PAC1 decompression).
        bpp: Bits per pixel (4 or 8).

    Returns:
        List of tiles. Each tile is a list of 64 pixel values:
        - 4bpp: 0-15
        - 8bpp: 0-255
        Values are row-major (row 0 left to right, row 1, ...).

    Raises:
        ValueError: If BPP is not 4 or 8.
    """
    _check_bpp(bpp)
    bytes_per_tile = BPP_TILE_BYTES[bpp]
    planes = BPP_PLANES[bpp]

    num_tiles = tile_count(data, bpp)
    tiles = []

    for t in range(num_tiles):
        tile_start = t * bytes_per_tile
        tile_data = data[tile_start:tile_start + bytes_per_tile]
        tile = [0] * 64

        for row in range(TILE_SIZE):
            for col in range(TILE_SIZE):
                pixel = 0
                for plane in range(planes):
                    byte_idx = row * planes + plane
                    bit = (tile_data[byte_idx] >> (7 - col)) & 1
                    pixel |= bit << plane
                tile[row * TILE_SIZE + col] = pixel

        tiles.append(tile)

    return tiles


# ── BPP Encoding (for round-trip testing) ──────────────────────────────────

def _encode_bpp_tiles(tiles: list[list[int]], bpp: int = 4) -> bytes:
    """Encode pixel tiles back into BPP planar format.

    This is the inverse of parse_bpp_tiles. Intended for testing.

    Args:
        tiles: List of tiles, each a list of 64 pixel values.
        bpp: Bits per pixel (4 or 8).

    Returns:
        BPP planar encoded bytes.

    Raises:
        ValueError: If BPP is not 4 or 8, or tile data is invalid.
    """
    _check_bpp(bpp)
    bytes_per_tile = BPP_TILE_BYTES[bpp]
    planes = BPP_PLANES[bpp]
    result = bytearray()

    for tile in tiles:
        if len(tile) != 64:
            raise ValueError(f'Tile has {len(tile)} pixels, expected 64')
        tile_data = bytearray(bytes_per_tile)

        for row in range(TILE_SIZE):
            for col in range(TILE_SIZE):
                pixel = tile[row * TILE_SIZE + col]
                for plane in range(planes):
                    if pixel & (1 << plane):
                        byte_idx = row * planes + plane
                        tile_data[byte_idx] |= 1 << (7 - col)

        result.extend(tile_data)

    return bytes(result)


# ── Rendering ──────────────────────────────────────────────────────────────

def tiles_to_png(
    tiles: list[list[int]],
    palette: list[tuple[int, int, int]],
    output_path: str,
    columns: int = 16,
    scale: int = 1,
) -> None:
    """Render tiles to a PNG image file.

    Each tile is an 8x8 grid of palette indices. The resulting image is an
    RGB PNG with tiles arranged in a grid (row-major).

    Args:
        tiles: List of tiles (each: list of 64 pixel values / palette indices).
        palette: List of (R, G, B) tuples.
        output_path: Path to save the PNG file.
        columns: Number of tiles per row in the output grid (default: 16).
        scale: Upscale factor per tile (1 = 8x8 px per tile, 2 = 16x16, etc).

    Raises:
        ValueError: If tiles or palette is empty, or tile size is invalid.
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError(
            'Pillow is required for PNG export. '
            'Install: pip install pillow'
        )

    if not tiles:
        raise ValueError('No tiles to render')
    if not palette:
        raise ValueError('Palette required for PNG export')

    tile_px = TILE_SIZE * scale
    num_tiles = len(tiles)
    rows = (num_tiles + columns - 1) // columns
    img = Image.new('RGB', (columns * tile_px, rows * tile_px))
    pixels = img.load()

    for tile_idx, tile in enumerate(tiles):
        if len(tile) != 64:
            raise ValueError(
                f'Tile {tile_idx} has {len(tile)} pixels, expected 64'
            )
        grid_x = tile_idx % columns
        grid_y = tile_idx // columns
        base_x = grid_x * tile_px
        base_y = grid_y * tile_px

        for py in range(TILE_SIZE):
            for px in range(TILE_SIZE):
                pixel_val = tile[py * TILE_SIZE + px]
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


def tile_to_ascii(tile: list[int],
                  palette: list[tuple[int, int, int]] | None = None,
                  bpp: int = 4) -> str:
    """Convert a tile to ASCII art string.

    Args:
        tile: List of 64 pixel values (0-15 for 4bpp, 0-255 for 8bpp).
        palette: Optional list of (R, G, B) tuples for color rendering.
                 If provided, uses ANSI true-color escape codes.
        bpp: Bits per pixel (4 or 8). Affects hex digit display.

    Returns:
        Multi-line ASCII representation.

        Without palette: shows pixel values as hex digits.
        With palette:   shows Unicode full block (\\u2588) in ANSI color.
    """
    if len(tile) != 64:
        return f'[Invalid tile: {len(tile)} pixels, expected 64]'

    _check_bpp(bpp)
    lines = []

    if palette:
        # ANSI colored full blocks
        for row in range(TILE_SIZE):
            line = ''
            for col in range(TILE_SIZE):
                idx = row * TILE_SIZE + col
                pixel_val = tile[idx]
                if pixel_val < len(palette):
                    r, g, b = palette[pixel_val]
                    line += f'\033[38;2;{r};{g};{b}m\u2588\033[0m'
                else:
                    line += '?'
            lines.append(line)
    else:
        # Hex digits
        hex_digits = 2 if bpp == 8 else 1
        fmt = f'{{:0{hex_digits}X}}'
        for row in range(TILE_SIZE):
            parts = []
            for col in range(TILE_SIZE):
                idx = row * TILE_SIZE + col
                parts.append(fmt.format(tile[idx]))
            lines.append(' '.join(parts))

    return '\n'.join(lines)


def tile_to_pixels(
    tile: list[int],
    palette: list[tuple[int, int, int]]
) -> list[tuple[int, int, int]]:
    """Map tile pixel indices to RGB colors using palette.

    Args:
        tile: List of 64 pixel values (palette indices).
        palette: List of (R, G, B) tuples.

    Returns:
        List of 64 (R, G, B) tuples. Out-of-range indices return (0, 0, 0).
    """
    result = []
    for pixel_val in tile:
        if 0 <= pixel_val < len(palette):
            result.append(palette[pixel_val])
        else:
            result.append((0, 0, 0))
    return result


def tiles_to_grid(tiles: list[list[int]],
                  columns: int = 4,
                  palette: list[tuple[int, int, int]] | None = None,
                  bpp: int = 4) -> str:
    """Render multiple tiles in a grid layout.

    Args:
        tiles: List of tiles (each: list of 64 pixel values).
        columns: Number of tiles per row (default: 4).
        palette: Optional palette for color rendering.
        bpp: Bits per pixel (4 or 8).

    Returns:
        Multi-line string with tiles arranged in a grid.
    """
    if not tiles:
        return '[No tiles]'

    _check_bpp(bpp)
    rendered = []
    for tile in tiles:
        rendered.append(tile_to_ascii(tile, palette, bpp).split('\n'))

    rows_of_tiles = [rendered[i:i + columns]
                     for i in range(0, len(rendered), columns)]

    output_lines = []
    for tile_row_group in rows_of_tiles:
        for tile_row in range(TILE_SIZE):
            line_parts = []
            for tile_repr in tile_row_group:
                if tile_row < len(tile_repr):
                    line_parts.append(tile_repr[tile_row])
                else:
                    line_parts.append(' ' * TILE_SIZE)
            output_lines.append('  '.join(line_parts))
        output_lines.append('')  # Blank line between tile rows

    return '\n'.join(output_lines).rstrip('\n')


def tile_dump(tile: list[int], bpp: int = 4) -> str:
    """Dump raw pixel values as a formatted grid.

    Args:
        tile: List of 64 pixel values.
        bpp: Bits per pixel (4 or 8), affects width.

    Returns:
        Formatted string showing pixel values in 8x8 grid.
    """
    _check_bpp(bpp)
    hex_digits = 2 if bpp == 8 else 1
    fmt = f'{{:0{hex_digits}X}}'
    lines = []
    lines.append(f'Pixel values (8x8, {bpp}bpp):')
    for row in range(TILE_SIZE):
        parts = []
        for col in range(TILE_SIZE):
            idx = row * TILE_SIZE + col
            parts.append(fmt.format(tile[idx]))
        lines.append(' '.join(parts))
    lines.append(f'Min={min(tile)}, Max={max(tile)}')
    return '\n'.join(lines)


# ── CLI ────────────────────────────────────────────────────────────────────

def parse_tile_range(s: str) -> range:
    """Parse tile range string like '0', '0-15', or '5'."""
    s = s.strip()
    if '-' in s:
        a, b = s.split('-', 1)
        return range(int(a.strip()), int(b.strip()) + 1)
    else:
        n = int(s)
        return range(n, n + 1)


def main():
    parser = argparse.ArgumentParser(
        description='DKC2 SNES BPP Planar Graphics Extractor')

    parser.add_argument('--input', '-i', required=True,
                        help='Raw BPP data file (decompressed graphics)')
    parser.add_argument('--bpp', type=int, default=4, choices=[4, 8],
                        help='Bits per pixel (4 or 8, default: 4)')
    parser.add_argument('--offset', type=lambda x: int(x, 16),
                        default=0,
                        help='Byte offset into input file (hex)')
    parser.add_argument('--length', type=int,
                        help='Number of bytes to read (default: entire file)')

    parser.add_argument('--info', action='store_true',
                        help='Show tile count and format info')
    parser.add_argument('--tile', type=int, default=None,
                        help='Show single tile by index')
    parser.add_argument('--tiles', type=str, default=None,
                        help='Tile range (e.g. "0-15" or "5")')
    parser.add_argument('--grid', type=int, default=None, metavar='COLS',
                        help='Show tile range as grid with N columns')
    parser.add_argument('--dump', action='store_true',
                        help='Dump raw pixel values for tile')

    parser.add_argument('--ascii', action='store_true',
                        help='Render tile(s) as ASCII art')
    parser.add_argument('--palette', type=str, default=None,
                        help='Palette file for color rendering')
    parser.add_argument('--pal-offset', type=lambda x: int(x, 16),
                        default=0,
                        help='Palette offset (hex)')
    parser.add_argument('--pal-colors', type=int, default=16,
                        help='Number of palette colors (default: 16)')

    parser.add_argument('--png', type=str, default=None, metavar='PATH',
                        help='Export tiles as PNG image')
    parser.add_argument('--png-columns', type=int, default=16,
                        help='Columns in PNG grid (default: 16)')
    parser.add_argument('--png-scale', type=int, default=1,
                        help='Scale factor per tile (default: 1)')

    args = parser.parse_args()

    # Read data
    with open(args.input, 'rb') as f:
        data = f.read()

    # Apply offset/length
    offset = args.offset or 0
    if offset > 0 or args.length is not None:
        length = args.length or (len(data) - offset)
        data = data[offset:offset + length]

    # Determine BPP
    bpp = args.bpp
    bytes_per_tile = BPP_TILE_BYTES[bpp]
    num_tiles = tile_count(data, bpp)
    remaining = len(data) - num_tiles * bytes_per_tile

    # Load palette if requested
    palette = None
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
            palette = parse_palette(pal_data, offset=args.pal_offset,
                                    num_colors=args.pal_colors)
        except Exception as e:
            print(f'Warning: palette load failed: {e}', file=sys.stderr)

    # Determine tiles to display
    show_tiles = None
    if args.tile is not None:
        show_tiles = [args.tile]
    elif args.tiles is not None:
        tr = parse_tile_range(args.tiles)
        show_tiles = list(tr)
    elif args.grid is not None:
        show_tiles = list(range(min(args.grid * 8, num_tiles)))

    # Parse all tiles
    try:
        tiles = parse_bpp_tiles(data, bpp)
    except ValueError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)

    # ── PNG export ────────────────────────────────────────────────────
    if args.png:
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            sys.exit('Pillow required for PNG export: pip install pillow')
        if palette is None:
            print('Error: --palette is required for --png export',
                  file=sys.stderr)
            sys.exit(1)
        try:
            tiles_to_png(tiles, palette, args.png,
                         columns=args.png_columns, scale=args.png_scale)
            print(f'Saved {len(tiles)} tiles to {args.png} '
                  f'({args.png_columns}x{args.png_columns} grid'
                  f'{", scale=" + str(args.png_scale) if args.png_scale > 1 else ""})')
        except (ValueError, ImportError) as e:
            print(f'PNG export failed: {e}', file=sys.stderr)
            sys.exit(1)

    # ── Info mode ──────────────────────────────────────────────────────
    if args.info or not (show_tiles is not None and
                         (args.ascii or args.dump)):
        print(f'Tiles:   {num_tiles}')
        print(f'BPP:     {bpp}bpp')
        print(f'Total:   {len(data)} bytes')
        print(f'Tile:    {bytes_per_tile} bytes/tile')
        if remaining > 0:
            print(f'Remain:  {remaining} bytes (partial tile)')
        if palette:
            print(f'Palette: {len(palette)} colors')

    # ── Show tiles ─────────────────────────────────────────────────────
    if show_tiles is not None:
        if args.grid is not None:
            # Grid mode
            grid_tiles = []
            for idx in show_tiles:
                if 0 <= idx < len(tiles):
                    grid_tiles.append(tiles[idx])
            if grid_tiles:
                print(tiles_to_grid(grid_tiles, columns=args.grid,
                                    palette=palette, bpp=bpp))
        else:
            for idx in show_tiles:
                if idx < 0 or idx >= len(tiles):
                    print(f'Tile {idx}: out of range (0-{len(tiles) - 1})',
                          file=sys.stderr)
                    continue

                tile = tiles[idx]

                if args.ascii:
                    print(f'--- Tile {idx} ({bpp}bpp) ---')
                    print(tile_to_ascii(tile, palette, bpp))
                    print()

                if args.dump:
                    print(tile_dump(tile, bpp))
                    print()

                if not args.ascii and not args.dump:
                    # Default: show both
                    print(f'--- Tile {idx} ({bpp}bpp) ---')
                    print(tile_to_ascii(tile, palette, bpp))
                    print()
                    print(tile_dump(tile, bpp))
                    print()


if __name__ == '__main__':
    main()
