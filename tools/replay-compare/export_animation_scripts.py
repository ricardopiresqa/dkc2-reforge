"""Export original F9 animation bytecode and BC8000 pose resources.

No replay frame sequence is used for production. Scripts come from the ROM;
observed pose traces are reserved for verification.
"""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools/vendor/DKC2-disasm/DKC2"
STAGE = ROOT / "assets-raw/pirate"
sys.path.insert(0, str(ROOT / "tools"))
import import_pirate_panic as parser

FIXED = {0x80: 1, 0x81: 3, 0x82: 3, 0x83: 3, 0x84: 3, 0x8E: 3}
GROUPS = (("IdleSway", "idle"), ("Walk", "walk"), ("Run", "run"), ("Jump", "jump"), ("Fall", "fall"), ("Land", "land"), ("Juggling", "juggle"))


def script(rom, animation):
    offset = animation * 4 + 0x390000
    start = int.from_bytes(rom[offset:offset + 2], "little")
    flags = int.from_bytes(rom[offset + 2:offset + 4], "little")
    pc = start
    instructions = {}
    for _ in range(1024):
        op = rom[0x390000 + pc]
        size = 3 if op < 128 else FIXED.get(op)
        if size is None:
            return {"start": start, "flags": flags, "code": instructions,
                    "status": "partial", "unsupported_opcode": op}
        argument = int.from_bytes(rom[0x390000 + pc + 1:0x390000 + pc + 3], "little") if size == 3 else 0
        instructions[pc] = {"op": op, "arg": argument, "next": pc + size}
        pc += size
        if op in (0x80, 0x82):
            return {"start": start, "flags": flags, "code": instructions, "status": "exported"}
    raise ValueError("animation instruction budget exceeded")


def pose_resources(rom):
    text = (SOURCE / "Routine_Macros_DKC2.asm").read_text(encoding="utf-8", errors="replace")
    pattern = r'^DATA_([0-9A-F]{6}):\n(?:\tdb [^\n]*\n)+\tincbin "Graphics/DynamicSprites/([^\"]+)"'
    by_address = {int(m.group(1), 16): m.group(2) for m in re.finditer(pattern, text, re.M)}
    poses = {}
    folder = ROOT / "assets/images/pirate/poses"
    folder.mkdir(parents=True, exist_ok=True)
    for index in range(0, 0x4000, 4):
        addr = int.from_bytes(rom[0x3C8000 + index:0x3C8000 + index + 3], "little")
        name = by_address.get(addr, "")
        for prefix, group in GROUPS:
            match = re.fullmatch("GFX_Diddy_" + prefix + r"(\d+)\.bin", name)
            if match:
                src = ROOT / ("assets/images/pirate/diddy/diddy_%s_%02d.png" % (group, int(match[1])))
                assert src.is_file(), "import original Diddy poses before scripts: " + name
                target = folder / ("diddy_pose_%04x_01.png" % index)
                shutil.copy2(src, target)
                poses[index] = {"animation": "diddy_pose_%04x" % index, "gfx": name}
                break
    return poses


def export():
    rom = (SOURCE / "Donkey Kong Country 2 (USA V1.0).sfc").read_bytes()
    scripts = {index: script(rom, index) for index in (1, 3, 4, 5, 6, 7, 8)}
    poses = pose_resources(rom)
    lines = ["-- Original ROM bytecode; not replay animation.", "return { scripts = {"]
    for index, data in scripts.items():
        lines.append("[%d] = { start = %d, flags = %d, code = {" % (index, data["start"], data["flags"]))
        for pc, op in data["code"].items():
            lines.append("[%d] = { op = %d, arg = %d, next = %d }," % (pc, op["op"], op["arg"], op["next"]))
        lines.append("} },")
    lines.append("}, poses = {")
    for index, data in poses.items():
        lines.append('[%d] = { animation = "%s", gfx = "%s" },' % (index, data["animation"], data["gfx"]))
    lines.append("} }")
    contents = "\n".join(lines)
    (STAGE / "animation_scripts.lua").write_text(contents, encoding="utf-8")
    runtime_dir = ROOT / "data/original/pirate"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "animation_scripts.lua").write_text(contents, encoding="utf-8")
    report = {"rom_sha256": hashlib.sha256(rom).hexdigest(), "scripts": scripts, "poses": poses,
              "status": "exported; callbacks/VM need runtime verification"}
    (STAGE / "animation-script-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    parser.write_atlas(str(ROOT), str(ROOT / "assets/images"))
    print("exported %d original scripts and %d pose resources; no replay as production logic" % (len(scripts), len(poses)))


if __name__ == "__main__":
    export()
