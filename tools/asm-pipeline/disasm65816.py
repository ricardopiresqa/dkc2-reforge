"""
DKC2 Reforge — Minimal 65816 Disassembler
Le a ROM, segue o reset vector, identifica codigo vs dados.
Gera: memory map entries, function list, cross-references.
"""

import struct
import sys
from pathlib import Path


# 65816 opcode table (core instructions only)
OPCODES = {
    0xEA: ("NOP", 1),
    0x00: ("BRK", 1),
    0x40: ("RTI", 1),
    0x60: ("RTS", 1),
    0x6B: ("RTL", 1),
    0x20: ("JSR abs", 3),
    0x22: ("JSL long", 4),
    0x4C: ("JMP abs", 3),
    0x5C: ("JML long", 4),
    0x6C: ("JMP [abs]", 3),
    0x7C: ("JMP [abs,X]", 3),
    0x80: ("BRA rel8", 2),
    0x82: ("BRL rel16", 3),
    0x10: ("BPL rel8", 2),
    0x30: ("BMI rel8", 2),
    0x50: ("BVC rel8", 2),
    0x70: ("BVS rel8", 2),
    0x90: ("BCC rel8", 2),
    0xB0: ("BCS rel8", 2),
    0xD0: ("BNE rel8", 2),
    0xF0: ("BEQ rel8", 2),
    # LDA
    0xA9: ("LDA #imm", 2),
    0xAD: ("LDA abs", 3),
    0xAF: ("LDA long", 4),
    0xBD: ("LDA abs,X", 3),
    0xB9: ("LDA abs,Y", 3),
    0xBF: ("LDA long,X", 4),
    0xA5: ("LDA dp", 2),
    0xB5: ("LDA dp,X", 2),
    0xA1: ("LDA (dp,X)", 2),
    0xB1: ("LDA (dp),Y", 2),
    0xB2: ("LDA (dp)", 2),
    0xA7: ("LDA [dp]", 2),
    0xB7: ("LDA [dp],Y", 2),
    # STA
    0x8D: ("STA abs", 3),
    0x8F: ("STA long", 4),
    0x9D: ("STA abs,X", 3),
    0x99: ("STA abs,Y", 3),
    0x9F: ("STA long,X", 4),
    0x85: ("STA dp", 2),
    0x95: ("STA dp,X", 2),
    0x81: ("STA (dp,X)", 2),
    0x91: ("STA (dp),Y", 2),
    0x92: ("STA (dp)", 2),
    0x87: ("STA [dp]", 2),
    0x97: ("STA [dp],Y", 2),
    # LDX
    0xA2: ("LDX #imm", 2),
    0xAE: ("LDX abs", 3),
    0xBE: ("LDX abs,Y", 3),
    0xA6: ("LDX dp", 2),
    0xB6: ("LDX dp,Y", 2),
    # LDY
    0xA0: ("LDY #imm", 2),
    0xAC: ("LDY abs", 3),
    0xBC: ("LDY abs,X", 3),
    0xA4: ("LDY dp", 2),
    0xB4: ("LDY dp,X", 2),
    # STX
    0x8E: ("STX abs", 3),
    0x86: ("STX dp", 2),
    0x96: ("STX dp,Y", 2),
    # STY
    0x8C: ("STY abs", 3),
    0x84: ("STY dp", 2),
    0x94: ("STY dp,X", 2),
    # STZ
    0x9C: ("STZ abs", 3),
    0x9E: ("STZ abs,X", 3),
    0x64: ("STZ dp", 2),
    0x74: ("STZ dp,X", 2),
    # INC/DEC
    0xE8: ("INX", 1),
    0xC8: ("INY", 1),
    0x1A: ("INC A", 1),
    0xE6: ("INC dp", 2),
    0xF6: ("INC dp,X", 2),
    0xEE: ("INC abs", 3),
    0xFE: ("INC abs,X", 3),
    0xCA: ("DEX", 1),
    0x88: ("DEY", 1),
    0x3A: ("DEC A", 1),
    0xC6: ("DEC dp", 2),
    0xD6: ("DEC dp,X", 2),
    0xCE: ("DEC abs", 3),
    0xDE: ("DEC abs,X", 3),
    # Transfer
    0xAA: ("TAX", 1),
    0x8A: ("TXA", 1),
    0xA8: ("TAY", 1),
    0x98: ("TYA", 1),
    0xBA: ("TSX", 1),
    0x9A: ("TXS", 1),
    0x5A: ("PHY", 1),
    0x7A: ("PLY", 1),
    0x48: ("PHA", 1),
    0x68: ("PLA", 1),
    0xDA: ("PHX", 1),
    0xFA: ("PLX", 1),
    0x8B: ("PHB", 1),
    0xAB: ("PLB", 1),
    0x0B: ("PHD", 1),
    0x2B: ("PLD", 1),
    0x4B: ("PEI (dp)", 2),
    0x62: ("PER rel16", 3),
    0xF4: ("PEA abs", 3),
    # Arithmetic
    0x69: ("ADC #imm", 2),
    0x6D: ("ADC abs", 3),
    0x6F: ("ADC long", 4),
    0x7D: ("ADC abs,X", 3),
    0x79: ("ADC abs,Y", 3),
    0x65: ("ADC dp", 2),
    0x75: ("ADC dp,X", 2),
    0x61: ("ADC (dp,X)", 2),
    0x71: ("ADC (dp),Y", 2),
    0x72: ("ADC (dp)", 2),
    0x67: ("ADC [dp]", 2),
    0x77: ("ADC [dp],Y", 2),
    0xE9: ("SBC #imm", 2),
    0xED: ("SBC abs", 3),
    0xEF: ("SBC long", 4),
    0xFD: ("SBC abs,X", 3),
    0xF9: ("SBC abs,Y", 3),
    0xE5: ("SBC dp", 2),
    0xF5: ("SBC dp,X", 2),
    0xE1: ("SBC (dp,X)", 2),
    0xF1: ("SBC (dp),Y", 2),
    0xF2: ("SBC (dp)", 2),
    0xE7: ("SBC [dp]", 2),
    0xF7: ("SBC [dp],Y", 2),
    # AND/ORA/EOR
    0x29: ("AND #imm", 2),
    0x2D: ("AND abs", 3),
    0x2F: ("AND long", 4),
    0x3D: ("AND abs,X", 3),
    0x39: ("AND abs,Y", 3),
    0x25: ("AND dp", 2),
    0x35: ("AND dp,X", 2),
    0x21: ("AND (dp,X)", 2),
    0x31: ("AND (dp),Y", 2),
    0x32: ("AND (dp)", 2),
    0x27: ("AND [dp]", 2),
    0x37: ("AND [dp],Y", 2),
    0x09: ("ORA #imm", 2),
    0x0D: ("ORA abs", 3),
    0x0F: ("ORA long", 4),
    0x1D: ("ORA abs,X", 3),
    0x19: ("ORA abs,Y", 3),
    0x05: ("ORA dp", 2),
    0x15: ("ORA dp,X", 2),
    0x01: ("ORA (dp,X)", 2),
    0x11: ("ORA (dp),Y", 2),
    0x12: ("ORA (dp)", 2),
    0x07: ("ORA [dp]", 2),
    0x17: ("ORA [dp],Y", 2),
    0x49: ("EOR #imm", 2),
    0x4D: ("EOR abs", 3),
    0x4F: ("EOR long", 4),
    0x5D: ("EOR abs,X", 3),
    0x59: ("EOR abs,Y", 3),
    0x45: ("EOR dp", 2),
    0x55: ("EOR dp,X", 2),
    0x41: ("EOR (dp,X)", 2),
    0x51: ("EOR (dp),Y", 2),
    0x52: ("EOR (dp)", 2),
    0x47: ("EOR [dp]", 2),
    0x57: ("EOR [dp],Y", 2),
    # Shift
    0x0A: ("ASL A", 1),
    0x0E: ("ASL abs", 3),
    0x1E: ("ASL abs,X", 3),
    0x06: ("ASL dp", 2),
    0x16: ("ASL dp,X", 2),
    0x4A: ("LSR A", 1),
    0x4E: ("LSR abs", 3),
    0x5E: ("LSR abs,X", 3),
    0x46: ("LSR dp", 2),
    0x56: ("LSR dp,X", 2),
    0x2A: ("ROL A", 1),
    0x2E: ("ROL abs", 3),
    0x3E: ("ROL abs,X", 3),
    0x26: ("ROL dp", 2),
    0x36: ("ROL dp,X", 2),
    0x6A: ("ROR A", 1),
    0x6E: ("ROR abs", 3),
    0x7E: ("ROR abs,X", 3),
    0x66: ("ROR dp", 2),
    0x76: ("ROR dp,X", 2),
    # Compare
    0xC9: ("CMP #imm", 2),
    0xCD: ("CMP abs", 3),
    0xCF: ("CMP long", 4),
    0xDD: ("CMP abs,X", 3),
    0xD9: ("CMP abs,Y", 3),
    0xC5: ("CMP dp", 2),
    0xD5: ("CMP dp,X", 2),
    0xC1: ("CMP (dp,X)", 2),
    0xD1: ("CMP (dp),Y", 2),
    0xD2: ("CMP (dp)", 2),
    0xC7: ("CMP [dp]", 2),
    0xD7: ("CMP [dp],Y", 2),
    0xE0: ("CPX #imm", 2),
    0xEC: ("CPX abs", 3),
    0xE4: ("CPX dp", 2),
    0xC0: ("CPY #imm", 2),
    0xCC: ("CPY abs", 3),
    0xC4: ("CPY dp", 2),
    # Flag
    0x18: ("CLC", 1),
    0x38: ("SEC", 1),
    0x58: ("CLI", 1),
    0x78: ("SEI", 1),
    0xB8: ("CLV", 1),
    0xD8: ("CLD", 1),
    0xF8: ("SED", 1),
    0xC2: ("REP #imm", 2),
    0xE2: ("SEP #imm", 2),
    0xFB: ("XCE", 1),
    0x28: ("PLP", 1),
    0x08: ("PHP", 1),
    # Misc
    0x9B: ("STY dp,X", 2),  # alias
    0x54: ("MVN bank24, bank24", 3),
    0x44: ("MVP bank24, bank24", 3),
     0xEB: ("XBA", 1),
    0x89: ("BIT #imm", 2),
    0x2C: ("BIT abs", 3),
    0x3C: ("BIT abs,X", 3),
    0x24: ("BIT dp", 2),
    0x34: ("BIT dp,X", 2),
    # Missing 65816 opcodes
    0x1B: ("TCS", 1),    # Transfer C to Stack (16-bit)
    0x3B: ("TSC", 1),    # Transfer Stack to C (16-bit)
    0x5B: ("TCD", 1),    # Transfer C to Direct Page (16-bit)
    0x7B: ("TDC", 1),    # Transfer Direct Page to C (16-bit)
    0xDB: ("STP", 1),    # Stop
    0xCB: ("WAI", 1),    # Wait for Interrupt
    0x02: ("STP", 1),    # Immediate stop (or COP)
    0x42: ("WDM", 2),    # Reserved
    0x53: ("TAM", 2),    # Transfer A to (accum) — actually TCS for 65816... 
    0x1C: ("TRB abs", 3),
    0x0C: ("TSB abs", 3),
    0x14: ("TRB dp", 2),
    0x04: ("TSB dp", 2),
    0x03: ("ORA dp,S", 2),
    0x13: ("ORA (dp,S),Y", 2),
    0x23: ("AND dp,S", 2),
    0x33: ("AND (dp,S),Y", 2),
    0x43: ("EOR dp,S", 2),
    0x53: ("EOR (dp,S),Y", 2),
    0x63: ("ADC dp,S", 2),
    0x73: ("ADC (dp,S),Y", 2),
    0x83: ("CMP dp,S", 2),
    0x93: ("CMP (dp,S),Y", 2),
    0xA3: ("LDA dp,S", 2),
    0xB3: ("LDA (dp,S),Y", 2),
    0xC3: ("STA dp,S", 2),
    0xD3: ("STA (dp,S),Y", 2),
    0xE3: ("SBC dp,S", 2),
    0xF3: ("SBC (dp,S),Y", 2),
}


