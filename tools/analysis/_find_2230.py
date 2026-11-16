"""Find actual SA-1 register writes in the ROM."""

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

patterns = {
    'STA $2230': bytes([0x8D, 0x30, 0x22]),
    'STZ $2230': bytes([0x9C, 0x30, 0x22]),
    'STA $2200': bytes([0x8D, 0x00, 0x22]),
    'STZ $2200': bytes([0x9C, 0x00, 0x22]),
    'STA $2224': bytes([0x8D, 0x24, 0x22]),
    'STA $2225': bytes([0x8D, 0x25, 0x22]),
    'STA $2226': bytes([0x8D, 0x26, 0x22]),
    'STZ $2224': bytes([0x9C, 0x24, 0x22]),
    'STA $2235': bytes([0x8D, 0x35, 0x22]),
    'STA $2236': bytes([0x8D, 0x36, 0x22]),
    'STA $2237': bytes([0x8D, 0x37, 0x22]),
    'STA $2238': bytes([0x8D, 0x38, 0x22]),
    'STA $2201': bytes([0x8D, 0x01, 0x22]),
    'STA $2202': bytes([0x8D, 0x02, 0x22]),
    'STA $2203': bytes([0x8D, 0x03, 0x22]),
    'STA $2204': bytes([0x8D, 0x04, 0x22]),
}
for label, pat in patterns.items():
    pos = 0
    count = 0
    while True:
        pos = rom.find(pat, pos)
        if pos < 0:
            break
        count += 1
        print(f"  ROM 0x{pos:06X}: {label}")
        pos += 1
    if count == 0:
        print(f"  (none) for {label}")
