import csv
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "assets-raw/pirate"
TRACE = STAGE / "reference-sprites-trace.csv"
local_capture = pytest.mark.skipif(
    not TRACE.is_file() or not (ROOT / "data/original/pirate/items.lua").is_file()
    or not (STAGE / "items-report.json").is_file(),
    reason="capturas e dados derivados da ROM são locais e não distribuídos")
FROZEN = {567, 568, 939, 940}  # sprites hold with the actor during the stomp hit-stops
SPRITES = {0x1A8: ("DKBarrel_Barrel", 1056), 0x11C: ("DKBarrel_Letters", 1056), 0x1BC: ("WoodenBox", 1352),
           0x170: ("BananaBunch", 1504)}


def rows(name):
    with (STAGE / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


def exporter():
    spec = importlib.util.spec_from_file_location("export_items", ROOT / "tools/replay-compare/export_items.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replay():
    """Yield (frame, [(sprite, left, top)]) for main/original_items.lua over the reference camera."""
    lupa = pytest.importorskip("lupa.luajit21")
    lua = lupa.LuaRuntime()
    lua.execute("jit.off()")
    for module in ("items", "pirate_panic_level"):
        lua.execute('package.preload["data.original.pirate.%s"] = function() return dofile([[%s]]) end'
                    % (module, ROOT / ("data/original/pirate/%s.lua" % module)))
    items = lua.eval("dofile([[%s]])" % (ROOT / "main/original_items.lua"))
    items.init(True)
    collect = lua.eval("function(m) local out = {} m.each_visible(function(s, l, t) out[#out + 1] = {s, l, t} end) return out end")
    camera = rows("reference-camera.csv")
    for frame in range(1, len(camera)):
        items.update(int(camera[frame - 1]["camera_x_raw"]) - 256, int(camera[frame - 1]["camera_y_raw"]) - 256,
                     frame in FROZEN)
        yield frame, [(entry[1], entry[2], entry[3]) for entry in collect(items).values()]


@local_capture
def test_item_spawn_pose_and_despawn_match_sprite_trace():
    module = exporter()
    name_of = module.pose_names(module.ROM.read_bytes())
    report = json.loads((STAGE / "items-report.json").read_text())
    pose_of = {frame["sprite"]: frame["pose"] for frames in report["animations"].values() for frame in frames}
    truth = {}
    for row in rows("reference-sprites-trace.csv"):
        sprite = SPRITES.get(int(row["sprite_id"]))
        if sprite:
            truth[(int(row["active_frame"]), sprite[0])] = name_of(int(row["pose"]))
    checked = 0
    for frame, visible in replay():
        shown = {}
        for sprite, left, _ in visible:
            pose = pose_of[sprite]
            for kind, x in SPRITES.values():
                if kind in pose and abs(left + 1 + 256 - x) < 40:
                    shown[kind] = pose
        for kind, _ in SPRITES.values():
            expected, got = truth.get((frame, kind)), shown.get(kind)
            if expected or got:
                checked += 1
                assert got == expected, (frame, kind, got, expected)
    assert checked > 500


@local_capture
def test_only_items_the_game_creates_spawn_along_the_route():
    kinds = set()
    for _, visible in replay():
        kinds.update(sprite.rsplit("_", 1)[0] for sprite, _, _ in visible)
    # DK barrel (anim $2E1, emblem $2BF), wooden box ($2E6) and the banana bunch ($2B2, sprite $170
    # from frame 962); script-10 Kremkoins and the rigging banana coin never spawn in
    # reference-sprites-trace.csv.
    assert kinds == {"original_item_2e1", "original_item_2bf", "original_item_2e6", "original_item_2b2"}


@local_capture
def test_item_pixels_match_new_original_screens():
    """Barrel, emblem and box as drawn by the module vs items-frame-*.ppm (lag 0-10)."""
    np = pytest.importorskip("numpy")
    from PIL import Image

    frames = {600, 800, 900, 950, 1000}
    if not all((STAGE / ("items-frame-%04d.ppm" % frame)).is_file() for frame in frames):
        pytest.skip("captura reference_items_frames_capture.lua ausente")
    history = {frame: visible for frame, visible in replay()}
    for frame in sorted(frames):
        screen = np.asarray(Image.open(STAGE / ("items-frame-%04d.ppm" % frame)).convert("RGB"))[7:231].astype(int)
        camera = rows("reference-camera.csv")
        best = 0.0
        for lag in range(0, 11):
            past = frame - lag
            cam_x, cam_y = int(camera[past]["camera_x_raw"]) - 256, int(camera[past]["camera_y_raw"]) - 256
            canvas = Image.new("RGBA", (256, 224))
            for sprite, left, top in history[past]:
                image = Image.open(ROOT / ("assets/images/pirate/items/%s.png" % sprite)).convert("RGBA")
                canvas.alpha_composite(image, (int(left - cam_x), int(top - cam_y)))
            drawn = np.asarray(canvas).astype(int)
            mask = drawn[:, :, 3] > 0
            if mask.sum():
                close = np.abs(drawn[:, :, :3] - screen).max(axis=2) <= 8
                best = max(best, float(close[mask].mean()))
        assert best == 1.0, (frame, best)
