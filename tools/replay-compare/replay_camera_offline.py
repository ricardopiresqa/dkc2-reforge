"""Replay main/original_camera.lua against the ORIGINAL camera, frame by frame.

Inputs come from the same capture as the expected output: actor words $0ABE/$0AC2
(subpixel), facing bit 14 of actor $0012, floor distance actor $000E and $002A.
Hit-stop ($0A36 bit $80) is inferred from the stomp-bounce state entry.
This tests the camera port only; it is not evidence about player motion.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "assets-raw/pirate"
TOLERANCE = 1  # owner-approved 1px per axis
BOUNCE_STATE, HITSTOP_FRAMES = "22", 2  # stomp bounce; runtime player.bounce(..., 2)


def rows(name):
    with (RAW / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


def inputs(kernel, pose):
    actor_x = int(kernel["region_boundary_xlow"]) + 65536 * int(kernel["region_boundary_xhigh"])
    actor_y = int(kernel["y_focus_lo"]) + 65536 * int(kernel["y_focus_hi"])
    floor = int(pose["meta_y"])
    return (actor_x / 256 - 256, actor_y / 256 - 256,
            bool(int(pose["flags"]) & 0x4000), None if floor & 0x8000 else floor)


def hitstop_frames(gameplay):
    """$0A36 bit $80 is not captured: derive it from the stomp-bounce state entry."""
    frozen = set()
    for frame in range(1, len(gameplay)):
        if gameplay[frame]["state_raw"] == BOUNCE_STATE != gameplay[frame - 1]["state_raw"]:
            frozen.update(range(frame, frame + HITSTOP_FRAMES))
    return frozen


def load_runtime():
    import lupa.luajit21 as lupa  # Defold runs LuaJIT

    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    # Interpreter only: JIT trace aborts raise SEH exceptions on Windows x64 that
    # pytest's faulthandler reports as fatal. Semantics are identical without the JIT.
    lua.execute("jit.off()")
    profile = ROOT / "data/original/pirate/camera_profile.lua"
    lua.execute('package.preload["data.original.pirate.camera_profile"] = '
                'function() return dofile([[%s]]) end' % profile)
    return lua, lua.eval("dofile([[%s]])" % (ROOT / "main/original_camera.lua"))


def load_camera():
    return load_runtime()[1]


def replay(hitstop=True):
    kernel, poses, camera = rows("reference-camera-kernel.csv"), rows("reference-poses.csv"), rows("reference-camera.csv")
    frozen = hitstop_frames(rows("reference-gameplay.csv")) if hitstop else set()
    port = load_camera()
    port.init(int(poses[0]["game_counter"]), *inputs(kernel[0], poses[0]))
    results = []
    for frame in range(1, len(kernel)):
        x, y = port.update(*inputs(kernel[frame], poses[frame]), frame in frozen)
        expected = (int(camera[frame]["camera_x_raw"]) - 256, int(camera[frame]["camera_y_raw"]) - 256)
        results.append({"frame": frame, "actual": [x, y], "expected": list(expected),
                        "dx": x - expected[0], "dy": y - expected[1]})
    failures = [r for r in results if max(abs(r["dx"]), abs(r["dy"])) > TOLERANCE]
    return {"scope": "camera port replay with original actor inputs; no HDMA/composition approval",
            "frames": len(results), "tolerance_px": TOLERANCE, "hitstop_frames": sorted(frozen),
            "exact_frames": sum(1 for r in results if r["dx"] == 0 and r["dy"] == 0),
            "failures": failures, "status": "PASS" if not failures else "FAIL"}


if __name__ == "__main__":
    report = replay()
    print(json.dumps({k: v for k, v in report.items() if k != "failures"}, indent=2))
    for failure in report["failures"]:
        print(failure)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(json.dumps(report, indent=2))
    raise SystemExit(0 if report["status"] == "PASS" else 1)
