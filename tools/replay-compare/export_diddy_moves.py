"""Add Diddy's remaining Pirate Panic animations to data/original/pirate/animation_scripts.lua.

Scripts: F9 bytecode for the player animation ids below (Misc_Defines_DKC2.asm
!Define_DKC2_Animation_Player_*), decoded with export_animation_scripts.script. Poses not
yet exported are rendered with gfx_assemble and the Diddy palette onto the same 88x88
canvas as the imported ones: pose origin at (31, 62), measured on Run1/Fall5 (both match).
The atlas is updated by inserting single entries (never import_pirate_panic.write_atlas).
"""
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "tools"))
import export_items as items  # noqa: E402
from gfx_convert import load_palette  # noqa: E402

DATA = ROOT / "data/original/pirate/animation_scripts.lua"
POSES = ROOT / "assets/images/pirate/poses"
ATLAS = ROOT / "main/game.atlas"
CANVAS, ORIGIN = 88, (31, 62)
BASE_IDS = (1, 3, 4, 5, 6, 7, 8)
EXTRA_IDS = (0x02, 0x09, 0x0A, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15,
             0x16, 0x17, 0x18, 0x19, 0x1C, 0x29, 0x45, 0x46)


SIZES = {0x80: 1, 0x81: 3, 0x82: 3, 0x83: 3, 0x84: 3, 0x8E: 3, 0x8B: 8, 0x8F: 5, 0x90: 5, 0x89: 6,
         0x91: 4, 0x92: 2, 0x8A: 10}


def script(rom, animation):
    """F9 bytecode with the extra opcodes Diddy's moves use: `$8B dur,pose,dx,dy` (frame
    with the held-object offset), `$8F cb,dst` (branch to dst when cb sets carry) and
    `$90 cb,anim` (call then switch animation), `$89 dur,pose,pose2` (frame + second
    sprite)."""
    word = lambda offset: int.from_bytes(rom[offset:offset + 2], "little")
    signed = lambda v: v - 0x10000 if v & 0x8000 else v
    offset = animation * 4 + 0x390000
    start, flags = word(offset), word(offset + 2)
    pc, code, pending = start, {}, [start]
    while pending:
        pc = pending.pop()
        for _ in range(256):
            if pc in code:
                break
            op = rom[0x390000 + pc]
            size = 3 if op < 0x80 else SIZES.get(op)
            if size is None:
                return {"start": start, "flags": flags, "code": code, "status": "partial", "unsupported_opcode": op}
            entry = {"op": op, "next": pc + size,
                     "arg": word(0x390000 + pc + 1) if size >= 3 and op not in (0x8B, 0x89, 0x8A) else 0}
            if op == 0x8B:
                entry.update(dur=rom[0x390000 + pc + 1], arg=word(0x390000 + pc + 2),
                             dx=signed(word(0x390000 + pc + 4)), dy=signed(word(0x390000 + pc + 6)))
            elif op == 0x89:  # frame + second sprite pose (level-end prize)
                entry.update(dur=rom[0x390000 + pc + 1], arg=word(0x390000 + pc + 2),
                             arg2=word(0x390000 + pc + 4))
            elif op == 0x8A:  # B9D3CA frame + carried Kong pose ($0D7A) at dx/dy ($0D7C/$0D7E)
                entry.update(dur=rom[0x390000 + pc + 1], arg=word(0x390000 + pc + 2),
                             arg2=word(0x390000 + pc + 4), dx=signed(word(0x390000 + pc + 6)),
                             dy=signed(word(0x390000 + pc + 8)))
            elif op in (0x91, 0x92):  # B9D240 call (return pc -> field slot) / B9D259 return
                entry.update(slot=rom[0x390000 + pc + 1], arg=word(0x390000 + pc + 2) if op == 0x91 else 0)
                if op == 0x91:
                    pending.append(entry["arg"])
            elif op in (0x8F, 0x90):
                entry["arg2"] = word(0x390000 + pc + 3)
                if op == 0x8F:
                    pending.append(entry["arg2"])
            code[pc] = entry
            if op in (0x80, 0x82, 0x90, 0x92):
                if op == 0x82:
                    pending.append(entry["arg"])
                break
            pc += size
    return {"start": start, "flags": flags, "code": dict(sorted(code.items())), "status": "exported"}


