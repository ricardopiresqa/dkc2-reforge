"""Report original per-frame CGRAM changes; does not alter rendered artwork."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "assets-raw/pirate"
FRAMES = (40, 60, 100, 140, 153, 158, 165, 173, 180)


def colors(raw):
    assert len(raw) == 512
    return [int.from_bytes(raw[index:index + 2], "little") & 0x7FFF
            for index in range(0, 512, 2)]


def main():
    results = []
    for frame in FRAMES:
        raw = (STAGE / ("reference-frame-%04d-cgram.bin" % frame)).read_bytes()
        sample = colors(raw)
        final = colors((STAGE / "reference-cgram.bin").read_bytes())
        changed = [index for index, pair in enumerate(zip(sample, final)) if pair[0] != pair[1]]
        results.append({"frame": frame, "cgram_sha256": hashlib.sha256(raw).hexdigest(),
                        "colors_changed_vs_final_snapshot": len(changed),
                        "indices_changed": changed,
                        "layer_palettes_changed": sorted({index // 16 for index in changed}),
                        "cgram_exactly_matches_final": not changed})
    report = {"scope": "palette memory only; scanline color math is separate", "frames": results}
    (STAGE / "frame-palette-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
