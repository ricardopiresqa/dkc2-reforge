rom = open('roms/dkc2.sfc', 'rb').read()

class Dis65816:
    def __init__(self, bank, m=True, x=True):
        self.bank = bank
        self.m = m
        self.x = x

    def r(self, addr):
        return rom[((self.bank & 0x3F) * 0x10000) + addr]

    def r16(self, addr):
        return self.r(addr) | (self.r(addr+1) << 8)

    def disp8(self, addr):
        d = self.r(addr)
        return d - 256 if d & 0x80 else d

    def disp16(self, addr):
        d = self.r16(addr)
        return d - 0x10000 if d & 0x8000 else d

    def _dp(self, a): return '$%02x' % self.r(a+1)
    def _dpx(self, a): return '$%02x,X' % self.r(a+1)
    def _dpy(self, a): return '$%02x,Y' % self.r(a+1)
    def _abs(self, a): return '$%04x' % self.r16(a+1)
    def _absx(self, a): return '$%04x,X' % self.r16(a+1)
    def _absy(self, a): return '$%04x,Y' % self.r16(a+1)
    def _lng(self, a): return '$%06x' % (self.r(a+1) | (self.r(a+2)<<8) | (self.r(a+3)<<16))
    def _indx(self, a): return '($%02x,X)' % self.r(a+1)
    def _indy(self, a): return '($%02x),Y' % self.r(a+1)
    def _ind(self, a): return '($%02x)' % self.r(a+1)
    def _indl(self, a): return '[$%02x]' % self.r(a+1)
    def _indly(self, a): return '[$%02x],Y' % self.r(a+1)
    def _lngy(self, a): return '$%06x,Y' % (self.r(a+1) | (self.r(a+2)<<8) | (self.r(a+3)<<16))

    def disasm(self, start, count=9999, overrides=None):
        if overrides is None:
            overrides = {}
        a = start
        end = start + count
        lines = []

        T = {}
        def add2(op, name, fn): T[op] = (name, 2, fn)
        def add3(op, name, fn): T[op] = (name, 3, fn)
        def add4(op, name, fn): T[op] = (name, 4, fn)
        def add1(op, name): T[op] = (name, 1, None)

        # LDA
        add2(0xA5,'LDA',self._dp); add2(0xB5,'LDA',self._dpx)
        add3(0xAD,'LDA',self._abs); add3(0xBD,'LDA',self._absx); add3(0xB9,'LDA',self._absy)
        add2(0xA1,'LDA',self._indx); add2(0xB1,'LDA',self._indy); add2(0xB2,'LDA',self._ind)
        add2(0xA7,'LDA',self._indl); add2(0xB7,'LDA',self._indly); add4(0xAF,'LDA',self._lng)
        add4(0xBF,'LDA',self._lngy)
        # STA
        add2(0x85,'STA',self._dp); add2(0x95,'STA',self._dpx)
        add3(0x8D,'STA',self._abs); add3(0x9D,'STA',self._absx); add3(0x99,'STA',self._absy)
        add2(0x81,'STA',self._indx); add2(0x91,'STA',self._indy); add2(0x92,'STA',self._ind)
        add2(0x87,'STA',self._indl); add2(0x97,'STA',self._indly); add4(0x8F,'STA',self._lng)
        # LDX
        add2(0xA6,'LDX',self._dp); add2(0xB6,'LDX',self._dpy)
        add3(0xAE,'LDX',self._abs); add3(0xBE,'LDX',self._absy)
        # STX
        add2(0x86,'STX',self._dp); add2(0x96,'STX',self._dpy); add3(0x8E,'STX',self._abs)
        # LDY
        add2(0xA4,'LDY',self._dp); add2(0xB4,'LDY',self._dpx)
        add3(0xAC,'LDY',self._abs); add3(0xBC,'LDY',self._absx)
        # STY
        add2(0x84,'STY',self._dp); add2(0x94,'STY',self._dpx); add3(0x8C,'STY',self._abs)
        # INC/DEC
        add2(0xE6,'INC',self._dp); add3(0xEE,'INC',self._abs); add3(0xFE,'INC',self._absx)
        add2(0xC6,'DEC',self._dp); add3(0xCE,'DEC',self._abs)
        add3(0xDE,'DEC',self._absx)
        # ORA
        add2(0x05,'ORA',self._dp); add2(0x15,'ORA',self._dpx)
        add3(0x0D,'ORA',self._abs); add3(0x1D,'ORA',self._absx); add3(0x19,'ORA',self._absy)
        add2(0x01,'ORA',self._indx); add2(0x11,'ORA',self._indy)
        add2(0x07,'ORA',self._indl); add2(0x17,'ORA',self._indly); add4(0x0F,'ORA',self._lng)
        # AND
        add2(0x25,'AND',self._dp); add2(0x35,'AND',self._dpx)
        add3(0x2D,'AND',self._abs); add3(0x3D,'AND',self._absx); add3(0x39,'AND',self._absy)
        add2(0x21,'AND',self._indx); add2(0x31,'AND',self._indy)
        add2(0x27,'AND',self._indl); add2(0x37,'AND',self._indly); add4(0x2F,'AND',self._lng)
        # EOR
        add2(0x45,'EOR',self._dp); add2(0x55,'EOR',self._dpx)
        add3(0x4D,'EOR',self._abs); add3(0x5D,'EOR',self._absx); add3(0x59,'EOR',self._absy)
        add2(0x41,'EOR',self._indx); add2(0x51,'EOR',self._indy)
        add2(0x47,'EOR',self._indl); add2(0x57,'EOR',self._indly); add4(0x4F,'EOR',self._lng)
        # ADC
        add2(0x65,'ADC',self._dp); add2(0x75,'ADC',self._dpx)
        add3(0x6D,'ADC',self._abs); add3(0x7D,'ADC',self._absx); add3(0x79,'ADC',self._absy)
        add2(0x61,'ADC',self._indx); add2(0x71,'ADC',self._indy); add2(0x72,'ADC',self._ind)
        add2(0x67,'ADC',self._indl); add2(0x77,'ADC',self._indly); add4(0x6F,'ADC',self._lng)
        # SBC
        add2(0xE5,'SBC',self._dp); add2(0xF5,'SBC',self._dpx)
        add3(0xED,'SBC',self._abs); add3(0xFD,'SBC',self._absx); add3(0xF9,'SBC',self._absy)
        add2(0xE1,'SBC',self._indx); add2(0xF1,'SBC',self._indy); add2(0xF2,'SBC',self._ind)
        add2(0xE7,'SBC',self._indl); add2(0xF7,'SBC',self._indly); add4(0xEF,'SBC',self._lng)
        # CMP
        add2(0xC5,'CMP',self._dp); add2(0xD5,'CMP',self._dpx)
        add3(0xCD,'CMP',self._abs); add3(0xDD,'CMP',self._absx); add3(0xD9,'CMP',self._absy)
        add2(0xC1,'CMP',self._indx); add2(0xD1,'CMP',self._indy); add2(0xD2,'CMP',self._ind)
        add2(0xC7,'CMP',self._indl); add2(0xD7,'CMP',self._indly); add4(0xCF,'CMP',self._lng)
        # BIT
        add2(0x24,'BIT',self._dp); add3(0x2C,'BIT',self._abs)
        add2(0x34,'BIT',self._dpx); add3(0x3C,'BIT',self._absx)
        # STZ
        add2(0x64,'STZ',self._dp); add2(0x74,'STZ',self._dpx)
        add3(0x9C,'STZ',self._abs); add3(0x9E,'STZ',self._absx)
        # ASL/LSR/ROL/ROR mem
        add2(0x06,'ASL',self._dp); add2(0x16,'ASL',self._dpx)
        add3(0x0E,'ASL',self._abs); add3(0x1E,'ASL',self._absx)
        add2(0x46,'LSR',self._dp); add2(0x56,'LSR',self._dpx)
        add3(0x4E,'LSR',self._abs); add3(0x5E,'LSR',self._absx)
        add2(0x26,'ROL',self._dp); add2(0x36,'ROL',self._dpx)
        add3(0x2E,'ROL',self._abs); add3(0x3E,'ROL',self._absx)
        add2(0x66,'ROR',self._dp); add2(0x76,'ROR',self._dpx)
        add3(0x6E,'ROR',self._abs); add3(0x7E,'ROR',self._absx)
        # ASL/LSR/ROL/ROR A
        add1(0x0A,'ASL'); add1(0x4A,'LSR'); add1(0x2A,'ROL'); add1(0x6A,'ROR')
        # TSB/TRB
        add2(0x04,'TSB',self._dp); add3(0x0C,'TSB',self._abs)
        add2(0x14,'TRB',self._dp); add3(0x1C,'TRB',self._abs)
        # MVN/MVP
        T[0x54] = ('MVN',3,None); T[0x44] = ('MVP',3,None)
        # INX/INY/DEX/DEY
        add1(0xE8,'INX'); add1(0xC8,'INY'); add1(0xCA,'DEX'); add1(0x88,'DEY')
        # Stack/transfer/flag
        for op,name in [(0x08,'PHP'),(0x28,'PLP'),(0x48,'PHA'),(0x68,'PLA'),
            (0xDA,'PHX'),(0xFA,'PLX'),(0x5A,'PHY'),(0x7A,'PLY'),
            (0x8B,'PHB'),(0xAB,'PLB'),(0x0B,'PHD'),(0x2B,'PLD'),(0x4B,'PHK'),
            (0xAA,'TAX'),(0x8A,'TXA'),(0xA8,'TAY'),(0x98,'TYA'),
            (0xBA,'TSX'),(0x9A,'TXS'),(0x5B,'TCD'),(0x7B,'TDC'),
            (0x3B,'TSC'),(0x1B,'TCS'),(0x9B,'TXY'),(0xBB,'TYX'),(0xEB,'XBA'),
            (0x18,'CLC'),(0x38,'SEC'),(0xD8,'CLD'),(0xF8,'SED'),
            (0x58,'CLI'),(0x78,'SEI'),(0xFB,'XCE'),
            (0xEA,'NOP'),(0xCB,'WAI'),(0xDB,'STP'),
            (0x1A,'INA'),(0x3A,'DEA')]:
            add1(op, name)
        # BRK/COP
        T[0x00] = ('BRK',2,None); T[0x02] = ('COP',2,None)
        # PEA/PEI/PER
        T[0xF4] = ('PEA',3,None); T[0xD4] = ('PEI',2,self._dp); T[0x62] = ('PER',3,None)

        while a < end:
            b = self.r(a)

            # State override check
            if a in overrides:
                self.m, self.x = overrides[a]
                lines.append('; [OVERRIDE] M=%d X=%d at $%04X' % (self.m, self.x, a))

            # SEP/REP
            if b == 0xE2:
                val = self.r(a+1)
                if val & 0x20: self.m = True
                if val & 0x10: self.x = True
                lines.append('%05X: %02x %02x      SEP     #$%02x' % (a, b, val, val))
                a += 2; continue
            if b == 0xC2:
                val = self.r(a+1)
                if val & 0x20: self.m = False
                if val & 0x10: self.x = False
                lines.append('%05X: %02x %02x      REP     #$%02x' % (a, b, val, val))
                a += 2; continue

            # Branches
            brs = {0x10:'BPL',0x30:'BMI',0x50:'BVC',0x70:'BVS',
                   0x90:'BCC',0xB0:'BCS',0xD0:'BNE',0xF0:'BEQ',0x80:'BRA'}
            if b in brs:
                d = self.disp8(a+1)
                lines.append('%05X: %02x %02x      %-6s $%05X' % (a, b, self.r(a+1), brs[b], a+2+d))
                a += 2; continue
            if b == 0x82:
                d = self.disp16(a+1)
                lines.append('%05X: %02x %02x %02x   BRL     $%05X' % (a, b, self.r(a+1), self.r(a+2), a+3+d))
                a += 3; continue

            # JMP/JSR/JSL/JML
            if b == 0x4C:
                lines.append('%05X: %02x %02x %02x   JMP     $%04x' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                a += 3; continue
            if b == 0x5C:
                ad = self.r(a+1) | (self.r(a+2)<<8) | (self.r(a+3)<<16)
                lines.append('%05X: %02x %02x %02x %02x JML     $%06x' % (a, b, self.r(a+1), self.r(a+2), self.r(a+3), ad))
                a += 4; continue
            if b == 0x20:
                lines.append('%05X: %02x %02x %02x   JSR     $%04x    ; [M=%d X=%d]' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1), self.m, self.x))
                a += 3; continue
            if b == 0x22:
                ad = self.r(a+1) | (self.r(a+2)<<8) | (self.r(a+3)<<16)
                lines.append('%05X: %02x %02x %02x %02x JSL     $%06x    ; [M=%d X=%d]' % (a, b, self.r(a+1), self.r(a+2), self.r(a+3), ad, self.m, self.x))
                a += 4; continue
            if b == 0xFC:
                ad = self.r16(a+1)
                lines.append('%05X: %02x %02x %02x   JSR     ($%04x,X)' % (a, b, self.r(a+1), self.r(a+2), ad))
                a += 3; continue

            # JMP indirect
            if b == 0x6C:
                lines.append('%05X: %02x %02x %02x   JMP     ($%04x)' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                a += 3; continue
            if b == 0x7C:
                lines.append('%05X: %02x %02x %02x   JMP     ($%04x,X)' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                a += 3; continue
            if b == 0xDC:
                lines.append('%05X: %02x %02x %02x   JML     [$%04x]' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                a += 3; continue

            # RTL/RTS/RTI
            if b in (0x6B, 0x60, 0x40):
                lines.append('%05X: %02x         %s' % (a, b, {0x6B:'RTL',0x60:'RTS',0x40:'RTI'}[b]))
                a += 1; continue

            # Immediates (flag-dependent size)
            if b == 0xA9:
                if self.m:
                    lines.append('%05X: %02x %02x      LDA     #$%02x' % (a, b, self.r(a+1), self.r(a+1)))
                    a += 2
                else:
                    lines.append('%05X: %02x %02x %02x   LDA     #$%04x' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                    a += 3
                continue

            if b == 0xA2:
                if self.x:
                    lines.append('%05X: %02x %02x      LDX     #$%02x' % (a, b, self.r(a+1), self.r(a+1)))
                    a += 2
                else:
                    lines.append('%05X: %02x %02x %02x   LDX     #$%04x' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                    a += 3
                continue
            if b == 0xA0:
                if self.x:
                    lines.append('%05X: %02x %02x      LDY     #$%02x' % (a, b, self.r(a+1), self.r(a+1)))
                    a += 2
                else:
                    lines.append('%05X: %02x %02x %02x   LDY     #$%04x' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                    a += 3
                continue
            if b == 0xE0:
                if self.x:
                    lines.append('%05X: %02x %02x      CPX     #$%02x' % (a, b, self.r(a+1), self.r(a+1)))
                    a += 2
                else:
                    lines.append('%05X: %02x %02x %02x   CPX     #$%04x' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                    a += 3
                continue
            if b == 0xC0:
                if self.x:
                    lines.append('%05X: %02x %02x      CPY     #$%02x' % (a, b, self.r(a+1), self.r(a+1)))
                    a += 2
                else:
                    lines.append('%05X: %02x %02x %02x   CPY     #$%04x' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                    a += 3
                continue

            immd = {0x09:'ORA',0x29:'AND',0x49:'EOR',0x69:'ADC',0xC9:'CMP',0xE9:'SBC'}
            if b in immd:
                if self.m:
                    lines.append('%05X: %02x %02x      %-6s  #$%02x' % (a, b, self.r(a+1), immd[b], self.r(a+1)))
                    a += 2
                else:
                    lines.append('%05X: %02x %02x %02x   %-6s  #$%04x' % (a, b, self.r(a+1), self.r(a+2), immd[b], self.r16(a+1)))
                    a += 3
                continue

            if b == 0x89:
                if self.m:
                    lines.append('%05X: %02x %02x      BIT     #$%02x' % (a, b, self.r(a+1), self.r(a+1)))
                    a += 2
                else:
                    lines.append('%05X: %02x %02x %02x   BIT     #$%04x' % (a, b, self.r(a+1), self.r(a+2), self.r16(a+1)))
                    a += 3
                continue

            # Main opcode table
            info = T.get(b)
            if info:
                name, sz, mode_fn = info
                raw = ' '.join('%02x' % self.r(a+i) for i in range(sz))
                if name in ('MVN', 'MVP'):
                    oper = '$%02x,$%02x' % (self.r(a+1), self.r(a+2))
                elif name in ('BRK', 'COP'):
                    oper = '#$%02x' % self.r(a+1)
                elif name == 'PEA':
                    oper = '#$%04x' % self.r16(a+1)
                elif name == 'PER':
                    d = self.disp16(a+1)
                    oper = '#$%05X' % (a+3+d)
                elif mode_fn:
                    oper = mode_fn(a)
                else:
                    oper = ''
                lines.append('%05X: %-8s %-6s %s' % (a, raw, name, oper))
                a += sz
                continue

            lines.append('%05X: %02x         ???' % (a, b))
            a += 1

        return '\n'.join(lines)


import os
os.chdir('C:/Projetos Cursor/dkc2-reforge')

def show(f, label, start, end=None, m=True, x=True, overrides=None):
    sz = (end - start) if end else 0x100
    f.write('=' * 60 + '\n')
    f.write('$80:%04X - %s  [init M=%d X=%d]\n' % (start, label, m, x))
    if overrides:
        for a, (om, ox) in sorted(overrides.items()):
            f.write('; Override: $%04X -> M=%d X=%d\n' % (a, om, ox))
    f.write('=' * 60 + '\n')
    c = Dis65816(0x80, m, x)
    f.write(c.disasm(start, sz, overrides))
    f.write('\n\n')

def show_bank(f, label, bank, start, end=None, m=True, x=True, overrides=None):
    sz = (end - start) if end else 0x100
    f.write('=' * 60 + '\n')
    f.write('$%02X:%04X - %s  [init M=%d X=%d]\n' % (bank, start, label, m, x))
    if overrides:
        for a, (om, ox) in sorted(overrides.items()):
            f.write('; Override: $%04X -> M=%d X=%d\n' % (a, om, ox))
    f.write('=' * 60 + '\n')
    c = Dis65816(bank, m, x)
    f.write(c.disasm(start, sz, overrides))
    f.write('\n\n')

f = open('tools/analysis/_disasm_all.txt', 'w', encoding='ascii')

show(f, "Title Screen Handler", 0xB461, 0xB700, m=False, x=False)
show(f, "Gameplay Entry $80A5F1", 0xA5F1, 0xA700, m=True, x=True)
show(f, "Attract/Level Select $A2CF", 0xA2CF, 0xA400, m=True, x=True)
show(f, "Handler $A86C", 0xA86C, 0xA900, m=True, x=True)
show(f, "Handler $99C3", 0x99C3, 0x9B00, m=True, x=True)
show(f, "Handler $80A5F1 (full to $A800)", 0xA5F1, 0xA800, m=True, x=True)

# Main Game Loop Handler $80B3D7 — entry point after intro transition
# Called via JMP ($0024) from bridge handler $8608
# Entry with M=0 X=0 (16-bit mode, inherited from NMI → $8608 path)
show(f, "Main Game Loop Handler $B3D7+", 0xB3D7, 0xB700, m=False, x=False)

# $8C3D is called from $99C3 (M=1) context, but $8CAC is called from $8C9E (M=0)
# Override M=0 at $8CAC (called from title handler path via JML $808C9E)
show(f, "Handler $8C3D + Dispatcher $8C82 + DMA $8CAC", 0x8C3D, 0x8D00, m=True, x=True,
    overrides={0x8CAC: (False, True), 0x8CC9: (False, False)})

# Bank $B5 — called via JSL from bank $80 handlers
# $B5:8000+ entry: enters with M=0 X=0 (called from $B3D7)
show_bank(f, "Bank $B5:8000+ (JSL $B5800C entry)", 0xB5, 0x8000, 0x8600, m=False, x=False)

# $B5:A800+ entry: enters with M=0 X=0 (called from title handler $B461)
show_bank(f, "Bank $B5:A800+ (JSL $B5A8DA entry)", 0xB5, 0xA800, 0xAE00, m=False, x=False)

# $B5:D000+ entries from dispatch table $8CCE (JML $B5D13B etc)
show_bank(f, "Bank $B5:D000+ (Dispatch table entries)", 0xB5, 0xD000, 0xE000, m=False, x=False)

# Bank $BB — Utility functions called via JSL from bank $80
# $BB:8089 — Palette data load via DMA (JSL $BB8089)
show_bank(f, "Bank $BB:8089 (Palette DMA load)", 0xBB, 0x8089, 0x80C0, m=False, x=False)

# $BB:8D91 — Decompress/VRAM data load (JSL $BB8D91)
show_bank(f, "Bank $BB:8D91 (Decompression function)", 0xBB, 0x8D91, 0x9200, m=False, x=False)

# $BB:91D9 — Init function (JSL $BB91D9)
show_bank(f, "Bank $BB:91D9 (Init)", 0xBB, 0x91D9, 0x9250, m=False, x=False)

f.close()
print('Wrote tools/analysis/_disasm_all.txt')
