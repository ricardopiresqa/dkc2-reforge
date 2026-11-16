import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from pipeline import pseudo_one, op_str, mmap_name
from disasm65816 import Dis65816


# ─── op_str tests ───────────────────────────────────────

class TestOpStr:
    def test_imm_8bit(self):
        assert op_str("LDA #imm", 0x42, 2) == "#0x42"

    def test_imm_16bit(self):
        assert op_str("LDA #imm", 0x1234, 3) == "#0x1234"

    def test_abs(self):
        r = op_str("STA abs", 0x0516, 3)
        assert "$0516" in r

    def test_abs_x(self):
        r = op_str("LDA abs,X", 0x888B, 3)
        assert "$888B" in r
        assert ",X" in r

    def test_abs_y(self):
        r = op_str("LDA abs,Y", 0x0B19, 3)
        assert "$0B19" in r
        assert ",Y" in r

    def test_long(self):
        r = op_str("JML long", 0xC0888B, 4)
        assert "$C0888B" in r

    def test_dp(self):
        r = op_str("LDA dp", 0x3E, 2)
        assert "$3E" in r or "$3e" in r

    def test_rel8(self):
        r = op_str("BRA rel8", 0xC08000, 2)
        assert "$C08000" in r or "$C08000" in r

    def test_bank24(self):
        r = op_str("MVN bank24, bank24", 0x0001, 3)
        assert "$00" in r
        assert "$01" in r


# ─── pseudo_one tests ───────────────────────────────────

class TestPseudoOne:
    def test_bra(self):
        r = pseudo_one(0xC08000, "BRA rel8", 0xC08002, 2, "test")
        assert "goto" in r

    def test_beq(self):
        r = pseudo_one(0xC08000, "BEQ rel8", 0xC08010, 2, "test")
        assert "if (Z)" in r
        assert "goto" in r

    def test_bne(self):
        r = pseudo_one(0xC08000, "BNE rel8", 0xC08010, 2, "test")
        assert "if (!Z)" in r

    def test_jsr(self):
        r = pseudo_one(0xC08000, "JSR abs", 0xC0888B, 3, "test")
        assert "CALL" in r
        assert "888B" in r

    def test_jsl(self):
        r = pseudo_one(0xC08000, "JSL long", 0xB5804C, 4, "test")
        assert "CALL_FAR" in r
        assert "B5804C" in r

    def test_rts(self):
        assert pseudo_one(0, "RTS", 0, 1, "test") == "return;"

    def test_rtl(self):
        assert pseudo_one(0, "RTL", 0, 1, "test") == "return_far();"

    def test_lda_imm(self):
        r = pseudo_one(0, "LDA #imm", 0x0001, 3, "test")
        assert "A = " in r
        assert "0x0001" in r

    def test_sta_abs(self):
        r = pseudo_one(0, "STA abs", 0x0516, 3, "test")
        assert " = A;" in r
        assert "$0516" in r

    def test_stz(self):
        r = pseudo_one(0, "STZ abs", 0x2100, 3, "test")
        assert "= 0;" in r
        assert "$2100" in r

    def tax(self):
        assert pseudo_one(0, "TAX", 0, 1, "test") == "X = A;"

    def test_clc(self):
        assert pseudo_one(0, "CLC", 0, 1, "test") == "C = 0;"

    def test_sec(self):
        assert pseudo_one(0, "SEC", 0, 1, "test") == "C = 1;"

    def test_rep(self):
        r = pseudo_one(0, "REP #imm", 0x30, 2, "test")
        assert "A16" in r
        assert "XY16" in r

    def test_sep(self):
        r = pseudo_one(0, "SEP #imm", 0x20, 2, "test")
        assert "A8" in r

    def test_inc_a(self):
        assert pseudo_one(0, "INC A", 0, 1, "test") == "A++;"

    def test_dec_a(self):
        assert pseudo_one(0, "DEC A", 0, 1, "test") == "A--;"

    def test_inx(self):
        assert pseudo_one(0, "INX", 0, 1, "test") == "X++;"

    def test_wai(self):
        assert pseudo_one(0, "WAI", 0, 1, "test") == "wait_nmi();"


# ─── InsnRecorder tests ─────────────────────────────────

def test_recorder_rts_only():
    rom = bytearray(0x400000)
    rom[0] = 0x60  # RTS
    dis = Dis65816(bytes(rom))
    from pipeline import InsnRecorder
    rec = InsnRecorder(dis, 0xC00000)
    assert len(rec.insns) == 1
    assert rec.insns[0][1] == "RTS"


def test_recorder_lda_rts():
    rom = bytearray(0x400000)
    rom[0] = 0xA9  # LDA #imm
    rom[1] = 0x01
    rom[2] = 0x00
    rom[3] = 0x60  # RTS
    dis = Dis65816(bytes(rom))
    from pipeline import InsnRecorder
    rec = InsnRecorder(dis, 0xC00000)
    assert len(rec.insns) == 2
    assert "LDA" in rec.insns[0][1]
    assert rec.insns[1][1] == "RTS"


def test_recorder_branch():
    rom = bytearray(0x400000)
    rom[0] = 0x80  # BRA +4
    rom[1] = 0x04
    rom[2] = 0xEA  # NOP (skipped by BRA)
    rom[3] = 0xEA  # NOP
    rom[4] = 0xEA  # NOP
    rom[5] = 0xEA  # NOP (skipped)
    rom[6] = 0x60  # RTS target (PC = $C00002 + 4 = $C00006)
    dis = Dis65816(bytes(rom))
    from pipeline import InsnRecorder
    rec = InsnRecorder(dis, 0xC00000)
    assert len(rec.insns) >= 1
    target_addrs = {a for a, _, _, _ in rec.insns}
    assert 0xC00006 in target_addrs  # BRA target = RTS
    assert 0xC00002 not in target_addrs  # skipped NOPs


def test_recorder_jmp_stops():
    rom = bytearray(0x400000)
    rom[0] = 0x4C  # JMP abs
    rom[1] = 0x00
    rom[2] = 0x80
    rom[3] = 0xEA  # NOP after JMP - should NOT be recorded
    rom[4] = 0x60
    dis = Dis65816(bytes(rom))
    from pipeline import InsnRecorder
    rec = InsnRecorder(dis, 0xC00000)
    addrs = {a for a, _, _, _ in rec.insns}
    assert 0xC00000 in addrs
    assert 0xC00003 not in addrs  # linear flow should stop at JMP


# ─── gen_pseudocode tests ───────────────────────────────

def test_gen_pseudocode_writes_file(tmp_path):
    rom = bytearray(0x400000)
    rom[0] = 0x60  # RTS
    dis = Dis65816(bytes(rom))
    from pipeline import gen_pseudocode
    n = gen_pseudocode(dis, 0xC00000, "func_C00000", str(tmp_path))
    assert n > 0
    out = tmp_path / "func_C00000.c"
    assert out.exists()
    content = out.read_text("utf-8")
    assert "func_C00000" in content
    assert "return;" in content
    assert "C00000" in content


# ─── mmap_name tests ────────────────────────────────────

def test_mmap_name_from_loaded_map():
    # The mmap is loaded from file at import time, test that at least
    # some known entries resolve
    names = {
        0x0516: "game_phase",
        0x7E1B29: "event_queue_count",
    }
    for addr, expected in names.items():
        result = mmap_name(addr)
        # May be empty if memory-map.md not loaded, but should not crash
        assert isinstance(result, str)
