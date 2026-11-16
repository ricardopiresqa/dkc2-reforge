"""Export the second sprite of Diddy's level-end dance: the boombox.

The victory script ($45, B9 bytecode) plays $89 frames: dur, the Kong's pose and a second
pose drawn with it (Diddy's radio). export_diddy_moves exports only the first pose; this
renders every second pose of $45/$46 with Diddy's palette onto the same canvas, inserts
each one into the atlas (export_diddy_moves.insert_atlas, never write_atlas) and appends
the pose entries to data/original/pirate/animation_scripts.lua.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import export_diddy_moves as moves  # noqa: E402
import export_items as items  # noqa: E402
from gfx_convert import load_palette  # noqa: E402

VICTORY_IDS = (0x45, 0x46)


def second_poses(text):
    """arg2 of every $89 (137) frame in the exported victory scripts."""
    found = set()
    for index in VICTORY_IDS:
        block = re.search(r"^\[%d\] = \{ start.*?^\} \},$" % index, text, re.M | re.S)
        if block:
            found |= {int(m) for m in re.findall(r"op = 137, .*?arg2 = (\d+)", block.group(0))}
    return found


def export():
    rom = items.ROM.read_bytes()
    name_of = items.pose_names(rom)
    palette = load_palette(str(items.SOURCE / "Palettes" / "Sprite_Diddy_Active.bin"))
    text = moves.DATA.read_text(encoding="utf-8")
    existing = moves.existing_poses()
    added, lines = [], []
    for pose in sorted(second_poses(text) - set(existing)):
        anim, gfx = "diddy_pose_%04x" % pose, name_of(pose)
        moves.render_pose(rom, gfx, palette).save(moves.POSES / (anim + "_01.png"))
        added.append(anim)
        lines.append('[%d] = { animation = "%s", gfx = "%s" },' % (pose, anim, gfx))
    if lines:
        head, tail = text.rsplit("} }", 1)
        moves.DATA.write_text(head + "\n".join(lines) + "\n} }" + tail, encoding="utf-8")
        moves.insert_atlas(added)
    return added


if __name__ == "__main__":
    print(export())
