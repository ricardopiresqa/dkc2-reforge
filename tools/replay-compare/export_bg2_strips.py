"""Bake ShipDeck BG2 into per-scanline strips with the original color math applied.

BG2 V-scroll is fixed at -1 (BBA655 / 809F81 write $FF), so screen row y always shows
BG2 row y; only H changes per line (main/original_bg2.lua ports 80E540). Color math:
$2131 enables BG2 only (ppu.colorMathEnabled=2), add mode, no halving; the fixed color
comes from HDMA channel 2 (COLDATA, mode 0) table DATA_BBA6C6. With no subscreen pixel
the fixed color is added per 5-bit channel, saturating at 31.
"""
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "assets-raw/pirate"
DISASM = ROOT / "tools/vendor/DKC2-disasm/DKC2/Routine_Macros_DKC2.asm"
OUT = ROOT / "assets/images/pirate/background/bg2"
BANDS = ((0, 24), (24, 48), (48, 104))  # BBA655 counts $18, $18, $38
SEA_FIRST, SCREEN_H = 104, 224
FRAME = 40


def coldata_table():
    source = DISASM.read_text(encoding="utf-8", errors="replace")
    block = source.split("DATA_BBA6C6:\n", 1)[1].split("\nCODE_", 1)[0]
    data = [int(value, 16) for value in re.findall(r"\$([0-9A-F]{2})", block)]
    rows, state, index = [], [0, 0, 0], 0
    while data[index] != 0:  # mode 0: count byte then one COLDATA byte
        count, value = data[index], data[index + 1]
        for channel, bit in enumerate((0x20, 0x40, 0x80)):  # R, G, B select bits
            if value & bit:
                state[channel] = value & 0x1F
        rows.extend([tuple(state)] * (count & 0x7F))
        index += 2
    return rows


def bg2_indices():
    """Return (palette-resolved 5-bit RGB rows) for BG2 from the captured VRAM/CGRAM."""
    spec = importlib.util.spec_from_file_location("bg", ROOT / "tools/replay-compare/export_original_backgrounds.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    vram = (STAGE / ("reference-frame-%04d-vram.bin" % FRAME)).read_bytes()
    cgram = (STAGE / ("reference-frame-%04d-cgram.bin" % FRAME)).read_bytes()
    meta = dict(line.split("=", 1) for line in (STAGE / ("reference-frame-%04d-ppu.txt" % FRAME)).read_text().splitlines())
    map_base = int(meta["ppu.layers[1].tilemapAddress"]) * 2
    gfx_base = int(meta["ppu.layers[1].chrAddress"]) * 2
    assert meta["ppu.layers[1].doubleWidth"] == "false" and meta["ppu.layers[1].doubleHeight"] == "false"
    pixels = [[None] * 256 for _ in range(256)]
    for ty in range(32):
        for tx in range(32):
            word = int.from_bytes(vram[map_base + (ty * 32 + tx) * 2:][:2], "little")
            tile = module.tile_pixels(vram, gfx_base + (word & 1023) * 32, 4)
            palette = (word >> 10) & 7
            for y in range(8):
                for x in range(8):
                    value = tile[7 - y if word & 0x8000 else y][7 - x if word & 0x4000 else x]
                    if value:
                        color = int.from_bytes(cgram[(palette * 16 + value) * 2:][:2], "little")
                        pixels[ty * 8 + y][tx * 8 + x] = (color & 31, color >> 5 & 31, color >> 10 & 31)
    return pixels


def to8(channel):
    return channel * 255 // 31  # same conversion as export_original_backgrounds.py


def strip(pixels, add, top, bottom):
    image = Image.new("RGBA", (256, bottom - top))
    out = image.load()  # PixelAccess writes (faster than putpixel)
    for y in range(top, bottom):
        for x in range(256):
            color = pixels[y][x]
            if color is None:
                continue
            r, g, b = (min(31, c + a) for c, a in zip(color, add[y]))
            out[x, y - top] = (to8(r), to8(g), to8(b), 255)
    return image


def export():
    add = coldata_table()
    assert len(add) >= SCREEN_H, len(add)
    assert all(row == (0, 0, 0) for row in add[:SEA_FIRST]), "sky bands must not receive color math"
    pixels = bg2_indices()
    OUT.mkdir(parents=True, exist_ok=True)
    strips = [("original_bg2_band_%d" % index, top, bottom) for index, (top, bottom) in enumerate(BANDS)]
    strips += [("original_bg2_line_%03d" % y, y, y + 1) for y in range(SEA_FIRST, SCREEN_H)]
    report = {"source_frame": FRAME, "coldata_first_add_row": next(i for i, r in enumerate(add) if r != (0, 0, 0)),
              "strips": []}
    for name, top, bottom in strips:
        image = strip(pixels, add, top, bottom)
        path = OUT / (name + ".png")
        image.save(path)
        report["strips"].append({"id": name, "top": top, "bottom": bottom,
                                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    (STAGE / "bg2-strips-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = export()
    print(json.dumps({"strips": len(result["strips"]), "coldata_first_add_row": result["coldata_first_add_row"]}))
    sys.exit(0)
