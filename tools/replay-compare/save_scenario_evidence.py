"""Keep separate QA scenario evidence before running another case in same bundle."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def save(bundle, scenario):
    assert scenario in ("movement", "idle"), "unknown QA scenario"
    folder = (ROOT / bundle / "dkc2-reforge").resolve()
    folder.relative_to(ROOT / "dist")
    outputs = []
    for filename in ("qa-runtime.json", "log.txt"):
        source = folder / filename
        assert source.is_file()
        target = folder / (scenario + "-" + filename)
        assert not target.exists(), "scenario evidence already exists; do not overwrite"
        contents = source.read_bytes()
        target.write_bytes(contents)
        outputs.append({"file": target.name, "sha256": hashlib.sha256(contents).hexdigest()})
    print(json.dumps({"scenario": scenario, "scope": "observed reports only", "files": outputs}))


if __name__ == "__main__":
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("bundle", type=Path)
    args.add_argument("scenario", choices=("movement", "idle"))
    options = args.parse_args()
    save(options.bundle, options.scenario)
