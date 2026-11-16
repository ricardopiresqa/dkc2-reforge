"""Find PAC1 archives that look like player sprite graphics by brute-force scanning."""
import os, sys, struct, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analysis'))
from decode_pac1 import decompress as pac1_decompress, parse_header

ROM = os.path.join(os.path.dirname(__file__), '..', '..', 'roms', 'dkc2.sfc')
MAP = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'rom-map.json')

with open(ROM, 'rb') as f:
    rom = bytearray(f.read())
with open(MAP) as f:
    map_data = json.load(f)

candidates = []
for bank in map_data['banks']:
    pac1_offsets = bank.get('pac1_offsets', [])
    if not pac1_offsets:
        continue
    bank_snes = bank['snes_bank']
    for i, offset in enumerate(pac1_offsets):
        try:
            data = pac1_decompress(rom, offset)
        except Exception:
            continue
        if not data or len(data) < 256:
            continue

        # Heuristics for 4bpp sprite data:
        # 1. Size multiple of 16 (tile size)
        # 2. Low entropy (sprite tiles have runs of same byte)
        # 3. Not too small (<1 tile) or too large (>500 tiles)
        tile_count = len(data) // 16
        if tile_count < 4 or tile_count > 2000:
            continue

        # Check byte variety (sprite data shouldn't be all zeros)
        unique = len(set(data[:512]))
        if unique < 4:
            continue

        candidates.append({
            'bank': bank_snes,
            'pac1_idx': i,
            'offset': offset,
            'size': len(data),
            'tiles': tile_count,
            'unique_bytes': unique,
        })

candidates.sort(key=lambda c: c['size'], reverse=True)
print(f'Found {len(candidates)} PAC1 archives with graphics-like data')
print(f'Top 30 by size:')
print(f'{"Bank":>4} {"Idx":>4} {"Offset":>8} {"Size":>8} {"Tiles":>6} {"Unique":>6}')
print('-' * 50)
for c in candidates[:30]:
    print(f'{c["bank"]:>4} {c["pac1_idx"]:>4} 0x{c["offset"]:06X} {c["size"]:>8} {c["tiles"]:>6} {c["unique_bytes"]:>6}')

# Save full list
with open(os.path.join(os.path.dirname(__file__), '..', '..', 'samples', 'gfx_candidates.json'), 'w') as f:
    json.dump(candidates, f, indent=2)
print(f'\nFull list saved to samples/gfx_candidates.json')
