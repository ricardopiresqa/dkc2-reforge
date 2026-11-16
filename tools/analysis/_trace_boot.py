"""Trace the boot code to find SA-1 initialization and BW-RAM copy."""

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

def hexs(b):
    return ' '.join(f'{x:02X}' for x in b)

# Full disass from boot start
print("=== Full disassembly of boot code ===")
print("(emulation mode at reset, then switches to native)\n")

boot_rom = 0x0083F7
pos = boot_rom

# Track for branch targets
labels = set()
instrs = []

# First pass: find all branch targets
for p in range(boot_rom, boot_rom + 0x1000):
    b = rom[p]
    if b == 0x4C:  # JMP abs -> 3 bytes
        target = rom[p+1] | (rom[p+2] << 8)
        labels.add(boot_rom + (target - 0x83F7))  # normalize to ROM offset
        p += 3
    elif b == 0x5C:  # JML long -> 4 bytes
        target = rom[p+1] | (rom[p+2] << 8) | (rom[p+3] << 16)
        # If target is in bank 80, convert to ROM offset
        if (target & 0xFF0000) == 0x800000:
            labels.add(((target & 0x7F) << 16 | (target & 0xFFFF)) & 0x3FFFFF)
        p += 4
    elif b == 0x20:  # JSR abs -> 3 bytes
        target = rom[p+1] | (rom[p+2] << 8)
        labels.add(boot_rom + (target - 0x83F7))
        p += 3
    elif b == 0x22:  # JSL long -> 4 bytes
        target = rom[p+1] | (rom[p+2] << 8) | (rom[p+3] << 16)
        if (target & 0xFF0000) == 0x800000:
            labels.add(((target & 0x7F) << 16 | (target & 0xFFFF)) & 0x3FFFFF)
        p += 4
    elif b == 0x80:  # BRA rel
        rel = rom[p+1]
        target = p + 2 + (rel if rel < 128 else rel - 256)
        labels.add(target)
        p += 2
    elif b == 0x82:  # BRL rel16
        rel = rom[p+1] | (rom[p+2] << 8)
        target = p + 3 + (rel if rel < 32768 else rel - 65536)
        labels.add(target)
        p += 3
    elif b in (0xF0, 0xD0, 0x30, 0xB0, 0x90, 0x70, 0x50, 0x10):  # BEQ/BNE/BMI/BCS/BCC/BVS/BVC/BPL
        rel = rom[p+1]
        target = p + 2 + (rel if rel < 128 else rel - 256)
        labels.add(target)
        p += 2
    elif b == 0x00:  # BRK
        p += 2
    else:
        p += 1

