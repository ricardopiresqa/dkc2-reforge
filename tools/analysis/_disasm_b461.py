rom = open('roms/dkc2.sfc', 'rb').read()

def rb(bank, addr):
    return rom[((bank & 0x3F) * 0x10000) + addr]

class Dis65816:
    def __init__(self, bank):
        self.bank = bank
        self.m = True  # 8-bit A
        self.x = True  # 8-bit X/Y

    def r(self, addr):
        return rb(self.bank, addr)

    def r16(self, addr):
        return rb(self.bank, addr) | (rb(self.bank, addr+1) << 8)

    def imm(self):
        return 1 if self.m else 2

    def immx(self):
        return 1 if self.x else 2

    def op(self, addr):
        b = self.r(addr)
        return _ops.get(b, None)
    
    def disasm(self, start, count=9999, chain=True):
        a = start
        end = start + count
        lines = []
        while a < end:
            mnem, size, callback = _ops.get(self.r(a), (None, 1, None))
            if mnem is None:
                lines.append('%05X: %02x         ???' % (a, self.r(a)))
                a += 1
                if chain:
                    continue
                break
            raw = ' '.join('%02x' % self.r(a+i) for i in range(size))
            operands = ''
            if callback:
                operands = callback(self, a)
            lines.append('%05X: %-8s %-8s %s' % (a, raw, mnem, operands))
            if mnem in ('RTL', 'RTS', 'RTI', 'JMP', 'JML', 'JSL', 'BRA', 'BRL'):
                if chain and mnem in ('BRA', 'BRL'):
                    if mnem == 'BRA':
                        a += self.r(a+1) - 128 if self.r(a+1) & 0x80 else self.r(a+1)
                        a += 2
                        continue
                    else:
                        disp = self.r16(a+1)
                        if disp & 0x8000:
                            disp -= 0x10000
                        a += 3 + disp
                        continue
                if not chain:
                    a += size
                    continue
            a += size
        return '\n'.join(lines)

_ops = {}

def _op(code, name, size, fn=None):
    _ops[code] = (name, size, fn)

# Immediate/accumulator
for c in range(0x00, 0x20): _op(c, '???', 1)
for c in range(0x20, 0x40): _op(c, '???', 1)

_op(0x00, 'BRK', 2, lambda s,a: '%02x' % s.r(a+1))
_op(0x01, 'ORA', 2, lambda s,a: '($%02x,X)' % s.r(a+1))
_op(0x02, 'COP', 2, lambda s,a: '#$%02x' % s.r(a+1))
_op(0x03, 'ORA', 1, lambda s,a: '$%02x,S' % s.r(a))
_op(0x04, 'TSB', 2, lambda s,a: '$%02x' % s.r(a+1))
_op(0x05, 'ORA', 2, lambda s,a: '$%02x' % s.r(a+1))
_op(0x06, 'ASL', 2, lambda s,a: '$%02x' % s.r(a+1))
_op(0x07, 'ORA', 1, lambda s,a: '[$%02x]' % s.r(a))
_op(0x08, 'PHP', 1)
_op(0x09, 'ORA', 2, lambda s,a: '#$%02x' % s.r(a+1))
_op(0x0A, 'ASL', 1)
_op(0x0B, 'PHD', 1)
_op(0x0C, 'TSB', 3, lambda s,a: '$%04x' % s.r16(a+1))
_op(0x0D, 'ORA', 3, lambda s,a: '$%04x' % s.r16(a+1))
_op(0x0E, 'ASL', 3, lambda s,a: '$%04x' % s.r16(a+1))
_op(0x0F, 'ORA', 4, lambda s,a: '$%06x' % (s.r(a+1) | (s.r(a+2) << 8) | (s.r(a+3) << 16)))

