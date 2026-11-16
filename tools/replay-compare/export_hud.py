"""Export DKC2 HUD digit sprites from captured VRAM/CGRAM (BEC814).

Each digit d is two 8x8 OBJ tiles stacked: $1CC + d on top and $1CC + d + $0A below
(name table 1, OBJ palette 0 per $5E = ($0D2C & $0E00) | $3000). The banana icon reuses
the level banana spin frames (tile $0D2C + ($2A & $1C) >> 1).
"""
import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "assets-raw/pirate"
OUT = ROOT / "assets/images/pirate/hud"


def load_background_module():
    spec = importlib.util.spec_from_file_location("bg", ROOT / "tools/replay-compare/export_original_backgrounds.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digits(frame=40):
    background = load_background_module()
    vram = (STAGE / ("reference-frame-%04d-vram.bin" % frame)).read_bytes()
    cgram = (STAGE / ("reference-frame-%04d-cgram.bin" % frame)).read_bytes()
    meta = dict(line.split("=", 1) for line in (STAGE / ("reference-frame-%04d-ppu.txt" % frame)).read_text().splitlines())
    base, second = int(meta["ppu.oamBaseAddress"]) * 2, int(meta["ppu.oamAddressOffset"]) * 2
    images = []
    for digit in range(10):
        image = Image.new("RGBA", (8, 16))
        canvas = image.load()  # PixelAccess writes (faster than putpixel)
        for dy, tile in ((0, 0x1CC + digit), (8, 0x1CC + digit + 0x0A)):
            pixels = background.tile_pixels(vram, base + (tile & 0xFF) * 32 + (second if tile & 0x100 else 0), 4)
            for y in range(8):
                for x in range(8):
                    if pixels[y][x]:
                        color = int.from_bytes(cgram[(128 + pixels[y][x]) * 2:][:2], "little")
                        canvas[x, dy + y] = tuple((color >> s & 31) * 255 // 31 for s in (0, 5, 10)) + (255,)
        images.append(image)
    return images


def life_icon():
    """Lives-panel head: pose GFX_Diddy_LifeIcon.bin ($0977) with palette
    Sprite_Diddy_Active.bin (DATA_FD6484, loaded by BEC68A). Pieces start at (-7, -14)
    from the sprite origin; measured origin = (212, lives digit Y + 16)."""
    sys.path.insert(0, str(ROOT / "tools"))
    import gfx_assemble
    from gfx_convert import load_palette

    poses = gfx_assemble.load_poses()
    palette = load_palette(str(Path(gfx_assemble.PALDIR) / "Sprite_Diddy_Active.bin"))
    image, error = gfx_assemble.render_pose("GFX_Diddy_LifeIcon.bin", poses, palette, pad=0)
    assert image is not None, error
    assert min(piece[0] for piece in gfx_assemble.build_pieces(poses["GFX_Diddy_LifeIcon.bin"])) == -7
    return image


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for index, image in enumerate(digits()):
        image.save(OUT / ("original_hud_digit_%d.png" % index))
    life_icon().save(OUT / "original_hud_diddy_head.png")
    print(json.dumps({"digits": 10, "head": True, "out": str(OUT.relative_to(ROOT))}))
    sys.exit(0)
