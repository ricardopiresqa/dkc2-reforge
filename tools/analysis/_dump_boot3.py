"""Dump vectors and boot code."""

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

off = 0x00FFE4
print('Vector table at ROM 0x00FFE4:')
for i in range(0, 32, 16):
    chunk = rom[off+i:off+i+16]
    print(f'  +{i:02X}: {" ".join(f"{b:02X}" for b in chunk)}')

print()
print(f'Native NMI: 0x{rom[off+6]|(rom[off+7]<<8):04X}')
print(f'Emul NMI: 0x{rom[off+22]|(rom[off+23]<<8):04X}')
print(f'RESET: 0x{rom[off+24]|(rom[off+25]<<8):04X}')

# Boot code at RESET vector address
# RESET = 0x83F7, bank 0 for emulation mode -> $00:83F7
# HiROM: bank 0 $8000-$FFFF = ROM offset 0x0000 + ($83F7 - $8000) = 0x03F7
rst_val = rom[off+24]|(rom[off+25]<<8)
boot_rom = rst_val - 0x8000  # HiROM bank 0 mapping
print(f'\nBoot code at ROM offset 0x{boot_rom:06X} ($00:{rst_val:04X}):')
for i in range(0, 384, 16):
    chunk = rom[boot_rom+i:boot_rom+i+16]
    print(f'{boot_rom+i:06X}: {" ".join(f"{b:02X}" for b in chunk)}')
