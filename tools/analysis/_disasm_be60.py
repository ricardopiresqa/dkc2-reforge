"""Disassemble the code at ROM 0x00BE60 (where JSL $B4BE60 goes with $2224=$80)."""

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

def decode(b, rom, i):
    """Decode a single 65816 instruction and return (asm, length)."""
    if b == 0x8D and i+3 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8)
        return f"STA ${addr:04X}", 3
    elif b == 0x9C and i+3 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8)
        return f"STZ ${addr:04X}", 3
    elif b == 0xAD and i+3 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8)
        return f"LDA ${addr:04X}", 3
    elif b == 0xA9 and i+2 <= len(rom):
        return f"LDA #${rom[i+1]:02X}", 2
    elif b == 0xA2 and i+2 <= len(rom):
        return f"LDX #${rom[i+1]:02X}", 2
    elif b == 0xA0 and i+2 <= len(rom):
        return f"LDY #${rom[i+1]:02X}", 2
    elif b == 0x8F and i+4 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        return f"STA ${addr:06X}", 4
    elif b == 0xAF and i+4 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        return f"LDA ${addr:06X}", 4
    elif b == 0x22 and i+4 <= len(rom):
        dest = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        return f"JSL ${dest:06X}", 4
    elif b == 0x5C and i+4 <= len(rom):
        dest = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        return f"JML ${dest:06X}", 4
    elif b == 0x20 and i+3 <= len(rom):
        return f"JSR ${rom[i+1] | (rom[i+2] << 8):04X}", 3
    elif b == 0x4C and i+3 <= len(rom):
        return f"JMP ${rom[i+1] | (rom[i+2] << 8):04X}", 3
    elif b == 0x85 and i+2 <= len(rom):
        return f"STA ${rom[i+1]:02X}", 2
    elif b == 0xA5 and i+2 <= len(rom):
        return f"LDA ${rom[i+1]:02X}", 2
    elif b == 0xC2 and i+2 <= len(rom):
        return f"REP #${rom[i+1]:02X}", 2
    elif b == 0xE2 and i+2 <= len(rom):
        return f"SEP #${rom[i+1]:02X}", 2
    elif b == 0x80 and i+2 <= len(rom):
        offset = rom[i+1] if rom[i+1] < 128 else rom[i+1] - 256
        return f"BRA 0x{i+2+offset:06X}", 2
    elif b == 0xD0 and i+2 <= len(rom):
        offset = rom[i+1] if rom[i+1] < 128 else rom[i+1] - 256
        return f"BNE 0x{i+2+offset:06X}", 2
    elif b == 0xF0 and i+2 <= len(rom):
        offset = rom[i+1] if rom[i+1] < 128 else rom[i+1] - 256
        return f"BEQ 0x{i+2+offset:06X}", 2
    elif b == 0xB0 and i+2 <= len(rom):
        offset = rom[i+1] if rom[i+1] < 128 else rom[i+1] - 256
        return f"BCS 0x{i+2+offset:06X}", 2
    elif b == 0x90 and i+2 <= len(rom):
        offset = rom[i+1] if rom[i+1] < 128 else rom[i+1] - 256
        return f"BCC 0x{i+2+offset:06X}", 2
    elif b == 0x10 and i+2 <= len(rom):
        offset = rom[i+1] if rom[i+1] < 128 else rom[i+1] - 256
        return f"BPL 0x{i+2+offset:06X}", 2
    elif b == 0x82 and i+3 <= len(rom):
        offset = rom[i+1] | (rom[i+2] << 8)
        return f"BRL 0x{i+3+offset:06X}", 3
    elif b == 0xEA: return "NOP", 1
    elif b == 0x6B: return "RTL", 1
    elif b == 0x60: return "RTS", 1
    elif b == 0x18: return "CLC", 1
    elif b == 0x38: return "SEC", 1
    elif b == 0x48: return "PHA", 1
    elif b == 0x68: return "PLA", 1
    elif b == 0xDA: return "PHX", 1
    elif b == 0xFA: return "PLX", 1
    elif b == 0x5A: return "PHY", 1
    elif b == 0x7A: return "PLY", 1
    elif b == 0x08: return "PHP", 1
    elif b == 0x28: return "PLP", 1
    elif b == 0x0B: return "PHD", 1
    elif b == 0x2B: return "PLD", 1
    elif b == 0x1A: return "INA", 1
    elif b == 0x3A: return "DEA", 1
    elif b == 0xAA: return "TAX", 1
    elif b == 0x8A: return "TXA", 1
    elif b == 0xA8: return "TAY", 1
    elif b == 0x98: return "TYA", 1
    elif b == 0x9B: return "TXY", 1
    elif b == 0xBB: return "TYX", 1
    elif b == 0xE8: return "INX", 1
    elif b == 0xCA: return "DEX", 1
    elif b == 0xC8: return "INY", 1
    elif b == 0x88: return "DEY", 1
    elif b == 0xFB: return "XCE", 1
    elif b == 0xDB: return "STP", 1
    elif b == 0xCB: return "WAI", 1
    elif b == 0x64 and i+2 <= len(rom): return f"STZ ${rom[i+1]:02X}", 2
    elif b == 0x21 and i+2 <= len(rom): return f"AND ${rom[i+1]:02X},X", 2
    elif b == 0x25 and i+2 <= len(rom): return f"AND ${rom[i+1]:02X}", 2
    elif b == 0x29 and i+2 <= len(rom): return f"AND #${rom[i+1]:02X}", 2
    elif b == 0x09 and i+2 <= len(rom): return f"ORA #${rom[i+1]:02X}", 2
    elif b == 0x0D and i+3 <= len(rom): 
        addr = rom[i+1] | (rom[i+2] << 8)
        return f"ORA ${addr:04X}", 3
    elif b == 0x1D and i+3 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8)
        return f"ORA ${addr:04X},X", 3
    elif b == 0xC9 and i+2 <= len(rom): return f"CMP #${rom[i+1]:02X}", 2
    elif b == 0xCD and i+3 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8)
        return f"CMP ${addr:04X}", 3
    elif b == 0xE0 and i+2 <= len(rom): return f"CPX #${rom[i+1]:02X}", 2
    elif b == 0xEC and i+3 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8)
        return f"CPX ${addr:04X}", 3
    elif b == 0xC0 and i+2 <= len(rom): return f"CPY #${rom[i+1]:02X}", 2
    elif b == 0x9A: return "TXS", 1
    elif b == 0xBA: return "TSX", 1
    elif b == 0x0F and i+4 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        return f"AND ${addr:06X}", 4
    elif b == 0x2F and i+4 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        return f"AND ${addr:06X}", 4
    elif b == 0x4A: return "LSR A", 1
    elif b == 0x0A: return "ASL A", 1
    elif b == 0x0E and i+3 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8)
        return f"ASL ${addr:04X}", 3
    elif b == 0x4E and i+3 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8)
        return f"LSR ${addr:04X}", 3
    elif b == 0x46 and i+2 <= len(rom): return f"LSR ${rom[i+1]:02X}", 2
    elif b == 0xA7 and i+2 <= len(rom): return f"LDA [${rom[i+1]:02X}]", 2
    elif b == 0xB7 and i+2 <= len(rom): return f"LDA [${rom[i+1]:02X}],Y", 2
    elif b == 0x97 and i+2 <= len(rom): return f"STA [${rom[i+1]:02X}],Y", 2
    elif b == 0xE6 and i+2 <= len(rom): return f"INC ${rom[i+1]:02X}", 2
    elif b == 0xC6 and i+2 <= len(rom): return f"DEC ${rom[i+1]:02X}", 2
    elif b == 0xCE and i+3 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8)
        return f"DEC ${addr:04X}", 3
    elif b == 0xBD and i+3 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8)
        return f"LDA ${addr:04X},X", 3
    elif b == 0xB9 and i+3 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8)
        return f"LDA ${addr:04X},Y", 3
    elif b == 0x99 and i+3 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8)
        return f"STA ${addr:04X},Y", 3
    elif b == 0x9D and i+3 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8)
        return f"STA ${addr:04X},X", 3
    elif b == 0x1A: return "INA", 1
    elif b == 0x3A: return "DEA", 1
    elif b == 0x89 and i+2 <= len(rom): return f"BIT #${rom[i+1]:02X}", 2
    elif b == 0x24 and i+2 <= len(rom): return f"BIT ${rom[i+1]:02X}", 2
    elif b == 0x2C and i+3 <= len(rom):
        addr = rom[i+1] | (rom[i+2] << 8)
        return f"BIT ${addr:04X}", 3
    elif b == 0x4B: return "LSR $43,~~ phk??", 1
    elif b == 0xAB: return "PLB", 1
    elif b == 0x8B: return "PHB", 1
    elif b == 0x0B: return "PHD", 1
    elif b == 0x2B: return "PLD", 1
    elif b == 0x5B: return "TCD", 1  # TCD
    elif b == 0x7B: return "TDC", 1  # TDC
    elif b == 0x1B: return "TCS", 1  # TCS
    elif b == 0x3B: return "TSC", 1  # TSC
    elif b == 0x6C and i+3 <= len(rom): return f"JMP (${rom[i+1] | (rom[i+2] << 8):04X})", 3
    elif b == 0x7C and i+3 <= len(rom): return f"JMP (${rom[i+1] | (rom[i+2] << 8):04X},X)", 3
    elif b == 0xDC and i+3 <= len(rom): return f"JML (${rom[i+1] | (rom[i+2] << 8):04X})", 3
    else:
        return f"--- ${b:02X}", 1

# Disassemble at ROM 0x00BE60
print("=== Disassembly of ROM 0x00BE60 (if $2224=$80, then $B4:BE60) ===")
i = 0x00BE50  # Start a bit earlier to get context
end = 0x00BF40
while i < end:
    b = rom[i]
    asm, size = decode(b, rom, i)
    print(f"  ROM 0x{i:06X}: {b:02X}  {asm}")
    i += size
