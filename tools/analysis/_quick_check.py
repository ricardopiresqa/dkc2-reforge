rom = open('roms/dkc2.sfc', 'rb').read()
def r(b,a): return (b&0x3F)*0x10000+a

def disasm_simple(addr, label, count=80):
    """Quick manual disassembly without mode tracking"""
    a = r(0x80, addr)
    lines = [f"\n=== {label} ($80:{addr:04X}) ==="]
    for i in range(count):
        if addr+i >= len(lines): break
        pos = r(0x80, addr+i)
        if pos >= len(rom): break
        byte = rom[pos]
        if byte == 0xEA: lines.append(f"  {addr+i:04X}: NOP"); continue
        elif byte == 0x4C and addr+i+2 < len(lines):  # JMP
            t = rom[pos+1] | (rom[pos+2]<<8)
            lines.append(f"  {addr+i:04X}: JMP ${t:04X}"); break
        elif byte == 0x80:  # BRA
            offset = rom[pos+1] if rom[pos+1] < 128 else rom[pos+1]-256
            t = addr+i+2+offset
            lines.append(f"  {addr+i:04X}: BRA ${t:04X}")
            if t > addr+i: i = t - addr - 1; continue
            else: break
        elif byte == 0x40: lines.append(f"  {addr+i:04X}: RTI"); break
        elif byte == 0x60: lines.append(f"  {addr+i:04X}: RTS"); break
        elif byte == 0x6B: lines.append(f"  {addr+i:04X}: RTL"); break
        elif byte == 0x5C:  # JML
            t = rom[pos+1] | (rom[pos+2]<<8) | (rom[pos+3]<<16)
            lines.append(f"  {addr+i:04X}: JML ${t:06X}"); break
        elif byte == 0xDC:  # JML [dp]
            lines.append(f"  {addr+i:04X}: JML [$00]"); break
        elif byte == 0x00: lines.append(f"  {addr+i:04X}: BRK"); break
        elif byte == 0x90:  # BCC
            offset = rom[pos+1] if rom[pos+1] < 128 else rom[pos+1]-256
            lines.append(f"  {addr+i:04X}: BCC ${addr+i+2+offset:04X}")
        elif byte == 0xB0:  # BCS
            offset = rom[pos+1] if rom[pos+1] < 128 else rom[pos+1]-256
            lines.append(f"  {addr+i:04X}: BCS ${addr+i+2+offset:04X}")
        elif byte == 0xD0:  # BNE
            offset = rom[pos+1] if rom[pos+1] < 128 else rom[pos+1]-256
            lines.append(f"  {addr+i:04X}: BNE ${addr+i+2+offset:04X}")
        elif byte == 0xF0:  # BEQ
            offset = rom[pos+1] if rom[pos+1] < 128 else rom[pos+1]-256
            lines.append(f"  {addr+i:04X}: BEQ ${addr+i+2+offset:04X}")
        elif byte in (0x10, 0x30, 0x50, 0x70, 0xC0, 0xE0):  # other branches
            lines.append(f"  {addr+i:04X}: BRA? ${addr+i+2}")
        else:
            lines.append(f"  {addr+i:04X}: ${byte:02X}")
    return '\n'.join(lines)

# Check key addresses
print(disasm_simple(0x9510, "BCC fallthrough ($9510)", 20))
print(disasm_simple(0x964C, "JMP target from $95BE", 20))
print(disasm_simple(0x96FB, "JMP target from $966D", 20))
print(disasm_simple(0x99C3, "Handler from $99BD", 20))
