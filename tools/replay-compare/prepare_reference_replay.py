"""Prepare private replay inputs and original checkpoints from observed RAM."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "assets-raw/pirate"
SNES_BITS = (0x8000, 0x4000, 0x2000, 0x1000, 0x0800, 0x0400,
             0x0200, 0x0100, 0x0080, 0x0040, 0x0020, 0x0010)
CHECKPOINTS = (0, 40, 60, 100, 140, 153, 158, 165, 173, 180)


def prepare():
    rows = list(csv.DictReader((STAGE / "reference-gameplay.csv").open(encoding="utf-8")))
    report = json.loads((STAGE / "reference-snapshot-report.json").read_text(encoding="utf-8"))
    assert report["rom_sha256"] == "35421a9af9dd011b40b91f792192af9f99c93201d8d394026bdfb42cbf2d8633"
    assert len(rows) > max(CHECKPOINTS)
    masks = []
    for index, row in enumerate(rows):
        assert int(row["active_frame"]) == index
        raw = int(row["hold_raw"])
        masks.append(sum(1 << bit for bit, flag in enumerate(SNES_BITS) if raw & flag))
    # Row 0 is the INITIAL observed state, not a transition to apply again.
    # inputs[0] advances state 0 -> state 1, keeping sampled frames aligned.
    initial_input = masks.pop(0)
    digest = hashlib.sha256(json.dumps(masks, separators=(",", ":")).encode()).hexdigest()
    points = []
    for frame in CHECKPOINTS:
        row = rows[frame]
        state = int(row["state_raw"])
        assert state in (0, 1, 6), "unsupported original state in focused motion gate"
        group = "ground_walk" if frame <= 140 else "short_jump"
        points.append({"id": "%s_%d" % (group, frame), "frame": frame,
                       "x": int(row["x_raw"]) - 256, "y": int(row["y_raw"]) - 256,
                       "state": "air" if state == 6 else "ground"})
    capture = {"rom_sha256": report["rom_sha256"], "input_sha256": digest,
               "initial_input": initial_input,
               "checkpoints": points, "scope": "original initial walking and first short-jump checkpoints only",
               "trace_sha256": hashlib.sha256((STAGE / "reference-gameplay.csv").read_bytes()).hexdigest()}
    (STAGE / "reference-checkpoints.json").write_text(json.dumps(capture, indent=2), encoding="utf-8")
    ground = dict(capture)
    ground["checkpoints"] = [p for p in points if p["frame"] <= 140]
    ground["scope"] = "original ground walking only"
    ground_text = json.dumps(ground, indent=2)
    (STAGE / "reference-ground-walk.json").write_text(ground_text, encoding="utf-8")
    lua = 'return { input_sha256 = "%s", rom_sha256 = "%s", initial_input = %d, inputs = {%s} }\n' % (
        digest, report["rom_sha256"], initial_input, ",".join(map(str, masks)))
    (STAGE / "reference_inputs.lua").write_text(lua, encoding="utf-8")
    runtime_dir = ROOT / "data/original/pirate"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "reference_inputs.lua").write_text(lua, encoding="utf-8")
    print("prepared %d observed input frames; %d original motion checkpoints" % (len(masks), len(points)))
    print("ground_reference_sha256=" + hashlib.sha256((STAGE / "reference-ground-walk.json").read_bytes()).hexdigest())


if __name__ == "__main__":
    prepare()
