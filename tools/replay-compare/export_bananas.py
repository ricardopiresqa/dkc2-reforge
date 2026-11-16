"""Decode Pirate Panic banana formations exactly as B5F10B does, and check them in WRAM.

Group entry (4 bytes, LevelData/BananaFormations/PiratePanic_Main.bin): b0 & $0F
selects the group's type bit (DATA_B5F369); X = (word(b0,b1) >> 1 & $3FF8) + $100 and
Y = (word(b1,b2) >> 4 & $03F8) + $100 for theme $0AB4 = 0 (DATA_B5F389 row 0,
CODE_B5F3C0 = four LSR); b3 indexes the formation table DATA_FDCA82. A formation is
a column count, a marker byte and a bit stream; each column yields a 16-bit mask
whose bit 15 is the top 8 px row. Each set bit is one 16x16 banana sprite (tile base
$0D2C = $21E0) at (X + 8*column, Y + 8*row) in source coordinates.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISASM = ROOT / "tools/vendor/DKC2-disasm/DKC2"
STAGE = ROOT / "assets-raw/pirate"


def asm():
    return (DISASM / "Routine_Macros_DKC2.asm").read_text(encoding="utf-8", errors="replace")


def formation_bytes(source):
    """Return {formation index: bytes} from DATA_FDCA82 (offset table) and its db records."""
    start = source.index("DATA_FDCA82:\n")
    table, records = [], {}
    for line in source[start:].splitlines()[1:]:
        match = re.match(r"\s*dw (DATA_[0-9A-F]+)-DATA_FDCA82", line)
        if not match:
            break
        table.append(match.group(1))
    for label in set(table):
        block = source.split(label + ":\n", 1)[1]
        data = []
        for line in block.splitlines():
            if not line.strip().startswith("db"):
                break
            data += [int(value, 16) for value in re.findall(r"\$([0-9A-F]{2})", line)]
        records[label] = bytes(data)
    return [records[label] for label in table]


def decode_formation(record):
    """Bit-exact model of CODE_B5F1E5..B5F22C: one 16-bit column mask per column."""
    if not record:  # e.g. the table's %FREE_BYTES end sentinel
        raise ValueError("empty formation record")
    count = record[0]
    if count == 0:
        return []
    marker_index = (record[1] << 1) & 0x7E
    marker = 1 << (marker_index // 2 - 1)  # DATA_B5F369 - 2 indexed by (byte*2 & $7F)
    word = lambda y: record[y] | (record[y + 1] << 8 if y + 1 < len(record) else 0)
    y, a, carry, masks = 2, 0, 0, []
    out = marker

    if not 1 <= record[1] & 0x3F <= 16:
        raise ValueError("formation marker out of range: %r" % record[:2])

    def load():
        nonlocal y, a, carry
        if y >= len(record) + 2:  # malformed record: never spin past its end
            raise ValueError("formation bit stream exhausted at byte %d" % y)
        a, y, carry = word(y), y + 2, 1   # LDA [$42],Y ; INY ; INY ; SEC

    load()
    while True:
        # B5F204: ROR A ; BEQ reload ; ROR $4A ; BCC loop
        new_carry = a & 1
        a = (a >> 1) | (carry << 15)
        carry = new_carry
        if a == 0:
            load()
            continue
        new_carry = out & 1
        out = (out >> 1) | (carry << 15)
        carry = new_carry
        if not carry:
            continue
        masks.append(out)                   # STA $7F0000,X
        out = marker
        count -= 1
        carry = 0                           # CLC
        if count == 0:
            return masks


def groups(source, area="Main"):
    data = (DISASM / ("LevelData/BananaFormations/PiratePanic_%s.bin" % area)).read_bytes()
    formations = formation_bytes(source)
    result = []
    for offset in range(0, len(data) - 3, 4):
        b0, b1, b2, b3 = data[offset:offset + 4]
        result.append({"type_bit": 1 << (b0 & 0x0F),
                       "x": (((b0 | b1 << 8) >> 1) & 0x3FF8) + 0x100,
                       "y": (((b1 | b2 << 8) >> 4) & 0x03F8) + 0x100,
                       "formation": b3, "masks": decode_formation(formations[b3])})
    return result


def bananas(level_groups):
    out = []
    for group in level_groups:
        for column, mask in enumerate(group["masks"]):
            for row in range(16):
                if mask & (0x8000 >> row):
                    out.append({"x": group["x"] + 8 * column, "y": group["y"] + 8 * row,
                                "type_bit": group["type_bit"]})
    return out


def check_wram(level_groups):
    """Compare decoded masks with the game's own list at $7F0000 (end-of-trace snapshot)."""
    wram = (STAGE / "reference-wram.bin").read_bytes()
    bank7f = wram[0x10000:]
    decoded = [mask for group in level_groups for mask in group["masks"]]
    actual = [bank7f[i] | bank7f[i + 1] << 8 for i in range(0xB232, 0xB232 + 2 * len(decoded), 2)]
    differing = [(i, hex(d), hex(a)) for i, (d, a) in enumerate(zip(decoded, actual)) if d != a]
    # Collected bananas clear bits in place; any other difference is a decoding error.
    cleared_only = all((a & ~int(d, 16)) == 0 for _, d, a in [(i, d, int(a, 16)) for i, d, a in differing])
    return {"columns": len(decoded), "differing_columns": differing, "differences_are_cleared_bits": cleared_only}


