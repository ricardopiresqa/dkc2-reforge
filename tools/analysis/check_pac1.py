"""Check what's at the top PAC1 offset."""
import sys, os
sys.path.insert(0, r'C:\Projetos Cursor\dkc2-reforge\tools\analysis')
from decode_pac1 import decompress, parse_header

rom = open(r'C:\Projetos Cursor\dkc2-reforge\roms\dkc2.sfc', 'rb').read()

off = 0x35fd8a
h = rom[off:off+39]
print(f'Header at 0x{off:08X}:')
print(f'  h[0]={h[0]:02X} h[1]={h[1]:02X} h[2]={h[2]:02X} h[3]={h[3]:02X} h[4]={h[4]:02X}')
print(f'  dirw: 0x{h[5]:02X}{h[6]:02X}')
lut_hex = ' '.join(f'{h[7+i*2]:02X}{h[8+i*2]:02X}' for i in range(16))
print(f'  LUT: {lut_hex}')

ph = parse_header(rom, off)
print(f'\nParsed: {ph}')

dec = decompress(rom, off)
if dec:
    print(f'\nDecompressed: {len(dec)} bytes')
    print(f'First 64 hex: {" ".join(f"{b:02X}" for b in dec[:64])}')
else:
    print(f'\nDecompression returned None')
    # Try with larger max_output
    from decode_pac1 import decompress
    import importlib
    importlib.reload(sys.modules['decode_pac1'])
    
# Now check a potentially bigger PAC1 - look at compressed data
# Let me see what a header that didn't decompress looks like
# Try a PAC1 from the original DKC that might hold sprite data
# First, let me find PAC1s that have compressed_size > 10000 by checking the raw bytes
# The compressed size is dir1|dir2 in the header... no, that's something else

# Let me check the biggest possible PAC1 by looking at the byte before each header
# PAC1 seems to be at specific offsets. Let me check a few from different banks
for test_off in [0x34ffe3, 0x35ca33, 0x333507, 0x1aa94e, 0x350000, 0x360000]:
    if test_off + 39 > len(rom):
        continue
    h2 = rom[test_off:test_off+39]
    if h2[0] == 0:
        dec2 = decompress(rom, test_off)
        status = f'{len(dec2)}B' if dec2 else 'None'
        print(f'\n0x{test_off:08X}: header[0]=00 -> {status}')
        if dec2 and len(dec2) > 100:
            print(f'  First 32 hex: {" ".join(f"{b:02X}" for b in dec2[:32])}')

# The problem might be that the PAC1 scanner found false positives - bytes that
# look like valid headers but aren't. Let me check the real sprite PAC1s.
# In DKC2, sprite graphics are usually in banks $80-$9F area.
# Let me check what banks have headers and their distribution.

print('\n\n=== Distribution of successful decompressions by ROM bank ===')
bank_counts = {}
for idx, h_entry in enumerate(__import__('json').load(open(r'C:\Projetos Cursor\dkc2-reforge\docs\rom-map.json'))['pac1_headers']):
    ro = h_entry['rom_offset']
    bank = ro // 0x8000
    bank_counts[bank] = bank_counts.get(bank, 0) + 1

for bk in sorted(bank_counts.keys()):
    print(f'  Bank {bk:3d} (0x{bk*0x8000:06X}): {bank_counts[bk]} headers')
