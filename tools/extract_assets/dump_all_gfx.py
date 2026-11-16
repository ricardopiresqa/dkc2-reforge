"""Decompress all PAC1 archives and dump tiles as grayscale PNGs for visual ID."""
import os, sys, json

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, '..', 'analysis'))
sys.path.insert(0, BASE)

from decode_pac1 import decompress, parse_header, header_score
from extract_bpp import parse_bpp_tiles
try:
    from PIL import Image
except ImportError:
    Image = None

ROM = os.path.join(BASE, '..', '..', 'roms', 'dkc2.sfc')
OUT = os.path.join(BASE, '..', '..', 'samples', 'dump_gfx')
os.makedirs(OUT, exist_ok=True)

with open(ROM, 'rb') as f:
    rom = f.read()

MAIN_BANKS = ['$80', '$81', '$82', '$83', '$84', '$85', '$86', '$87',
              '$88', '$89', '$8A', '$8B', '$8C', '$8D', '$8E', '$8F',
              '$90', '$91', '$92', '$93', '$94', '$95', '$96', '$97',
              '$98', '$99', '$9A', '$9B', '$9C', '$9D', '$9E', '$9F',
              '$A0', '$A1', '$A2', '$A3', '$A4', '$A5', '$A6', '$A7',
              '$A8', '$A9', '$AA', '$AB', '$AC', '$AD', '$AE', '$AF',
              '$B0', '$B1', '$B2', '$B3', '$B4', '$B5', '$B6', '$B7',
              '$B8', '$B9', '$BA', '$BB', '$BC', '$BD', '$BE', '$BF']

with open(os.path.join(BASE, '..', '..', 'docs', 'rom-map.json')) as f:
    map_data = json.load(f)

# Build bank index
bank_by_snes = {b['snes_bank']: b for b in map_data['banks']}

# Dummy grayscale palette (16 shades of gray)
dummy_palette = [(i * 17, i * 17, i * 17) for i in range(16)]

count = 0
failed = 0

for bank_name in MAIN_BANKS:
    bank = bank_by_snes.get(bank_name)
    if not bank:
        continue
    offs = bank.get('pac1_offsets', [])
    if not offs:
        continue

    for idx, off in enumerate(offs):
        try:
            h = parse_header(rom, off)
            if not h:
                continue
            data = decompress(rom, off)
            if not data or len(data) < 128:
                failed += 1
                continue
        except:
            failed += 1
            continue

        # Pad to 16-byte boundary for tile parsing
        pad = (16 - len(data) % 16) % 16
        padded = data + b'\x00' * pad

        try:
            tiles = parse_bpp_tiles(padded, bpp=4)
            if not tiles or len(tiles) < 4:
                failed += 1
                continue
        except:
            failed += 1
            continue

        if Image is None:
            continue

        num_tiles = len(tiles)
        cols = min(16, num_tiles)
        rows = (num_tiles + cols - 1) // cols
        img = Image.new('RGB', (cols * 8, rows * 8))
        px = img.load()

        for ti, tile in enumerate(tiles):
            cx = ti % cols
            cy = ti // cols
            for py in range(8):
                for px_i in range(8):
                    val = tile[py * 8 + px_i]
                    if 0 <= val < 16:
                        c = dummy_palette[val]
                    else:
                        c = (0, 0, 0)
                    px[cx * 8 + px_i, cy * 8 + py] = c

        fname = f'b{bank_name}_idx{idx}_{off:06X}_{len(data)}B_{num_tiles}t.png'
        img.save(os.path.join(OUT, fname))
        count += 1

        if count % 30 == 0:
            print(f'{count} PNGs...', flush=True)

print(f'\nDone: {count} PNGs saved to {OUT}')
print(f'Failed/skipped: {failed}')
