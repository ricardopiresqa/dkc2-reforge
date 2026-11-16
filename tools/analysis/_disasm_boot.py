import sys

rom = open('roms/dkc2.sfc', 'rb').read()

def disas(data, base=0):
    m, x = 1, 1
    addr = 0
    out = []
    while addr < len(data):
        pos = base + addr
        b = data[addr]
        if addr + 3 >= len(data):
            out.append(f'{pos:06X}: --- end')
            break
        if b == 0x78: out.append(f'{pos:06X}: SEI'); addr += 1
        elif b == 0xA9:
            if m == 0:
                v = data[addr+1] | (data[addr+2] << 8)
                out.append(f'{pos:06X}: LDA #${v:04X}'); addr += 3
            else:
                out.append(f'{pos:06X}: LDA #${data[addr+1]:02X}'); addr += 2
        elif b == 0x8D:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: STA ${v:04X}'); addr += 3
        elif b == 0x8F:
            v = data[addr+1] | (data[addr+2] << 8) | (data[addr+3] << 16)
            out.append(f'{pos:06X}: STA ${v:06X}'); addr += 4
        elif b == 0xAF:
            v = data[addr+1] | (data[addr+2] << 8) | (data[addr+3] << 16)
            out.append(f'{pos:06X}: LDA ${v:06X}'); addr += 4
        elif b == 0xBF:
            v = data[addr+1] | (data[addr+2] << 8) | (data[addr+3] << 16)
            out.append(f'{pos:06X}: LDA ${v:06X},X'); addr += 4
        elif b == 0xCF:
            v = data[addr+1] | (data[addr+2] << 8) | (data[addr+3] << 16)
            out.append(f'{pos:06X}: CMP ${v:06X}'); addr += 4
        elif b == 0x9F:
            v = data[addr+1] | (data[addr+2] << 8) | (data[addr+3] << 16)
            out.append(f'{pos:06X}: STA ${v:06X},X'); addr += 4
        elif b == 0x9C:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: STZ ${v:04X}'); addr += 3
        elif b == 0x9E:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: STZ ${v:04X},X'); addr += 3
        elif b == 0xC2:
            v = data[addr+1]
            if v & 0x20: m = 0
            if v & 0x10: x = 0
            out.append(f'{pos:06X}: REP #${v:02X}'); addr += 2
        elif b == 0xE2:
            v = data[addr+1]
            if v & 0x20: m = 1
            if v & 0x10: x = 1
            out.append(f'{pos:06X}: SEP #${v:02X}'); addr += 2
        elif b == 0x18: out.append(f'{pos:06X}: CLC'); addr += 1
        elif b == 0x38: out.append(f'{pos:06X}: SEC'); addr += 1
        elif b == 0x58: out.append(f'{pos:06X}: CLI'); addr += 1
        elif b == 0x3A: out.append(f'{pos:06X}: DEC'); addr += 1
        elif b == 0x1A: out.append(f'{pos:06X}: INC'); addr += 1
        elif b == 0x7B: out.append(f'{pos:06X}: TDC'); addr += 1
        elif b == 0xFB: out.append(f'{pos:06X}: XCE'); addr += 1
        elif b == 0xBA: out.append(f'{pos:06X}: TSX'); addr += 1
        elif b == 0x9A: out.append(f'{pos:06X}: TXS'); addr += 1
        elif b == 0xAA: out.append(f'{pos:06X}: TAX'); addr += 1
        elif b == 0x8A: out.append(f'{pos:06X}: TXA'); addr += 1
        elif b == 0x98: out.append(f'{pos:06X}: TYA'); addr += 1
        elif b == 0x9B: out.append(f'{pos:06X}: TXY'); addr += 1
        elif b == 0xBB: out.append(f'{pos:06X}: TYX'); addr += 1
        elif b == 0x4B: out.append(f'{pos:06X}: PHK'); addr += 1
        elif b == 0xAB: out.append(f'{pos:06X}: PLB'); addr += 1
        elif b == 0x8B: out.append(f'{pos:06X}: PHB'); addr += 1
        elif b == 0x48: out.append(f'{pos:06X}: PHA'); addr += 1
        elif b == 0x68: out.append(f'{pos:06X}: PLA'); addr += 1
        elif b == 0x5A: out.append(f'{pos:06X}: PHY'); addr += 1
        elif b == 0x7A: out.append(f'{pos:06X}: PLY'); addr += 1
        elif b == 0xDA: out.append(f'{pos:06X}: PHX'); addr += 1
        elif b == 0xFA: out.append(f'{pos:06X}: PLX'); addr += 1
        elif b == 0x08: out.append(f'{pos:06X}: PHP'); addr += 1
        elif b == 0x28: out.append(f'{pos:06X}: PLP'); addr += 1
        elif b == 0xEA: out.append(f'{pos:06X}: NOP'); addr += 1
        elif b == 0x00: out.append(f'{pos:06X}: BRK #${data[addr+1]:02X}'); addr += 2
        elif b == 0x02: out.append(f'{pos:06X}: COP #${data[addr+1]:02X}'); addr += 2
        elif b == 0x69:
            if m == 0:
                v = data[addr+1] | (data[addr+2] << 8)
                out.append(f'{pos:06X}: ADC #${v:04X}'); addr += 3
            else:
                out.append(f'{pos:06X}: ADC #${data[addr+1]:02X}'); addr += 2
        elif b == 0x6D:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: ADC ${v:04X}'); addr += 3
        elif b == 0xED:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: SBC ${v:04X}'); addr += 3
        elif b == 0xE9:
            if m == 0:
                v = data[addr+1] | (data[addr+2] << 8)
                out.append(f'{pos:06X}: SBC #${v:04X}'); addr += 3
            else:
                out.append(f'{pos:06X}: SBC #${data[addr+1]:02X}'); addr += 2
        elif b in (0xF0, 0x10, 0x30, 0xD0, 0x90, 0xB0, 0x80):
            off = data[addr+1]
            if off & 0x80: off -= 0x100
            names = {0xF0:'BEQ',0x10:'BPL',0x30:'BMI',0xD0:'BNE',0x90:'BCC',0xB0:'BCS',0x80:'BRA'}
            out.append(f'{pos:06X}: {names[b]} ${pos+2+off:06X}'); addr += 2
        elif b == 0x82:
            off = data[addr+1] | (data[addr+2] << 8)
            if off & 0x8000: off -= 0x10000
            out.append(f'{pos:06X}: BRL ${pos+3+off:06X}'); addr += 3
        elif b == 0x5C:
            v = data[addr+1] | (data[addr+2] << 8) | (data[addr+3] << 16)
            out.append(f'{pos:06X}: JML ${v:06X}'); addr += 4
        elif b == 0x22:
            v = data[addr+1] | (data[addr+2] << 8) | (data[addr+3] << 16)
            out.append(f'{pos:06X}: JSL ${v:06X}'); addr += 4
        elif b == 0x4C:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: JMP ${v:04X}'); addr += 3
        elif b == 0x6C:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: JMP (${v:04X})'); addr += 3
        elif b == 0x20:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: JSR ${v:04X}'); addr += 3
        elif b == 0xFC:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: JSR (${v:04X},X)'); addr += 3
        elif b == 0x60: out.append(f'{pos:06X}: RTS'); addr += 1
        elif b == 0x6B: out.append(f'{pos:06X}: RTL'); addr += 1
        elif b == 0x40: out.append(f'{pos:06X}: RTI'); addr += 1
        elif b == 0xDD:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: CMP ${v:04X},X'); addr += 3
        elif b == 0xBD:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: LDA ${v:04X},X'); addr += 3
        elif b == 0xB9:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: LDA ${v:04X},Y'); addr += 3
        elif b == 0x9D:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: STA ${v:04X},X'); addr += 3
        elif b == 0x99:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: STA ${v:04X},Y'); addr += 3
        elif b == 0xBE:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: LDX ${v:04X},Y'); addr += 3
        elif b == 0xAD:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: LDA ${v:04X}'); addr += 3
        elif b == 0xA2:
            if x == 0:
                v = data[addr+1] | (data[addr+2] << 8)
                out.append(f'{pos:06X}: LDX #${v:04X}'); addr += 3
            else:
                out.append(f'{pos:06X}: LDX #${data[addr+1]:02X}'); addr += 2
        elif b == 0xA0:
            if x == 0:
                v = data[addr+1] | (data[addr+2] << 8)
                out.append(f'{pos:06X}: LDY #${v:04X}'); addr += 3
            else:
                out.append(f'{pos:06X}: LDY #${data[addr+1]:02X}'); addr += 2
        elif b == 0xE0:
            if x == 0:
                v = data[addr+1] | (data[addr+2] << 8)
                out.append(f'{pos:06X}: CPX #${v:04X}'); addr += 3
            else:
                out.append(f'{pos:06X}: CPX #${data[addr+1]:02X}'); addr += 2
        elif b == 0xC0:
            if x == 0:
                v = data[addr+1] | (data[addr+2] << 8)
                out.append(f'{pos:06X}: CPY #${v:04X}'); addr += 3
            else:
                out.append(f'{pos:06X}: CPY #${data[addr+1]:02X}'); addr += 2
        elif b == 0xC9:
            if m == 0:
                v = data[addr+1] | (data[addr+2] << 8)
                out.append(f'{pos:06X}: CMP #${v:04X}'); addr += 3
            else:
                out.append(f'{pos:06X}: CMP #${data[addr+1]:02X}'); addr += 2
        elif b == 0xC5:
            out.append(f'{pos:06X}: CMP ${data[addr+1]:02X}'); addr += 2
        elif b == 0x29:
            if m == 0:
                v = data[addr+1] | (data[addr+2] << 8)
                out.append(f'{pos:06X}: AND #${v:04X}'); addr += 3
            else:
                out.append(f'{pos:06X}: AND #${data[addr+1]:02X}'); addr += 2
        elif b == 0x09:
            if m == 0:
                v = data[addr+1] | (data[addr+2] << 8)
                out.append(f'{pos:06X}: ORA #${v:04X}'); addr += 3
            else:
                out.append(f'{pos:06X}: ORA #${data[addr+1]:02X}'); addr += 2
        elif b == 0x05:
            out.append(f'{pos:06X}: ORA ${data[addr+1]:02X}'); addr += 2
        elif b == 0x1F:
            v = data[addr+1] | (data[addr+2] << 8) | (data[addr+3] << 16)
            out.append(f'{pos:06X}: ORA ${v:06X},X'); addr += 4
        elif b == 0x03:
            out.append(f'{pos:06X}: ORA (${data[addr+1]:02X},S),Y'); addr += 2
        elif b == 0xA5:
            out.append(f'{pos:06X}: LDA ${data[addr+1]:02X}'); addr += 2
        elif b == 0x85:
            out.append(f'{pos:06X}: STA ${data[addr+1]:02X}'); addr += 2
        elif b == 0x86:
            out.append(f'{pos:06X}: STX ${data[addr+1]:02X}'); addr += 2
        elif b == 0xA6:
            out.append(f'{pos:06X}: LDX ${data[addr+1]:02X}'); addr += 2
        elif b == 0xA7:
            out.append(f'{pos:06X}: LDA [${data[addr+1]:02X}]'); addr += 2
        elif b == 0xB5:
            out.append(f'{pos:06X}: LDA ${data[addr+1]:02X},X'); addr += 2
        elif b == 0xE4:
            out.append(f'{pos:06X}: CPX ${data[addr+1]:02X}'); addr += 2
        elif b == 0x64:
            out.append(f'{pos:06X}: STZ ${data[addr+1]:02X}'); addr += 2
        elif b == 0x54:
            d = data[addr+1]; s = data[addr+2]
            out.append(f'{pos:06X}: MVN ${d:02X},${s:02X}'); addr += 3
        elif b == 0x44:
            d = data[addr+1]; s = data[addr+2]
            out.append(f'{pos:06X}: MVP ${d:02X},${s:02X}'); addr += 3
        elif b == 0xCB: out.append(f'{pos:06X}: WAI'); addr += 1
        elif b == 0x42: out.append(f'{pos:06X}: WDM ${data[addr+1]:02X}'); addr += 2
        elif b == 0x89:
            if m == 0:
                v = data[addr+1] | (data[addr+2] << 8)
                out.append(f'{pos:06X}: BIT #${v:04X}'); addr += 3
            else:
                out.append(f'{pos:06X}: BIT #${data[addr+1]:02X}'); addr += 2
        elif b == 0x06: out.append(f'{pos:06X}: ASL ${data[addr+1]:02X}'); addr += 2
        elif b == 0x0A: out.append(f'{pos:06X}: ASL'); addr += 1
        elif b == 0x0E:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: ASL ${v:04X}'); addr += 3
        elif b == 0x4A: out.append(f'{pos:06X}: LSR'); addr += 1
        elif b == 0x46: out.append(f'{pos:06X}: LSR ${data[addr+1]:02X}'); addr += 2
        elif b == 0xCE:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: DEC ${v:04X}'); addr += 3
        elif b == 0xE6: out.append(f'{pos:06X}: INC ${data[addr+1]:02X}'); addr += 2
        elif b == 0xC6: out.append(f'{pos:06X}: DEC ${data[addr+1]:02X}'); addr += 2
        elif b == 0x24: out.append(f'{pos:06X}: BIT ${data[addr+1]:02X}'); addr += 2
        elif b == 0x2C:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: BIT ${v:04X}'); addr += 3
        elif b == 0xF4:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: PEA ${v:04X}'); addr += 3
        elif b == 0xD4:
            out.append(f'{pos:06X}: PEI (${data[addr+1]:02X})'); addr += 2
        elif b == 0x62:
            off = data[addr+1] | (data[addr+2] << 8)
            if off & 0x8000: off -= 0x10000
            out.append(f'{pos:06X}: PER ${pos+3+off:06X}'); addr += 3
        elif b == 0x0B: out.append(f'{pos:06X}: PHD'); addr += 1
        elif b == 0x2B: out.append(f'{pos:06X}: PLD'); addr += 1
        elif b == 0x5B: out.append(f'{pos:06X}: TCD'); addr += 1
        elif b == 0x1B: out.append(f'{pos:06X}: TCS'); addr += 1
        elif b == 0x7C:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: JMP (${v:04X},X)'); addr += 3
        elif b == 0xDC:
            v = data[addr+1] | (data[addr+2] << 8)
            out.append(f'{pos:06X}: JML [${v:04X}]'); addr += 3
        elif b == 0xE8: out.append(f'{pos:06X}: INX'); addr += 1
        elif b == 0xC8: out.append(f'{pos:06X}: INY'); addr += 1
        elif b == 0x88: out.append(f'{pos:06X}: DEY'); addr += 1
        else:
            out.append(f'{pos:06X}: ??? [{b:02X}]')
            addr += 1
    return out

data = rom[0x83F7:0x8600]
lines = disas(data, 0x83F7)
for l in lines:
    print(l)
