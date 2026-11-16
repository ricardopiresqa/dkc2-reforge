"""Print only selected measured spring terms from original-camera capture."""
import csv
import sys
from pathlib import Path

path = Path(__file__).resolve().parents[2] / "assets-raw/pirate/reference-camera-kernel.csv"
wanted = {0, 1, 100, 138, 139, 140, 141, 142, 143, 151, 153, 158, 165, 173, 180}
with path.open(encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        frame = int(row["active_frame"])
        if frame in wanted:
            print(frame, *("%s=%s" % (key, row[key]) for key in
                ("y_velocity_lo", "y_position_lo", "y_position_hi", "y_target_lo", "y_target_hi",
                 "y_prev_target_lo", "y_prev_target_hi", "y_focus_lo", "y_focus_hi", "y_active_cap",
                 "region_index", "viewport_x", "viewport_y", "x_low", "y_low", "aux_x", "aux_y",
                 "old_target_x_lo", "old_target_x_hi", "old_position_x_lo", "old_position_x_hi",
                 "new_target_x_lo", "new_target_x_hi", "camera_velocity_x_lo", "camera_velocity_x_hi",
                 "accel_cap", "x_shift", "y_shift")))
