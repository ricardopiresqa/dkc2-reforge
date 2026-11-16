"""Analyze sprite graphics pipeline - find the PAC1 sprite mapping table."""
import os, sys

rom = open(os.path.join(os.path.dirname(__file__), '..', '..', 'roms', 'dkc2.sfc'), 'rb').read()

# Use the real rom_offset function
# LDA $C25E at $A9:8620 context: the data bank is $A9
# So $A9:C25E -> ((0xA9 & 0x7F) << 15) | (0xC25E & 0x7FFF)
# = 0x29 << 15 | 0x425E = 0x148000 | 0x425E = 0x14C25E
off = 0x14C25E
print(f'=== Table at $A9:C25E (ROM {off:#010x}) ===')
for i in range(0, 128, 16):
    hex_str = ' '.join(f'{b:02x}' for b in rom[off+i:off+i+16])
    print(f'  {off+i:06X}: {hex_str}')

# Also $A9:C2C9 and $A9:C2D5 which are referenced in the code
for addr in [0xC2C9, 0xC2D5]:
    off2 = ((0xA9 & 0x7F) << 15) | (addr & 0x7FFF)
    print(f'\n=== $A9:{addr:04X} (ROM {off2:#010x}) ===')
    hex_str = ' '.join(f'{b:02x}' for b in rom[off2:off2+32])
    print(f'  {hex_str}')

# Now let me find the sprite PAC1 mapping table.
# The function at $A98620 writes to $0685 = $041E and $0687 = $8000.
# $0685 and $0687 together make a sprite code ID.
# Let me search for code that reads ROM PAC1 offsets.

# In DKC2, the decompression of sprite graphics is handled by referencing
# a table that maps {sprite_type -> {bank, offset}}.
# Let me search for the decompress call pattern.
# The SA-1 decompress function at $B80000 area takes parameters in registers
# that indicate which data to decompress.

# Let me look at the full function around $A98600
print('\n\n=== Full function at $A98500-$A98FFF ===')
off = 0x348500
for i in range(0, 0xB00, 16):
    hex_str = ' '.join(f'{b:02x}' for b in rom[off+i:off+i+16])
    line = f'  {off+i:06X}: {hex_str}'
    # Highlight if it's a JSL or references important addresses
    if '22' in hex_str[:8] or 'a7 06' in hex_str or '87 06' in hex_str or '06a7' in hex_str:
        print(f'{line}  <---')
    else:
        print(line)

# Also look for the actual decompression function in bank $B8
print('\n\n=== SA-1 decompression functions at $B80000+ ===')
off = 0x2E0000  # $B8 = 0x2E * 0x8000
# Read a table of contents if present
for i in range(0, 0x200, 16):
    hex_str = ' '.join(f'{b:02x}' for b in rom[off+i:off+i+16])
    if hex_str != '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00':
        print(f'  {off+i:06X}: {hex_str}')
    else:
        # print blank line for zeros but skip to reduce noise
        pass
