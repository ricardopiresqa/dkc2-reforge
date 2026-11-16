"""List only collision handlers referenced by the verified Pirate Panic room."""
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "assets-raw/pirate"
SOURCE = ROOT / "tools/vendor/DKC2-disasm/DKC2"
MAP_ROOM = (STAGE / "_decoded/map.bin").read_bytes()[32:32 + 7136]
PROPS = (STAGE / "_decoded/collision_fc6154.bin").read_bytes()
ROM = (SOURCE / "Donkey Kong Country 2 (USA V1.0).sfc").read_bytes()
DEFS = (STAGE / "_decoded/defs.bin").read_bytes()
used_ids = sorted({word & 0x3FFF for offset in range(0, len(MAP_ROOM), 2)
                   for word in (int.from_bytes(MAP_ROOM[offset:offset + 2], "little"),)})
handlers = set()
for tile_id in used_ids:
    if tile_id >= len(PROPS) // 4:
        continue
    left, right = struct.unpack_from("<HH", PROPS, tile_id * 4)
    handlers.update((left & 255, right & 255))
result = []
for index in sorted(handlers - {0}):
    if index >= 80:
        result.append({"id": index, "status": "outside 80-function source table"})
        continue
    address = int.from_bytes(ROM[0x35CA38 + index * 2:0x35CA3A + index * 2], "little")
    code = ROM[0x350000 + address:0x350000 + address + 16]
    result.append({"id": index, "pointer": "%04X" % address, "bytes": code.hex(" ")})
path = STAGE / "used-collision-handlers.json"
path.write_text(json.dumps({"metatiles": used_ids, "handlers": result}, indent=2), encoding="utf-8")
print(json.dumps({"unique_metatiles": len(used_ids), "handler_count": len(result),
                  "handlers": result}, indent=2))
