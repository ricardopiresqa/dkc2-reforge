rom = open('roms/dkc2.sfc', 'rb').read()
print('ROM size:', len(rom), 'bytes')

# For $80:B461, expected bytes: a2 ff 01 9a 9c 02 21 e2 20 a9
# Current formula: (bank & 0x3F) * 0x10000 + addr = 0xB461
print('Current mapping at $80:B461 (offset 0xB461):')
print(' '.join(f'{rom[0xB461+i]:02x}' for i in range(10)))

# LoROM: offset = (bank & 0x3F) * 0x8000 + (addr & 0x7FFF)
# For $80:B461: offset = 0 * 0x8000 + 0x3461 = 0x3461
lo_offset = 0x3461
print(f'LoROM mapping at $80:B461 (offset 0x{lo_offset:X}):')
print(' '.join(f'{rom[lo_offset+i]:02x}' for i in range(10)))

# HiROM: offset = (bank & 0x3F) * 0x10000 + addr
# For $80:B461: offset = 0 * 0x10000 + 0xB461 = 0xB461 (what current code uses)
# For $80:8CAC: offset = 0 * 0x10000 + 0x8CAC = 0x8CAC
print()
print('Current mapping at $80:8CAC (offset 0x8CAC):')
print(' '.join(f'{rom[0x8CAC+i]:02x}' for i in range(24)))

# LoROM mapping for $80:8CAC
lo_offset2 = 0x0CAC
print(f'LoROM mapping at $80:8CAC (offset 0x{lo_offset2:X}):')
print(' '.join(f'{rom[lo_offset2+i]:02x}' for i in range(24)))

# Now try a completely different mapping: what if bank $80 = offset 0x800000?
# Actually for >4MB games, there's ExHiROM etc
# Let's check the ROM header at different standard positions
print()
print('Header at offset 0xFFC0:', ' '.join(f'{rom[i]:02x}' for i in range(0xFFC0, 0xFFD0)))
print('Header at offset 0x7FC0:', ' '.join(f'{rom[i]:02x}' for i in range(0x7FC0, 0x7FD0)))
print('Header at offset 0x40FFC0:', ' '.join(f'{rom[i]:02x}' for i in range(0x40FFC0, 0x40FFD0) if i < len(rom)))
print('Header at offset 0x407FC0:', ' '.join(f'{rom[i]:02x}' for i in range(0x407FC0, 0x407FD0) if i < len(rom)))

# Also check the actual bytes in bank $00 at addr B461
print()
print('Bank $00, addr $B461 (offset 0x00B461):')
# For LoROM bank $00: offset = 0 * 0x8000 + (B461 & 0x7FFF) = 0x3461
# Actually no - bank $00 is at 0x000000-0x007FFF in LoROM, with only $8000-$FFFF accessible
# The addr part is $8000-$FFFF so subtract $8000: B461 - 8000 = 3461
print('  Same as LoROM, offset 0x3461:', ' '.join(f'{rom[0x3461+i]:02x}' for i in range(10)))