def spin_frames(frame=40):
    """The 8 spin frames (tiles $1E0 + 2n, 16x16, OBJ palette 0) from captured VRAM/CGRAM."""
    import importlib.util

    from PIL import Image

    spec = importlib.util.spec_from_file_location("bg", ROOT / "tools/replay-compare/export_original_backgrounds.py")
    assert spec is not None and spec.loader is not None
    background = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(background)
    vram = (STAGE / ("reference-frame-%04d-vram.bin" % frame)).read_bytes()
    cgram = (STAGE / ("reference-frame-%04d-cgram.bin" % frame)).read_bytes()
    meta = dict(line.split("=", 1) for line in (STAGE / ("reference-frame-%04d-ppu.txt" % frame)).read_text().splitlines())
    base, second = int(meta["ppu.oamBaseAddress"]) * 2, int(meta["ppu.oamAddressOffset"]) * 2
    images = []
    for index in range(8):
        tile = 0x1E0 + 2 * index  # $0D2C low 9 bits; & $EE keeps tiles inside $1E0-$1EF
        image = Image.new("RGBA", (16, 16))
        canvas = image.load()  # PixelAccess writes (faster than putpixel)
        for dx, dy, part in ((0, 0, tile), (8, 0, tile + 1), (0, 8, tile + 16), (8, 8, tile + 17)):
            address = base + (part & 0xFF) * 32 + (second if part & 0x100 else 0)
            pixels = background.tile_pixels(vram, address, 4)
            for y in range(8):
                for x in range(8):
                    value = pixels[y][x]
                    if value:  # OBJ palette 0 = CGRAM 128-143
                        color = int.from_bytes(cgram[(128 + value) * 2:][:2], "little")
                        canvas[dx + x, dy + y] = tuple((color >> s & 31) * 255 // 31 for s in (0, 5, 10)) + (255,)
        images.append(image)
    return images


def export():
    source = asm()
    level = groups(source)
    wram = check_wram(level)
    assert wram["differences_are_cleared_bits"], wram
    lines = ["-- Generated by tools/replay-compare/export_bananas.py from BananaFormations/",
             "-- PiratePanic_Main.bin (B5F10B decode). Source coordinates; top-left of 16x16.",
             "return {"]
    column = 0
    for group_index, group in enumerate(level):
        for col, mask in enumerate(group["masks"]):
            for row in range(16):
                if mask & (0x8000 >> row):
                    lines.append("  { x = %d, y = %d, gx = %d, gy = %d, col = %d, row = %d, group = %d, type_bit = %d },"
                                 % (group["x"] + 8 * col, group["y"] + 8 * row, group["x"], group["y"],
                                    col, row, group_index + 1, group["type_bit"]))
            column += 1
    lines.append("}")
    out = ROOT / "data/original/pirate/bananas.lua"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    frames_dir = ROOT / "assets/images/pirate/banana"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for index, image in enumerate(spin_frames()):
        image.save(frames_dir / ("original_banana_%d.png" % index))
    report = {"groups": len(level), "bananas": len(bananas(level)), "wram": wram}
    (STAGE / "bananas-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


# Subarea formations (same decode, B5F10B runs on every area load): the warp room's
# banana "!" and the first bonus. Written as data/original/pirate/bananas_<name>.lua.
SUBAREAS = {"warp": "Warp", "bonus_1": "Bonus1"}


def export_subareas():
    source = asm()
    counts = {}
    for name, area in SUBAREAS.items():
        lines = ["-- Generated by tools/replay-compare/export_bananas.py from BananaFormations/",
                 "-- PiratePanic_%s.bin (B5F10B decode). Source coordinates; top-left of 16x16." % area,
                 "return {"]
        level = groups(source, area)
        for group_index, group in enumerate(level):
            for col, mask in enumerate(group["masks"]):
                for row in range(16):
                    if mask & (0x8000 >> row):
                        lines.append("  { x = %d, y = %d, gx = %d, gy = %d, col = %d, row = %d, group = %d, type_bit = %d },"
                                     % (group["x"] + 8 * col, group["y"] + 8 * row, group["x"], group["y"],
                                        col, row, group_index + 1, group["type_bit"]))
        lines.append("}")
        (ROOT / ("data/original/pirate/bananas_%s.lua" % name)).write_text("\n".join(lines) + "\n", encoding="utf-8")
        counts[name] = len(bananas(level))
    return counts


if __name__ == "__main__":
    if sys.argv[1:] == ["--subareas"]:
        print(json.dumps(export_subareas()))
        sys.exit(0)
    result = export()
    print(json.dumps({key: result[key] for key in ("groups", "bananas")}))
    sys.exit(0)
