import sys, struct
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from disasm65816 import Dis65816, read_word, read_long, rom_offset, OPCODES, IMM8


def make_rom(size=0x400000):
    return bytearray(size)


def test_read_word():
    data = b"\x34\x12\x78\x56"
    assert read_word(data, 0) == 0x1234
    assert read_word(data, 2) == 0x5678


def test_read_long():
    data = b"\x01\x02\x03\x04\x05\x06"
    v = read_long(data, 0)
    assert v == 0x030201, f"got {v:06X}"
    v = read_long(data, 2)
    assert v == 0x050403, f"got {v:06X}"


def test_rom_offset_lorom_mirror():
    """SA-1 ExLoROM mapping (Mode $31): $C0-$FF mirrors $00-$3F."""
    # $C0:8000 -> LoROM mirror: bank 0 * 0x8000 + (0x8000 & 0x7FFF) = 0x0000
    assert rom_offset(None, 0xC08000) == 0x0000
    # $C0:0000 -> 0x0000
    assert rom_offset(None, 0xC00000) == 0x0000
    # $C1:1234 -> bank 1 * 0x8000 + 0x1234 = 0x9234
    assert rom_offset(None, 0xC11234) == 0x9234
    # $FF:FFFE -> bank 0x3F * 0x8000 + 0x7FFE = 0x1FFFFE
    assert rom_offset(None, 0xFFFFFE) == 0x1FFFFE


def test_rom_offset_lorom_fallback():
    # $00:8000 -> LoROM fallback: bank 0, offset 0x0000
    assert rom_offset(None, 0x008000) == 0x0000
    assert rom_offset(None, 0x008002) == 0x0002
    # $7E:8000 -> LoROM: bank 0x7E&0x7F=0x7E -> 0x7E*8000 + 0 = 0x3F0000
    assert rom_offset(None, 0x7E8000) == 0x3F0000


def test_inst_size_16bit_mode():
    dis = Dis65816(b"")
    dis.m = 0
    # LDA #imm -> base 2, +1 in 16-bit mode => 3
    assert dis.inst_size(0xA9, 2) == 3
    # LDA dp -> base 2, NOT in IMM8 => 2
    assert dis.inst_size(0xA5, 2) == 2
    # NOP -> base 1, NOT in IMM8 => 1
    assert dis.inst_size(0xEA, 1) == 1


def test_inst_size_8bit_mode():
    dis = Dis65816(b"")
    dis.m = 1
    assert dis.inst_size(0xA9, 2) == 2  # normal 8-bit
    assert dis.inst_size(0xA5, 2) == 2  # dp unaffected


def test_disasm_1byte():
    dis = Dis65816(b"\xEA\x60\x6B\x40")
    # NOP
    addr, text = dis.disasm_at(0xC00000)
    assert addr == 0xC00001
    assert text == "NOP"
    # RTS
    addr, text = dis.disasm_at(0xC00001)
    assert addr == 0xC00002
    assert text == "RTS"
    # RTL
    addr, text = dis.disasm_at(0xC00002)
    assert addr == 0xC00003
    assert text == "RTL"
    # RTI
    addr, text = dis.disasm_at(0xC00003)
    assert addr == 0xC00004
    assert text == "RTI"


def test_disasm_lda_imm_8bit():
    rom = make_rom()
    rom[0] = 0xA9
    rom[1] = 0x42
    dis = Dis65816(bytes(rom))
    dis.m = 1
    addr, text = dis.disasm_at(0xC00000)
    assert addr == 0xC00002
    assert "#$42" in text or "#$0042" in text


def test_disasm_lda_imm_16bit():
    rom = make_rom()
    rom[0] = 0xA9
    rom[1] = 0x34
    rom[2] = 0x12
    dis = Dis65816(bytes(rom))
    dis.m = 0
    addr, text = dis.disasm_at(0xC00000)
    assert addr == 0xC00003
    assert "#$1234" in text


def test_disasm_branch_rel8():
    rom = make_rom()
    rom[0] = 0xD0  # BNE
    rom[1] = 0xFC  # -4 (backward)
    dis = Dis65816(bytes(rom))
    addr, text = dis.disasm_at(0xC00000)
    assert addr == 0xC00002
    assert "BFFFFE" in text


def test_disasm_jsr():
    rom = make_rom()
    rom[0] = 0x20  # JSR abs
    rom[1] = 0x8B
    rom[2] = 0x88
    dis = Dis65816(bytes(rom))
    addr, text = dis.disasm_at(0xC00000)
    assert addr == 0xC00003
    assert "JSR" in text
    assert "888B" in text


def test_disasm_jsl_long():
    rom = make_rom()
    rom[0] = 0x22  # JSL long
    rom[1] = 0x4C
    rom[2] = 0x80
    rom[3] = 0xB5
    dis = Dis65816(bytes(rom))
    addr, text = dis.disasm_at(0xC00000)
    assert addr == 0xC00004
    assert "JSL" in text
    assert "B5804C" in text


