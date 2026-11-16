"""
DKC2 Reforge — Assembly → Pseudocode Pipeline

Gera pseudocodigo C-like a partir do disassembly 65816.
Usa Dis65816 para rastrear fluxo, memory-map.md para naming.
"""
import os, re, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from disasm65816 import Dis65816, OPCODES, IMM8, read_word, read_long, rom_offset

# ─── Load memory map ────────────────────────────────────────

MEMORY_MAP = {}
MMAP_PATH = Path(__file__).parent.parent.parent / "docs" / "memory-map.md"
if MMAP_PATH.exists():
    text = MMAP_PATH.read_text("utf-8")
    for m in re.finditer(r'\{[^}]*"address"[^}]*\}', text, re.DOTALL):
        try:
            entry = json.loads(m.group())
            addr = int(entry["address"], 16)
            MEMORY_MAP[addr] = entry
        except:
            pass

def mmap_name(addr):
    e = MEMORY_MAP.get(addr)
    if e: return e.get("name", "")
    bank = (addr >> 16) & 0xFF
    if bank in (0x7E, 0x7F):
        e = MEMORY_MAP.get(addr & 0xFFFF)
        if e: return e.get("name", "")
    return ""

# ─── Instruction → C translation ────────────────────────────

def op_str(mnem, opval, size):
    base = mnem.split()[0]
    mode_raw = mnem[len(base):].strip()
    addr = opval
    n = ""
    if mode_raw in ("abs", "[abs]", "abs,X", "abs,Y", "long", "long,X") and isinstance(opval, int):
        n = mmap_name(opval if opval < 0x10000 else opval)
        n = f" // {n}" if n else ""
    if mode_raw == "#imm":
        return f"#{opval:#06x}" if size >= 3 else f"#{opval:#04x}"
    if mode_raw in ("rel8", "rel16"):
        return f"${opval:06X}"
    if mode_raw in ("abs", "[abs]"):
        return f"${opval:04X}{n}"
    if mode_raw == "abs,X":
        return f"${opval:04X},X{n}"
    if mode_raw == "abs,Y":
        return f"${opval:04X},Y{n}"
    if mode_raw == "long":
        return f"${opval:06X}{n}"
    if mode_raw == "long,X":
        return f"${opval:06X},X{n}"
    if mode_raw == "long,Y":
        return f"${opval:06X},Y{n}"
    if mode_raw == "dp":
        return f"${opval:02X}{n}"
    if mode_raw == "dp,X":
        return f"${opval:02X},X{n}"
    if mode_raw == "dp,Y":
        return f"${opval:02X},Y{n}"
    if mode_raw == "(dp,X)":
        return f"(${opval:02X},X){n}"
    if mode_raw == "(dp),Y":
        return f"(${opval:02X}),Y{n}"
    if mode_raw == "(dp)":
        return f"(${opval:02X}){n}"
    if mode_raw == "[dp]":
        return f"[${opval:02X}]{n}"
    if mode_raw == "[dp],Y":
        return f"[${opval:02X}],Y{n}"
    if mode_raw in ("(dp,S)", "(dp,S),Y", "dp,S"):
        return f"${opval:02X},S"
    if "bank24" in mode_raw:
        return f"${opval>>8:02X}, ${opval&0xFF:02X}"
    return f"${opval:04X}"

