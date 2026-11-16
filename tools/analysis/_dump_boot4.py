"""Disassemble the boot code at bank 80."""

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

def hexs(b):
    return ' '.join(f'{x:02X}' for x in b)

# Check boot at different ROM offsets
# RESET=0x83F7. Could be at $80:83F7 -> ROM 0x0083F7
# Or $00:83F7 -> ROM 0x03F7
rom_off_80 = 0x0083F7  # bank 80 hirom
rom_off_0 = 0x03F7     # bank 0 hirom

print("=== ROM 0x0083F7 (bank 80 mapping) ===")
for i in range(0, 256, 16):
    chunk = rom[rom_off_80+i:rom_off_80+i+16]
    print(f'{rom_off_80+i:06X}: {hexs(chunk)}')

print("\n=== ROM 0x03F7 (bank 0 mapping) ===")
for i in range(0, 256, 16):
    chunk = rom[rom_off_0+i:rom_off_0+i+16]
    print(f'{rom_off_0+i:06X}: {hexs(chunk)}')

# Check if the RESET code uses JML to jump to another location
# Look for JML opcode 0x5C followed by a 3-byte address
rst = 0x03F7
print(f"\n=== RESET code at ROM 0x{rst:06X} (disassembly attempt) ===")
# 65816 emulation mode at boot, so we use 8-bit flags
pos = rst
while pos < rst + 64:
    b = rom[pos]
    if b == 0x5C:  # JML long
        dest = rom[pos+1] | (rom[pos+2] << 8) | (rom[pos+3] << 16)
        print(f'  {pos:06X}: JML ${dest:06X}')
        pos += 4
    elif b == 0x22:  # JSL long
        dest = rom[pos+1] | (rom[pos+2] << 8) | (rom[pos+3] << 16)
        print(f'  {pos:06X}: JSL ${dest:06X}')
        pos += 4
    elif b == 0x4C:  # JMP abs
        dest = rom[pos+1] | (rom[pos+2] << 8)
        print(f'  {pos:06X}: JMP ${dest:04X}')
        pos += 3
    elif b == 0x20:  # JSR abs
        dest = rom[pos+1] | (rom[pos+2] << 8)
        print(f'  {pos:06X}: JSR ${dest:04X}')
        pos += 3
    elif b == 0x60:  # RTS
        print(f'  {pos:06X}: RTS')
        pos += 1
    elif b == 0x6B:  # RTL
        print(f'  {pos:06X}: RTL')
        pos += 1
    elif b == 0x40:  # RTI
        print(f'  {pos:06X}: RTI')
        pos += 1
    elif b == 0xA9:  # LDA #imm
        imm = rom[pos+1]
        print(f'  {pos:06X}: LDA #${imm:02X}')
        pos += 2
    elif b == 0x8D:  # STA abs
        addr = rom[pos+1] | (rom[pos+2] << 8)
        print(f'  {pos:06X}: STA ${addr:04X}')
        pos += 3
    elif b == 0x8F:  # STA long
        addr = rom[pos+1] | (rom[pos+2] << 8) | (rom[pos+3] << 16)
        print(f'  {pos:06X}: STA ${addr:06X}')
        pos += 4
    elif b == 0x9C:  # STZ abs
        addr = rom[pos+1] | (rom[pos+2] << 8)
        print(f'  {pos:06X}: STZ ${addr:04X}')
        pos += 3
    elif b == 0x78:  # SEI
        print(f'  {pos:06X}: SEI')
        pos += 1
    elif b == 0x18:  # CLC
        print(f'  {pos:06X}: CLC')
        pos += 1
    elif b == 0x38:  # SEC
        print(f'  {pos:06X}: SEC')
        pos += 1
    elif b == 0xFB:  # XCE
        print(f'  {pos:06X}: XCE')
        pos += 1
    elif b == 0xD8:  # CLD
        print(f'  {pos:06X}: CLD')
        pos += 1
    elif b == 0xE2:  # SEP #imm
        imm = rom[pos+1]
        print(f'  {pos:06X}: SEP #${imm:02X}')
        pos += 2
    elif b == 0xC2:  # REP #imm
        imm = rom[pos+1]
        print(f'  {pos:06X}: REP #${imm:02X}')
        pos += 2
    elif b == 0xC9:  # CMP #imm
        imm = rom[pos+1]
        print(f'  {pos:06X}: CMP #${imm:02X}')
        pos += 2
    elif b == 0xF0:  # BEQ rel
        rel = rom[pos+1]
        print(f'  {pos:06X}: BEQ ${pos+2+rel if rel < 128 else pos+2+rel-256:04X}')
        pos += 2
    elif b == 0xD0:  # BNE rel
        rel = rom[pos+1]
        print(f'  {pos:06X}: BNE ${pos+2+rel if rel < 128 else pos+2+rel-256:04X}')
        pos += 2
    elif b == 0x80:  # BRA rel
        rel = rom[pos+1]
        print(f'  {pos:06X}: BRA ${pos+2+rel if rel < 128 else pos+2+rel-256:04X}')
        pos += 2
    elif b == 0x82:  # BRL rel
        rel = rom[pos+1] | (rom[pos+2] << 8)
        print(f'  {pos:06X}: BRL ${pos+3+rel if rel < 32768 else pos+3+rel-65536:04X}')
        pos += 3
    elif b == 0xAF:  # LDA long
        addr = rom[pos+1] | (rom[pos+2] << 8) | (rom[pos+3] << 16)
        print(f'  {pos:06X}: LDA ${addr:06X}')
        pos += 4
    elif b == 0xAD:  # LDA abs
        addr = rom[pos+1] | (rom[pos+2] << 8)
        print(f'  {pos:06X}: LDA ${addr:04X}')
        pos += 3
    elif b == 0x48:  # PHA
        print(f'  {pos:06X}: PHA')
        pos += 1
    elif b == 0xDA:  # PHX
        print(f'  {pos:06X}: PHX')
        pos += 1
    elif b == 0x5A:  # PHY
        print(f'  {pos:06X}: PHY')
        pos += 1
    elif b == 0x68:  # PLA
        print(f'  {pos:06X}: PLA')
        pos += 1
    elif b == 0xFA:  # PLX
        print(f'  {pos:06X}: PLX')
        pos += 1
    elif b == 0x7A:  # PLY
        print(f'  {pos:06X}: PLY')
        pos += 1
    elif b == 0x00:  # BRK
        imm = rom[pos+1]
        print(f'  {pos:06X}: BRK #${imm:02X}')
        pos += 2
    else:
        print(f'  {pos:06X}: {b:02X} (unknown)')
        pos += 1