def test_update_state_rep():
    dis = Dis65816(b"")
    # REP #$30 -> clear m (bit5) and x (bit4)
    dis.update_state(0xC2, 0xC00000)
    # uses read_byte at 0xC00001 - we need rom bytes
    dis.data = b"\xC2\x30"
    dis.update_state(0xC2, 0xC00000)
    assert dis.m == 0
    assert dis.x == 0


def test_update_state_sep():
    dis = Dis65816(b"")
    dis.m = 0
    dis.x = 0
    dis.data = b"\xE2\x30"
    dis.update_state(0xE2, 0xC00000)
    assert dis.m == 1
    assert dis.x == 1


def test_disasm_sta_abs():
    rom = make_rom()
    rom[0] = 0x8D  # STA abs
    rom[1] = 0x16
    rom[2] = 0x05
    dis = Dis65816(bytes(rom))
    addr, text = dis.disasm_at(0xC00000)
    assert addr == 0xC00003
    assert "STA" in text
    assert "0516" in text


def test_disasm_stz():
    rom = make_rom()
    rom[0] = 0x9C  # STZ abs
    rom[1] = 0x00
    rom[2] = 0x21
    dis = Dis65816(bytes(rom))
    addr, text = dis.disasm_at(0xC00000)
    assert "STZ" in text
    assert "2100" in text


def test_follow_code_simple():
    rom = make_rom()
    # RTS at 0xC00000
    rom[0] = 0x60
    dis = Dis65816(bytes(rom))
    dis.follow_code(0xC00000)
    assert 0xC00000 in dis.code_regions
    assert len(dis.functions) == 0  # no JSR/JSL, no function


def test_follow_code_with_jsr():
    rom = make_rom()
    # JSR $C0888B, then RTS
    rom[0] = 0x20
    rom[1] = 0x8B
    rom[2] = 0x88
    rom[3] = 0x60
    # Place target at $C0888B -> ROM offset 0x888B
    target_off = 0x888B
    rom[target_off] = 0xA9  # LDA #imm
    rom[target_off+1] = 0x01
    rom[target_off+2] = 0x00
    rom[target_off+3] = 0x60  # RTS
    dis = Dis65816(bytes(rom))
    dis.follow_code(0xC00000)
    assert 0xC00000 in dis.code_regions
    assert 0xC0888B in dis.functions
    assert 0xC0888B in dis.code_regions


def test_follow_code_loop_terminates():
    """Infinite loop (BRA to self) should terminate cleanly."""
    rom = make_rom()
    rom[0] = 0x80  # BRA
    rom[1] = 0xFE  # -2 -> back to self
    dis = Dis65816(bytes(rom))
    dis.follow_code(0xC00000)  # should not hang
    assert 0xC00000 in dis.code_regions


def test_follow_code_indirect_jmp_stops():
    """JMP indirect should stop linear flow (can't statically resolve)."""
    rom = make_rom()
    rom[0] = 0x6C  # JMP [abs]
    rom[1] = 0x00
    rom[2] = 0x10
    rom[3] = 0xEA  # NOP - should not be reached
    dis = Dis65816(bytes(rom))
    dis.follow_code(0xC00000)
    assert 0xC00000 in dis.code_regions
    assert 0xC00003 not in dis.code_regions


def test_follow_code_jml_ext_bank_skipped():
    """JML to bank < C0 should NOT be followed."""
    rom = make_rom()
    rom[0] = 0x5C  # JML long
    rom[1] = 0x00
    rom[2] = 0x80
    rom[3] = 0xB5  # bank $B5 (external)
    rom[4] = 0x60  # RTS - should not be reached
    dis = Dis65816(bytes(rom))
    dis.follow_code(0xC00000)
    assert 0xC00000 in dis.code_regions
    assert 0xB58000 not in dis.code_regions


def test_follow_code_jml_c0_bank_followed():
    """JML to bank C0 should be followed."""
    rom = make_rom()
    rom[0] = 0x5C  # JML long
    rom[1] = 0x8B
    rom[2] = 0x88
    rom[3] = 0xC0  # bank $C0
    rom[4] = 0x60  # RTS - should not be reached
    # Place target at $C0888B -> 0x888B
    target_off = 0x888B
    rom[target_off] = 0x60  # RTS
    dis = Dis65816(bytes(rom))
    dis.follow_code(0xC00000)
    assert 0xC0888B in dis.code_regions


def test_unknown_opcode_skipped():
    rom = make_rom()
    rom[0] = 0xFF  # invalid opcode
    rom[1] = 0x60  # RTS
    dis = Dis65816(bytes(rom))
    addr, text = dis.disasm_at(0xC00000)
    assert "??" in text


def test_function_names_use_correct_casing():
    rom = make_rom()
    rom[0] = 0x20  # JSR
    rom[1] = 0x8B
    rom[2] = 0x88
    rom[3] = 0x60  # RTS
    rom[0x888B] = 0x60
    dis = Dis65816(bytes(rom))
    dis.follow_code(0xC00000)
    assert dis.functions[0xC0888B] == "func_C0888B"
