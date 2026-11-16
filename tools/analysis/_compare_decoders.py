"""Compare _decompress vs decode_pac1 on all samples."""
import sys, os, glob
sys.path.insert(0, '.')
from _decompress import decompress as dec_new
import decode_pac1 as ref

files = sorted(glob.glob('samples/*.bin'))
results = {'match': 0, 'mismatch': [], 'ref_none': [], 'new_zero': []}

for f in files:
    data = open(f, 'rb').read()
    name = os.path.basename(f)

    out_ref = ref.decompress(data, 0)
    out_new = dec_new(data)

    if out_ref is None:
        results['ref_none'].append(name)
    elif out_ref == out_new:
        results['match'] += 1
    elif len(out_ref) != len(out_new):
        results['mismatch'].append((name, len(out_ref), len(out_new), 'len'))
    else:
        for i in range(len(out_ref)):
            if out_ref[i] != out_new[i]:
                results['mismatch'].append((name, len(out_ref), len(out_new), 'diff@%d' % i))
                break
    if len(out_new) == 0:
        results['new_zero'].append(name)

print("Match: %d" % results['match'])
print("Mismatch: %d" % len(results['mismatch']))
print("Ref None: %d" % len(results['ref_none']))
print("New zero-byte: %d" % len(results['new_zero']))
print()
if results['mismatch']:
    print("=== Mismatches ===")
    for name, rl, nl, reason in results['mismatch'][:15]:
        print("%s: ref=%d new=%d %s" % (name, rl, nl, reason))
if results['ref_none']:
    print("Ref None samples: %s ..." % results['ref_none'][:3])
if results['new_zero']:
    print("New 0-byte samples: %d" % len(results['new_zero']))
