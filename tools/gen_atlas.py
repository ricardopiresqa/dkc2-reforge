"""Gera main/game.atlas a partir de assets/images/gen/.

Agrupa arquivos <base>_<n>.png numa animacao chamada <base>; arquivos sem
sufixo numerico viram animacao de 1 frame com o proprio nome. Rodar da raiz:

    python tools/gen_atlas.py
"""

import os
import re
from collections import defaultdict

SRC = os.path.join("assets", "images", "gen")
OUT = os.path.join("main", "game.atlas")

# fps por animacao (default 8). Chave = id da animacao.
FPS = {
    "player_idle": 3,
    "player_run": 12,
    "player_roll": 16,
    "player_swim": 6,
    "player_climb": 8,
    "en_kritter": 5,
    "en_zinger": 12,
    "en_flitter": 14,
}

FRAME_RE = re.compile(r"^(?P<base>.+)_(?P<idx>\d+)$")


def collect():
    groups = defaultdict(list)
    for root, _dirs, files in os.walk(SRC):
        for f in sorted(files):
            if not f.endswith(".png"):
                continue
            stem = f[:-4]
            path = "/" + os.path.join(root, f).replace(os.sep, "/")
            m = FRAME_RE.match(stem)
            if m:
                groups[m.group("base")].append((int(m.group("idx")), path))
            else:
                groups[stem].append((0, path))
    return groups


def main():
    groups = collect()
    out = []
    for anim_id in sorted(groups):
        frames = [p for _i, p in sorted(groups[anim_id])]
        loop = len(frames) > 1
        out.append("animations {")
        out.append('  id: "%s"' % anim_id)
        for path in frames:
            out.append("  images {")
            out.append('    image: "%s"' % path)
            out.append("    sprite_trim_mode: SPRITE_TRIM_MODE_OFF")
            out.append("  }")
        out.append("  playback: %s" % ("PLAYBACK_LOOP_FORWARD" if loop else "PLAYBACK_NONE"))
        out.append("  fps: %d" % FPS.get(anim_id, 8))
        out.append("  flip_horizontal: 0")
        out.append("  flip_vertical: 0")
        out.append("}")
    out.append("margin: 0")
    out.append("extrude_borders: 2")
    out.append("inner_padding: 0")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")

    total = sum(len(v) for v in groups.values())
    print("wrote %s (%d animations, %d frames)" % (OUT, len(groups), total))


if __name__ == "__main__":
    main()
