"""Find closest original recorded state to a collision QA coordinate."""
import csv
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
path = root / "assets-raw/pirate/reference-walk-collision-qa-v5.csv"
target = int(sys.argv[1]) if len(sys.argv) > 1 else 1318
rows = list(csv.DictReader(path.open(encoding="utf-8")))
selected = min(rows, key=lambda row: abs(int(row["x_raw"]) - target))
print({key: int(value) for key, value in selected.items()})