# Now let me also check if bank 80 has a sane program
print("\n=== Bank 80 analysis ===")
base_80 = 0x000000  # ROM offset for bank 80 in HiROM
# Check for code signature: SEI (0x78) is common at start
for off in range(base_80, base_80 + 0x10000, 1):
    if rom[off] == 0x78 and off < len(rom)-8:
        # Check if followed by common boot opcodes
        next_b = rom[off+1]
        if next_b in (0xE2, 0xC2, 0x18, 0xA9, 0xD8, 0xF8, 0x20, 0x4C):
            print(f'  Potential boot at ROM 0x{off:06X}: SEI, {next_b:02X}')

# Check for copy loop pattern: A9 xx 8D xx 22 (LDA #xx STA $22xx, i.e., SA-1 init)
print("\n=== SA-1 init patterns (LDA #xx STA $22xx) ===")
for i in range(0x000000, min(0x100000, len(rom))):
    if rom[i] == 0xA9 and i+4 < len(rom) and rom[i+2] == 0x8D and rom[i+3] == 0x20 and rom[i+4] == 0x22:
        print(f'  ROM 0x{i:06X}: LDA #${rom[i+1]:02X} STA $2220')
    if rom[i] == 0xA9 and i+4 < len(rom) and rom[i+2] == 0x8D and rom[i+3] == 0x21 and rom[i+4] == 0x22:
        print(f'  ROM 0x{i:06X}: LDA #${rom[i+1]:02X} STA $2221 SA-1 bank')
