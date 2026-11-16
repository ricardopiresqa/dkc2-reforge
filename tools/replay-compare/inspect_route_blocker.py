"""Inspect decoded collision cells around observed route stall, read-only."""
import re
import hashlib
import struct
import sys
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import import_pirate_panic as importer

source = (ROOT / "data/original/pirate/pirate_panic_level.lua").read_text(encoding="utf-8")
match = re.search(r"grid_cols = (\d+),\s*grid_rows = (\d+),\s*grid_rle = '([^']*)'", source)
assert match is not None, "runtime collision grid unavailable"
cols, rows, encoded = int(match[1]), int(match[2]), match[3]
grid = importer.decode_rle(encoded)
profile = re.search(r"surface_cols = (\d+),\s*surface_rows = (\d+),\s*surface_rle = '([^']*)'", source)
assert profile is not None, "flat surface grid unavailable"
scols, srows, srle = int(profile[1]), int(profile[2]), profile[3]
surfaces = importer.decode_rle(srle)
objects = []
for record in re.finditer(r"\{ type = (\d+), script = (\d+), class = (\d+), x = (-?\d+), feet_y = (-?\d+), param = (\d+), sprite = '([^']+)' \}", source):
    x = int(record[4])
    if 3450 <= x <= 4050:
        objects.append({"type": int(record[1]), "script": int(record[2]), "class": int(record[3]),
                        "x": x, "feet_y": int(record[5]), "param": int(record[6]), "sprite": record[7]})
center = int(sys.argv[1]) if len(sys.argv) > 1 else 3687
feet = int(sys.argv[2]) if len(sys.argv) > 2 else 320
for y in tuple(range(max(0, feet - 96), feet + 9, 16)):
    print("player_top_y=%d" % y)
    for x in tuple(range(max(0, center - 16), center + 18, 8)):
        col, row = x // 16, y // 16
        print(" x=%d cell=(%d,%d) value=%d" % (x, col, row, grid[row * cols + col]))
print("nearby source objects:", objects)

rom_path = ROOT / "tools/vendor/DKC2-disasm/DKC2/Donkey Kong Country 2 (USA V1.0).sfc"
rom = rom_path.read_bytes()
room = (ROOT / "assets-raw/pirate/_decoded/map.bin").read_bytes()[32:32 + 7136]
defs = (ROOT / "assets-raw/pirate/_decoded/defs.bin").read_bytes()
props = (ROOT / "assets-raw/pirate/_decoded/collision_fc6154.bin").read_bytes()
center_col = center // 32
for col in (center_col - 1, center_col, center_col + 1):
    print("metatile column=%d x=%d" % (col, col * 32))
    center_row = feet // 32
    for row in range(max(0, center_row - 4), min(16, center_row + 3)):
        offset = col * 32 + row * 2
        word = int.from_bytes(room[offset:offset + 2], "little")
        metatile = word & 0x3FFF
        left, right = (struct.unpack_from("<HH", props, metatile * 4)
                       if metatile < len(props) // 4 else (0, 0))
        entry_words = struct.unpack_from("<16H", defs, metatile * 32)
        print(" row=%d mapword=%04X id=%d flags=%04X left=%04X right=%04X handler=%d,%d tiles=%s" %
              (row, word, metatile, word & 0xC000, left, right, left & 255, right & 255,
               [w & 1023 for w in entry_words]))
        for value in (left, right):
            idx = value & 255
            if idx < 80:
                pointer = int.from_bytes(rom[0x35CA38 + idx * 2:0x35CA3A + idx * 2], "little")
                code = rom[0x350000 + pointer:0x350000 + pointer + 8]
                print("  property=%d pointer=%04X code=%s" % (idx, pointer, code.hex(" ")))
print("rom_sha256=%s" % hashlib.sha256(rom).hexdigest())
