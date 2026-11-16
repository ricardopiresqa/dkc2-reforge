"""Inspect generated source collision profile at a bounded original coordinate."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import import_pirate_panic as parser
text = (ROOT / "data/original/pirate/pirate_panic_level.lua").read_text(encoding="utf-8")
match_cols = re.search(r"surface_cols = (\d+)", text)
match_rows = re.search(r"surface_rows = (\d+)", text)
match_rle = re.search(r"surface_rle = '([^']*)'", text)
assert match_cols and match_rows and match_rle
cols = int(match_cols[1])
rows = int(match_rows[1])
rle = match_rle[1]
values = parser.decode_rle(rle)
row = int(sys.argv[1]) if len(sys.argv) > 1 else 6
center = int(sys.argv[2]) if len(sys.argv) > 2 else 3504
vendor = ROOT / "tools/vendor/DKC2-disasm/DKC2"
rom_path = vendor / "Donkey Kong Country 2 (USA V1.0).sfc"
rom = rom_path.read_bytes()
raw_map = parser.cmp_decompress((vendor / "LevelData/ShipDeckLevels.bin").read_bytes())
room_meta = parser.verified_room_capture(raw_map, rom)
assert room_meta is not None
runtime_map = raw_map[room_meta["source_offset"]:room_meta["source_offset"] + room_meta["bytes"]]
props = parser.collision_property_map(rom)
for x in range(center - 16, center + 17):
    metatile_col, local = divmod(x, 32)
    mapword = int.from_bytes(runtime_map[metatile_col * 32 + row * 2:metatile_col * 32 + row * 2 + 2], "little")
    metatile = mapword & 0x3FFF
    pair = ((props[metatile]["left"], props[metatile]["right"])
            if metatile < len(props) else (0, 0))
    subcolumn = 1 if local >= 16 else 0
    prop = pair[subcolumn]
    local_x = local & 15
    if prop & 0x8000: local_x ^= 15
    if mapword & 0x4000: prop ^= 0x8000
    raw_handler = parser.execute_collision_handler(prop & 255, local_x, rom)
    print("x=%d yrow=%d height=%d map=%04X prop=%04X lx=%d handler=%d" %
          (x, row, values[row * cols + x], mapword, prop, local_x, raw_handler))
print("columns=%d rows=%d total=%d" % (cols, rows, len(values)))