def read_word(data, addr):
    return struct.unpack_from("<H", data, addr)[0]


def read_long(data, addr):
    return struct.unpack_from("<I", data, addr)[0] & 0xFFFFFF


def lorom_addr(bank, offset):
    """LoROM mapping: bank*0x8000 + (offset & 0x7FFF)"""
    return bank * 0x8000 + (offset & 0x7FFF)


def rom_offset(bank, addr_lo):
    """Convert SNES addr to ROM file offset.
    DKC2 SA-1 ExLoROM (mode $31):
    - $00:8000-$3F:FFFF -> LoROM, file 0x000000-0x1FFFFF (32K per bank)
    - $80:8000-$BF:FFFF -> FastROM, file 0x200000-0x3FFFFF (32K per bank)
    - $C0:0000-$FF:FFFF -> LoROM mirror of $00-$3F (32K per bank)
    """
    bank_num = (addr_lo >> 16) & 0xFF
    offset = addr_lo & 0xFFFF
    if bank_num >= 0xC0:
        phys_bank = bank_num - 0xC0
        return phys_bank * 0x8000 + (offset & 0x7FFF)
    if bank_num >= 0x80:
        phys_bank = bank_num - 0x80
        return phys_bank * 0x8000 + (offset & 0x7FFF) + 0x200000
    phys_bank = bank_num
    return phys_bank * 0x8000 + (offset & 0x7FFF)