_op(0x10, 'BPL', 2, lambda s,a: '$%05X' % (a+2+(s.r(a+1)-256 if s.r(a+1)&0x80 else s.r(a+1))))
_op(0x11, 'ORA', 2, lambda s,a: '($%02x),Y' % s.r(a+1))
_op(0x12, 'ORA', 1, lambda s,a: '($%02x)' % s.r(a))
_op(0x13, 'ORA', 1, lambda s,a: '($%02x),Y' % s.r(a))
_op(0x14, 'TRB', 2, lambda s,a: '$%02x' % s.r(a+1))
_op(0x15, 'ORA', 2, lambda s,a: '$%02x,X' % s.r(a+1))
_op(0x16, 'ASL', 2, lambda s,a: '$%02x,X' % s.r(a+1))
_op(0x17, 'ORA', 1, lambda s,a: '[$%02x],Y' % s.r(a))
_op(0x18, 'CLC', 1)
_op(0x19, 'ORA', 3, lambda s,a: '$%04x,Y' % s.r16(a+1))
_op(0x1A, 'INC', 1) if False else _op(0x1A, 'INA', 1)
_op(0x1B, 'TCS', 1)
_op(0x1C, 'TRB', 3, lambda s,a: '$%04x' % s.r16(a+1))
_op(0x1D, 'ORA', 3, lambda s,a: '$%04x,X' % s.r16(a+1))
_op(0x1E, 'ASL', 3, lambda s,a: '$%04x,X' % s.r16(a+1))
_op(0x1F, 'ORA', 4, lambda s,a: '$%06x' % (s.r(a+1) | (s.r(a+2) << 8) | (s.r(a+3) << 16)))

# JSR/JMP
_op(0x20, 'JSR', 3, lambda s,a: '$%04x' % s.r16(a+1))
_op(0x22, 'JSL', 4, lambda s,a: '$%06x' % (s.r(a+1) | (s.r(a+2) << 8) | (s.r(a+3) << 16)))
_op(0x4C, 'JMP', 3, lambda s,a: '$%04x' % s.r16(a+1))
_op(0x5C, 'JML', 4, lambda s,a: '$%06x' % (s.r(a+1) | (s.r(a+2) << 8) | (s.r(a+3) << 16)))
_op(0x6C, 'JMP', 3, lambda s,a: '($%04x)' % s.r16(a+1))
_op(0x7C, 'JMP', 3, lambda s,a: '($%04x,X)' % s.r16(a+1))
_op(0xDC, 'JML', 4, lambda s,a: '[$%04x]' % s.r16(a+1))

_op(0x40, 'RTI', 1)
_op(0x60, 'RTS', 1)
_op(0x6B, 'RTL', 1)

# Branch
def _bra(addr, delta):
    return '$%05X' % (addr + 2 + (delta - 256 if delta & 0x80 else delta))
_op(0x80, 'BRA', 2, lambda s,a: _bra(a, s.r(a+1)))
_op(0x82, 'BRL', 3, lambda s,a: '$%05X' % (a+3+(d := s.r16(a+1) - (0x10000 if s.r16(a+1) & 0x8000 else 0))))
_op(0x90, 'BCC', 2, lambda s,a: _bra(a, s.r(a+1)))
_op(0xB0, 'BCS', 2, lambda s,a: _bra(a, s.r(a+1)))
_op(0xD0, 'BNE', 2, lambda s,a: _bra(a, s.r(a+1)))
_op(0xF0, 'BEQ', 2, lambda s,a: _bra(a, s.r(a+1)))
_op(0x30, 'BMI', 2, lambda s,a: _bra(a, s.r(a+1)))
_op(0x10, 'BPL', 2, lambda s,a: _bra(a, s.r(a+1)))
_op(0x50, 'BVC', 2, lambda s,a: _bra(a, s.r(a+1)))
_op(0x70, 'BVS', 2, lambda s,a: _bra(a, s.r(a+1)))
_op(0x80, 'BRA', 2, lambda s,a: _bra(a, s.r(a+1)))

