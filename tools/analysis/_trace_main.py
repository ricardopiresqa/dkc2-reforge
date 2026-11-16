rom = open('roms/dkc2.sfc', 'rb').read()

def r(bank, addr):
    return (bank & 0x3F) * 0x10000 + addr

def rb(off):
    return rom[off]

def rw(off):
    return rom[off] | (rom[off+1] << 8)

def rl(off):
    return rom[off] | (rom[off+1] << 8) | (rom[off+2] << 16)

def peek(bank, p):
    """Parse 65816 instruction at SNES $bank:pc and return (size, mnemonic)"""
    addr = r(bank, p)
    op = rom[addr]
    
    # Determine m/x mode (unknown here, assume 16-bit)
    msize = 2  # default 16-bit accum
    xsize = 2  # default 16-index
    
    # Simple opcode table for key opcodes only
    if op == 0xEA: return (1, 'NOP')
    elif op == 0x00: return (1, 'BRK')
    elif op == 0x6B: return (1, 'RTL')
    elif op == 0x60: return (1, 'RTS')
    elif op == 0x40: return (1, 'RTI')
    elif op == 0xCA: return (1, 'DEX')
    elif op == 0xE8: return (1, 'INX')
    elif op == 0x88: return (1, 'DEY')
    elif op == 0xC8: return (1, 'INY')
    elif op == 0x9C: return (3, f'STZ ${rw(addr+1):04X}')
    elif op == 0x64: return (2, f'STZ ${rb(addr+1):02X}')
    elif op == 0xA9:
        if msize == 2:
            return (3, f'LDA #${rw(addr+1):04X}')
        else:
            return (2, f'LDA #${rb(addr+1):02X}')
    elif op == 0xA5: return (2, f'LDA ${rb(addr+1):02X}')
    elif op == 0xAD: return (3, f'LDA ${rw(addr+1):04X}')
    elif op == 0x85: return (2, f'STA ${rb(addr+1):02X}')
    elif op == 0x8D: return (3, f'STA ${rw(addr+1):04X}')
    elif op == 0x20: return (3, f'JSR ${rw(addr+1):04X}')
    elif op == 0x22: return (4, f'JSL ${rw(addr+1):06X}')
    elif op == 0x4C: return (3, f'JMP ${rw(addr+1):04X}')
    elif op == 0x5C: return (4, f'JML ${rl(addr+1):06X}')
    elif op == 0xE2: return (2, f'SEP #${rb(addr+1):02X}')
    elif op == 0xC2: return (2, f'REP #${rb(addr+1):02X}')
    elif op == 0xFB: return (1, 'XCE')
    elif op == 0x18: return (1, 'CLC')
    elif op == 0x38: return (1, 'SEC')
    elif op == 0x58: return (1, 'CLI')
    elif op == 0x78: return (1, 'SEI')
    elif op == 0xDA: return (1, 'PHX')
    elif op == 0x5A: return (1, 'PHY')
    elif op == 0xFA: return (1, 'PLX')
    elif op == 0x7A: return (1, 'PLY')
    elif op == 0x48: return (1, 'PHA')
    elif op == 0x68: return (1, 'PLA')
    elif op == 0x8B: return (1, 'PHB')
    elif op == 0xAB: return (1, 'PLB')
    elif op == 0x0B: return (1, 'PHD')
    elif op == 0x2B: return (1, 'PLD')
    elif op == 0x1A: return (1, 'INC A')
    elif op == 0x3A: return (1, 'DEC A')
    elif op == 0xE6: return (2, f'INC ${rb(addr+1):02X}')
    elif op == 0xCE: return (3, f'DEC ${rw(addr+1):04X}')
    elif op == 0xA2:
        if xsize == 2:
            return (3, f'LDX #${rw(addr+1):04X}')
        else:
            return (2, f'LDX #${rb(addr+1):02X}')
    elif op == 0xA0:
        if xsize == 2:
            return (3, f'LDY #${rw(addr+1):04X}')
        else:
            return (2, f'LDY #${rb(addr+1):02X}')
    elif op == 0x9A: return (1, 'TXS')
    elif op == 0xBA: return (1, 'TSX')
    elif op == 0xAA: return (1, 'TAX')
    elif op == 0x8A: return (1, 'TXA')
    elif op == 0xA8: return (1, 'TAY')
    elif op == 0x98: return (1, 'TYA')
    elif op == 0x5B: return (1, 'TCD')
    elif op == 0x7B: return (1, 'TDC')
    elif op == 0x1B: return (1, 'TCS')
    elif op == 0x3B: return (1, 'TSC')
    elif op == 0xEB: return (1, 'XBA')
    elif op == 0x29: return (3, f'AND #${rw(addr+1):04X}')
    elif op == 0x09: return (3, f'ORA #${rw(addr+1):04X}')
    elif op == 0x49: return (3, f'EOR #${rw(addr+1):04X}')
    elif op == 0x18: return (1, 'CLC')
    elif op == 0x69: return (3, f'ADC #${rw(addr+1):04X}')
    elif op == 0x6D: return (3, f'ADC ${rw(addr+1):04X}')
    elif op == 0xE9: return (3, f'SBC #${rw(addr+1):04X}')
    elif op == 0xC9: return (3, f'CMP #${rw(addr+1):04X}')
    elif op == 0xC5: return (2, f'CMP ${rb(addr+1):02X}')
    elif op == 0xCD: return (3, f'CMP ${rw(addr+1):04X}')
    elif op == 0xF0: return (2, f'BEQ ${p+2+(rom[addr+1] if rom[addr+1] < 128 else rom[addr+1]-256):04X}')
    elif op == 0xD0: return (2, f'BNE ${p+2+(rom[addr+1] if rom[addr+1] < 128 else rom[addr+1]-256):04X}')
    elif op == 0x90: return (2, f'BCC ${p+2+(rom[addr+1] if rom[addr+1] < 128 else rom[addr+1]-256):04X}')
    elif op == 0xB0: return (2, f'BCS ${p+2+(rom[addr+1] if rom[addr+1] < 128 else rom[addr+1]-256):04X}')
    elif op == 0x80: return (2, f'BRA ${p+2+(rom[addr+1] if rom[addr+1] < 128 else rom[addr+1]-256):04X}')
    elif op == 0x82: return (3, f'BRL ${p+3+rw(addr+1):04X}')
    elif op == 0x10: return (2, f'BPL ${p+2+(rom[addr+1] if rom[addr+1] < 128 else rom[addr+1]-256):04X}')
    elif op == 0x30: return (2, f'BMI ${p+2+(rom[addr+1] if rom[addr+1] < 128 else rom[addr+1]-256):04X}')
    elif op == 0x54: return (4, f'MVN ${rb(addr+2):02X},${rb(addr+1):02X}')
    elif op == 0x44: return (4, f'MVP ${rb(addr+2):02X},${rb(addr+1):02X}')
    elif op == 0xC0:
        if xsize == 2:
            return (3, f'CPY #${rw(addr+1):04X}')
        else:
            return (2, f'CPY #${rb(addr+1):02X}')
    elif op == 0xE0:
        if xsize == 2:
            return (3, f'CPX #${rw(addr+1):04X}')
        else:
            return (2, f'CPX #${rb(addr+1):02X}')
    elif op == 0xF4: return (3, f'PEA ${rw(addr+1):04X}')
    elif op == 0xD4: return (3, f'PEI (${rb(addr+1):02X})')
    elif op == 0x62: return (3, f'PER ${p+3+rw(addr+1):04X}')
    elif op == 0x02: return (2, f'COP #${rb(addr+1):02X}')
    elif op == 0x42: return (1, 'WDM')
    elif op == 0xDB: return (1, 'STP')
    elif op == 0xCB: return (1, 'WAI')
    elif op == 0xA6: return (2, f'LDX ${rb(addr+1):02X}')
    elif op == 0xB5: return (2, f'LDA ${rb(addr+1):02X},X')
    elif op == 0x95: return (2, f'STA ${rb(addr+1):02X},X')
    elif op == 0x9D: return (3, f'STA ${rw(addr+1):04X},X')
    elif op == 0x99: return (3, f'STA ${rw(addr+1):04X},Y')
    elif op == 0xBD: return (3, f'LDA ${rw(addr+1):04X},X')
    elif op == 0xB9: return (3, f'LDA ${rw(addr+1):04X},Y')
    elif op == 0xBF: return (4, f'LDA ${rl(addr+1):06X},X')
    elif op == 0x8F: return (4, f'STA ${rl(addr+1):06X}')
    elif op == 0xAF: return (4, f'LDA ${rl(addr+1):06X}')
    elif op == 0xAE: return (3, f'LDX ${rw(addr+1):04X}')
    elif op == 0xAC: return (3, f'LDY ${rw(addr+1):04X}')
    elif op == 0x8E: return (3, f'STX ${rw(addr+1):04X}')
    elif op == 0x8C: return (3, f'STY ${rw(addr+1):04X}')
    elif op == 0xA7: return (2, f'LDA [${rb(addr+1):02X}]')
    elif op == 0xB7: return (2, f'LDA [${rb(addr+1):02X}],Y')
    elif op == 0x97: return (2, f'STA [${rb(addr+1):02X}],Y')
    elif op == 0x87: return (2, f'STA [${rb(addr+1):02X}]')
    elif op == 0xA3: return (2, f'LDA (${rb(addr+1):02X},S),Y')
    elif op == 0xE3: return (2, f'PEI (${rb(addr+1):02X},S),Y')  # jmag
    elif op == 0xF8: return (1, 'SED')
    elif op == 0xD8: return (1, 'CLD')
    elif op == 0x08: return (1, 'PHP')
    elif op == 0x28: return (1, 'PLP')
    elif op == 0xE2: return (2, f'SEP #${rb(addr+1):02X}')
    # conditional branches
    elif op == 0x4F: return (4, f'AND ${rl(addr+1):06X}')
    elif op == 0x0F: return (4, f'ORA ${rl(addr+1):06X}')
    elif op == 0x0D: return (3, f'ORA ${rw(addr+1):04X}')
    elif op == 0x1D: return (3, f'ORA ${rw(addr+1):04X},X')
    elif op == 0x3D: return (3, f'AND ${rw(addr+1):04X},X')
    elif op == 0x2D: return (3, f'AND ${rw(addr+1):04X}')
    elif op == 0x4D: return (3, f'EOR ${rw(addr+1):04X}')
    elif op == 0x1F: return (4, f'ORA ${rl(addr+1):06X},X')
    elif op == 0x3F: return (4, f'AND ${rl(addr+1):06X},X')
    elif op == 0x5F: return (4, f'EOR ${rl(addr+1):06X},X')
    elif op == 0x2F: return (4, f'AND ${rl(addr+1):06X}')
    elif op == 0x7F: return (4, f'ADC ${rl(addr+1):06X},X')
    elif op == 0xEF: return (4, f'SBC ${rl(addr+1):06X}')
    elif op == 0xFF: return (4, f'SBC ${rl(addr+1):06X},X')
    elif op == 0x6F: return (4, f'ADC ${rl(addr+1):06X}')
    elif op == 0x0A: return (1, 'ASL A')
    elif op == 0x4A: return (1, 'LSR A')
    elif op == 0x2A: return (1, 'ROL A')
    elif op == 0x6A: return (1, 'ROR A')
    elif op == 0x0E: return (3, f'ASL ${rw(addr+1):04X}')
    elif op == 0x4E: return (3, f'LSR ${rw(addr+1):04X}')
    elif op == 0x1E: return (3, f'ASL ${rw(addr+1):04X},X')
    elif op == 0x3E: return (3, f'ROL ${rw(addr+1):04X},X')
    elif op == 0x7E: return (3, f'ROR ${rw(addr+1):04X},X')
    elif op == 0xD9: return (3, f'CMP ${rw(addr+1):04X},Y')
    elif op == 0xDD: return (3, f'CMP ${rw(addr+1):04X},X')
    elif op == 0xDA: return (1, 'PHX')
    elif op == 0x5A: return (1, 'PHY')
    elif op == 0x84: return (2, f'STY ${rb(addr+1):02X}')
    elif op == 0x86: return (2, f'STX ${rb(addr+1):02X}')
    elif op == 0x24: return (2, f'BIT ${rb(addr+1):02X}')
    elif op == 0xA1: return (2, f'LDA (${rb(addr+1):02X},X)')
    elif op == 0x81: return (2, f'STA (${rb(addr+1):02X},X)')
    elif op == 0xB1: return (2, f'LDA (${rb(addr+1):02X}),Y')
    elif op == 0x91: return (2, f'STA (${rb(addr+1):02X}),Y')
    elif op == 0x92: return (2, f'STA (${rb(addr+1):02X})')
    elif op == 0xF6: return (2, f'INC ${rb(addr+1):02X},X')
    elif op == 0xFC: return (4, f'JSR (${rw(addr+1):04X},X)')
    elif op == 0xD6: return (2, f'DEC ${rb(addr+1):02X},X')    
    elif op == 0x9E: return (3, f'STZ ${rw(addr+1):04X},X')
    elif op == 0x3C: return (3, f'BIT ${rw(addr+1):04X},X')
    else: return (1, f'?? ${op:02X}')

