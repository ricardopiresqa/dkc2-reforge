rom = open('roms/dkc2.sfc', 'rb').read()

def r(bank, addr):
    return (bank & 0x3F) * 0x10000 + addr

# $80:8CCE dispatch table
print("=== $80:8CCE dispatch table ===")
off = r(0x80, 0x8CCE)
for i in range(0, 256, 16):
    d = rom[off+i:off+i+16]
    line = ' '.join(f'{b:02X}' for b in d)
    # Check if this looks like JML table (5C xx xx xx)
    jml_count = sum(1 for j in range(0, len(d), 4) if d[j] == 0x5C)
    if jml_count >= 2:
        print(f'  {off+i:06X}: {line}  [JML x{jml_count}]')
    else:
        print(f'  {off+i:06X}: {line}')

# Check what's at $80:8CCE in terms of JSL
print("\n=== $80:8CCE parsing as JSL table ===")
for entry in range(4):
    base = off + entry * 4
    if rom[base] == 0x22:  # JSL
        target = rom[base+1] | (rom[base+2] << 8) | (rom[base+3] << 16)
        print(f'  Entry {entry}: JSL ${target:06X}')
    elif rom[base] == 0x5C:  # JML
        target = rom[base+1] | (rom[base+2] << 8) | (rom[base+3] << 16)
        print(f'  Entry {entry}: JML ${target:06X}')
    else:
        print(f'  Entry {entry}: op=${rom[base]:02X}')

# Check the flow more carefully
# After LDA #$0011 and JSL $B58006, what's the next major section?
print("\n=== Main entry final section ($80:9197+) ===")
off = r(0x80, 0x9197)
for i in range(0, 256, 16):
    d = rom[off+i:off+i+16]
    print(f'  {off+i:06X}: {" ".join(f"{b:02X}" for b in d)}')

# Search for the game loop (infinite loop pattern: BRA *, JMP *, etc.)
print("\n=== Game loop search around $9200-$C000 ===")
games = r(0x80, 0x9200)
# look for BRA -1 pattern (80 FE) or JMP $xxxx (4C xx xx)
for off2 in range(games, r(0x80, 0x9800), 2):
    if rom[off2] == 0x80 and rom[off2+1] == 0xFE:
        print(f'  BRA * found at ROM 0x{off2:06X} (SNES $80:{off2 & 0xFFFF:04X})')
    # Look for JML to same addr
    if rom[off2] == 0x5C:
        target = rom[off2+1] | (rom[off2+2] << 8) | (rom[off2+3] << 16)
        if target & 0xFFFF == off2 & 0xFFFF:
            print(f'  JML self at ROM 0x{off2:06X} (SNES ${target:06X})')
