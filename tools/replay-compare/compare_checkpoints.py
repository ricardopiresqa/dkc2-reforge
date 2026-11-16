"""Compare explicit original/port checkpoints at owner-approved 1px/1frame.

Input JSON: {input_sha256, rom_sha256, checkpoints:[{id,frame,x,y,state}]}.
Checkpoints must be captured from the same input sequence; never synthesize
reference data from the port. Missing, duplicate or reordered events fail.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def validate_capture(capture):
    for key in ("input_sha256", "rom_sha256"):
        value = capture.get(key, "")
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("invalid or missing " + key)
    points = capture.get("checkpoints", [])
    if not points:
        raise ValueError("empty checkpoint capture")
    ids = [p.get("id") for p in points]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("missing or duplicate checkpoint IDs")
    last = -1
    for point in points:
        frame = point.get("frame")
        if type(frame) is not int or frame < last or frame < 0:
            raise ValueError("frames must be nonnegative ordered integers")
        last = frame
        for key in ("x", "y"):
            value = point.get(key)
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError("invalid " + key)
        if not isinstance(point.get("state"), str) or not point["state"]:
            raise ValueError("missing semantic state")
    return points


def compare(reference, port):
    original = validate_capture(reference)
    actual = validate_capture(port)
    for key in ("input_sha256", "rom_sha256"):
        if reference[key] != port[key]:
            raise ValueError("capture provenance differs: " + key)
    if reference.get("initial_input", 0) != port.get("initial_input", 0):
        raise ValueError("initial controller context differs")
    if [p["id"] for p in original] != [p["id"] for p in actual]:
        return ["checkpoint sequence differs"]
    failures = []
    for expected, observed in zip(original, actual):
        deltas = {key: abs(expected[key] - observed[key]) for key in ("frame", "x", "y")}
        if any(delta > 1 for delta in deltas.values()) or expected["state"] != observed["state"]:
            failures.append({"id": expected["id"], "deltas": deltas,
                             "state_matches": expected["state"] == observed["state"]})
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("port", type=Path)
    args = parser.parse_args()
    try:
        reference = json.loads(args.reference.read_text(encoding="utf-8"))
        port = json.loads(args.port.read_text(encoding="utf-8"))
        failures = compare(reference, port)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"status": "UNAVAILABLE", "error": str(error)}))
        return 2
    print(json.dumps({"status": "FAIL" if failures else "PASS", "failures": failures,
                      "scope": "supplied checkpoints only; not entire-game fidelity",
                      "reference_sha256": hashlib.sha256(args.reference.read_bytes()).hexdigest(),
                      "port_sha256": hashlib.sha256(args.port.read_bytes()).hexdigest()}))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
