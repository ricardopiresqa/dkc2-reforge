"""Inspect render API usage shipped in our exact installed Bob version."""
from pathlib import Path
from zipfile import ZipFile

root = Path(__file__).resolve().parents[2]
with ZipFile(root / "bob.jar") as archive:
    content = archive.read("builtins/render/default.render_script")
target = root / "assets-raw/pirate/installed-default.render_script"
target.write_bytes(content)
print(target)