# SEP/REP
_op(0xE2, 'SEP', 2, lambda s,a: '#$%02x' % s.r(a+1))
_op(0xC2, 'REP', 2, lambda s,a: '#$%02x' % s.r(a+1))

# LDX/STX etc with immx
_op(0xA0, 'LDY', 2, lambda s,a: '#$%02x' % s.r(a+1))
_op(0xA2, 'LDX', 2, lambda s,a: '#$%02x' % s.r(a+1))
_op(0xE0, 'CPX', 2, lambda s,a: '#$%02x' % s.r(a+1))
_op(0xC0, 'CPY', 2, lambda s,a: '#$%02x' % s.r(a+1))

# 16-bit versions of these
_op(0xA0, 'LDY', 3, lambda s,a: '#$%04x' % s.r16(a+1))
_op(0xA2, 'LDX', 3, lambda s,a: '#$%04x' % s.r16(a+1))
_op(0xE0, 'CPX', 3, lambda s,a: '#$%04x' % s.r16(a+1))
_op(0xC0, 'CPY', 3, lambda s,a: '#$%04x' % s.r16(a+1))

# LDA/STA etc
for imm_vals, imm_op, zp, zpx, zpy, abs_a, abx, aby, ind_x, ind_y, ind, ind_l, sr, lng in [
    ('LDA', 0xA9, 0xA5, 0xB5, 0xB9, 0xAD, 0xBD, 0xB9, 0xA1, 0xB1, 0xB2, 0xA7, 0xB7, 0xAF),
]:
    pass

# Direct page / absolute addressing
def _dp(s,a): return '$%02x' % s.r(a+1)
def _dpx(s,a): return '$%02x,X' % s.r(a+1)
def _dpy(s,a): return '$%02x,Y' % s.r(a+1)
def _abs(s,a): return '$%04x' % s.r16(a+1)
def _absx(s,a): return '$%04x,X' % s.r16(a+1)
def _absy(s,a): return '$%04x,Y' % s.r16(a+1)
def _indx(s,a): return '($%02x,X)' % s.r(a+1)
def _indy(s,a): return '($%02x),Y' % s.r(a+1)
def _ind(s,a): return '($%02x)' % s.r(a+1)
def _indl(s,a): return '[$%02x]' % s.r(a+1)
def _indly(s,a): return '[$%02x],Y' % s.r(a+1)
def _lng(s,a): return '$%06x' % (s.r(a+1) | (s.r(a+2) << 8) | (s.r(a+3) << 16))
def _imm(s,a): return '#$%02x' % s.r(a+1)
def _imm16(s,a): return '#$%04x' % s.r16(a+1)

