"""SNES RGB555 Palette Extraction.

Parses SNES standard RGB555 palettes (2 bytes per color, little-endian)
and provides rendering in hex, ANSI colored blocks, and raw RGB tuples.

SNES RGB555 format:
  Bit  15     = 0 (unused/master brightness in some contexts)
  Bits 10-14  = Red   (0-31)
  Bits  5-9   = Green (0-31)
  Bits  0-4   = Blue  (0-31)

Mapping 0-31 to 0-255: channel * 255 // 31

Usage:
    # Parse palette from file
    python extract_palette.py --input palette.bin --colors 16 --ascii

    # Parse palette from ROM at offset
    python extract_palette.py --rom roms/dkc2.sfc --offset 0x296B2A \
        --colors 256 --hex

    # Quick info
    python extract_palette.py --input palette.bin --info
"""

import argparse
import io
import os
import struct
import sys

# Ensure stdout supports UTF-8 for Unicode block chars on Windows
if sys.platform == 'win32' and isinstance(sys.stdout, io.TextIOWrapper):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except AttributeError:
            pass




# ── RGB555 Conversion ──────────────────────────────────────────────────────

def rgb555_to_rgb(word: int) -> tuple[int, int, int]:
    """Convert an RGB555 word to (R, G, B) in 0-255 range.

    Args:
        word: 16-bit RGB555 value (bits 0-14 used).

    Returns:
        (R, G, B) tuple, each 0-255.
    """
    r = (word >> 10) & 0x1F
    g = (word >> 5) & 0x1F
    b = word & 0x1F
    return (r * 255 // 31, g * 255 // 31, b * 255 // 31)


def rgb555_to_rgb_float(word: int) -> tuple[float, float, float]:
    """Convert RGB555 word to (R, G, B) in 0.0-1.0 range."""
    r = (word >> 10) & 0x1F
    g = (word >> 5) & 0x1F
    b = word & 0x1F
    return (r / 31.0, g / 31.0, b / 31.0)


# ── Palette Parsing ────────────────────────────────────────────────────────

def parse_palette(data: bytes, offset: int = 0,
                  num_colors: int = 16) -> list[tuple[int, int, int]]:
    """Parse SNES RGB555 palette from binary data.

    Args:
        data: Raw binary data containing palette entries.
        offset: Byte offset into data where palette starts.
        num_colors: Number of colors to read (default: 16).

    Returns:
        List of (R, G, B) tuples, each component 0-255.

    Raises:
        ValueError: If data is too short for requested colors.
    """
    needed = offset + num_colors * 2
    if len(data) < needed:
        raise ValueError(
            f'Data too short: need {needed}B for {num_colors} colors '
            f'at offset {offset}, got {len(data)}B'
        )
    palette = []
    for i in range(num_colors):
        word = struct.unpack_from('<H', data, offset + i * 2)[0]
        palette.append(rgb555_to_rgb(word))
    return palette


# ── Rendering ──────────────────────────────────────────────────────────────

def palette_to_hex(color: tuple[int, int, int]) -> str:
    """Return #RRGGBB string for an RGB tuple."""
    return f'#{color[0]:02X}{color[1]:02X}{color[2]:02X}'


def palette_to_ascii(palette: list[tuple[int, int, int]],
                     columns: int = 8) -> str:
    """Render palette as colored ASCII blocks.

    Uses ANSI true-color escape codes (\033[38;2;R;G;Bm) for color
    and Unicode full block character (\\u2588) for each color swatch.

    Args:
        palette: List of (R, G, B) tuples.
        columns: Number of swatches per row (default: 8).

    Returns:
        String with ANSI-colored blocks and hex labels.
    """
    lines = []
    for i in range(0, len(palette), columns):
        row = palette[i:i + columns]
        # Color swatch row
        swatch_line = ''
        label_line = ''
        for j, color in enumerate(row):
            r, g, b = color
            swatch_line += f'\033[38;2;{r};{g};{b}m\u2588\033[0m '
            label_line += f'{palette_to_hex(color)} '
        lines.append(swatch_line)
        lines.append(label_line)
        lines.append('')
    return '\n'.join(lines).rstrip('\n')


def palette_info(palette: list[tuple[int, int, int]]) -> str:
    """Return summary info about a palette."""
    if not palette:
        return 'Empty palette'
    unique = len(set(palette))
    r_avg = sum(c[0] for c in palette) / len(palette)
    g_avg = sum(c[1] for c in palette) / len(palette)
    b_avg = sum(c[2] for c in palette) / len(palette)
    return (
        f'{len(palette)} colors, {unique} unique, '
        f'avg RGB({r_avg:.0f}, {g_avg:.0f}, {b_avg:.0f})'
    )


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='DKC2 SNES RGB555 Palette Extractor')

    # Mutually exclusive input group
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', '-i',
                             help='Raw palette binary file')
    input_group.add_argument('--rom',
                             help='ROM file (requires --offset)')
    input_group.add_argument('--decompressed', '-d',
                             help='Decompressed asset file containing palette')

    parser.add_argument('--offset',
                        type=lambda x: int(x, 16),
                        help='ROM/decompressed offset (hex, default: 0)')
    parser.add_argument('--colors', '-n', type=int, default=16,
                        help='Number of palette colors (default: 16)')

    output_group = parser.add_argument_group('Output modes')
    output_group.add_argument('--ascii', action='store_true',
                              help='Render palette as ANSI colored blocks')
    output_group.add_argument('--hex', action='store_true',
                              help='Show palette as #RRGGBB list')
    output_group.add_argument('--info', action='store_true',
                              help='Show palette summary info')
    output_group.add_argument('--raw', action='store_true',
                              help='Show raw RGB555 hex values')
    output_group.add_argument('--columns', type=int, default=8,
                              help='Columns per row for --ascii (default: 8)')
    parser.add_argument('--extract', '-e',
                        help='Extract palette to binary file')

    args = parser.parse_args()

    # Read data
    if args.input:
        with open(args.input, 'rb') as f:
            data = f.read()
    elif args.rom:
        with open(args.rom, 'rb') as f:
            data = f.read()
    elif args.decompressed:
        with open(args.decompressed, 'rb') as f:
            data = f.read()

    offset = args.offset or 0

    try:
        palette = parse_palette(data, offset=offset, num_colors=args.colors)
    except ValueError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)

    # Default: show hex if no output mode specified
    if not (args.ascii or args.hex or args.info or args.raw):
        args.hex = True

    if args.info:
        print(palette_info(palette))

    if args.raw:
        for i, color in enumerate(palette):
            word = (color[0] * 31 // 255) << 10 | \
                   (color[1] * 31 // 255) << 5 | \
                   (color[2] * 31 // 255)
            print(f'  [{i:3d}] 0x{word:04X}  '
                  f'R={color[0]:3d} G={color[1]:3d} B={color[2]:3d}')

    if args.hex:
        for i, color in enumerate(palette):
            print(f'  [{i:3d}] {palette_to_hex(color)}')

    if args.ascii:
        print(palette_to_ascii(palette, columns=args.columns))

    if args.extract:
        # Write as raw RGB555 (2 bytes per color, little-endian)
        out_data = bytearray()
        for i, color in enumerate(palette):
            r5 = color[0] * 31 // 255
            g5 = color[1] * 31 // 255
            b5 = color[2] * 31 // 255
            word = (r5 << 10) | (g5 << 5) | b5
            out_data.extend(struct.pack('<H', word))
        with open(args.extract, 'wb') as f:
            f.write(out_data)
        print(f'Wrote {len(out_data)}B to {args.extract}')


if __name__ == '__main__':
    main()
