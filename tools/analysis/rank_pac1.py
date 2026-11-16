"""Rank PAC1 archives by actual decompressed size + try tile extraction."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from decode_pac1 import decompress

rom = open(os.path.join(os.path.dirname(__file__), '..', '..', 'roms', 'dkc2.sfc'), 'rb').read()

with open(os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'rom-map.json')) as f:
    rd = json.load(f)

headers = rd['pac1_headers']

results = []
for h in headers:
    off = h['rom_offset']
    try:
        data = decompress(rom, off)
        if data:
            results.append({
                'rom_offset': off,
                'snes_addr': h['snes_addr'],
                'decomp_size': len(data),
                'comp_size': data[3] | (data[4] << 8) if len(data) > 4 else 0,
            })
    except Exception:
        pass

results.sort(key=lambda x: x['decomp_size'], reverse=True)

print(f"=== Successfully decompressed: {len(results)} / {len(headers)} PAC1 headers ===")
print(f"\n=== Top 60 by decompressed size ===")
for i, r in enumerate(results[:60]):
    print(f"  {i+1:2d}. ROM {r['rom_offset']:#08x} {r['snes_addr']}  decomp={r['decomp_size']:>6}  comp={r['comp_size']:>6}")

sizes = [r['decomp_size'] for r in results]
print(f"\n=== Stats ===")
print(f"Decompressed: {len(results)} / {len(headers)}")
print(f"Min: {min(sizes)}  Max: {max(sizes)}  Median: {sorted(sizes)[len(sizes)//2]}")

for threshold in [0, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]:
    count = sum(1 for s in sizes if s > threshold)
    print(f"  > {threshold:>6}: {count}")

# Now try extracting top ones as 4bpp tiles
print("\n\n=== Attempting 4bpp tile extraction for top 30 ===")
out_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'samples', 'dump_gfx_v2')
os.makedirs(out_dir, exist_ok=True)

for i, r in enumerate(results[:30]):
    off = r['rom_offset']
    data = decompress(rom, off)
    if not data:
        continue
    # Try 4bpp
    tile_count_4bpp = len(data) // 32
    # Also try 2bpp and 8bpp
    tile_count_2bpp = len(data) // 16
    tile_count_8bpp = len(data) // 64
    
    # Write RAW data for inspection
    raw_path = os.path.join(out_dir, f'{i+1:02d}_rom{off:08x}_size{r["decomp_size"]:05d}.raw')
    with open(raw_path, 'wb') as f:
        f.write(data)
    
    valid = []
    for bpp, tile_size in [(2, 16), (4, 32), (8, 64)]:
        if len(data) % tile_size == 0:
            valid.append(f'{bpp}bpp({len(data)//tile_size}tiles)')
    
    print(f"  {i+1:2d}. ROM {off:#08x} size={r['decomp_size']:>6}  formats: {', '.join(valid)}")
