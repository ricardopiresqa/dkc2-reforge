rom = open('roms/dkc2.sfc', 'rb').read()

# Check potential $B5:8000 targets
# Standard HiROM: bank $B5 -> ROM offset = (B5-80)*10000 + (offset)
# $B5:8000 -> ($35)*10000 + $8000 = $358000
candidates = {
    '0x358000 (HiROM B5:8000)': 0x358000,
    '0x008000 (SA-1 B5->80)': 0x008000,
    '0x308000 (B5-80)*8000': 0x308000,
    '0x348000 (B5-80)*8000+8000': 0x348000,
    '0x358000+8000': 0x358000,
}

for name, offset in candidates.items():
    if offset + 16 <= len(rom):
        data = rom[offset:offset+16]
        hexb = ' '.join(f'{b:02X}' for b in data)
        print(f'{name} @ 0x{offset:06X}: {hexb}')
    else:
        print(f'{name} @ 0x{offset:06X}: out of bounds')

# Also check what is called after that
# JSL $BB91D9
print()
print('=== JSL $BB91D9 target check ===')
# $BB:91D9 in HiROM
# Standard: ($BB-$80)*10000 + 91D9 = $3B0000 + 91D9 = $3B91D9... 
# But it's in the $8000-$FFFF range typically
# Actually in HiROM, addr $xx:yyyy where $80<=xx<=$FF, $8000<=yyyy<=$FFFF
# ROM offset = (xx & 0x3F) * 0x8000 + (yyyy & 0x7FFF) + 0x400000? No
# Let me try a few

for test_bank_hi in range(0x80, 0xC0):
    test_offset = test_bank_hi
    # Standard HiROM: offset = (bank-0x80)*0x10000 + (addr-0x8000)
    # Actually for $B5:91D9: (0xB5-0x80)*0x10000 + (0x91D9-0x8000) = 0x350000 + 0x11D9 = 0x3511D9
    pass

# Let me try the most common HiROM formula
# ROM offset = ((bank - 0x80) << 4) << 12 as a 24-bit linearization
# Actually straightforward: for 4MB HiROM, the mapping is:
# Bank $80-$BF maps linearly, each bank is 64KB
# Address $B5:XXXX -> linear offset = ($B5 - $80) * 0x10000 + XXXX
# But the lower 32KB ($0000-$7FFF) is typically a repeat or latch
# For HiROM, the "visible" portion in $8000-$FFFF:
# offset = (bank - $80) * 0x8000 + (addr & 0x7FFF)
# BUT for $8000+ addresses: offset = (bank - $80) * 0x8000 + (addr - 0x8000)

# So for $BB:91D9 -> $8000 <= $91D9 so:
# offset = (0xBB - 0x80) * 0x8000 + (0x91D9 - 0x8000)
# = 0x3B * 0x8000 + 0x11D9
# = 0x1D8000 + 0x11D9
# = 0x1D91D9

# Hmm but that's only 1.9MB into a 4MB ROM. Let me check.
off_bb = (0xBB - 0x80) * 0x8000 + (0x91D9 - 0x8000)
print(f'HiROM ($8000 visible) $BB:91D9 -> ROM 0x{off_bb:06X}')
if off_bb < len(rom):
    print(f'  Data: {" ".join(f"{b:02X}" for b in rom[off_bb:off_bb+16])}')
else:
    print(f'  Out of bounds')

# Also try the full 64KB bank mapping
off_bb2 = (0xBB - 0x80) * 0x10000 + 0x91D9
print(f'HiROM (64KB full) $BB:91D9 -> ROM 0x{off_bb2:06X}')
if off_bb2 < len(rom):
    print(f'  Data: {" ".join(f"{b:02X}" for b in rom[off_bb2:off_bb2+16])}')
else:
    print(f'  Out of bounds')

# Check $B5:8000 same way
off_b5 = (0xB5 - 0x80) * 0x8000 + (0x8000 - 0x8000)
print(f'\nHiROM ($8000 visible) $B5:8000 -> ROM 0x{off_b5:06X} (=0x{off_b5:X})')
if off_b5 < len(rom):
    print(f'  Data: {" ".join(f"{b:02X}" for b in rom[off_b5:off_b5+16])}')
    
off_b5_full = (0xB5 - 0x80) * 0x10000 + 0x8000
print(f'HiROM (64KB full) $B5:8000 -> ROM 0x{off_b5_full:06X}')
if off_b5_full < len(rom):
    print(f'  Data: {" ".join(f"{b:02X}" for b in rom[off_b5_full:off_b5_full+16])}')

# Also check what ROM data is at offset 0x008000 - see if it's boot code or vectors
print(f'\nROM 0x008000 start: {" ".join(f"{b:02X}" for b in rom[0x8000:0x8010])}')
print(f'ROM 0x00FFC0 (vectors in bank 0 area): {" ".join(f"{b:02X}" for b in rom[0xFFC0:0x10000])}')
