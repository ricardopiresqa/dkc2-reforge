"""Summarize route-bot-trace.csv into gameplay events (QA evidence only).

Rows: `P,frame,mode,level,x,y,state,animation,lives,camera_x` for the active player and
`S,frame,slot,id,x,y,pose,animation,attributes,state` per live sprite slot.
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import import_pirate_panic as importer  # noqa: E402

TRACE = ROOT / "assets-raw/pirate/route-bot-trace.csv"


def load():
    players, sprites = {}, defaultdict(list)
    with TRACE.open(newline="") as handle:
        for row in csv.DictReader(handle):
            frame = int(row["active_frame"])
            if row["kind"] == "P":
                players[frame] = {"mode": int(row["a"]), "level": int(row["b"]), "x": int(row["c"]),
                                  "y": int(row["d"]), "state": int(row["e"]), "animation": int(row["f"]),
                                  "lives": int(row["g"]), "camera_x": int(row["h"])}
            else:
                sprites[frame].append({"slot": int(row["a"]), "id": int(row["b"]), "x": int(row["c"]),
                                       "y": int(row["d"]), "pose": int(row["e"]), "animation": int(row["f"]),
                                       "attributes": int(row["g"]), "state": int(row["h"])})
    return players, sprites


def summarize():
    names = importer.load_sprite_id_names(str(ROOT / "tools/vendor/DKC2-disasm/DKC2/Misc_Defines_DKC2.asm"))
    name = lambda sprite_id: names.get(sprite_id, "0x%X" % sprite_id)
    players, sprites = load()
    events = []
    previous = None
    for frame in sorted(players):
        player = players[frame]
        if previous and player["lives"] != previous["lives"]:
            events.append({"frame": frame, "event": "lives", "from": previous["lives"], "to": player["lives"]})
        if previous and player["state"] != previous["state"]:
            events.append({"frame": frame, "event": "state", "from": previous["state"], "to": player["state"],
                           "animation": player["animation"], "x": player["x"], "y": player["y"]})
        previous = player
    alive = {}
    for frame in sorted(sprites):
        current = {(s["slot"], s["id"]): s for s in sprites[frame]}
        for key, sprite in current.items():
            if key not in alive:
                events.append({"frame": frame, "event": "spawn", "sprite": name(sprite["id"]),
                               "x": sprite["x"], "y": sprite["y"], "animation": sprite["animation"]})
        for key, sprite in alive.items():
            if key not in current:
                events.append({"frame": frame, "event": "despawn", "sprite": name(sprite["id"]),
                               "x": sprite["x"], "y": sprite["y"]})
        alive = current
    events.sort(key=lambda event: event["frame"])
    return events


if __name__ == "__main__":
    for item in summarize():
        if len(sys.argv) < 2 or any(word in json.dumps(item) for word in sys.argv[1:]):
            print(json.dumps(item))