# Mode-sensitive opcodes: size depends on accumulator/index bit
MODE_SENSITIVE = {0xA9, 0xAD, 0xAF, 0xBD, 0xB9, 0xBF,  # LDA
                  0xA5, 0xB5, 0xA1, 0xB1, 0xB2, 0xA7, 0xB7,
                  0xA2, 0xAE, 0xBE, 0xA6, 0xB6,  # LDX
                  0xA0, 0xAC, 0xBC, 0xA4, 0xB4,  # LDY
                  0xE8, 0xC8, 0xCA, 0x88,  # INX, INY, DEX, DEY
                  0xC9, 0xCD, 0xCF, 0xDD, 0xD9, 0xC5, 0xD5, 0xC1, 0xD1, 0xD2, 0xC7, 0xD7,  # CMP
                  0xE0, 0xEC, 0xE4, 0xC0, 0xCC, 0xC4,  # CPX, CPY
                  0x69, 0x6D, 0x6F, 0x7D, 0x79, 0x65, 0x75, 0x61, 0x71, 0x72, 0x67, 0x77,  # ADC
                  0xE9, 0xED, 0xEF, 0xFD, 0xF9, 0xE5, 0xF5, 0xE1, 0xF1, 0xF2, 0xE7, 0xF7,  # SBC
                  0x29, 0x2D, 0x2F, 0x3D, 0x39, 0x25, 0x35, 0x21, 0x31, 0x32, 0x27, 0x37,  # AND
                  0x09, 0x0D, 0x0F, 0x1D, 0x19, 0x05, 0x15, 0x01, 0x11, 0x12, 0x07, 0x17,  # ORA
                  0x49, 0x4D, 0x4F, 0x5D, 0x59, 0x45, 0x55, 0x41, 0x51, 0x52, 0x47, 0x57,  # EOR
                  0x89, 0x2C, 0x3C, 0x24, 0x34,  # BIT
                  0x0A, 0x0E, 0x1E, 0x06, 0x16,  # ASL
                  0x4A, 0x4E, 0x5E, 0x46, 0x56,  # LSR
                  0x2A, 0x2E, 0x3E, 0x26, 0x36,  # ROL
                  0x6A, 0x6E, 0x7E, 0x66, 0x76,  # ROR
                  }

