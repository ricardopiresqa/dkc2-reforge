import json, sys
sys.path.insert(0, '.')
from decode_pac1 import decompress

with open('rom-map.json') as f:
    rm = json.load(f)

with open('../../roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

# Decompress top 500 by score
sorted_headers = sorted(rm['pac1_headers'], key=lambda x: -x['score'])[:500]

results = []
for p in sorted_headers:
    off = p['rom_offset']
    dec = decompress(rom, off, max_output=65536)
    if dec and len(dec) >= 256:
        results.append((off, p['score'], len(dec)))

results.sort(key=lambda x: -x[2])
print('Top 40 PAC1 archives by decompressed size:')
print(f'  {"ROM Offset":>10} {"Score":>5} {"Size":>8} {"Bank":>5} {"Sector":>5}')
print('  ' + '-'*40)
for off, sc, sz in results[:40]:
    bank = off // 0x10000
    sector = (off % 0x10000) // 0x2000
    print(f'  0x{off:08X}  {sc:3d}  {sz:6d}B  ${bank+0xC0:02X}  {sector*0x2000:04X}')
print(f'\nTotal with >=256B: {len(results)}')
if results:
    max_sz = results[0][2]
    print(f'Max size: {max_sz}B ({max_sz/1024:.1f}KB)')
    print(f'256 tile threshold (4bpp): 8192B')
    print(f'Count > 8192B: {sum(1 for _,_,s in results if s > 8192)}')
    print(f'Count > 4096B: {sum(1 for _,_,s in results if s > 4096)}')
    print(f'Count > 2048B: {sum(1 for _,_,s in results if s > 2048)}')
    print(f'Count > 1024B: {sum(1 for _,_,s in results if s > 1024)}')
