"""Summarize original camera direct-page state around initial region/jump."""
import csv
from pathlib import Path

path = Path(__file__).resolve().parents[2] / "assets-raw/pirate/reference-camera-aux.csv"
frames = {0, 40, 60, 100, 138, 139, 140, 141, 153, 158, 165, 173, 180}
with path.open(encoding="utf-8") as file:
    for row in csv.DictReader(file):
        if int(row["active_frame"]) in frames:
            print(row["active_frame"], *("%s=%s" % (key, row[key]) for key in (
                "abe","ac0","ac2","ac4","ac6","ac8","aca","acc","ad0","ad2","ad4",
                "ad6","ad8","ada","adc","ade","ae0","ae2","ae4","ae6","ae8","aea",
                "aec","aee","af0","af2","af4","d4e","d50")))
