"""Summarize one opt-in walk trace without treating all contacts as defects."""
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
bundle = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dist/pirate-panic-walk-collision-qa")
path = ROOT / bundle / "dkc2-reforge/qa-runtime.json"
data = json.loads(path.read_text(encoding="utf-8"))
events = data.get("collision_events") or []
neek_samples = data.get("neek_interaction_samples") or []
counts = collections.Counter(event["kind"] for event in events)
legacy = [event for event in events if event["kind"].startswith("legacy_grid_")]
groups = {}
for event in events:
    if not event["kind"].startswith("source_"):
        continue
    key = (event["kind"], event["col"], event["row"], event["source_value"], event.get("surface_y"))
    item = groups.setdefault(key, {"kind": event["kind"], "col": event["col"],
        "row": event["row"], "source_value": event["source_value"],
        "surface_y": event.get("surface_y"), "count": 0, "first_frame": event["frame"],
        "last_frame": event["frame"], "min_player_x": event["x"], "max_player_x": event["x"]})
    item["count"] += 1
    item["last_frame"] = event["frame"]
    item["min_player_x"] = min(item["min_player_x"], event["x"])
    item["max_player_x"] = max(item["max_player_x"], event["x"])
summary = {
    "walk_collision_qa": data.get("collision_walk_qa"),
    "frames": data.get("frames"),
    "events": len(events),
    "counts_by_kind": dict(counts),
    "legacy_fallback_events": len(legacy),
    "legacy_fallback_first20": legacy[:20],
    "neek_hit_frames": [sample["frame"] for sample in neek_samples if sample.get("neek_hit")],
    "neek_interaction_samples": neek_samples,
    "unique_source_contact_sites": list(groups.values()),
    "source_contacts_first20": [e for e in events if e["kind"].startswith("source_")][:20],
    "scope": "contacts observed during one scripted walking run; a legacy fallback is a review candidate, not automatically an invisible collision",
}
output = path.with_name("collision-walk-summary.json")
output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
