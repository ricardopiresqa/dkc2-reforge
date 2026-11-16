"""Disassemble SA-1 DMA setup area at 0xB3C6 and surrounding code."""

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

def fmt_insn(opc, insn):
    return f"{opc:02X}  {insn}"

start = 0xB350
end = 0xB440
print(f"=== Disassembly of SA-1 DMA area (ROM 0x{start:06X}-0x{end:06X}) ===")
i = start
while i < end:
    b = rom[i]
    asm = ""
    size = 1
    if b == 0xA9 and i+2 < end:  # LDA #xx
        asm = f"LDA #${rom[i+1]:02X}"
        size = 2
    elif b == 0xA2 and i+2 < end:  # LDX #xx
        asm = f"LDX #${rom[i+1]:02X}"
        size = 2
    elif b == 0xA0 and i+2 < end:  # LDY #xx
        asm = f"LDY #${rom[i+1]:02X}"
        size = 2
    elif b == 0x8D and i+3 < end:  # STA abs
        addr = rom[i+1] | (rom[i+2] << 8)
        asm = f"STA ${addr:04X}"
        size = 3
    elif b == 0xAD and i+3 < end:  # LDA abs
        addr = rom[i+1] | (rom[i+2] << 8)
        asm = f"LDA ${addr:04X}"
        size = 3
    elif b == 0x9C and i+3 < end:  # STZ abs
        addr = rom[i+1] | (rom[i+2] << 8)
        asm = f"STZ ${addr:04X}"
        size = 3
    elif b == 0xAF and i+4 < end:  # LDA long
        addr = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        asm = f"LDA ${addr:06X}"
        size = 4
    elif b == 0x8F and i+4 < end:  # STA long
        addr = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        asm = f"STA ${addr:06X}"
        size = 4
    elif b == 0x22 and i+4 < end:  # JSL long
        dest = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        asm = f"JSL ${dest:06X}"
        size = 4
    elif b == 0x5C and i+4 < end:  # JML long
        dest = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        asm = f"JML ${dest:06X}"
        size = 4
    elif b == 0x20 and i+3 < end:  # JSR abs
        asm = f"JSR ${rom[i+1] | (rom[i+2] << 8):04X}"
        size = 3
    elif b == 0x4C and i+3 < end:  # JMP abs
        asm = f"JMP ${rom[i+1] | (rom[i+2] << 8):04X}"
        size = 3
    elif b == 0xA5 and i+2 < end:  # LDA dp
        asm = f"LDA ${rom[i+1]:02X}"
        size = 2
    elif b == 0x85 and i+2 < end:  # STA dp
        asm = f"STA ${rom[i+1]:02X}"
        size = 2
    elif b == 0xC2 and i+2 < end:  # REP #xx
        asm = f"REP #${rom[i+1]:02X}"
        size = 2
    elif b == 0xE2 and i+2 < end:  # SEP #xx
        asm = f"SEP #${rom[i+1]:02X}"
        size = 2
    elif b == 0xEA:
        asm = "NOP"
    elif b == 0x6B:
        asm = "RTL"
    elif b == 0x60:
        asm = "RTS"
    elif b == 0x18:
        asm = "CLC"
    elif b == 0x38:
        asm = "SEC"
    elif b == 0xE8:
        asm = "INX"
    elif b == 0xCA:
        asm = "DEX"
    elif b == 0xC8:
        asm = "INY"
    elif b == 0x88:
        asm = "DEY"
    elif b == 0x9B:
        asm = "TXY"
    elif b == 0xBB:
        asm = "TYX"
    elif b == 0xAA:  # TAX
        asm = "TAX"
    elif b == 0x8A:  # TXA
        asm = "TXA"
    elif b == 0xA8:  # TAY
        asm = "TAY"
    elif b == 0x98:  # TYA
        asm = "TYA"
    elif b == 0x5A:
        asm = "PHY"
    elif b == 0x7A:
        asm = "PLY"
    elif b == 0xDA:
        asm = "PHX"
    elif b == 0xFA:
        asm = "PLX"
    elif b == 0x48:
        asm = "PHA"
    elif b == 0x68:
        asm = "PLA"
    elif b == 0x08:
        asm = "PHP"
    elif b == 0x28:
        asm = "PLP"
    elif b == 0x1A:
        asm = "INA"
    elif b == 0x3A:
        asm = "DEA"
    elif b == 0x9C and i+3 < end:
        addr = rom[i+1] | (rom[i+2] << 8)
        asm = f"STZ ${addr:04X}"
        size = 3
    elif b == 0x64 and i+2 < end:  # STZ dp
        asm = f"STZ ${rom[i+1]:02X}"
        size = 2
    elif b in [0xD0, 0xF0, 0x30, 0x10, 0x90, 0xB0, 0x80, 0x50, 0x70]:
        target = i + 2 + (rom[i+1] if rom[i+1] < 128 else rom[i+1] - 256)
        names = {0xD0: "BNE", 0xF0: "BEQ", 0x30: "BMI", 0x10: "BPL", 
                 0x90: "BCC", 0xB0: "BCS", 0x80: "BRA", 0x50: "BVC", 0x70: "BVS"}
        asm = f"{names[b]} 0x{target:06X}"
        size = 2
    elif b == 0x82 and i+3 < end:  # BRL rel16
        target = i + 3 + (rom[i+1] | (rom[i+2] << 8))
        asm = f"BRL 0x{target:06X}"
        size = 3
    else:
        asm = f".db ${b:02X}"
    print(f"  ROM 0x{i:06X}: {fmt_insn(b, asm)}")
    i += size
