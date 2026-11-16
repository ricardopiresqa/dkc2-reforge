"""
Try to decompress all samples and report results.
"""
import os, glob
import sys
sys.path.insert(0, '.')
from _decompress import decompress

samples_dir = 'samples'
files = sorted(glob.glob(os.path.join(samples_dir, '*.bin')))

results = {'ok': [], 'not_impl': [], 'error': []}

for f in files:
    data = open(f, 'rb').read()
    name = os.path.basename(f)
    try:
        result = decompress(data)
        results['ok'].append((name, len(data), len(result)))
    except NotImplementedError as e:
        results['not_impl'].append((name, str(e)))
    except Exception as e:
        results['error'].append((name, str(e)[:80]))

print(f"OK: {len(results['ok'])}")
print(f"NotImplemented: {len(results['not_impl'])}")
print(f"Error: {len(results['error'])}")
print()

if results['ok']:
    print("=== Decompressed OK ===")
    for name, src, dst in results['ok'][:10]:
        print(f"  {name}: {src} -> {dst} bytes")

if results['not_impl']:
    print("\n=== NotImplemented (need table context) ===")
    for name, reason in results['not_impl'][:10]:
        print(f"  {name}: {reason}")

if results['error']:
    print("\n=== Errors (potential bugs) ===")
    for name, reason in results['error'][:10]:
        print(f"  {name}: {reason}")