# Opcodes whose immediate form size depends on mode
IMM_MODE_SENSITIVE = {0xA9, 0xA2, 0xA0, 0xC9, 0xE0, 0xC0, 0x69, 0xE9, 0x29, 0x09, 0x49, 0x89}

# #imm opcodes that need mode tracking
IMM8 = {0xA9, 0xA2, 0xA0, 0xC9, 0xE0, 0xC0, 0x69, 0xE9, 0x29, 0x09, 0x49, 0x89}

# dp/abs opcodes whose size depends on mode (base sizes: dp=2, abs=3, long=4)
SIZE_BY_ADDR = {
    # dp: opcode -> base size (2 always for dp)
    0xA5:2, 0xB5:2, 0xA1:2, 0xB1:2, 0xB2:2, 0xA7:2, 0xB7:2, # LDA dp
    0xA6:2, 0xB6:2, # LDX dp
    0xA4:2, 0xB4:2, # LDY dp
    0xC5:2, 0xD5:2, 0xC1:2, 0xD1:2, 0xD2:2, 0xC7:2, 0xD7:2, # CMP dp
    0xE4:2, 0xC4:2, # CPX dp, CPY dp
    0x65:2, 0x75:2, 0x61:2, 0x71:2, 0x72:2, 0x67:2, 0x77:2, # ADC dp
    0xE5:2, 0xF5:2, 0xE1:2, 0xF1:2, 0xF2:2, 0xE7:2, 0xF7:2, # SBC dp
    0x25:2, 0x35:2, 0x21:2, 0x31:2, 0x32:2, 0x27:2, 0x37:2, # AND dp
    0x05:2, 0x15:2, 0x01:2, 0x11:2, 0x12:2, 0x07:2, 0x17:2, # ORA dp
    0x45:2, 0x55:2, 0x41:2, 0x51:2, 0x52:2, 0x47:2, 0x57:2, # EOR dp
    0x24:2, 0x34:2, # BIT dp
    0x06:2, 0x16:2, # ASL dp
    0x46:2, 0x56:2, # LSR dp
    0x26:2, 0x36:2, # ROL dp
    0x66:2, 0x76:2, # ROR dp
    # abs: opcode -> base size (3 for most)
    0xAD:3, 0xBD:3, 0xB9:3, # LDA abs
    0xAE:3, 0xBE:3, # LDX abs
    0xAC:3, 0xBC:3, # LDY abs
    0xCD:3, 0xDD:3, 0xD9:3, # CMP abs
    0xEC:3, 0xCC:3, # CPX abs, CPY abs
    0x6D:3, 0x7D:3, 0x79:3, # ADC abs
    0xED:3, 0xFD:3, 0xF9:3, # SBC abs
    0x2D:3, 0x3D:3, 0x39:3, # AND abs
    0x0D:3, 0x1D:3, 0x19:3, # ORA abs
    0x4D:3, 0x5D:3, 0x59:3, # EOR abs
    0x2C:3, 0x3C:3, # BIT abs
    0x0E:3, 0x1E:3, # ASL abs
    0x4E:3, 0x5E:3, # LSR abs
    0x2E:3, 0x3E:3, # ROL abs
    0x6E:3, 0x7E:3, # ROR abs
    # long: opcode -> base size (4 for most)
    0xAF:4, 0xBF:4, # LDA long
    0xCF:4, # CMP long
    0x6F:4, # ADC long
    0xEF:4, # SBC long
    0x2F:4, # AND long
    0x0F:4, # ORA long
    0x4F:4, # EOR long
}


