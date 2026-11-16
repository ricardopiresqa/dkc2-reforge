import sys; sys.path.insert(0,'tools/asm-pipeline')
import pipeline
print(f"Pipeline functions: {len(pipeline.dis.functions)}")
fs = set()
for addr, name in pipeline.dis.functions.items():
    fs.add(f"func_{addr:06X}.c")
import os
pseudo_dir = "docs/pseudocode"
on_disk = set(os.listdir(pseudo_dir))
extra = on_disk - fs
missing = fs - on_disk
if extra:
    print(f"Stale files (not in pipeline): {len(extra)}")
    for f in sorted(extra): print(f"  {f}")
if missing:
    print(f"Missing files (in pipeline but not on disk): {len(missing)}")
    for f in sorted(missing): print(f"  {f}")
if not extra and not missing: print("All files match!")
