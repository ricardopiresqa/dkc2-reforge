import copy
import importlib.util
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[1] / "replay-compare/compare_checkpoints.py"
spec = importlib.util.spec_from_file_location("compare_checkpoints", path)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def capture():
    return {"input_sha256": "a" * 64, "rom_sha256": "b" * 64,
            "checkpoints": [{"id": "jump_apex", "frame": 80, "x": 110,
                             "y": 65, "state": "fall"}]}


def test_owner_tolerance_inclusive():
    reference = capture()
    actual = copy.deepcopy(reference)
    actual["checkpoints"][0].update(frame=81, x=111, y=64)
    assert module.compare(reference, actual) == []
    actual["checkpoints"][0]["x"] = 112
    assert module.compare(reference, actual)


def test_semantic_event_cannot_be_hidden_by_frame_tolerance():
    actual = capture()
    actual["checkpoints"][0]["state"] = "death"
    assert module.compare(capture(), actual)


@pytest.mark.parametrize("bad", [{}, {"checkpoints": []},
                                  {"input_sha256": "c" * 64}])
def test_missing_or_conflicting_evidence_never_passes(bad):
    actual = capture()
    actual.update(bad)
    if not bad:
        actual = {}
    with pytest.raises(ValueError):
        module.compare(capture(), actual)


def test_duplicate_nan_and_reordered_frames_rejected():
    actual = capture()
    actual["checkpoints"].append(copy.deepcopy(actual["checkpoints"][0]))
    with pytest.raises(ValueError):
        module.compare(capture(), actual)
    actual = capture()
    actual["checkpoints"][0]["y"] = float("nan")
    with pytest.raises(ValueError):
        module.compare(capture(), actual)
