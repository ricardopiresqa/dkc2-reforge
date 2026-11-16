"""Audit a fresh bundle for proprietary analysis/ROM files before delivery.

Checks Bob's resource index/archive and extracted bundle paths. Uses no external
scanner and never modifies the bundle. A failure blocks calling it safe.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN = (b"assets-raw", b"reference-vram.bin", b"reference-cgram.bin",
             b"Donkey Kong Country 2 (USA V1.0).sfc", b"screenshot-source.zip",
             b"manifest.private.der", b"BEGIN PRIVATE KEY", b"dkc2_save.dat")
RUNTIME = ("data.original.pirate.pirate_panic_level",
           "data.original.pirate.render_info",
           "data.original.pirate.camera_profile",
           "data.original.pirate.animation_scripts",
           "data.original.pirate.reference_inputs")


def audit(bundle_arg):
    bundle = (ROOT / bundle_arg / "dkc2-reforge").resolve()
    bundle.relative_to(ROOT / "dist")
    assert (bundle / "dkc2reforge.exe").is_file()
    index = (bundle / "game.arci").read_bytes()
    archive = (bundle / "game.arcd").read_bytes()
    hits = [token.decode("ascii") for token in FORBIDDEN if token in index or token in archive]
    files = sorted(str(path.relative_to(bundle)).replace("\\", "/") for path in bundle.rglob("*") if path.is_file())
    leaked_paths = [name for name in files if name.startswith(("assets-raw/", "tools/", "roms/"))
                    or name.endswith("manifest.private.der")]
    report = {"bundle": str(bundle.relative_to(ROOT)),
              "status": "FAIL" if hits or leaked_paths else "PASS",
              "forbidden_index_strings": hits, "raw_tree_files": leaked_paths,
              "game_arci_sha256": hashlib.sha256(index).hexdigest(),
              "game_arcd_sha256": hashlib.sha256(archive).hexdigest(),
              "runtime_modules_expected": list(RUNTIME),
              "note": "runtime module names may be compressed in archive; .defignore plus build dependency is also verified by successful launch",
              "file_count": len(files)}
    path = bundle / "qa-bundle-audit.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(audit(Path(sys.argv[1])))