class Dis65816:
    def __init__(self, rom_data, output_file=None):
        self.data = rom_data
        self.code_regions = set()
        self.functions = {}
        self.labels = {}
        self.visited = set()
        self.m = 1  # accumulator size (1=8bit, 0=16bit)
        self.x = 1  # index size (1=8bit, 0=16bit)
        self._output_file = output_file

    def inst_size(self, op, mode_table_size):
        """Return actual instruction size considering REP/SEP state."""
        # Immediate opcodes: 16-bit mode adds 1 byte
        if op in IMM8 and self.m == 0:
            return mode_table_size + 1
        return mode_table_size

    def read_byte(self, addr):
        offset = rom_offset(None, addr)
        if offset < len(self.data):
            return self.data[offset]
        return 0

    def read_snes_word(self, addr):
        return self.read_byte(addr) | (self.read_byte(addr + 1) << 8)

    def read_snes_long(self, addr):
        return self.read_byte(addr) | (self.read_byte(addr + 1) << 8) | (self.read_byte(addr + 2) << 16)

    def disasm_at(self, addr):
        op = self.read_byte(addr)
        info = OPCODES.get(op)
        if info is None:
            return (addr + 1, f"?? ${op:02X}")

        mnem, base_size = info
        size = self.inst_size(op, base_size)

        if size == 1:
            return (addr + 1, mnem)
        elif mnem.endswith("#imm"):
            if size == 3:
                val = read_word(self.data, rom_offset(None, addr + 1))
                return (addr + 3, f"{mnem} #${val:04X}")
            else:
                val = self.read_byte(addr + 1)
                return (addr + 2, f"{mnem} #${val:02X}")
        elif size == 2:
            val = self.read_byte(addr + 1)
            if mnem.endswith("rel8"):
                target = addr + 2 + (val if val < 128 else val - 256)
                return (addr + 2, f"{mnem[:-4]} ${target:06X}")
            if mnem.endswith("dp"):
                return (addr + 2, f"{mnem} ${val:02X}")
            return (addr + 2, f"{mnem} ${val:02X}")
        elif size == 3:
            val = read_word(self.data, rom_offset(None, addr + 1))
            if mnem.endswith("rel16"):
                target = addr + 3 + (val if val < 0x8000 else val - 0x10000)
                return (addr + 3, f"{mnem[:-5]} ${target:06X}")
            if "abs" in mnem or mnem == "JMP [abs]":
                return (addr + 3, f"{mnem} ${val:04X}")
            if "bank24" in mnem:
                return (addr + 3, mnem.replace("bank24, bank24", f"${val>>8:02X}, ${val&0xFF:02X}"))
            return (addr + 3, f"{mnem} ${val:04X}")
        elif size == 4:
            val = self.read_byte(addr + 1) | (self.read_byte(addr + 2) << 8) | (self.read_byte(addr + 3) << 16)
            if "#" in mnem:
                return (addr + 4, f"{mnem} #${val:06X}")
            return (addr + 4, f"{mnem} ${val:06X}")
        return (addr + 1, f"?? ${op:02X}")

    def update_state(self, op, addr):
        """Track REP/SEP for accumulator/index size."""
        off = rom_offset(None, addr + 1)
        if off >= len(self.data):
            return
        if op == 0xC2:  # REP
            imm = self.data[off]
            if imm & 0x20:
                self.m = 0
            if imm & 0x10:
                self.x = 0
        elif op == 0xE2:  # SEP
            imm = self.data[off]
            if imm & 0x20:
                self.m = 1
            if imm & 0x10:
                self.x = 1

    def follow_code(self, start_addr, depth=0, source="entry"):
        if depth > 20:
            return

        # Save and restore m/x state at top-level entry points
        # so each function starts with reset defaults (m=1, x=1)
        # independent of whatever state the previous trace left behind.
        if depth == 0:
            _saved_m, _saved_x = self.m, self.x
            self.m, self.x = 1, 1

        addr = start_addr

        # If this exact address was already visited, skip
        if addr in self.visited:
            if depth == 0:
                self.m, self.x = _saved_m, _saved_x
            return
        self.visited.add(addr)

        while True:
            self.code_regions.add(addr)

            op = self.read_byte(addr)
            self.update_state(op, addr)

            next_addr, text = self.disasm_at(addr)
            if self._output_file:
                self._output_file.write(f"  ${addr:06X}: {text}\n")

            # Branch instructions - follow both paths
            if op in (0x10, 0x30, 0x50, 0x70, 0x90, 0xB0, 0xD0, 0xF0, 0x80):
                offset = self.read_byte(addr + 1)
                target = addr + 2 + (offset if offset < 128 else offset - 256)
                self.follow_code(target, depth + 1, source)
            elif op == 0x82:  # BRL
                offset = read_word(self.data, rom_offset(None, addr + 1))
                target = addr + 3 + (offset if offset < 0x8000 else offset - 0x10000)
                self.follow_code(target, depth + 1, source)

            # JMP/JML - follow only same-bank jumps (jump tables are tricky)
            if op == 0x4C:  # JMP abs
                target = self.read_snes_word(addr + 1) | (addr >> 16 << 16)
                if target & 0xFF0000 == addr & 0xFF0000:
                    self.follow_code(target, depth + 1, source)
            elif op == 0x5C:  # JML long
                target = self.read_snes_long(addr + 1)
                bank = (target >> 16) & 0xFF
                if bank >= 0xC0:
                    self.follow_code(target, depth + 1, source)

            # JSR/JSL - record function + follow
            if op == 0x20:  # JSR abs
                target = self.read_snes_word(addr + 1) | (addr >> 16 << 16)
                if target not in self.functions:
                    self.functions[target] = f"func_{target:06X}"
                self.follow_code(target, depth + 1, source)
            elif op == 0x22:  # JSL long
                target = self.read_snes_long(addr + 1)
                if target not in self.functions:
                    self.functions[target] = f"func_{target:06X}"
                target_bank = (target >> 16) & 0xFF
                if target_bank >= 0xC0:
                    self.follow_code(target, depth + 1, source)
                else:
                    tag = f"  ; JSL to external bank ${target_bank:02X} (${target:06X}), skipping"
                    if hasattr(self, '_output_file') and self._output_file:
                        self._output_file.write(f"  ; [{source}] JSL ${target:06X} -> ext bank ${target_bank:02X}, skip\n")

            # BRA/BRL are unconditional — don't fall through to next addr
            if op in (0x80, 0x82):
                break

            # Stop at RTS/RTL/RTI, indirect JMPs, BRK/COP
            if op in (0x60, 0x6B, 0x40, 0x6C, 0x7C, 0x00, 0x02):
                break

            addr = next_addr

        if depth == 0:
            self.m, self.x = _saved_m, _saved_x