def pseudo_one(addr, mnem, opval, size, label_name):
    """Convert one 65816 instruction to C-like pseudocode."""
    base = mnem.split()[0]

    if base == "BRA": return f"goto ${opval:06X};"
    if base == "BRL": return f"goto ${opval:06X}; // far"

    cond_map = {"BEQ":"Z","BNE":"!Z","BPL":"!N","BMI":"N",
                "BCC":"!C","BCS":"C","BVC":"!V","BVS":"V"}
    if base in cond_map:
        return f"if ({cond_map[base]}) goto ${opval:06X};"

    if base == "JSR":  return f"CALL(${opval:06X});"
    if base == "JSL":  return f"CALL_FAR(${opval:06X});"
    if base == "JMP":
        mode = mnem[len("JMP"):].strip()
        if mode == "[abs]": return f"JUMP_INDIRECT(${opval:04X});"
        return f"goto ${opval:06X};"
    if base == "JML": return f"JUMP_FAR(${opval:06X});"
    if base == "RTS": return "return;"
    if base == "RTL": return "return_far();"
    if base == "RTI": return "return_irq();"
    if base == "BRK": return "BRK();"
    if base == "WAI": return "wait_nmi();"

    size_annot = "A16" if size == 3 and mnem.endswith("#imm") else ""
    if base == "LDA":
        o = op_str(mnem, opval, size)
        return f"A = {o};{size_annot}"
    if base == "LDX":
        o = op_str(mnem, opval, size)
        return f"X = {o};"
    if base == "LDY":
        o = op_str(mnem, opval, size)
        return f"Y = {o};"
    if base == "STA":
        return f"{op_str(mnem, opval, size)} = A;"
    if base == "STX":
        return f"{op_str(mnem, opval, size)} = X;"
    if base == "STY":
        return f"{op_str(mnem, opval, size)} = Y;"
    if base == "STZ":
        return f"{op_str(mnem, opval, size)} = 0;"

    writes = {"ADC":"+=","SBC":"-=","AND":"&=","ORA":"|=","EOR":"^="}
    if base in writes and mnem.endswith("#imm"):
        o = op_str(mnem, opval, size)
        return f"A {writes[base]} {o};"
    if base in writes:
        o = op_str(mnem, opval, size)
        return f"A {writes[base]} {o}; // {mnem}"

    if base == "CMP":
        o = op_str(mnem, opval, size)
        return f"Z, N, C = A - {o};"
    if base == "CPX":
        o = op_str(mnem, opval, size)
        return f"Z, N, C = X - {o};"
    if base == "CPY":
        o = op_str(mnem, opval, size)
        return f"Z, N, C = Y - {o};"
    if base == "BIT":
        o = op_str(mnem, opval, size)
        return f"Z = (A & {o}) == 0;"

    if base in ("INC","DEC","ASL","LSR","ROL","ROR"):
        if mnem == f"{base} A": return {"INC":"A++;","DEC":"A--;","ASL":"A <<= 1;","LSR":"A >>= 1;","ROL":"A = ROL(A);","ROR":"A = ROR(A);"}[base]
        o = op_str(mnem, opval, size)
        name = {"INC":"++","DEC":"--","ASL":"<<=1","LSR":">>=1","ROL":"=ROL(","ROR":"=ROR("}[base]
        return f"{o}{name};"

    simple = {"INX":"X++;","INY":"Y++;","DEX":"X--;","DEY":"Y--;",
              "TAX":"X = A;","TXA":"A = X;","TAY":"Y = A;","TYA":"A = Y;",
              "TSX":"X = SP;","TXS":"SP = X;",
              "PHA":"push(A);","PLA":"A = pop();",
              "PHX":"push(X);","PLX":"X = pop();",
              "PHY":"push(Y);","PLY":"Y = pop();",
              "PHB":"push(DB);","PLB":"DB = pop();",
              "PHD":"push(DP);","PLD":"DP = pop();",
              "PHP":"push(P);","PLP":"P = pop();",
              "CLC":"C = 0;","SEC":"C = 1;",
              "CLI":"I = 0;","SEI":"I = 1;",
              "CLD":"D = 0;","SED":"D = 1;","CLV":"V = 0;",
              "XBA":"SWAP_AB(A);","XCE":"E ^= 1;",
              "TCD":"DP = A;","TDC":"A = DP;",
              "TCS":"SP = A;","TSC":"A = SP;",
              "NOP":"; // nop","STP":"stop_cpu();",
              "WDM":"; // wdm"}
    if base in simple:
        return simple[base]
    if base == "REP": return f"A16={bool(opval&0x20)} XY16={bool(opval&0x10)};"
    if base == "SEP": return f"A8={bool(opval&0x20)} XY8={bool(opval&0x10)};"
    if base == "TSB": return f"TEST_SET({op_str(mnem, opval, size)});"
    if base == "TRB": return f"TEST_RESET({op_str(mnem, opval, size)});"
    if base in ("MVN","MVP"):
        dir = "fwd" if base == "MVN" else "bwd"
        return f"block_copy_{dir}({op_str(mnem, opval, size)});"

    return f"; // {mnem} {op_str(mnem, opval, size)}"


# ─── Instruction recorder (traces via Dis65816) ─────────────