# Map opcodes to addressing modes
# (opcode, name, mode_fn) where mode_fn returns operand string
_modes = {
    0xA9: ('LDA', 2, _imm), 0xA5: ('LDA', 2, _dp), 0xB5: ('LDA', 2, _dpx),
    0xAD: ('LDA', 3, _abs), 0xBD: ('LDA', 3, _absx), 0xB9: ('LDA', 3, _absy),
    0xA1: ('LDA', 2, _indx), 0xB1: ('LDA', 2, _indy), 0xB2: ('LDA', 2, _ind),
    0xA7: ('LDA', 2, _indl), 0xB7: ('LDA', 2, _indly), 0xAF: ('LDA', 4, _lng),
    
    0x85: ('STA', 2, _dp), 0x95: ('STA', 2, _dpx),
    0x8D: ('STA', 3, _abs), 0x9D: ('STA', 3, _absx), 0x99: ('STA', 3, _absy),
    0x81: ('STA', 2, _indx), 0x91: ('STA', 2, _indy), 0x92: ('STA', 2, _ind),
    0x87: ('STA', 2, _indl), 0x97: ('STA', 2, _indly), 0x8F: ('STA', 4, _lng),
    
    0xA6: ('LDX', 2, _dp), 0xB6: ('LDX', 2, _dpy),
    0xAE: ('LDX', 3, _abs), 0xBE: ('LDX', 3, _absy),
    
    0x86: ('STX', 2, _dp), 0x96: ('STX', 2, _dpy),
    0x8E: ('STX', 3, _abs),
    
    0xA4: ('LDY', 2, _dp), 0xB4: ('LDY', 2, _dpx),
    0xAC: ('LDY', 3, _abs), 0xBC: ('LDY', 3, _absx),
    
    0x84: ('STY', 2, _dp), 0x94: ('STY', 2, _dpx),
    0x8C: ('STY', 3, _abs),
    
    0xE6: ('INC', 2, _dp), 0xEE: ('INC', 3, _abs),
    0xFE: ('INC', 3, _absx),
    0xC6: ('DEC', 2, _dp), 0xCE: ('DEC', 3, _abs),
    
    0xE8: ('INX', 1, None), 0xC8: ('INY', 1, None),
    0xCA: ('DEX', 1, None), 0x88: ('DEY', 1, None),
    
    0x9A: ('TXS', 1, None), 0xBA: ('TSX', 1, None),
    0x9B: ('TXY', 1, None), 0xBB: ('TYX', 1, None),
    0xAA: ('TAX', 1, None), 0x8A: ('TXA', 1, None),
    0xA8: ('TAY', 1, None), 0x98: ('TYA', 1, None),
    0x5A: ('PHY', 1, None), 0x7A: ('PLY', 1, None),
    0xDA: ('PHX', 1, None), 0xFA: ('PLX', 1, None),
    0x48: ('PHA', 1, None), 0x68: ('PLA', 1, None),
    0x8B: ('PHB', 1, None), 0xAB: ('PLB', 1, None),
    0x0B: ('PHD', 1, None), 0x2B: ('PLD', 1, None),
    0x4B: ('PHK', 1, None),
    
    0x18: ('CLC', 1, None), 0x38: ('SEC', 1, None),
    0xD8: ('CLD', 1, None), 0xF8: ('SED', 1, None),
    0x58: ('CLI', 1, None), 0x78: ('SEI', 1, None),
    0xFB: ('XCE', 1, None),
    0xE2: ('SEP', 2, _imm),
    0xC2: ('REP', 2, _imm),
    
    0xEA: ('NOP', 1, None),
    0xCB: ('WAI', 1, None),
    
    0x09: ('ORA', 2, _imm), 0x05: ('ORA', 2, _dp), 0x15: ('ORA', 2, _dpx),
    0x0D: ('ORA', 3, _abs), 0x1D: ('ORA', 3, _absx), 0x19: ('ORA', 3, _absy),
    0x01: ('ORA', 2, _indx), 0x11: ('ORA', 2, _indy), 
    0x03: ('ORA', 1, lambda s,a: '$%02x,S' % s.r(a)),
    0x07: ('ORA', 1, _indl), 0x17: ('ORA', 1, _indly),
    0x0F: ('ORA', 4, _lng), 0x13: ('ORA', 1, lambda s,a: '($%02x),Y' % s.r(a)),
    
    0x29: ('AND', 2, _imm), 0x25: ('AND', 2, _dp), 0x35: ('AND', 2, _dpx),
    0x2D: ('AND', 3, _abs), 0x3D: ('AND', 3, _absx), 0x39: ('AND', 3, _absy),
    0x21: ('AND', 2, _indx), 0x31: ('AND', 2, _indy),
    0x27: ('AND', 1, _indl), 0x37: ('AND', 1, _indly),
    0x2F: ('AND', 4, _lng), 0x23: ('AND', 1, lambda s,a: '$%02x,S' % s.r(a)),
    0x33: ('AND', 1, lambda s,a: '($%02x),Y' % s.r(a)),
    
    0x49: ('EOR', 2, _imm), 0x45: ('EOR', 2, _dp), 0x55: ('EOR', 2, _dpx),
    0x4D: ('EOR', 3, _abs), 0x5D: ('EOR', 3, _absx), 0x59: ('EOR', 3, _absy),
    0x41: ('EOR', 2, _indx), 0x51: ('EOR', 2, _indy),
    0x47: ('EOR', 1, _indl), 0x57: ('EOR', 1, _indly),
    0x4F: ('EOR', 4, _lng),
    
    0x6D: ('ADC', 3, _abs), 0x69: ('ADC', 2, _imm), 0x65: ('ADC', 2, _dp),
    0x75: ('ADC', 2, _dpx), 0x7D: ('ADC', 3, _absx), 0x79: ('ADC', 3, _absy),
    0x61: ('ADC', 2, _indx), 0x71: ('ADC', 2, _indy), 0x72: ('ADC', 2, _ind),
    0x67: ('ADC', 1, _indl), 0x77: ('ADC', 1, _indly),
    0x6F: ('ADC', 4, _lng), 0x63: ('ADC', 1, lambda s,a: '$%02x,S' % s.r(a)),
    0x73: ('ADC', 1, lambda s,a: '($%02x),Y' % s.r(a)),
    
    0xED: ('SBC', 3, _abs), 0xE9: ('SBC', 2, _imm), 0xE5: ('SBC', 2, _dp),
    0xF5: ('SBC', 2, _dpx), 0xFD: ('SBC', 3, _absx), 0xF9: ('SBC', 3, _absy),
    0xE1: ('SBC', 2, _indx), 0xF1: ('SBC', 2, _indy), 0xF2: ('SBC', 2, _ind),
    0xE7: ('SBC', 1, _indl), 0xF7: ('SBC', 1, _indly),
    0xEF: ('SBC', 4, _lng),
    
    0x0A: ('ASL', 1, None), 0x06: ('ASL', 2, _dp), 0x16: ('ASL', 2, _dpx),
    0x0E: ('ASL', 3, _abs), 0x1E: ('ASL', 3, _absx),
    
    0x4A: ('LSR', 1, None), 0x46: ('LSR', 2, _dp), 0x56: ('LSR', 2, _dpx),
    0x4E: ('LSR', 3, _abs), 0x5E: ('LSR', 3, _absx),
    
    0x2A: ('ROL', 1, None), 0x26: ('ROL', 2, _dp), 0x36: ('ROL', 2, _dpx),
    0x2E: ('ROL', 3, _abs), 0x3E: ('ROL', 3, _absx),
    
    0x6A: ('ROR', 1, None), 0x66: ('ROR', 2, _dp), 0x76: ('ROR', 2, _dpx),
    0x6E: ('ROR', 3, _abs), 0x7E: ('ROR', 3, _absx),
    
    0xEB: ('XBA', 1, None),
    
    0xC9: ('CMP', 2, _imm), 0xC5: ('CMP', 2, _dp), 0xD5: ('CMP', 2, _dpx),
    0xCD: ('CMP', 3, _abs), 0xDD: ('CMP', 3, _absx), 0xD9: ('CMP', 3, _absy),
    0xC1: ('CMP', 2, _indx), 0xD1: ('CMP', 2, _indy), 0xD2: ('CMP', 2, _ind),
    0xC7: ('CMP', 1, _indl), 0xD7: ('CMP', 1, _indly),
    0xCF: ('CMP', 4, _lng),
    
    0xE0: ('CPX', 2, _imm), 0xE4: ('CPX', 2, _dp), 0xEC: ('CPX', 3, _abs),
    0xC0: ('CPY', 2, _imm), 0xC4: ('CPY', 2, _dp), 0xCC: ('CPY', 3, _abs),
    
    0x28: ('PLP', 1, None),
    0x08: ('PHP', 1, None),
    
    0x1B: ('TCS', 1, None), 0x1A: ('INC', 1, None),
    0x3A: ('DEC', 1, None),
    0xFB: ('XCE', 1, None),
    
    0x5B: ('TCD', 1, None), 0x7B: ('TDC', 1, None),
    0x3B: ('TSC', 1, None), 0x1B: ('TCS', 1, None),
    
    0x54: ('MVN', 3, lambda s,a: '$%02x,$%02x' % (s.r(a+1), s.r(a+2))),
    0x44: ('MVP', 3, lambda s,a: '$%02x,$%02x' % (s.r(a+1), s.r(a+2))),
    
    0x64: ('STZ', 2, _dp), 0x74: ('STZ', 2, _dpx),
    0x9C: ('STZ', 3, _abs), 0x9E: ('STZ', 3, _absx),
    
    0x89: ('BIT', 2, _imm), 0x24: ('BIT', 2, _dp), 0x2C: ('BIT', 3, _abs),
    0x34: ('BIT', 2, _dpx), 0x3C: ('BIT', 3, _absx),
    
    0x80: ('BRA', 2, lambda s,a: _bra(a, s.r(a+1))),
    0x82: ('BRL', 3, lambda s,a: '$%05X' % (a+3+(d := s.r16(a+1)) if d < 0x8000 else a+3+(d-0x10000))),
    0xF0: ('BEQ', 2, lambda s,a: _bra(a, s.r(a+1))),
    0xD0: ('BNE', 2, lambda s,a: _bra(a, s.r(a+1))),
    0x90: ('BCC', 2, lambda s,a: _bra(a, s.r(a+1))),
    0xB0: ('BCS', 2, lambda s,a: _bra(a, s.r(a+1))),
    0x30: ('BMI', 2, lambda s,a: _bra(a, s.r(a+1))),
    0x10: ('BPL', 2, lambda s,a: _bra(a, s.r(a+1))),
    0x50: ('BVC', 2, lambda s,a: _bra(a, s.r(a+1))),
    0x70: ('BVS', 2, lambda s,a: _bra(a, s.r(a+1))),
}

