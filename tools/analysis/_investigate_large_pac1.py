"""Investigate the large PAC1 candidates found by byte-level scanning."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from decode_pac1 import decompress, parse_header, header_score

rom = open(os.path.join(os.path.dirname(__file__), '..', '..', 'roms', 'dkc2.sfc'), 'rb').read()

# Check the found large entries
offsets = [0x3BE7DF, 0x3CB5E2, 0x3CB5E4, 0x3CB5E6, 0x3CB5E8]

for off in offsets:
    h = parse_header(rom, off)
    score = header_score(rom, off)
    data = decompress(rom, off)
    
    print(f'=== ROM {hex(off)} ===')
    print(f'  Score: {score}')
    if h:
        print(f'  LUT: {", ".join(f"{w:04x}" for w in h["lut"])}')
    if data:
        print(f'  Decompressed: {len(data)} bytes')
        print(f'  Validity check:')
        print(f'    Unique bytes: {len(set(data))} / 256')
        # Check entropy
        from collections import Counter
        counts = Counter(data)
        entropy = -sum((c/len(data)) * __import__('math').log2(c/len(data)) for c in counts.values())
        print(f'    Entropy: {entropy:.2f} (random data ~8.0)')
        print(f'    Zero bytes: {counts[0]} / {len(data)} ({100*counts[0]/len(data):.1f}%)')
        
        # Try 4bpp tile interpretation
        if len(data) % 32 == 0:
            tiles = len(data) // 32
            print(f'    4bpp tiles: {tiles}')
        if len(data) % 64 == 0:
            print(f'    8bpp tiles: {len(data)//64}')
        if len(data) % 16 == 0:
            print(f'    2bpp tiles: {len(data)//16}')
        
        # First 64 bytes
        print(f'  First 64B:')
        for i in range(0, min(64, len(data)), 16):
            chunk = data[i:i+16]
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            print(f'    {i:04x}: {" ".join(f"{b:02x}" for b in chunk)}  {ascii_str}')
    print()

# Now let's figure out what these data areas actually are.
# Check the raw ROM data around the large PAC1 hits
print('=== Raw ROM around 0x3BE7DF ===')
for i in range(-32, 128, 16):
    off = 0x3BE7DF + i
    chunk = rom[off:off+16]
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    marker = ' <-- header' if i == 0 else ''
    print(f'  {off:06X}: {" ".join(f"{b:02x}" for b in chunk)}  {ascii_str}{marker}')

print()
print('=== Raw ROM around 0x3CB5E2 ===')
for i in range(-32, 128, 16):
    off = 0x3CB5E2 + i
    chunk = rom[off:off+16]
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    marker = ' <-- header' if i == 0 else ''
    print(f'  {off:06X}: {" ".join(f"{b:02x}" for b in chunk)}  {ascii_str}{marker}')

# Quick scan: find ALL PAC1 that decompress to > 2KB
print()
print('=== Full scan for PAC1 > 2KB decompressed ===')
import json
with open(os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'rom-map.json')) as f:
    rd = json.load(f)

big = []
for h in rd['pac1_headers']:
    off = h['rom_offset']
    try:
        data = decompress(rom, off)
    except Exception:
        continue
    if data and len(data) > 2000:
        big.append((off, len(data), h.get('snes_addr', '')))

if big:
    print(f'Found {len(big)} large PAC1:')
    for off, size, snes in big:
        print(f'  ROM {hex(off)}: {size}B {snes}')
else:
    print('None found - 39-step scan misses all large headers')

# Full byte-level scan limited to specific bank ranges that have density
print()
print('=== Targeted byte-level scan of high banks (0x38-0x3F) ===')
from decode_pac1 import header_score
big2 = []
step = 1
for off in range(0x380000, min(len(rom), 0x400000), step):
    score = header_score(rom, off)
    if score >= 12:
        data = decompress(rom, off)
        if data and len(data) > 1000:
            big2.append((off, len(data), score, data[:16]))

if big2:
    big2.sort(key=lambda x: x[1], reverse=True)
    print(f'Found {len(big2)} PAC1 > 1KB in 0x38-0x3F range:')
    for off, size, score, first16 in big2[:30]:
        print(f'  ROM {hex(off)}: {size}B score={score}')
    print(f'  ... and {len(big2)-30} more')
else:
    print('None found')
