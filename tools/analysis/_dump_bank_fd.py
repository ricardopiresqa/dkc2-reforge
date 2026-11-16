"""Dump bank FD to understand its data structure."""
with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

print('=== Bank FD (0x3D0000-0x3D00FF) ===')
for i in range(0, 256, 16):
    chunk = rom[0x3D0000+i:0x3D0000+i+16]
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    hex_str = ' '.join(f'{b:02x}' for b in chunk)
    print(f'{0x3D0000+i:06X}: {hex_str}  {ascii_str}')

print()
print('=== FD:8000 (0x3D8000-0x3D80FF) ===')
for i in range(0, 256, 16):
    chunk = rom[0x3D8000+i:0x3D8000+i+16]
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    hex_str = ' '.join(f'{b:02x}' for b in chunk)
    print(f'{0x3D8000+i:06X}: {hex_str}  {ascii_str}')

# Also check what's at FD:A000+ (data section)
print()
print('=== FD:A000 (0x3DA000-0x3DA0FF) ===')
for i in range(0, 256, 16):
    chunk = rom[0x3DA000+i:0x3DA000+i+16]
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    hex_str = ' '.join(f'{b:02x}' for b in chunk)
    print(f'{0x3DA000+i:06X}: {hex_str}  {ascii_str}')
