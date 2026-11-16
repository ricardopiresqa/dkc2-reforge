"""Dump boot code from both candidate RESET vectors."""

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

# Option 1: RESET vector from $3FFFC = 0xFB4F -> $00:FB4F
# HiROM bank 0: $8000-$FFFF map to ROM offset 0 + (addr - $8000)
# $00:FB4F -> ROM offset = FB4F - 8000 = 7B4F
boot1 = 0x7B4F
print(f"=== Boot candidate 1: RESET=0xFB4F, ROM offset 0x{boot1:06X} (HiROM \$00:FB4F) ===")
for i in range(0, 256, 16):
    chunk = rom[boot1+i:boot1+i+16]
    hexs = ' '.join(f'{b:02X}' for b in chunk)
    print(f'{boot1+i:06X}: {hexs}')

# Option 2: rom_map.py said RESET=$80:83F7
# HiROM bank $80 -> ROM offset = (($80 & 0x7F) << 16) | $83F7 = 0x0083F7
boot2 = 0x0083F7
print(f"\n=== Boot candidate 2: RESET=0x83F7 (bank \$80), ROM offset 0x{boot2:06X} ===")
for i in range(0, 256, 16):
    chunk = rom[boot2+i:boot2+i+16]
    hexs = ' '.join(f'{b:02X}' for b in chunk)
    print(f'{boot2+i:06X}: {hexs}')

# Option 3: also check $00:83F7 via HiROM mapping
# Actually $00:83F7 -> ROM = (0*0x8000)+(0x83F7-0x8000) = 0x03F7
boot3 = 0x03F7
print(f"\n=== Boot candidate 3: $00:83F7, ROM offset 0x{boot3:06X} ===")
for i in range(0, 128, 16):
    chunk = rom[boot3+i:boot3+i+16]
    hexs = ' '.join(f'{b:02X}' for b in chunk)
    print(f'{boot3+i:06X}: {hexs}')

# Also dump the native mode vectors
print(f"\n=== Vectors at \$C0:FFE4 (ROM 0x{0x3FFFE4:06X}) ===")
for off in [0x3FFFE4, 0x3FFFF4]:
    chunk = rom[off:off+16]
    hexs = ' '.join(f'{b:02X}' for b in chunk)
    print(f'{off:06X}: {hexs}')

# NMI / RESET / IRQ / COP vectors
for vec_name, vec_off in [('COP', 0xFFE4), ('BRK', 0xFFE6), ('ABORT', 0xFFE8),
                          ('NMI', 0xFFEA), ('RESET', 0xFFFC), ('IRQ', 0xFFEE)]:
    val = rom[0x3FFFE0 + vec_off - 0xFFE4] | (rom[0x3FFFE0 + vec_off - 0xFFE4 + 1] << 8)  
    # Actually the vectors are at specific offsets in the last bank
    # Mode 31 HiROM: vectors at $FFE4-$FFFF of the last bank
    # $C0:FFE4-$C0:FFFF -> ROM offset $3FFFE4-$3FFFFF
    # But $00:FFE4-$00:FFFF also reads from $C0:FFE4-$C0:FFFF
    pass

# Just read the vectors directly
print()
for name, voff in [('COP', 0xFFE4), ('BRK', 0xFFE6), ('ABORT', 0xFFE8), 
                   ('NMI', 0xFFEA), ('RST', 0xFFEA+2), ('IRQ', 0xFFEE),
                   ('COP_E', 0xFFF4), ('BRK_E', 0xFFF6), ('ABORT_E', 0xFFF8),
                   ('NMI_E', 0xFFFA), ('RST_E', 0xFFFC), ('IRQ_E', 0xFFFE)]:
    val = rom[0x3FFFE0 + voff - 0xFFE4] | (rom[0x3FFFE0 + voff - 0xFFE4 + 1] << 8)
    print(f'  {name}: 0x{val:04X}')
