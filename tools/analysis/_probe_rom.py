"""Probe the new ROM for disassembly signature compatibility."""
with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

# Try multiple addressing interpretations for FD:8000
tests = [
    ('HiROM (bank-0xC0)*0x10000+0x8000', (0xFD - 0xC0) * 0x10000 + 0x8000),
    ('HiROM (bank-0xC0)*0x10000', (0xFD - 0xC0) * 0x10000),
    ('ExHiROM (bank-0x40)*0x10000+0x8000', (0xFD - 0x40) * 0x10000 + 0x8000),
    ('LoROM (bank-0x80)*0x8000', (0xFD - 0x80) * 0x8000),
    ('offset 0xFFC0', 0xFFC0),
]
for label, offset in tests:
    if offset < len(rom):
        sig = rom[offset:offset+8]
        print(f'{label}: {hex(offset)} sig={sig.hex()}')

# Scan for the disassembly's FD8000 signature
target = bytes.fromhex('cc81cc816c848484')
results = []
for i in range(len(rom) - 8):
    if rom[i:i+8] == target:
        results.append(hex(i))
if results:
    print(f'\nSignature found at: {", ".join(results)}')
else:
    print('\nSignature NOT FOUND anywhere in ROM')

# Check header
print(f'\nROM type@FFD5: {hex(rom[0xFFD5])}')
print(f'ROM sub@FFD6: {hex(rom[0xFFD6])}')
print(f'Size exp@FFD7: {hex(rom[0xFFD7])}')
print(f'Version@FFDB: {hex(rom[0xFFDB])}')
print(f'Header (0xFFC0-0xFFDF): {rom[0xFFC0:0xFFE0].hex()}')
