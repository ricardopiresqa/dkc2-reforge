"""Export layer pixels from original captured SNES hardware state.

No screenshot is used as the gameplay background: planes are decoded from
VRAM/CGRAM. This does NOT emulate HDMA, scroll timing or color math.
"""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "assets-raw/pirate"


def tile_pixels(data, offset, bpp):
    pixels = []
    for y in range(8):
        row = []
        for x in range(8):
            value = 0
            for plane in range(bpp):
                address = offset + (plane // 2) * 16 + y * 2 + plane % 2
                # SNES 64KiB VRAM addressing wraps at the hardware boundary.
                value |= ((data[address % len(data)] >> (7 - x)) & 1) << plane
            row.append(value)
        pixels.append(row)
    return pixels


def render_layer(vram, cgram, metadata, index, bpp):
    prefix = "ppu.layers[%d]." % index
    width = 64 if metadata[prefix + "doubleWidth"] == "true" else 32
    height = 64 if metadata[prefix + "doubleHeight"] == "true" else 32
    map_base = int(metadata[prefix + "tilemapAddress"]) * 2
    gfx_base = int(metadata[prefix + "chrAddress"]) * 2
    assert metadata[prefix + "largeTiles"] == "false"
    image = Image.new("RGBA", (width * 8, height * 8))
    canvas = image.load()  # PixelAccess writes (faster than putpixel)
    for ty in range(height):
        for tx in range(width):
            block = (ty // 32) * (width // 32) + tx // 32
            offset = map_base + block * 2048 + ((ty % 32) * 32 + tx % 32) * 2
            word = int.from_bytes(vram[offset:offset + 2], "little")
            tile = word & 1023
            palette = (word >> 10) & 7
            pixels = tile_pixels(vram, gfx_base + tile * bpp * 8, bpp)
            for y in range(8):
                for x in range(8):
                    sx = 7 - x if word & 0x4000 else x
                    sy = 7 - y if word & 0x8000 else y
                    value = pixels[sy][sx]
                    if value == 0:
                        continue
                    color_index = palette * (1 << bpp) + value
                    color = int.from_bytes(cgram[color_index * 2:color_index * 2 + 2], "little")
                    rgb = tuple((color >> shift & 31) * 255 // 31 for shift in (0, 5, 10))
                    canvas[tx * 8 + x, ty * 8 + y] = (*rgb, 255)
    return image


def export(frame=None):
    suffix = "-frame-%04d" % frame if frame is not None else ""
    vram = (STAGE / ("reference%s-vram.bin" % suffix if frame is not None else "reference-vram.bin")).read_bytes()
    cgram = (STAGE / ("reference%s-cgram.bin" % suffix if frame is not None else "reference-cgram.bin")).read_bytes()
    assert len(vram) == 65536 and len(cgram) == 512
    ppu_path = STAGE / ("reference-frame-%04d-ppu.txt" % frame if frame is not None else "reference-ppu.txt")
    metadata = dict(line.split("=", 1) for line in ppu_path.read_text().splitlines())
    assert metadata["ppu.bgMode"] == "1"
    out = (STAGE / ("frame-backgrounds/%04d" % frame) if frame is not None
           else ROOT / "assets/images/pirate/background")
    out.mkdir(parents=True, exist_ok=True)
    report = {"frame": frame, "vram_sha256": hashlib.sha256(vram).hexdigest(),
              "cgram_sha256": hashlib.sha256(cgram).hexdigest(),
              "ppu_sha256": hashlib.sha256(ppu_path.read_bytes()).hexdigest(),
              "status": "original hardware pixels; HDMA/color math/scroll not validated", "layers": []}
    for index, bpp in ((0, 4), (1, 4), (2, 2)):
        image = render_layer(vram, cgram, metadata, index, bpp)
        name = "original_bg%d_01.png" % (index + 1)
        image.save(out / name)
        report["layers"].append({"id": index + 1, "bpp": bpp,
                                 "width": image.width, "height": image.height,
                                 "source_png": name, "png_sha256": hashlib.sha256((out / name).read_bytes()).hexdigest()})
    (STAGE / "background-render-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    export(int(sys.argv[1]) if len(sys.argv) > 1 else None)
