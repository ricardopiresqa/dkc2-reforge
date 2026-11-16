"""Install isolated, pinned screenshot native engine in a NEW local QA bundle.

No cloud compilation of game sources/assets: native engine is built separately.
Does not modify older verified bundles or the production source game.project.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def install(bundle):
    bundle = (ROOT / bundle).resolve()
    bundle.relative_to(ROOT / "dist")
    assert bundle.name in ("pirate-panic-framebuffer-qa", "pirate-panic-original-animation",
                           "pirate-panic-animation-connected", "pirate-panic-animation-land-fixed",
                           "pirate-panic-animation-complete-resources", "pirate-panic-diddy-verified",
                           "pirate-panic-diddy-final-qa", "pirate-panic-fixed-tick-qa",
                           "pirate-panic-camera-initial-qa", "pirate-panic-camera-shifts-fixed",
                           "pirate-panic-camera-fraction-fixed", "pirate-panic-camera-phase-fixed",
                           "pirate-panic-camera-table-index-fixed", "pirate-panic-camera-profiled",
                           "pirate-panic-camera-spring-preserved", "pirate-panic-camera-final-recheck",
                           "pirate-panic-camera-damping-fixed", "pirate-panic-camera-damping-restored",
                           "pirate-panic-camera-state-diagnostic", "pirate-panic-faithful-slice",
                           "pirate-panic-silent-original-audio", "pirate-panic-safe-assetsraw",
                           "pirate-panic-secure-bundle", "pirate-panic-bg3-source-isolated",
                           "pirate-panic-route-qa", "pirate-panic-route-wall-test",
                           "pirate-panic-route-slope-fixed", "pirate-panic-route-slope-collision-check",
                           "pirate-panic-route-slope-step", "pirate-panic-route-slope-support-fixed",
                            "pirate-panic-save-native-route-qa", "pirate-panic-route-early-held-jump",
                             "pirate-panic-current-safe", "pirate-panic-latest-safe",
                             "pirate-panic-current-delivery", "pirate-panic-final-secure-current",
                             "pirate-panic-final-source-current",
                              "pirate-panic-collision-frame-qa",
                              "pirate-panic-walk-collision-qa", "pirate-panic-walk-collision-qa2",
                              "pirate-panic-walk-collision-qa3", "pirate-panic-walk-collision-qa4",
                              "pirate-panic-walk-collision-qa5", "pirate-panic-walk-collision-qa6",
                              "pirate-panic-walk-collision-qa7", "pirate-panic-walk-collision-qa8",
                              "pirate-panic-walk-collision-qa9", "pirate-panic-walk-collision-qa10",
                              "pirate-panic-walk-collision-qa11", "pirate-panic-neek-collision-qa12",
                              "pirate-panic-neek-collision-qa13", "pirate-panic-neek-collision-qa14",
                              "pirate-panic-neek-collision-qa15", "pirate-panic-neek-collision-qa16",
                              "pirate-panic-neek-collision-qa17", "pirate-panic-neek-collision-qa18",
                              "pirate-panic-collision-frames",
                             "pirate-panic-delivery-secure", "pirate-panic-final-qa",
                             "pirate-panic-latest-tested",
                              "pirate-panic-route-repeated-jumps", "pirate-panic-route-boundary-probe",
                               "pirate-panic-ledged-route-qa", "pirate-panic-invisible-collision-fix",
                               "pirate-panic-camera-source-pipeline", "pirate-panic-bg3-rigging",
                               "pirate-panic-bg2-hdma", "pirate-panic-lag-matched-qa",
                               "pirate-panic-bananas", "pirate-panic-bananas2",
                               "pirate-panic-hud", "pirate-panic-hud2",
                               "pirate-panic-hud3", "pirate-panic-items",
                               "pirate-panic-walkers", "pirate-panic-n1", "pirate-panic-n1b", "pirate-panic-n2", "pirate-panic-n3", "pirate-panic-n4", "pirate-panic-n5", "pirate-panic-n6", "pirate-panic-n7", "pirate-panic-n8", "pirate-panic-n9") or bundle.name.startswith("pirate-panic-qa-"), \
        "only new task-owned QA bundles may be replaced"
    game = bundle / "dkc2-reforge"
    source = ROOT / "tools/native-build-screenshot/build/x86_64-win32/dmengine.exe"
    target = game / "dkc2reforge.exe"
    assert source.is_file() and target.is_file()
    assert (game / "game.arci").is_file() and (game / "game.arcd").is_file()
    old = hashlib.sha256(target.read_bytes()).hexdigest()
    native = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source.read_bytes()[:2] == b"MZ", "invalid native engine binary"
    shutil.copy2(source, target)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == native
    report = {"bundle": str(bundle.relative_to(ROOT)),
              "source_commit": "5f3098e3bfc37e8f26bde9428436b4d4499d1d50",
              "native_engine_sha256": native, "original_bundle_engine_sha256": old,
              "native_build_scope": "isolated MIT sources only; no ROM/art/private signing key",
              "capture_scope": "game framebuffer only; opt-in QA",
              "status": "installed; capture runtime verification pending"}
    (game / "qa-engine-provenance.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle")
    install(parser.parse_args().bundle)
