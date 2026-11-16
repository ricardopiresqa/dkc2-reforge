"""
Verify sample extraction against ROM and check header format.
"""
import struct

rom = open('roms/dkc2.sfc', 'rb').read()
rom_size = len(rom)
print(f"ROM size: {rom_size} bytes ({rom_size//1024}KB)")

# Extract a few samples directly from ROM using the offset formula
# offset = (bank & 0x3F) * 0x10000 + addr
sample_specs = [
    ("asset_b80_8F54", 0x80, 0x8F54, 1266),
    ("asset_b80_936E", 0x80, 0x936E, 1213),
    ("asset_b80_943C", 0x80, 0x943C, 908),
    ("asset_b80_D0CA", 0x80, 0xD0CA, 2075),
]

for name, bank, addr, size in sample_specs:
    rom_offset = (bank & 0x3F) * 0x10000 + addr
    if rom_offset >= rom_size:
        print(f"{name}: ROM offset 0x{rom_offset:06X} out of range!")
        continue
    rom_data = rom[rom_offset:rom_offset+size]
    
    # Try to find the 39-byte header
    # The header has a specific pattern: byte[0] can be anything, byte[39]=format
    # Let's scan for potential format bytes
    print(f"\n{name}: ROM offset 0x{rom_offset:06X}, size {size}")
    print(f"  First 40 bytes from ROM:")
    print(f"  [0]={rom_data[0]:02X} [1]={rom_data[1]:02X} [2]={rom_data[2]:02X} [3]={rom_data[3]:02X} [4]={rom_data[4]:02X}")
    print(f"  [5-6]={struct.unpack_from('<H', rom_data, 5)[0]:04X}")
    print(f"  [7-14]={list(rom_data[7:15])}")
    print(f"  [39]={rom_data[39]:02X} (fmt: hi={(rom_data[39]>>4)&0xF} lo={rom_data[39]&0xF})")
    
    # Compare with sample file
    sample = open(f'samples/{name}_{size}B.bin', 'rb').read()
    match = all(rom_data[i] == sample[i] for i in range(min(len(rom_data), len(sample))))
    print(f"  Matches sample: {match}")

# Also check: where in the ROM does the compressed data actually live?
# The callers use LDX for source in WRAM $7F, but the data is loaded from ROM by a loader.
# Let's find the loader.
print("\n\nLooking for compressed data patterns in ROM...")
# Scan for potential compressed blocks (40+ bytes, valid format byte at [39])
count = 0
for offset in range(0, min(rom_size, 0x100000), 1):
    if offset + 40 >= rom_size:
        break
    # Check if byte[39] looks like a valid format byte (high nibble 0-15, any)
    fmt = rom[offset + 39]
    hi = (fmt >> 4) & 0xF
    # The header params are usually sequential or have patterns
    p1, p2, p3, p4 = rom[offset+1], rom[offset+2], rom[offset+3], rom[offset+4]
    w = struct.unpack_from('<H', rom, offset+5)[0]
    # Check if word[5-6] seems related to params
    count += 1
    if count <= 5:
        print(f"ROM+0x{offset:06X}: fmt=${fmt:02X} params=({p1:02X},{p2:02X},{p3:02X},{p4:02X}) word={w:04X}")
