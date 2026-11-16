"""
Show raw disassembly of the 4 dispatch handler candidates.
"""
data = open('roms/dkc2.sfc', 'rb').read()

OPCODES = {
    0x0E: ("ASL", 3), 0x09: ("ORA", 3), 0x29: ("AND", 3), 0x99: ("STA", 3),
    0xBD: ("LDA", 3), 0x9D: ("STA", 3), 0x98: ("TYA", 1), 0x3A: ("DEC", 1),
    0xA8: ("TAY", 1), 0xB9: ("LDA", 3), 0x60: ("RTS", 1), 0x20: ("JSR", 3),
    0x22: ("JSL", 4), 0x6B: ("RTL", 1), 0xA9: ("LDA", 2), 0xAA: ("TAX", 1),
    0xE8: ("INX", 1), 0xCA: ("DEX", 1), 0xC8: ("INY", 1), 0x88: ("DEY", 1),
    0x18: ("CLC", 1), 0x38: ("SEC", 1), 0x80: ("BRA", 2), 0xF0: ("BEQ", 2),
    0xD0: ("BNE", 2), 0x10: ("BPL", 2), 0x30: ("BMI", 2), 0xA0: ("LDY", 2),
    0xA2: ("LDX", 2), 0x8A: ("TXA", 1), 0x9A: ("TXS", 1), 0xBA: ("TSX", 1),
    0x48: ("PHA", 1), 0x68: ("PLA", 1), 0xDA: ("PHX", 1), 0xFA: ("PLX", 1),
    0x5A: ("PHY", 1), 0x7A: ("PLY", 1), 0x4C: ("JMP", 3), 0x5C: ("JML", 4),
    0x64: ("STZ", 2), 0x9C: ("STZ", 3), 0x84: ("STY", 2), 0x86: ("STX", 2),
    0x85: ("STA", 2), 0x8D: ("STA", 3), 0xAD: ("LDA", 3), 0xA5: ("LDA", 2),
    0xE2: ("SEP", 2), 0xC2: ("REP", 2), 0xFB: ("XCE", 1), 0x78: ("SEI", 1),
    0x58: ("CLI", 1), 0xEA: ("NOP", 1), 0xCB: ("WAI", 1),
    0x1A: ("INC", 1), 0xC6: ("DEC", 2), 0xE6: ("INC", 2),
    0xC9: ("CMP", 3), 0xE0: ("CPX", 3), 0xE4: ("CPX", 2),
    0x4A: ("LSR", 1), 0x08: ("PHP", 1), 0x28: ("PLP", 1),
    0x5C: ("JMP", 4), 0xDA: ("PHX", 1), 0xFA: ("PLX", 1),
    0x5A: ("PHY", 1), 0x7A: ("PLY", 1),
    0x0C: ("TSB", 3), 0x1C: ("TRB", 3), 0x89: ("BIT", 3),
    0x49: ("EOR", 3), 0x45: ("EOR", 2), 0x41: ("EOR", 2),
    0x6D: ("ADC", 3), 0x65: ("ADC", 2), 0x63: ("ADC", 2),
    0xED: ("SBC", 3), 0xE5: ("SBC", 2), 0xE3: ("SBC", 2),
    0xAE: ("LDX", 3), 0xAC: ("LDY", 3),
    0xCE: ("DEC", 3), 0xEE: ("INC", 3), 0x2C: ("BIT", 3),
    # Long variants
    0xAF: ("LDA", 4), 0xBF: ("LDA", 4), 0xA7: ("LDA", 2),
    0xB7: ("LDA", 2), 0x87: ("STA", 2), 0x97: ("STA", 2),
}

MODE_MAP = {
    0x85: 2, 0x8D: 3, 0xA5: 2, 0xAD: 3, 0xBD: 3, 0xB9: 3,
    0x99: 3, 0x9D: 3, 0xA9: 2, 0xA0: 2, 0xA2: 2,
    0x20: 3, 0x4C: 3, 0x22: 4, 0xE2: 2, 0xC2: 2,
    0x09: 3, 0x29: 3, 0x49: 3, 0x45: 2, 0x0E: 3,
    0x0C: 3, 0x1C: 3, 0x89: 3, 0x80: 2, 0xF0: 2, 0xD0: 2,
    0x10: 2, 0x30: 2, 0xC9: 3, 0xE0: 3, 0xE4: 2,
    0xAE: 3, 0xAC: 3, 0x9C: 3, 0xCE: 3, 0xEE: 3, 0x2C: 3,
    0xAF: 4, 0xBF: 4,
}

def disasm_line(offset):
    op = data[offset]
    mnem = OPCODES.get(op, ("??", 1))
    name = mnem[0]
    length = MODE_MAP.get(op, mnem[1] if isinstance(mnem, tuple) else 1)
    
    if length == 1:
        extra = ""
    elif length == 2:
        extra = f"${data[offset+1]:02X}"
    elif length == 3:
        extra = f"${data[offset+1] | (data[offset+2] << 8):04X}"
    elif length == 4:
        extra = f"${data[offset+1] | (data[offset+2] << 8) | (data[offset+3] << 16):06X}"
    else:
        extra = "?"
    
    return f"{name:7s} {extra}", length

addrs = [(0xC0885F, "state_9"), (0xC0888B, "state_A"),
         (0xC088B7, "state_B"), (0xC088E3, "state_C")]

for addr, label in addrs:
    print(f"\n=== {label} (${addr:06X}) ===")
    offset = addr & 0xFFFF
    for _ in range(40):
        line, length = disasm_line(offset)
        snes = 0xC00000 | offset
        print(f"  ${snes:06X}: {line}")
        offset += length
        if "RTS" in line or "RTL" in line:
            break
