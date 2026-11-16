"""Classify VRAM/CGRAM changes between gameplay and late reference snapshots."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "assets-raw/pirate"


def ranges(different, width):
    spans = []
    for start in range(0, len(different), width):
        part = different[start:start + width]
        if any(part):
            spans.append({"offset": start, "changed_bytes": sum(part)})
    return spans


def main():
    a, b = ((STAGE / name).read_bytes() for name in (
        "reference-frame-0040-vram.bin", "reference-vram.bin"))
    ca, cb = ((STAGE / name).read_bytes() for name in (
        "reference-frame-0040-cgram.bin", "reference-cgram.bin"))
    assert len(a) == len(b) == 65536 and len(ca) == len(cb) == 512
    delta = bytes(x != y for x, y in zip(a, b))
    cdelta = bytes(x != y for x, y in zip(ca, cb))
    report = {"scope": "SNES memory snapshots only; no per-pixel claim",
              "gameplay_vram_sha256": hashlib.sha256(a).hexdigest(),
              "late_vram_sha256": hashlib.sha256(b).hexdigest(),
              "vram_changed_bytes": sum(delta),
              "vram_changed_256B_pages": ranges(delta, 256),
              "cgram_changed_bytes": sum(cdelta),
              "cgram_changed_words": [i for i in range(256) if ca[i*2:i*2+2] != cb[i*2:i*2+2]],
              "status": "classified; determine which source ranges feed composited ShipDeck planes"}
    (STAGE / "ppu-snapshot-difference.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
