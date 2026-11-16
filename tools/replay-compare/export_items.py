"""Export Pirate Panic item sprites from their original spawn and animation scripts.

Spawn script (param -> DATA_FBE800 -> bank $FF): `$0000 : id` sets the SpriteID,
`$8100 : n` the animation (F9 table at $390000 + n*4), `$8D00 : p` the palette index
into DATA_FD5FEE. Animation bytecode `op < $80` shows pose `arg` (BC8000 table at
$3C8000 + arg) for `op` frames; `$80`/`$82` close the idle loop; `$81 xx` is a callback and `$8F cb,dst`
a conditional branch (both skipped: idle path only).
Poses render with gfx_assemble; their pieces are relative to the sprite origin, which
is the level object's (x, feet_y) in port coordinates (verified: WoodenBox in WRAM).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools/vendor/DKC2-disasm/DKC2"
ROM = SOURCE / "Donkey Kong Country 2 (USA V1.0).sfc"
OUT = ROOT / "assets/images/pirate/items"
sys.path.insert(0, str(ROOT / "tools"))
import gfx_assemble  # noqa: E402
import import_pirate_panic as importer  # noqa: E402
from gfx_convert import load_palette  # noqa: E402

# DK barrel emblem: sprite $11C spawned with the barrel at the same origin
# (reference-sprites-trace.csv), animation $2BF; OBJ palette 0 in the captured CGRAM is
# exactly Palettes/Sprite_HUDNumbers.bin (items-frame-0600-cgram.bin).
COMPANIONS = {2638: (0x2BF, "Sprite_HUDNumbers.bin")}
# Level-end goal children and hit animation (goal-route-t4/t6.csv, OAM + CGRAM of
# goal-t7-frame-4946): $2B4 the struck target (goal's own palette, OBJ slot 5), $2C1 the
# pole ($168) and $2C2 the barrel on top ($164), both in OBJ slot 3 = Sprite_Barrel.
EXTRA_ANIMATIONS = {0x2B4: "Sprite_LevelEndGoal.bin", 0x2C1: "Sprite_Barrel.bin", 0x2C2: "Sprite_Barrel.bin"}

ITEM_PARAMS = {2102: "banana_coin", 2106: "kremkoin", 2110: "kremkoin", 2112: "dk_coin",
               2046: "wooden_box", 2042: "star_barrel", 2638: "dk_barrel",
               2114: "kong_k", 2116: "kong_o", 2120: "kong_n",  # $4C letter bit 1/2/4
               3174: "level_end_goal", 2138: "no_animal_sign", 2020: "animal_buddy_box",
               2636: "krool_note",  # Captain's Kabin
               3188: "banana_bunch",  # sprite $170 at 1504/384 (route-bot-trace.csv; level object named 'Kloak')
               2852: "extra_life_balloon"}  # ExtraLifeBalloon $178 in the Kabin (kabin-route-t3.csv)


def word(rom, offset):
    return rom[offset] | rom[offset + 1] << 8


def spawn_fields(rom, param):
    """Run the spawn script: `$8300 p` CALLS sub-script p and returns (`$8000` ends the
    current level); later writes override earlier ones. Returns sprite_id, animation,
    palette, fields."""
    result, fields = {}, {}

    def run(pointer, depth):
        if depth > 8:
            raise ValueError("spawn script nesting too deep at param %d" % param)
        offset = importer.DEF_BANK_FILE_OFFSET + pointer
        for _ in range(64):
            opcode = word(rom, offset)
            offset += 2
            if opcode & 0x8000 == 0:
                fields[opcode] = word(rom, offset)
                offset += 2
            elif opcode >> 8 == 0x80:
                return
            elif opcode >> 8 == 0x83:
                run(word(rom, offset), depth + 1)
                offset += 2
            elif opcode >> 8 in (0x81, 0x82, 0x84, 0x85, 0x8A, 0x8B, 0x8C, 0x8D):
                value = word(rom, offset)
                offset += 2
                result[{0x81: "animation", 0x8D: "palette"}.get(opcode >> 8, "op%02x" % (opcode >> 8))] = value
            elif opcode >> 8 in (0x86, 0x87):
                offset += 4
            elif opcode >> 8 == 0x88:
                pass
            else:
                raise ValueError("unsupported spawn opcode %04x at param %d" % (opcode, param))
        raise ValueError("spawn script too long at param %d" % param)

    run(word(rom, importer.FBE800_ROM_OFFSET + param), 0)
    result["sprite_id"] = fields.get(0)
    result["fields"] = fields
    return result


def animation(rom, number):
    """[(frames, pose_offset)] from F9 bytecode until $80 (loop)."""
    pc = word(rom, 0x390000 + number * 4)
    frames = []
    for _ in range(256):
        op = rom[0x390000 + pc]
        if op < 0x80:
            frames.append((op, word(rom, 0x390000 + pc + 1)))
            pc += 3
        elif op in (0x80, 0x82):  # $80 restart / $82 jump: end of the idle loop
            return frames
        elif op == 0x8F:          # conditional callback + branch (e.g. "collected"): not taken
            pc += 5
        elif op in (0x81, 0x83, 0x84, 0x8E):
            pc += 3
        else:
            raise ValueError("unsupported animation opcode %02x in %x" % (op, number))
    raise ValueError("animation %x too long" % number)


def pose_names(rom):
    text = (SOURCE / "Routine_Macros_DKC2.asm").read_text(encoding="utf-8", errors="replace")
    pattern = r'^DATA_([0-9A-F]{6}):\n(?:\tdb [^\n]*\n)+\tincbin "Graphics/DynamicSprites/([^"]+)"'
    by_address = {int(m.group(1), 16): m.group(2) for m in re.finditer(pattern, text, re.M)}
    return lambda offset: by_address[int.from_bytes(rom[0x3C8000 + offset:0x3C8000 + offset + 3], "little")]


def palette_file(index):
    text = (SOURCE / "Routine_Macros_DKC2.asm").read_text(encoding="utf-8", errors="replace")
    block = text.split("DATA_FD5FEE:\n", 1)[1].split("\n\n", 1)[0]
    labels = re.findall(r"DATA_([0-9A-F]{6})(\+\$02)?", block)
    label, plus = labels[index]
    assert not plus, "palette entries with +$02 offsets are not used by these items"
    return re.search(r"^DATA_%s:\n\tincbin \"Palettes/([^\"]+)\"" % label, text, re.M).group(1)


def render(pose, palette):
    """Pose image plus the origin's position inside it."""
    poses = gfx_assemble.load_poses()
    image, error = gfx_assemble.render_pose(pose, poses, palette, pad=0)
    assert image is not None, error
    pieces = gfx_assemble.build_pieces(poses[pose])
    return image, -min(p[0] for p in pieces), -min(p[1] for p in pieces)


