"""Summarize bounded route QA; does not claim original route fidelity."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
bundle = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dist/pirate-panic-route-qa")
path = root / bundle / "dkc2-reforge/qa-runtime.json"
data = json.loads(path.read_text(encoding="utf-8"))
samples = data.get("samples", [])
print(json.dumps({"version": data.get("qa_version"), "frames": data.get("frames"),
                  "route_qa": data.get("route_qa"), "level_complete": data.get("level_complete"),
                  "input_check": data.get("input_check"),
                  "min_health": min((s["health"] for s in samples), default=None),
                  "max_x": max((s["x"] for s in samples), default=None),
                  "last_sample": samples[-1] if samples else None,
                  "scope": "mixed reference-opening + synthetic run/jump tail; functional completion only"},
                 indent=2))
