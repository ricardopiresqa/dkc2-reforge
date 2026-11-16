"""Show the original camera controller branch operands without word misalignment."""
import csv
from pathlib import Path

path = Path(__file__).resolve().parents[2] / "assets-raw/pirate/reference-camera-dp-bytes.csv"
for row in csv.DictReader(path.open(encoding="utf-8")):
    if int(row["active_frame"]) in {0,100,138,139,140,141,153,158,165,173,180}:
        print(row["active_frame"], *("%s=%s" % (key, row[key]) for key in
              ("9F","A7","BA","BE","BF","C0","C2","C3","C4","C6","C8","C9","CA","CC","CD","CE","D0","D2","D4","D6","D8","DA","DC","DE","E0","E2","E4","E6","EA","EC","EE","F0","F2","F4","F6","F8","FA")))