def _bra(a, delta):
    return '$%05X' % (a + 2 + (delta - 256 if delta & 0x80 else delta))

for code, (name, size, mode_fn) in _modes.items():
    _op(code, name, size, mode_fn)

# Override specific entries with correct imm/imm16 based on m/x flags
# We'll handle that in disasm

c = Dis65816(0x80)

# Actually let me rebuild with proper flag tracking
class Dis65816V2:
    def __init__(self, bank):
        self.bank = bank
        self.m = True
        self.x = True

    def r(self, addr):
        return rom[((self.bank & 0x3F) * 0x10000) + addr]

    def r16(self, addr):
        return self.r(addr) | (self.r(addr+1) << 8)

    def disasm(self, start, count=9999):
        a = start
        end = start + count
        lines = []
        while a < end:
            b = self.r(a)
            mnem = None
            size = 1
            oper = ''
            
            # Track flag changes
            if b == 0xE2:  # SEP
                val = self.r(a+1)
                if val & 0x20: self.m = True
                if val & 0x10: self.x = True
                lines.append('%05X: %02x %02x      SEP     #$%02x' % (a, b, self.r(a+1), val))
                a += 2
                continue
            elif b == 0xC2:  # REP
                val = self.r(a+1)
                if val & 0x20: self.m = False
                if val & 0x10: self.x = False
                lines.append('%05X: %02x %02x      REP     #$%02x' % (a, b, self.r(a+1), val))
                a += 2
                continue

            # Handle based on opcode
            if b in (0xA9,):  # LDA immediate
                if self.m:
                    lines.append('%05X: %02x %02x      LDA     #$%02x' % (a, b, self.r(a+1), self.r(a+1)))
                    a += 2
                else:
                    lines.append('%05X: %02x %02x %02x   LDA     #$%04x' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                    a += 3
                continue
            
            if b in (0xA2,):  # LDX immediate
                if self.x:
                    lines.append('%05X: %02x %02x      LDX     #$%02x' % (a, b, self.r(a+1), self.r(a+1)))
                    a += 2
                else:
                    lines.append('%05X: %02x %02x %02x   LDX     #$%04x' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                    a += 3
                continue

            if b in (0xA0,):  # LDY immediate
                if self.x:
                    lines.append('%05X: %02x %02x      LDY     #$%02x' % (a, b, self.r(a+1), self.r(a+1)))
                    a += 2
                else:
                    lines.append('%05X: %02x %02x %02x   LDY     #$%04x' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                    a += 3
                continue

            if b in (0xE0,):  # CPX immediate
                if self.x:
                    lines.append('%05X: %02x %02x      CPX     #$%02x' % (a, b, self.r(a+1), self.r(a+1)))
                    a += 2
                else:
                    lines.append('%05X: %02x %02x %02x   CPX     #$%04x' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                    a += 3
                continue

            if b in (0xC0,):  # CPY immediate
                if self.x:
                    lines.append('%05X: %02x %02x      CPY     #$%02x' % (a, b, self.r(a+1), self.r(a+1)))
                    a += 2
                else:
                    lines.append('%05X: %02x %02x %02x   CPY     #$%04x' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                    a += 3
                continue

            if b in (0x09, 0x29, 0x49, 0x69, 0xC9, 0xE9):  # ORA/AND/EOR/ADC/CMP/SBC immediate
                if self.m:
                    lines.append('%05X: %02x %02x      %-6s  #$%02x' % (a, b, self.r(a+1), _opnames.get(b,b), self.r(a+1)))
                    a += 2
                else:
                    lines.append('%05X: %02x %02x %02x   %-6s  #$%04x' % (a, b, self.r(a+1), self.r(a+2), _opnames.get(b,b), self.r16(a+1)))
                    a += 3
                continue

            if b in (0x89,):  # BIT immediate
                if self.m:
                    lines.append('%05X: %02x %02x      BIT     #$%02x' % (a, b, self.r(a+1), self.r(a+1)))
                    a += 2
                else:
                    lines.append('%05X: %02x %02x %02x   BIT     #$%04x' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                    a += 3
                continue

            # Handle all table-based opcodes
            # (I'll just use a big table approach)

            # Fall through to table
            info = _modes.get(b)
            if info:
                name, sz, mode_fn = info
                if mode_fn:
                    oper = mode_fn(self, a)
                raw = ' '.join('%02x' % self.r(a+i) for i in range(sz))
                lines.append('%05X: %-8s %-6s %s' % (a, raw, name, oper))
                a += sz
                continue
            
            lines.append('%05X: %02x         ???' % (a, b))
            a += 1
        return '\n'.join(lines)

_opnames = {0x09:'ORA', 0x29:'AND', 0x49:'EOR', 0x69:'ADC', 0xC9:'CMP', 0xE9:'SBC'}

# Actually let me just make a simpler version that works
# and use a better approach with the table but handling immediate sizes dynamically

c2 = Dis65816V2(0x80)
print("=== $80:B461-$B700 (Title handler + attract) ===")
print(c2.disasm(0xB461, 0xB700 - 0xB461))
print()

print("=== $80:A2C0-$A310 (Handler $A2CF) ===")
print(c2.disasm(0xA2C0, 0xA310 - 0xA2C0))
print()

print("=== $80:A800-$A900 (Handler $A86C) ===")
print(c2.disasm(0xA800, 0xA900 - 0xA800))
print()

print("=== $80:99C0-$9A40 (Handler $99C3) ===")
print(c2.disasm(0x99C0, 0x9A40 - 0x99C0))
print()

print("=== $80:B0E0-$B110 ===")
print(c2.disasm(0xB0E0, 0xB110 - 0xB0E0))
print()

print("=== $80:A5F0-$A670 (HDMA/gameplay mode) ===")
c2.m = False
c2.x = False
print(c2.disasm(0xA5F0, 0xA670 - 0xA5F0))
