"""Find SA-1 DMA setup context using known positions from earlier search."""

with open('roms/dkc2.sfc', 'rb') as f:
    rom = f.read()

# Known positions: STA $2230 at 0xB3C6, etc.
known = [
    0xB3C6,  # STA $2230
    0xB3CC,  # STZ $2231
    0xB3D0,  # STZ $2232  
    0xB3D9,  # STA $2235
    0xB3DE,  # STA $2236
    0xB3E3,  # STA $2237
    0xB3E8,  # STA $2238
]

for pos in known:
    print(f"\n=== Context around ROM 0x{pos:06X} ===")
    start = max(0, pos - 40)
    end = min(len(rom), pos + 30)
    for j in range(start, end):
        b = rom[j]
        line = f"  ROM 0x{j:06X}: {b:02X}"
        marker = "  <<<" if j == pos else ""
        
        # Try to decode the instruction
        if b == 0x8D and j+3 <= len(rom):  # STA abs
            addr = rom[j+1] | (rom[j+2] << 8)
            line += f"  STA ${addr:04X}"
        elif b == 0x9C and j+3 <= len(rom):  # STZ abs
            addr = rom[j+1] | (rom[j+2] << 8)
            line += f"  STZ ${addr:04X}"
        elif b == 0xA9 and j+2 <= len(rom):  # LDA #xx
            line += f"  LDA #${rom[j+1]:02X}"
        elif b == 0xA2 and j+2 <= len(rom):  # LDX #xx
            line += f"  LDX #${rom[j+1]:02X}"
        elif b == 0xA0 and j+2 <= len(rom):  # LDY #xx
            line += f"  LDY #${rom[j+1]:02X}"
        elif b == 0x8F and j+4 <= len(rom):  # STA long
            addr = rom[j+1] | (rom[j+2] << 8) | (rom[j+3] << 16)
            line += f"  STA ${addr:06X}"
        elif b == 0xAF and j+4 <= len(rom):  # LDA long
            addr = rom[j+1] | (rom[j+2] << 8) | (rom[j+3] << 16)
            line += f"  LDA ${addr:06X}"
        elif b == 0x22 and j+4 <= len(rom):  # JSL
            dest = rom[j+1] | (rom[j+2] << 8) | (rom[j+3] << 16)
            line += f"  JSL ${dest:06X}"
        elif b == 0x5C and j+4 <= len(rom):  # JML
            dest = rom[j+1] | (rom[j+2] << 8) | (rom[j+3] << 16)
            line += f"  JML ${dest:06X}"
        elif b == 0xEA: line += "  NOP"
        elif b == 0x6B: line += "  RTL"
        elif b == 0x60: line += "  RTS"
        elif b == 0x18: line += "  CLC"
        elif b == 0x38: line += "  SEC"
        elif b == 0xE8: line += "  INX"
        elif b == 0xCA: line += "  DEX"
        elif b == 0xC8: line += "  INY"
        elif b == 0x88: line += "  DEY"
        elif b == 0x48: line += "  PHA"
        elif b == 0x68: line += "  PLA"
        elif b == 0xDA: line += "  PHX"
        elif b == 0xFA: line += "  PLX"
        elif b == 0x5A: line += "  PHY"
        elif b == 0x7A: line += "  PLY"
        elif b == 0xC2 and j+2 <= len(rom): line += f"  REP #${rom[j+1]:02X}"
        elif b == 0xE2 and j+2 <= len(rom): line += f"  SEP #${rom[j+1]:02X}"
        elif b == 0xD0 and j+2 <= len(rom): line += f"  BNE 0x{j+2+rom[j+1] if rom[j+1] < 128 else j+2+rom[j+1]-256:06X}"
        elif b == 0xF0 and j+2 <= len(rom): line += f"  BEQ 0x{j+2+rom[j+1] if rom[j+1] < 128 else j+2+rom[j+1]-256:06X}"
        elif b == 0x80 and j+2 <= len(rom): line += f"  BRA 0x{j+2+rom[j+1] if rom[j+1] < 128 else j+2+rom[j+1]-256:06X}"
        elif b == 0x1A: line += "  INA"
        elif b == 0x3A: line += "  DEA"
        elif b == 0xAA: line += "  TAX"
        elif b == 0x8A: line += "  TXA"
        elif b == 0xA8: line += "  TAY"
        elif b == 0x98: line += "  TYA"
        elif b == 0x9B: line += "  TXY"
        elif b == 0xBB: line += "  TYX"
        elif b == 0xAD and j+3 <= len(rom):  # LDA abs
            addr = rom[j+1] | (rom[j+2] << 8)
            line += f"  LDA ${addr:04X}"
        elif b == 0x85 and j+2 <= len(rom):  # STA dp
            line += f"  STA ${rom[j+1]:02X}"
        elif b == 0xA5 and j+2 <= len(rom):  # LDA dp
            line += f"  LDA ${rom[j+1]:02X}"
        elif b == 0x20 and j+3 <= len(rom):  # JSR
            line += f"  JSR ${rom[j+1] | (rom[j+2] << 8):04X}"
        elif b == 0x4C and j+3 <= len(rom):  # JMP
            line += f"  JMP ${rom[j+1] | (rom[j+2] << 8):04X}"
        
        print(f"{line}{marker}")
