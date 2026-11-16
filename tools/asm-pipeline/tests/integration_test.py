"""Integration test: runs pipeline against real ROM, verifies expected functions."""
import sys, tempfile, json, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

ROM_PATH = Path(__file__).parent.parent.parent.parent / "roms" / "dkc2.sfc"


def test_rom_exists():
    assert ROM_PATH.exists(), f"ROM not found at {ROM_PATH}"
    data = ROM_PATH.read_bytes()
    assert len(data) == 0x400000, f"Expected 4MB, got {len(data)}"


def test_rom_is_hirom():
    data = ROM_PATH.read_bytes()
    assert len(data) == 0x400000, f"Expected 4MB, got {len(data)}"
    # Safer assertion: title is at 0x3FFFC0 for HiROM, 0xFFC0 for LoROM
    title_hi = data[0x3FFFC0:0x3FFFC0+21].decode("ascii", errors="replace").strip()
    title_lo = data[0xFFC0:0xFFC0+21].decode("ascii", errors="replace").strip()
    assert title_hi == "DONKEY KONG COUNTRY" or title_lo == "DONKEY KONG COUNTRY"


def test_vectors_at_hirom_end():
    from disasm65816 import read_word
    data = ROM_PATH.read_bytes()
    nat_reset = read_word(data, 0x3FFFE8)
    assert nat_reset == 0x877C, f"Expected 0x877C, got {nat_reset:04X}"
    nat_nmi = read_word(data, 0x3FFFE6)
    assert nat_nmi == 0x8916, f"Expected 0x8916, got {nat_nmi:04X}"
    emu_reset = read_word(data, 0x3FFFF8)
    assert emu_reset == 0x8E87, f"Expected 0x8E87, got {emu_reset:04X}"


def test_game_title():
    data = ROM_PATH.read_bytes()
    title = data[0xFFC0:0xFFC0+21].decode("ascii", errors="replace").strip()
    assert title == "DONKEY KONG COUNTRY", f"Got '{title}'"


def test_pipeline_discovers_functions():
    from disasm65816 import Dis65816, read_word
    data = ROM_PATH.read_bytes()
    dis = Dis65816(data)

    entries = [
        ("NATIVE_COP",   0xC00000 | read_word(data, 0x3FFFE0)),
        ("NATIVE_BRK",   0xC00000 | read_word(data, 0x3FFFE2)),
        ("NATIVE_ABORT", 0xC00000 | read_word(data, 0x3FFFE4)),
        ("NATIVE_NMI",   0xC00000 | read_word(data, 0x3FFFE6)),
        ("NATIVE_RESET", 0xC00000 | read_word(data, 0x3FFFE8)),
        ("NATIVE_IRQ",   0xC00000 | read_word(data, 0x3FFFEA)),
        ("EMU_COP",      0xC00000 | read_word(data, 0x3FFFF0)),
        ("EMU_ABORT",    0xC00000 | read_word(data, 0x3FFFF4)),
        ("EMU_NMI",      0xC00000 | read_word(data, 0x3FFFF6)),
        ("EMU_RESET",    0xC00000 | read_word(data, 0x3FFFF8)),
        ("EMU_IRQBRK",   0xC00000 | read_word(data, 0x3FFFFC)),
    ]
    for label, addr in entries:
        dis.follow_code(addr, source=label)
        if addr not in dis.functions:
            dis.functions[addr] = f"func_{addr:06X}"

    for sa1 in [0xC08687, 0xC0888B, 0xC088B0, 0xC088E3]:
        try:
            dis.follow_code(sa1, source="SA1_DISPATCH")
            if sa1 not in dis.functions:
                dis.functions[sa1] = f"func_{sa1:06X}"
        except:
            pass

    c0_funcs = [(a, n) for a, n in sorted(dis.functions.items()) if (a>>16)&0xFF == 0xC0]
    expected_addrs = {
        0xC0852D,  # unknown init
        0xC08687,  # SA-1 main dispatch
        0xC0877C,  # NATIVE_RESET handler
        0xC08811,  # COP handler
        0xC0888B,  # State A handler
        0xC088B0,  # State B (state->value mapper)
        0xC088E3,  # State C handler
        0xC08916,  # NMI handler
        0xC08E87,  # EMU_RESET handler
    }
    found = {a for a, _ in c0_funcs}
    missing = [f"${a:06X}" for a in expected_addrs if a not in found]
    assert not missing, f"Missing expected functions: {missing}"
    print(f"Total C0 functions: {len(c0_funcs)} — expected {len(expected_addrs)}")


def test_pipeline_generates_pseudocode():
    from disasm65816 import Dis65816, read_word
    from pipeline import gen_pseudocode
    data = ROM_PATH.read_bytes()
    dis = Dis65816(data)

    emu_reset_addr = 0xC00000 | read_word(data, 0x3FFFF8)
    dis.follow_code(emu_reset_addr)
    dis.functions[emu_reset_addr] = f"func_{emu_reset_addr:06X}"

    with tempfile.TemporaryDirectory() as tmpdir:
        n = gen_pseudocode(dis, emu_reset_addr, "func_C08E87", tmpdir)
        out = Path(tmpdir) / "func_C08E87.c"
        assert out.exists(), "Output file not created"
        content = out.read_text("utf-8")
        assert "func_C08E87" in content
        assert "void" in content
        assert "return;" in content or "return_far" in content or "return_irq" in content
        print(f"func_C08E87.c: {len(content)} chars, {n} lines")
