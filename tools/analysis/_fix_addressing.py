"""Verify HiROM addressing for DKC2 and fix snes_to_rom / rom_to_snes."""
import hashlib

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

ROM_SIZE = len(rom)  # 4MB
print(f'ROM size: {ROM_SIZE} bytes = {ROM_SIZE // 1024}KB')
print(f'MD5: {hashlib.md5(rom).hexdigest()}')

# SNES header
hdr = rom[0xFFC0:0xFFE0]
rom_type = hdr[0x15]  # FFD5
print(f'ROM type @FFD5: {hex(rom_type)} (bit4=HiROM: {bool(rom_type & 0x10)})')

# For HiROM, the standard mapping for C0-FF banks:
# SNES $C0:0000-$C0:FFFF <-> ROM 0x000000-0x00FFFF
# SNES $C1:0000-$C1:FFFF <-> ROM 0x010000-0x01FFFF
# ...
# SNES $FF:0000-$FF:FFFF <-> ROM 0x3F0000-0x3FFFFF
#
# So: ROM offset = (SNES_bank - 0xC0) * 0x10000 + offset_within_bank
# For SNES $FD:8000: ROM offset = (0xFD - 0xC0) * 0x10000 + 0x8000 = 0x3D8000

def hirom_snes_to_rom(snes_addr):
    """Convert SNES HiROM address to ROM offset."""
    bank = (snes_addr >> 16) & 0xFF
    offset = snes_addr & 0xFFFF
    
    if 0xC0 <= bank <= 0xFF:
        # Direct mapped: ROM offset = (bank - 0xC0) * 0x10000 + offset
        rom_off = (bank - 0xC0) * 0x10000 + offset
    elif 0x80 <= bank <= 0xBF:
        # Mirrors of 0x00-0x3F
        rom_off = ((bank & 0x3F) * 0x8000) + (offset - 0x8000) if offset >= 0x8000 else None
    elif 0x40 <= bank <= 0x7F:
        # Direct mapped for 64KB banks
        rom_off = (bank - 0x40) * 0x10000 + offset
    elif 0x00 <= bank <= 0x3F:
        # $8000-$FFFF only
        rom_off = (bank * 0x8000) + (offset - 0x8000) if offset >= 0x8000 else None
    else:
        return None
    
    if rom_off is not None and (rom_off < 0 or rom_off >= ROM_SIZE):
        return None
    return rom_off

def hirom_rom_to_snes(rom_off):
    """Convert ROM offset to SNES HiROM address."""
    if rom_off < 0 or rom_off >= ROM_SIZE:
        return None
    
    # Banks C0-FF: direct mapped
    # ROM offset 0x000000-0x3FFFFF -> SNES $C0:0000-$FF:FFFF
    snes_bank = 0xC0 + (rom_off // 0x10000)
    snes_offset = rom_off % 0x10000
    snes_addr = (snes_bank << 16) | snes_offset
    return snes_addr

# Verify against known addresses
tests = [
    ('ROM start', 0x000000, '$C0:0000'),
    ('ROM end-1', 0x3FFFFF, '$FF:FFFF'),
    ('Header', 0x3FFFC0, '$FF:C000'),
    ('Reset vector', 0x3FFFFC, '$FF:FFFC'),
    ('Bank FD', 0x3D0000, '$FD:0000'),
    ('Bank BB (LoROM area)', 0x3B0000, '$FB:0000 if hirom'),
]

print('\n=== Addressing verification ===')
for name, rom_off, expected_snes in tests:
    snes = hirom_rom_to_snes(rom_off)
    if snes:
        snes_str = f'${snes:06X}'
    else:
        snes_str = 'None'
    print(f'  {name}: ROM {rom_off:#08x} -> SNES {snes_str} (expected {expected_snes})')

# Verify that reset vector points to valid ROM
reset_vec = rom[0xFFFC] | (rom[0xFFFD] << 8)
print(f'\nReset vector: ${reset_vec:04X}')
# The reset vector is a 16-bit address with implied bank $00 for emulation
# For HiROM, the code typically starts at $80:8000+  
# The reset vector $83F7 means bank $80 (mirrored) or $00 (if in first 32KB?)
print(f'  In HiROM, reset vector ${reset_vec:04X} at bank ${(reset_vec >> 16) & 0xFF:#04x} offset ${reset_vec & 0xFFFF:04X}')

# Check common DKC2 code starting positions
print('\n=== Code area checks ===')
for snes_addr, label in [
    (0x808000, 'Main code start (typical HiROM)'),
    (0x8083F7, 'Reset handler (vector target)'),
    (0x00FFC0, 'Header via bank 00'),
    (0xC0FFC0, 'Header via bank C0'),
]:
    rom_off = hirom_snes_to_rom(snes_addr)
    if rom_off is not None:
        b = rom[rom_off:rom_off+4]
        print(f'  SNES ${snes_addr:06X} -> ROM {rom_off:#08x}: {b.hex()} ({label})')

# Show what the disassembly bank addresses map to
print('\n=== Disassembly bank mapping ===')
for bank in ['BB', 'FD', 'F9', 'B5', 'B3']:
    snes_bank = int(bank, 16)
    if snes_bank >= 0xC0:
        rom_start = (snes_bank - 0xC0) * 0x10000
    elif snes_bank >= 0x80:
        rom_start = (snes_bank & 0x3F) * 0x8000
    else:
        rom_start = None
    if rom_start is not None and rom_start < ROM_SIZE:
        b = rom[rom_start:rom_start+4]
        print(f'  Bank ${bank}: SNES ${bank}:8000 -> ROM {rom_start:#08x}+8000: {b.hex()}')

# Dump bank FD entirely
print('\n=== Bank FD (SNES $FD:0000-$FD:FFFF -> ROM 0x3D0000-0x3DFFFF) ===')
for i in range(0, 0x10000, 16):
    chunk = rom[0x3D0000+i:0x3D0000+i+16]
    if any(b != 0 for b in chunk):
        print(f'  {0x3D0000+i:06X}: {" ".join(f"{b:02x}" for b in chunk)}')
    else:
        # Print first zero line then skip
        pass

print('\nFirst 64 non-zero bytes:')
count = 0
for i in range(0, 0x10000, 1):
    b = rom[0x3D0000+i]
    if b != 0:
        print(f'  {0x3D0000+i:06X}: {b:02x}')
        count += 1
        if count >= 64:
            break
