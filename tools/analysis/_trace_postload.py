rom = open('roms/dkc2.sfc', 'rb').read()

def r(bank, addr):
    return (bank & 0x3F) * 0x10000 + addr

def peek(bank, p, m_flag=0, x_flag=0):
    """m_flag: 0=16bit A, 1=8bit A; x_flag: 0=16bit XY, 1=8bit XY"""
    addr = r(bank, p)
    if addr >= len(rom): return (1, '???', 0xFF, False, 0)
    op = rom[addr]
    txt = ''
    is_branch = False
    branch_target = 0
    
    single_map = {
        0xEA:'NOP', 0x6B:'RTL', 0x60:'RTS', 0x40:'RTI',
        0xCA:'DEX', 0xE8:'INX', 0x88:'DEY', 0xC8:'INY',
        0xDA:'PHX', 0x5A:'PHY', 0xFA:'PLX', 0x7A:'PLY',
        0x48:'PHA', 0x68:'PLA', 0x8B:'PHB', 0xAB:'PLB',
        0x0B:'PHD', 0x2B:'PLD', 0x9A:'TXS', 0xBA:'TSX',
        0xAA:'TAX', 0x8A:'TXA', 0xA8:'TAY', 0x98:'TYA',
        0x5B:'TCD', 0x7B:'TDC', 0x1B:'TCS', 0x3B:'TSC',
        0xEB:'XBA', 0x18:'CLC', 0x38:'SEC', 0x58:'CLI',
        0x78:'SEI', 0x08:'PHP', 0x28:'PLP', 0x4B:'PHK',
        0x1A:'INC A', 0x3A:'DEC A', 0x0A:'ASL A', 0x4A:'LSR A',
        0x2A:'ROL A', 0x6A:'ROR A', 0xFB:'XCE', 0xF8:'SED',
        0xD8:'CLD', 0x00:'BRK', 0xDB:'STP', 0xCB:'WAI',
        0x42:'WDM', 0x9B:'TXY', 0xBB:'TYS',
    }
    if op in single_map:
        return (1, single_map[op], op, False, 0)
    
    if op == 0xE2: v = rom[addr+1]; return (2, f'SEP #${v:02X}', op, False, 0)
    if op == 0xC2: v = rom[addr+1]; return (2, f'REP #${v:02X}', op, False, 0)
    if op == 0x64: return (2, f'STZ ${rom[addr+1]:02X}', op, False, 0)
    if op == 0x85: return (2, f'STA ${rom[addr+1]:02X}', op, False, 0)
    if op == 0x86: return (2, f'STX ${rom[addr+1]:02X}', op, False, 0)
    if op == 0x84: return (2, f'STY ${rom[addr+1]:02X}', op, False, 0)
    if op == 0x24: return (2, f'BIT ${rom[addr+1]:02X}', op, False, 0)
    if op == 0xC5: return (2, f'CMP ${rom[addr+1]:02X}', op, False, 0)
    if op == 0xE6: return (2, f'INC ${rom[addr+1]:02X}', op, False, 0)
    if op == 0xC6: return (2, f'DEC ${rom[addr+1]:02X}', op, False, 0)
    if op == 0x95: return (2, f'STA ${rom[addr+1]:02X},X', op, False, 0)
    if op == 0xB5: return (2, f'LDA ${rom[addr+1]:02X},X', op, False, 0)
    if op == 0xA5: return (2, f'LDA ${rom[addr+1]:02X}', op, False, 0)
    if op == 0xA6: return (2, f'LDX ${rom[addr+1]:02X}', op, False, 0)
    if op == 0xA7: return (2, f'LDA [${rom[addr+1]:02X}]', op, False, 0)
    if op == 0xB7: return (2, f'LDA [${rom[addr+1]:02X}],Y', op, False, 0)
    if op == 0x97: return (2, f'STA [${rom[addr+1]:02X}],Y', op, False, 0)
    if op == 0xA1: return (2, f'LDA (${rom[addr+1]:02X},X)', op, False, 0)
    if op == 0x81: return (2, f'STA (${rom[addr+1]:02X},X)', op, False, 0)
    if op == 0xB1: return (2, f'LDA (${rom[addr+1]:02X}),Y', op, False, 0)
    if op == 0x91: return (2, f'STA (${rom[addr+1]:02X}),Y', op, False, 0)
    if op == 0x92: return (2, f'STA (${rom[addr+1]:02X})', op, False, 0)
    if op == 0x94: return (2, f'STY ${rom[addr+1]:02X},X', op, False, 0)
    if op == 0x96: return (2, f'STX ${rom[addr+1]:02X},Y', op, False, 0)
    if op == 0x1E: a16 = imm16(p); return (3, f'ASL {a16:04X},X', op, False, 0)
    if op == 0x3E: a16 = imm16(p); return (3, f'ROL {a16:04X},X', op, False, 0)
    if op == 0x5E: a16 = imm16(p); return (3, f'LSR {a16:04X},X', op, False, 0)
    if op == 0x7E: a16 = imm16(p); return (3, f'ROR {a16:04X},X', op, False, 0)
    if op == 0x1C: return (3, f'TRB {imm16(p):04X}', op, False, 0)
    if op == 0x04: return (2, f'TSB ${rom[addr+1]:02X}', op, False, 0)
    if op == 0x0C: return (3, f'TSB {imm16(p):04X}', op, False, 0)
    if op == 0x14: return (2, f'TRB ${rom[addr+1]:02X}', op, False, 0)
    if op == 0xE0: sz = 3 if not x_flag else 2; return (sz, f'CPX #{imm(p, x_flag):04X}', op, False, 0)
    if op == 0xC0: sz = 3 if not x_flag else 2; return (sz, f'CPY #{imm(p, x_flag):04X}', op, False, 0)
    
    # Branches
    if op in [0xF0, 0xD0, 0x90, 0xB0, 0x80, 0x10, 0x30]:
        disp = rom[addr+1]
        if disp >= 128: disp -= 256
        names = {0xF0:'BEQ', 0xD0:'BNE', 0x90:'BCC', 0xB0:'BCS', 0x80:'BRA', 0x10:'BPL', 0x30:'BMI'}
        target = p + 2 + disp
        txt = f'{names[op]} ${target:04X}'
        return (2, txt, op, True, target)
    
    if op == 0x82:
        if addr+2 >= len(rom): return (1, '???', 0xFF, False, 0)
        disp = rom[addr+1] | (rom[addr+2] << 8)
        if disp >= 32768: disp -= 65536
        target = p + 3 + disp
        return (3, f'BRL ${target:04X}', op, True, target)
    
    # Immediate values depending on mode
    i16 = imm16(p)
    i8 = rom[addr+1]
    
    if op == 0xA9: sz = 3 if not m_flag else 2; return (sz, f'LDA #{imm(p, m_flag):04X}', op, False, 0)
    if op == 0xA2: sz = 3 if not x_flag else 2; return (sz, f'LDX #{imm(p, x_flag):04X}', op, False, 0)
    if op == 0xA0: sz = 3 if not x_flag else 2; return (sz, f'LDY #{imm(p, x_flag):04X}', op, False, 0)
    if op == 0xE2: pass  # handled
    if op == 0xC2: pass
    
    if op == 0x20: return (3, f'JSR {i16:04X}', op, False, i16)
    if op == 0x4C: return (3, f'JMP {i16:04X}', op, False, i16)
    if op == 0x9C: return (3, f'STZ {i16:04X}', op, False, 0)
    if op == 0xAD: return (3, f'LDA {i16:04X}', op, False, 0)
    if op == 0x8D: return (3, f'STA {i16:04X}', op, False, 0)
    if op == 0xAE: return (3, f'LDX {i16:04X}', op, False, 0)
    if op == 0xAC: return (3, f'LDY {i16:04X}', op, False, 0)
    if op == 0x8E: return (3, f'STX {i16:04X}', op, False, 0)
    if op == 0x8C: return (3, f'STY {i16:04X}', op, False, 0)
    if op == 0x0E: return (3, f'ASL {i16:04X}', op, False, 0)
    if op == 0x4E: return (3, f'LSR {i16:04X}', op, False, 0)
    if op == 0xCD: return (3, f'CMP {i16:04X}', op, False, 0)
    if op == 0xCE: return (3, f'DEC {i16:04X}', op, False, 0)
    if op == 0xEC: return (3, f'CPX {i16:04X}', op, False, 0)
    if op == 0xCC: return (3, f'CPY {i16:04X}', op, False, 0)
    if op == 0x09: sz = 3 if not m_flag else 2; return (sz, f'ORA #{imm(p, m_flag):04X}', op, False, 0)
    if op == 0x29: sz = 3 if not m_flag else 2; return (sz, f'AND #{imm(p, m_flag):04X}', op, False, 0)
    if op == 0x49: sz = 3 if not m_flag else 2; return (sz, f'EOR #{imm(p, m_flag):04X}', op, False, 0)
    if op == 0x69: sz = 3 if not m_flag else 2; return (sz, f'ADC #{imm(p, m_flag):04X}', op, False, 0)
    if op == 0xE9: sz = 3 if not m_flag else 2; return (sz, f'SBC #{imm(p, m_flag):04X}', op, False, 0)
    if op == 0xC9: sz = 3 if not m_flag else 2; return (sz, f'CMP #{imm(p, m_flag):04X}', op, False, 0)
    if op == 0x89: sz = 3 if not m_flag else 2; return (sz, f'BIT #{imm(p, m_flag):04X}', op, False, 0)
    if op == 0x2C: return (3, f'BIT {i16:04X}', op, False, 0)
    if op == 0x3C: return (3, f'BIT {i16:04X},X', op, False, 0)
    if op == 0xF4: return (3, f'PEA {i16:04X}', op, False, 0)
    if op == 0xD4: return (2, f'PEI (${rom[addr+1]:02X})', op, False, 0)
    if op == 0x9E: return (3, f'STZ {i16:04X},X', op, False, 0)
    if op == 0xBD: return (3, f'LDA {i16:04X},X', op, False, 0)
    if op == 0x99: return (3, f'STA {i16:04X},Y', op, False, 0)
    if op == 0x9D: return (3, f'STA {i16:04X},X', op, False, 0)
    if op == 0xB9: return (3, f'LDA {i16:04X},Y', op, False, 0)
    if op == 0xD9: return (3, f'CMP {i16:04X},Y', op, False, 0)
    if op == 0xDD: return (3, f'CMP {i16:04X},X', op, False, 0)
    if op == 0xBC: return (3, f'LDY {i16:04X},X', op, False, 0)
    if op == 0xBE: return (3, f'LDX {i16:04X},Y', op, False, 0)
    if op == 0x0D: return (3, f'ORA {i16:04X}', op, False, 0)
    if op == 0x1D: return (3, f'ORA {i16:04X},X', op, False, 0)
    if op == 0x2D: return (3, f'AND {i16:04X}', op, False, 0)
    if op == 0x3D: return (3, f'AND {i16:04X},X', op, False, 0)
    if op == 0x4D: return (3, f'EOR {i16:04X}', op, False, 0)
    if op == 0x6D: return (3, f'ADC {i16:04X}', op, False, 0)
    if op == 0x7D: return (3, f'ADC {i16:04X},X', op, False, 0)
    if op == 0xED: return (3, f'SBC {i16:04X}', op, False, 0)
    if op == 0xFD: return (3, f'SBC {i16:04X},X', op, False, 0)
    if op == 0x22: return (4, f'JSL {rom[addr+1] | (rom[addr+2] << 8) | (rom[addr+3] << 16):06X}', op, False, 0)
    if op == 0x5C: return (4, f'JML {rom[addr+1] | (rom[addr+2] << 8) | (rom[addr+3] << 16):06X}', op, False, 0)
    if op == 0x8F: return (4, f'STA {rom[addr+1] | (rom[addr+2] << 8) | (rom[addr+3] << 16):06X}', op, False, 0)
    if op == 0xAF: return (4, f'LDA {rom[addr+1] | (rom[addr+2] << 8) | (rom[addr+3] << 16):06X}', op, False, 0)
    if op == 0xBF: return (4, f'LDA {rom[addr+1] | (rom[addr+2] << 8) | (rom[addr+3] << 16):06X},X', op, False, 0)
    if op == 0xCF: return (4, f'CMP {rom[addr+1] | (rom[addr+2] << 8) | (rom[addr+3] << 16):06X}', op, False, 0)
    if op == 0xDF: return (4, f'CMP {rom[addr+1] | (rom[addr+2] << 8) | (rom[addr+3] << 16):06X},X', op, False, 0)
    if op == 0x54: return (4, f'MVN ${rom[addr+2]:02X},${rom[addr+1]:02X}', op, False, 0)
    if op == 0x44: return (4, f'MVP ${rom[addr+2]:02X},${rom[addr+1]:02X}', op, False, 0)
    if op == 0x7C: return (3, f'JMP ({i16:04X},X)', op, False, 0)
    if op == 0xFC: return (4, f'JSR ({i16:04X},X)', op, False, 0)
    if op == 0xDC: return (3, f'JMP ({i16:04X})', op, False, 0)
    if op == 0x6C: return (3, f'JMP ({i16:04X})', op, False, 0)
    if op == 0x62: return (3, f'PER ${i16:04X}', op, False, 0)
    
    return (1, f'?? ${op:02X}', op, False, 0)

