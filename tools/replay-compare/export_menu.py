"""Original menu screens after the title (game select, mode select, island, level card).

Input: assets-raw/pirate/menu-nav/t2..t6-frame-NNNN.ppm (menu_nav_capture.lua):
  t2 = Select Game with the cursor on each item, t3 = the mode screen, t5 = the Mono/
  Stereo and English/Francais toggles, t6 = island and Pirate Panic card (steady frames).
The Select Game screen is static; only the selected item changes (bright text). Output:
a base screen (cursor on game 1) plus per item an "on" and an "off" patch cropped where
that item differs, and full screens for the rest, under assets/images/pirate/menu, and
data/original/pirate/menu.lua. Stereo has no captured dim frame: its "off" patch maps the
"on" colours through the Mono on->off colour pairs (APPROXIMATION, marked in the data).
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "assets-raw/pirate/menu-nav"
OUT = ROOT / "assets/images/pirate/menu"

SELECT = {"game1": "t2-frame-1155", "game2": "t2-frame-1200", "game3": "t2-frame-1260",
          "copy": "t2-frame-1320", "mono": "t2-frame-1380", "english": "t2-frame-1440",
          "erase": "t2-frame-1500"}
MODE = {"one": "t3-frame-1395", "team": "t3-frame-1440", "contest": "t3-frame-1500",
        # hidden modes (t9/t11): 5 DOWN on Contest reveal Music Test, 5 more Cheat Mode
        "music": "t9-frame-1745", "cheat": "t11-frame-1750"}
# Music Test names are OBJ in the area-name font (CODE_809DA2): char c -> tile $002 +
# 2 * DATA_B4C46B[c - $21], an 8x16 pair; OBJ tiles from VRAM 0, OBJ palette 0 (t13).
FONT_FRAME = "t13-frame-1660"
FONT_TABLE = [0x26, 0x28, 0x2A, 0x2B, 0x2C, 0x2D, 0x1A, 0x2F, 0x30, 0x31, 0x32, 0x26, 0x22, 0x1E, 0x29, 0x03,
              0x07, 0x0B, 0x0F, 0x13, 0x17, 0x1B, 0x1F, 0x23, 0x27, 0x33, 0x34, 0x35, 0x36, 0x37, 0x2E, 0x38,
              0x00, 0x04, 0x08, 0x0C, 0x10, 0x14, 0x18, 0x1C, 0x20, 0x24, 0x01, 0x05, 0x09, 0x0D, 0x11, 0x15,
              0x19, 0x1D, 0x21, 0x25, 0x02, 0x06, 0x0A, 0x0E, 0x12, 0x16]  # DATA_B4C46B, chars $21-$5A


def track_names():
    """DATA_809C59 -> the 31 Music Test names (DATA_809C99...)."""
    text = (ROOT / "tools/vendor/DKC2-disasm/DKC2/Routine_Macros_DKC2.asm").read_text(encoding="utf-8", errors="replace")
    block = text.split("DATA_809C59:\n", 1)[1].split("\n\n", 1)[0]
    labels = re.findall(r"DATA_809[0-9A-F]{3}", block)
    return [re.search(r'^%s:\n\tdb "([^"]*)"' % label, text, re.M).group(1) for label in labels]


def font_glyphs():
    """{char code: image 8x16} from the captured VRAM and CGRAM."""
    sys.path.insert(0, str(ROOT / "tools"))
    from gfx_convert import decode_tile
    vram = (SOURCE / (FONT_FRAME + "-vram.bin")).read_bytes()
    cgram = (SOURCE / (FONT_FRAME + "-cgram.bin")).read_bytes()

    def colour(index):
        word = cgram[index * 2] | cgram[index * 2 + 1] << 8
        return ((word & 31) * 255 // 31, (word >> 5 & 31) * 255 // 31, (word >> 10 & 31) * 255 // 31, 255)
    glyphs = {}
    for offset, index in enumerate(FONT_TABLE):
        image = Image.new("RGBA", (8, 16), (0, 0, 0, 0))
        for half in range(2):
            tile = 0x002 + 2 * index + half
            for y, row in enumerate(decode_tile(vram[tile * 32:tile * 32 + 32])):
                for x, value in enumerate(row):
                    if value:
                        image.putpixel((x, y + 8 * half), colour(128 + value))
        glyphs[0x21 + offset] = image
    return glyphs
# Animated screens (t14: every frame while they wait): base frame + per-region patches,
# one per distinct crop, looped over the captured run (no period found in 560/600 frames).
ANIMATED = {
    "island": (1600, 2160, [(0, 0, 256, 32), (128, 32, 192, 48), (0, 48, 64, 176), (96, 48, 224, 96),
                            (208, 112, 256, 176), (0, 160, 256, 224), (64, 112, 96, 144), (160, 128, 208, 160)]),
    "card": (2260, 2860, [(29, 65, 46, 84)]),
}
# Stereo on (Mono toggled), Francais on and off (English toggled; cursor elsewhere).
STEREO_ON, MONO_ON_T5 = "t5-frame-1390", "t5-frame-1330"
FRANCAIS_ON, ENGLISH_ON_T5, FRANCAIS_OFF = "t5-frame-1570", "t5-frame-1510", "t5-frame-1690"


def load(name):
    image = Image.open(SOURCE / (name + ".ppm")).convert("RGB")
    return image.crop((0, 7, 256, 231)) if image.height > 224 else image


def changed(a, b, area=None):
    mask = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 20 else 0)
    if area:
        clipped = Image.new("L", mask.size, 0)
        clipped.paste(mask.crop(area), area[:2])
        mask = clipped
    return mask.getbbox()


def regions(screens):
    """Item box: where the item's state differs from game 1's, inside the item's area."""
    base = screens["game1"]
    g1 = changed(base, screens["game2"], (0, 40, 256, 80))
    result = {"game1": g1}
    areas = {"game2": (0, 80, 256, 120), "game3": (0, 120, 256, 165), "copy": (0, 165, 128, 197),
             "erase": (128, 165, 256, 197), "mono": (0, 197, 128, 224), "english": (128, 197, 256, 224)}
    for item, area in areas.items():
        result[item] = changed(screens[item], base, area)
    return result