def main():
    rom_path = "roms/dkc2.sfc"
    data = open(rom_path, "rb").read()

    # Determine entry points from vectors
    # Emulation RESET ($00:FFFC) = $8000 -> $C0:8000
    emu_reset = read_word(data, 0x00FFFC)
    entry_reset = 0xC00000 | emu_reset

    # SA-1 vector area ($FF:FFE0 in flat map = ROM offset 0x3FFFE0)
    # NMI native: addr $8916, IRQ: $877C
    nmi_raw = read_word(data, 0x3FFFE6)
    irq_raw = read_word(data, 0x3FFFEA)

    # Map these as $C0:XXXX targets (SA-1 vectors point to bank C0 code)
    entry_nmi = 0xC00000 | nmi_raw
    entry_irq = 0xC00000 | irq_raw

    print(f"ROM: {rom_path} ({len(data)} bytes)")
    print(f"Entry points:")
    print(f"  1. Reset vector:   ${entry_reset:06X}")
    print(f"  2. NMI vector:     ${entry_nmi:06X}")
    print(f"  3. IRQ vector:     ${entry_irq:06X}")
    print()

    output_path = "tools/disassembly/export/disassembly_full.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        dis = Dis65816(data, output_file=f)

        # Trace from each entry point in sequence
        for label, addr in [("RESET", entry_reset), ("NMI", entry_nmi), ("IRQ", entry_irq)]:
            f.write(f"\n{'='*60}\n")
            f.write(f"=== Following {label} vector at ${addr:06X} ===\n")
            f.write(f"{'='*60}\n")
            # Save state and trace
            dis.follow_code(addr, source=label)

        # Summary
        f.write(f"\n{'='*60}\n")
        f.write(f"=== Summary ===\n")
        f.write(f"Code regions: {len(dis.code_regions)}\n")
        f.write(f"Functions found: {len(dis.functions)}\n")
        for addr, name in sorted(dis.functions.items()):
            f.write(f"  ${addr:06X}: {name}\n")

        # STA targets analysis
        f.write(f"\n{'='*60}\n")
        f.write(f"=== STA targets ===\n")
        sta_targets = {}
        for addr in sorted(dis.visited):
            op = dis.read_byte(addr)
            if op in (0x8D, 0x8F, 0x9D, 0x99, 0x9F, 0x85, 0x95, 0x81, 0x91,
                      0x87, 0x97, 0x8E, 0x86, 0x96, 0x8C, 0x84, 0x94,
                      0x9C, 0x9E, 0x64, 0x74):
                size = 3 if op in (0x8D, 0x8F, 0x9D, 0x99, 0x9F, 0x8E, 0x8C, 0x9C, 0x9E,
                                    0xEE, 0xFE, 0xCE, 0xDE, 0x0E, 0x1E, 0x4E, 0x5E,
                                    0x2E, 0x3E, 0x6E, 0x7E) else 2
                if size == 3:
                    target = dis.read_snes_word(addr + 1)
                else:
                    target = dis.read_byte(addr + 1)
                if target < 0x2000 or (0x7E0000 <= target < 0x800000):
                    key = target
                    sta_targets.setdefault(key, []).append(addr)

        # Write STA targets by address
        f.write(f"Total unique STA targets: {len(sta_targets)}\n\n")
        for target in sorted(sta_targets.keys()):
            srcs = sta_targets[target]
            if target >= 0x7E0000:
                f.write(f"  WRAM ${target:06X}: {len(srcs)} writes\n")
            elif 0x2100 <= target < 0x2200:
                f.write(f"  PPU   ${target:04X}: {len(srcs)} writes\n")
            elif 0x4200 <= target < 0x4300:
                f.write(f"  CPU   ${target:04X}: {len(srcs)} writes\n")
            elif 0x4300 <= target < 0x4400:
                f.write(f"  DMA   ${target:04X}: {len(srcs)} writes\n")
            else:
                f.write(f"  OTHER ${target:04X}: {len(srcs)} writes\n")

        # Also print to console
        print(f"\n=== Summary ===")
        print(f"Total: {len(dis.code_regions)} code regions, {len(dis.functions)} functions, {len(sta_targets)} STA targets")
        print(f"Output written to {output_path}")
        print(f"Functions in bank $C0:")
        for addr, name in sorted(dis.functions.items()):
            bank = (addr >> 16) & 0xFF
            if bank == 0xC0:
                print(f"  ${addr:06X}: {name}")


if __name__ == "__main__":
    main()