def export():
    rom = ROM.read_bytes()
    name_of = pose_names(rom)
    OUT.mkdir(parents=True, exist_ok=True)
    items, animations = {}, {}
    for param, kind in ITEM_PARAMS.items():
        spawn = spawn_fields(rom, param)
        number = spawn["animation"]
        # DK Coin's spawn omits $8D; the coin family ($15C) only has Sprite_Coins (index
        # 20) in the ROM. Inferred, pending a pixel capture with the DK Coin on screen.
        palette_index = spawn.get("palette", 20 if spawn["sprite_id"] == 0x15C else None)
        palette_name = palette_file(palette_index)
        palette = load_palette(str(SOURCE / "Palettes" / palette_name))
        items[param] = {"kind": kind, "sprite_id": spawn["sprite_id"], "animation": number,
                        "palette": palette_name, "palette_inferred": "palette" not in spawn,
                        "subtype": spawn["fields"].get(0x2E, 0),
                        "spawn_range": spawn["fields"].get(0x5C, 0)}
        jobs = [(number, palette)]
        if param in COMPANIONS:
            companion, companion_palette = COMPANIONS[param]
            items[param]["companion"] = companion
            jobs.append((companion, load_palette(str(SOURCE / "Palettes" / companion_palette))))
        render_animations(rom, name_of, animations, jobs)
    extra = [(number, load_palette(str(SOURCE / "Palettes" / name))) for number, name in EXTRA_ANIMATIONS.items()]
    render_animations(rom, name_of, animations, extra)
    import export_diddy_moves as moves  # imports this module: deferred
    moves.insert_atlas_groups({"original_item_%03x" % number: ["/assets/images/pirate/items/%s.png" % frame["sprite"]
                                                               for frame in animations[number]]
                               for number, _ in extra})
    write(items, animations)
    report = {"items": items, "animations": {hex(k): v for k, v in animations.items()}}
    (ROOT / "assets-raw/pirate/items-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def write(items, animations):
    lines = ["-- Generated by tools/replay-compare/export_items.py (spawn + F9 animation scripts).",
             "return { items = {"]
    for param, item in items.items():
        lines.append('  [%d] = { kind = "%s", sprite_id = %d, animation = %d, subtype = %d, spawn_range = %d, companion = %s },'
                     % (param, item["kind"], item["sprite_id"], item["animation"], item["subtype"],
                        item["spawn_range"], item.get("companion", "nil")))
    lines.append("}, animations = {")
    for number, frames in animations.items():
        lines.append("  [%d] = {" % number)
        for frame in frames:
            lines.append('    { sprite = "%s", frames = %d, origin_x = %d, origin_y = %d, width = %d, height = %d, pose = %d },'
                         % (frame["sprite"], frame["frames"], frame["origin_x"], frame["origin_y"],
                            frame["width"], frame["height"], frame["pose_offset"]))
        lines.append("  },")
    lines.append("} }")
    (ROOT / "data/original/pirate/items.lua").write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_animations(rom, name_of, animations, jobs):
    """Render [(animation number, palette)] into animations[number] (skips done ones)."""
    for job_number, job_palette in jobs:
        if job_number in animations:
            continue
        frames = []
        for index, (duration, offset) in enumerate(animation(rom, job_number)):
            pose = name_of(offset)
            image, origin_x, origin_y = render(pose, job_palette)
            sprite = "original_item_%03x_%d" % (job_number, index)
            image.save(OUT / (sprite + ".png"))
            frames.append({"sprite": sprite, "frames": duration, "pose": pose, "pose_offset": offset,
                           "origin_x": origin_x, "origin_y": origin_y,
                           "width": image.width, "height": image.height})
        animations[job_number] = frames


if __name__ == "__main__":
    result = export()
    print(json.dumps({param: (item["kind"], hex(item["animation"]), item["palette"])
                      for param, item in result["items"].items()}, indent=1))
    sys.exit(0)
