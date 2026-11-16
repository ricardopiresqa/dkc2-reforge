"""Match original palette resource to a captured exact-frame CGRAM bank."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "assets-raw/pirate"


def words(raw):
    return [int.from_bytes(raw[i:i + 2], "little") & 0x7FFF for i in range(0, len(raw) - 1, 2)]


def find(source, cgram):
    palette = words(source)
    colors = words(cgram)
    matches = []
    for start in range(0, len(colors) - len(palette) + 1):
        count = sum(a == b for a, b in zip(palette, colors[start:start + len(palette)]))
        matches.append((count, start))
    matches.sort(reverse=True)
    return {"source_words": len(palette),
            "top_cgram_matches": [{"matching_words": count, "start_index": start,
                                   "exact": count == len(palette)} for count, start in matches[:3]]}


def main():
    palette_path = ROOT / "tools/vendor/DKC2-disasm/DKC2/Palettes/Sprite_Diddy_Active.bin"
    report = {"source": "Palettes/Sprite_Diddy_Active.bin",
              "palette_sha256": hashlib.sha256(palette_path.read_bytes()).hexdigest(), "frames": []}
    for frame in (40, 100, 140, 153, 180):
        cgram = (STAGE / ("reference-frame-%04d-cgram.bin" % frame)).read_bytes()
        report["frames"].append({"frame": frame, **find(palette_path.read_bytes(), cgram),
                                 "cgram_sha256": hashlib.sha256(cgram).hexdigest()})
    path = STAGE / "diddy-palette-verification.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
