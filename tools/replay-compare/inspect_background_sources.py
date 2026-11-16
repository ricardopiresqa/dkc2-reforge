"""Decode original ShipDeck background sources; report facts before integration."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import import_pirate_panic as parser


def main():
    source = ROOT / "tools/vendor/DKC2-disasm/DKC2"
    stage = ROOT / "assets-raw/pirate/backgrounds"
    stage.mkdir(parents=True, exist_ok=True)
    inputs = {
        "bg2_map": ("Tilemaps/Compressed/Layer2_Level_ShipDeck.bin", True),
        "bg2_gfx": ("Graphics/Compressed/GFX_Layer2_Level_ShipDeck.bin", True),
        "bg3_map": ("Tilemaps/Layer3_ShipDeck.bin", False),
        "bg3_gfx": ("Graphics/GFX_Layer3_ShipDeck.bin", False),
    }
    report = {}
    vram = (ROOT / "assets-raw/pirate/reference-vram.bin").read_bytes()
    for name, (relative, compressed) in inputs.items():
        raw = (source / relative).read_bytes()
        data = parser.cmp_decompress(raw) if compressed else raw
        (stage / (name + ".bin")).write_bytes(data)
        report[name] = {"source": relative, "source_sha256": hashlib.sha256(raw).hexdigest(),
                        "decoded_bytes": len(data), "decoded_sha256": hashlib.sha256(data).hexdigest(),
                        "first_128_bytes_match_vram_offset": vram.find(data[:128]),
                        "full_bytes_match_vram_offset": vram.find(data),
                        "status": "decoded; dimensions/scroll require hardware metadata"}
    (stage / "source-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