# Second pass: print
pos = boot_rom
end = boot_rom + 0x1000
while pos < end:
    if pos in labels and pos != boot_rom:
        print(f'\n; === label at ROM 0x{pos:06X} (SNES ${80:02X}:{0x83F7 + pos - boot_rom:04X}) ===')
    
    b = rom[pos]
    
    # SA-1 register write detection
    def note_sa1(addr, desc):
        if 0x2200 <= addr <= 0x22FF:
            return f'  ; SA-1: {desc}'
        if 0x2220 <= addr <= 0x223F:
            return f'  ; SA-1: {desc}'
        return ''
    
    # Detect COP (actually JML instruction)
    # In emulation mode, 0x02 is COP, in native mode 0x22 is JSL
    # 0x5C = JML
    
    if b == 0x78:
        print(f'  {pos:06X}: SEI')
        pos += 1
    elif b == 0x18:
        print(f'  {pos:06X}: CLC')
        pos += 1
    elif b == 0xFB:
        print(f'  {pos:06X}: XCE')
        pos += 1
    elif b == 0xD8:
        print(f'  {pos:06X}: CLD')
        pos += 1
    elif b == 0x58:
        print(f'  {pos:06X}: CLI')
        pos += 1
    elif b == 0x38:
        print(f'  {pos:06X}: SEC')
        pos += 1
    elif b == 0x3A:
        print(f'  {pos:06X}: DEC')
        pos += 1
    elif b == 0x1A:
        print(f'  {pos:06X}: INC')
        pos += 1
    elif b == 0x7B:
        print(f'  {pos:06X}: TDC')
        pos += 1
    elif b == 0x0B:
        print(f'  {pos:06X}: PHD')
        pos += 1
    elif b == 0x4B:
        print(f'  {pos:06X}: PHK')
        pos += 1
    elif b == 0xAB:
        print(f'  {pos:06X}: PLB')
        pos += 1
    elif b == 0xBB:
        print(f'  {pos:06X}: TYX (or TYB?)')
        pos += 1
    elif b == 0x5B:
        print(f'  {pos:06X}: TCD')
        pos += 1
    elif b == 0x1B:
        print(f'  {pos:06X}: TCS')
        pos += 1
    elif b == 0x48:
        print(f'  {pos:06X}: PHA')
        pos += 1
    elif b == 0x68:
        print(f'  {pos:06X}: PLA')
        pos += 1
    elif b == 0xDA:
        print(f'  {pos:06X}: PHX')
        pos += 1
    elif b == 0xFA:
        print(f'  {pos:06X}: PLX')
        pos += 1
    elif b == 0x5A:
        print(f'  {pos:06X}: PHY')
        pos += 1
    elif b == 0x7A:
        print(f'  {pos:06X}: PLY')
        pos += 1
    elif b == 0xE2:
        imm = rom[pos+1]
        print(f'  {pos:06X}: SEP #${imm:02X}')
        pos += 2
    elif b == 0xC2:
        imm = rom[pos+1]
        print(f'  {pos:06X}: REP #${imm:02X}')
        pos += 2
    elif b == 0xA9:
        imm = rom[pos+1]
        m = note_sa1(0, '')
        extra = ''
        if imm in (0x80, 0x81, 0x82, 0x00, 0x01):
            # Check next instruction
            if pos+2 < len(rom) and rom[pos+2] in (0x8D, 0x8F):
                pass  # will be handled by STA
        print(f'  {pos:06X}: LDA #${imm:02X} {extra}')
        pos += 2
    elif b == 0xA5:
        dp = rom[pos+1]
        print(f'  {pos:06X}: LDA ${dp:02X}')
        pos += 2
    elif b == 0xA6:
        dp = rom[pos+1]
        print(f'  {pos:06X}: LDX ${dp:02X}')
        pos += 2
    elif b == 0x8D:
        addr = rom[pos+1] | (rom[pos+2] << 8)
        sa1 = note_sa1(addr, f'STA ${addr:04X}')
        print(f'  {pos:06X}: STA ${addr:04X}{sa1}')
        pos += 3
    elif b == 0x8F:
        addr = rom[pos+1] | (rom[pos+2] << 8) | (rom[pos+3] << 16)
        sa1 = note_sa1(addr & 0xFFFF, f'STA ${addr:06X}')
        print(f'  {pos:06X}: STA ${addr:06X}{sa1}')
        pos += 4
    elif b == 0xAD:
        addr = rom[pos+1] | (rom[pos+2] << 8)
        print(f'  {pos:06X}: LDA ${addr:04X}')
        pos += 3
    elif b == 0xAF:
        addr = rom[pos+1] | (rom[pos+2] << 8) | (rom[pos+3] << 16)
        print(f'  {pos:06X}: LDA ${addr:06X}')
        pos += 4
    elif b == 0x9C:
        addr = rom[pos+1] | (rom[pos+2] << 8)
        sa1 = note_sa1(addr, f'STZ ${addr:04X}')
        print(f'  {pos:06X}: STZ ${addr:04X}{sa1}')
        pos += 3
    elif b == 0x5C:
        dest = rom[pos+1] | (rom[pos+2] << 8) | (rom[pos+3] << 16)
        print(f'  {pos:06X}: JML ${dest:06X}')
        pos += 4
    elif b == 0x22:
        dest = rom[pos+1] | (rom[pos+2] << 8) | (rom[pos+3] << 16)
        print(f'  {pos:06X}: JSL ${dest:06X}')
        pos += 4
    elif b == 0x4C:
        dest = rom[pos+1] | (rom[pos+2] << 8)
        print(f'  {pos:06X}: JMP ${dest:04X}')
        pos += 3
    elif b == 0x20:
        dest = rom[pos+1] | (rom[pos+2] << 8)
        print(f'  {pos:06X}: JSR ${dest:04X}')
        pos += 3
    elif b == 0x60:
        print(f'  {pos:06X}: RTS')
        pos += 1
    elif b == 0x6B:
        print(f'  {pos:06X}: RTL')
        pos += 1
    elif b == 0x40:
        print(f'  {pos:06X}: RTI')
        pos += 1
    elif b == 0xA2:
        imm = rom[pos+1]
        # 8-bit or 16-bit depending on X flag
        print(f'  {pos:06X}: LDX #${imm:02X}')
        pos += 2
    elif b == 0xA0:
        imm = rom[pos+1]
        print(f'  {pos:06X}: LDY #${imm:02X}')
        pos += 2
    elif b == 0xF0:
        rel = rom[pos+1]
        t = pos+2+(rel if rel<128 else rel-256)
        print(f'  {pos:06X}: BEQ ${t:06X}')
        pos += 2
    elif b == 0xD0:
        rel = rom[pos+1]
        t = pos+2+(rel if rel<128 else rel-256)
        print(f'  {pos:06X}: BNE ${t:06X}')
        pos += 2
    elif b == 0x30:
        rel = rom[pos+1]
        t = pos+2+(rel if rel<128 else rel-256)
        print(f'  {pos:06X}: BMI ${t:06X}')
        pos += 2
    elif b == 0x10:
        rel = rom[pos+1]
        t = pos+2+(rel if rel<128 else rel-256)
        print(f'  {pos:06X}: BPL ${t:06X}')
        pos += 2
    elif b == 0xB0:
        rel = rom[pos+1]
        t = pos+2+(rel if rel<128 else rel-256)
        print(f'  {pos:06X}: BCS ${t:06X}')
        pos += 2
    elif b == 0x90:
        rel = rom[pos+1]
        t = pos+2+(rel if rel<128 else rel-256)
        print(f'  {pos:06X}: BCC ${t:06X}')
        pos += 2
    elif b == 0x80:
        rel = rom[pos+1]
        t = pos+2+(rel if rel<128 else rel-256)
        print(f'  {pos:06X}: BRA ${t:06X}')
        pos += 2
    elif b == 0x82:
        rel = rom[pos+1] | (rom[pos+2] << 8)
        t = pos+3+(rel if rel<32768 else rel-65536)
        print(f'  {pos:06X}: BRL ${t:06X}')
        pos += 3
    elif b == 0xC9:
        imm = rom[pos+1]
        print(f'  {pos:06X}: CMP #${imm:02X}')
        pos += 2
    elif b == 0xE0:
        imm = rom[pos+1]
        print(f'  {pos:06X}: CPX #${imm:02X}')
        pos += 2
    elif b == 0x9B:
        print(f'  {pos:06X}: TXY')
        pos += 1
    elif b == 0xBB:
        print(f'  {pos:06X}: TYX')
        pos += 1
    elif b == 0xFB:
        print(f'  {pos:06X}: XCE')
        pos += 1
    elif b == 0xBA:
        print(f'  {pos:06X}: TSX')
        pos += 1
    elif b == 0x8A:
        print(f'  {pos:06X}: TXA')
        pos += 1
    elif b == 0x9A:
        print(f'  {pos:06X}: TXS')
        pos += 1
    elif b == 0x98:
        print(f'  {pos:06X}: TYA')
        pos += 1
    elif b == 0xEB:
        print(f'  {pos:06X}: XBA (or SWA)')
        pos += 1
    elif b in (0x08, 0x28, 0x88, 0xCA, 0xE8, 0xC8, 0xE6, 0xC6, 0xCE, 0xEE, 0x4A, 0x0A, 0x2A, 0x6A, 0x89, 0x24, 0x26, 0x46, 0x66, 
               0x06, 0x16, 0x0E, 0x1E, 0x00, 0x01, 0xEA, 0x14, 0x04, 0x34, 0x44, 0x54, 0x64, 0x74, 0x84, 0x94, 0x7C, 0xFC, 0x6C):
        if b == 0x08:
            print(f'  {pos:06X}: PHP')
        elif b == 0x28:
            print(f'  {pos:06X}: PLP')
        elif b == 0x88:
            print(f'  {pos:06X}: DEY')
        elif b == 0xCA:
            print(f'  {pos:06X}: DEX')
        elif b == 0xE8:
            print(f'  {pos:06X}: INX')
        elif b == 0xC8:
            print(f'  {pos:06X}: INY')
        elif b == 0xEA:
            print(f'  {pos:06X}: NOP')
        elif b == 0x00:
            print(f'  {pos:06X}: BRK #{rom[pos+1]:02X}')
            pos += 2
            continue
        else:
            print(f'  {pos:06X}: {b:02X} (implied)')
        pos += 1
    elif b == 0x6C:
        addr = rom[pos+1] | (rom[pos+2] << 8)
        print(f'  {pos:06X}: JMP (${addr:04X})')
        pos += 3
    elif b == 0x7C:
        addr = rom[pos+1] | (rom[pos+2] << 8)
        print(f'  {pos:06X}: JMP (${addr:04X},X)')
        pos += 3
    elif b == 0xCF:
        addr = rom[pos+1] | (rom[pos+2] << 8) | (rom[pos+3] << 16)
        print(f'  {pos:06X}: CMP ${addr:06X}')
        pos += 4
    elif b == 0xDB:
        print(f'  {pos:06X}: STP')
        pos += 1
    elif b == 0xCB:
        print(f'  {pos:06X}: WAI')
        pos += 1
    elif b == 0xFA:
        print(f'  {pos:06X}: PLX')
        pos += 1
    elif b == 0x7A:
        print(f'  {pos:06X}: PLY')
        pos += 1
    elif b == 0x4B:
        print(f'  {pos:06X}: PHK')
        pos += 1
    elif b == 0xAB:
        print(f'  {pos:06X}: PLB')
        pos += 1
    else:
        print(f'  {pos:06X}: {b:02X} (unknown)')
        pos += 1

    if pos >= boot_rom + 0x1000:
        break
