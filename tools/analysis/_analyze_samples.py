"""
Scan compressed data files and find ones with known/low complexity opcodes.
Count opcode usage to find samples suitable for testing.
"""
import os, glob
from collections import Counter

samples_dir = 'samples'
files = sorted(glob.glob(os.path.join(samples_dir, '*.bin')))

def scan_opcodes(data):
    """Scan the compressed stream and categorize format bytes."""
    if len(data) < 40:
        return None
    fmt_byte = data[39]  # First format byte
    hi = (fmt_byte >> 4) & 0xF
    lo = fmt_byte & 0xF
    
    # Scan all format bytes in the stream
    offset = 40
    ops = Counter()
    while offset < len(data):
        fmt = data[offset]
        offset += 1
        h = (fmt >> 4) & 0xF
        l = fmt & 0xF
        ops[f"P{h}S{l}"] = ops.get(f"P{h}S{l}", 0) + 1
        
        # Account for operands consumed by each op type
        if h == 0:  # literal copy: count = lo, consume lo bytes
            offset += l
        elif h == 3:  # long literal: consume lo+3 bytes
            offset += l + 3
        elif h in (4, 5):  # fill: no extra bytes
            pass
        elif h == 6:  # word fill + secondary dispatch
            pass  # $54 already in header, no stream bytes for the value
        elif h in (7, 8):  # write header byte
            pass
        elif h == 9:  # backref short: no extra bytes
            pass
        elif h == 0xA:  # backref extra: 1 extra byte
            offset += 1
        elif h == 0xB:  # backref long1: 2 bytes
            offset += 2
        elif h == 0xC:  # backref long2: 2 bytes
            offset += 2
        elif h in (0xD, 0xE):  # shift: no extra, secondary dispatch
            pass
        elif h == 0xF:  # header indirect: no extra
            pass
        elif h in (1, 2):  # OR-copy: 1 or 2 index bytes
            offset += l
        
        # Handle secondary ops that consume stream bytes
        s_ops_extra = {0: None, 1: 1, 2: 2, 3: None, 4: None, 5: None,
                       9: 1, 0xA: 2, 0xB: 2, 0xC: 3, 0xF: 1}
        if l in s_ops_extra and s_ops_extra[l] is not None:
            sec_extra = s_ops_extra[l]
            if sec_extra is not None:
                offset += sec_extra

    return fmt_byte, hi, lo, ops

results = []
for f in files:
    data = open(f, 'rb').read()
    result = scan_opcodes(data)
    if result is None:
        continue
    fmt_byte, hi, lo, ops = result
    # Count problematic opcodes (OR-copy ops)
    problem_ops = sum(v for k, v in ops.items() if k.startswith('P1') or k.startswith('P2'))
    # Count secondary ops needing tables
    sec_problems = sum(v for k, v in ops.items() if k in [f'P{x}S{y}' for x in range(16) for y in (0,3,4,5)])
    
    results.append((os.path.basename(f), len(data), hi, lo, problem_ops, sec_problems, ops.most_common(5)))

# Sort by fewest problem ops
results.sort(key=lambda r: r[4] + r[5])

print("Top 20 files with fewest problematic opcodes:")
print(f"{'File':<35} {'Size':<6} {'Fmt':<4} {'Prob':<4} {'SecProb':<7} {'Top ops'}")
print("-"*85)
for name, size, hi, lo, prob, sprob, top5 in results[:20]:
    top_str = ', '.join(f'{k}:{v}' for k, v in top5)
    print(f"{name:<35} {size:<6} ${hi:X}{lo:X}  {prob:<4} {sprob:<7} {top_str}")
