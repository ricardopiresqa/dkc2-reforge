"""Compare actual ROM pose IDs with the port VM snapshots; no fake pass."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def compare(bundle):
    folder = (ROOT / bundle / "dkc2-reforge").resolve()
    folder.relative_to(ROOT / "dist")
    port = json.loads((folder / "port-checkpoints.json").read_text())
    reference = {int(row["active_frame"]): row for row in csv.DictReader(
        (ROOT / "assets-raw/pirate/reference-poses.csv").open(encoding="utf-8"))}
    outcomes = []
    for point in port["checkpoints"]:
        frame = point["frame"]
        expected = reference[frame]
        actual = point.get("original_animation", {})
        same_pose = actual.get("pose") == int(expected["pose_table_offset"])
        same_mode = actual.get("id") == int(expected["animation_id"])
        outcomes.append({"frame": frame, "expected_pose": int(expected["pose_table_offset"]),
                         "expected_animation": int(expected["animation_id"]), "actual": actual,
                         "status": "PASS" if same_pose and same_mode else "FAIL"})
    report = {"scope": "sampled pose/mode equality, not full rendered fidelity",
              "status": "PASS" if all(o["status"] == "PASS" for o in outcomes) else "FAIL", "checkpoints": outcomes}
    (folder / "pose-comparison.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(compare(Path(sys.argv[1])))
