"""Find SA-1 DMA setup context (around STA $2230 at 0xB3C6)."""

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

# Find the exact positions
targets = {
    'STA $2230': b'\x8D\x30\x22',
    'STA $2235': b'\x8D\x35\x22',
    'STA $2236': b'\x8D\x36\x22',
    'STA $2237': b'\x8D\x37\x22',
    'STA $2238': b'\x8D\x38\x22',
}

for label, pattern in targets.items():
    pos = rom.find(pattern)
    if pos >= 0:
        print(f"\n=== Context around {label} at ROM 0x{pos:06X} ===")
        start = max(0, pos - 30)
        end = min(len(rom), pos + 20)
        for j in range(start, end):
            b = rom[j]
            if b in [0x8D, 0x9C, 0xAD, 0xA9, 0xA2, 0xA0, 0xC2, 0xE2, 0xEA, 0x6B, 0x60, 0x20, 0x4C, 0x22, 0x5C, 0x18, 0x38, 0xE8, 0xC8, 0x88, 0xAA, 0x8A, 0xA8, 0x98, 0x48, 0x68, 0x08, 0x28, 0xDA, 0xFA, 0x5A, 0x7A, 0x1A, 0x3A, 0xCA, 0xD0, 0xF0, 0x80, 0x90, 0xB0, 0x10, 0x30, 0x50, 0x70, 0x85, 0xA5, 0x64, 0x9B, 0xBB]:
                marker = " <<<" if j == pos else ""
                print(f"  ROM 0x{j:06X}: {b:02X} {'' if j == pos else ''} [{' '.join(f'{rom[j+k]:02X}' for k in range(min(4, end-j)))}] {marker}")
