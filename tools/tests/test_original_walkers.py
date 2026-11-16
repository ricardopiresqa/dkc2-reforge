"""main/original_walkers.lua vs the original walker structs (route-bot-walkers.csv).

The capture (tools/replay-compare/route_bot_walkers_capture.lua) holds the full $5E-byte
sprite struct of every live Neek/Klomp per frame. Inputs taken from the trace, not
derived: the camera x (route-bot-trace.csv), the hit-stop frames (every walker struct
unchanged) and the stomp frames with the player's facing (contact detection is not
part of this module).
"""
import csv
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "assets-raw/pirate"
WALKERS = STAGE / "route-bot-walkers.csv"
local_capture = pytest.mark.skipif(
    not WALKERS.is_file() or not (ROOT / "data/original/pirate/walkers.lua").is_file(),
    reason="capturas e dados derivados da ROM são locais e não distribuídos")
SPECIES = {0x1E4: "Neek", 0x1EC: "Klomp"}


def word(raw, offset):
    return raw[offset] | raw[offset + 1] << 8


def load_trace():
    frames = defaultdict(list)
    with WALKERS.open(newline="") as handle:
        for row in csv.DictReader(handle):
            frames[int(row["active_frame"])].append((int(row["slot"]), bytes.fromhex(row["struct_hex"])))
    camera = {}
    with (STAGE / "route-bot-trace.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["kind"] == "P":
                camera[int(row["active_frame"])] = int(row["h"]) - 256
    return frames, camera


def same(before, after):
    return before is not None and before[:0x18] == after[:0x18] and before[0x1A:] == after[0x1A:]


def inputs(frames):
    frozen, stomps = set(), {}
    for frame in sorted(frames):
        previous = dict(frames.get(frame - 1, []))
        now = dict(frames[frame])
        # $0A36 (hit-stop, partner release) is not captured: a frame where any live walker
        # struct is unchanged is a freeze frame for all walkers.
        # ($18, the displayed pose, may still change while frozen.)
        if any(same(previous.get(slot), raw) for slot, raw in now.items()):
            frozen.add(frame)
        for slot, raw in now.items():
            before = previous.get(slot)
            if before and word(raw, 0x2E) == 1 and word(before, 0x2E) == 0 and word(raw, 0) == word(before, 0):
                stomps[frame] = (word(raw, 6) - 256, word(raw, 0x20) == 0x100)  # vx +$100: player faced left
    return frozen, stomps


def runtime():
    lupa = pytest.importorskip("lupa.luajit21")
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    lua.execute("jit.off()")
    for module in ("walkers", "pirate_panic_level"):
        lua.execute('package.preload["data.original.pirate.%s"] = function() return dofile([[%s]]) end'
                    % (module, ROOT / ("data/original/pirate/%s.lua" % module)))
    collision = lua.eval("dofile([[%s]])" % (ROOT / "main/collision.lua"))
    level = lua.eval("dofile([[%s]])" % (ROOT / "data/levels/level_1_1.lua"))
    collision.load_original_surfaces(level.flat_surfaces)
    walkers = lua.eval("dofile([[%s]])" % (ROOT / "main/original_walkers.lua"))
    walkers.init(True, collision.surface_at, collision.steep_tile)
    return lua, walkers, (collision.surface_at, collision.steep_tile)


def replay(last=3200):
    frames, camera = load_trace()
    frozen, stomps = inputs(frames)
    lua, walkers, surface_at = runtime()
    state = lua.eval("function(m) local out = {} for i, w in ipairs(m.walkers()) do if w.alive then "
                     "out[#out + 1] = {i, w.spawn.species, w.x, w.y, w.vx, w.pose, w.defeated} end end return out end")
    for frame in range(1, last + 1):
        if frame in stomps:
            x, facing_left = stomps[frame]
            for walker in walkers.walkers().values():
                if walker.alive and abs((walker.x >> 8) - 256 - x) <= 2:
                    walkers.defeat(walker, facing_left)
        if camera[frame - 1] < 0:  # death: the level restarts
            walkers.init(True, *surface_at)
        else:
            walkers.update(camera[frame - 1], frame in frozen, frame)
        yield frame, [tuple(entry.values()) for entry in state(walkers).values()], frames.get(frame, [])


@local_capture
def test_walker_struct_fields_match_original_frame_by_frame():
    checked, wrong = defaultdict(int), defaultdict(list)
    for frame, simulated, truth in replay():
        for _slot, raw in truth:
            species = SPECIES[word(raw, 0)]
            x = word(raw, 6) << 8 | raw[5]
            match = [s for s in simulated if s[1] == species and abs((s[2] >> 8) - (x >> 8)) <= 8]
            if not match:
                wrong[species].append((frame, "missing", hex(x)))
                continue
            got = min(match, key=lambda s: abs(s[2] - x))
            checked[species] += 1
            expected = (x, word(raw, 10), word(raw, 0x20), word(raw, 0x1A))
            actual = (got[2], got[3] >> 8, got[4] & 0xFFFF, got[5])
            if actual != expected:
                wrong[species].append((frame, [hex(v) for v in actual], [hex(v) for v in expected]))
    report = {k: (checked[k], len(wrong[k]), wrong[k][:5]) for k in SPECIES.values()}
    print(report)
    assert all(checked[k] > 300 for k in SPECIES.values()), report
    assert all(not wrong[k] for k in SPECIES.values()), report


@local_capture
def test_contact_decision_matches_original_handlers():
    """M.decide on the boxes the game built (route-bot-contact2.csv): a stomp exactly where
    the original ran player action $1B (BEC4EF), otherwise the ground handler BEC01F."""
    path = STAGE / "route-bot-contact2.csv"
    if not path.is_file():
        pytest.skip("captura route_bot_contact2_capture.lua ausente")
    _, walkers, _ = runtime()
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    stomps = {(r["active_frame"], r["slot"]) for r in rows if r["kind"] == "A" and r["player_state"] == "27"}
    ground = {(r["active_frame"], r["slot"]) for r in rows if r["kind"] == "H0"}
    checked = 0
    for row in rows:
        if row["kind"] != "O":
            continue
        boxes = [int(v, 16) for v in row["boxes"].split()]
        outer, enemy = boxes[8:12], boxes[24:28]
        vy = int(row["player_vy"])
        airborne = (int(row["player_41"]) >> 5) == 1
        kind = walkers.decide(*outer, *enemy, airborne, vy - 0x10000 if vy & 0x8000 else vy)
        key = (row["active_frame"], row["slot"])
        assert (kind == "stomp") == (key in stomps), (key, kind)
        assert (kind == "hurt") == (key in ground), (key, kind)
        checked += 1
    assert checked == 35 and len(stomps) == 4
