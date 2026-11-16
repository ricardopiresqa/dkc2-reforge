"""Assemble the ShipDeck BG3 rigging map from source data and check it against VRAM.

Source: DATA_F526A7 (40 columns x 16 rows of metatile words, column-major) and
DATA_F52087 (32x32 px metatiles, 4x4 tile words, row-major) as streamed by
B5A950/B5AAE6. Entry bit $8000 flips V (rows reversed, tile EOR $8000), bit $4000
flips H (columns mirrored, tile EOR $4000). Screen pixel (sx, sy) shows map pixel
((L1X + L1X/4 + sx) mod 1280, (L1Y - 256 + sy) mod 512) — see 80E4EB.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISASM = ROOT / "tools/vendor/DKC2-disasm/DKC2"
STAGE = ROOT / "assets-raw/pirate"
COLUMNS, ROWS = 40, 16
FRAMES = (40, 60, 100, 140, 153, 158, 165, 173, 180)


def bg3_scroll(l1x, l1y):
    """80E4EB/NMI: BG3 registers from the PREVIOUS frame's layer-1 position."""
    return (l1x + (l1x >> 2)) % 1024, (l1y - 257) % 1024


def map_origin(l1x, l1y):
    """Map pixel shown at screen (0, 0): rigging wraps at 1280 x 512."""
    return (l1x + (l1x >> 2)) % 1280, (l1y - 256) % 512


def column_map():
    source = (DISASM / "Routine_Macros_DKC2.asm").read_text(encoding="utf-8", errors="replace")
    block = source.split("DATA_F526A7:\n", 1)[1].split(".End:", 1)[0]  # local .End label
    words = [int(value, 16) for value in re.findall(r"\$([0-9A-F]{4})", block)]
    assert len(words) == COLUMNS * ROWS, len(words)
    return words


def tile_words():
    """Return the map as 160x64 tile words (8x8 tiles), exactly as streamed."""
    entries = column_map()
    metatiles = (DISASM / "Tilemaps/Layer3_ShipDeck.bin").read_bytes()
    word = lambda offset: int.from_bytes(metatiles[offset:offset + 2], "little")
    grid = [[0] * (COLUMNS * 4) for _ in range(ROWS * 4)]
    for column in range(COLUMNS):
        for row in range(ROWS):
            entry = entries[column * ROWS + row]
            base = (entry << 5) & 0xFFFF  # ASL x5 drops the flip bits
            flip = entry & 0xC000
            for ty in range(4):
                for tx in range(4):
                    sx = 3 - tx if flip & 0x4000 else tx
                    sy = 3 - ty if flip & 0x8000 else ty
                    grid[row * 4 + ty][column * 4 + tx] = word(base + sy * 8 + sx * 2) ^ flip
    return grid


def ppu(frame):
    path = STAGE / ("reference-frame-%04d-ppu.txt" % frame)
    return dict(line.split("=", 1) for line in path.read_text().splitlines())


def verify(grid):
    """Every interior on-screen BG3 tilemap cell in VRAM must equal the map word."""
    import csv

    camera = list(csv.DictReader((STAGE / "reference-camera.csv").open()))
    results = []
    for frame in FRAMES:
        vram = (STAGE / ("reference-frame-%04d-vram.bin" % frame)).read_bytes()
        meta = ppu(frame)
        base = int(meta["ppu.layers[2].tilemapAddress"]) * 2
        wide = meta["ppu.layers[2].doubleWidth"] == "true"
        h, v = int(camera[frame]["bg3_hscroll"]), int(camera[frame]["bg3_vscroll"])
        l1x, l1y = int(camera[frame - 1]["camera_x_raw"]), int(camera[frame - 1]["camera_y_raw"])
        map_x, map_y = map_origin(l1x, l1y)
        checked = mismatched = 0
        # Interior only: edge columns/rows are streamed one 8px step behind.
        for sy in range(8, 216, 8):
            for sx in range(8, 248, 8):
                vx, vy = (h + sx) % (512 if wide else 256), (v + 1 + sy) % 256
                tx, ty = vx // 8, vy // 8
                block = (tx // 32) if wide else 0
                offset = base + block * 2048 + ((ty % 32) * 32 + tx % 32) * 2
                observed = int.from_bytes(vram[offset:offset + 2], "little")
                mx, my = (map_x + sx) % 1280, (map_y + sy) % 512
                if (mx % 8, my % 8) != (vx % 8, vy % 8):
                    raise ValueError("sub-tile phase differs at frame %d" % frame)
                expected = grid[my // 8][mx // 8]
                checked += 1
                mismatched += observed != expected
        results.append({"frame": frame, "cells": checked, "mismatched": mismatched})
    return results


def render(grid, cgram, chr_base):
    from PIL import Image

    gfx = (DISASM / "Graphics/GFX_Layer3_ShipDeck.bin").read_bytes()
    vram = bytearray(65536)
    vram[46048:46048 + len(gfx)] = gfx  # load address proven in source-report.json
    layers = {0: Image.new("RGBA", (1280, 512)), 1: Image.new("RGBA", (1280, 512))}
    access = {key: image.load() for key, image in layers.items()}  # PixelAccess writes (faster than putpixel)
    for ty, line in enumerate(grid):
        for tx, word in enumerate(line):
            address = chr_base + (word & 1023) * 16
            palette = (word >> 10) & 7
            pixels = access[(word >> 13) & 1]
            for y in range(8):
                for x in range(8):
                    px = 7 - x if word & 0x4000 else x
                    py = 7 - y if word & 0x8000 else y
                    row = address + py * 2
                    value = (vram[row] >> (7 - px) & 1) | (vram[row + 1] >> (7 - px) & 1) << 1
                    if value:
                        color = int.from_bytes(cgram[(palette * 4 + value) * 2:][:2], "little")
                        rgb = tuple((color >> shift & 31) * 255 // 31 for shift in (0, 5, 10))
                        pixels[tx * 8 + x, ty * 8 + y] = (*rgb, 255)
    return layers


def export():
    grid = tile_words()
    checks = verify(grid)
    meta = ppu(40)
    cgram = (STAGE / "reference-frame-0040-cgram.bin").read_bytes()
    layers = render(grid, cgram, int(meta["ppu.layers[2].chrAddress"]) * 2)
    out = ROOT / "assets/images/pirate/background"
    out.mkdir(parents=True, exist_ok=True)
    report = {"source": "DATA_F526A7 + Tilemaps/Layer3_ShipDeck.bin + Graphics/GFX_Layer3_ShipDeck.bin",
              "map_px": [1280, 512], "vram_checks": checks,
              "priority_tiles": sum(1 for line in grid for word in line if word & 0x2000),
              "status": "PASS" if all(c["mismatched"] == 0 for c in checks) else "FAIL",
              "layers": []}
    for priority, image in layers.items():
        if image.getbbox() is None:
            continue
        name = "original_bg3_rigging_p%d.png" % priority
        image.save(out / name)
        report["layers"].append({"priority": priority, "png": name,
                                 "png_sha256": hashlib.sha256((out / name).read_bytes()).hexdigest()})
    (STAGE / "bg3-rigging-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(export())
