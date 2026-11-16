"""Extract first batch of PAC1 archives as PNGs for visual identification."""
import json, os, sys, struct

ROM = os.path.join(os.path.dirname(__file__), '..', '..', 'roms', 'dkc2.sfc')
MAP = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'rom-map.json')
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'samples', 'batch_pac1_png')

os.makedirs(OUT, exist_ok=True)

with open(ROM, 'rb') as f:
    rom = bytearray(f.read())

with open(MAP) as f:
    map_data = json.load(f)

import importlib.util
spec = importlib.util.spec_from_file_location("extract_bpp",
    os.path.join(os.path.dirname(__file__), 'extract_bpp.py'))
bpp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bpp)

spec2 = importlib.util.spec_from_file_location("extract_pac1",
    os.path.join(os.path.dirname(__file__), 'extract_pac1.py'))
pac1 = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(pac1)

count = 0
for bank in map_data['banks']:
    pac1_offsets = bank.get('pac1_offsets', [])
    if not pac1_offsets:
        continue
    bank_snes = bank['snes_bank']
    for i, offset in enumerate(pac1_offsets):
        if count >= 100:
            break
        try:
            decompressed = pac1.decompress_pac1(rom, offset)
        except Exception:
            continue
        if not decompressed or len(decompressed) < 64:
            continue
        data = bytes(decompressed)
        tiles = bpp.parse_bpp(data, bpp=4)
        if not tiles:
            continue
        png = bpp.tiles_to_png(tiles, columns=16, scale=1)
        fname = f'b{bank_snes}_i{i}_off{offset:06X}_{len(data)}B.png'
        with open(os.path.join(OUT, fname), 'wb') as pf:
            pf.write(png)
        count += 1
    if count >= 100:
        break

print(f'Done: {count} PNGs -> {OUT}')
