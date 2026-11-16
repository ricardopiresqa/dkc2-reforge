DOLLAR = chr(36)
with open('../../roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

# Boot code at RESET vector -> ROM 0x83F7 (HiROM mask)
off = 0x83F7
print(f'=== Boot code at ROM 0x{off:06X} ===')
print(f'First 200 bytes (hex):')
for i in range(0, 200, 16):
    row = rom[off+i:off+i+16]
    hex_str = ' '.join(f'{b:02X}' for b in row)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
    print(f'  {off+i:06X}: {hex_str:<48} {ascii_str}')

# Context around SA-1 init at ROM 0x368CD3
print()
off2 = 0x368CD3
start = off2 - 40
print(f'=== Context around SA-1 init at ROM 0x{off2:06X} ===')
for i in range(0, 80, 16):
    addr = start + i
    row = rom[addr:addr+16]
    hex_str = ' '.join(f'{b:02X}' for b in row)
    print(f'  {addr:06X}: {hex_str}')

# Also dump at stz context ROM 0x36F5BA
print()
off3 = 0x36F5BA
start3 = off3 - 40
print(f'=== Context around stz {DOLLAR}2200 at ROM 0x{off3:06X} ===')
for i in range(0, 80, 16):
    addr = start3 + i
    row = rom[addr:addr+16]
    hex_str = ' '.join(f'{b:02X}' for b in row)
    print(f'  {addr:06X}: {hex_str}')
