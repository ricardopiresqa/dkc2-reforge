"""Debug PAC1 decompression: check top candidates in detail."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from decode_pac1 import decompress, parse_header

rom = open(os.path.join(os.path.dirname(__file__), '..', '..', 'roms', 'dkc2.sfc'), 'rb').read()

test_offsets = [0x35fd8a, 0x34ffe3, 0x35ca33, 0x333507, 0x3b956b]

for off in test_offsets:
    h = parse_header(rom, off)
    if h:
        print(f'=== ROM {hex(off)} ===')
        print(f'  Header: fill={h["fill1"]:02x}{h["fill2"]:02x} dir={h["dir1"]:02x}{h["dir2"]:02x} dirw={h["dirw"]:04x}')
        print(f'  LUT: {", ".join(f"{w:04x}" for w in h["lut"])}')
    
    data = decompress(rom, off)
    if data:
        print(f'  Decompressed: {len(data)} bytes')
        print(f'  First 16: {" ".join(f"{b:02x}" for b in data[:16])}')
        print(f'  Last 16: {" ".join(f"{b:02x}" for b in data[-16:])}')
        
        # Check for 4bpp tile-like structure
        if len(data) >= 32:
            # Check first "tile" - should have non-uniform data
            tile = data[:32]
            unique = len(set(tile))
            print(f'  First 32B unique values: {unique}/32')
    else:
        print(f'  FAILED')
    print()

# Also check: are there larger PAC1 headers we're missing?
# Try scanning without the 39-byte step constraint
print('=== Scanning for ALL possible PAC1 headers (not just 39-step aligned) ===')
from decode_pac1 import header_score
found = []
step = 1  # check every byte
for off in range(0, min(len(rom), 0x400000), step):
    score = header_score(rom, off)
    if score >= 12:
        data = decompress(rom, off)
        if data and len(data) > 5000:
            found.append((off, len(data), score))
            print(f'  ROM {hex(off)}: decompressed={len(data)} score={score}')

if not found:
    print('  No large PAC1 (>5000B) found even with byte-level scanning')
    
# Count how many decompress to >2KB
count = 0
for off in range(0, min(len(rom), 0x400000), 39):
    score = header_score(rom, off)
    if score >= 12:
        data = decompress(rom, off)
        if data and len(data) > 2000:
            count += 1
print(f'\nTotal PAC1 > 2KB (39-step scan): {count}')
