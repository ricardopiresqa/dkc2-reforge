rom = open('roms/dkc2.sfc', 'rb').read()
def r(b,a): return (b&0x3F)*0x10000+a

targets = [0x9510, 0x964C, 0x96FB, 0x99C3, 0x95B3, 0x967C]

def disasm(target, maxlen=60):
    pos = 0
    out = []
    out.append(f"=== ${target:04X} ===")
    while pos < maxlen:
        a = r(0x80, target+pos)
        if a >= len(rom):
            break
        byte = rom[a]
        if byte == 0x40: out.append(f"  {target+pos:04X}: RTI"); break
        elif byte == 0x60: out.append(f"  {target+pos:04X}: RTS"); break
        elif byte == 0x6B: out.append(f"  {target+pos:04X}: RTL"); break
        elif byte == 0xEA: out.append(f"  {target+pos:04X}: NOP"); pos+=1
        elif byte == 0x38: out.append(f"  {target+pos:04X}: SEC"); pos+=1
        elif byte == 0x18: out.append(f"  {target+pos:04X}: CLC"); pos+=1
        elif byte == 0xE8: out.append(f"  {target+pos:04X}: INX"); pos+=1
        elif byte == 0xCA: out.append(f"  {target+pos:04X}: DEX"); pos+=1
        elif byte == 0x1A: out.append(f"  {target+pos:04X}: INC A"); pos+=1
        elif byte == 0x3A: out.append(f"  {target+pos:04X}: DEC A"); pos+=1
        elif byte == 0x48: out.append(f"  {target+pos:04X}: PHA"); pos+=1
        elif byte == 0x68: out.append(f"  {target+pos:04X}: PLA"); pos+=1
        elif byte == 0xDA: out.append(f"  {target+pos:04X}: PHX"); pos+=1
        elif byte == 0xFA: out.append(f"  {target+pos:04X}: PLX"); pos+=1
        elif byte == 0x5A: out.append(f"  {target+pos:04X}: PHY"); pos+=1
        elif byte == 0x7A: out.append(f"  {target+pos:04X}: PLY"); pos+=1
        elif byte == 0x0A: out.append(f"  {target+pos:04X}: ASL A"); pos+=1
        elif byte == 0x4A: out.append(f"  {target+pos:04X}: LSR A"); pos+=1
        elif byte == 0xAA: out.append(f"  {target+pos:04X}: TAX"); pos+=1
        elif byte == 0x8A: out.append(f"  {target+pos:04X}: TXA"); pos+=1
        elif byte == 0xBB: out.append(f"  {target+pos:04X}: TYX"); pos+=1  # actually TYB?
        elif byte == 0x9A: out.append(f"  {target+pos:04X}: TXS"); pos+=1
        elif byte == 0xBA: out.append(f"  {target+pos:04X}: TSX"); pos+=1
        elif byte == 0xC8: out.append(f"  {target+pos:04X}: INY"); pos+=1
        elif byte == 0x88: out.append(f"  {target+pos:04X}: DEY"); pos+=1
        elif byte == 0x4C:
            t = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: JMP ${t:04X}"); break
        elif byte == 0x80:
            off = rom[a+1] if rom[a+1] < 128 else rom[a+1]-256
            t = target+pos+2+off
            out.append(f"  {target+pos:04X}: BRA ${t:04X}")
            if t <= target+pos: break
            pos = t - target; continue
        elif byte == 0x10:
            off = rom[a+1] if rom[a+1] < 128 else rom[a+1]-256
            t = target+pos+2+off; out.append(f"  {target+pos:04X}: BPL ${t:04X}"); pos+=2
        elif byte == 0x30:
            off = rom[a+1] if rom[a+1] < 128 else rom[a+1]-256
            t = target+pos+2+off; out.append(f"  {target+pos:04X}: BMI ${t:04X}"); pos+=2
        elif byte == 0x90:
            off = rom[a+1] if rom[a+1] < 128 else rom[a+1]-256
            t = target+pos+2+off; out.append(f"  {target+pos:04X}: BCC ${t:04X}"); pos+=2
        elif byte == 0xB0:
            off = rom[a+1] if rom[a+1] < 128 else rom[a+1]-256
            t = target+pos+2+off; out.append(f"  {target+pos:04X}: BCS ${t:04X}"); pos+=2
        elif byte == 0xD0:
            off = rom[a+1] if rom[a+1] < 128 else rom[a+1]-256
            t = target+pos+2+off; out.append(f"  {target+pos:04X}: BNE ${t:04X}"); pos+=2
        elif byte == 0xF0:
            off = rom[a+1] if rom[a+1] < 128 else rom[a+1]-256
            t = target+pos+2+off; out.append(f"  {target+pos:04X}: BEQ ${t:04X}"); pos+=2
        elif byte == 0xA9:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: LDA #{val:04X}"); pos+=3
        elif byte == 0xA2:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: LDX #{val:04X}"); pos+=3
        elif byte == 0xA0:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: LDY #{val:04X}"); pos+=3
        elif byte == 0xE2:
            out.append(f"  {target+pos:04X}: SEP #{rom[a+1]:02X}"); pos+=2
        elif byte == 0xC2:
            out.append(f"  {target+pos:04X}: REP #{rom[a+1]:02X}"); pos+=2
        elif byte == 0x22:
            b = rom[a+1] | (rom[a+2]<<8) | (rom[a+3]<<16)
            out.append(f"  {target+pos:04X}: JSL ${b:06X}"); pos+=4
        elif byte == 0x20:
            t = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: JSR ${t:04X}"); pos+=3
        elif byte == 0x5C:
            t = rom[a+1] | (rom[a+2]<<8) | (rom[a+3]<<16)
            out.append(f"  {target+pos:04X}: JML ${t:06X}"); break
        elif byte == 0x85:
            out.append(f"  {target+pos:04X}: STA ${rom[a+1]:02X}"); pos+=2
        elif byte == 0x87:
            out.append(f"  {target+pos:04X}: STA [{rom[a+1]:02X}]"); pos+=2
        elif byte == 0x95:
            out.append(f"  {target+pos:04X}: STA ${rom[a+1]:02X},X"); pos+=2
        elif byte == 0x8D:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: STA ${val:04X}"); pos+=3
        elif byte == 0x8F:
            val = rom[a+1] | (rom[a+2]<<8) | (rom[a+3]<<16)
            out.append(f"  {target+pos:04X}: STA ${val:06X}"); pos+=4
        elif byte == 0xA5:
            out.append(f"  {target+pos:04X}: LDA ${rom[a+1]:02X}"); pos+=2
        elif byte == 0xB5:
            out.append(f"  {target+pos:04X}: LDA ${rom[a+1]:02X},X"); pos+=2
        elif byte == 0xAD:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: LDA ${val:04X}"); pos+=3
        elif byte == 0xAF:
            val = rom[a+1] | (rom[a+2]<<8) | (rom[a+3]<<16)
            out.append(f"  {target+pos:04X}: LDA ${val:06X}"); pos+=4
        elif byte == 0xA6:
            out.append(f"  {target+pos:04X}: LDX ${rom[a+1]:02X}"); pos+=2
        elif byte == 0xA7:
            out.append(f"  {target+pos:04X}: LDA [{rom[a+1]:02X}]"); pos+=2
        elif byte == 0xAE:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: LDX ${val:04X}"); pos+=3
        elif byte == 0xE0:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: CPX #{val:04X}"); pos+=3
        elif byte == 0xE4:
            out.append(f"  {target+pos:04X}: CPX ${rom[a+1]:02X}"); pos+=2
        elif byte == 0xC9:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: CMP #{val:04X}"); pos+=3
        elif byte == 0xC5:
            out.append(f"  {target+pos:04X}: CMP ${rom[a+1]:02X}"); pos+=2
        elif byte == 0xCD:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: CMP ${val:04X}"); pos+=3
        elif byte == 0x29:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: AND #{val:04X}"); pos+=3
        elif byte == 0x25:
            out.append(f"  {target+pos:04X}: AND ${rom[a+1]:02X}"); pos+=2
        elif byte == 0x09:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: ORA #{val:04X}"); pos+=3
        elif byte == 0x05:
            out.append(f"  {target+pos:04X}: ORA ${rom[a+1]:02X}"); pos+=2
        elif byte == 0x0D:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: ORA ${val:04X}"); pos+=3
        elif byte == 0x04:
            out.append(f"  {target+pos:04X}: TSB ${rom[a+1]:02X}"); pos+=2
        elif byte == 0x89:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: BIT #{val:04X}"); pos+=3
        elif byte == 0x24:
            out.append(f"  {target+pos:04X}: BIT ${rom[a+1]:02X}"); pos+=2
        elif byte == 0xF4:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: STP ${val:04X}"); pos+=3  # actually PEA
        elif byte == 0x9C:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: STZ ${val:04X}"); pos+=3
        elif byte == 0x64:
            out.append(f"  {target+pos:04X}: STZ ${rom[a+1]:02X}"); pos+=2
        elif byte == 0xE5:
            out.append(f"  {target+pos:04X}: SBC ${rom[a+1]:02X}"); pos+=2
        elif byte == 0xE9:
            val = rom[a+1] | (rom[a+2]<<8)
            out.append(f"  {target+pos:04X}: SBC #{val:04X}"); pos+=3
        elif byte == 0x10: out.append(f"  {target+pos:04X}: BPL"); pos+=2
        else:
            out.append(f"  {target+pos:04X}: ?? ${byte:02X}"); pos+=1
    return '\n'.join(out)

for addr in targets:
    print(disasm(addr))
    print()