class InsnRecorder:
    """Records instruction trace for pseudocode generation."""
    def __init__(self, dis, func_addr):
        self.dis = dis
        self.func_addr = func_addr
        self.insns = []
        self._seen = set()
        self._insn_seen = set()
        self._m = 0  # local REP/SEP tracking, default 16-bit (game operational mode)
        self._x = 1
        self._follow(func_addr)

    def _follow(self, start_addr, depth=0):
        if depth > 15 or start_addr in self._seen:
            return
        self._seen.add(start_addr)
        addr = start_addr
        while True:
            if addr in self._insn_seen:
                break
            self._insn_seen.add(addr)
            op = self.dis.read_byte(addr)
            # Local REP/SEP tracking
            if op == 0xC2:
                imm = self.dis.read_byte(addr+1)
                if imm & 0x20: self._m = 0
                if imm & 0x10: self._x = 0
            elif op == 0xE2:
                imm = self.dis.read_byte(addr+1)
                if imm & 0x20: self._m = 1
                if imm & 0x10: self._x = 1
            info = OPCODES.get(op)
            if info is None:
                self.insns.append((addr, f"?? ${op:02X}", 0, 1))
                break
            mnem, base_size = info
            size = base_size + (1 if op in IMM8 and self._m == 0 else 0)
            opval = 0
            off2 = rom_offset(None, addr + 1)
            if size == 3:
                opval = read_word(self.dis.data, off2)
            elif size == 4:
                opval = self.dis.read_byte(addr+1) | (self.dis.read_byte(addr+2)<<8) | (self.dis.read_byte(addr+3)<<16)
            elif size == 2:
                opval = self.dis.read_byte(addr+1)
            self.insns.append((addr, mnem, opval, size))

            # Follow branches
            if op in (0x10,0x30,0x50,0x70,0x90,0xB0,0xD0,0xF0,0x80,0x82):
                off = self.dis.read_byte(addr+1)
                if size == 2:  # rel8
                    target = addr + 2 + (off if off < 128 else off - 256)
                elif size == 3:  # BRL rel16
                    target = addr + 3 + (off | (self.dis.read_byte(addr+2)<<8))
                    if target >= 0x1000000: target -= 0x1000000
                else:
                    break
                if op in (0x80, 0x82):
                    addr = target  # unconditional, follow only path
                    continue
                self._follow(target, depth+1)

            # JMP/JML — unconditional, stop linear flow
            # 0x6C/0x7C = JMP indirect — can't statically resolve, treat as stop
            if op in (0x4C, 0x5C, 0x6C, 0x7C):
                break

            # JSR/JSL - don't inline
            if op in (0x20, 0x22):
                pass  # just record the call instruction, continue linearly

            if op in (0x60, 0x6B, 0x40, 0xDB):
                break
            addr += size

# ─── Pseudocode generation ─────────────────────────────────

def gen_pseudocode(dis, func_addr, func_name, out_dir):
    recorder = InsnRecorder(dis, func_addr)

    lines = []
    lines.append(f"// Function: {func_name} @ ${func_addr:06X}")
    lines.append(f"void {func_name}(void) {{")
    lines.append("")

    for addr, mnem, opval, size in recorder.insns:
        pseudo = pseudo_one(addr, mnem, opval, size, func_name)
        comment = f"  // ${addr:06X}"
        lines.append(f"  {pseudo}{comment}")

    lines.append("}")
    out_path = Path(out_dir) / f"{func_name}.c"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), "utf-8")
    return len(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--func", help="C0:XXXX")
    parser.add_argument("--output", default="docs/pseudocode")
    args = parser.parse_args()

    data = open("roms/dkc2.sfc", "rb").read()
    dis = Dis65816(data)

    # DKC2 uses SA-1 HiROM; vectors at ROM end (0x3FFFE0+)
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

    print(f"ROM loaded. Functions: {len(dis.functions)}, MMAP: {len(MEMORY_MAP)}")

    if args.func:
        addr = int(args.func.replace(":",""), 16)
        name = dis.functions.get(addr, f"func_{addr:06X}")
        n = gen_pseudocode(dis, addr, name, args.output)
        print(f"  {name} ({n} lines)")
    elif args.all:
        c0_funcs = [(a, n) for a, n in sorted(dis.functions.items()) if (a>>16)&0xFF == 0xC0]
        for i, (addr, name) in enumerate(c0_funcs, 1):
            try:
                n = gen_pseudocode(dis, addr, name, args.output)
                print(f"  [{i:3d}/{len(c0_funcs):3d}] {name} ({n} lines)")
            except Exception as e:
                print(f"  [{i:3d}/{len(c0_funcs):3d}] {name}: ERR {e}")
        print(f"Done: {len(c0_funcs)} functions to {args.output}/")
    else:
        print("Use --all or --func C0:XXXX")
        c0 = [(a, n) for a, n in sorted(dis.functions.items()) if (a>>16)&0xFF == 0xC0]
        for a, n in c0:
            print(f"  {n:30s} @ ${a:06X}")


if __name__ == "__main__":
    main()