def animated(name, first, end, boxes, images):
    """Lua lines for one animated screen; patches go into `images`."""
    base = load("t14-frame-%04d" % first)
    images["original_menu_%s" % name] = base
    lines = ['  %s_anim = { frames = %d, regions = {' % (name, end - first)]
    for index, box in enumerate(boxes):
        seen, sequence, previous = {}, [], None
        for frame in range(first, end):
            patch = load("t14-frame-%04d" % frame).crop(box)
            key = patch.tobytes()
            if key == previous:
                continue
            previous = key
            if key not in seen:
                seen[key] = "original_menu_%s_r%d_%03d" % (name, index, len(seen))
                images[seen[key]] = patch
            sequence.append('{ %d, "%s" }' % (frame - first, seen[key]))
        lines.append("    { box = { %d, %d, %d, %d }, seq = { %s } }," % (
            box[0], box[1], box[2] - box[0], box[3] - box[1], ", ".join(sequence)))
    lines.append("  } },")
    return lines


def dim_like(on_patch, mono_on, mono_off):
    """Map bright text colours to dim ones through the Mono on/off pixel pairs."""
    pairs = {}
    for a, b in zip(mono_on.getdata(), mono_off.getdata()):
        if a != b:
            pairs.setdefault(a, b)
    out = on_patch.copy()
    out.putdata([pairs.get(pixel, pixel) for pixel in on_patch.getdata()])
    return out


def export():
    OUT.mkdir(parents=True, exist_ok=True)
    screens = {item: load(name) for item, name in SELECT.items()}
    boxes = regions(screens)
    images = {"original_menu_select": screens["game1"]}
    patches = []
    for item, box in boxes.items():
        off_source = screens["game2"] if item == "game1" else screens["game1"]
        images["original_menu_%s_on" % item] = screens[item].crop(box)
        images["original_menu_%s_off" % item] = off_source.crop(box)
        patches.append((item, box))
    # toggled labels
    stereo_on, mono_on = load(STEREO_ON), load(MONO_ON_T5)
    def union(a, b):  # the toggled label covers the other one's box too
        return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))
    stereo_box = union(changed(stereo_on, mono_on, (0, 197, 128, 224)), boxes["mono"])
    images["original_menu_stereo_on"] = stereo_on.crop(stereo_box)
    images["original_menu_stereo_off"] = dim_like(stereo_on.crop(stereo_box), mono_on.crop(stereo_box),
                                                  screens["game1"].crop(stereo_box))
    francais_on, english_on = load(FRANCAIS_ON), load(ENGLISH_ON_T5)
    francais_box = union(changed(francais_on, english_on, (128, 197, 256, 224)), boxes["english"])
    images["original_menu_francais_on"] = francais_on.crop(francais_box)
    images["original_menu_francais_off"] = load(FRANCAIS_OFF).crop(francais_box)
    for item, name in MODE.items():
        images["original_menu_mode_%s" % item] = load(name)
    anim_lines = []
    for item, (first, end, boxes) in ANIMATED.items():
        anim_lines += animated(item, first, end, boxes, images)
    for code, glyph in font_glyphs().items():
        images["original_menu_font_%02x" % code] = glyph
    for name, image in images.items():
        image.save(OUT / (name + ".png"))
    lines = ["-- Generated by tools/replay-compare/export_menu.py (menu_nav_capture.lua t2..t6).",
             "-- Boxes are x, y, w, h on the 256x224 screen. stereo_off is derived (APPROXIMATION).",
             "return {", "  items = {"]
    for item, box in patches:
        lines.append('    %s = { %d, %d, %d, %d },' % ((item,) + (box[0], box[1], box[2] - box[0], box[3] - box[1])))
    lines.append("  },")
    for name, box in (("stereo", stereo_box), ("francais", francais_box)):
        lines.append('  %s = { %d, %d, %d, %d },' % ((name,) + (box[0], box[1], box[2] - box[0], box[3] - box[1])))
    lines.append("  tracks = { %s }," % ", ".join('"%s"' % name for name in track_names()))
    lines += anim_lines
    lines.append("}")
    (ROOT / "data/original/pirate/menu.lua").write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import export_diddy_moves as moves
    moves.insert_atlas_groups({name: ["/assets/images/pirate/menu/%s.png" % name] for name in images})
    return {item: box for item, box in patches}, stereo_box, francais_box


if __name__ == "__main__":
    print(export())
