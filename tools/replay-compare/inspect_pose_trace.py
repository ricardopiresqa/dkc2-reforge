"""Resolve observed sprite pose indices using the original BC8000 table."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools/vendor/DKC2-disasm/DKC2"
STAGE = ROOT / "assets-raw/pirate"


def inspect():
    rom = (SOURCE / "Donkey Kong Country 2 (USA V1.0).sfc").read_bytes()
    text = (SOURCE / "Routine_Macros_DKC2.asm").read_text(encoding="utf-8", errors="replace")
    blocks = re.finditer(r'^DATA_([0-9A-F]{6}):\n(?:\tdb [^\n]*\n)+\tincbin "Graphics/DynamicSprites/([^\"]+)"', text, re.M)
    addresses = {int(match.group(1), 16): match.group(2) for match in blocks}
    rows = list(csv.DictReader((STAGE / "reference-poses.csv").open(encoding="utf-8")))
    report = []
    for frame in (0, 1, 39, 40, 41, 60, 100, 140, 151, 153, 158, 165, 173, 180):
        row = rows[frame]
        index = int(row["pose_table_offset"])
        offset = 0x3C8000 + index
        address = int.from_bytes(rom[offset:offset + 3], "little")
        report.append({**row, "pose_data_address": hex(address), "gfx": addresses.get(address),
                       "status": "mapped" if address in addresses else "unresolved"})
    (STAGE / "pose-lookup-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    inspect()
