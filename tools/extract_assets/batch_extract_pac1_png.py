"""Batch PAC1 extraction: decompress all archives, dump tiles as PNGs."""
import json, os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_bpp import parse_bpp, tiles_to_png
from extract_pac1 import decompress_pac1

ROM_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'roms', 'dkc2.sfc')
ROM_MAP = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'rom-map.json')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'samples', 'batch_pac1_png')

os.makedirs(OUT_DIR, exist_ok=True)

with open(ROM_PATH, 'rb') as f:
    rom = f.read()

with open(ROM_MAP) as f:
    map_data = json.load(f)

count = 0
for bank in map_data['banks']:
    pac1_offsets = bank.get('pac1_offsets', [])
    if not pac1_offsets:
        continue
    for i, offset in enumerate(pac1_offsets):
        try:
            decompressed = decompress_pac1(rom, offset)
        except Exception as e:
            continue
        if not decompressed or len(decompressed) < 64:
            continue
        data = decompressed

        # Try 4bpp tiles (16 bytes/tile)
        bpp = 4
        tile_bytes = 16
        num_tiles = len(data) // tile_bytes
        if num_tiles == 0:
            continue

        tiles_4bpp = parse_bpp(data, bpp=bpp)
        if not tiles_4bpp:
            continue

        png_data = tiles_to_png(tiles_4bpp, columns=16, scale=1)
        bank_snes = bank['snes_bank']
        aid = bank.get('pac1_ids', {}).get(str(i), i)
        fname = f'b{bank_snes}_id{aid}_off{offset:06X}_{len(data)}B_{num_tiles}tiles.png'
        fpath = os.path.join(OUT_DIR, fname)
        with open(fpath, 'wb') as pf:
            pf.write(png_data)
        count += 1

        if count % 50 == 0:
            print(f'Extracted {count}...', flush=True)

print(f'Done. {count} PNGs written to {OUT_DIR}')