def existing_poses():
    text = DATA.read_text(encoding="utf-8").split("poses = {", 1)[1]
    return {int(m[1]): (m[2], m[3]) for m in
            re.finditer(r'^\[(\d+)\] = \{ animation = "([^"]+)", gfx = "([^"]+)" \},', text, re.M)}


def render_pose(rom, name, palette):
    image, origin_x, origin_y = items.render(name, palette)
    canvas = Image.new("RGBA", (CANVAS, CANVAS))
    canvas.alpha_composite(image.convert("RGBA"), (ORIGIN[0] - origin_x, ORIGIN[1] - origin_y))
    return canvas


def insert_atlas(ids):
    insert_atlas_groups({anim: ["/assets/images/pirate/poses/%s_01.png" % anim] for anim in ids})


def insert_atlas_groups(groups):
    """{animation id: [image paths]} inserted before original_bg2; existing ids are kept.
    Frames are played by image name ("x_0"), so each image is also declared as its own
    animation: the engine does not resolve image names inside groups (qa-24..qa-48 drew
    every such sprite as the atlas's first animation; explicit ids fixed it in qa-49)."""
    text = ATLAS.read_text(encoding="utf-8")
    anchor = 'animations {\n  id: "original_bg2"\n'
    block = ""

    def animation(anim, images):
        return ('animations {\n  id: "%s"\n' % anim
                + "".join('  images {\n    image: "%s"\n    sprite_trim_mode: SPRITE_TRIM_MODE_OFF\n  }\n' % image
                          for image in images)
                + '  playback: PLAYBACK_NONE\n  fps: 8\n  flip_horizontal: 0\n  flip_vertical: 0\n}\n')

    for anim, images in groups.items():
        if 'id: "%s"\n' % anim not in text + block:
            block += animation(anim, images)
        for image in images:
            if 'id: "%s"\n' % Path(image).stem not in text + block:
                block += animation(Path(image).stem, [image])
    assert anchor in text
    ATLAS.write_text(text.replace(anchor, block + anchor, 1), encoding="utf-8")


def export():
    rom = items.ROM.read_bytes()
    name_of = items.pose_names(rom)
    palette = load_palette(str(items.SOURCE / "Palettes" / "Sprite_Diddy_Active.bin"))
    poses = existing_poses()
    scripts = {index: script(rom, index) for index in BASE_IDS + EXTRA_IDS}
    added = []
    for data in scripts.values():
        for op in data["code"].values():
            if (op["op"] < 0x80 or op["op"] in (0x8B, 0x89, 0x8A)) and op["arg"] not in poses:
                name = name_of(op["arg"])
                anim = "diddy_pose_%04x" % op["arg"]
                render_pose(rom, name, palette).save(POSES / (anim + "_01.png"))
                poses[op["arg"]] = (anim, name)
                added.append(anim)
    lines = ["-- Original ROM bytecode; not replay animation.", "return { scripts = {"]
    for index, data in scripts.items():
        lines.append("[%d] = { start = %d, flags = %d, code = {" % (index, data["start"], data["flags"]))
        for pc, op in data["code"].items():
            extra = "".join(", %s = %d" % (key, op[key]) for key in ("dur", "dx", "dy", "arg2", "slot") if key in op)
            lines.append("[%d] = { op = %d, arg = %d, next = %d%s }," % (pc, op["op"], op["arg"], op["next"], extra))
        lines.append("} },")
    lines.append("}, poses = {")
    for index, (anim, gfx) in sorted(poses.items()):
        lines.append('[%d] = { animation = "%s", gfx = "%s" },' % (index, anim, gfx))
    lines.append("} }")
    DATA.write_text("\n".join(lines), encoding="utf-8")
    insert_atlas(added)
    return scripts, added


if __name__ == "__main__":
    scripts, added = export()
    print({hex(k): v.get("status") for k, v in scripts.items()})
    print(len(added), "new poses")
