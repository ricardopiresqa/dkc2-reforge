"""Stage ONLY approved screenshot extension sources for native cloud build.

Never copy resources from the game, ROMs, extracted art or private signing keys.
Input is git archive of reviewed pinned commit, not an executable installer.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "5f3098e3bfc37e8f26bde9428436b4d4499d1d50"
ALLOWED_SUFFIXES = {".c", ".cpp", ".h", ".hpp", ".mm", ".m", ".manifest", ".md", ".txt", ".script_api"}


def prepare():
    stage = ROOT / "tools/native-build-screenshot"
    stage.mkdir(parents=True, exist_ok=True)
    ref = ROOT / "tools/vendor/defold-screenshot/.git/refs/heads/master"
    assert ref.read_text().strip() == COMMIT
    archive_path = ROOT / "assets-raw/screenshot-source.zip"
    files = []
    with ZipFile(archive_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = PurePosixPath(info.filename)
            assert not name.is_absolute() and ".." not in name.parts
            assert name.parts[0] == "screenshot" or str(name) == "LICENSE.md"
            if str(name).startswith("screenshot/lib/web/"):
                continue  # not building HTML5; no JavaScript runtime or upload needed
            if name.suffix.lower() not in ALLOWED_SUFFIXES:
                raise ValueError("review unsupported native file before upload: " + str(name))
            assert info.file_size < 4_000_000
            data = archive.read(info)
            path = stage.joinpath(*name.parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            files.append({"path": str(name), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    # Minimal local scaffold, no game scenes/behavior/resource uploads.
    (stage / "game.project").write_text(
        "[project]\ntitle = ScreenshotQA\n\n[bootstrap]\nmain_collection = /main.collectionc\n"
        "\n[input]\ngame_binding = /empty.input_bindingc\n", encoding="utf-8")
    (stage / "empty.input_binding").write_text("", encoding="utf-8")
    (stage / "main.collection").write_text('name: "ScreenshotQA"\n', encoding="utf-8")
    report = {"source_commit": COMMIT, "license": "MIT", "budget_brl": 0,
              "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
              "native_source_files": files,
              "excluded": ["ROM", "extracted assets", "game Lua/scenes", "private signing keys"],
              "status": "staged; source review required before upload"}
    (ROOT / "docs/delivery/screenshot-native-source.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    prepare()
