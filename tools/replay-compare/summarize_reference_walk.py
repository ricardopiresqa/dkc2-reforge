"""Summarize original same-ROM walking trace and visited source coordinates."""
import csv
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
stage = root / "assets-raw/pirate"
csv_path = next((stage / name for name in (
    "reference-walk-collision-qa-v5.csv", "reference-walk-collision-qa-v4.csv",
    "reference-walk-collision-qa-v3.csv", "reference-walk-collision-qa.csv")
    if (stage / name).exists()))
rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
for row in rows:
    for key in row:
        row[key] = int(row[key])
summary = {"rows": len(rows), "max_x_raw": max(row["x_raw"] for row in rows),
           "min_x_raw": min(row["x_raw"] for row in rows),
           "levels": sorted({row["level"] for row in rows}),
           "modes": sorted({row["mode"] for row in rows}),
           "samples": [row for row in rows if row["frame"] in (0,100,500,1000,1500,2000,3000,5000,8000,9999)],
           "new_wall_points": []}
last_x, last_vx = None, None
for row in rows:
    if last_x is not None and row["x_raw"] != last_x and row["x_raw"] < last_x:
        summary["new_wall_points"].append({"frame": row["frame"], "x_raw": row["x_raw"],
                                           "vx_raw": row["vx_raw"], "y_raw": row["y_raw"]})
    last_x, last_vx = row["x_raw"], row["vx_raw"]
(stage / "reference-walk-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