def imm16(p):
    addr = r(0x80, p)
    return rom[addr+1] | (rom[addr+2] << 8)

def imm(p, flag):
    """Return immediate value based on flag (0=16bit, 1=8bit)"""
    addr = r(0x80, p)
    if not flag:
        return rom[addr+1] | (rom[addr+2] << 8)
    else:
        return rom[addr+1]

def trace(bank, start, limit=800):
    p = start
    m_flag = 0  # 0=16bit, 1=8bit
    x_flag = 0
    end = start + limit
    visited = set()
    
    while p < end:
        if p in visited:
            print(f'  ; REVISIT ${bank:02X}:{p:04X}')
            break
        visited.add(p)
        
        addr = r(bank, p)
        if addr >= len(rom): break
        size, txt, op, is_branch, target = peek(bank, p, m_flag, x_flag)
        
        # Update flags
        if op == 0xE2:  # SEP
            v = rom[addr+1]
            if v & 0x20: m_flag = 1
            if v & 0x10: x_flag = 1
        if op == 0xC2:  # REP
            v = rom[addr+1]
            if v & 0x20: m_flag = 0
            if v & 0x10: x_flag = 0
        
        em = f'[m={m_flag}]' if op in [0xE2, 0xC2, 0x00] else ''
        print(f'${bank:02X}:{p:04X} ({addr:06X}): {txt}')
        
        if op == 0x6B: return  # RTL
        if op == 0x60:  # RTS
            print(f'  ; RTS')
            return
        if op == 0x5C:  # JML
            t = rom[addr+1] | (rom[addr+2] << 8) | (rom[addr+3] << 16)
            b = (t >> 16) & 0xFF
            o = t & 0xFFFF
            print(f'  ; JML to ${b:02X}:{o:04X}')
            return
        if op == 0x4C:  # JMP absolute
            t = rom[addr+1] | (rom[addr+2] << 8)
            print(f'  ; JMP to ${bank:02X}:{t:04X}')
            p = t
            continue
        if is_branch and op == 0x80 and target < p:  # BRA backward
            print(f'  ; *** INFINITE LOOP at ${bank:02X}:{target:04X} -> GAME LOOP? ***')
            return
        if is_branch and op == 0x80:  # BRA forward
            print(f'  ; -> BRA to ${bank:02X}:{target:04X}')
            p = target
            continue
        
        p += size
    
    print(f'  ; STOP (limit)')

print("=" * 60)
print("TRACE FROM $80:92BD (after last JSL $BB loading)")
print("=" * 60)
trace(0x80, 0x92BD)
