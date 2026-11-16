"""Compare sampled camera offsets in matching ORIGINAL clock context.

Reject unaligned clock context instead of choosing an attractive camera phase.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def compare(bundle):
    folder = (ROOT / bundle / "dkc2-reforge").resolve()
    folder.relative_to(ROOT / "dist")
    port = json.loads((folder / "port-checkpoints.json").read_text())
    reference = {int(r["active_frame"]): r for r in csv.DictReader(
        (ROOT / "assets-raw/pirate/reference-camera.csv").open())}
    poses = list(csv.DictReader((ROOT / "assets-raw/pirate/reference-poses.csv").open()))
    start_clock = int(poses[0]["game_counter"])
    results = []
    for point in port["checkpoints"]:
        frame = point["frame"]
        camera = point.get("camera")
        if not camera or camera["context"]["clock"] != (start_clock + frame) % 65536:
            raise ValueError("original clock context is missing/different at frame %d" % frame)
        expected = reference[frame]
        dx = abs(camera["x"] - (int(expected["camera_x_raw"]) - 256))
        dy = abs(camera["y"] - (int(expected["camera_y_raw"]) - 256))
        results.append({"frame": frame, "dx": dx, "dy": dy, "actual": camera,
                        "source": {"camera_x_raw": int(expected["camera_x_raw"]),
                                   "camera_y_raw": int(expected["camera_y_raw"]),
                                   "camera_kernel": next((r for r in csv.DictReader(
                                       (ROOT / "assets-raw/pirate/reference-camera-kernel.csv").open())
                                       if int(r["active_frame"]) == frame), None)},
                        "expected": [int(expected["camera_x_raw"]) - 256, int(expected["camera_y_raw"]) - 256],
                        "status": "PASS" if max(dx, dy) <= 1 else "FAIL"})
    report = {"scope": "initial camera offsets only; no background HDMA/color math approval",
              "status": "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL", "checkpoints": results}
    (folder / "camera-comparison.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(compare(Path(sys.argv[1])))
