"""Exercise each original collision handler used in the room at all 16 offsets."""
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import import_pirate_panic as parser

stage = ROOT / "assets-raw/pirate"
raw_map = (stage / "_decoded/map.bin").read_bytes()
room = raw_map[32:32 + 7136]
rom = (ROOT / "tools/vendor/DKC2-disasm/DKC2/Donkey Kong Country 2 (USA V1.0).sfc").read_bytes()
props = (stage / "_decoded/collision_fc6154.bin").read_bytes()
handler_ids = set()
for offset in range(0, len(room), 2):
    metatile = int.from_bytes(room[offset:offset + 2], "little") & 0x3FFF
    if metatile >= len(props) // 4:
        continue
    left, right = struct.unpack_from("<HH", props, metatile * 4)
    handler_ids.update((left & 255, right & 255))

report = []
for handler in sorted(handler_ids):
    results = [parser.execute_collision_handler(handler, x, rom) for x in range(16)]
    report.append({"handler": handler, "results": results,
                   "unsupported_offsets": [x for x, result in enumerate(results) if result == -2],
                   "no_floor_offsets": [x for x, result in enumerate(results) if result == -1]})
out = {"status": "REVIEW", "unique_handlers": len(report), "handlers": report,
       "rule": "Never silently map unsupported native handler to solid grid filler."}
(stage / "collision-handler-coverage.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