def disasm(bank, start, length):
    p = start
    end = start + length
    bank_off = r(bank, 0)
    while p < end:
        addr = r(bank, p)
        if addr >= len(rom):
            break
        size, txt = peek(bank, p)
        print(f'  ${bank:02X}:{p:04X} ({addr:06X}): {txt}')
        
        # Track m/x mode changes
        if rom[addr] == 0xE2:
            imm = rom[addr+1]
            txt2 = ''
            if imm & 0x10: txt2 += 'm8 '
            if imm & 0x20: txt2 += 'x8 '
            if imm & 0x01: txt2 += 'c '
            if txt2: print(f'    ; mode -> {txt2}')
        elif rom[addr] == 0xC2:
            imm = rom[addr+1]
            txt2 = ''
            if imm & 0x10: txt2 += 'm16 '
            if imm & 0x20: txt2 += 'x16 '
            if imm & 0x01: txt2 += 'c=0 '
            if txt2: print(f'    ; mode -> {txt2}')
        
        p += size

print('=== Main entry: $80:90DA (0x90DA) ===')
disasm(0x80, 0x90DA, 0x100)

print('\n=== Sub $80:90CD ===')
disasm(0x80, 0x90CD, 20)

print('\n=== $B5:818D (entry 0) ===')
disasm(0xB5, 0x818D, 64)

print('\n=== $B5:8132 (entry 5) ===')
disasm(0xB5, 0x8132, 32)

print('\n=== $B5:8030 (entry 1) ===')
disasm(0xB5, 0x8030, 48)
