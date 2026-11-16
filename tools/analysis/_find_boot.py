"""Find the real boot code by searching for 65816 init sequences."""

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

def hexs(b):
    return ' '.join(f'{x:02X}' for x in b)

patterns = [
    (b'\x78\xe2\x20', 'SEI, SEP #20 (8-bit A)'),
    (b'\x78\xc2\x10', 'SEI, REP #10 (16-bit XY)'),
    (b'\x78\x18\xfb', 'SEI, CLC, XCE'),
    (b'\x78\xa9\x00', 'SEI, LDA #00'),
    (b'\x78\x9c', 'SEI, STZ abs'),
    (b'\x78\x8e', 'SEI, STX abs'),
    (b'\x78\x4c', 'SEI, JMP'),
    (b'\x78\x20', 'SEI, JSR'),
    (b'\x78\x5c', 'SEI, JML'),
    (b'\x78\xd8', 'SEI, CLD'),
    (b'\x78\xf8', 'SEI, SED'),
    (b'\xe2\x20', 'SEP #20 (switch to 8-bit A)'),
    (b'\xc2\x10', 'REP #10 (switch to 16-bit XY)'),
]

print("Searching for 65816 boot patterns...")
for pattern, desc in patterns:
    pos = 0
    while True:
        idx = rom.find(pattern, pos)
        if idx == -1:
            break
        bank = idx // 0x10000
        off_in_bank = idx % 0x10000
        if 0xFFE4 <= off_in_bank <= 0xFFFF:
            pos = idx + 1
            continue
        print(f'  {desc} at ROM 0x{idx:06X} (bank {bank:02X}, offset {off_in_bank:04X})')
        print(f'    {hexs(rom[idx:idx+32])}')
        pos = idx + 1

# Get RESET vector
rst_val = rom[0x00FFE4+24] | (rom[0x00FFE4+25] << 8)
print(f'\nRESET vector value: 0x{rst_val:04X}')

if rst_val >= 0x8000:
    rom_off_b0 = rst_val - 0x8000
else:
    rom_off_b0 = rst_val
print(f'  HiROM bank 0 -> ROM 0x{rom_off_b0:06X}')
print(f'    {hexs(rom[rom_off_b0:rom_off_b0+32])}')

# Scan banks E0-FF for code headers
print(f'\nScanning banks E0-FF for code headers...')
for bank in range(0xE0, 0x100):
    base = (bank - 0xE0) * 0x10000 + 0x200000
    if base >= len(rom):
        continue
    chunk = rom[base:base+16]
    if chunk[0] in (0x78, 0x18, 0xA9, 0xC2, 0xE2, 0x20, 0x4C, 0x5C, 0x80):
        print(f'  Bank {bank:02X} (ROM 0x{base:06X}) starts with {hexs(chunk[:16])}')

# Search for SA-1 init patterns (STZ/LDA/STA to $22xx)
print(f'\nSearching for SA-1 init pattern...')
for i in range(len(rom)-4):
    if rom[i] == 0x9C and i+2 < len(rom) and (rom[i+1] & 0xF0) == 0x20 and rom[i+2] == 0x22:
        ctx = rom[max(0,i-4):i+12]
        print(f'  STZ $22{rom[i+1]:02X} at ROM 0x{i:06X}: {hexs(ctx)}')
    if rom[i] == 0xA9 and i+4 < len(rom) and rom[i+2] == 0x8D and (rom[i+3] & 0xF0) == 0x20 and rom[i+4] == 0x22:
        ctx = rom[i:i+8]
        print(f'  LDA# STA $22{rom[i+3]:02X} at ROM 0x{i:06X}: {hexs(ctx)}')
    if rom[i] == 0x8D and i+2 < len(rom) and (rom[i+1] & 0xF0) == 0x20 and rom[i+2] == 0x22:
        ctx = rom[max(0,i-4):i+12]
        if i < 4 or rom[i-1] not in (0x8D, 0x9C, 0xA9):
            print(f'  STA $22{rom[i+1]:02X} at ROM 0x{i:06X}: {hexs(ctx)}')

# Also search for the NMI handler at the native NMI vector value
nmi_val = rom[0x00FFE4+6] | (rom[0x00FFE4+7] << 8)
print(f'\nNative NMI vector: 0x{nmi_val:04X}')
# In HiROM, NMI fetches from $00:FFEA but redirects
# NMI handler would execute at this bank+address
# Native NMI runs with K=0 or whatever the current bank is
nmi_rom = nmi_val & 0xFFFF  # offset within bank
print(f'  NMI code at offset 0x{nmi_rom:04X} within bank')
# Try bank 0 first
print(f'  Bank 0: ROM 0x{nmi_rom:06X}')
print(f'    {hexs(rom[nmi_rom:nmi_rom+32])}')

# For SA-1: the NMI might be in an extended bank
# Check if the native NMI bank is stored differently
# Some HiROM carts use $80 as the NMI bank
nmi_full = 0x800000 | nmi_val  # assume bank 80
print(f'  Bank 80: ROM 0x{(0x800000 | nmi_val) & 0x3FFFFF:06X}')
print(f'    {hexs(rom[((0x80 & 0x7F) << 16 | nmi_val) & 0x3FFFFF:((0x80 & 0x7F) << 16 | nmi_val) & 0x3FFFFF+32] if ((0x80 & 0x7F) << 16 | nmi_val) & 0x3FFFFF+32 < len(rom) else "oob")}')
